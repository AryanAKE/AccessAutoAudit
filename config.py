import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'accessibility-audit-secret-key-2026')
    # Default to SQLite for zero-configuration startup, with full MySQL compatibility via DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///accessibility_audit.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Crawler configuration
    MAX_PAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum as per SRS NFR-01 / TC-12
    REQUEST_TIMEOUT_SECONDS = 5            # 5 seconds timeout as per SRS NFR-01
    USER_AGENT = "AccessibilityAuditBot/1.0 (+https://github.com/accessibility-assistant)"
