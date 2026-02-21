import sys
import traceback
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, 
                             QSizePolicy, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import QWebEngineProfile
from page_dashboard import DashboardPage
from page_findings import FindingsPage
from page_incidents import IncidentsPage
from page_compliance import CompliancePage
from page_vault import VaultPage
from page_integrations import IntegrationsPage
from page_cve import CVEPage
from activity_feed import ActivityFeed
from detail_panels import FindingDetailPanel, IncidentDetailPanel

# Setup crash log
logging.basicConfig(
    filename='cloudstrike_crash.log',
    level=logging.DEBUG,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

# Reduce boto3 logging noise
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical(
        "UNCAUGHT EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

class StatCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, value, change, trend_up=True):
        super().__init__()
        self.setObjectName("statCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)
        
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        self.value_label = value_label  # Store reference for updates
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        
        change_label = QLabel(change)
        change_label.setObjectName("statChange")
        
        trend_label = QLabel("▲" if trend_up else "▼")
        trend_label.setObjectName("trendUp" if trend_up else "trendDown")
        
        bottom_layout.addWidget(trend_label)
        bottom_layout.addWidget(change_label)
        bottom_layout.addStretch()
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addLayout(bottom_layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

class NavButton(QPushButton):
    def __init__(self, icon_text, label):
        super().__init__()
        self.setText(f"{icon_text}\n{label}")
        self.setObjectName("navButton")
        self.setCheckable(True)

class CloudStrikeUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudStrike")
        self.setGeometry(100, 100, 1400, 900)
        
        # Load Google Fonts
        self.load_fonts()
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Left sidebar
        sidebar = self.create_sidebar()
        content_layout.addWidget(sidebar)
        
        # Center panel with QStackedWidget
        self.stack = self.create_center_panel()
        content_layout.addWidget(self.stack, 1)
        
        # Right panel with QStackedWidget
        self.right_stack = self.create_right_panel()
        content_layout.addWidget(self.right_stack)
        
        main_layout.addLayout(content_layout, 1)
        
        self.setStyleSheet(self.get_stylesheet())
        
        # Connect page signals
        self.connect_signals()
        
        # Check first launch and show appropriate page
        self.check_first_launch()
    
    def load_fonts(self):
        """Load Google Fonts for the application"""
        # Skip font download - use system fonts with fallbacks
        # Google Fonts will be used if available, otherwise fallback to system fonts
        pass
    
    def create_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(130)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        logo = QLabel("CloudStrike")
        logo.setObjectName("logo")
        logo.setFixedWidth(160)
        layout.addWidget(logo)
        
        self.stat_cards = []
        for title, value, change, up in [
            ("Open Vulnerabilities", "0", "—", True),
            ("Active Incidents", "0", "—", True),
            ("Compliance Score", "—", "—", True),
            ("Time to Remediate", "—", "—", True),
        ]:
            card = StatCard(title, value, change, up)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.stat_cards.append(card)
            layout.addWidget(card, 1)
        
        # Connect stat cards to pages
        self.stat_cards[0].clicked.connect(lambda: self.switch_page("Findings"))
        self.stat_cards[1].clicked.connect(lambda: self.switch_page("Incidents"))
        
        # Export button
        export_btn = QPushButton("⬇ EXPORT REPORT")
        export_btn.setObjectName("exportButton")
        export_btn.clicked.connect(self.export_report)
        layout.addWidget(export_btn)
        
        return top_bar
    
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(140)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)
        
        nav_items = [
            ("▣", "Dashboard"),
            ("⚑", "Findings"),
            ("⚡", "Incidents"),
            ("✦", "Compliance"),
            ("📡", "CVE Feed"),
            ("⊞", "Vault"),
            ("⚙", "Integrations")
        ]
        
        self.nav_buttons = []
        for icon, label in nav_items:
            btn = NavButton(icon, label)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)
            
            # Connect button to switch page
            page_name = label
            btn.clicked.connect(lambda checked, p=page_name: self.switch_page(p))
        
        self.nav_buttons[0].setChecked(True)
        
        layout.addStretch()
        
        profile = QFrame()
        profile.setObjectName("profile")
        profile.setFixedHeight(60)
        profile_layout = QVBoxLayout(profile)
        profile_layout.setContentsMargins(12, 8, 12, 8)
        profile_name = QLabel("Admin User")
        profile_name.setObjectName("profileName")
        profile_role = QLabel("Security Lead")
        profile_role.setObjectName("profileRole")
        profile_layout.addWidget(profile_name)
        profile_layout.addWidget(profile_role)
        layout.addWidget(profile)
        
        return sidebar
    
    def create_center_panel(self):
        stack = QStackedWidget()
        stack.setObjectName("centerPanel")
        
        self.pages = {
            "Dashboard":    DashboardPage(),
            "Findings":     FindingsPage(),
            "Incidents":    IncidentsPage(),
            "Compliance":   CompliancePage(),
            "CVE Feed":     CVEPage(),
            "Vault":        VaultPage(),
            "Integrations": IntegrationsPage()
        }
        
        for page in self.pages.values():
            stack.addWidget(page)
        
        return stack
    
    def create_right_panel(self):
        right_container = QFrame()
        right_container.setObjectName("rightPanel")
        right_container.setFixedWidth(320)
        container_layout = QVBoxLayout(right_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        right_stack = QStackedWidget()
        
        # Default activity feed
        default_widget = QWidget()
        default_layout = QVBoxLayout(default_widget)
        default_layout.setContentsMargins(20, 20, 20, 20)
        default_layout.setSpacing(12)
        
        title = QLabel("RECENT ACTIVITY")
        title.setObjectName("panelTitle")
        default_layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setObjectName("activityScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.activity_feed = ActivityFeed()
        scroll.setWidget(self.activity_feed)
        default_layout.addWidget(scroll)
        
        right_stack.addWidget(default_widget)
        
        # Finding detail panel
        self.finding_detail = FindingDetailPanel()
        right_stack.addWidget(self.finding_detail)
        
        # Incident detail panel
        self.incident_detail = IncidentDetailPanel()
        right_stack.addWidget(self.incident_detail)
        
        container_layout.addWidget(right_stack)
        
        self.right_stack_widget = right_stack
        return right_container
    
    def connect_signals(self):
        # Connect findings page signal
        self.pages["Findings"].finding_selected.connect(self.show_finding_detail)
        
        # Connect incidents page signal
        self.pages["Incidents"].incident_selected.connect(self.show_incident_detail)
        
        # Connect vault page to main window for navigation
        self.pages["Vault"].parent_window = self
    
    def check_first_launch(self):
        import sqlite3, os
        db_path = "cloudstrike_vault.db"
        
        # If no db or no credentials saved
        if not os.path.exists(db_path):
            self.switch_page("Vault")
            return
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM credentials")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                self.switch_page("Vault")
            else:
                self.switch_page("Dashboard")
        except:
            self.switch_page("Vault")
    
    def switch_page(self, page_name):
        self.stack.setCurrentWidget(self.pages[page_name])
        
        # Update nav button states
        for btn in self.nav_buttons:
            btn_label = btn.text().strip().split('\n')[-1]
            btn.setChecked(btn_label == page_name)
        
        # Reset right panel to default when switching pages
        if page_name in ["Dashboard", "Compliance", "Vault", "Integrations"]:
            self.right_stack_widget.setCurrentIndex(0)
    
    def start_scan_safe(self):
        # Pause map rendering during scan to free up network resources
        dashboard = self.pages.get("Dashboard")
        if dashboard and hasattr(dashboard, 'threat_map'):
            dashboard.threat_map.setVisible(False)
    
    def restore_after_scan(self, findings):
        # Restore map after scan completes
        dashboard = self.pages.get("Dashboard")
        if dashboard and hasattr(dashboard, 'threat_map'):
            dashboard.threat_map.setVisible(True)
        # Update stat cards with real data
        self.update_stat_cards(findings)
        self.switch_page("Findings")
    
    def update_stat_cards(self, findings):
        """Update dashboard stat cards with real scan data"""
        counts = {'CRITICAL':0, 'HIGH':0, 'MEDIUM':0, 'LOW':0}
        for f in findings:
            sev = f.get('severity', 'LOW').upper()
            counts[sev] = counts.get(sev, 0) + 1

        total = len(findings)
        critical_high = counts['CRITICAL'] + counts['HIGH']

        # Directly update stat card value labels by object name
        from PyQt6.QtWidgets import QLabel
        all_labels = self.findChildren(QLabel, 'statValue')
        if len(all_labels) >= 1:
            all_labels[0].setText(str(total))
        if len(all_labels) >= 2:
            all_labels[1].setText(str(critical_high))
        
        # Calculate and update remediation time
        self.calculate_remediation_time(findings)
    
    def calculate_remediation_time(self, findings):
        """Calculate estimated time to remediate all findings"""
        hours = 0
        for f in findings:
            sev = f.get('severity', 'LOW')
            if sev == 'CRITICAL':   hours += 4
            elif sev == 'HIGH':     hours += 2
            elif sev == 'MEDIUM':   hours += 1
            elif sev == 'LOW':      hours += 0.5
        
        # Find Time to Remediate stat card (index 3)
        from PyQt6.QtWidgets import QLabel
        labels = self.findChildren(QLabel, 'statValue')
        if len(labels) >= 4:
            if hours < 24:
                labels[3].setText(f"{hours:.1f}h")
            else:
                days = hours / 8  # 8 hour work day
                labels[3].setText(f"{days:.1f}d")
    
    def show_finding_detail(self, finding_data):
        self.finding_detail.load(finding_data)
        self.right_stack_widget.setCurrentWidget(self.finding_detail)
    
    def show_incident_detail(self, incident_data):
        self.incident_detail.load(incident_data)
        self.right_stack_widget.setCurrentWidget(self.incident_detail)
    
    def export_report(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from report_generator import generate_report
        import sqlite3
        from datetime import datetime

        findings_page = self.pages.get("Findings")
        if not findings_page:
            return

        findings = findings_page.get_findings()

        if not findings:
            QMessageBox.information(self, "No Findings",
                "Run a scan first before exporting.")
            return

        credentials = {'account_name': 'AWS Account', 'region': 'us-east-1'}
        try:
            conn = sqlite3.connect("cloudstrike_vault.db")
            row = conn.execute("SELECT * FROM credentials LIMIT 1").fetchone()
            conn.close()
            if row:
                credentials = {'account_name': row[2], 'region': row[5]}
        except: pass

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report",
            f"CloudStrike_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            try:
                generate_report(findings, credentials, path)
                QMessageBox.information(self, "✓ Report Exported",
                    f"Saved to:\n{path}")
                import subprocess
                subprocess.Popen(['start', '', path], shell=True)
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
    
    def get_stylesheet(self):
        return """
            * {
                font-family: 'Rajdhani', 'Segoe UI', Arial, sans-serif;
                color: #e8e6e3;
            }
            
            QMainWindow {
                background-color: #1a0f0a;
            }
            
            #topBar {
                background-color: #0f0a08;
                border-bottom: 1px solid #2a1f1a;
            }
            
            #logo {
                font-size: 24px;
                font-weight: bold;
                color: #ff4500;
                padding-right: 20px;
                font-family: 'Orbitron', 'Segoe UI';
            }
            
            #statCard {
                background-color: #1a0f0a;
                border: 1px solid #2a1f1a;
                border-radius: 6px;
                padding: 8px;
            }
            
            #statCard:hover {
                border-color: #ff4500;
                background-color: #1f1410;
            }
            
            #statTitle {
                font-size: 11px;
                color: #8a7a6a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            #statValue {
                font-size: 26px;
                font-weight: 600;
                color: #ff6b35;
                font-family: 'Orbitron', 'Segoe UI';
            }
            
            #statChange {
                font-size: 12px;
                color: #8a7a6a;
            }
            
            #trendUp {
                color: #4ade80;
                font-size: 10px;
            }
            
            #trendDown {
                color: #ff4500;
                font-size: 10px;
            }
            
            #sidebar {
                background-color: #0f0a08;
                border-right: 1px solid #2a1f1a;
            }
            
            #navButton {
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding: 12px 16px;
                font-size: 11px;
                color: #8a7a6a;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }
            
            #navButton:hover {
                background-color: #1a0f0a;
                color: #ff6b35;
            }
            
            #navButton:checked {
                background-color: #1a0f0a;
                border-left: 3px solid #ff4500;
                color: #ff4500;
            }
            
            #profile {
                background-color: #1a0f0a;
                border-top: 1px solid #2a1f1a;
                margin: 0 8px;
            }
            
            #profileName {
                font-size: 13px;
                color: #e8e6e3;
                font-weight: 500;
            }
            
            #profileRole {
                font-size: 11px;
                color: #8a7a6a;
            }
            
            #centerPanel {
                background-color: #1a0f0a;
            }
            
            #mapFrame, #chartFrame {
                background-color: #0f0a08;
                border: 1px solid #2a1f1a;
                border-radius: 6px;
                padding: 16px;
            }
            
            #rightPanel {
                background-color: #0f0a08;
                border-left: 1px solid #2a1f1a;
            }
            
            #panelTitle {
                font-size: 11px;
                font-weight: 600;
                color: #8a7a6a;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
                font-family: 'Orbitron', 'Segoe UI';
            }
            
            #activityScroll {
                background-color: transparent;
                border: none;
            }
            
            #activityItem {
                background-color: #1a0f0a;
                border: 1px solid #2a1f1a;
                border-radius: 4px;
            }
            
            #activityItem:hover {
                background-color: #1f1410;
                border-color: #3a2f2a;
            }
            
            #activityTitle {
                font-size: 13px;
                color: #e8e6e3;
                font-weight: 500;
            }
            
            #activityTime {
                font-size: 11px;
                color: #6a5a4a;
            }
            
            #severityCritical {
                color: #e63c00;
                font-size: 16px;
            }
            
            #severityHigh {
                color: #ff4500;
                font-size: 16px;
            }
            
            #severityMedium {
                color: #ff6b35;
                font-size: 16px;
            }
            
            #severityLow {
                color: #8a7a6a;
                font-size: 16px;
            }
            
            QTableWidget {
                background-color: #0f0a08;
                border: 1px solid #2a1f1a;
                gridline-color: #2a1f1a;
                color: #e8e6e3;
            }
            
            QTableWidget::item {
                padding: 6px;
            }
            
            QTableWidget::item:selected {
                background-color: #2a1f1a;
                color: #ff6b35;
            }
            
            QHeaderView::section {
                background-color: #1a0f0a;
                color: #8a7a6a;
                border: none;
                padding: 8px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            QListWidget {
                background-color: #0f0a08;
                border: 1px solid #2a1f1a;
                color: #e8e6e3;
            }
            
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #2a1f1a;
            }
            
            QListWidget::item:selected {
                background-color: #2a1f1a;
                color: #ff6b35;
            }
            
            QListWidget::item:hover {
                background-color: #1f1410;
            }
            
            QLineEdit, QComboBox {
                background-color: #1a0f0a;
                border: 1px solid #2a1f1a;
                color: #e8e6e3;
                padding: 8px;
                border-radius: 4px;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border-color: #ff4500;
            }
            
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #8a7a6a;
                width: 0;
                height: 0;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1a0f0a;
                border: 1px solid #2a1f1a;
                selection-background-color: #2a1f1a;
                selection-color: #ff6b35;
            }
            
            QPushButton#primaryButton, QPushButton#vaultButton {
                background-color: #ff4500;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            QPushButton#primaryButton:hover, QPushButton#vaultButton:hover {
                background-color: #ff6b35;
            }
            
            QCheckBox {
                color: #8a7a6a;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #2a1f1a;
                border-radius: 3px;
                background-color: #1a0f0a;
            }
            
            QCheckBox::indicator:checked {
                background-color: #ff4500;
                border-color: #ff4500;
            }
            
            QTextEdit#codeBlock {
                background-color: #0a0605;
                border: 1px solid #2a1f1a;
                color: #ff6b35;
                font-family: 'Share Tech Mono', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
            
            #detailLabel {
                font-size: 10px;
                font-weight: 600;
                color: #8a7a6a;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 8px;
            }
            
            #detailValue {
                font-size: 12px;
                color: #e8e6e3;
                margin-bottom: 8px;
            }
            
            #settingsLabel {
                font-size: 12px;
                font-weight: 600;
                color: #8a7a6a;
                margin-top: 12px;
            }
            
            #welcomeBanner {
                background-color: #1a0f0a;
                border: 1px solid #ff4500;
                border-radius: 6px;
                padding: 16px;
                margin-bottom: 16px;
            }
            
            #welcomeTitle {
                font-size: 16px;
                font-weight: bold;
                color: #ff6b35;
                margin-bottom: 8px;
            }
            
            #welcomeMsg {
                font-size: 12px;
                color: #8a7a6a;
                line-height: 1.5;
            }
            
            #demoButton {
                background-color: transparent;
                border: 1px solid #ff4500;
                color: #ff4500;
                padding: 8px 16px;
                border-radius: 4px;
                margin-top: 12px;
                text-align: left;
            }
            
            #demoButton:hover {
                background-color: #2a1500;
            }
            
            #demoBanner {
                background-color: #2a1500;
                color: #ff6b35;
                border-bottom: 1px solid #ff4500;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: 600;
            }
            
            QPushButton#scanButton {
                background-color: #ff4500;
                color: #ffffff;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 8px;
            }
            
            QPushButton#scanButton:hover {
                background-color: #ff6b35;
            }
            
            QPushButton#scanButton:disabled {
                background-color: #2a1f1a;
                color: #555;
            }
            
            #scanStatus {
                font-size: 11px;
                color: #ff6b35;
                letter-spacing: 1px;
                margin-top: 6px;
            }
            
            QScrollBar:vertical {
                background-color: #0f0a08;
                width: 8px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #2a1f1a;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #3a2f2a;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #0f0a08;
                height: 8px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #2a1f1a;
                border-radius: 4px;
                min-width: 20px;
            }
            
            QPushButton#exportButton {
                background-color: transparent;
                border: 1px solid #ff4500;
                color: #ff4500;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
                letter-spacing: 1px;
            }
            
            QPushButton#exportButton:hover {
                background-color: rgba(255,69,0,0.15);
            }
            
            #warningBanner {
                background-color: rgba(255,170,0,0.1);
                border: 1px solid #ffaa00;
                border-radius: 4px;
                color: #ffaa00;
                padding: 8px 12px;
                font-size: 11px;
            }
            
            QPushButton#simButton {
                background-color: transparent;
                border: 1px solid #ff4500;
                color: #ff4500;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            
            QPushButton#simButton:hover {
                background-color: rgba(255,69,0,0.15);
                color: #ff6b35;
            }
            
            QPushButton#simButton:disabled {
                border-color: #2a1f1a;
                color: #2a1f1a;
            }
            
            QTextEdit#simulationLog {
                background-color: #020a02;
                border: 1px solid #1a3a1a;
                border-radius: 4px;
                font-family: 'Share Tech Mono', 'Courier New', monospace;
                font-size: 11px;
                color: #e8e6e3;
                padding: 12px;
            }
            
            QPushButton#secondaryButton {
                background-color: transparent;
                border: 1px solid #ff4500;
                color: #ff4500;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                letter-spacing: 1px;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: rgba(255,69,0,0.15);
            }
            
            #sectionLabel {
                font-size: 9px;
                letter-spacing: 2px;
                color: #8a7a6a;
                margin-top: 8px;
            }
            
            #detailMeta {
                font-size: 11px;
                color: #8a7a6a;
            }
            
            #detailText {
                font-size: 12px;
                color: #e8e6e3;
                line-height: 1.5;
            }
            
            QPushButton#fixButton {
                background-color: #ff4500;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 4px;
            }
            
            QPushButton#fixButton:hover {
                background-color: #ff6b35;
            }
            
            QPushButton#fixButton:disabled {
                background-color: #2a1f1a;
                color: #444;
            }
            
            QTextEdit#remediationBox {
                background-color: #020a02;
                border: 1px solid #1a3a1a;
                border-radius: 4px;
                font-family: 'Share Tech Mono', 'Courier New', monospace;
                font-size: 10px;
                color: #ff6b35;
                padding: 6px;
            }
        """

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    from splash_screen import SplashScreen
    
    app = QApplication(sys.argv)
    # Allow remote content loading for map tiles
    QWebEngineProfile.defaultProfile().setHttpCacheType(
        QWebEngineProfile.HttpCacheType.NoCache
    )
    
    # Show splash first
    splash = SplashScreen()
    splash.show()
    
    # When splash finishes, show main window
    def launch_main():
        window = CloudStrikeUI()
        window.show()
    
    splash.finished.connect(launch_main)
    sys.exit(app.exec())
