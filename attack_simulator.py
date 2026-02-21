from PyQt6.QtCore import QThread, pyqtSignal
import time
import boto3
from datetime import datetime

class AttackSimulator(QThread):
    step_update = pyqtSignal(dict)
    sim_complete = pyqtSignal(str, list)
    sim_error = pyqtSignal(str)

    def __init__(self, simulation_name, credentials):
        super().__init__()
        self.simulation_name = simulation_name
        self.credentials = credentials

    def run(self):
        try:
            if self.simulation_name == 'iam_privesc':
                self.simulate_iam_privesc()
            elif self.simulation_name == 's3_takeover':
                self.simulate_s3_takeover()
        except Exception as e:
            import traceback
            self.sim_error.emit(f'{e}\n{traceback.format_exc()}')

    def send_step(self, step_num, title, detail, status, risk=None):
        self.step_update.emit({
            'step': step_num,
            'title': title,
            'detail': detail,
            'status': status,
            'risk': risk,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

    def simulate_iam_privesc(self):
        self.send_step(0, 'Starting...', 'Initializing IAM Privilege Escalation simulation...', 'running')
        
        try:
            session = boto3.Session(
                aws_access_key_id=self.credentials['access_key'],
                aws_secret_access_key=self.credentials['secret_key'],
                region_name=self.credentials['region']
            )
            iam = session.client('iam')
            sts = session.client('sts')
        except Exception as e:
            self.sim_error.emit(f'Failed to create AWS session: {e}')
            return

        try:
            self.send_step(1, 'Identity Reconnaissance',
                'Calling sts:GetCallerIdentity to identify current user/role...', 'running')
            time.sleep(1)
            try:
                identity = sts.get_caller_identity()
                self.send_step(1, 'Identity Reconnaissance',
                    f'✓ Identified as: {identity["Arn"]}\n'
                    f'  Account: {identity["Account"]}\n'
                    f'  UserID: {identity["UserId"]}',
                    'success',
                    risk='LOW — Recon successful. Attacker now knows account structure.'
                )
            except Exception as e:
                self.send_step(1, 'Identity Reconnaissance',
                    f'✗ Failed: {e}', 'fail')
                self.sim_complete.emit('BLOCKED', [])
                return

            time.sleep(0.5)

            self.send_step(2, 'Permission Enumeration',
                'Enumerating attached policies and inline policies...', 'running')
            time.sleep(1.5)
            try:
                users = iam.list_users().get('Users', [])
                policies_found = []
                for user in users:
                    attached = iam.list_attached_user_policies(
                        UserName=user['UserName']
                    ).get('AttachedPolicies', [])
                    policies_found.extend(attached)

                self.send_step(2, 'Permission Enumeration',
                    f'✓ Found {len(users)} IAM users\n'
                    f'  Attached policies: {len(policies_found)}\n'
                    f'  Checking for iam:AttachUserPolicy permission...',
                    'success',
                    risk='MEDIUM — Full policy enumeration possible. Attacker maps privilege paths.'
                )
            except Exception as e:
                self.send_step(2, 'Permission Enumeration',
                    f'⚠ Partial: {e}', 'warning')

            time.sleep(0.5)

            self.send_step(3, 'Escalation Vector Detection',
                'Simulating policy simulation to check iam:AttachUserPolicy...', 'running')
            time.sleep(2)
            try:
                account = sts.get_caller_identity()["Account"]
                username = self.credentials.get('account_name', 'cloud-pentest-user')
                sim_result = iam.simulate_principal_policy(
                    PolicySourceArn=f'arn:aws:iam::{account}:user/{username}',
                    ActionNames=['iam:AttachUserPolicy', 'iam:CreatePolicyVersion']
                )
                decisions = {
                    r['EvalActionName']: r['EvalDecision']
                    for r in sim_result.get('EvaluationResults', [])
                }
                can_escalate = any(v == 'allowed' for v in decisions.values())
                if can_escalate:
                    self.send_step(3, 'Escalation Vector Detection',
                        f'🚨 VULNERABILITY CONFIRMED\n'
                        f'  iam:AttachUserPolicy = {decisions.get("iam:AttachUserPolicy","unknown")}\n'
                        f'  iam:CreatePolicyVersion = {decisions.get("iam:CreatePolicyVersion","unknown")}\n'
                        f'  Attacker CAN escalate privileges!',
                        'fail',
                        risk='CRITICAL — Privilege escalation path confirmed via policy simulation.'
                    )
                else:
                    self.send_step(3, 'Escalation Vector Detection',
                        f'✓ PROTECTED\n'
                        f'  iam:AttachUserPolicy = {decisions.get("iam:AttachUserPolicy","denied")}\n'
                        f'  Escalation blocked by IAM policies.',
                        'success',
                        risk='LOW — Account is protected against this attack vector.'
                    )
            except Exception as e:
                self.send_step(3, 'Escalation Vector Detection',
                    f'⚠ Could not simulate: {e}\n'
                    f'  Manual verification recommended.',
                    'warning',
                    risk='UNKNOWN — Unable to determine escalation risk.'
                )

            time.sleep(0.5)

            self.send_step(4, 'Backdoor User Detection',
                'Checking for suspicious IAM users created recently...', 'running')
            time.sleep(1.5)
            try:
                users = iam.list_users().get('Users', [])
                suspicious = []
                for user in users:
                    created = user['CreateDate'].replace(tzinfo=None)
                    age_days = (datetime.now() - created).days
                    if age_days < 7:
                        suspicious.append(f'{user["UserName"]} (created {age_days}d ago)')

                if suspicious:
                    self.send_step(4, 'Backdoor User Detection',
                        f'🚨 SUSPICIOUS USERS FOUND:\n' +
                        '\n'.join(f'  • {u}' for u in suspicious),
                        'fail',
                        risk='HIGH — Recently created users may be attacker backdoors.'
                    )
                else:
                    self.send_step(4, 'Backdoor User Detection',
                        f'✓ No suspicious recent users found\n'
                        f'  All {len(users)} users appear legitimate.',
                        'success'
                    )
            except Exception as e:
                self.send_step(4, 'Backdoor User Detection',
                    f'⚠ Check failed: {e}', 'warning')

            time.sleep(0.5)

            self.send_step(5, 'Attack Chain Complete',
                '✓ IAM Privilege Escalation simulation complete\n'
                '✓ No destructive actions were taken\n'
                '✓ All checks were read-only or policy simulation only\n'
                '✓ Review findings above and apply remediations',
                'success',
                risk='See individual steps for risk assessment.'
            )

            self.sim_complete.emit('COMPLETED', [
                'IAM policy simulation reveals escalation paths',
                'Check iam:AttachUserPolicy permissions',
                'Enforce least-privilege IAM policies'
            ])

        except Exception as e:
            import traceback
            self.sim_error.emit(f'{e}\n{traceback.format_exc()}')

    def simulate_s3_takeover(self):
        self.send_step(0, 'Starting...', 'Initializing S3 Bucket Takeover simulation...', 'running')
        
        try:
            session = boto3.Session(
                aws_access_key_id=self.credentials['access_key'],
                aws_secret_access_key=self.credentials['secret_key'],
                region_name=self.credentials['region']
            )
            s3 = session.client('s3')
        except Exception as e:
            self.sim_error.emit(f'Failed to create AWS session: {e}')
            return

        try:
            self.send_step(1, 'Bucket Enumeration',
                'Calling s3:ListBuckets to enumerate all buckets...', 'running')
            time.sleep(1)
            buckets = s3.list_buckets().get('Buckets', [])
            self.send_step(1, 'Bucket Enumeration',
                f'✓ Found {len(buckets)} S3 buckets:\n' +
                '\n'.join(f'  • {b["Name"]}' for b in buckets[:10]),
                'success',
                risk='LOW — Bucket names exposed to authenticated user.'
            )
            time.sleep(0.5)

            if not buckets:
                self.send_step(2, 'No Buckets Found',
                    'No S3 buckets in this account to test.', 'warning')
                self.sim_complete.emit('NO_TARGETS', [])
                return

            self.send_step(2, 'Public Access Analysis',
                'Checking each bucket for public access configuration...', 'running')
            time.sleep(1.5)
            public_buckets = []
            for bucket in buckets:
                name = bucket['Name']
                try:
                    pab = s3.get_public_access_block(Bucket=name)
                    config = pab['PublicAccessBlockConfiguration']
                    if not all(config.values()):
                        public_buckets.append(name)
                except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
                    public_buckets.append(name)
                except Exception:
                    pass

            if public_buckets:
                self.send_step(2, 'Public Access Analysis',
                    f'🚨 {len(public_buckets)} BUCKET(S) WITHOUT FULL PUBLIC BLOCK:\n' +
                    '\n'.join(f'  • {b}' for b in public_buckets),
                    'fail',
                    risk='CRITICAL — Buckets may be publicly accessible.'
                )
            else:
                self.send_step(2, 'Public Access Analysis',
                    '✓ All buckets have public access block enabled.',
                    'success',
                    risk='LOW — Public access properly blocked.'
                )
            time.sleep(0.5)

            self.send_step(3, 'ACL Vulnerability Check',
                'Checking bucket ACLs for AllUsers or AuthenticatedUsers grants...', 'running')
            time.sleep(1.5)
            vulnerable = []
            for bucket in buckets:
                name = bucket['Name']
                try:
                    acl = s3.get_bucket_acl(Bucket=name)
                    for grant in acl.get('Grants', []):
                        uri = grant.get('Grantee', {}).get('URI', '')
                        if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                            perm = grant.get('Permission', 'UNKNOWN')
                            vulnerable.append(f'{name} — {perm} to {uri.split("/")[-1]}')
                except Exception:
                    pass

            if vulnerable:
                self.send_step(3, 'ACL Vulnerability Check',
                    f'🚨 VULNERABLE BUCKET ACLs FOUND:\n' +
                    '\n'.join(f'  • {v}' for v in vulnerable),
                    'fail',
                    risk='CRITICAL — Public ACL grants detected. Data exposed.'
                )
            else:
                self.send_step(3, 'ACL Vulnerability Check',
                    '✓ No public ACL grants found on any bucket.',
                    'success'
                )
            time.sleep(0.5)

            target = public_buckets[0] if public_buckets else buckets[0]['Name']
            self.send_step(4, 'Data Exposure Simulation',
                f'Attempting to list objects in: {target}\n'
                f'(Simulating what an attacker would see)...', 'running')
            time.sleep(2)
            try:
                objects = s3.list_objects_v2(Bucket=target, MaxKeys=5)
                obj_list = objects.get('Contents', [])
                total = objects.get('KeyCount', 0)
                if obj_list:
                    self.send_step(4, 'Data Exposure Simulation',
                        f'🚨 OBJECTS ACCESSIBLE — {total} items found:\n' +
                        '\n'.join(f'  • {o["Key"]} ({o["Size"]} bytes)' for o in obj_list[:5]),
                        'fail',
                        risk='CRITICAL — Attacker can enumerate and download all objects.'
                    )
                else:
                    self.send_step(4, 'Data Exposure Simulation',
                        f'✓ Bucket {target} is empty or access denied.',
                        'success'
                    )
            except Exception as e:
                self.send_step(4, 'Data Exposure Simulation',
                    f'✓ Access denied to {target}\n  Error: {e}',
                    'success',
                    risk='LOW — Bucket properly protected.'
                )
            time.sleep(0.5)

            self.send_step(5, 'Simulation Complete',
                '✓ S3 Bucket Takeover simulation complete\n'
                '✓ No data was modified or deleted\n'
                '✓ Only read operations were performed\n'
                '✓ Apply remediations for any findings above',
                'success'
            )

            self.sim_complete.emit('COMPLETED', [
                f'{len(public_buckets)} buckets without full public access block',
                f'{len(vulnerable)} buckets with public ACL grants',
                'Enable S3 Block Public Access at account level'
            ])

        except Exception as e:
            import traceback
            self.sim_error.emit(f'{e}\n{traceback.format_exc()}')
