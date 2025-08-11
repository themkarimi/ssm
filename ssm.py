#!/usr/bin/env python3
"""
Simple SealedSecret Manager - A streamlined CLI tool for Kubernetes SealedSecrets
Requirements:
- kubectl CLI tool
- kubeseal CLI tool  
- Python 3.7+
- PyYAML library
Usage:
    ssm create <name> [--namespace=default]     # Create new SealedSecret
    ssm update <file>                           # Update existing SealedSecret
    ssm list [--namespace=<namespace>]          # List all SealedSecrets (local and cluster)
    ssm decrypt <file|name>                     # Decrypt and view SealedSecret
    ssm apply <file>                            # Apply SealedSecret to cluster
    ssm convert <name> [--namespace=default]    # Convert existing Kubernetes secret to SealedSecret
"""
import argparse
import base64
import getpass
import os
import subprocess
import sys
import tempfile
from pathlib import Path
try:
    import yaml
except ImportError:
    print("❌ PyYAML library not found! Install with: pip3 install PyYAML")
    sys.exit(1)

class SealedSecretManager:
    """Simple SealedSecret manager"""
    def __init__(self, directory: str = None, controller_namespace: str = "sealed-secrets"):
        self.directory = Path(directory or os.getcwd())
        self.controller_namespace = controller_namespace

    def check_tools(self) -> bool:
        """Check if required tools are available"""
        for tool, cmd in [('kubectl', ['kubectl', 'version', '--client']), 
                         ('kubeseal', ['kubeseal', '--version'])]:
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                print(f"✅ {tool} found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"❌ {tool} not found")
                return False
        return True

    def get_secret_data(self) -> dict:
        """Collect secret key-value pairs from user"""
        print("\n📝 Enter secret data (empty key to finish):")
        data = {}
        while True:
            key = input("Key: ").strip()
            if not key:
                break
            # Hide sensitive values
            if any(word in key.lower() for word in ['password', 'token', 'key', 'secret']):
                value = getpass.getpass(f"Value for '{key}' (hidden): ")
            else:
                value = input(f"Value for '{key}': ")
            data[key] = value
        return data

    def create_secret(self, name: str, namespace: str = "default") -> bool:
        """Create a new SealedSecret"""
        print(f"🔐 Creating SealedSecret '{name}' in namespace '{namespace}'")
        # Get secret data
        data = self.get_secret_data()
        if not data:
            print("❌ No data provided")
            return False

        # Create secret YAML
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {'name': name, 'namespace': namespace},
            'type': 'Opaque',
            'stringData': data
        }

        # Write to temp file and seal it
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(secret, f)
            temp_file = f.name

        try:
            # Seal the secret using input redirection
            result = subprocess.run(
                f'kubeseal --controller-namespace={self.controller_namespace} -o yaml < {temp_file}',
                shell=True, capture_output=True, text=True, check=True
            )
            # Save sealed secret
            output_file = self.directory / f"{name}.yaml"
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            print(f"✅ SealedSecret created: {output_file}")
            # Ask to apply
            if input("Apply to cluster? [y/N]: ").lower().startswith('y'):
                return self.apply(str(output_file))
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to seal secret:")
            print(f"   Error: {e.stderr}")
            print(f"   Command: {' '.join(e.cmd) if e.cmd else 'Unknown'}")
            print(f"   Return code: {e.returncode}")
            return False
        finally:
            os.unlink(temp_file)

    def update_secret(self, file_path: str) -> bool:
        """Update an existing SealedSecret"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        # Read existing sealed secret
        with open(file_path, 'r') as f:
            sealed = yaml.safe_load(f)

        if sealed.get('kind') != 'SealedSecret':
            print(f"❌ Not a SealedSecret: {file_path}")
            return False

        name = sealed['metadata']['name']
        namespace = sealed['metadata']['namespace']
        print(f"🔄 Updating SealedSecret '{name}' in '{namespace}'")

        # Show existing keys
        existing_keys = list(sealed.get('spec', {}).get('encryptedData', {}).keys())
        if existing_keys:
            print(f"Existing keys: {', '.join(existing_keys)}")

        # Get current secret from cluster to preserve existing values
        existing_data = {}
        try:
            result = subprocess.run([
                'kubectl', 'get', 'secret', name, '-n', namespace, '-o', 'yaml'
            ], capture_output=True, text=True, check=True)
            current_secret = yaml.safe_load(result.stdout)
            if 'data' in current_secret:
                for key, value in current_secret['data'].items():
                    try:
                        existing_data[key] = base64.b64decode(value).decode('utf-8')
                    except Exception:
                        pass
        except subprocess.CalledProcessError:
            print("⚠️  Could not retrieve existing secret from cluster")

        # Get new data
        print("\nChoose action:")
        print("1. Add new keys")
        print("2. Update existing keys")
        choice = input("Choice [1-2]: ").strip()

        if choice == "1":
            # Add new keys
            print("Enter new keys:")
            new_data = self.get_secret_data()
            all_data = {**existing_data, **new_data}
        elif choice == "2":
            # Update existing keys with selection mode
            print("\nSelect keys to update:")
            for i, key in enumerate(existing_keys, 1):
                print(f"  {i}. {key}")
            print("\nEnter selection (e.g., '1,3' or '1-3' or 'all'):")
            selection = input("Selection: ").strip()
            # Parse selection
            selected_indices = []
            if selection.lower() == 'all':
                selected_indices = list(range(len(existing_keys)))
            else:
                try:
                    for part in selection.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            selected_indices.extend(range(start-1, end))
                        else:
                            selected_indices.append(int(part) - 1)
                except ValueError:
                    print("❌ Invalid selection format")
                    return False
            # Filter valid indices
            selected_indices = [i for i in selected_indices if 0 <= i < len(existing_keys)]
            if not selected_indices:
                print("❌ No valid keys selected")
                return False

            # Get new values for selected keys
            updated_data = existing_data.copy()
            print(f"\nEnter new values for {len(selected_indices)} selected key(s):")
            for i in selected_indices:
                key = existing_keys[i]
                # Hide sensitive values
                if any(word in key.lower() for word in ['password', 'token', 'key', 'secret']):
                    value = getpass.getpass(f"New value for '{key}' (hidden): ")
                else:
                    value = input(f"New value for '{key}': ")
                updated_data[key] = value
            all_data = updated_data
        else:
            print("❌ Invalid choice")
            return False

        if not all_data:
            print("❌ No data to update")
            return False

        # Create new secret and seal it
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {'name': name, 'namespace': namespace},
            'type': 'Opaque',
            'stringData': all_data
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(secret, f)
            temp_file = f.name

        try:
            # Seal the secret using input redirection
            result = subprocess.run(
                f'kubeseal --controller-namespace={self.controller_namespace} -o yaml < {temp_file}',
                shell=True, capture_output=True, text=True, check=True
            )
            # Backup and save
            backup_file = f"{file_path}.backup"
            if os.path.exists(backup_file):
                counter = 1
                while os.path.exists(f"{backup_file}.{counter}"):
                    counter += 1
                backup_file = f"{backup_file}.{counter}"
            os.rename(file_path, backup_file)
            print(f"📁 Backup: {backup_file}")
            with open(file_path, 'w') as f:
                f.write(result.stdout)
            print(f"✅ Updated: {file_path}")
            # Ask to apply
            if input("Apply to cluster? [y/N]: ").lower().startswith('y'):
                return self.apply(file_path)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to seal secret:")
            print(f"   Error: {e.stderr}")
            print(f"   Command: {' '.join(e.cmd) if e.cmd else 'Unknown'}")
            print(f"   Return code: {e.returncode}")
            return False
        finally:
            os.unlink(temp_file)

    def list_secrets(self, namespace: str = None):
        """List SealedSecrets"""
        print("📁 Local files:")
        yaml_files = list(self.directory.glob("*.yaml")) + list(self.directory.glob("*.yml"))
        sealed_files = []
        for file in yaml_files:
            try:
                with open(file, 'r') as f:
                    content = yaml.safe_load(f)
                    # Optionally filter by namespace in local files
                    if content.get('kind') == 'SealedSecret':
                        if namespace is None or content.get('metadata', {}).get('namespace') == namespace:
                             sealed_files.append(file.name)
            except Exception:
                continue
        if sealed_files:
            for i, file in enumerate(sealed_files, 1):
                print(f"  {i}. {file}")
        else:
            print("  No matching SealedSecret files found locally")

        print(f"\n🔍 Cluster SealedSecrets:")
        try:
            # Prepare kubectl command
            kubectl_cmd = ['kubectl', 'get', 'sealedsecrets']
            if namespace:
                kubectl_cmd.extend(['-n', namespace])
            else:
                 kubectl_cmd.append('--all-namespaces')

            result = subprocess.run(
                kubectl_cmd,
                capture_output=True, text=True, check=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr}")

    def apply(self, file_path: str) -> bool:
        """Apply SealedSecret to cluster"""
        try:
            result = subprocess.run([
                'kubectl', 'apply', '-f', file_path
            ], capture_output=True, text=True, check=True)
            print(f"✅ Applied: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Apply failed: {e.stderr}")
            return False

    def decrypt(self, target: str, namespace: str = "default") -> bool:
        """Decrypt a SealedSecret (from file or cluster)"""
        name = None
        # Check if target is a file
        if os.path.exists(target):
            # Decrypt from file
            print(f"🔓 Decrypting from file: {target}")
            with open(target, 'r') as f:
                sealed = yaml.safe_load(f)
            if sealed.get('kind') != 'SealedSecret':
                print(f"❌ Not a SealedSecret: {target}")
                return False
            name = sealed['metadata']['name']
            namespace = sealed['metadata']['namespace']
            # Apply first to ensure secret exists in cluster
            self.apply(target)
        else:
            # Decrypt from cluster by name
            name = target
            print(f"🔓 Decrypting from cluster: {name} in {namespace}")

        # Get the decrypted secret
        try:
            result = subprocess.run([
                'kubectl', 'get', 'secret', name, '-n', namespace, '-o', 'yaml'
            ], capture_output=True, text=True, check=True)
            secret = yaml.safe_load(result.stdout)
            if 'data' in secret:
                print(f"\n🔑 Secret data for '{name}':")
                print("=" * 40)
                for key, value in secret['data'].items():
                    try:
                        decoded = base64.b64decode(value).decode('utf-8')
                        # Mask sensitive values
                        if any(word in key.lower() for word in ['password', 'token', 'key', 'secret']):
                            display = "***hidden***"
                        else:
                            display = decoded
                        print(f"  {key}: {display}")
                    except Exception:
                        print(f"  {key}: <decode error>")
                print("=" * 40)
                # Option to show full values
                if input("\nShow full values? [y/N]: ").lower().startswith('y'):
                    print(f"\n🚨 Full values for '{name}':")
                    print("=" * 40)
                    for key, value in secret['data'].items():
                        try:
                            decoded = base64.b64decode(value).decode('utf-8')
                            print(f"  {key}: {decoded}")
                        except Exception:
                            print(f"  {key}: <decode error>")
                    print("=" * 40)
            else:
                print("❌ No data found")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Decrypt failed: {e.stderr}")
            return False

    def convert_secret(self, name: str, namespace: str = "default", output_file: str = None) -> bool:
        """Convert an existing Kubernetes secret to a SealedSecret"""
        print(f"🔄 Converting Kubernetes secret '{name}' from namespace '{namespace}' to SealedSecret")
        
        # Set default output file if not provided
        if not output_file:
            output_file = str(self.directory / f"{name}.yaml")
        
        try:
            # Get the existing secret from the cluster
            result = subprocess.run([
                'kubectl', 'get', 'secret', name, '-n', namespace, '-o', 'yaml'
            ], capture_output=True, text=True, check=True)
            
            # Parse the secret
            secret = yaml.safe_load(result.stdout)
            
            if not secret or secret.get('kind') != 'Secret':
                print(f"❌ '{name}' is not a valid Kubernetes Secret")
                return False
            
            # Extract the secret data
            secret_data = {}
            if 'data' in secret:
                print(f"📋 Found {len(secret['data'])} data fields in secret")
                for key, value in secret['data'].items():
                    try:
                        # Decode base64 data back to string
                        decoded_value = base64.b64decode(value).decode('utf-8')
                        secret_data[key] = decoded_value
                    except Exception as e:
                        print(f"⚠️  Could not decode key '{key}': {e}")
                        continue
            
            if not secret_data:
                print(f"❌ No decodable data found in secret '{name}'")
                return False
            
            # Create a new secret structure for sealing
            new_secret = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'metadata': {
                    'name': name,
                    'namespace': namespace
                },
                'type': secret.get('type', 'Opaque'),
                'stringData': secret_data
            }
            
            # Write to temp file for kubeseal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(new_secret, f)
                temp_file = f.name
            
            try:
                # Seal the secret using kubeseal
                result = subprocess.run(
                    f'kubeseal --controller-namespace={self.controller_namespace} -o yaml < {temp_file}',
                    shell=True, capture_output=True, text=True, check=True
                )
                
                # Save the sealed secret to output file
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                print(f"✅ SealedSecret created successfully: {output_file}")
                
                # Show the YAML output
                print(f"\n📄 Generated SealedSecret YAML:")
                print("=" * 50)
                print(result.stdout)
                print("=" * 50)
                
                # Ask if user wants to apply it
                if input("\nApply SealedSecret to cluster? [y/N]: ").lower().startswith('y'):
                    return self.apply(output_file)
                
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to seal secret:")
                print(f"   Error: {e.stderr}")
                print(f"   Return code: {e.returncode}")
                return False
            finally:
                os.unlink(temp_file)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to retrieve secret '{name}' from namespace '{namespace}':")
            print(f"   Error: {e.stderr}")
            print("   Make sure the secret exists and you have proper permissions")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Simple SealedSecret Manager')
    parser.add_argument('--dir', help='Directory for secrets', default=os.getcwd())
    parser.add_argument('--skip-check', action='store_true', help='Skip tool checks')
    parser.add_argument('--controller-namespace', default='sealed-secrets', 
                       help='Sealed secrets controller namespace')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create
    create_parser = subparsers.add_parser('create', help='Create SealedSecret')
    create_parser.add_argument('name', help='Secret name')
    create_parser.add_argument('--namespace', default='default', help='Namespace')

    # Update
    update_parser = subparsers.add_parser('update', help='Update SealedSecret')
    update_parser.add_argument('file', help='SealedSecret file')

    # List
    list_parser = subparsers.add_parser('list', help='List SealedSecrets')
    list_parser.add_argument('--namespace', default=None, help='Filter by namespace') # Added namespace option

    # Apply
    apply_parser = subparsers.add_parser('apply', help='Apply SealedSecret')
    apply_parser.add_argument('file', help='SealedSecret file')

    # Decrypt
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt SealedSecret')
    decrypt_parser.add_argument('target', help='File path or secret name')
    decrypt_parser.add_argument('--namespace', default='default', help='Namespace (for name)')

    # Convert
    convert_parser = subparsers.add_parser('convert', help='Convert existing Kubernetes secret to SealedSecret')
    convert_parser.add_argument('name', help='Secret name')
    convert_parser.add_argument('--namespace', default='default', help='Namespace')
    convert_parser.add_argument('--output', '-o', help='Output file path (default: <name>.yaml)')

    args = parser.parse_args()

    # Create manager
    manager = SealedSecretManager(args.dir, args.controller_namespace)

    # Check tools unless skipped
    if not args.skip_check and not manager.check_tools():
        print("❌ Required tools missing")
        sys.exit(1)

    # Execute command
    if args.command == 'create':
        success = manager.create_secret(args.name, args.namespace)
    elif args.command == 'update':
        success = manager.update_secret(args.file)
    elif args.command == 'list':
        # Pass the namespace argument to the list_secrets method
        manager.list_secrets(namespace=args.namespace) 
        success = True
    elif args.command == 'apply':
        success = manager.apply(args.file)
    elif args.command == 'decrypt':
        success = manager.decrypt(args.target, args.namespace)
    elif args.command == 'convert':
        success = manager.convert_secret(args.name, args.namespace, args.output)
    else:
        # Interactive mode
        print("🔐 SealedSecret Manager")
        print("Available commands: create, update, list, apply, decrypt, convert")
        parser.print_help()
        success = True

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()