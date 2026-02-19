from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class FindingsPage(QWidget):
    finding_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        frame = QFrame()
        frame.setObjectName("mapFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("SECURITY FINDINGS")
        title.setObjectName("panelTitle")
        frame_layout.addWidget(title)
        
        # Scan Again button - smaller and left-aligned
        btn_layout = QHBoxLayout()
        scan_again_btn = QPushButton("↺  SCAN AGAIN")
        scan_again_btn.setObjectName("secondaryButton")
        scan_again_btn.setFixedWidth(160)
        scan_again_btn.clicked.connect(lambda: self.window().switch_page("Vault"))
        btn_layout.addWidget(scan_again_btn)
        btn_layout.addStretch()
        frame_layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setObjectName("findingsTable")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Severity", "Finding", "Service", "Region", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        self.findings_data = [
            {"severity": "Critical", "finding": "S3 bucket exposed publicly", "service": "S3", "region": "us-east-1", "status": "Open", "resource": "arn:aws:s3:::prod-data-bucket", "description": "S3 bucket has public read access enabled, exposing sensitive data.", "fix": "aws s3api put-public-access-block --bucket prod-data-bucket --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"},
            {"severity": "High", "finding": "IAM policy overly permissive", "service": "IAM", "region": "Global", "status": "Open", "resource": "arn:aws:iam::123456789012:policy/DevPolicy", "description": "IAM policy grants wildcard permissions on all resources.", "fix": "aws iam delete-policy-version --policy-arn arn:aws:iam::123456789012:policy/DevPolicy --version-id v1"},
            {"severity": "Critical", "finding": "SQL injection vulnerability", "service": "Lambda", "region": "us-east-1", "status": "Open", "resource": "user-api-handler", "description": "Lambda function constructs SQL queries using unsanitized user input.", "fix": "# Update code to use parameterized queries\n# Deploy: aws lambda update-function-code --function-name user-api-handler --zip-file fileb://function.zip"},
            {"severity": "High", "finding": "Unencrypted RDS instance", "service": "RDS", "region": "us-east-1", "status": "In Progress", "resource": "prod-db", "description": "RDS database instance does not have encryption at rest enabled.", "fix": "aws rds create-db-snapshot --db-instance-identifier prod-db --db-snapshot-identifier prod-db-snapshot\naws rds restore-db-instance-from-db-snapshot --db-instance-identifier prod-db-encrypted --db-snapshot-identifier prod-db-snapshot --storage-encrypted"},
            {"severity": "Medium", "finding": "Security group allows 0.0.0.0/0", "service": "EC2", "region": "us-west-2", "status": "Open", "resource": "sg-0a1b2c3d4e5f6g7h8", "description": "Security group allows inbound SSH access from any IP address.", "fix": "aws ec2 revoke-security-group-ingress --group-id sg-0a1b2c3d4e5f6g7h8 --protocol tcp --port 22 --cidr 0.0.0.0/0"},
            {"severity": "High", "finding": "Outdated Lambda runtime", "service": "Lambda", "region": "eu-west-1", "status": "Open", "resource": "auth-function", "description": "Lambda function uses deprecated Node.js 12 runtime.", "fix": "aws lambda update-function-configuration --function-name auth-function --runtime nodejs18.x"},
            {"severity": "Low", "finding": "CloudTrail logging disabled", "service": "CloudTrail", "region": "ap-south-1", "status": "Resolved", "resource": "main-trail", "description": "CloudTrail is not logging API calls.", "fix": "aws cloudtrail start-logging --name main-trail"},
            {"severity": "Medium", "finding": "MFA not enabled", "service": "IAM", "region": "Global", "status": "Open", "resource": "root account", "description": "Root account does not have multi-factor authentication enabled.", "fix": "# Enable MFA via AWS Console: IAM > Security Credentials > Assign MFA device"},
        ]
        
        self.populate_table()
        frame_layout.addWidget(self.table)
        layout.addWidget(frame)
    
    def populate_table(self):
        self.table.setRowCount(len(self.findings_data))
        for row, finding in enumerate(self.findings_data):
            severity_item = QTableWidgetItem(finding["severity"])
            severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if finding["severity"] == "Critical":
                severity_item.setForeground(Qt.GlobalColor.red)
            elif finding["severity"] == "High":
                severity_item.setForeground(Qt.GlobalColor.darkYellow)
            
            self.table.setItem(row, 0, severity_item)
            self.table.setItem(row, 1, QTableWidgetItem(finding["finding"]))
            self.table.setItem(row, 2, QTableWidgetItem(finding["service"]))
            self.table.setItem(row, 3, QTableWidgetItem(finding["region"]))
            self.table.setItem(row, 4, QTableWidgetItem(finding["status"]))
    
    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            self.finding_selected.emit(self.findings_data[row])
    
    def add_finding(self, finding):
        self.findings_data.append(finding)
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Color code severity
        severity_colors = {
            'CRITICAL': '#ff0000',
            'HIGH':     '#ff4500',
            'MEDIUM':   '#ff6b35',
            'LOW':      '#888888'
        }
        
        from PyQt6.QtGui import QColor
        
        severity_item = QTableWidgetItem(finding.get('severity', 'UNKNOWN'))
        severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        severity_item.setForeground(QColor(severity_colors.get(finding.get('severity'), '#888')))
        
        self.table.setItem(row, 0, severity_item)
        self.table.setItem(row, 1, QTableWidgetItem(finding.get('title', '')))
        self.table.setItem(row, 2, QTableWidgetItem(finding.get('service', '')))
        self.table.setItem(row, 3, QTableWidgetItem(finding.get('region', '')))
        self.table.setItem(row, 4, QTableWidgetItem(finding.get('status', 'OPEN')))
        
        # Store full finding data for detail panel
        title_item = self.table.item(row, 1)
        if title_item:
            title_item.setData(256, finding)  # Qt.UserRole = 256
    
    def get_findings(self):
        findings = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item:
                data = item.data(256)
                if data:
                    findings.append(data)
                else:
                    findings.append({
                        'severity':    self.table.item(row,0).text() if self.table.item(row,0) else '',
                        'title':       self.table.item(row,1).text() if self.table.item(row,1) else '',
                        'service':     self.table.item(row,2).text() if self.table.item(row,2) else '',
                        'region':      self.table.item(row,3).text() if self.table.item(row,3) else '',
                        'description': 'See full report.',
                        'remediation': 'See CloudStrike remediation guide.'
                    })
        return findings
