from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class IncidentsPage(QWidget):
    incident_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.simulator = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("ATTACK CHAIN SIMULATION")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        warning = QLabel(
            "⚠  All simulations are READ-ONLY and NON-DESTRUCTIVE. "
            "No data will be modified. Uses IAM policy simulation APIs only."
        )
        warning.setObjectName("warningBanner")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        btn_layout = QHBoxLayout()

        self.iam_btn = QPushButton("⚡  SIMULATE — IAM Privilege Escalation")
        self.iam_btn.setObjectName("simButton")
        self.iam_btn.clicked.connect(lambda: self.start_simulation('iam_privesc'))

        self.s3_btn = QPushButton("🪣  SIMULATE — S3 Bucket Takeover")
        self.s3_btn.setObjectName("simButton")
        self.s3_btn.clicked.connect(lambda: self.start_simulation('s3_takeover'))

        btn_layout.addWidget(self.iam_btn)
        btn_layout.addWidget(self.s3_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setObjectName("scanStatus")
        layout.addWidget(self.status_label)

        steps_label = QLabel("SIMULATION OUTPUT")
        steps_label.setObjectName("panelTitle")
        layout.addWidget(steps_label)

        self.output_log = QTextEdit()
        self.output_log.setObjectName("simulationLog")
        self.output_log.setReadOnly(True)
        self.output_log.setPlaceholderText(
            "Click a simulation button above to start an attack chain...\n\n"
            "Available simulations:\n"
            "  ⚡ IAM Privilege Escalation — Tests if attacker can escalate permissions\n"
            "  🪣 S3 Bucket Takeover — Tests if buckets are exposed to public\n\n"
            "All simulations are READ-ONLY and non-destructive."
        )
        layout.addWidget(self.output_log, 1)

    def start_simulation(self, sim_name):
        import sqlite3
        from PyQt6.QtCore import Qt

        try:
            conn = sqlite3.connect("cloudstrike_vault.db")
            row = conn.execute(
                "SELECT * FROM credentials LIMIT 1"
            ).fetchone()
            conn.close()
            if not row:
                self.status_label.setText("✗ No credentials found. Add credentials in Vault first.")
                return
            credentials = {
                'access_key':   row[3],
                'secret_key':   row[4],
                'region':       row[5],
                'account_name': row[2]
            }
        except Exception as e:
            self.status_label.setText(f"✗ Credential error: {e}")
            return

        self.output_log.clear()
        self.iam_btn.setEnabled(False)
        self.s3_btn.setEnabled(False)
        name = 'IAM Privilege Escalation' if sim_name == 'iam_privesc' else 'S3 Bucket Takeover'
        self.status_label.setText(f"● Running: {name}...")
        self.append_log(f"{'='*60}", '#ff4500')
        self.append_log(f"  CLOUDSTRIKE — {name.upper()} SIMULATION", '#ff4500')
        from datetime import datetime
        self.append_log(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", '#8a7a6a')
        self.append_log(f"{'='*60}\n", '#ff4500')

        from attack_simulator import AttackSimulator
        self.simulator = AttackSimulator(sim_name, credentials)
        self._sim_ref = self.simulator

        self.simulator.step_update.connect(
            self.on_step_update,
            Qt.ConnectionType.QueuedConnection
        )
        self.simulator.sim_complete.connect(
            self.on_sim_complete,
            Qt.ConnectionType.QueuedConnection
        )
        self.simulator.sim_error.connect(
            self.on_sim_error,
            Qt.ConnectionType.QueuedConnection
        )
        self.simulator.start()

    def on_step_update(self, step_data):
        step = step_data.get('step', 0)
        title = step_data.get('title', '')
        detail = step_data.get('detail', '')
        status = step_data.get('status', '')
        risk = step_data.get('risk')
        timestamp = step_data.get('timestamp', '')

        status_colors = {
            'running': '#ff6b35',
            'success': '#28c840',
            'fail':    '#ff0000',
            'warning': '#ffaa00'
        }
        status_icons = {
            'running': '●',
            'success': '✓',
            'fail':    '✗',
            'warning': '⚠'
        }

        color = status_colors.get(status, '#e8e6e3')
        icon = status_icons.get(status, '›')

        if step > 0:
            self.append_log(
                f"\n[{timestamp}] STEP {step} — {title}",
                color
            )
        self.append_log(detail, '#e8e6e3')
        if risk:
            self.append_log(f"\n  RISK: {risk}", '#ffaa00')

        self.status_label.setText(
            f"{'●' if status == 'running' else icon} Step {step}: {title}"
        )

    def on_sim_complete(self, result, findings):
        self.append_log(
            f"\n{'='*60}\n  SIMULATION COMPLETE — Result: {result}\n{'='*60}",
            '#28c840'
        )
        if findings:
            self.append_log("\nKEY FINDINGS:", '#ff4500')
            for f in findings:
                self.append_log(f"  • {f}", '#e8e6e3')

        self.status_label.setText(f"✓ Simulation complete — {result}")
        self.iam_btn.setEnabled(True)
        self.s3_btn.setEnabled(True)

    def on_sim_error(self, error):
        self.append_log(f"\n✗ ERROR: {error}", '#ff0000')
        self.status_label.setText("✗ Simulation failed")
        self.iam_btn.setEnabled(True)
        self.s3_btn.setEnabled(True)

    def append_log(self, text, color='#e8e6e3'):
        self.output_log.setTextColor(QColor(color))
        self.output_log.append(text)
        scrollbar = self.output_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
