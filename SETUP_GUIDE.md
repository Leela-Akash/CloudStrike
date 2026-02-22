# CloudStrike - Quick Setup Guide

## For New Users Cloning the Project

### Prerequisites
- **Windows 10 or 11**
- **Python 3.11 or higher** ([Download here](https://www.python.org/downloads/))
- **Git** (optional, for cloning)

---

## Installation Steps

### 1. Clone or Download the Project

**Using Git:**
```bash
git clone <repository-url>
cd CloudStrike_Final_Version
```

**Or download ZIP:**
- Download the project ZIP file
- Extract to a folder
- Open Command Prompt in that folder

---

### 2. Install Dependencies

**Recommended - Use requirements.txt:**
```bash
pip install -r requirements.txt
```

This installs all packages needed for AWS, Azure, and GCP scanning.

---

### 3. Run CloudStrike

```bash
python cloudstrike_ui.py
```

The application will launch with an animated splash screen, then open the main dashboard.

---

## Alternative Installation Options

### Option A - Full Installation (All Cloud Providers)
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph azure-identity azure-mgmt-resource azure-mgmt-storage azure-mgmt-compute azure-mgmt-network google-cloud-storage google-auth
```

### Option B - AWS Only (Minimal)
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph
```

### Option C - AWS + Azure
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph azure-identity azure-mgmt-resource azure-mgmt-storage azure-mgmt-compute azure-mgmt-network
```

### Option D - AWS + GCP
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph google-cloud-storage google-auth
```

---

## Package Breakdown

| Package | Purpose | Required For |
|---------|---------|--------------|
| PyQt6 | GUI framework | All users |
| PyQt6-WebEngine | Threat map display | All users |
| boto3 | AWS SDK | AWS scanning |
| reportlab | PDF report generation | All users |
| pyqtgraph | Scan activity charts | All users |
| azure-identity | Azure authentication | Azure scanning |
| azure-mgmt-* | Azure resource management | Azure scanning |
| google-cloud-storage | GCP storage API | GCP scanning |
| google-auth | GCP authentication | GCP scanning |

---

## Troubleshooting

### "pip is not recognized"
**Solution:** Add Python to PATH or use:
```bash
python -m pip install -r requirements.txt
```

### "Permission denied" errors
**Solution:** Run Command Prompt as Administrator or use:
```bash
pip install --user -r requirements.txt
```

### "No module named 'PyQt6'"
**Solution:** Ensure pip installed successfully:
```bash
pip list | findstr PyQt6
```

### Azure/GCP packages fail to install
**Solution:** These are optional. Install AWS-only version:
```bash
pip install PyQt6 PyQt6-WebEngine boto3 reportlab pyqtgraph
```

---

## First Run

1. **Launch:** `python cloudstrike_ui.py`
2. **Watch splash screen** (Terminal boot animation + radar sweep)
3. **Choose mode:**
   - **Demo Mode** - No credentials needed, explore with sample data
   - **Real Scan** - Enter cloud credentials in Vault page

---

## Demo Mode (No Credentials Needed)

Perfect for testing the application:

1. Launch CloudStrike
2. On the Vault page, click **"Launch in Demo Mode"**
3. Explore all features with pre-loaded sample findings
4. Test PDF export, threat map, compliance checks, etc.

---

## Real Scanning Setup

### AWS Setup
1. Create IAM user with policies:
   - `SecurityAudit` (AWS managed policy)
   - `ReadOnlyAccess` (AWS managed policy)
2. Generate Access Key + Secret Key
3. Enter in CloudStrike Vault page

### Azure Setup
1. Create Service Principal:
   ```bash
   az ad sp create-for-rbac --name CloudStrike --role Reader
   ```
2. Note: Client ID, Client Secret, Tenant ID
3. Get Subscription ID: `az account show --query id`
4. Enter in CloudStrike Vault page

### GCP Setup
1. Create Service Account in GCP Console
2. Grant roles: `Viewer`, `Security Reviewer`
3. Download JSON key file
4. Paste JSON content in CloudStrike Vault page

---

## Quick Command Reference

```bash
# Clone project
git clone <repository-url>
cd CloudStrike_Final_Version

# Install dependencies
pip install -r requirements.txt

# Run application
python cloudstrike_ui.py

# Check Python version
python --version

# List installed packages
pip list

# Upgrade pip
python -m pip install --upgrade pip
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| Python | 3.11 | 3.12+ |
| RAM | 4 GB | 8 GB |
| Disk Space | 500 MB | 1 GB |
| Internet | Required | Required |

---

## Support

If you encounter issues:

1. Check Python version: `python --version` (must be 3.11+)
2. Verify all packages installed: `pip list`
3. Try running as Administrator
4. Check Windows Firewall isn't blocking Python
5. Review error messages in Command Prompt

---

## What's Next?

After installation:

1. ✅ Run in Demo Mode to explore features
2. ✅ Set up cloud credentials for real scanning
3. ✅ Configure scan settings (depth, regions, notifications)
4. ✅ Run your first security scan
5. ✅ Generate PDF reports
6. ✅ Try attack simulations

---

**Ready to scan? Launch CloudStrike and start securing your cloud! ⚡**
