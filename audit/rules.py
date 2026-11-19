import re
from bs4 import BeautifulSoup, Tag

def clean_snippet(tag: Tag, max_len: int = 250) -> str:
    """Format and truncate HTML tag snippet for clean readability."""
    if not isinstance(tag, Tag):
        return str(tag)[:max_len]
    raw = str(tag)
    # If tag has deep children, truncate inner content to keep snippet readable
    if len(raw) > max_len:
        # Keep opening tag and closing
        name = tag.name
        attrs_str = " ".join(f'{k}="{v}"' if not isinstance(v, list) else f'{k}="{" ".join(v)}"' for k, v in tag.attrs.items())
        return f"<{name} {attrs_str}>...</{name}>" if attrs_str else f"<{name}>...</{name}>"
    return raw


# =========================================================================
# Rule 1: Missing Alt Text (R-01)
# =========================================================================
def check_missing_alt_text(soup: BeautifulSoup) -> list[dict]:
    issues = []
    for img in soup.find_all('img'):
        alt = img.get('alt')
        role = img.get('role', '').lower()
        aria_hidden = img.get('aria-hidden', '').lower()

        # Decorative images with role="presentation" or aria-hidden="true" are exempt
        if role in ('presentation', 'none') or aria_hidden == 'true':
            continue

        if alt is None:
            # Completely missing alt attribute
            snippet = clean_snippet(img)
            # Create recommended fix
            fix_img = Tag(name='img', attrs=dict(img.attrs))
            fix_img['alt'] = "Descriptive image description"
            issues.append({
                'rule_id': 'R-01',
                'rule_name': 'Missing Alt Text',
                'category': 'Images & Media',
                'severity': 'Critical',
                'wcag': 'WCAG 1.1.1 (Non-text Content)',
                'element': snippet,
                'explanation': 'The <img> element is missing an alt attribute. Screen readers cannot describe this image to visually impaired users.',
                'fix': str(fix_img)
            })
        elif alt.strip() == '':
            # Empty alt attribute without presentation role
            snippet = clean_snippet(img)
            issues.append({
                'rule_id': 'R-01',
                'rule_name': 'Empty Alt Text Without Decorative Role',
                'category': 'Images & Media',
                'severity': 'Medium',
                'wcag': 'WCAG 1.1.1 (Non-text Content)',
                'element': snippet,
                'explanation': 'The <img> element has an empty alt="" attribute. If this image is purely decorative, add role="presentation"; otherwise, provide descriptive text.',
                'fix': f'<img src="{img.get("src", "image.png")}" alt="Brief description" /> <!-- OR for decorative: alt="" role="presentation" -->'
            })
    return issues


# =========================================================================
# Rule 2: Missing Page Title (R-02)
# =========================================================================
def check_missing_page_title(soup: BeautifulSoup) -> list[dict]:
    issues = []
    head = soup.find('head')
    title = head.find('title') if head else soup.find('title')

    if not title or not title.string or not title.string.strip():
        issues.append({
            'rule_id': 'R-02',
            'rule_name': 'Missing Page Title',
            'category': 'Page Structure',
            'severity': 'Critical',
            'wcag': 'WCAG 2.4.2 (Page Titled)',
            'element': '<head> <!-- Missing or empty <title> tag --> </head>',
            'explanation': 'The web page lacks a descriptive <title> tag inside the <head>. Screen readers and browser tabs require a title to orient users.',
            'fix': '<head>\n    <title>Descriptive, Concise Page Title | Brand</title>\n</head>'
        })
    return issues


# =========================================================================
# Rule 3: Missing Language Attribute (R-03)
# =========================================================================
def check_missing_language_attribute(soup: BeautifulSoup) -> list[dict]:
    issues = []
    html_tag = soup.find('html')
    if not html_tag:
        issues.append({
            'rule_id': 'R-03',
            'rule_name': 'Missing HTML Tag',
            'category': 'Document Metadata',
            'severity': 'Critical',
            'wcag': 'WCAG 3.1.1 (Language of Page)',
            'element': '<html>',
            'explanation': 'Document is missing a root <html> element with a valid lang attribute.',
            'fix': '<html lang="en">'
        })
    else:
        lang = html_tag.get('lang')
        if not lang or not lang.strip():
            issues.append({
                'rule_id': 'R-03',
                'rule_name': 'Missing Language Attribute',
                'category': 'Document Metadata',
                'severity': 'High',
                'wcag': 'WCAG 3.1.1 (Language of Page)',
                'element': clean_snippet(html_tag),
                'explanation': 'The root <html> element does not specify a lang attribute. Screen readers cannot identify the correct speech pronunciation.',
                'fix': '<html lang="en">'
            })
    return issues


# =========================================================================
# Rule 4: Missing Form Labels (R-04)
# =========================================================================
def check_missing_form_labels(soup: BeautifulSoup) -> list[dict]:
    issues = []
    inputs = soup.find_all(['input', 'textarea', 'select'])
    for field in inputs:
        # Ignore non-input or self-labeled input types
        field_type = field.get('type', 'text').lower()
        if field.name == 'input' and field_type in ('hidden', 'submit', 'button', 'reset', 'image'):
            continue

        field_id = field.get('id')
        has_associated_label = False

        # 1. Check if enclosed in a <label>
        if field.find_parent('label'):
            has_associated_label = True

        # 2. Check for matching <label for="id">
        if not has_associated_label and field_id:
            matching_label = soup.find('label', attrs={'for': field_id})
            if matching_label and matching_label.get_text(strip=True):
                has_associated_label = True

        # 3. Check for aria-label or aria-labelledby
        if not has_associated_label:
            if field.get('aria-label', '').strip() or field.get('aria-labelledby', '').strip():
                has_associated_label = True

        if not has_associated_label:
            snippet = clean_snippet(field)
            f_id = field_id or "input-field-1"
            issues.append({
                'rule_id': 'R-04',
                'rule_name': 'Missing Form Label',
                'category': 'Forms & Controls',
                'severity': 'High',
                'wcag': 'WCAG 1.3.1 (Info and Relationships) & 3.3.2 (Labels or Instructions)',
                'element': snippet,
                'explanation': f'The form control <{field.name}> does not have an associated <label> or aria-label. Users with screen readers will not know its purpose.',
                'fix': f'<label for="{f_id}">Descriptive Label</label>\n<{field.name} id="{f_id}" name="{field.get("name", f_id)}" type="{field_type}" />'
            })
    return issues


# =========================================================================
# Rule 5: Empty Buttons (R-05)
# =========================================================================
def check_empty_buttons(soup: BeautifulSoup) -> list[dict]:
    issues = []
    for btn in soup.find_all(['button', 'input']):
        if btn.name == 'input':
            input_type = btn.get('type', '').lower()
            if input_type in ('button', 'submit', 'reset'):
                val = btn.get('value', '').strip()
                aria_lbl = btn.get('aria-label', '').strip()
                if not val and not aria_lbl:
                    issues.append({
                        'rule_id': 'R-05',
                        'rule_name': 'Empty Button Input',
                        'category': 'Buttons & Controls',
                        'severity': 'High',
                        'wcag': 'WCAG 4.1.2 (Name, Role, Value)',
                        'element': clean_snippet(btn),
                        'explanation': 'Input button has no visible value text or aria-label.',
                        'fix': f'<input type="{input_type}" value="Submit Action" />'
                    })
            continue

        # For <button> tag
        text_content = btn.get_text(strip=True)
        aria_label = btn.get('aria-label', '').strip()
        aria_labelledby = btn.get('aria-labelledby', '').strip()
        has_alt_img = any(img.get('alt', '').strip() for img in btn.find_all('img'))

        if not text_content and not aria_label and not aria_labelledby and not has_alt_img:
            issues.append({
                'rule_id': 'R-05',
                'rule_name': 'Empty Button',
                'category': 'Buttons & Controls',
                'severity': 'High',
                'wcag': 'WCAG 4.1.2 (Name, Role, Value)',
                'element': clean_snippet(btn),
                'explanation': 'The <button> contains no readable text, aria-label, or image with alt text. Assistive technology cannot convey its purpose.',
                'fix': '<button type="button" aria-label="Perform Action">\n    <i class="icon"></i> <span>Action Name</span>\n</button>'
            })
    return issues


# =========================================================================
# Rule 6: Improper Heading Hierarchy (R-06)
# =========================================================================
def check_heading_hierarchy(soup: BeautifulSoup) -> list[dict]:
    issues = []
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    if not headings:
        issues.append({
            'rule_id': 'R-06',
            'rule_name': 'No Headings Found',
            'category': 'Heading Structure',
            'severity': 'Medium',
            'wcag': 'WCAG 1.3.1 (Info and Relationships)',
            'element': '<body> <!-- No heading tags found --> </body>',
            'explanation': 'The webpage contains no heading tags (<h1> to <h6>). Screen readers use headings as the primary table of contents to navigate.',
            'fix': '<h1>Main Page Title</h1>\n<section>\n    <h2>Section Subtitle</h2>\n</section>'
        })
        return issues

    h1_count = sum(1 for h in headings if h.name == 'h1')
    if h1_count == 0:
        issues.append({
            'rule_id': 'R-06',
            'rule_name': 'Missing Top-Level Heading (h1)',
            'category': 'Heading Structure',
            'severity': 'High',
            'wcag': 'WCAG 1.3.1 (Info and Relationships)',
            'element': clean_snippet(headings[0]),
            'explanation': 'The page does not contain a top-level <h1> heading. Every accessible document should have an <h1> representing the main page topic.',
            'fix': '<h1>Primary Topic of This Page</h1>'
        })
    elif h1_count > 1:
        issues.append({
            'rule_id': 'R-06',
            'rule_name': 'Multiple h1 Headings',
            'category': 'Heading Structure',
            'severity': 'Low',
            'wcag': 'WCAG 1.3.1 (Info and Relationships)',
            'element': f'Found {h1_count} separate <h1> tags',
            'explanation': 'Having multiple <h1> elements can disorient assistive device users. Reserve <h1> for the overarching page title and use <h2> for subsections.',
            'fix': 'Use exactly one <h1> for the page title, then convert secondary <h1> elements into <h2> tags.'
        })

    # Check for skipped levels (e.g. h1 -> h3 skipping h2)
    last_level = 0
    for h in headings:
        current_level = int(h.name[1])
        if last_level != 0 and current_level > last_level + 1:
            issues.append({
                'rule_id': 'R-06',
                'rule_name': f'Skipped Heading Level (<{h.name}> after <h{last_level}>)',
                'category': 'Heading Structure',
                'severity': 'Medium',
                'wcag': 'WCAG 1.3.1 (Info and Relationships)',
                'element': clean_snippet(h),
                'explanation': f'Heading level was skipped from <h{last_level}> directly to <{h.name}>. Headings must follow a sequential structure without skipping steps.',
                'fix': f'<h{last_level + 1}>{h.get_text(strip=True) or "Subsection Title"}</h{last_level + 1}>'
            })
        last_level = current_level

    return issues


# =========================================================================
# Rule 7: Broken / Non-descriptive Anchor Text (R-07)
# =========================================================================
GENERIC_LINK_TEXTS = {
    'click here', 'click', 'here', 'read more', 'read', 'learn more', 'more',
    'link', 'go', 'view', 'details', 'check out', 'continue', 'this'
}

def check_link_text(soup: BeautifulSoup) -> list[dict]:
    issues = []
    for a in soup.find_all('a'):
        # Check if it has an aria-label or title
        aria_label = a.get('aria-label', '').strip()
        title = a.get('title', '').strip()
        text = a.get_text(strip=True)

        # Check if link has an image with alt text
        img_alt = ' '.join(img.get('alt', '').strip() for img in a.find_all('img')).strip()

        effective_text = (aria_label or text or img_alt or title).lower()

        if not effective_text:
            issues.append({
                'rule_id': 'R-07',
                'rule_name': 'Empty Link Text',
                'category': 'Links & Navigation',
                'severity': 'High',
                'wcag': 'WCAG 2.4.4 (Link Purpose In Context)',
                'element': clean_snippet(a),
                'explanation': 'The link contains no readable text, aria-label, or image alt description. Screen reader users cannot discern the link destination.',
                'fix': f'<a href="{a.get("href", "#")}">Descriptive Destination Name</a>'
            })
        elif effective_text in GENERIC_LINK_TEXTS:
            issues.append({
                'rule_id': 'R-07',
                'rule_name': f'Non-Descriptive Link Text ("{text}")',
                'category': 'Links & Navigation',
                'severity': 'Medium',
                'wcag': 'WCAG 2.4.4 (Link Purpose In Context)',
                'element': clean_snippet(a),
                'explanation': f'The link text "{text}" is ambiguous out of context. Screen reader users navigating a list of links cannot tell where it leads.',
                'fix': f'<a href="{a.get("href", "#")}" aria-label="Read more about our upcoming software releases">{text}</a>'
            })
    return issues


# =========================================================================
# Rule 8: Missing ARIA Attributes (R-08)
# =========================================================================
def check_aria_attributes(soup: BeautifulSoup) -> list[dict]:
    issues = []
    # Check elements acting as interactive elements without role / keyboard focus
    for tag in soup.find_all(attrs={'onclick': True}):
        if tag.name not in ('button', 'a', 'input', 'select', 'textarea'):
            role = tag.get('role')
            tabindex = tag.get('tabindex')
            if not role or tabindex is None:
                issues.append({
                    'rule_id': 'R-08',
                    'rule_name': f'Interactive <{tag.name}> Missing ARIA Role or Tabindex',
                    'category': 'ARIA & Interactive Elements',
                    'severity': 'High',
                    'wcag': 'WCAG 4.1.2 (Name, Role, Value) & 2.1.1 (Keyboard)',
                    'element': clean_snippet(tag),
                    'explanation': f'A non-interactive element <{tag.name}> has an onclick handler but lacks role="button" and tabindex="0", rendering it inaccessible to keyboard & screen reader users.',
                    'fix': f'<{tag.name} role="button" tabindex="0" onkeydown="if(event.key===\'Enter\'||event.key===\' \') {{ this.click(); }}" {clean_snippet(tag)[1:]}'
                })

    # Check disclosure/expandable elements
    for tag in soup.find_all(attrs={'aria-controls': True}):
        if 'aria-expanded' not in tag.attrs:
            issues.append({
                'rule_id': 'R-08',
                'rule_name': 'Missing aria-expanded on Disclosure Trigger',
                'category': 'ARIA & Interactive Elements',
                'severity': 'Medium',
                'wcag': 'WCAG 4.1.2 (Name, Role, Value)',
                'element': clean_snippet(tag),
                'explanation': 'Element has aria-controls referencing another panel, but is missing aria-expanded ("true" or "false") to signal state.',
                'fix': f'Add aria-expanded="false" to: {clean_snippet(tag)}'
            })
    return issues


# =========================================================================
# Rule 9: Accessibility-related HTML Errors: Duplicate IDs (R-09)
# =========================================================================
def check_duplicate_ids(soup: BeautifulSoup) -> list[dict]:
    issues = []
    id_counts = {}
    for tag in soup.find_all(attrs={'id': True}):
        elem_id = tag['id'].strip()
        if not elem_id:
            continue
        if elem_id not in id_counts:
            id_counts[elem_id] = []
        id_counts[elem_id].append(tag)

    for elem_id, tags in id_counts.items():
        if len(tags) > 1:
            snippet = f'Found id="{elem_id}" repeated on {len(tags)} elements: ' + ", ".join(f"<{t.name}>" for t in tags[:3])
            issues.append({
                'rule_id': 'R-09',
                'rule_name': f'Duplicate ID attribute (id="{elem_id}")',
                'category': 'HTML Validation & Structure',
                'severity': 'High',
                'wcag': 'WCAG 4.1.1 (Parsing) & 1.3.1 (Info and Relationships)',
                'element': snippet,
                'explanation': f'The id="{elem_id}" is used on {len(tags)} elements. Duplicate IDs cause screen readers to read the wrong form labels, focus wrong elements, and confuse ARIA references.',
                'fix': f'Ensure each element has a distinct ID, e.g. id="{elem_id}-1", id="{elem_id}-2"'
            })
    return issues


# =========================================================================
# Rule 10: Basic Color Contrast (R-10)
# =========================================================================
def parse_color_hex_or_rgb(color_str: str) -> tuple[int, int, int] | None:
    """Parses hex or rgb() strings into (r, g, b) tuple."""
    color_str = color_str.strip().lower()
    
    # Hex: #fff or #ffffff
    if color_str.startswith('#'):
        hex_code = color_str.lstrip('#')
        if len(hex_code) == 3:
            hex_code = ''.join(c * 2 for c in hex_code)
        if len(hex_code) == 6:
            try:
                return (int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16))
            except ValueError:
                return None
                
    # RGB: rgb(255, 255, 255)
    rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
    if rgb_match:
        try:
            return (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)))
        except ValueError:
            return None

    # Common named colors fallback
    named_colors = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'lightgray': (211, 211, 211),
        'red': (255, 0, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0)
    }
    return named_colors.get(color_str)

def get_relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Computes relative luminance for an sRGB tuple per WCAG 2.1 specs."""
    normalized = []
    for c in rgb:
        v = c / 255.0
        if v <= 0.03928:
            normalized.append(v / 12.92)
        else:
            normalized.append(((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * normalized[0] + 0.7152 * normalized[1] + 0.0722 * normalized[2]

def get_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """Calculates contrast ratio (L1 + 0.05) / (L2 + 0.05)."""
    l1 = get_relative_luminance(rgb1)
    l2 = get_relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def check_color_contrast(soup: BeautifulSoup) -> list[dict]:
    issues = []
    # Inspect tags with inline styles declaring both color and background
    for tag in soup.find_all(attrs={'style': True}):
        style = tag['style']
        # Extract color: ...; and background[-color]: ...;
        fg_match = re.search(r'(?<![a-z\-])color\s*:\s*([^;]+)', style, re.I)
        bg_match = re.search(r'background(?:-color)?\s*:\s*([^;]+)', style, re.I)

        if fg_match and bg_match:
            fg_str = fg_match.group(1).strip()
            bg_str = bg_match.group(1).strip()

            fg_rgb = parse_color_hex_or_rgb(fg_str)
            bg_rgb = parse_color_hex_or_rgb(bg_str)

            if fg_rgb and bg_rgb:
                ratio = get_contrast_ratio(fg_rgb, bg_rgb)
                # WCAG AA requires at least 4.5:1 for normal text
                if ratio < 4.5:
                    issues.append({
                        'rule_id': 'R-10',
                        'rule_name': f'Insufficient Color Contrast ({ratio:.2f}:1)',
                        'category': 'Color & Visual Contrast',
                        'severity': 'Medium',
                        'wcag': 'WCAG 1.4.3 (Contrast Minimum)',
                        'element': clean_snippet(tag),
                        'explanation': f'Inline styles specify foreground color "{fg_str}" on background "{bg_str}" resulting in a {ratio:.2f}:1 contrast ratio. WCAG AA requires a minimum of 4.5:1 for standard text.',
                        'fix': 'Increase the difference between text and background colors. For example, use #111827 (dark text) on #FFFFFF (light background), or #FFFFFF (light text) on #1F2937 (dark background).'
                    })
    return issues


# =========================================================================
# Master Audit Runner
# =========================================================================
def run_all_accessibility_checks(html_content: str) -> list[dict]:
    """
    Parses HTML content using BeautifulSoup and runs all 10 predefined
    accessibility rules (R-01 through R-10).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    all_issues = []

    all_issues.extend(check_missing_alt_text(soup))
    all_issues.extend(check_missing_page_title(soup))
    all_issues.extend(check_missing_language_attribute(soup))
    all_issues.extend(check_missing_form_labels(soup))
    all_issues.extend(check_empty_buttons(soup))
    all_issues.extend(check_heading_hierarchy(soup))
    all_issues.extend(check_link_text(soup))
    all_issues.extend(check_aria_attributes(soup))
    all_issues.extend(check_duplicate_ids(soup))
    all_issues.extend(check_color_contrast(soup))

    return all_issues
