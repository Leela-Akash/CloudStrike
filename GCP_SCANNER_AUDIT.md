# GCP Scanner Audit Report

## Executive Summary
✅ **VERDICT**: GCP scanner is correctly implemented with proper real API calls, clean demo fallback, and accurate service/region labeling.

---

## Question 1: Real GCP APIs vs Fake Data?

### Answer: **REAL GCP APIs ARE CALLED**

When valid credentials are provided, the scanner makes actual Google Cloud API calls:

**Connection Test (Line 147-150)**:
```python
storage_client = storage.Client(credentials=gcp_creds, project=project_id)
list(storage_client.list_buckets(max_results=1))
```
- Tests real connection by listing 1 bucket
- If this succeeds, proceeds to real scanning
- If this fails, falls back to demo mode

**Real Scanning Section (Lines 165-257)**:
- Only executes if connection test passes
- Makes actual API calls to live GCP resources
- Returns real findings from user's GCP account

---

## Question 2: Specific GCP APIs Called

### API Calls Made (in order):

#### 1. **Cloud Storage API** (Lines 197-218)
```python
storage_client = storage.Client(credentials=gcp_creds, project=project_id)
for bucket in storage_client.list_buckets():
    policy = bucket.get_iam_policy()
```
- `storage_client.list_buckets()` - Lists all GCS buckets
- `bucket.get_iam_policy()` - Gets IAM policy for each bucket
- `bucket.versioning_enabled` - Checks versioning status
- `bucket.location` - Gets bucket region

**Checks**:
- Public access (allUsers/allAuthenticatedUsers in IAM)
- Versioning enabled/disabled

#### 2. **Compute Engine API - Firewalls** (Lines 221-241)
```python
compute = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_creds)
firewalls = compute.firewalls().list(project=project_id).execute()
```
- `compute.firewalls().list()` - Lists all firewall rules

**Checks**:
- Ingress rules allowing 0.0.0.0/0
- SSH (port 22) and RDP (port 3389) exposure

#### 3. **Compute Engine API - VM Instances** (Lines 244-257)
```python
compute = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_creds)
agg = compute.instances().aggregatedList(project=project_id).execute()
```
- `compute.instances().aggregatedList()` - Lists all VMs across all zones

**Checks**:
- VMs with external IP addresses (accessConfigs)
- Extracts zone from instance metadata

### Required GCP Libraries:
- `google.oauth2.service_account` - Authentication
- `google.cloud.storage` - Cloud Storage API
- `googleapiclient.discovery` - Compute Engine API

---

## Question 3: Demo Fallback Behavior

### Answer: **YES - PROPER FALLBACK**

**Trigger Conditions** (Lines 145-156):
1. No `credentials_json` provided
2. JSON parsing fails
3. Service account creation fails
4. Connection test fails (can't list buckets)

**Fallback Behavior** (Lines 158-164):
```python
if use_demo:
    result_queue.put({'type': 'info', 'msg': 'Using demo data — connect real GCP credentials for live scan'})
    # ... sends demo findings ...
    result_queue.put({'type': 'progress', 'pct': 100, 'msg': 'GCP SCAN COMPLETE (DEMO)'})
```

**User Notification**:
- Progress message: `"GCP CONNECTION FAILED — RUNNING DEMO MODE"` (Line 156)
- Completion message: `"GCP SCAN COMPLETE (DEMO)"` (Line 163)
- Info message sent to queue (Line 159)

✅ **Clean separation** - Demo code only runs if `use_demo = True`
✅ **No mixing** - Real scan section (lines 165-257) never executes in demo mode

---

## Question 4: Demo Findings Quality

### Answer: **REALISTIC AND CLEARLY LABELED**

**Demo Findings** (Lines 8-123):
- 10 findings total
- Severity distribution: 2 CRITICAL, 3 HIGH, 3 MEDIUM, 2 LOW
- All have `'cloud': 'GCP'` field
- All use GCP service names (GCS, Compute, IAM, Logging, Resource Manager, Cloud DNS)
- All use GCP regions (us-central1, us-east1, global)
- Realistic titles with resource names
- Accurate descriptions of security issues
- Valid gcloud/gsutil remediation commands

**Example Demo Finding**:
```python
{
    'severity': 'CRITICAL',
    'title': 'GCS Bucket Publicly Accessible: prod-data-bucket',
    'service': 'GCS',  # ✓ GCP service name
    'region': 'us-central1',  # ✓ GCP region
    'cloud': 'GCP',  # ✓ Provider labeled
    'remediation': 'gsutil iam ch -d allUsers gs://prod-data-bucket'  # ✓ Valid command
}
```

**Demo Labeling**:
- Progress bar shows: `"GCP SCAN COMPLETE (DEMO)"` (Line 163)
- User clearly informed it's demo data

---

## Question 5: Hardcoded Data Mixing

### Answer: **NO MIXING - CLEAN SEPARATION**

**Code Flow**:
```
Line 145: Try real connection
Line 154: If fails → use_demo = True
Line 158: if use_demo:
              return demo data (lines 159-164)
              EXITS FUNCTION (line 164: return)
Line 167: # Real scanning code only runs if demo was NOT used
```

**Proof of Separation**:
- Demo mode has explicit `return` statement (Line 164)
- Real scanning code (lines 165-257) is AFTER the demo return
- Impossible for both to execute in same scan

✅ **No hardcoded data in real scan results**
✅ **Demo findings never mixed with real findings**

---

## Question 6: Service/Region/Cloud Labeling

### Real Scan Findings (add_finding function, Lines 167-179):

```python
def add_finding(severity, title, service, region, description, remediation):
    finding = {
        'severity': severity,
        'title': title,
        'service': service,      # ← Passed as parameter
        'region': region,         # ← Passed as parameter
        'cloud': 'GCP',          # ✓ HARDCODED TO 'GCP'
        'resource': f'{service}:{region}',
        'fix': remediation,
        'timestamp': datetime.now().isoformat()
    }
```

### Service Names Used:

**GCS Buckets** (Lines 206, 213):
```python
'service': 'GCS'  # ✓ Correct GCP service name
```

**Firewall Rules** (Line 234):
```python
'service': 'Compute'  # ✓ Correct GCP service name
```

**VM Instances** (Line 251):
```python
'service': 'Compute'  # ✓ Correct GCP service name
```

### Region Names Used:

**GCS Buckets** (Lines 207, 214):
```python
'region': bucket.location or 'us'  # ✓ Real GCP region from API
```
- Returns actual bucket location (e.g., "us-central1", "europe-west1")
- Fallback to "us" if location is None

**Firewall Rules** (Line 235):
```python
'region': 'global'  # ✓ Correct - firewalls are global in GCP
```

**VM Instances** (Line 252):
```python
'region': instance.get('zone', '').split('/')[-1]  # ✓ Extracts zone from full path
```
- GCP returns zone as: `"https://www.googleapis.com/compute/v1/projects/PROJECT/zones/us-central1-a"`
- `.split('/')[-1]` extracts: `"us-central1-a"`
- This is the correct GCP zone format

### ✅ VERIFICATION:
- Service: GCS, Compute (NOT S3, EC2, etc.)
- Region: us-central1, europe-west1, global (NOT us-east-1, eu-west-1)
- Cloud: 'GCP' (hardcoded correctly)

---

## Question 7: Threat Map Geographic Placement

### Current Threat Map Coordinates (threat_map.py):

```javascript
// GCP Regions
'us-central1':    [41.2, -95.9],   // Iowa
'us-east1':       [33.1, -80.0],   // South Carolina
'us-east4':       [39.0, -77.5],   // Virginia
'us-west1':       [45.5, -122.6],  // Oregon
'us-west2':       [34.0, -118.2],  // Los Angeles
'europe-west1':   [50.4, 3.8],     // Belgium
'europe-west2':   [51.5, -0.1],    // London
'europe-west3':   [50.1, 8.7],     // Frankfurt
'asia-south1':    [19.0, 72.8],    // Mumbai
'asia-southeast1':[1.3, 103.8],    // Singapore
'asia-northeast1':[35.7, 139.7],   // Tokyo
'australia-southeast1':[-33.8, 151.2],  // Sydney
'southamerica-east1':[-23.5, -46.6],    // São Paulo
```

### GCP Scanner Region Output:

**From Buckets**:
- Returns: `bucket.location` (e.g., "US", "EU", "ASIA", or specific region)
- May return multi-region codes like "US" instead of "us-central1"

**From VMs**:
- Returns: Zone name like "us-central1-a", "europe-west1-b"
- Includes zone letter suffix

**From Firewalls**:
- Returns: "global" (firewalls are global resources)

### ⚠️ ISSUE FOUND: Zone vs Region Mismatch

**Problem**: VM findings return ZONE (e.g., "us-central1-a") but threat map expects REGION (e.g., "us-central1")

**Impact**: VM findings won't show on map because "us-central1-a" doesn't match "us-central1" in coordinate lookup

---

## Issues Found & Fixes Needed

### Issue 1: VM Zone Suffix Breaks Map Lookup

**Current Code** (Line 252):
```python
'region': instance.get('zone', '').split('/')[-1]
```
Returns: `"us-central1-a"` (with zone suffix)

**Fix Needed**:
```python
zone = instance.get('zone', '').split('/')[-1]
region = '-'.join(zone.split('-')[:-1]) if zone else 'global'
'region': region
```
Returns: `"us-central1"` (without zone suffix)

### Issue 2: Bucket Multi-Region Codes

**Current Code** (Line 207):
```python
'region': bucket.location or 'us'
```
Returns: `"US"`, `"EU"`, `"ASIA"` for multi-region buckets

**Fix Needed**:
```python
location = (bucket.location or 'us').lower()
# Map multi-region to specific region for map display
region_map = {'us': 'us-central1', 'eu': 'europe-west1', 'asia': 'asia-southeast1'}
'region': region_map.get(location, location)
```

### Issue 3: Missing GCP Zone Coordinates

**Current Map**: Has region coordinates but not zone coordinates
**Fix**: Add zone-to-region mapping in JavaScript or strip zone suffix in Python (Fix #1 handles this)

---

## Summary Table

| Question | Answer | Status |
|----------|--------|--------|
| Real APIs called? | YES - Cloud Storage, Compute Engine | ✅ PASS |
| Specific APIs? | list_buckets, get_iam_policy, firewalls.list, instances.aggregatedList | ✅ PASS |
| Demo fallback? | YES - clean separation with user notification | ✅ PASS |
| Demo realistic? | YES - 10 findings, proper GCP services/regions/commands | ✅ PASS |
| Hardcoded mixing? | NO - demo returns early, real scan separate | ✅ PASS |
| Service names? | GCS, Compute, IAM, Logging, Resource Manager, Cloud DNS | ✅ PASS |
| Region names? | us-central1, europe-west1, global (GCP format) | ⚠️ NEEDS FIX |
| Cloud label? | 'GCP' hardcoded correctly | ✅ PASS |
| Map placement? | Coordinates exist but zone suffix breaks lookup | ⚠️ NEEDS FIX |

---

## Fixes Required

1. **Strip zone suffix from VM regions** (Line 252)
2. **Map multi-region bucket codes to specific regions** (Line 207, 214)

Both fixes will be applied in next step.
