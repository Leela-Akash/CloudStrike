from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QFrame
from settings_manager import save_setting, get_all_settings

class IntegrationsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        frame = QFrame()
        frame.setObjectName("mapFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("SCAN CONFIGURATION")
        title.setObjectName("panelTitle")
        frame_layout.addWidget(title)
        
        depth_label = QLabel("Scan Depth")
        depth_label.setObjectName("settingsLabel")
        frame_layout.addWidget(depth_label)
        
        self.depth_combo = QComboBox()
        self.depth_combo.setObjectName("settingsCombo")
        self.depth_combo.addItems(["Quick (5 min)", "Standard (15 min)", "Deep (45 min)"])
        frame_layout.addWidget(self.depth_combo)
        
        regions_label = QLabel("AWS Regions")
        regions_label.setObjectName("settingsLabel")
        frame_layout.addWidget(regions_label)
        
        self.region_checks = {}
        for region in ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2", "ap-southeast-1", "ca-central-1"]:
            cb = QCheckBox(region)
            cb.setObjectName("settingsCheckbox")
            self.region_checks[region] = cb
            frame_layout.addWidget(cb)
        
        frame_layout.addSpacing(16)
        notif_label = QLabel("NOTIFICATION SETTINGS")
        notif_label.setObjectName("sectionLabel")
        frame_layout.addWidget(notif_label)
        
        self.notify_critical = QCheckBox("Alert on Critical findings")
        self.notify_high = QCheckBox("Alert on High findings")
        self.notify_scan_done = QCheckBox("Notify when scan completes")
        
        for cb in [self.notify_critical, self.notify_high, self.notify_scan_done]:
            frame_layout.addWidget(cb)
        
        frame_layout.addSpacing(16)
        report_label = QLabel("REPORT SETTINGS")
        report_label.setObjectName("sectionLabel")
        frame_layout.addWidget(report_label)
        
        self.auto_pdf = QCheckBox("Auto-generate PDF after each scan")
        self.include_low = QCheckBox("Include LOW severity in reports")
        frame_layout.addWidget(self.auto_pdf)
        frame_layout.addWidget(self.include_low)
        
        frame_layout.addStretch()
        
        save_btn = QPushButton("SAVE SETTINGS")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_settings)
        frame_layout.addWidget(save_btn)
        
        self.status_label = QLabel("")
        self.status_label.setObjectName("scanStatus")
        frame_layout.addWidget(self.status_label)
        
        layout.addWidget(frame)
        
        self.load_settings()
    
    def load_settings(self):
        s = get_all_settings()
        idx = self.depth_combo.findText(s['scan_depth'])
        if idx >= 0:
            self.depth_combo.setCurrentIndex(idx)
        for region, cb in self.region_checks.items():
            cb.setChecked(region in s['regions'])
        self.notify_critical.setChecked(s['notify_critical'])
        self.notify_high.setChecked(s['notify_high'])
        self.notify_scan_done.setChecked(s['notify_scan_done'])
        self.auto_pdf.setChecked(s['auto_pdf'])
        self.include_low.setChecked(s['include_low'])
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_settings()
    
    def save_settings(self):
        save_setting('scan_depth', self.depth_combo.currentText())
        save_setting('regions', [r for r, cb in self.region_checks.items() if cb.isChecked()])
        save_setting('notify_critical', self.notify_critical.isChecked())
        save_setting('notify_high', self.notify_high.isChecked())
        save_setting('notify_scan_done', self.notify_scan_done.isChecked())
        save_setting('auto_pdf', self.auto_pdf.isChecked())
        save_setting('include_low', self.include_low.isChecked())
        self.status_label.setText("✓ Settings saved successfully")
