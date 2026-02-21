import json
import urllib.request
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer


# ── DEMO CVE DATA (fallback if API unavailable) ──
DEMO_CVES = [
    {
        'id': 'CVE-2026-21234',
        'score': 9.8,
        'severity': 'CRITICAL',
        'description': 'AWS S3 presigned URL bypass allows unauthenticated access to private bucket objects via malformed signature.',
        'services': ['AWS', 'S3'],
        'published': '2 min ago',
        'matched': 'S3 bucket exposed publicly'
    },
    {
        'id': 'CVE-2026-18901',
        'score': 8.1,
        'severity': 'HIGH',
        'description': 'AWS IAM role chaining allows privilege escalation when sts:AssumeRole is combined with misconfigured trust policies.',
        'services': ['AWS', 'IAM'],
        'published': '18 min ago',
        'matched': 'IAM policy overly permissive'
    },
    {
        'id': 'CVE-2026-17823',
        'score': 9.1,
        'severity': 'CRITICAL',
        'description': 'Azure AD OAuth token validation flaw enables authentication bypass in multi-tenant applications.',
        'services': ['Azure', 'AD'],
        'published': '34 min ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-15670',
        'score': 7.5,
        'severity': 'HIGH',
        'description': 'CloudTrail log tampering via S3 object deletion allows attackers to erase audit evidence post-compromise.',
        'services': ['AWS', 'CloudTrail'],
        'published': '1 hr ago',
        'matched': 'CloudTrail not enabled'
    },
    {
        'id': 'CVE-2026-14422',
        'score': 7.2,
        'severity': 'HIGH',
        'description': 'GCP Cloud Run service account token leakage via metadata endpoint when IMDSv1 is enabled.',
        'services': ['GCP', 'CloudRun'],
        'published': '2 hr ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-12190',
        'score': 6.5,
        'severity': 'MEDIUM',
        'description': 'AWS RDS MySQL parameter group injection allows remote code execution via malformed SQL mode flags.',
        'services': ['AWS', 'RDS'],
        'published': '3 hr ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-11034',
        'score': 5.9,
        'severity': 'MEDIUM',
        'description': 'Azure Blob Storage SAS token expiry bypass allows continued access after token revocation.',
        'services': ['Azure', 'Storage'],
        'published': '5 hr ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-09871',
        'score': 9.0,
        'severity': 'CRITICAL',
        'description': 'AWS Lambda function URL authentication bypass allows unauthenticated invocation of private functions.',
        'services': ['AWS', 'Lambda'],
        'published': '6 hr ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-08234',
        'score': 7.8,
        'severity': 'HIGH',
        'description': 'GCP IAM service account key exfiltration via metadata server SSRF allows full account takeover.',
        'services': ['GCP', 'IAM'],
        'published': '8 hr ago',
        'matched': None
    },
    {
        'id': 'CVE-2026-07123',
        'score': 4.3,
        'severity': 'LOW',
        'description': 'AWS CloudWatch log group retention policy bypass allows indefinite log storage without billing controls.',
        'services': ['AWS', 'CloudWatch'],
        'published': '12 hr ago',
        'matched': None
    },
]


class CVEFetchThread(QThread):
    """Fetches real CVEs from NVD API"""
    cves_loaded = pyqtSignal(list)
    fetch_failed = pyqtSignal()

    def run(self):
        try:
            import urllib.request
            import json
            import ssl

            # Create SSL context that doesn't verify — fixes corporate network issues
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # NVD API v2 — search for cloud CVEs published recently
            url = (
                'https://services.nvd.nist.gov/rest/json/cves/2.0'
                '?keywordSearch=AWS%20cloud%20security'
                '&resultsPerPage=15'
            )

            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'CloudStrike-Security-Tool/1.0',
                    'Accept': 'application/json'
                }
            )

            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                raw = resp.read()
                data = json.loads(raw)

            cves = []
            for item in data.get('vulnerabilities', []):
                cve = item.get('cve', {})
                cve_id = cve.get('id', '')

                # Get description
                desc = ''
                for d in cve.get('descriptions', []):
                    if d.get('lang') == 'en':
                        desc = d.get('value', '')[:250]
                        break

                # Get CVSS score
                score = 0.0
                severity = 'MEDIUM'
                metrics = cve.get('metrics', {})
                for key in ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2']:
                    if key in metrics and metrics[key]:
                        m = metrics[key][0]
                        cvss_data = m.get('cvssData', {})
                        score = cvss_data.get('baseScore', 0.0)
                        severity = (
                            cvss_data.get('baseSeverity') or
                            m.get('baseSeverity', 'MEDIUM')
                        ).upper()
                        break

                # Get published date
                published = cve.get('published', '')
                if published:
                    from datetime import datetime, timezone
                    try:
                        pub_dt = datetime.fromisoformat(
                            published.replace('Z', '+00:00')
                        )
                        now = datetime.now(timezone.utc)
                        diff = now - pub_dt
                        if diff.days == 0:
                            hours = diff.seconds // 3600
                            pub_str = f"{hours} hr ago" if hours > 0 else "Just now"
                        elif diff.days == 1:
                            pub_str = "Yesterday"
                        else:
                            pub_str = f"{diff.days} days ago"
                    except:
                        pub_str = published[:10]
                else:
                    pub_str = 'Unknown'

                # Detect services
                desc_lower = desc.lower()
                services = []
                if any(x in desc_lower for x in ['aws', 'amazon', 's3', 'ec2', 'iam', 'lambda']):
                    services.append('AWS')
                if any(x in desc_lower for x in ['azure', 'microsoft', 'blob']):
                    services.append('Azure')
                if any(x in desc_lower for x in ['gcp', 'google cloud', 'gcs']):
                    services.append('GCP')
                if not services:
                    services = ['Cloud']

                if cve_id and desc:
                    cves.append({
                        'id':          cve_id,
                        'score':       score,
                        'severity':    severity,
                        'description': desc,
                        'services':    services,
                        'published':   pub_str,
                        'matched':     None
                    })

            if cves:
                self.cves_loaded.emit(cves)
            else:
                self.fetch_failed.emit()

        except urllib.error.HTTPError as e:
            # NVD returns 403 if rate limited — wait and use demo
            print(f"CVE API HTTP Error: {e.code} {e.reason}")
            self.fetch_failed.emit()
        except urllib.error.URLError as e:
            print(f"CVE API URL Error: {e.reason}")
            self.fetch_failed.emit()
        except Exception as e:
            import traceback
            print(f"CVE API Error: {e}")
            traceback.print_exc()
            self.fetch_failed.emit()


class CVECard(QFrame):
    def __init__(self, cve_data, parent=None):
        super().__init__(parent)
        self.setObjectName("cveCard")
        sev = cve_data.get('severity', 'LOW')
        colors = {
            'CRITICAL': '#ff0000',
            'HIGH':     '#ff4500',
            'MEDIUM':   '#ff6b35',
            'LOW':      '#888888'
        }
        color = colors.get(sev, '#888')
        matched = cve_data.get('matched')

        self.setStyleSheet(f"""
            QFrame#cveCard {{
                background: #130c09;
                border: 1px solid {'#ff450040' if matched else '#1a0f0a'};
                border-left: 3px solid {color};
                border-radius: 6px;
                margin-bottom: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row
        top = QHBoxLayout()
        cve_id = QLabel(cve_data.get('id', ''))
        cve_id.setStyleSheet(
            "color:#ff6b35; font-family:'Share Tech Mono','Courier New';"
            "font-size:11px; border:none;"
        )
        score = cve_data.get('score', 0)
        score_badge = QLabel(f"{score} {sev}")
        score_badge.setStyleSheet(
            f"color:{color}; background:{color}20; border:1px solid {color}40;"
            f"padding:2px 8px; border-radius:3px; font-size:10px;"
            f"font-family:'Share Tech Mono','Courier New';"
        )
        top.addWidget(cve_id)
        top.addStretch()
        top.addWidget(score_badge)
        layout.addLayout(top)

        # Description
        desc = QLabel(cve_data.get('description', ''))
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "color:#8a7a6a; font-size:11px; border:none; "
            "font-family:'Rajdhani','Segoe UI';"
        )
        layout.addWidget(desc)

        # Tags + time
        bottom = QHBoxLayout()
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(4)
        for tag in cve_data.get('services', []):
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(
                "color:#ff6b35; background:#ff450010; border:1px solid #ff450060;"
                "padding:1px 6px; border-radius:2px; font-size:9px;"
            )
            tags_layout.addWidget(tag_lbl)
        tags_layout.addStretch()
        time_lbl = QLabel(cve_data.get('published', ''))
        time_lbl.setStyleSheet(
            "color:#3a2a1a; font-size:9px;"
            "font-family:'Share Tech Mono','Courier New'; border:none;"
        )
        bottom.addLayout(tags_layout)
        bottom.addWidget(time_lbl)
        layout.addLayout(bottom)

        # Matched banner
        if matched:
            match_frame = QFrame()
            match_frame.setStyleSheet(
                "background:#ff450015; border:1px solid #ff450040;"
                "border-radius:3px;"
            )
            match_layout = QHBoxLayout(match_frame)
            match_layout.setContentsMargins(8, 4, 8, 4)
            match_lbl = QLabel(f"⚠ MATCHES YOUR SCAN — {matched}")
            match_lbl.setStyleSheet(
                "color:#ff6b35; font-size:9px; letter-spacing:1px; border:none;"
            )
            match_layout.addWidget(match_lbl)
            layout.addWidget(match_frame)


class CVEPage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_cves = DEMO_CVES.copy()
        self.current_filter = 'ALL'
        self._build_ui()
        # Auto-fetch real CVEs on load - wait 2 seconds for page to load
        QTimer.singleShot(2000, self.fetch_cves)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("LIVE CVE THREAT FEED")
        title.setObjectName("panelTitle")
        self.live_label = QLabel("● LIVE — NVD API")
        self.live_label.setStyleSheet(
            "color:#28c840; font-size:10px; letter-spacing:1px;"
        )
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.live_label)
        layout.addLayout(header)

        # Stats row
        stats_row = QHBoxLayout()
        self.matched_stat = self._stat_widget("3", "MATCHED", "#ff0000")
        self.today_stat   = self._stat_widget("47", "TODAY", "#ff4500")
        self.critical_stat = self._stat_widget("12", "CRITICAL", "#888")
        stats_row.addWidget(self.matched_stat)
        stats_row.addWidget(self.today_stat)
        stats_row.addWidget(self.critical_stat)
        layout.addLayout(stats_row)

        # Filter buttons
        filter_row = QHBoxLayout()
        self.filter_btns = {}
        for label in ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', '⚠ MATCHED']:
            btn = QPushButton(label)
            btn.setObjectName(
                "primaryButton" if label == 'ALL' else "secondaryButton"
            )
            btn.setFixedHeight(28)
            btn.clicked.connect(
                lambda checked, l=label: self.apply_filter(l)
            )
            self.filter_btns[label] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("↺ REFRESH")
        self.refresh_btn.setObjectName("secondaryButton")
        self.refresh_btn.clicked.connect(self.fetch_cves)
        filter_row.addWidget(self.refresh_btn)
        layout.addLayout(filter_row)

        # Status label
        self.status_label = QLabel(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')} — "
            f"Showing demo data. Fetching live CVEs..."
        )
        self.status_label.setObjectName("scanStatus")
        layout.addWidget(self.status_label)

        # Scroll area for CVE cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border:none; background:transparent; }"
            "QScrollBar:vertical { background:#0a0705; width:6px; }"
            "QScrollBar::handle:vertical { background:#2a1f1a; border-radius:3px; }"
        )
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.addStretch()
        scroll.setWidget(self.scroll_widget)
        layout.addWidget(scroll)

        self._populate_cards(self.all_cves)

    def _stat_widget(self, value, label, color):
        frame = QFrame()
        frame.setStyleSheet(
            "background:#130c09; border:1px solid #1a0f0a; border-radius:6px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 10, 16, 10)
        val = QLabel(value)
        val.setStyleSheet(
            f"color:{color}; font-size:22px; font-family:'Orbitron','Segoe UI';"
            f"font-weight:600; border:none;"
        )
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color:#4a3a2a; font-size:9px; letter-spacing:2px; border:none;"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(val)
        lay.addWidget(lbl)
        return frame

    def _populate_cards(self, cves):
        # Clear existing
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for cve in cves:
            card = CVECard(cve)
            self.scroll_layout.addWidget(card)
        self.scroll_layout.addStretch()

    def apply_filter(self, filter_name):
        self.current_filter = filter_name
        # Update button styles
        for label, btn in self.filter_btns.items():
            btn.setObjectName(
                "primaryButton" if label == filter_name else "secondaryButton"
            )
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Filter CVEs
        if filter_name == 'ALL':
            filtered = self.all_cves
        elif filter_name == '⚠ MATCHED':
            filtered = [c for c in self.all_cves if c.get('matched')]
        else:
            filtered = [
                c for c in self.all_cves
                if c.get('severity') == filter_name
            ]
        self._populate_cards(filtered)

    def fetch_cves(self):
        self.status_label.setText("Connecting to NVD API (nvd.nist.gov)...")
        self.refresh_btn.setEnabled(False)
        self.live_label.setText("● CONNECTING...")
        self.live_label.setStyleSheet(
            "color:#ff6b35; font-size:10px; letter-spacing:1px;"
        )
        self.thread = CVEFetchThread()
        self.thread.cves_loaded.connect(self.on_cves_loaded)
        self.thread.fetch_failed.connect(self.on_fetch_failed)
        self.thread.start()

    def on_cves_loaded(self, cves):
        # Preserve matched status from demo data
        matched_map = {
            c['id']: c['matched']
            for c in DEMO_CVES if c.get('matched')
        }
        for cve in cves:
            cve['matched'] = matched_map.get(cve['id'])

        self.all_cves = cves
        self._populate_cards(cves)

        self.status_label.setText(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')} — "
            f"Live data from NVD API"
        )
        self.live_label.setText("● LIVE — NVD API")
        self.live_label.setStyleSheet(
            "color:#28c840; font-size:10px; letter-spacing:1px;"
        )
        self.refresh_btn.setEnabled(True)

    def on_fetch_failed(self):
        self.all_cves = DEMO_CVES.copy()
        self._populate_cards(self.all_cves)
        self.status_label.setText(
            f"Last updated: {datetime.now().strftime('%H:%M:%S')} — "
            f"Demo data (Check console for API error details)"
        )
        self.live_label.setText("● DEMO MODE")
        self.live_label.setStyleSheet(
            "color:#888888; font-size:10px; letter-spacing:1px;"
        )
        self.refresh_btn.setEnabled(True)

    def update_matches(self, findings):
        """Called after scan to highlight CVEs matching findings"""
        finding_titles = [
            f.get('title', '').lower() for f in findings
        ]
        finding_services = [
            f.get('service', '').lower() for f in findings
        ]

        for cve in self.all_cves:
            cve['matched'] = None
            for service in cve.get('services', []):
                if service.lower() in finding_services:
                    cve['matched'] = f"{service} finding detected in your scan"
                    break

        self._populate_cards(self.all_cves)
