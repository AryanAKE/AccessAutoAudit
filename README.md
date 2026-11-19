# Accessibility Auto-Audit & Repair Assistant

> **Software Requirements Specification (SRS) Implementation — Version 1.0**  
> **Course:** Software Engineering – Innovative Software Development Project  
> **Department of Computer Science & Engineering, Tezpur University**  
> **Presenters:** Aryan Kumar Ekka (CSM25024), Himanshu Gogoi (CSM25027), Tushar Bharali (CSM25055)

---

## 📌 Project Overview
The **Accessibility Auto-Audit & Repair Assistant** is a web-based software engineering platform designed to evaluate target web pages against recognized **WCAG 2.1** accessibility standards.

It crawls a target website URL, parses the Document Object Model (DOM), identifies accessibility violations across **10 core rules**, calculates a quantifiable **compliance score (0–100)**, generates **exact code-level repair recommendations**, provides downloadable **PDF audit reports**, and tracks historical compliance trends for authenticated users.

---

## 🛠️ Tech Stack (Simple & Lightweight)
- **Backend:** Python 3.10+ / 3.11 with **Flask Microframework**
- **DOM Parsing & Crawling:** `BeautifulSoup4` + `Requests`
- **Database / ORM:** SQLite (zero-config, out-of-the-box) or **MySQL 8.0+** via `Flask-SQLAlchemy`
- **Authentication & Security:** Bcrypt/Werkzeug password hashing, `Flask-Login` sessions, and SSRF (Server-Side Request Forgery) protection
- **PDF Generation:** `ReportLab`
- **Frontend:** HTML5, CSS3, Bootstrap 5, Bootstrap Icons, and **Chart.js** for trend visualization

---

## 📋 The 10 Automated WCAG Rules Enforced (Chapter 5)
1. **R-01: Missing Alt Text (WCAG 1.1.1)** — Checks `<img>` tags for missing or empty `alt` attributes on non-decorative images.
2. **R-02: Missing Page Title (WCAG 2.4.2)** — Verifies `<head>` contains a non-empty, descriptive `<title>` tag.
3. **R-03: Missing Language Attribute (WCAG 3.1.1)** — Ensures the root `<html>` element specifies a `lang` attribute for screen readers.
4. **R-04: Missing Form Labels (WCAG 1.3.1 & 3.3.2)** — Validates that form fields (`<input>`, `<textarea>`, `<select>`) have associated `<label for="...">` or `aria-label`.
5. **R-05: Empty Buttons (WCAG 4.1.2)** — Flags `<button>` elements lacking discernible text, aria-labels, or labeled icons.
6. **R-06: Improper Heading Hierarchy (WCAG 1.3.1)** — Detects skipped heading levels (e.g. `<h1>` followed by `<h3>`) and missing top-level `<h1>` headings.
7. **R-07: Broken / Non-descriptive Anchor Text (WCAG 2.4.4)** — Flags vague link text like *"click here"* or *"read more"* without destination context.
8. **R-08: Missing ARIA Attributes (WCAG 4.1.2 & 2.1.1)** — Catches clickable non-interactive tags (`<div>`, `<span>`) missing `role="button"`, `tabindex="0"`, or disclosure `aria-expanded`.
9. **R-09: Accessibility-related HTML Errors (WCAG 4.1.1)** — Flags duplicate `id` attributes that disorient assistive technologies.
10. **R-10: Basic Color Contrast (WCAG 1.4.3)** — Computes relative luminance on inline styles to enforce a minimum 4.5:1 contrast ratio.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10 or higher.
- A virtual environment is already provisioned in `.venv`.

### 2. Run the Application
From the project folder, run:
```powershell
.venv\Scripts\python.exe app.py
```
Or with standard Python on your PATH:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Run Automated System Tests (Chapter 11)
To run the automated test suite verifying all 15 test cases (TC-01 to TC-15):
```powershell
.venv\Scripts\python.exe run_tests.py
```

Expected output:
```text
...............
Ran 15 tests in 2.975s
OK
```

---

## 🗄️ Database Architecture (Chapter 9)

### Tables
1. **`users`**:
   - `user_id` (INT, Primary Key)
   - `username` (VARCHAR(50), Unique)
   - `password_hash` (VARCHAR(255))
   - `created_at` (TIMESTAMP)

2. **`scan_reports`**:
   - `scan_id` (INT, Primary Key)
   - `user_id` (INT, Foreign Key referencing `users.user_id`, nullable for guest scans)
   - `target_url` (VARCHAR(255))
   - `total_score` (INT)
   - `scan_date` (TIMESTAMP)

3. **`accessibility_issues`**:
   - `issue_id` (INT, Primary Key)
   - `scan_id` (INT, Foreign Key referencing `scan_reports.scan_id`)
   - `rule_violated` (VARCHAR(100))
   - `rule_id` (VARCHAR(10))
   - `severity` (VARCHAR(20))
   - `html_snippet` (TEXT)
   - `recommended_fix` (TEXT)
   - `explanation` (TEXT)

---

## 🧪 Verification Matrix: SRS Chapter 11 Test Cases

| Test Case | Description | Verification Method | Status |
| :--- | :--- | :--- | :---: |
| **TC-01** | Submit Valid URL | Valid URL passes syntax & SSRF checks | ✅ PASS |
| **TC-02** | Submit Invalid URL Format | Invalid protocol (e.g. ftp) blocked | ✅ PASS |
| **TC-03** | Submit Unreachable URL | Non-existent domain handled gracefully | ✅ PASS |
| **TC-04** | Detect Missing Alt Text | `<img>` without `alt` flags R-01 | ✅ PASS |
| **TC-05** | Detect Empty Button | Empty `<button>` flags R-05 | ✅ PASS |
| **TC-06** | Verify Score Math | 8 passed, 2 failed calculates to 80% | ✅ PASS |
| **TC-07** | Verify Code Snippet | Generates `<img alt="...">` remediation | ✅ PASS |
| **TC-08** | User Registration | Account created and saved to database | ✅ PASS |
| **TC-09** | Password Hashing | Stored with secure one-way hash | ✅ PASS |
| **TC-10** | Save Scan History | Scans saved and displayed in user profile | ✅ PASS |
| **TC-11** | Guest Scan Restrictions | Direct access to history requires login | ✅ PASS |
| **TC-12** | Handle Massive Page | Large page handled without crashing | ✅ PASS |
| **TC-13** | Detect ARIA Issue | `onclick` on non-button flags R-08 | ✅ PASS |
| **TC-14** | Duplicate IDs Check | Repeated `id` across DOM flags R-09 | ✅ PASS |
| **TC-15** | Generate PDF Report | ReportLab generates valid `%PDF` stream | ✅ PASS |

---

## 👥 Project Team
- **Aryan Kumar Ekka** (CSM25024)
- **Himanshu Gogoi** (CSM25027)
- **Tushar Bharali** (CSM25055)
