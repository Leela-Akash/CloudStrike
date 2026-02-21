from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QFrame
from PyQt6.QtCore import Qt

class CompliancePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        frame = QFrame()
        frame.setObjectName("mapFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("COMPLIANCE CHECKLIST - CIS AWS FOUNDATIONS")
        title.setObjectName("panelTitle")
        frame_layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setObjectName("findingsTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Control ID", "Description", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        cis_checks = [
            ('1.1',  'Avoid use of root account',           'IAM',        'PASS'),
            ('1.2',  'MFA enabled for all IAM users',        'IAM',        'FAIL'),
            ('1.3',  'Credentials unused 90+ days disabled', 'IAM',        'PASS'),
            ('1.4',  'Access keys rotated every 90 days',    'IAM',        'FAIL'),
            ('2.1',  'CloudTrail enabled all regions',       'CloudTrail', 'FAIL'),
            ('2.2',  'CloudTrail log file validation',       'CloudTrail', 'PASS'),
            ('3.1',  'No unauthorized API calls',            'CloudWatch', 'PASS'),
            ('4.1',  'No unrestricted SSH access',           'EC2',        'FAIL'),
            ('4.2',  'No unrestricted RDP access',           'EC2',        'PASS'),
            ('4.3',  'VPC flow logging enabled',             'VPC',        'FAIL'),
            ('5.1',  'S3 no public read access',             'S3',         'FAIL'),
            ('5.2',  'S3 no public write access',            'S3',         'PASS'),
            ('5.3',  'S3 bucket logging enabled',            'S3',         'FAIL'),
        ]
        
        self.table.setRowCount(len(cis_checks))
        for row, (control_id, desc, service, status) in enumerate(cis_checks):
            self.table.setItem(row, 0, QTableWidgetItem(control_id))
            self.table.setItem(row, 1, QTableWidgetItem(desc))
            
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "PASS":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)
        
        frame_layout.addWidget(self.table)
        layout.addWidget(frame)
    
    def update_from_findings(self, findings, provider='AWS'):
        """Update compliance PASS/FAIL based on real scan findings"""
        from PyQt6.QtGui import QColor
        
        # If not AWS, show message instead of AWS-specific checks
        if provider != 'AWS':
            self.show_non_aws_message(provider)
            return
        
        # Map finding types to CIS controls
        failed_controls = set()
        
        for f in findings:
            title = f.get('title', '').lower()
            service = f.get('service', '').lower()
            
            if 'mfa' in title:
                failed_controls.add('1.2')
            if 'root' in title:
                failed_controls.add('1.1')
            if 'access key' in title or 'key rotation' in title:
                failed_controls.add('1.4')
            if 'unused' in title or 'inactive' in title:
                failed_controls.add('1.3')
            if 'cloudtrail' in title:
                failed_controls.add('2.1')
                failed_controls.add('2.2')
            if 'ssh' in title or '0.0.0.0' in title:
                failed_controls.add('4.1')
            if 'rdp' in title:
                failed_controls.add('4.2')
            if 'vpc' in title or 'flow log' in title:
                failed_controls.add('4.3')
            if 's3' in service and 'public' in title:
                failed_controls.add('5.1')
                failed_controls.add('5.2')
            if 's3' in service and 'log' in title:
                failed_controls.add('5.3')

        # Update table rows
        total = self.table.rowCount()
        passed = 0
        for row in range(total):
            control_id = self.table.item(row, 0)
            if control_id:
                cid = control_id.text()
                status_item = self.table.item(row, 2)
                if status_item:
                    if cid in failed_controls:
                        status_item.setText('FAIL')
                        status_item.setForeground(QColor('#ff0000'))
                    else:
                        status_item.setText('PASS')
                        status_item.setForeground(QColor('#28c840'))
                        passed += 1

        # Update compliance score stat card
        score = int((passed / total) * 100) if total > 0 else 0
        main = self.window()
        if main:
            from PyQt6.QtWidgets import QLabel
            labels = main.findChildren(QLabel, 'statValue')
            if len(labels) >= 3:
                labels[2].setText(f"{score}%")
    
    def show_non_aws_message(self, provider):
        """Show message when scanning non-AWS providers"""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.horizontalHeader().setVisible(False)
        
        from PyQt6.QtWidgets import QTableWidgetItem
        from PyQt6.QtCore import Qt
        
        item = QTableWidgetItem(
            f"Compliance checks are based on CIS AWS Foundations Benchmark.\n\n"
            f"Currently scanning {provider}.\n\n"
            f"Switch to AWS credentials to see compliance results."
        )
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(0, 0, item)
        self.table.setRowHeight(0, 200)
