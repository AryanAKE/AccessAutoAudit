import os
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    jsonify, send_file, session
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from config import Config
from models import db, User, ScanReport, AccessibilityIssue
from audit import (
    is_safe_url, fetch_website_html, run_all_accessibility_checks, 
    calculate_accessibility_score, generate_pdf_report
)

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if test_config:
        app.config.update(test_config)

    # Initialize Database
    db.init_app(app)

    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access your audit history and saved reports.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Create tables automatically
    with app.app_context():
        db.create_all()

    # -------------------------------------------------------------
    # Routes
    # -------------------------------------------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/scan', methods=['POST'])
    def scan():
        target_url = request.form.get('url', '').strip()
        custom_html = request.form.get('custom_html', '').strip()

        # Check if user entered URL or direct HTML for testing
        if not target_url and not custom_html:
            flash("Please provide a valid URL to begin accessibility scan.", "warning")
            return redirect(url_for('index'))

        if target_url:
            # Add scheme if missing
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url

            # Validate URL and SSRF protection
            is_safe, error_msg = is_safe_url(target_url)
            if not is_safe:
                flash(f"Invalid or restricted URL: {error_msg}", "danger")
                return redirect(url_for('index'))

            # Fetch HTML
            html_content, fetch_error = fetch_website_html(target_url)
            if fetch_error:
                flash(f"Failed to crawl target website: {fetch_error}", "danger")
                return redirect(url_for('index'))
        else:
            # Custom HTML audit mode
            html_content = custom_html
            target_url = "Direct HTML Input"

        # Execute Accessibility Rules Engine
        issues = run_all_accessibility_checks(html_content)

        # Compute Score
        score_data = calculate_accessibility_score(issues)

        # Save to database if user is logged in
        saved_scan_id = None
        if current_user.is_authenticated:
            scan_report = ScanReport(
                user_id=current_user.user_id,
                target_url=target_url,
                total_score=score_data['total_score']
            )
            db.session.add(scan_report)
            db.session.flush() # obtain scan_id

            for iss in issues:
                db_issue = AccessibilityIssue(
                    scan_id=scan_report.scan_id,
                    rule_violated=iss.get('rule_name', 'Rule Violation'),
                    rule_id=iss.get('rule_id', 'R-00'),
                    severity=iss.get('severity', 'Medium'),
                    html_snippet=iss.get('element', '')[:1000],
                    recommended_fix=iss.get('fix', '')[:1000],
                    explanation=iss.get('explanation', '')[:1000]
                )
                db.session.add(db_issue)
            
            db.session.commit()
            saved_scan_id = scan_report.scan_id
        else:
            # Store temporary audit data in session for guest PDF download
            session['guest_audit'] = {
                'target_url': target_url,
                'score_data': score_data,
                'issues': issues
            }

        return render_template(
            'dashboard.html',
            target_url=target_url,
            score_data=score_data,
            issues=issues,
            scan_id=saved_scan_id,
            is_guest=not current_user.is_authenticated
        )

    @app.route('/report/<int:scan_id>')
    def view_report(scan_id):
        report = db.session.get(ScanReport, scan_id)
        if not report:
            flash("Audit report not found.", "warning")
            return redirect(url_for('index'))

        # Prepare score data and issues from DB
        issues_list = []
        for iss in report.issues:
            issues_list.append({
                'rule_id': iss.rule_id,
                'rule_name': iss.rule_violated,
                'severity': iss.severity,
                'element': iss.html_snippet,
                'fix': iss.recommended_fix,
                'explanation': iss.explanation,
                'wcag': 'WCAG 2.1'
            })

        score_data = calculate_accessibility_score(issues_list)

        return render_template(
            'dashboard.html',
            target_url=report.target_url,
            score_data=score_data,
            issues=issues_list,
            scan_id=report.scan_id,
            scan_date=report.scan_date,
            is_guest=False
        )

    @app.route('/download-pdf/<int:scan_id>')
    def download_saved_pdf(scan_id):
        report = db.session.get(ScanReport, scan_id)
        if not report:
            flash("Scan report not found.", "danger")
            return redirect(url_for('index'))

        issues_list = [
            {
                'rule_id': iss.rule_id,
                'rule_name': iss.rule_violated,
                'severity': iss.severity,
                'element': iss.html_snippet,
                'fix': iss.recommended_fix,
                'explanation': iss.explanation,
                'wcag': 'WCAG 2.1'
            }
            for iss in report.issues
        ]
        score_data = calculate_accessibility_score(issues_list)
        pdf_buffer = generate_pdf_report(report.target_url, score_data, issues_list)

        clean_name = report.target_url.replace("https://", "").replace("http://", "").replace("/", "_")[:30]
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"audit_report_{clean_name}_{report.scan_id}.pdf",
            mimetype='application/pdf'
        )

    @app.route('/download-guest-pdf')
    def download_guest_pdf():
        guest_data = session.get('guest_audit')
        if not guest_data:
            flash("No active audit session found to generate PDF.", "warning")
            return redirect(url_for('index'))

        pdf_buffer = generate_pdf_report(
            guest_data['target_url'],
            guest_data['score_data'],
            guest_data['issues']
        )
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="accessibility_audit_report.pdf",
            mimetype='application/pdf'
        )

    # -------------------------------------------------------------
    # Authentication & User Accounts
    # -------------------------------------------------------------
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('history'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not username or not password:
                flash("Username and password are required.", "danger")
                return render_template('register.html')

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "warning")
                return render_template('register.html')

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template('register.html')

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Please pick another.", "warning")
                return render_template('register.html')

            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            flash(f"Welcome, {username}! Your account has been registered successfully.", "success")
            return redirect(url_for('index'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('history'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f"Logged in as {username}.", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('history'))
            else:
                flash("Invalid username or password. Please try again.", "danger")

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for('index'))

    @app.route('/history')
    @login_required
    def history():
        scans = ScanReport.query.filter_by(user_id=current_user.user_id)\
                                .order_by(ScanReport.scan_date.desc()).all()

        # Prepare dates and scores for Chart.js trend graph (chronological order)
        chart_scans = list(reversed(scans))
        chart_labels = [s.scan_date.strftime('%b %d, %H:%M') for s in chart_scans]
        chart_scores = [s.total_score for s in chart_scans]

        return render_template(
            'history.html',
            scans=scans,
            chart_labels=chart_labels,
            chart_scores=chart_scores
        )

    # -------------------------------------------------------------
    # REST API for automated testing or headless integration
    # -------------------------------------------------------------
    @app.route('/api/audit', methods=['POST'])
    def api_audit():
        data = request.get_json(silent=True) or {}
        html = data.get('html', '')
        url = data.get('url', '')

        if not html and not url:
            return jsonify({'error': 'Either "url" or "html" parameter is required.'}), 400

        if url:
            is_safe, error_msg = is_safe_url(url)
            if not is_safe:
                return jsonify({'error': error_msg}), 400
            html, fetch_error = fetch_website_html(url)
            if fetch_error:
                return jsonify({'error': fetch_error}), 502

        issues = run_all_accessibility_checks(html)
        score_data = calculate_accessibility_score(issues)

        return jsonify({
            'status': 'success',
            'score': score_data['total_score'],
            'grade': score_data['grade'],
            'passed_rules': score_data['passed_rules'],
            'failed_rules': score_data['failed_rules'],
            'total_issues': len(issues),
            'issues': issues
        })

    return app

if __name__ == '__main__':
    app = create_app()
    # Runs locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
