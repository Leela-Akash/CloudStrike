import multiprocessing
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

# Windows multiprocessing fix
try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass  # Already set

def run_azure_scan_process(credentials, result_queue):
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.resource import ResourceManagementClient
        from azure.mgmt.storage import StorageManagementClient
        from azure.mgmt.compute import ComputeManagementClient
        from azure.mgmt.network import NetworkManagementClient

        # Test credentials first
        try:
            credential = ClientSecretCredential(
                tenant_id=credentials['tenant_id'],
                client_id=credentials['client_id'],
                client_secret=credentials['client_secret']
            )
            subscription_id = credentials['subscription_id']
            # Test with a simple API call
            test_client = ResourceManagementClient(credential, subscription_id)
            list(test_client.resource_groups.list())
        except Exception as e:
            error_str = str(e)
            if 'AADSTS' in error_str or 'authentication' in error_str.lower() or 'unauthorized' in error_str.lower():
                result_queue.put({'type': 'fatal', 'msg': f'❌ AZURE AUTHENTICATION FAILED\n\nInvalid Azure credentials. Please check:\n• Client ID\n• Client Secret\n• Tenant ID\n• Subscription ID\n\nError: {error_str}'})
                return
            else:
                result_queue.put({'type': 'fatal', 'msg': f'❌ AZURE CONNECTION FAILED\n\n{error_str}'})
                return
        
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
                'timestamp': datetime.now().isoformat(),
                'cloud': 'Azure'
            }
            findings.append(finding)
            result_queue.put({'type': 'finding', 'data': finding})

        # STORAGE ACCOUNT CHECKS
        result_queue.put({'type': 'progress', 'pct': 10, 'msg': 'AZURE STORAGE ACCOUNTS'})
        try:
            storage_client = StorageManagementClient(credential, subscription_id)
            for account in storage_client.storage_accounts.list():
                if account.allow_blob_public_access:
                    add_finding(
                        'CRITICAL',
                        f'Storage Account Public: {account.name}',
                        'Azure Storage',
                        account.location,
                        f'Storage account {account.name} allows public blob access.',
                        f'az storage account update --name {account.name} --allow-blob-public-access false'
                    )
                if not account.enable_https_traffic_only:
                    add_finding(
                        'HIGH',
                        f'HTTP Allowed: {account.name}',
                        'Azure Storage',
                        account.location,
                        f'Storage account {account.name} allows HTTP traffic.',
                        f'az storage account update --name {account.name} --https-only true'
                    )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'Storage check failed: {e}'})

        # VIRTUAL MACHINE CHECKS
        result_queue.put({'type': 'progress', 'pct': 35, 'msg': 'AZURE VIRTUAL MACHINES'})
        try:
            compute_client = ComputeManagementClient(credential, subscription_id)
            for vm in compute_client.virtual_machines.list_all():
                for disk in (vm.storage_profile.data_disks or []):
                    if not disk.managed_disk:
                        add_finding(
                            'HIGH',
                            f'Unencrypted Disk: {vm.name}',
                            'Azure VM',
                            vm.location,
                            f'VM {vm.name} has unmanaged/unencrypted disk.',
                            f'az vm encryption enable --resource-group <rg> --name {vm.name} --disk-encryption-keyvault <keyvault>'
                        )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'VM check failed: {e}'})

        # NETWORK SECURITY GROUP CHECKS
        result_queue.put({'type': 'progress', 'pct': 60, 'msg': 'AZURE NETWORK SECURITY GROUPS'})
        try:
            network_client = NetworkManagementClient(credential, subscription_id)
            for nsg in network_client.network_security_groups.list_all():
                for rule in (nsg.security_rules or []):
                    if (rule.access == 'Allow' and
                        rule.direction == 'Inbound' and
                        rule.source_address_prefix in ['*','0.0.0.0/0','Internet']):
                        port = rule.destination_port_range
                        
                        # Specific checks for SSH and RDP
                        if port == '22':
                            add_finding(
                                'CRITICAL',
                                f'NSG Allows SSH from Internet: {nsg.name}',
                                'Azure NSG',
                                nsg.location,
                                f'Network Security Group {nsg.name} allows SSH port 22 from any source.',
                                f'az network nsg rule delete --resource-group <rg> --nsg-name {nsg.name} --name {rule.name}'
                            )
                        elif port == '3389':
                            add_finding(
                                'CRITICAL',
                                f'NSG Allows RDP from Internet: {nsg.name}',
                                'Azure NSG',
                                nsg.location,
                                f'Network Security Group {nsg.name} allows RDP port 3389 from any source.',
                                f'az network nsg rule delete --resource-group <rg> --nsg-name {nsg.name} --name {rule.name}'
                            )
                        else:
                            sev = 'CRITICAL' if port == '*' else 'HIGH'
                            add_finding(
                                sev,
                                f'Open NSG Rule: {nsg.name} port {port}',
                                'Azure NSG',
                                nsg.location,
                                f'NSG {nsg.name} allows inbound from Internet on port {port}.',
                                f'az network nsg rule delete --resource-group <rg> --nsg-name {nsg.name} --name {rule.name}'
                            )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'NSG check failed: {e}'})

        # RESOURCE GROUP CHECKS
        result_queue.put({'type': 'progress', 'pct': 85, 'msg': 'AZURE RESOURCE GROUPS'})
        try:
            resource_client = ResourceManagementClient(credential, subscription_id)
            for rg in resource_client.resource_groups.list():
                if not rg.tags or 'Owner' not in rg.tags:
                    add_finding(
                        'LOW',
                        f'Untagged Resource Group: {rg.name}',
                        'Azure Resources',
                        rg.location,
                        f'Resource group {rg.name} has no Owner tag.',
                        f'az group update --name {rg.name} --tags Owner=<owner>'
                    )
        except Exception as e:
            result_queue.put({'type': 'error_check', 'msg': f'Resource check failed: {e}'})

        result_queue.put({'type': 'progress', 'pct': 100, 'msg': 'AZURE SCAN COMPLETE'})
        result_queue.put({'type': 'complete', 'data': findings})

    except Exception as e:
        import traceback
        result_queue.put({'type': 'fatal', 'msg': f'Azure scan failed: {e}\n{traceback.format_exc()}'})


class AzureScanner(QThread):
    finding_found  = pyqtSignal(dict)
    scan_progress  = pyqtSignal(int, str)
    scan_complete  = pyqtSignal(list)
    scan_error     = pyqtSignal(str)

    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials

    def run(self):
        ctx = multiprocessing.get_context('spawn')
        result_queue = ctx.Queue()

        process = ctx.Process(
            target=run_azure_scan_process,
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
            except Exception as e:
                self.scan_error.emit(f'Azure scan timeout: {e}')
                break

        process.join(timeout=5)
        if process.is_alive():
            process.terminate()


if __name__ == '__main__':
    multiprocessing.freeze_support()
