from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QScrollArea, QDialog, QPushButton)
from PyQt6.QtCore import Qt

class FindingDetailDialog(QDialog):
    def __init__(self, finding, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Finding Details")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel(finding['title'])
        title.setObjectName("dialogTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Severity
        severity_layout = QHBoxLayout()
        severity_label = QLabel("Severity:")
        severity_label.setObjectName("dialogLabel")
        severity_value = QLabel(finding['severity'].upper())
        severity_value.setObjectName(f"severity{finding['severity'].title()}")
        severity_layout.addWidget(severity_label)
        severity_layout.addWidget(severity_value)
        severity_layout.addStretch()
        layout.addLayout(severity_layout)
        
        # Resource
        resource_layout = QHBoxLayout()
        resource_label = QLabel("Affected Resource:")
        resource_label.setObjectName("dialogLabel")
        resource_value = QLabel(finding['resource'])
        resource_value.setObjectName("dialogValue")
        resource_value.setWordWrap(True)
        resource_layout.addWidget(resource_label)
        resource_layout.addWidget(resource_value, 1)
        layout.addLayout(resource_layout)
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setObjectName("dialogLabel")
        layout.addWidget(desc_label)
        
        desc_value = QLabel(finding['description'])
        desc_value.setObjectName("dialogValue")
        desc_value.setWordWrap(True)
        layout.addWidget(desc_value)
        
        # Recommended Fix
        fix_label = QLabel("Recommended Fix:")
        fix_label.setObjectName("dialogLabel")
        layout.addWidget(fix_label)
        
        fix_value = QLabel(finding['fix'])
        fix_value.setObjectName("dialogValue")
        fix_value.setWordWrap(True)
        layout.addWidget(fix_value)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("dialogButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setStyleSheet(self.get_dialog_style())
    
    def get_dialog_style(self):
        return """
            QDialog {
                background-color: #1a0f0a;
                border: 1px solid #2a1f1a;
            }
            #dialogTitle {
                font-size: 16px;
                font-weight: 600;
                color: #ff6b35;
            }
            #dialogLabel {
                font-size: 12px;
                font-weight: 600;
                color: #8a7a6a;
                text-transform: uppercase;
            }
            #dialogValue {
                font-size: 13px;
                color: #e8e6e3;
            }
            #dialogButton {
                background-color: #ff4500;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
            }
            #dialogButton:hover {
                background-color: #e63c00;
            }
        """

class ActivityFeedItem(QFrame):
    def __init__(self, finding):
        super().__init__()
        self.finding = finding
        self.setObjectName("activityItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        dot = QLabel("●")
        dot.setObjectName(f"severity{finding['severity'].title()}")
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        title_label = QLabel(finding['title'])
        title_label.setObjectName("activityTitle")
        
        time_label = QLabel(finding['time'])
        time_label.setObjectName("activityTime")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(time_label)
        
        layout.addWidget(dot)
        layout.addLayout(content_layout, 1)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog = FindingDetailDialog(self.finding, self)
            dialog.exec()

class ActivityFeed(QWidget):
    def __init__(self):
        super().__init__()
        
        # Activity data
        self.activities = [
            {
                'severity': 'critical',
                'title': 'S3 bucket exposed publicly',
                'time': '2 min ago',
                'resource': 'arn:aws:s3:::prod-data-bucket',
                'description': 'S3 bucket has public read access enabled, exposing sensitive data to the internet.',
                'fix': 'Remove public access by updating bucket policy and enabling Block Public Access settings.'
            },
            {
                'severity': 'high',
                'title': 'IAM policy overly permissive',
                'time': '8 min ago',
                'resource': 'arn:aws:iam::123456789012:policy/DevPolicy',
                'description': 'IAM policy grants wildcard permissions on all resources, violating least privilege principle.',
                'fix': 'Restrict policy to specific resources and actions required for the role.'
            },
            {
                'severity': 'medium',
                'title': 'Unencrypted RDS instance',
                'time': '15 min ago',
                'resource': 'arn:aws:rds:us-east-1:123456789012:db:prod-db',
                'description': 'RDS database instance does not have encryption at rest enabled.',
                'fix': 'Enable encryption by creating an encrypted snapshot and restoring to a new instance.'
            },
            {
                'severity': 'low',
                'title': 'CloudTrail logging disabled',
                'time': '23 min ago',
                'resource': 'arn:aws:cloudtrail:us-east-1:123456789012:trail/main',
                'description': 'CloudTrail is not logging API calls, reducing audit visibility.',
                'fix': 'Enable CloudTrail logging and configure log file validation.'
            },
            {
                'severity': 'critical',
                'title': 'SQL injection vulnerability',
                'time': '31 min ago',
                'resource': 'Lambda function: user-api-handler',
                'description': 'Lambda function constructs SQL queries using unsanitized user input.',
                'fix': 'Use parameterized queries or ORM to prevent SQL injection attacks.'
            },
            {
                'severity': 'high',
                'title': 'Outdated Lambda runtime',
                'time': '45 min ago',
                'resource': 'arn:aws:lambda:us-east-1:123456789012:function:auth',
                'description': 'Lambda function uses deprecated Node.js 12 runtime with known vulnerabilities.',
                'fix': 'Update to Node.js 18 or later and test for compatibility.'
            },
            {
                'severity': 'medium',
                'title': 'Security group allows 0.0.0.0/0',
                'time': '1 hr ago',
                'resource': 'sg-0a1b2c3d4e5f6g7h8',
                'description': 'Security group allows inbound SSH access from any IP address.',
                'fix': 'Restrict SSH access to specific IP ranges or use AWS Systems Manager Session Manager.'
            },
            {
                'severity': 'low',
                'title': 'MFA not enabled',
                'time': '1 hr ago',
                'resource': 'IAM user: admin@company.com',
                'description': 'Root account does not have multi-factor authentication enabled.',
                'fix': 'Enable virtual or hardware MFA device for the root account immediately.'
            },
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        for activity in self.activities:
            item = ActivityFeedItem(activity)
            layout.addWidget(item)
        
        layout.addStretch()
    
    def clear_and_reload(self, findings):
        """Called after real scan — replaces fake data with real findings"""
        # Clear existing items
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if not findings:
            return
        
        # Show ALL findings sorted by severity
        sev_order = {'CRITICAL':0,'HIGH':1,'MEDIUM':2,'LOW':3}
        sorted_findings = sorted(
            findings,
            key=lambda x: sev_order.get(x.get('severity','LOW'), 4)
        )
        
        for i, finding in enumerate(sorted_findings):
            activity = {
                'severity': finding.get('severity', 'LOW').lower(),
                'title': finding.get('title', 'Unknown Finding'),
                'time': 'Just now' if i == 0 else f'{i} min ago',
                'resource': finding.get('resource', 'N/A'),
                'description': finding.get('description', ''),
                'fix': finding.get('fix', '')
            }
            item = ActivityFeedItem(activity)
            self.layout().addWidget(item)
        
        self.layout().addStretch()
