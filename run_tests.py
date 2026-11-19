"""
Accessibility Auto-Audit & Repair Assistant — Automated Test Suite
Executes all 15 Test Cases defined in Chapter 11 of the SRS.
"""

import sys
import unittest
from app import create_app
from models import db, User, ScanReport, AccessibilityIssue
from audit.rules import (
    run_all_accessibility_checks, check_missing_alt_text,
    check_empty_buttons, check_aria_attributes, check_duplicate_ids
)
from audit.scorer import calculate_accessibility_score
from audit.crawler import is_safe_url, fetch_website_html
from audit.pdf_generator import generate_pdf_report
from bs4 import BeautifulSoup

class AccessibilityAssistantTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret'
        })
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # TC-01: Submit Valid URL Format
    def test_tc01_submit_valid_url(self):
        is_safe, msg = is_safe_url("https://example.com")
        self.assertTrue(is_safe)
        self.assertEqual(msg, "")

    # TC-02: Submit Invalid URL Format
    def test_tc02_submit_invalid_url(self):
        is_safe, msg = is_safe_url("ftp://not-supported.org")
        self.assertFalse(is_safe)
        self.assertIn("Only HTTP and HTTPS", msg)

        is_safe2, msg2 = is_safe_url("not a url at all")
        self.assertFalse(is_safe2)

    # TC-03: Submit Unreachable URL
    def test_tc03_submit_unreachable_url(self):
        html, err = fetch_website_html("https://thisdomaindoesnotexistatall123456789.org", timeout=2)
        self.assertEqual(html, "")
        # TC-03 SRS: HTTP error / timeout handled gracefully
        self.assertTrue(any(term in err.lower() for term in ['error', 'timeout', 'connect', 'reach']))

    # TC-04: Detect Missing Alt Text
    def test_tc04_detect_missing_alt_text(self):
        html = '<img src="cat.jpg">'
        soup = BeautifulSoup(html, 'html.parser')
        issues = check_missing_alt_text(soup)
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0]['rule_id'], 'R-01')

    # TC-05: Detect Empty Button
    def test_tc05_detect_empty_button(self):
        html = '<button></button>'
        soup = BeautifulSoup(html, 'html.parser')
        issues = check_empty_buttons(soup)
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0]['rule_id'], 'R-05')

    # TC-06: Verify Score Math (8 passed, 2 failed -> 80%)
    def test_tc06_verify_score_math(self):
        mock_issues = [
            {'rule_id': 'R-01', 'severity': 'Critical'},
            {'rule_id': 'R-04', 'severity': 'High'}
        ]
        score_data = calculate_accessibility_score(mock_issues)
        self.assertEqual(score_data['passed_rules'], 8)
        self.assertEqual(score_data['failed_rules'], 2)
        self.assertEqual(score_data['total_score'], 80)

    # TC-07: Verify Code Snippet Remediation
    def test_tc07_verify_code_snippet(self):
        html = '<img src="x.png">'
        soup = BeautifulSoup(html, 'html.parser')
        issues = check_missing_alt_text(soup)
        self.assertIn('alt="Descriptive image description"', issues[0]['fix'])

    # TC-08: User Registration
    def test_tc08_user_registration(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)

    # TC-09: Password Hashing
    def test_tc09_password_hashing(self):
        user = User(username='hashcheck')
        user.set_password('mysecretpass')
        self.assertNotEqual(user.password_hash, 'mysecretpass')
        self.assertTrue(user.check_password('mysecretpass'))
        self.assertFalse(user.check_password('wrongpass'))

    # TC-10: Save Scan History
    def test_tc10_save_scan_history(self):
        with self.app.app_context():
            user = User(username='historyuser')
            user.set_password('pass1234')
            db.session.add(user)
            db.session.commit()

            report = ScanReport(
                user_id=user.user_id,
                target_url='https://sample.edu',
                total_score=85
            )
            db.session.add(report)
            db.session.commit()

            saved = ScanReport.query.filter_by(user_id=user.user_id).first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.total_score, 85)

    # TC-11: Guest Scan Restrictions
    def test_tc11_guest_scan_restrictions(self):
        # Accessing /history without login should redirect to /login
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    # TC-12: Handle Massive Page
    def test_tc12_handle_massive_page(self):
        # Simulated >5MB content truncation test
        huge_html = "<html><body>" + ("<p>Text</p>" * 10000) + "</body></html>"
        issues = run_all_accessibility_checks(huge_html)
        self.assertIsInstance(issues, list)

    # TC-13: Detect ARIA Issue
    def test_tc13_detect_aria_issue(self):
        html = '<div onclick="doSomething()">Click me</div>'
        soup = BeautifulSoup(html, 'html.parser')
        issues = check_aria_attributes(soup)
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0]['rule_id'], 'R-08')

    # TC-14: Duplicate IDs Check
    def test_tc14_duplicate_ids_check(self):
        html = '<div id="primary-nav">1</div><div id="primary-nav">2</div>'
        soup = BeautifulSoup(html, 'html.parser')
        issues = check_duplicate_ids(soup)
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0]['rule_id'], 'R-09')

    # TC-15: Generate PDF Report
    def test_tc15_generate_pdf_report(self):
        mock_score = {
            'total_score': 80,
            'passed_rules': 8,
            'failed_rules': 2,
            'total_rules': 10,
            'status': 'Good',
            'severity_breakdown': {'Critical': 1, 'High': 1, 'Medium': 0, 'Low': 0}
        }
        mock_issues = [
            {
                'rule_id': 'R-01',
                'rule_name': 'Empty Alt Text',
                'severity': 'Critical',
                'wcag': 'WCAG 1.1.1',
                'element': '<img src="cat.png">',
                'fix': '<img src="cat.png" alt="Cat photo">',
                'explanation': 'The <img> element has an empty alt="" attribute. If this image is purely decorative, add role="presentation"; otherwise, provide descriptive text.'
            }
        ]
        pdf_buf = generate_pdf_report("https://example.com?foo=1&bar=2", mock_score, mock_issues)
        pdf_bytes = pdf_buf.getvalue()
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()
