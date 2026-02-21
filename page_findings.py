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
        
        self.findings_data = []
        
        frame_layout.addWidget(self.table)
        layout.addWidget(frame)
    
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
        
        sev = finding.get('severity', 'LOW').upper()
        severity_item = QTableWidgetItem(sev)
        severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        severity_item.setForeground(QColor(severity_colors.get(sev, '#888')))
        
        # Standardized dynamic status based on severity
        if sev in ['CRITICAL', 'HIGH']:
            status = 'OPEN'
            status_color = severity_colors.get(sev, '#ff0000')
        elif sev == 'MEDIUM':
            status = 'IN PROGRESS'
            status_color = '#ff6b35'
        else:
            status = 'MONITORED'
            status_color = '#888888'
        
        self.table.setItem(row, 0, severity_item)
        self.table.setItem(row, 1, QTableWidgetItem(finding.get('title', '')))
        self.table.setItem(row, 2, QTableWidgetItem(finding.get('service', '')))
        self.table.setItem(row, 3, QTableWidgetItem(finding.get('region', '')))
        
        # Set status with color
        status_item = QTableWidgetItem(status)
        status_item.setForeground(QColor(status_color))
        self.table.setItem(row, 4, status_item)
        
        # Store full finding data for detail panel
        title_item = self.table.item(row, 1)
        if title_item:
            title_item.setData(256, finding)  # Qt.UserRole = 256
    
    def clear_findings(self):
        """Clear all findings before new scan"""
        self.table.setRowCount(0)
        self.findings_data = []
    
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
