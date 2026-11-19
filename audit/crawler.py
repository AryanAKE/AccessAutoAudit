import socket
import ipaddress
from urllib.parse import urlparse
import requests

def is_safe_url(url: str) -> tuple[bool, str]:
    """
    Validates URL syntax and guards against SSRF (Server-Side Request Forgery)
    by disallowing loopback, local network, and private IPs.
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ('http', 'https'):
        return False, "Only HTTP and HTTPS URLs are supported."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing domain or host."

    # Prevent loopback and obvious internal hostnames
    if hostname in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
        return False, "Access to localhost or loopback addresses is restricted."

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return False, f"Access to private/internal IP address {hostname} is blocked for security."
    except ValueError:
        # Hostname is a domain name, resolve and check its IP
        try:
            resolved_ip = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved_ip)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return False, f"Domain {hostname} resolves to restricted private IP {resolved_ip}."
        except socket.error:
            # Allow crawler to attempt connection which will report proper network error
            pass

    return True, ""


def fetch_website_html(url: str, timeout: int = 5, max_bytes: int = 5 * 1024 * 1024) -> tuple[str, str]:
    """
    Fetches the HTML of a target URL.
    Returns: (html_text, error_message)
    """
    is_safe, error_msg = is_safe_url(url)
    if not is_safe:
        return "", error_msg

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (AccessibilityBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            stream=True,
            allow_redirects=True
        )
        response.raise_for_status()

        # Check content type if available
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type and not any(t in content_type for t in ['text/html', 'application/xhtml+xml', 'text/plain']):
            return "", f"URL does not return HTML (received: {content_type})"

        # Read content up to max_bytes gracefully (SRS TC-12)
        content_bytes = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                content_bytes.extend(chunk)
                if len(content_bytes) >= max_bytes:
                    break

        # Decode content with detected or fallback encoding
        encoding = response.encoding or 'utf-8'
        try:
            html = content_bytes.decode(encoding, errors='replace')
        except Exception:
            html = content_bytes.decode('utf-8', errors='replace')

        return html, ""

    except requests.exceptions.Timeout:
        return "", f"Connection timed out while fetching {url} (exceeded {timeout}s limit)."
    except requests.exceptions.ConnectionError:
        return "", f"Could not connect to {url}. The server may be unreachable or the domain does not exist."
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Error"
        return "", f"HTTP error {status_code} received from target server."
    except Exception as e:
        return "", f"Unexpected error while fetching URL: {str(e)}"
