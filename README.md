# Sealed Secret Manager (SSM)

A streamlined CLI tool for managing Kubernetes SealedSecrets with an intuitive interface and secure secret handling.

## 🚀 Features

- **Interactive Secret Creation**: Easily create new SealedSecrets with automatic sensitive value masking
- **Smart Updates**: Update existing secrets with selective key modification and automatic backups
- **Secret Conversion**: Convert existing Kubernetes secrets to SealedSecrets with YAML output
- **Unified Listing**: View both local SealedSecret files and cluster-deployed secrets
- **Secure Decryption**: Decrypt and view secret contents with optional value masking for security
- **One-Step Deployment**: Apply SealedSecrets to your Kubernetes cluster seamlessly
- **Shell Completion**: zsh tab completion support for enhanced productivity

## 📋 Prerequisites

Before using SSM, ensure you have the following tools installed:

- **kubectl**: Kubernetes command-line tool
- **kubeseal**: Sealed Secrets CLI tool
- **Python 3.7+**: With PyYAML library

### Installing Prerequisites

```bash
# Install kubectl (macOS with Homebrew)
brew install kubectl

# Install kubeseal
brew install kubeseal

# Install Python dependencies
pip3 install PyYAML
```

## 🛠️ Installation

### Option 1: Direct Installation with pip

```bash
pip3 install -e .
```

### Option 2: Manual Setup

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x ssm.py
   ```
3. Add to your PATH or create a symlink:
   ```bash
   ln -s $(pwd)/ssm.py /usr/local/bin/ssm
   ```

### Shell Completion (Optional)

SSM supports shell completion for enhanced productivity. Follow the instructions for your shell:

**For zsh:**
```bash
# Generate and install completion script
mkdir -p ~/.zsh/completions
cp _ssm_completion.zsh ~/.zsh/completions/_ssm

# Add to your ~/.zshrc (if not already present)
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc

# Reload your shell
exec zsh
```

**Alternative: System-wide installation (requires sudo)**
```bash
# Install to system completion directory
sudo cp _ssm_completion.zsh /usr/local/share/zsh/site-functions/_ssm

# Reload completions
compinit
```

**For bash:**
```bash
# Method 1: User-specific installation
mkdir -p ~/.bash_completion.d
cp _ssm_completion.bash ~/.bash_completion.d/_ssm

# Add to your ~/.bashrc (if not already present)
echo 'for f in ~/.bash_completion.d/*; do [ -f "$f" ] && source "$f"; done' >> ~/.bashrc

# Reload your shell
exec bash
```

**Alternative bash methods:**
```bash
# Method 2: Direct sourcing in ~/.bashrc
echo 'source /path/to/sealed-secret-manager/_ssm_completion.bash' >> ~/.bashrc
exec bash

# Method 3: System-wide installation (requires sudo)
sudo cp _ssm_completion.bash /etc/bash_completion.d/ssm
# Then reload: exec bash
```

**Verify completion is working:**

**For zsh:**
```bash
# Test tab completion
ssm <TAB>        # Should show: create, update, list, apply, decrypt
ssm create <TAB> # Should show available options

# If using Oh My Zsh and completion doesn't work:
omz reload       # Reload Oh My Zsh
compinit         # Reload completions manually
```

**For bash:**
```bash
# Test tab completion (press TAB twice if single TAB doesn't work)
ssm <TAB><TAB>        # Should show: create, update, list, apply, decrypt
ssm create <TAB><TAB> # Should show available options

# If completion doesn't work:
source ~/.bashrc      # Reload bash configuration
```

## 📖 Usage

### Basic Commands

```bash
# Create a new SealedSecret
ssm create my-secret --namespace production

# Update an existing SealedSecret file
ssm update my-secret.yaml

# List all SealedSecrets (local files and cluster)
ssm list

# List SealedSecrets in a specific namespace
ssm list --namespace production

# Apply a SealedSecret to the cluster
ssm apply my-secret.yaml

# Decrypt and view a SealedSecret
ssm decrypt my-secret.yaml
ssm decrypt my-secret --namespace production

# Convert an existing Kubernetes secret to a SealedSecret
ssm convert existing-secret --namespace production
ssm convert existing-secret --namespace production --output my-sealed-secret.yaml
```

### Advanced Options

```bash
# Use a specific directory for secret files
ssm --dir /path/to/secrets list

# Skip tool availability checks
ssm --skip-check create my-secret

# Use a custom sealed-secrets controller namespace
ssm --controller-namespace kube-system create my-secret
```

## 🔄 Workflow Examples

### Creating a New Secret

```bash
$ ssm create database-credentials --namespace production
🔐 Creating SealedSecret 'database-credentials' in namespace 'production'

📝 Enter secret data (empty key to finish):
Key: username
Value for 'username': admin
Key: password
New value for 'password' (hidden): ********
Key: 

✅ SealedSecret created: database-credentials.yaml
Apply to cluster? [y/N]: y
✅ Applied: sealedsecret.bitnami.com/database-credentials created
```

### Updating an Existing Secret

```bash
$ ssm update database-credentials.yaml
🔄 Updating SealedSecret 'database-credentials' in 'production'
Existing keys: username, password

Choose action:
1. Add new keys
2. Update existing keys
Choice [1-2]: 2

Select keys to update:
  1. username
  2. password

Enter selection (e.g., '1,3' or '1-3' or 'all'):
Selection: 2

Enter new values for 1 selected key(s):
New value for 'password' (hidden): ********

📁 Backup: database-credentials.yaml.backup
✅ Updated: database-credentials.yaml
Apply to cluster? [y/N]: y
```

### Listing Secrets

```bash
$ ssm list --namespace production
📁 Local files:
  1. database-credentials.yaml
  2. api-keys.yaml

🔍 Cluster SealedSecrets:
NAMESPACE    NAME                   AGE
production   database-credentials   5m
production   api-keys              2d
```

### Decrypting Secrets

```bash
$ ssm decrypt database-credentials.yaml
🔓 Decrypting from file: database-credentials.yaml

🔑 Secret data for 'database-credentials':
========================================
  username: admin
  password: ***hidden***
========================================

Show full values? [y/N]: y

🚨 Full values for 'database-credentials':
========================================
  username: admin
  password: super-secret-password
========================================
```

### Converting Existing Kubernetes Secrets

```bash
$ ssm convert database-credentials --namespace production
🔄 Converting Kubernetes secret 'database-credentials' from namespace 'production' to SealedSecret
📋 Found 2 data fields in secret
✅ SealedSecret created successfully: database-credentials.yaml

📄 Generated SealedSecret YAML:
==================================================
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  creationTimestamp: null
  name: database-credentials
  namespace: production
spec:
  encryptedData:
    password: AgBy3i4OJSWK+PiTySYZZA9rO21HcMiSsxXR4gY...
    username: AgBjbvvhh0jOMJi4LlbSEr27YO7Y8vGMwVGmDY...
  template:
    metadata:
      creationTimestamp: null
      name: database-credentials
      namespace: production
    type: Opaque
==================================================

Apply SealedSecret to cluster? [y/N]: y
✅ Applied: sealedsecret.bitnami.com/database-credentials configured
```

## 🔒 Security Features

- **Automatic Value Masking**: Sensitive keys (containing 'password', 'token', 'key', 'secret') are automatically hidden during input
- **Selective Decryption Display**: Option to show masked values first, then reveal full values if needed
- **Automatic Backups**: Original files are backed up before updates
- **No Plaintext Storage**: Secrets are immediately encrypted using kubeseal

## 🏗️ Project Structure

```
sealed-secret-manager/
├── ssm.py                    # Main CLI application
├── setup.py                  # Python package configuration
├── _ssm_completion.zsh       # zsh tab completion script
├── _ssm_completion.bash      # bash tab completion script
└── README.md                 # This file
```

## ⚙️ Configuration

SSM uses the following default settings:

- **Default namespace**: `default`
- **Controller namespace**: `sealed-secrets`
- **Working directory**: Current directory

These can be overridden using command-line flags or by modifying the script.

## 🐛 Troubleshooting

### Common Issues

1. **"kubectl not found"**: Install kubectl CLI tool
2. **"kubeseal not found"**: Install kubeseal CLI tool
3. **"PyYAML library not found"**: Install with `pip3 install PyYAML`
4. **Permission denied**: Ensure proper kubectl context and permissions
5. **Completion not working**: 
   - Ensure completion is properly installed: `ls ~/.zsh/completions/_ssm`
   - Check fpath includes completion directory: `echo $fpath`
   - Reload completions: `compinit`
   - Restart shell: `exec zsh`
6. **Completion errors**: If you get `_arguments:comparguments:327` errors:
   - Remove any old sourced completion from ~/.zshrc
   - Reinstall using the proper installation method above
   - Restart your shell: `exec zsh`
7. **Bash completion not working**:
   - Check bash completion is enabled: `type _completion_loader`
   - Verify completion file exists: `ls ~/.bash_completion.d/_ssm`
   - Test if completion function is loaded: `complete -p ssm`
   - Reload bash config: `source ~/.bashrc`
   - Try manual load: `source ~/.bash_completion.d/_ssm`
8. **Bash completion shows no suggestions**:
   - Press TAB twice instead of once
   - Check if bash-completion package is installed: `which bash_completion`
   - On macOS with Homebrew: `brew install bash-completion`
   - Add to ~/.bash_profile: `[[ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]] && . "/opt/homebrew/etc/profile.d/bash_completion.sh"`

### Error Handling

SSM provides detailed error messages including:
- Tool availability checks
- Kubernetes connectivity issues
- File permission problems
- YAML parsing errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 🔗 Related Projects

- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets): The underlying encryption technology
- [kubectl](https://kubernetes.io/docs/reference/kubectl/): Kubernetes command-line tool
- [Kubernetes](https://kubernetes.io/): Container orchestration platform

---

**Happy secret managing! 🔐**