from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_reports = db.relationship('ScanReport', backref='user', lazy=True, cascade='all, delete-orphan')

    # Flask-Login integration
    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ScanReport(db.Model):
    __tablename__ = 'scan_reports'
    
    scan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True) # Nullable for guest scans
    target_url = db.Column(db.String(255), nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('AccessibilityIssue', backref='report', lazy=True, cascade='all, delete-orphan')


class AccessibilityIssue(db.Model):
    __tablename__ = 'accessibility_issues'
    
    issue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan_reports.scan_id'), nullable=False)
    rule_violated = db.Column(db.String(100), nullable=False)
    rule_id = db.Column(db.String(10), nullable=True)
    severity = db.Column(db.String(20), default='Medium')
    html_snippet = db.Column(db.Text, nullable=False)
    recommended_fix = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
