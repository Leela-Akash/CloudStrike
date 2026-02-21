# GCP Findings Display Fixes

## Issues Fixed

### Issue 1: GCP Findings Not Showing in Findings Table
**Problem**: GCP scanner was emitting findings but they weren't appearing in the findings table

**Root Cause**: `on_finding()` method in page_vault.py was using `self.parent_window` which could be None or not properly set

**Before**:
```python
def on_finding(self, finding):
    if self.parent_window and hasattr(self.parent_window, 'pages'):
        self.parent_window.pages["Findings"].add_finding(finding)
```

**After**:
```python
def on_finding(self, finding):
    """Called when scanner emits a finding - add to findings page and activity feed"""
    try:
        # Add finding to findings page
        main = self.window()  # ✓ Use self.window() instead of self.parent_window
        if main and hasattr(main, 'pages'):
            findings_page = main.pages.get("Findings")
            if findings_page:
                findings_page.add_finding(finding)
        
        # Show notifications if enabled
        from settings_manager import get_all_settings
        settings = get_all_settings()
        sev = finding.get('severity', '')
        if sev == 'CRITICAL' and settings.get('notify_critical'):
            self.show_notification(finding)
        elif sev == 'HIGH' and settings.get('notify_high'):
            self.show_notification(finding)
    except Exception as e:
        import logging
        logging.error(f"on_finding error: {e}")
```

**Changes**:
- Use `self.window()` instead of `self.parent_window` (more reliable)
- Added try/except with logging for debugging
- Added null checks for findings_page

**Signal Connections Verified**:
All scanner signals (AWS, Azure, GCP) are connected identically in `start_scan()`:
```python
self.scanner.scan_progress.connect(
    self.on_progress, Qt.ConnectionType.QueuedConnection
)
self.scanner.finding_found.connect(
    self.on_finding, Qt.ConnectionType.QueuedConnection
)
self.scanner.scan_complete.connect(
    self.on_complete, Qt.ConnectionType.QueuedConnection
)
self.scanner.scan_error.connect(
    self.on_error, Qt.ConnectionType.QueuedConnection
)
```
✓ GCP scanner uses same signal connection pattern as AWS/Azure

---

### Issue 2: Compliance Showing 100% PASS for GCP Scan
**Problem**: When scanning GCP, compliance page showed all AWS CIS checks as PASS (100% score)

**Root Cause**: Compliance page was calculating PASS/FAIL based on AWS findings, but GCP findings don't match AWS service names, so all checks defaulted to PASS

**Before**:
```python
def show_non_aws_message(self, provider):
    # Replaced entire table with single message cell
    self.table.setRowCount(1)
    self.table.setColumnCount(1)
    # ... showed message in one big cell
```

**After**:
```python
def show_non_aws_message(self, provider):
    """Show N/A status for non-AWS providers"""
    from PyQt6.QtWidgets import QTableWidgetItem
    from PyQt6.QtGui import QColor
    from PyQt6.QtCore import Qt
    
    # Update all status cells to show N/A
    for row in range(self.table.rowCount()):
        status_item = QTableWidgetItem(f"N/A — {provider}")
        status_item.setForeground(QColor('#888888'))
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, status_item)
    
    # Update compliance score to N/A
    main = self.window()
    if main:
        from PyQt6.QtWidgets import QLabel
        labels = main.findChildren(QLabel, 'statValue')
        if len(labels) >= 3:
            labels[2].setText("N/A")
```

**Changes**:
- Keep table structure intact (13 rows, 3 columns)
- Update Status column (column 2) to show "N/A — GCP" or "N/A — Azure"
- Set compliance score stat card to "N/A" instead of percentage
- Grey color (#888888) for N/A status

**Result**:
- GCP scan shows: Control ID | Description | N/A — GCP
- Azure scan shows: Control ID | Description | N/A — Azure
- AWS scan shows: Control ID | Description | PASS/FAIL
- Compliance score: N/A for GCP/Azure, percentage for AWS

---

### Issue 3: Provider Not Passed to Compliance Update
**Problem**: Already fixed in previous service isolation audit

**Verification**: `on_complete()` in page_vault.py correctly:
1. Retrieves provider from database
2. Passes provider to `compliance.update_from_findings(findings, provider)`

```python
# Get provider from database
try:
    conn = sqlite3.connect(self.db_path)
    row = conn.execute("SELECT provider FROM credentials ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    provider = row[0] if row else 'AWS'
except:
    provider = 'AWS'

# Update compliance page with provider info
try:
    compliance = main.pages.get("Compliance")
    if compliance:
        compliance.update_from_findings(findings, provider)
except Exception as e:
    pass
```

✓ Already implemented correctly

---

## Testing Checklist

### GCP Scan - Findings Display
- [x] GCP findings appear in Findings table
- [x] Service column shows "GCS", "Compute", "IAM" (not empty)
- [x] Region column shows "us-central1", "europe-west1" (not empty)
- [x] Severity colors correct (CRITICAL=red, HIGH=orange, etc.)
- [x] Status calculated correctly (CRITICAL/HIGH=OPEN, MEDIUM=IN PROGRESS, LOW=MONITORED)

### GCP Scan - Compliance Page
- [x] All 13 rows show "N/A — GCP" in Status column
- [x] Status text is grey (#888888)
- [x] Control ID and Description columns unchanged
- [x] Compliance Score stat card shows "N/A"
- [x] Table structure preserved (not replaced with message)

### Azure Scan - Compliance Page
- [x] All 13 rows show "N/A — Azure" in Status column
- [x] Compliance Score stat card shows "N/A"

### AWS Scan - Compliance Page
- [x] Status shows "PASS" or "FAIL" based on findings
- [x] Compliance Score shows percentage (e.g., "62%")

---

## Files Modified

1. **page_vault.py**
   - Line 398: Updated `on_finding()` to use `self.window()` instead of `self.parent_window`
   - Added try/except with logging
   - Added null checks for findings_page

2. **page_compliance.py**
   - Line 127: Updated `show_non_aws_message()` to preserve table structure
   - Sets Status column to "N/A — {provider}" for each row
   - Sets compliance score to "N/A"

---

## Before vs After

### Before (GCP Scan):
- Findings table: Empty (findings not showing)
- Compliance: All PASS (100% score)

### After (GCP Scan):
- Findings table: Shows all GCP findings with correct services/regions
- Compliance: All "N/A — GCP" with "N/A" score

### Before (Azure Scan):
- Compliance: All PASS (100% score)

### After (Azure Scan):
- Compliance: All "N/A — Azure" with "N/A" score

### AWS Scan (Unchanged):
- Findings table: Shows AWS findings
- Compliance: PASS/FAIL based on findings with percentage score

---

## Final Status

✅ **GCP findings now display correctly in findings table**
✅ **Compliance page shows N/A for GCP/Azure scans**
✅ **Compliance score shows N/A instead of 100%**
✅ **All scanner signals connected identically**
✅ **Provider detection working correctly**

**All issues resolved - GCP/Azure scans now display correctly.**
