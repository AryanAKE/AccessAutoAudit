import io
import html
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(target_url: str, score_data: dict, issues: list[dict]) -> io.BytesIO:
    """
    Generates a professional accessibility audit PDF report buffer in memory.
    Safely escapes all dynamic strings to prevent ReportLab XML/HTML paraparser errors.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        spaceAfter=15
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#111827'),
        spaceBefore=12,
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B'),
        backColor=colors.HexColor('#F1F5F9'),
        spaceBefore=3,
        spaceAfter=3
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Accessibility Auto-Audit &amp; Repair Assistant", title_style))
    story.append(Paragraph(f"Official Web Accessibility Evaluation Report | Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

    # Executive Summary Card Table
    score = score_data.get('total_score', 0)
    score_color = colors.HexColor('#16A34A') if score >= 80 else (colors.HexColor('#D97706') if score >= 50 else colors.HexColor('#DC2626'))
    safe_target_url = html.escape(str(target_url))
    status_label = html.escape(str(score_data.get('status', 'Audited')))

    summary_data = [
        [
            Paragraph("<b>Target URL:</b>", styles['Normal']),
            Paragraph(f"<font color='#2563EB'>{safe_target_url}</font>", styles['Normal'])
        ],
        [
            Paragraph("<b>Overall Compliance Score:</b>", styles['Normal']),
            Paragraph(f"<b><font size='14' color='{score_color.hexval()}'>{score} / 100</font></b> ({status_label})", styles['Normal'])
        ],
        [
            Paragraph("<b>Rules Status:</b>", styles['Normal']),
            Paragraph(f"{score_data.get('passed_rules', 0)} Passed / {score_data.get('failed_rules', 0)} Failed (out of {score_data.get('total_rules', 10)} evaluated rules)", styles['Normal'])
        ],
        [
            Paragraph("<b>Total Issues Detected:</b>", styles['Normal']),
            Paragraph(f"{len(issues)} issue(s) found across DOM structure", styles['Normal'])
        ]
    ]

    summary_table = Table(summary_data, colWidths=[160, 370])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#EDF2F7')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Severity Breakdown
    sev = score_data.get('severity_breakdown', {})
    sev_data = [
        [
            Paragraph("<b>Critical Violations</b>", styles['Normal']),
            Paragraph("<b>High Severity</b>", styles['Normal']),
            Paragraph("<b>Medium Severity</b>", styles['Normal']),
            Paragraph("<b>Low Severity</b>", styles['Normal'])
        ],
        [
            Paragraph(f"<font color='#DC2626'><b>{sev.get('Critical', 0)}</b></font>", styles['Normal']),
            Paragraph(f"<font color='#EA580C'><b>{sev.get('High', 0)}</b></font>", styles['Normal']),
            Paragraph(f"<font color='#D97706'><b>{sev.get('Medium', 0)}</b></font>", styles['Normal']),
            Paragraph(f"<font color='#2563EB'><b>{sev.get('Low', 0)}</b></font>", styles['Normal']),
        ]
    ]
    sev_table = Table(sev_data, colWidths=[132, 132, 133, 133])
    sev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(sev_table)
    story.append(Spacer(1, 15))

    # Detailed Violations & Code Fixes
    story.append(Paragraph("Detailed Findings &amp; Code Remediation Guide", section_heading))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=10))

    if not issues:
        story.append(Paragraph("<font color='#16A34A'><b>Outstanding! No accessibility violations were detected on this page.</b></font>", styles['Normal']))
    else:
        for idx, issue in enumerate(issues, 1):
            rule_name = issue.get('rule_name', issue.get('rule_violated', 'Violation'))
            rule_id = issue.get('rule_id', 'R-XX')
            severity = issue.get('severity', 'Medium')
            wcag = issue.get('wcag', 'WCAG Guideline')
            explanation = issue.get('explanation', '')
            elem = issue.get('element', '') or issue.get('html_snippet', '')
            fix = issue.get('fix', '') or issue.get('recommended_fix', '')

            # Crucial: Escape XML special characters so ReportLab's HTML/XML paraparser doesn't parse HTML tags as PDF tags
            safe_rule_name = html.escape(str(rule_name))
            safe_rule_id = html.escape(str(rule_id))
            safe_severity = html.escape(str(severity))
            safe_wcag = html.escape(str(wcag))
            safe_explanation = html.escape(str(explanation))
            safe_elem = html.escape(str(elem))
            safe_fix = html.escape(str(fix))

            issue_content = [
                Paragraph(f"<b>#{idx}. [{safe_rule_id}] {safe_rule_name}</b> &mdash; <i>{safe_severity}</i> ({safe_wcag})", styles['Heading3']),
                Paragraph(f"<b>Problem:</b> {safe_explanation}", styles['Normal']),
                Spacer(1, 3),
                Paragraph("<b>Offending HTML Snippet:</b>", styles['Normal']),
                Paragraph(safe_elem, code_style),
                Spacer(1, 3),
                Paragraph("<b>Recommended Code-Level Fix:</b>", styles['Normal']),
                Paragraph(safe_fix, code_style),
                Spacer(1, 10),
                HRFlowable(width="100%", thickness=0.25, color=colors.HexColor('#E2E8F0'), spaceAfter=10)
            ]
            story.append(KeepTogether(issue_content))

    doc.build(story)
    buffer.seek(0)
    return buffer
