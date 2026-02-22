import multiprocessing
import boto3
import logging
from PyQt6.QtCore import QThread, pyqtSignal

# Windows multiprocessing fix
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

# This function runs in a SEPARATE PROCESS - completely isolated from Qt
def run_scan_process(credentials, result_queue, settings=None):
    try:
        if settings is None:
            from settings_manager import get_all_settings
            settings = get_all_settings()
        
        regions = settings.get('regions', [credentials['region']])
        scan_depth = settings.get('scan_depth', 'Standard (15 min)')
        
        if 'Quick' in scan_depth:
            checks_to_run = ['s3', 'iam_users', 'security_groups']
        elif 'Deep' in scan_depth:
            checks_to_run = ['s3', 'iam_users', 'iam_policies', 'security_groups', 'cloudtrail', 'root_account', 'rds', 'ec2_instances']
        else:
            checks_to_run = ['s3', 'iam_users', 'iam_policies', 'security_groups', 'cloudtrail', 'root_account']
        
        result_queue.put({'type': 'progress', 'pct': 5, 'msg': f'SCAN DEPTH: {scan_depth} | REGIONS: {", ".join(regions)}'})
        
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
                'fix': remediation
            }
            findings.append(finding)
            result_queue.put({'type': 'finding', 'data': finding})
        
        # Test credentials first
        try:
            test_session = boto3.Session(
                aws_access_key_id=credentials['access_key'],
                aws_secret_access_key=credentials['secret_key'],
                region_name=credentials['region']
            )
            sts = test_session.client('sts')
            sts.get_caller_identity()
        except Exception as e:
            error_str = str(e)
            if 'InvalidClientTokenId' in error_str or 'SignatureDoesNotMatch' in error_str or 'AuthFailure' in error_str:
                result_queue.put({'type': 'fatal', 'msg': f'❌ AUTHENTICATION FAILED\n\nInvalid AWS credentials. Please check:\n• Access Key ID\n• Secret Access Key\n• Region\n\nError: {error_str}'})
                return
            else:
                result_queue.put({'type': 'fatal', 'msg': f'❌ CONNECTION FAILED\n\n{error_str}'})
                return
        
        for region in regions:
            result_queue.put({'type': 'progress', 'pct': 10, 'msg': f'SCANNING REGION: {region}'})
        session = boto3.Session(
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'],
            region_name=region
        )
        
        # S3 CHECK
        if 's3' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 15, 'msg': 'S3 BUCKETS'})
            try:
                s3 = session.client('s3')
                buckets = s3.list_buckets().get('Buckets', [])
                for bucket in buckets:
                    name = bucket['Name']
                    try:
                        acl = s3.get_bucket_acl(Bucket=name)
                        for grant in acl.get('Grants', []):
                            if grant.get('Grantee', {}).get('URI', '').endswith('AllUsers'):
                                add_finding('CRITICAL', f'S3 Bucket Public: {name}', 'S3',
                                    region,
                                    f'Bucket {name} is publicly accessible.',
                                    f'aws s3api put-public-access-block --bucket {name} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true')
                    except: pass
                    
                    # Check for encryption
                    try:
                        s3.get_bucket_encryption(Bucket=name)
                    except: 
                        add_finding('HIGH', f'S3 Not Encrypted: {name}', 'S3',
                            region,
                            f'Bucket {name} has no server-side encryption enabled.',
                            f'aws s3api put-bucket-encryption --bucket {name} --server-side-encryption-configuration \'{{"Rules":[{{"ApplyServerSideEncryptionByDefault":{{"SSEAlgorithm":"AES256"}}}}]}}\'')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'S3 check failed: {e}'})

        # IAM USERS CHECK
        if 'iam_users' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 30, 'msg': 'IAM USERS'})
            try:
                iam = session.client('iam')
                users = iam.list_users().get('Users', [])
                for user in users:
                    username = user['UserName']
                    
                    # Check MFA
                    mfa = iam.list_mfa_devices(UserName=username).get('MFADevices', [])
                    if not mfa:
                        add_finding('HIGH', f'MFA Not Enabled: {username}', 'IAM', 'global',
                            f'User {username} has no MFA.',
                            f'aws iam enable-mfa-device --user-name {username} --serial-number <arn> --authentication-code1 <code1> --authentication-code2 <code2>')
                    
                    # Check access key age
                    keys = iam.list_access_keys(UserName=username).get('AccessKeyMetadata', [])
                    from datetime import datetime, timezone
                    for key in keys:
                        created = key['CreateDate'].replace(tzinfo=None)
                        age = (datetime.now() - created).days
                        if age > 90:
                            add_finding('MEDIUM', f'Old Access Key: {username} ({age}d)', 'IAM', 'global',
                                f'Key is {age} days old.',
                                f'aws iam delete-access-key --user-name {username} --access-key-id {key["AccessKeyId"]}')
                    
                    # Check for inactive users (90+ days no password use)
                    last_used = user.get('PasswordLastUsed')
                    if last_used:
                        last_used = last_used.replace(tzinfo=None)
                        days = (datetime.now() - last_used).days
                        if days > 90:
                            add_finding('MEDIUM', f'IAM User Inactive 90+ Days: {username}', 'IAM', 'global',
                                f'User {username} has not logged in for {days} days.',
                                f'aws iam delete-login-profile --user-name {username}')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'IAM check failed: {e}'})

        # IAM POLICIES CHECK
        if 'iam_policies' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 45, 'msg': 'IAM POLICIES'})
            try:
                iam = session.client('iam')
                policies = iam.list_policies(Scope='Local').get('Policies', [])
                for policy in policies:
                    try:
                        ver = iam.get_policy_version(
                            PolicyArn=policy['Arn'],
                            VersionId=policy['DefaultVersionId']
                        )
                        for stmt in ver['PolicyVersion']['Document'].get('Statement', []):
                            if stmt.get('Effect') == 'Allow' and stmt.get('Action') == '*':
                                add_finding('CRITICAL', f'Wildcard Policy: {policy["PolicyName"]}', 'IAM', 'global',
                                    'Policy grants full admin access.',
                                    f'aws iam delete-policy --policy-arn {policy["Arn"]}')
                    except: pass
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'Policy check failed: {e}'})

        # SECURITY GROUPS CHECK
        if 'security_groups' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 60, 'msg': 'SECURITY GROUPS'})
            try:
                ec2 = session.client('ec2')
                sgs = ec2.describe_security_groups().get('SecurityGroups', [])
                for sg in sgs:
                    for rule in sg.get('IpPermissions', []):
                        for ip in rule.get('IpRanges', []):
                            if ip.get('CidrIp') == '0.0.0.0/0':
                                port = rule.get('FromPort', 'ALL')
                                sev = 'CRITICAL' if port in [22, 3389] else 'HIGH'
                                add_finding(sev, f'Open Port {port}: {sg["GroupName"]}', 'EC2',
                                    region,
                                    f'Port {port} open to internet.',
                                    f'aws ec2 revoke-security-group-ingress --group-id {sg["GroupId"]} --protocol tcp --port {port} --cidr 0.0.0.0/0')
                
                # Check for EC2 instances with public IPs
                reservations = ec2.describe_instances().get('Reservations', [])
                for r in reservations:
                    for instance in r.get('Instances', []):
                        if instance.get('PublicIpAddress'):
                            instance_id = instance.get('InstanceId')
                            az = instance.get('Placement', {}).get('AvailabilityZone', region)
                            instance_region = az[:-1] if az else region
                            add_finding('MEDIUM', f'EC2 Instance Has Public IP: {instance_id}', 'EC2',
                                instance_region,
                                f'EC2 instance {instance_id} directly exposed to internet via public IP.',
                                f'aws ec2 modify-instance-attribute --instance-id {instance_id} --no-source-dest-check')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'SG check failed: {e}'})

        # CLOUDTRAIL CHECK
        if 'cloudtrail' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 75, 'msg': 'CLOUDTRAIL'})
            try:
                ct = session.client('cloudtrail')
                trails = ct.describe_trails().get('trailList', [])
                if not trails:
                    add_finding('HIGH', 'CloudTrail Not Enabled', 'CloudTrail',
                        region,
                        'No audit trail exists.',
                        'aws cloudtrail create-trail --name audit-trail --s3-bucket-name <bucket>')
                else:
                    for trail in trails:
                        status = ct.get_trail_status(Name=trail['TrailARN'])
                        if not status.get('IsLogging'):
                            add_finding('HIGH', f'CloudTrail Disabled: {trail["Name"]}', 'CloudTrail',
                                region,
                                'Trail exists but logging off.',
                                f'aws cloudtrail start-logging --name {trail["Name"]}')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'CloudTrail check failed: {e}'})

        # ROOT MFA CHECK
        if 'root_account' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 85, 'msg': 'ROOT ACCOUNT'})
            try:
                iam = session.client('iam')
                summary = iam.get_account_summary().get('SummaryMap', {})
                
                # Check root MFA
                if summary.get('AccountMFAEnabled', 0) == 0:
                    add_finding('CRITICAL', 'Root Account MFA Disabled', 'Root Account', 'global',
                        'Root account has no MFA — highest risk finding.',
                        'Enable MFA via AWS Console > Security Credentials')
                
                # Check for root access keys
                if summary.get('AccountAccessKeysPresent', 0) > 0:
                    add_finding('CRITICAL', 'Root Account Has Active Access Keys', 'Root Account', 'global',
                        'Root account access keys should never exist. Immediate security risk.',
                        'Delete root access keys immediately from AWS Console → My Security Credentials')
                
                # Check for password policy
                try:
                    iam.get_account_password_policy()
                except:
                    add_finding('HIGH', 'No IAM Password Policy Configured', 'IAM', 'global',
                        'Account has no password policy — weak passwords allowed.',
                        'aws iam update-account-password-policy --minimum-password-length 14 --require-symbols --require-numbers --require-uppercase-characters --require-lowercase-characters')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'Root check failed: {e}'})

        # RDS CHECK
        if 'rds' in checks_to_run:
            result_queue.put({'type': 'progress', 'pct': 95, 'msg': 'RDS INSTANCES'})
            try:
                rds = session.client('rds')
                instances = rds.describe_db_instances().get('DBInstances', [])
                for db in instances:
                    if db.get('PubliclyAccessible'):
                        add_finding('HIGH', f'RDS Public: {db["DBInstanceIdentifier"]}', 'RDS',
                            region,
                            'Database accessible from internet.',
                            f'aws rds modify-db-instance --db-instance-identifier {db["DBInstanceIdentifier"]} --no-publicly-accessible')
                    if not db.get('StorageEncrypted'):
                        add_finding('MEDIUM', f'RDS Unencrypted: {db["DBInstanceIdentifier"]}', 'RDS',
                            region,
                            'Database storage not encrypted.',
                            'Create encrypted snapshot and restore.')
            except Exception as e:
                result_queue.put({'type': 'error_check', 'msg': f'RDS check failed: {e}'})

        # DONE
        result_queue.put({'type': 'progress', 'pct': 100, 'msg': 'COMPLETE'})
        result_queue.put({'type': 'complete', 'data': findings})

    except Exception as e:
        import traceback
        result_queue.put({'type': 'fatal', 'msg': f'{e}\n{traceback.format_exc()}'})


class AWSScanner(QThread):
    finding_found  = pyqtSignal(dict)
    scan_progress  = pyqtSignal(int, str)
    scan_complete  = pyqtSignal(list)
    scan_error     = pyqtSignal(str)

    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials

    def run(self):
        from settings_manager import get_all_settings
        settings = get_all_settings()
        
        ctx = multiprocessing.get_context('spawn')
        result_queue = ctx.Queue()
        
        process = ctx.Process(
            target=run_scan_process,
            args=(self.credentials, result_queue, settings),
            daemon=True
        )
        process.start()

        while True:
            try:
                msg = result_queue.get(timeout=60)
                
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
                    
                elif msg['type'] == 'error_check':
                    logging.warning(msg['msg'])
                    
            except Exception as e:
                self.scan_error.emit(f'Queue timeout or error: {e}')
                break

        process.join(timeout=5)
        if process.is_alive():
            process.terminate()


# REQUIRED for Windows multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
