ALL_RULES = [
    {'id': 'R-01', 'name': 'Missing Alt Text', 'category': 'Images & Media'},
    {'id': 'R-02', 'name': 'Missing Page Title', 'category': 'Page Structure'},
    {'id': 'R-03', 'name': 'Missing Language Attribute', 'category': 'Document Metadata'},
    {'id': 'R-04', 'name': 'Missing Form Labels', 'category': 'Forms & Controls'},
    {'id': 'R-05', 'name': 'Empty Buttons', 'category': 'Buttons & Controls'},
    {'id': 'R-06', 'name': 'Improper Heading Hierarchy', 'category': 'Heading Structure'},
    {'id': 'R-07', 'name': 'Broken / Non-descriptive Anchor Text', 'category': 'Links & Navigation'},
    {'id': 'R-08', 'name': 'Missing ARIA Attributes', 'category': 'ARIA & Interactive Elements'},
    {'id': 'R-09', 'name': 'Accessibility-related HTML Errors', 'category': 'HTML Validation & Structure'},
    {'id': 'R-10', 'name': 'Basic Color Contrast', 'category': 'Color & Visual Contrast'}
]

def calculate_accessibility_score(issues: list[dict]) -> dict:
    """
    Computes accessibility metrics and score (0 to 100).
    Complies with SRS FR-05 and TC-06 (8 passed, 2 failed -> 80%).
    """
    failed_rule_ids = {issue['rule_id'] for issue in issues if 'rule_id' in issue}
    total_rule_count = len(ALL_RULES)
    failed_rule_count = len(failed_rule_ids)
    passed_rule_count = total_rule_count - failed_rule_count

    # Base rule-compliance score (each rule is worth 10%)
    base_score = int(round((passed_rule_count / total_rule_count) * 100))
    
    # Severity breakdown
    severity_counts = {
        'Critical': 0,
        'High': 0,
        'Medium': 0,
        'Low': 0
    }
    
    for issue in issues:
        sev = issue.get('severity', 'Medium')
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Final score clamped between 0 and 100
    final_score = max(0, min(100, base_score))

    # Health status grade
    if final_score >= 90:
        grade = 'A'
        status = 'Excellent'
        color = 'success'
    elif final_score >= 75:
        grade = 'B'
        status = 'Good'
        color = 'primary'
    elif final_score >= 50:
        grade = 'C'
        status = 'Needs Improvement'
        color = 'warning'
    else:
        grade = 'F'
        status = 'Critical Violations'
        color = 'danger'

    return {
        'total_score': final_score,
        'grade': grade,
        'status': status,
        'color': color,
        'passed_rules': passed_rule_count,
        'failed_rules': failed_rule_count,
        'total_rules': total_rule_count,
        'total_issues': len(issues),
        'severity_breakdown': severity_counts,
        'rule_status': [
            {
                'id': r['id'],
                'name': r['name'],
                'category': r['category'],
                'passed': r['id'] not in failed_rule_ids,
                'issue_count': sum(1 for iss in issues if iss.get('rule_id') == r['id'])
            }
            for r in ALL_RULES
        ]
    }
