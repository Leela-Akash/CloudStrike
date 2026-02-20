from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                             QTextEdit, QPushButton, QDialog, QApplication)
from PyQt6.QtCore import Qt, QTimer

class FindingDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.current_finding = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        self.title_label = QLabel("SELECT A FINDING")
        self.title_label.setObjectName("panelTitle")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        self.severity_label = QLabel("")
        self.severity_label.setObjectName("severityBadge")
        layout.addWidget(self.severity_label)
        
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#2a1f1a;")
        layout.addWidget(sep)
        
        self.service_label = QLabel("")
        self.service_label.setObjectName("detailMeta")
        layout.addWidget(self.service_label)
        
        self.region_label = QLabel("")
        self.region_label.setObjectName("detailMeta")
        layout.addWidget(self.region_label)
        
        desc_title = QLabel("DESCRIPTION")
        desc_title.setObjectName("sectionLabel")
        layout.addWidget(desc_title)
        
        self.description_label = QLabel("")
        self.description_label.setObjectName("detailText")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        rem_title = QLabel("REMEDIATION COMMAND")
        rem_title.setObjectName("sectionLabel")
        layout.addWidget(rem_title)
        
        self.remediation_box = QTextEdit()
        self.remediation_box.setObjectName("remediationBox")
        self.remediation_box.setReadOnly(True)
        self.remediation_box.setMaximumHeight(80)
        layout.addWidget(self.remediation_box)
        
        self.copy_btn = QPushButton("📋  COPY FIX COMMAND")
        self.copy_btn.setObjectName("fixButton")
        self.copy_btn.clicked.connect(self.copy_remediation)
        self.copy_btn.setEnabled(False)
        layout.addWidget(self.copy_btn)
        
        self.steps_btn = QPushButton("📖  HOW TO FIX — STEP BY STEP")
        self.steps_btn.setObjectName("secondaryButton")
        self.steps_btn.clicked.connect(self.show_fix_steps)
        self.steps_btn.setEnabled(False)
        layout.addWidget(self.steps_btn)
        
        self.copy_status = QLabel("")
        self.copy_status.setObjectName("scanStatus")
        layout.addWidget(self.copy_status)
        
        layout.addStretch()
    
    def load(self, data):
        self.current_finding = data
        sev = data.get('severity', '')
        severity_colors = {
            'CRITICAL': '#ff0000',
            'HIGH':     '#ff4500',
            'MEDIUM':   '#ff6b35',
            'LOW':      '#888888'
        }
        color = severity_colors.get(sev, '#888')
        
        self.title_label.setText(data.get('title', ''))
        self.severity_label.setText(f"● {sev}")
        self.severity_label.setStyleSheet(f"color:{color};font-weight:bold;font-size:12px;")
        self.service_label.setText(f"Service: {data.get('service', '')}")
        self.region_label.setText(f"Region:  {data.get('region', '')}")
        self.description_label.setText(data.get('description', ''))
        self.remediation_box.setText(data.get('remediation', 'No remediation available'))
        self.copy_btn.setEnabled(True)
        self.steps_btn.setEnabled(True)
        self.copy_status.setText("")
    
    def copy_remediation(self):
        if not self.current_finding:
            return
        remediation = self.current_finding.get('remediation', '')
        clipboard = QApplication.clipboard()
        clipboard.setText(remediation)
        self.copy_status.setText("✓ Command copied to clipboard!")
        self.copy_btn.setText("✓  COPIED!")
        self.copy_btn.setStyleSheet(
            "background:#28c840;color:white;border:none;"
            "padding:8px;border-radius:4px;font-weight:bold;"
        )
        QTimer.singleShot(3000, self.reset_copy_btn)
    
    def reset_copy_btn(self):
        self.copy_btn.setText("📋  COPY FIX COMMAND")
        self.copy_btn.setStyleSheet("")
    
    def show_fix_steps(self):
        if not self.current_finding:
            return
        
        service = self.current_finding.get('service', '')
        title = self.current_finding.get('title', '')
        remediation = self.current_finding.get('remediation', '')
        
        steps = self.get_fix_steps(service, title, remediation)
        
        dialog = QDialog(self.window())
        dialog.setWindowTitle(f"How to Fix — {title[:40]}")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog { background:#1a0f0a; color:#e8e6e3; }
            QLabel { color:#e8e6e3; }
            QTextEdit {
                background:#0a0705;
                color:#e8e6e3;
                border:1px solid #2a1f1a;
                font-family:'Courier New';
                font-size:11px;
                padding:8px;
            }
            QPushButton {
                background:#ff4500;
                color:white;
                border:none;
                padding:8px 16px;
                border-radius:4px;
                font-weight:bold;
            }
        """)
        dlayout = QVBoxLayout(dialog)
        
        title_lbl = QLabel(f"FIX: {title}")
        title_lbl.setStyleSheet("color:#ff4500;font-weight:bold;font-size:13px;")
        title_lbl.setWordWrap(True)
        dlayout.addWidget(title_lbl)
        
        steps_box = QTextEdit()
        steps_box.setReadOnly(True)
        steps_box.setText(steps)
        dlayout.addWidget(steps_box)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        dlayout.addWidget(close_btn)
        
        dialog.exec()
    
    def get_fix_steps(self, service, title, remediation):
        if service == 'S3':
            return (
                "STEP 1 — Open AWS Console\n"
                "  Go to: https://s3.console.aws.amazon.com\n\n"
                "STEP 2 — Find the affected bucket\n"
                "  Click on the bucket name shown in the finding\n\n"
                "STEP 3 — Go to Permissions tab\n"
                "  Click 'Permissions' in the bucket menu\n\n"
                "STEP 4 — Block Public Access\n"
                "  Click 'Edit' under Block Public Access\n"
                "  Enable all 4 checkboxes\n"
                "  Click Save\n\n"
                "STEP 5 — OR run this CLI command:\n"
                f"  {remediation}\n\n"
                "STEP 6 — Verify\n"
                "  Re-run CloudStrike scan to confirm fix"
            )
        elif service == 'IAM':
            return (
                "STEP 1 — Open AWS Console\n"
                "  Go to: https://console.aws.amazon.com/iam\n\n"
                "STEP 2 — Navigate to Users\n"
                "  Click 'Users' in left sidebar\n\n"
                "STEP 3 — Select the affected user\n"
                "  Click on the username shown in the finding\n\n"
                "STEP 4 — Enable MFA\n"
                "  Click 'Security credentials' tab\n"
                "  Click 'Assign MFA device'\n"
                "  Follow the setup wizard\n\n"
                "STEP 5 — OR run this CLI command:\n"
                f"  {remediation}\n\n"
                "STEP 6 — Verify\n"
                "  Re-run CloudStrike scan to confirm fix"
            )
        elif service == 'EC2':
            return (
                "STEP 1 — Open AWS Console\n"
                "  Go to: https://console.aws.amazon.com/ec2\n\n"
                "STEP 2 — Go to Security Groups\n"
                "  Click 'Security Groups' under Network & Security\n\n"
                "STEP 3 — Find the affected security group\n"
                "  Look for the group name shown in the finding\n\n"
                "STEP 4 — Edit Inbound Rules\n"
                "  Click 'Edit inbound rules'\n"
                "  Remove the rule with 0.0.0.0/0\n"
                "  Replace with specific IP range\n"
                "  Click Save rules\n\n"
                "STEP 5 — OR run this CLI command:\n"
                f"  {remediation}\n\n"
                "STEP 6 — Verify\n"
                "  Re-run CloudStrike scan to confirm fix"
            )
        elif service == 'CloudTrail':
            return (
                "STEP 1 — Open AWS Console\n"
                "  Go to: https://console.aws.amazon.com/cloudtrail\n\n"
                "STEP 2 — Create or enable trail\n"
                "  Click 'Create trail' if none exists\n"
                "  Or click existing trail and enable logging\n\n"
                "STEP 3 — Configure trail\n"
                "  Enable for all regions\n"
                "  Enable log file validation\n"
                "  Set S3 bucket for log storage\n\n"
                "STEP 4 — OR run this CLI command:\n"
                f"  {remediation}\n\n"
                "STEP 5 — Verify\n"
                "  Re-run CloudStrike scan to confirm fix"
            )
        elif service == 'RDS':
            return (
                "STEP 1 — Open AWS Console\n"
                "  Go to: https://console.aws.amazon.com/rds\n\n"
                "STEP 2 — Find affected database\n"
                "  Click 'Databases' in left sidebar\n\n"
                "STEP 3 — Modify the instance\n"
                "  Select the database\n"
                "  Click 'Modify'\n\n"
                "STEP 4 — Disable public access\n"
                "  Set 'Public access' to No\n"
                "  Click Continue and Apply\n\n"
                "STEP 5 — OR run this CLI command:\n"
                f"  {remediation}\n\n"
                "STEP 6 — Verify\n"
                "  Re-run CloudStrike scan to confirm fix"
            )
        else:
            return (
                "STEP 1 — Review the finding details above\n\n"
                "STEP 2 — Run the remediation command:\n"
                f"  {remediation}\n\n"
                "STEP 3 — Verify the fix\n"
                "  Re-run CloudStrike scan to confirm finding is resolved"
            )

class IncidentDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        self.title_label = QLabel("INCIDENT LOG")
        self.title_label.setObjectName("panelTitle")
        layout.addWidget(self.title_label)
        
        scroll = QScrollArea()
        scroll.setObjectName("activityScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def load(self, data):
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add incident name
        name_label = QLabel(data.get('name', 'Unknown Incident'))
        name_label.setObjectName("detailValue")
        name_label.setWordWrap(True)
        self.content_layout.addWidget(name_label)
        
        # Add steps
        for step in data.get('steps', []):
            step_frame = QFrame()
            step_frame.setObjectName("activityItem")
            step_layout = QVBoxLayout(step_frame)
            step_layout.setContentsMargins(8, 6, 8, 6)
            
            step_label = QLabel(step)
            step_label.setObjectName("activityTitle")
            step_label.setWordWrap(True)
            step_layout.addWidget(step_label)
            
            self.content_layout.addWidget(step_frame)
        
        self.content_layout.addStretch()
