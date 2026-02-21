from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from threat_map import ThreatMap
from scan_activity_chart import ScanActivityChart

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Demo mode banner (hidden by default)
        self.demo_banner = QLabel("⚠  DEMO MODE — Showing sample data. Connect credentials in Vault to scan real accounts.")
        self.demo_banner.setObjectName("demoBanner")
        self.demo_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.demo_banner.hide()
        layout.addWidget(self.demo_banner)
        
        # Main content container
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        map_frame = QFrame()
        map_frame.setObjectName("mapFrame")
        map_layout = QVBoxLayout(map_frame)
        map_layout.setContentsMargins(16, 16, 16, 16)
        map_label = QLabel("THREAT MAP")
        map_label.setObjectName("panelTitle")
        map_layout.addWidget(map_label)
        
        self.threat_map = ThreatMap()
        map_layout.addWidget(self.threat_map, 1)
        
        chart_frame = QFrame()
        chart_frame.setObjectName("chartFrame")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        chart_label = QLabel("SCAN ACTIVITY")
        chart_label.setObjectName("panelTitle")
        chart_layout.addWidget(chart_label)
        
        self.scan_chart = ScanActivityChart()
        chart_layout.addWidget(self.scan_chart, 1)
        
        content_layout.addWidget(map_frame, 3)
        content_layout.addWidget(chart_frame, 2)
        
        layout.addWidget(content)
    
    def show_demo_banner(self):
        self.demo_banner.show()
