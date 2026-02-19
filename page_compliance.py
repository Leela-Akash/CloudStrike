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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Control ID", "Description", "Status", "Score"])
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
            
            score = "100%" if status == "PASS" else "0%"
            self.table.setItem(row, 3, QTableWidgetItem(score))
        
        frame_layout.addWidget(self.table)
        layout.addWidget(frame)
