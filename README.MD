# ⚡ CloudStrike
### Automated Cloud Pentesting & Security Auditor

> A professional desktop application for AWS security auditing, attack simulation, and automated remediation — built for the Skill Palavar Hackathon.

---

## 🎯 What is CloudStrike?

CloudStrike is a Windows desktop tool that goes beyond traditional cloud security scanners. It combines:

- **Real-time AWS security scanning** — detects misconfigurations across S3, IAM, EC2, RDS, CloudTrail
- **Live attack chain simulation** — simulates real attacker techniques safely using read-only APIs
- **Auto-remediation guidance** — generates exact AWS CLI commands to fix every finding
- **Professional PDF reports** — branded security audit reports with risk scores
- **Live threat map** — geographic visualization of findings per AWS region

---

## 🖥️ Requirements

| Requirement | Version |
|---|---|
| Windows | 10 or 11 |
| Python | 3.11+ |
| AWS Account | Any (free tier works) |

---

## ⚙️ Installation

**Step 1 — Clone the repository:**
```bash
git clone <repository-url>
cd CloudStrike_Final_Version
```

**Step 2 — Install all dependencies:**

**Option A - Using requirements.txt (recommended):**
```bash
pip install -r requirements.txt
```

**Option B - Manual installation (single command):**
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph azure-identity azure-mgmt-resource azure-mgmt-storage azure-mgmt-compute azure-mgmt-network google-cloud-storage google-auth
```

**Option C - AWS only (minimal install):**
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph
```

**Step 3 — Run the application:**
```bash
python cloudstrike_ui.py
```

> 💡 **Note:** Azure and GCP packages are optional. If you only scan AWS, use Option C for minimal installation.

---

## 🔐 AWS Setup (for real scanning)

Create an IAM user with these policies attached:

```bash
# Attach required policies
aws iam attach-user-policy \
  --user-name your-user \
  --policy-arn arn:aws:iam::aws:policy/SecurityAudit

aws iam attach-user-policy \
  --user-name your-user \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

Then generate Access Key + Secret Key for that user.

> ⚠️ CloudStrike **never** performs write operations. All scanning is read-only.

---

## 🚀 Quick Start

### Option A — Real AWS Scan
1. Launch: `python cloudstrike_ui.py`
2. Watch the splash screen (Terminal Boot → Radar Sweep)
3. Enter AWS credentials in the **Vault** page
4. Click **START AWS SCAN**
5. Watch real findings populate in real time
6. Navigate to **Incidents** to run attack simulations
7. Click **EXPORT REPORT** to generate PDF

### Option B — Demo Mode (no credentials needed)
1. Launch: `python cloudstrike_ui.py`
2. Click **Launch in Demo Mode** on the Vault page
3. Explore all features with sample data

---

## 🛡️ Features

### 1. Real AWS Security Scanning
Scans your AWS account across multiple regions and services:

| Service | Checks |
|---|---|
| S3 | Public access, encryption, versioning, ACLs |
| IAM | MFA enforcement, old access keys, wildcard policies |
| EC2 | Open security groups, IMDSv1 vulnerability |
| RDS | Public accessibility, storage encryption |
| CloudTrail | Logging enabled, log validation |
| Root Account | MFA enabled |

### 2. Attack Chain Simulation
Safe, read-only attack simulations that show real attacker techniques:

- **⚡ IAM Privilege Escalation** — Checks if attacker can escalate permissions via policy simulation
- **🪣 S3 Bucket Takeover** — Tests bucket exposure, ACL misconfigurations, data accessibility

All simulations are:
- ✅ Read-only
- ✅ Non-destructive
- ✅ Use official AWS IAM policy simulation APIs
- ✅ Compliant with AWS acceptable use policy

### 3. Compliance Dashboard
CIS AWS Foundations Benchmark checklist with PASS/FAIL status across 13 controls covering IAM, CloudTrail, EC2, S3, and VPC.

### 4. PDF Report Export
Professional branded reports including:
- Executive summary with risk score (0-100)
- Severity breakdown (Critical/High/Medium/Low)
- Full findings table sorted by severity
- AWS CLI remediation commands for every finding
- CloudStrike branding

### 5. Live Threat Map
World map showing findings geographically:
- 🔴 Red = Critical findings in region
- 🟠 Orange = High findings in region
- ⚫ Grey = No findings / not scanned

### 6. Configurable Scan Settings
- **Scan Depth**: Quick (3 checks), Standard (6 checks), Deep (8 checks)
- **Region Selection**: Choose which AWS regions to scan
- **Notifications**: Real-time popups for Critical/High findings
- **Auto PDF**: Automatically generate report after scan

---

## 📁 Project Structure

```
CloudStrike_Final_Version/
├── cloudstrike_ui.py        # Main window + navigation
├── splash_screen.py         # Animated splash screen
├── aws_scanner.py           # Real AWS scanning (multiprocessing)
├── attack_simulator.py      # Attack chain simulations
├── report_generator.py      # PDF report generation
├── settings_manager.py      # Settings persistence
├── threat_map.py            # Leaflet.js world map
├── scan_activity_chart.py   # PyQtGraph scan chart
├── activity_feed.py         # Real-time activity feed
├── page_dashboard.py        # Dashboard page
├── page_findings.py         # Findings table
├── page_incidents.py        # Attack simulations
├── page_compliance.py       # CIS compliance checklist
├── page_vault.py            # Credential management
├── page_integrations.py     # Scan settings
├── detail_panels.py         # Finding detail panels
└── cloudstrike_vault.db     # Local credential storage (auto-created)
```

---

## 🔒 Security & Privacy

- **Credentials stored locally** in SQLite database — never transmitted
- **Read-only AWS access** — SecurityAudit policy only
- **No external servers** — everything runs on your machine
- **No telemetry** — zero data collection

---

## 🏆 What Makes CloudStrike Different

| Feature | CloudStrike | ScoutSuite | Prowler |
|---|---|---|---|
| Desktop GUI | ✅ | ❌ | ❌ |
| Attack Simulation | ✅ | ❌ | ❌ |
| Live Threat Map | ✅ | ❌ | ❌ |
| PDF Reports | ✅ | ✅ | ✅ |
| Real-time findings | ✅ | ❌ | ❌ |
| One-click setup | ✅ | ❌ | ❌ |

---

## 👥 Team

Built for **Skill Palavar Hackathon**
Category: Cloud Security / Cybersecurity Tools

---

## 📄 License

This project is built for educational and security research purposes.
All AWS scanning is performed with read-only credentials in compliance with AWS acceptable use policies.