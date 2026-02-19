from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, 
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime

# CloudStrike brand colors
CS_DARK    = colors.HexColor('#0f0a08')
CS_PANEL   = colors.HexColor('#1a0f0a')
CS_ORANGE  = colors.HexColor('#ff4500')
CS_ORANGE2 = colors.HexColor('#ff6b35')
CS_TEXT    = colors.HexColor('#e8e6e3')
CS_DIM     = colors.HexColor('#8a7a6a')
CS_BORDER  = colors.HexColor('#2a1f1a')

SEV_COLORS = {
    'CRITICAL': colors.HexColor('#ff0000'),
    'HIGH':     colors.HexColor('#ff4500'),
    'MEDIUM':   colors.HexColor('#ff6b35'),
    'LOW':      colors.HexColor('#888888'),
}

def generate_report(findings: list, credentials: dict, output_path: str) -> str:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    story = []

    # ── HEADER ──
    header_data = [[
        Paragraph(
            '<font color="#ff4500" size="22"><b>CLOUDSTRIKE</b></font>'
            '<br/><font color="#8a7a6a" size="9">AUTOMATED CLOUD PENTESTING &amp; SECURITY AUDITOR</font>',
            ParagraphStyle('h', fontName='Helvetica', fontSize=22)
        ),
        Paragraph(
            f'<font color="#8a7a6a" size="9">SECURITY AUDIT REPORT</font>'
            f'<br/><font color="#ff6b35" size="11"><b>{datetime.now().strftime("%d %B %Y")}</b></font>'
            f'<br/><font color="#8a7a6a" size="9">{datetime.now().strftime("%H:%M UTC")}</font>',
            ParagraphStyle('hr', fontName='Helvetica', fontSize=9, alignment=TA_RIGHT)
        )
    ]]
    header_table = Table(header_data, colWidths=[100*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CS_DARK),
        ('TEXTCOLOR',  (0,0), (-1,-1), CS_TEXT),
        ('PADDING',    (0,0), (-1,-1), 12),
        ('LINEBELOW',  (0,0), (-1,-1), 2, CS_ORANGE),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # ── EXECUTIVE SUMMARY ──
    story.append(Paragraph(
        '<font color="#ff4500"><b>EXECUTIVE SUMMARY</b></font>',
        ParagraphStyle('s', fontName='Helvetica-Bold', fontSize=11,
                      textColor=CS_ORANGE, spaceAfter=4)
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=CS_BORDER))
    story.append(Spacer(1, 4*mm))

    # Count severities
    counts = {'CRITICAL':0,'HIGH':0,'MEDIUM':0,'LOW':0}
    for f in findings:
        counts[f.get('severity','LOW')] = counts.get(f.get('severity','LOW'),0) + 1

    total = len(findings)
    risk_score = min(100, counts['CRITICAL']*15 + counts['HIGH']*8 + counts['MEDIUM']*3 + counts['LOW']*1)
    risk_label = 'CRITICAL' if risk_score >= 70 else 'HIGH' if risk_score >= 40 else 'MEDIUM' if risk_score >= 20 else 'LOW'
    risk_color = SEV_COLORS.get(risk_label, colors.HexColor('#28c840'))

    summary_data = [
        ['ACCOUNT', credentials.get('account_name', 'N/A')],
        ['CLOUD PROVIDER', 'Amazon Web Services (AWS)'],
        ['REGION SCANNED', credentials.get('region', 'us-east-1')],
        ['SCAN DATE', datetime.now().strftime('%Y-%m-%d %H:%M UTC')],
        ['TOTAL FINDINGS', str(total)],
        ['RISK SCORE', f'{risk_score}/100 — {risk_label}'],
    ]
    summary_table = Table(summary_data, colWidths=[50*mm, 130*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), CS_PANEL),
        ('BACKGROUND', (1,0), (1,-1), CS_DARK),
        ('TEXTCOLOR',  (0,0), (0,-1), CS_DIM),
        ('TEXTCOLOR',  (1,0), (1,-1), CS_TEXT),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('PADDING',    (0,0), (-1,-1), 8),
        ('GRID',       (0,0), (-1,-1), 0.5, CS_BORDER),
        ('TEXTCOLOR',  (1,5), (1,5), risk_color),
        ('FONTNAME',   (1,5), (1,5), 'Helvetica-Bold'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6*mm))

    # ── SEVERITY BREAKDOWN ──
    story.append(Paragraph(
        '<font color="#ff4500"><b>SEVERITY BREAKDOWN</b></font>',
        ParagraphStyle('s2', fontName='Helvetica-Bold', fontSize=11,
                      textColor=CS_ORANGE, spaceAfter=4)
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=CS_BORDER))
    story.append(Spacer(1, 4*mm))

    sev_data = [['SEVERITY', 'COUNT', 'PERCENTAGE']]
    for sev in ['CRITICAL','HIGH','MEDIUM','LOW']:
        count = counts[sev]
        pct = f'{(count/total*100):.1f}%' if total > 0 else '0%'
        sev_data.append([sev, str(count), pct])

    sev_table = Table(sev_data, colWidths=[60*mm, 40*mm, 80*mm])
    sev_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CS_PANEL),
        ('TEXTCOLOR',  (0,0), (-1,0), CS_ORANGE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,1), (-1,-1), CS_DARK),
        ('TEXTCOLOR',  (0,1), (-1,-1), CS_TEXT),
        ('GRID',       (0,0), (-1,-1), 0.5, CS_BORDER),
        ('PADDING',    (0,0), (-1,-1), 8),
        ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
    ])
    for i, sev in enumerate(['CRITICAL','HIGH','MEDIUM','LOW'], 1):
        sev_style.add('TEXTCOLOR', (0,i), (0,i), SEV_COLORS[sev])
        sev_style.add('FONTNAME',  (0,i), (0,i), 'Helvetica-Bold')
    sev_table.setStyle(sev_style)
    story.append(sev_table)
    story.append(Spacer(1, 8*mm))

    # ── DETAILED FINDINGS ──
    story.append(Paragraph(
        '<font color="#ff4500"><b>DETAILED FINDINGS</b></font>',
        ParagraphStyle('s3', fontName='Helvetica-Bold', fontSize=11,
                      textColor=CS_ORANGE, spaceAfter=4)
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=CS_BORDER))
    story.append(Spacer(1, 4*mm))

    # Sort by severity
    sev_order = {'CRITICAL':0,'HIGH':1,'MEDIUM':2,'LOW':3}
    sorted_findings = sorted(findings, key=lambda x: sev_order.get(x.get('severity','LOW'),4))

    findings_data = [['#', 'SEV', 'FINDING', 'SERVICE', 'REGION']]
    for i, f in enumerate(sorted_findings, 1):
        findings_data.append([
            str(i),
            f.get('severity','N/A'),
            Paragraph(f.get('title','N/A'),
                ParagraphStyle('ft', fontName='Helvetica', fontSize=8, textColor=CS_TEXT)),
            f.get('service','N/A'),
            f.get('region','N/A'),
        ])

    findings_table = Table(
        findings_data,
        colWidths=[10*mm, 22*mm, 80*mm, 22*mm, 26*mm]
    )
    f_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CS_PANEL),
        ('TEXTCOLOR',  (0,0), (-1,0), CS_ORANGE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), CS_DARK),
        ('TEXTCOLOR',  (0,1), (-1,-1), CS_TEXT),
        ('GRID',       (0,0), (-1,-1), 0.5, CS_BORDER),
        ('PADDING',    (0,0), (-1,-1), 6),
        ('ALIGN',      (0,0), (1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [CS_DARK, CS_PANEL]),
    ])
    for i, f in enumerate(sorted_findings, 1):
        sev = f.get('severity','LOW')
        f_style.add('TEXTCOLOR', (1,i), (1,i), SEV_COLORS.get(sev, CS_DIM))
        f_style.add('FONTNAME',  (1,i), (1,i), 'Helvetica-Bold')
    findings_table.setStyle(f_style)
    story.append(findings_table)
    story.append(Spacer(1, 8*mm))

    # ── REMEDIATION SECTION ──
    story.append(Paragraph(
        '<font color="#ff4500"><b>REMEDIATION COMMANDS</b></font>',
        ParagraphStyle('s4', fontName='Helvetica-Bold', fontSize=11,
                      textColor=CS_ORANGE, spaceAfter=4)
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=CS_BORDER))
    story.append(Spacer(1, 4*mm))

    critical_findings = [f for f in sorted_findings 
                        if f.get('severity') in ['CRITICAL','HIGH']]
    
    for i, f in enumerate(critical_findings, 1):
        sev_color = SEV_COLORS[f.get('severity','HIGH')]
        story.append(Paragraph(
            f'<font color="{sev_color.hexval()}"><b>{i}. {f.get("title","")}</b></font>',
            ParagraphStyle('rt', fontName='Helvetica-Bold', fontSize=9, textColor=CS_ORANGE)
        ))
        story.append(Paragraph(
            f.get('description',''),
            ParagraphStyle('rd', fontName='Helvetica', fontSize=8, 
                          textColor=CS_DIM, spaceAfter=3)
        ))
        rem_data = [[
            Paragraph(
                f'<font color="#ff6b35" size="8">{f.get("remediation","N/A")}</font>',
                ParagraphStyle('rc', fontName='Courier', fontSize=7, textColor=CS_ORANGE2)
            )
        ]]
        rem_table = Table(rem_data, colWidths=[180*mm])
        rem_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CS_PANEL),
            ('GRID',       (0,0), (-1,-1), 1, CS_ORANGE),
            ('PADDING',    (0,0), (-1,-1), 8),
        ]))
        story.append(rem_table)
        story.append(Spacer(1, 4*mm))

    # ── FOOTER ──
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width='100%', thickness=1, color=CS_ORANGE))
    story.append(Paragraph(
        '<font color="#8a7a6a" size="8">Generated by CloudStrike v1.0 — Automated Cloud Pentesting &amp; Security Auditor | CONFIDENTIAL</font>',
        ParagraphStyle('ft', fontName='Helvetica', fontSize=8, 
                      textColor=CS_DIM, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path
