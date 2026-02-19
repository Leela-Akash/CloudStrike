from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                             QComboBox, QPushButton, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
import sqlite3
import os
import logging
import traceback

class VaultPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = "cloudstrike_vault.db"
        self.parent_window = None
        self.init_database()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Welcome banner for first-time users
        self.welcome_banner = QFrame()
        self.welcome_banner.setObjectName("welcomeBanner")
        banner_layout = QVBoxLayout(self.welcome_banner)
        banner_layout.setContentsMargins(16, 16, 16, 16)
        banner_layout.setSpacing(8)
        
        welcome_title = QLabel("👋  Welcome to CloudStrike")
        welcome_title.setObjectName("welcomeTitle")
        
        welcome_msg = QLabel(
            "To get started, connect your first cloud account.\n"
            "Your credentials are stored locally and never sent anywhere."
        )
        welcome_msg.setObjectName("welcomeMsg")
        welcome_msg.setWordWrap(True)
        
        demo_btn = QPushButton("▶  Launch in Demo Mode (No credentials needed)")
        demo_btn.setObjectName("demoButton")
        demo_btn.clicked.connect(self.launch_demo_mode)
        
        banner_layout.addWidget(welcome_title)
        banner_layout.addWidget(welcome_msg)
        banner_layout.addWidget(demo_btn)
        
        layout.addWidget(self.welcome_banner)
        
        # Check if credentials exist to hide banner
        if self.has_credentials():
            self.welcome_banner.hide()
        
        frame = QFrame()
        frame.setObjectName("mapFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("CREDENTIAL VAULT")
        title.setObjectName("panelTitle")
        frame_layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("vaultInput")
        self.provider_combo.addItems(["AWS", "Azure", "GCP"])
        
        self.account_input = QLineEdit()
        self.account_input.setObjectName("vaultInput")
        self.account_input.setPlaceholderText("Production Account")
        
        self.access_key_input = QLineEdit()
        self.access_key_input.setObjectName("vaultInput")
        self.access_key_input.setPlaceholderText("AKIAIOSFODNN7EXAMPLE")
        
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setObjectName("vaultInput")
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_input.setPlaceholderText("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
        
        self.region_input = QLineEdit()
        self.region_input.setObjectName("vaultInput")
        self.region_input.setPlaceholderText("us-east-1")
        
        form_layout.addRow("Cloud Provider:", self.provider_combo)
        form_layout.addRow("Account Name:", self.account_input)
        form_layout.addRow("Access Key:", self.access_key_input)
        form_layout.addRow("Secret Key:", self.secret_key_input)
        form_layout.addRow("Region:", self.region_input)
        
        save_btn = QPushButton("Save Credentials")
        save_btn.setObjectName("secondaryButton")
        save_btn.clicked.connect(self.save_credentials)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background:#2a1f1a;")
        
        self.scan_btn = QPushButton("▶  START AWS SCAN")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(self.has_credentials())
        
        self.scan_status = QLabel("")
        self.scan_status.setObjectName("scanStatus")
        
        frame_layout.addLayout(form_layout)
        frame_layout.addWidget(save_btn)
        frame_layout.addWidget(separator)
        frame_layout.addWidget(self.scan_btn)
        frame_layout.addWidget(self.scan_status)
        frame_layout.addStretch()
        
        layout.addWidget(frame)
        
        # Load saved credentials if they exist
        self.load_credentials()
    
    def load_credentials(self):
        """Load and display saved credentials when page opens"""
        if not os.path.exists(self.db_path):
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data = dict(zip(columns, row))
                
                # Use exact attribute names from form
                if hasattr(self, 'account_input'):
                    self.account_input.setText(str(data.get('account_name', '')))
                if hasattr(self, 'access_key_input'):
                    self.access_key_input.setText(str(data.get('access_key', '')))
                if hasattr(self, 'secret_key_input'):
                    self.secret_key_input.setText(str(data.get('secret_key', '')))
                if hasattr(self, 'region_input'):
                    self.region_input.setText(str(data.get('region', '')))
                if hasattr(self, 'provider_combo'):
                    provider = data.get('provider', 'AWS')
                    index = self.provider_combo.findText(provider)
                    if index >= 0:
                        self.provider_combo.setCurrentIndex(index)
                
                # Enable scan button
                if hasattr(self, 'scan_btn'):
                    self.scan_btn.setEnabled(True)
                
                # Hide welcome banner
                if hasattr(self, 'welcome_banner'):
                    self.welcome_banner.hide()
                
                # Show status
                if hasattr(self, 'scan_status'):
                    account = data.get('account_name', 'Unknown')
                    region = data.get('region', 'Unknown')
                    self.scan_status.setText(f"✓ Credentials loaded — {account} ({region})")
        except Exception as e:
            print(f"DEBUG load_credentials error: {e}")
            import traceback
            traceback.print_exc()
    
    def showEvent(self, event):
        """Reload credentials every time page becomes visible"""
        super().showEvent(event)
        self.load_credentials()
    
    def has_credentials(self):
        if not os.path.exists(self.db_path):
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM credentials")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False
    
    def launch_demo_mode(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().setProperty("demo_mode", True)
        
        # Show demo banner on dashboard
        if self.parent_window:
            self.parent_window.pages["Dashboard"].show_demo_banner()
            self.parent_window.switch_page("Dashboard")
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT,
                account_name TEXT,
                access_key TEXT,
                secret_key TEXT,
                region TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_credentials(self):
        provider = self.provider_combo.currentText()
        account = self.account_input.text()
        access_key = self.access_key_input.text()
        secret_key = self.secret_key_input.text()
        region = self.region_input.text()
        
        if not all([account, access_key, secret_key, region]):
            QMessageBox.warning(self, "Validation Error", "All fields are required")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO credentials (provider, account_name, access_key, secret_key, region)
            VALUES (?, ?, ?, ?, ?)
        ''', (provider, account, access_key, secret_key, region))
        conn.commit()
        conn.close()
        
        QMessageBox.information(self, "Success", "Credentials saved securely")
        self.welcome_banner.hide()
        self.scan_btn.setEnabled(True)
        self.clear_form()
        
        # Switch to dashboard after saving
        if self.parent_window:
            self.parent_window.switch_page("Dashboard")
    
    def start_scan(self):
        logging.debug("start_scan called")
        try:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1").fetchone()
            conn.close()
            logging.debug(f"Credentials row found: {row is not None}")
            
            if not row:
                self.scan_status.setText("✗ No credentials saved")
                logging.warning("No credentials found in database")
                return
            
            credentials = {
                'access_key': row[3],
                'secret_key': row[4],
                'region': row[5]
            }
            logging.debug(f"Credentials loaded - region: {credentials['region']}")
            logging.debug("Starting scanner thread")
            
            from aws_scanner import AWSScanner
            self.scanner = AWSScanner(credentials)
            self._scanner_ref = self.scanner
            
            from PyQt6.QtCore import Qt
            self.scanner.scan_progress.connect(
                self.on_progress,
                Qt.ConnectionType.QueuedConnection
            )
            self.scanner.finding_found.connect(
                self.on_finding,
                Qt.ConnectionType.QueuedConnection
            )
            self.scanner.scan_complete.connect(
                self.on_complete,
                Qt.ConnectionType.QueuedConnection
            )
            self.scanner.scan_error.connect(
                self.on_error,
                Qt.ConnectionType.QueuedConnection
            )
            
            # Connect to main window restore
            main = self.window()
            if hasattr(main, 'start_scan_safe'):
                main.start_scan_safe()
            if hasattr(main, 'restore_after_scan'):
                self.scanner.scan_complete.connect(
                    main.restore_after_scan,
                    Qt.ConnectionType.QueuedConnection
                )
            
            logging.debug("All signals connected, calling scanner.start()")
            self.scanner.start()
            logging.debug("Scanner thread started successfully")
            self.scan_btn.setEnabled(False)
            self.scan_status.setText("● SCANNING...")
            
        except Exception as e:
            logging.critical(f"start_scan crashed: {e}\n{traceback.format_exc()}")
            self.scan_status.setText(f"✗ Failed to start: {str(e)}")
    
    def on_progress(self, pct, check_name):
        self.scan_status.setText(f"● {pct}% — Checking {check_name}...")
    
    def on_finding(self, finding):
        if self.parent_window and hasattr(self.parent_window, 'pages'):
            self.parent_window.pages["Findings"].add_finding(finding)
        
        from settings_manager import get_all_settings
        settings = get_all_settings()
        sev = finding.get('severity', '')
        if sev == 'CRITICAL' and settings.get('notify_critical'):
            self.show_notification(finding)
        elif sev == 'HIGH' and settings.get('notify_high'):
            self.show_notification(finding)
    
    def show_notification(self, finding):
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self.window())
        msg.setWindowTitle(f"⚠ {finding['severity']} Finding Detected")
        msg.setText(finding['title'])
        msg.setInformativeText(
            f"Service: {finding['service']}\n"
            f"Region: {finding['region']}\n\n"
            f"{finding['description']}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1a0f0a;
                color: #e8e6e3;
            }
            QPushButton {
                background: #ff4500;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 3px;
            }
        """)
        msg.show()
    
    def on_complete(self, findings):
        self.scan_status.setText(f"✓ SCAN COMPLETE — {len(findings)} findings")
        self.scan_btn.setEnabled(True)
        
        from settings_manager import get_all_settings
        settings = get_all_settings()
        
        main = self.window()
        
        # Update threat map with real findings
        if hasattr(main, 'pages'):
            dashboard = main.pages.get("Dashboard")
            if dashboard and hasattr(dashboard, 'threat_map'):
                dashboard.threat_map.update_with_findings(findings)
        
        # Update activity feed
        if hasattr(main, 'activity_feed'):
            main.activity_feed.clear_and_reload(findings)
        
        # Update stat cards
        if hasattr(main, 'update_stat_cards'):
            main.update_stat_cards(findings)
        
        # Auto PDF if enabled
        if settings.get('auto_pdf'):
            try:
                import sqlite3
                from report_generator import generate_report
                from datetime import datetime
                conn = sqlite3.connect("cloudstrike_vault.db")
                row = conn.execute("SELECT * FROM credentials LIMIT 1").fetchone()
                conn.close()
                credentials = {
                    'account_name': row[2] if row else 'AWS Account',
                    'region': row[5] if row else 'us-east-1'
                }
                path = f"CloudStrike_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                generate_report(findings, credentials, path)
                self.scan_status.setText(
                    f"✓ SCAN COMPLETE — {len(findings)} findings | PDF saved: {path}"
                )
                import subprocess
                subprocess.Popen(['start', '', path], shell=True)
            except Exception as e:
                self.scan_status.setText(
                    f"✓ Scan complete | Auto-PDF failed: {e}"
                )
        
        # Notify scan complete
        if settings.get('notify_scan_done'):
            from PyQt6.QtWidgets import QMessageBox
            critical = sum(1 for f in findings if f.get('severity') == 'CRITICAL')
            high = sum(1 for f in findings if f.get('severity') == 'HIGH')
            QMessageBox.information(
                self.window(), "✓ Scan Complete",
                f"Scan finished!\n\n"
                f"Total findings: {len(findings)}\n"
                f"Critical: {critical}\n"
                f"High: {high}"
            )
        
        # Switch to findings page
        if self.parent_window:
            self.parent_window.switch_page("Findings")
    
    def on_error(self, error):
        self.scan_status.setText("✗ ERROR — See details")
        self.scan_btn.setEnabled(True)
        
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Scan Error")
        msg.setText("AWS Scan failed:")
        msg.setDetailedText(error)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
    
    def clear_form(self):
        self.account_input.clear()
        self.access_key_input.clear()
        self.secret_key_input.clear()
        self.region_input.clear()
