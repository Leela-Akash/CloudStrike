import multiprocessing
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

# Windows multiprocessing fix
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set


# ── DEMO DATA FALLBACK ──
GCP_DEMO_FINDINGS = [
    {
        'severity': 'CRITICAL',
        'title': 'GCS Bucket Publicly Accessible: prod-data-bucket',
        'service': 'GCS',
        'region': 'us-central1',
        'description': 'GCS bucket prod-data-bucket has allUsers granted Storage Object Viewer. Anyone on internet can read all objects.',
        'remediation': 'gsutil iam ch -d allUsers gs://prod-data-bucket',
        'resource': 'GCS:us-central1',
        'fix': 'gsutil iam ch -d allUsers gs://prod-data-bucket',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'CRITICAL',
        'title': 'Service Account Has Owner Role: sa@project.iam.gserviceaccount.com',
        'service': 'IAM',
        'region': 'global',
        'description': 'Service account has primitive Owner role granting full access to all GCP services.',
        'remediation': 'gcloud projects remove-iam-policy-binding PROJECT_ID --member=serviceAccount:sa@project.iam.gserviceaccount.com --role=roles/owner',
        'resource': 'IAM:global',
        'fix': 'gcloud projects remove-iam-policy-binding PROJECT_ID --member=serviceAccount:sa@project.iam.gserviceaccount.com --role=roles/owner',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'HIGH',
        'title': 'Firewall Rule Allows SSH from 0.0.0.0/0',
        'service': 'Compute',
        'region': 'us-central1',
        'description': 'Firewall rule default-allow-ssh allows inbound SSH from all IP addresses.',
        'remediation': 'gcloud compute firewall-rules update default-allow-ssh --source-ranges=YOUR_IP/32',
        'resource': 'Compute:us-central1',
        'fix': 'gcloud compute firewall-rules update default-allow-ssh --source-ranges=YOUR_IP/32',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'HIGH',
        'title': 'Firewall Rule Allows RDP from 0.0.0.0/0',
        'service': 'Compute',
        'region': 'us-central1',
        'description': 'Firewall rule default-allow-rdp allows inbound RDP from all IP addresses.',
        'remediation': 'gcloud compute firewall-rules update default-allow-rdp --source-ranges=YOUR_IP/32',
        'resource': 'Compute:us-central1',
        'fix': 'gcloud compute firewall-rules update default-allow-rdp --source-ranges=YOUR_IP/32',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'HIGH',
        'title': 'Cloud Audit Logging Disabled for Project',
        'service': 'Logging',
        'region': 'global',
        'description': 'Cloud Audit Logs are not enabled for all services. Attacker activity may go undetected.',
        'remediation': 'gcloud projects get-iam-policy PROJECT_ID --format=json | enable auditConfigs for allServices',
        'resource': 'Logging:global',
        'fix': 'gcloud projects get-iam-policy PROJECT_ID --format=json | enable auditConfigs for allServices',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'MEDIUM',
        'title': 'VM Instance Has Public IP: web-server-prod',
        'service': 'Compute',
        'region': 'us-central1',
        'description': 'VM instance web-server-prod has an external IP address directly exposed to internet.',
        'remediation': 'gcloud compute instances delete-access-config web-server-prod --access-config-name="External NAT"',
        'resource': 'Compute:us-central1',
        'fix': 'gcloud compute instances delete-access-config web-server-prod --access-config-name="External NAT"',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'MEDIUM',
        'title': 'GCS Bucket Versioning Disabled: backup-bucket',
        'service': 'GCS',
        'region': 'us-central1',
        'description': 'Bucket backup-bucket does not have versioning enabled. Data loss risk.',
        'remediation': 'gsutil versioning set on gs://backup-bucket',
        'resource': 'GCS:us-central1',
        'fix': 'gsutil versioning set on gs://backup-bucket',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'MEDIUM',
        'title': 'VM OS Login Disabled: db-server-01',
        'service': 'Compute',
        'region': 'us-east1',
        'description': 'VM db-server-01 does not have OS Login enabled. SSH key management is manual.',
        'remediation': 'gcloud compute instances add-metadata db-server-01 --metadata enable-oslogin=TRUE',
        'resource': 'Compute:us-east1',
        'fix': 'gcloud compute instances add-metadata db-server-01 --metadata enable-oslogin=TRUE',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'LOW',
        'title': 'Project Has No Resource Labels',
        'service': 'Resource Manager',
        'region': 'global',
        'description': 'GCP project has no labels applied. Makes cost tracking and resource management difficult.',
        'remediation': 'gcloud resource-manager tags keys create --parent=projects/PROJECT_ID environment=production',
        'resource': 'Resource Manager:global',
        'fix': 'gcloud resource-manager tags keys create --parent=projects/PROJECT_ID environment=production',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
    {
        'severity': 'LOW',
        'title': 'Cloud DNS DNSSEC Disabled',
        'service': 'Cloud DNS',
        'region': 'global',
        'description': 'DNSSEC is not enabled on managed zones. Vulnerable to DNS spoofing attacks.',
        'remediation': 'gcloud dns managed-zones update ZONE_NAME --dnssec-state=on',
        'resource': 'Cloud DNS:global',
        'fix': 'gcloud dns managed-zones update ZONE_NAME --dnssec-state=on',
        'cloud': 'GCP',
        'timestamp': datetime.now().isoformat()
    },
]


def run_gcp_scan_process(credentials, result_queue):
    """Runs in separate process — tries real GCP, falls back to demo data"""

    use_demo = False

    # Try real GCP connection first
    try:
        from google.oauth2 import service_account
        from google.cloud import storage
        import json

        result_queue.put({'type': 'progress', 'pct': 5, 'msg': 'CONNECTING TO GCP...'})

        # Parse and test credentials
        if credentials.get('credentials_json'):
            try:
                creds_info = json.loads(credentials['credentials_json'])
                gcp_creds = service_account.Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                project_id = creds_info.get('project_id', credentials.get('project_id', ''))
            except json.JSONDecodeError:
                result_queue.put({'type': 'fatal', 'msg': '✗ GCP AUTHENTICATION FAILED\n\nInvalid service account JSON format. Please check:\n• JSON is properly formatted\n• Contains all required fields\n• No extra characters or line breaks'})
                return
            except Exception as e:
                result_queue.put({'type': 'fatal', 'msg': f'✗ GCP CREDENTIAL ERROR\n\n{str(e)}'})
                return
        else:
            use_demo = True

        if not use_demo:
            # Test connection with actual API call
            try:
                storage_client = storage.Client(credentials=gcp_creds, project=project_id)
                list(storage_client.list_buckets(max_results=1))
                result_queue.put({'type': 'progress', 'pct': 10, 'msg': 'GCP CONNECTION SUCCESSFUL'})
            except Exception as e:
                error_str = str(e)
                if 'invalid_grant' in error_str or 'unauthorized' in error_str.lower() or 'permission denied' in error_str.lower():
                    result_queue.put({'type': 'fatal', 'msg': f'✗ GCP AUTHENTICATION FAILED\n\nInvalid GCP credentials. Please check:\n• Service account JSON is correct\n• Service account has required permissions\n• Project ID matches\n\nError: {error_str}'})
                    return
                else:
                    result_queue.put({'type': 'fatal', 'msg': f'✗ GCP CONNECTION FAILED\n\n{error_str}'})
                    return

    except Exception as e:
        use_demo = True
        result_queue.put({'type': 'progress', 'pct': 10, 'msg': 'GCP CONNECTION FAILED — RUNNING DEMO MODE'})

    if use_demo:
        # Send demo findings with realistic delays
        result_queue.put({'type': 'info', 'msg': 'Using demo data — connect real GCP credentials for live scan'})
        total = len(GCP_DEMO_FINDINGS)
        for i, finding in enumerate(GCP_DEMO_FINDINGS):
            pct = int(10 + (i / total) * 85)
            result_queue.put({'type': 'progress', 'pct': pct, 'msg': f'SCANNING {finding["service"].upper()}...'})
            time.sleep(0.4)
            result_queue.put({'type': 'finding', 'data': finding})

        result_queue.put({'type': 'progress', 'pct': 100, 'msg': 'GCP SCAN COMPLETE (DEMO)'})
        result_queue.put({'type': 'complete', 'data': GCP_DEMO_FINDINGS})
        return

    # ── REAL GCP SCANNING ──
    findings = []

    def add_finding(severity, title, service, region, description, remediation):
        finding = {
            'severity': severity,
            'title': title,
            'service': service,
            'region': region,
            'description': description,
            'remediation': remediation,
            'resource': f'{service}:{region}',
            'fix': remediation,
            'cloud': 'GCP',
            'timestamp': datetime.now().isoformat()
        }
        findings.append(finding)
        result_queue.put({'type': 'finding', 'data': finding})

    try:
        # GCS BUCKET CHECKS
        result_queue.put({'type': 'progress', 'pct': 20, 'msg': 'GCS BUCKETS'})
        try:
            storage_client = storage.Client(credentials=gcp_creds, project=project_id)
            for bucket in storage_client.list_buckets():
                try:
                    policy = bucket.get_iam_policy()
                    for binding in policy.bindings:
                        if 'allUsers' in binding['members'] or 'allAuthenticatedUsers' in binding['members']:
                            # Map multi-region codes to specific regions for map display
                            location = (bucket.location or 'us').lower()
                            region_map = {'us': 'us-central1', 'eu': 'europe-west1', 'asia': 'asia-southeast1'}
                            region = region_map.get(location, location)
                            
                            add_finding(
                                'CRITICAL',
                                f'GCS Bucket Public: {bucket.name}',
                                'GCS',
                                region,
                                f'Bucket {bucket.name} is publicly accessible.',
                                f'gsutil iam ch -d allUsers gs://{bucket.name}'
                            )
                except: pass

                if not bucket.versioning_enabled:
                    # Map multi-region codes to specific regions for map display
                    location = (bucket.location or 'us').lower()
                    region_map = {'us': 'us-central1', 'eu': 'europe-west1', 'asia': 'asia-southeast1'}
                    region = region_map.get(location, location)
                    
                    add_finding(
                        'MEDIUM',
                        f'GCS Versioning Disabled: {bucket.name}',
                        'GCS',
                        region,
                        f'Bucket {bucket.name} versioning not enabled — deleted files unrecoverable.',
                        f'gsutil versioning set on gs://{bucket.name}'
                    )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'GCS check failed: {e}'})

        # FIREWALL RULES
        result_queue.put({'type': 'progress', 'pct': 50, 'msg': 'GCP FIREWALL RULES'})
        try:
            import googleapiclient.discovery
            compute = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_creds)
            firewalls = compute.firewalls().list(project=project_id).execute()
            for fw in firewalls.get('items', []):
                if fw.get('direction') == 'INGRESS':
                    for allowed in fw.get('allowed', []):
                        source_ranges = fw.get('sourceRanges', [])
                        if '0.0.0.0/0' in source_ranges:
                            ports = allowed.get('ports', [])
                            
                            # Check for all traffic allowed
                            if not ports:
                                add_finding(
                                    'CRITICAL',
                                    f'Firewall Allows ALL Traffic: {fw["name"]}',
                                    'Compute',
                                    'global',
                                    f'Firewall rule {fw["name"]} allows all ingress traffic from internet.',
                                    f'gcloud compute firewall-rules delete {fw["name"]}'
                                )
                            else:
                                sev = 'CRITICAL' if any(p in ['22', '3389'] for p in ports) else 'HIGH'
                                add_finding(
                                    sev,
                                    f'Open Firewall: {fw["name"]} port {ports}',
                                    'Compute',
                                    'global',
                                    f'Firewall {fw["name"]} allows inbound from 0.0.0.0/0.',
                                    f'gcloud compute firewall-rules update {fw["name"]} --source-ranges=YOUR_IP/32'
                                )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'Firewall check failed: {e}'})

        # VM INSTANCES
        result_queue.put({'type': 'progress', 'pct': 75, 'msg': 'GCP VM INSTANCES'})
        try:
            compute = googleapiclient.discovery.build('compute', 'v1', credentials=gcp_creds)
            agg = compute.instances().aggregatedList(project=project_id).execute()
            for zone_name, zone_data in agg.get('items', {}).items():
                for instance in zone_data.get('instances', []):
                    zone = instance.get('zone', '').split('/')[-1]
                    region = '-'.join(zone.split('-')[:-1]) if zone and '-' in zone else 'global'
                    
                    # Check for public IPs
                    for iface in instance.get('networkInterfaces', []):
                        if iface.get('accessConfigs'):
                            add_finding(
                                'MEDIUM',
                                f'VM Public IP: {instance["name"]}',
                                'Compute',
                                region,
                                f'VM {instance["name"]} has external IP.',
                                f'gcloud compute instances delete-access-config {instance["name"]} --access-config-name="External NAT" --zone {zone}'
                            )
                    
                    # Check for default service account
                    for sa in instance.get('serviceAccounts', []):
                        if 'compute@developer' in sa.get('email', '') or '-compute@developer' in sa.get('email', ''):
                            add_finding(
                                'HIGH',
                                f'VM Uses Default Service Account: {instance["name"]}',
                                'Compute',
                                region,
                                f'VM {instance["name"]} uses default compute service account with broad permissions.',
                                f'gcloud compute instances set-service-account {instance["name"]} --service-account=custom-sa@{project_id}.iam.gserviceaccount.com --zone {zone}'
                            )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'VM check failed: {e}'})

        result_queue.put({'type': 'progress', 'pct': 100, 'msg': 'GCP SCAN COMPLETE'})
        result_queue.put({'type': 'complete', 'data': findings})

    except Exception as e:
        import traceback
        result_queue.put({'type': 'fatal', 'msg': f'GCP scan failed: {e}\n{traceback.format_exc()}'})


class GCPScanner(QThread):
    finding_found = pyqtSignal(dict)
    scan_progress = pyqtSignal(int, str)
    scan_complete = pyqtSignal(list)
    scan_error    = pyqtSignal(str)

    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials

    def run(self):
        ctx = multiprocessing.get_context('spawn')
        result_queue = ctx.Queue()

        process = ctx.Process(
            target=run_gcp_scan_process,
            args=(self.credentials, result_queue),
            daemon=True
        )
        process.start()

        while True:
            try:
                msg = result_queue.get(timeout=120)
                if msg['type'] == 'progress':
                    self.scan_progress.emit(msg['pct'], msg['msg'])
                elif msg['type'] == 'finding':
                    self.finding_found.emit(msg['data'])
                elif msg['type'] == 'complete':
                    self.scan_complete.emit(msg['data'])
                    break
                elif msg['type'] == 'fatal':
                    self.scan_error.emit(msg['msg'])
                    break
                elif msg['type'] in ['info', 'error_check']:
                    pass
            except Exception as e:
                self.scan_error.emit(f'GCP timeout: {e}')
                break

        process.join(timeout=5)
        if process.is_alive():
            process.terminate()


if __name__ == '__main__':
    multiprocessing.freeze_support()
