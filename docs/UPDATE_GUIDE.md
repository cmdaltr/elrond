# elrond Update Guide

**Feature**: Platform-aware update system
**Version**: elrond v2.1+
**Status**: ✅ Implemented

---

## Overview

elrond now includes a **cross-platform update system** that automatically updates elrond and all dependencies based on your platform. The new Python-based updater replaces the legacy Ubuntu-only bash script.

### Supported Platforms
- ✅ **Linux**: Ubuntu, Debian, RHEL, CentOS, Fedora, Arch
- ✅ **macOS**: 11+ (Intel & Apple Silicon)
- ✅ **Windows**: 10, 11, Server 2019/2022

---

## Quick Start

### Simple Update (Recommended)

```bash
# From elrond directory
./update.sh
```

or

```bash
# Direct Python script
python3 update_elrond.py
```

This will update **everything**:
- System packages
- elrond repository
- Python dependencies
- Forensic tools
- SIEM tools (Splunk, Elasticsearch, Kibana)
- Additional repositories
- ClamAV signatures

---

## Update Steps

The updater performs 8 steps in sequence:

### STEP 1: System Packages
Updates your system package manager:
- **Linux (apt)**: `apt update && apt upgrade`
- **Linux (dnf/yum)**: `dnf update`
- **macOS**: `brew update && brew upgrade`
- **Windows**: `choco upgrade all` (if Chocolatey installed)

### STEP 2: elrond Repository
Updates elrond from GitHub:
- If `/opt/elrond` doesn't exist: Clones repository
- If exists: Pulls latest changes from `main` branch

### STEP 3: Python Dependencies
Updates all Python packages:
- Reads `pyproject.toml`
- Installs/upgrades all dependencies
- Installs optional extras: `[all]`

### STEP 4: Forensic Tools
Updates forensic analysis tools:
- **Linux**: ewf-tools, yara, clamav, sleuthkit, qemu-utils, volatility3
- **macOS**: libewf, yara, clamav, sleuthkit, qemu, volatility

### STEP 5: SIEM Tools
Checks and updates SIEM tools with version compatibility:
- Detects installed versions of Splunk, Elasticsearch, Kibana
- Verifies version compatibility with platform
- **Prompts** if incompatible version found
- **Auto-downloads** compatible version if approved
- **Validates** Elasticsearch/Kibana version match

Example output:
```
STEP 5: Checking SIEM Tools
======================================================================

  Checking splunk...
    Installed: 9.0.5
    Compatible: False - Version 9.0.5 is below minimum 9.1.0 for ubuntu_22.04
    Incompatible version detected!
    Update splunk to compatible version? [y/N]: y
    ✓ splunk 9.2.0 installed successfully

  Checking elasticsearch...
    Installed: 8.11.0
    Compatible: True - Version 8.11.0 is compatible with ubuntu_22.04

  Checking kibana...
    Installed: 8.11.0
    Compatible: True - Version 8.11.0 is compatible with ubuntu_22.04

  Elasticsearch/Kibana version match: True
  Elasticsearch 8.11.0 and Kibana 8.11.0 versions match
```

### STEP 6: Additional Repositories
Updates supplementary tools from GitHub:
- USN-Journal-Parser
- KStrike
- plaso
- etl-parser
- gandalf
- sigma
- DeepBlueCLI
- KAPE
- attack-navigator

If repository doesn't exist locally, it clones it. If it exists, it pulls latest changes.

### STEP 7: ClamAV Signatures
Updates virus definition database:
- Stops `clamav-freshclam` service
- Runs `freshclam` to download latest signatures
- Restarts service

### STEP 8: Permissions
Sets correct file ownership and permissions:
- Changes ownership to current user
- Sets permissions to `755`
- Makes `elrond.py` executable

---

## Advanced Usage

### Command-Line Options

```bash
python3 update_elrond.py --help
```

**Options**:
```
--quiet, -q         Suppress verbose output
--skip-siem         Skip SIEM tool updates
--skip-repos        Skip additional repository updates
```

**Examples**:
```bash
# Quiet mode (minimal output)
python3 update_elrond.py --quiet

# Skip SIEM updates
python3 update_elrond.py --skip-siem

# Skip additional repo updates
python3 update_elrond.py --skip-repos

# Combine options
python3 update_elrond.py --quiet --skip-siem --skip-repos
```

---

## Platform-Specific Notes

### Linux

**Package Managers Supported**:
- apt (Ubuntu, Debian, Kali, Mint)
- dnf (Fedora, RHEL 8+)
- yum (RHEL 7, CentOS)
- pacman (Arch, Manjaro)

**Permissions**:
- Uses `sudo` for system operations
- Sets ownership based on current user (UID 1000)

**Systemd Services**:
- Manages ClamAV freshclam service
- Manages Elasticsearch/Kibana services (if installed)

### macOS

**Package Manager**:
- Requires **Homebrew** (`brew`)
- Install Homebrew: https://brew.sh

**Permissions**:
- Uses standard Unix permissions
- No `sudo` required for Homebrew operations

**ARM64 (Apple Silicon)**:
- Automatically detects architecture
- Downloads ARM64 packages where available
- Falls back to Intel packages with Rosetta 2

### Windows

**Package Managers**:
- **Chocolatey** (recommended): https://chocolatey.org
- **Winget** (alternative, limited support)

**Permissions**:
- May require running as Administrator
- Uses Windows-style paths (`C:\Program Files\...`)

**WSL2**:
- If using WSL2, run updater inside WSL environment
- Treats WSL as Linux (uses apt/dnf/yum)

---

## Troubleshooting

### "Permission denied" Error

**Cause**: Insufficient permissions

**Solution (Linux/macOS)**:
```bash
sudo python3 update_elrond.py
```

**Solution (Windows)**:
- Run PowerShell as Administrator
- Or use WSL2

### "git: command not found"

**Cause**: Git not installed

**Solution**:
```bash
# Linux (apt)
sudo apt install git

# Linux (dnf/yum)
sudo dnf install git

# macOS
brew install git

# Windows (Chocolatey)
choco install git
```

### "Package manager not found"

**Cause**: Unsupported package manager

**Solution**:
- Linux: Install apt, dnf, yum, or pacman
- macOS: Install Homebrew
- Windows: Install Chocolatey

### SIEM Update Fails

**Cause**: Download error, network issues, or incompatible version

**Solution**:
```bash
# Skip SIEM updates
python3 update_elrond.py --skip-siem

# Manual SIEM installation (see SIEM_AUTO_INSTALL.md)
```

### Repository Clone/Pull Fails

**Cause**: Network issues or authentication required

**Solution**:
```bash
# Skip repo updates
python3 update_elrond.py --skip-repos

# Manual clone
cd /opt
sudo git clone https://github.com/cyberg3cko/elrond.git
```

### ClamAV Update Fails

**Cause**: freshclam service not running or network issues

**Solution**:
```bash
# Linux: Restart freshclam
sudo systemctl restart clamav-freshclam

# macOS: Run freshclam manually
freshclam

# Windows: Update via ClamAV GUI
```

---

## Manual Update (Fallback)

If the automatic updater fails, you can update manually:

### 1. Update elrond Repository
```bash
cd /opt/elrond
git pull origin main
```

### 2. Update Python Dependencies
```bash
# Create/activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[all]" --upgrade
```

### 3. Update System Packages
```bash
# Linux (apt)
sudo apt update && sudo apt upgrade -y

# Linux (dnf)
sudo dnf update -y

# macOS
brew update && brew upgrade

# Windows (Chocolatey)
choco upgrade all -y
```

### 4. Update Forensic Tools
See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for manual tool installation.

### 5. Update SIEM Tools
See [SIEM_AUTO_INSTALL.md](SIEM_AUTO_INSTALL.md) for SIEM tool installation.

---

## Update Frequency

**Recommended Schedule**:
- **Weekly**: System packages and ClamAV signatures
- **Monthly**: elrond repository, Python dependencies, forensic tools
- **As Needed**: SIEM tools (when version incompatibility detected)

**Automated Updates**:

Create a cron job (Linux/macOS):
```bash
# Edit crontab
crontab -e

# Add weekly update (every Sunday at 2 AM)
0 2 * * 0 /opt/elrond/update.sh >> /var/log/elrond-update.log 2>&1
```

Create a scheduled task (Windows):
```powershell
# Run as Administrator
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\opt\elrond\update_elrond.py"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
Register-ScheduledTask -TaskName "elrond Update" -Action $action -Trigger $trigger
```

---

## What Gets Updated?

### Always Updated
✅ elrond source code (from GitHub)
✅ Python dependencies (from PyPI)
✅ System packages (via package manager)
✅ ClamAV signatures (virus definitions)

### Conditionally Updated
⚠️ **SIEM tools** - Only if incompatible version detected (with user confirmation)
⚠️ **Additional repos** - Only if `--skip-repos` not specified
⚠️ **Forensic tools** - Only available packages (platform-dependent)

### Never Updated
❌ User configuration files (preserved)
❌ Case data (in output directories)
❌ Custom scripts (unless in elrond repo)

---

## Rollback (If Update Breaks Something)

If an update causes issues:

### 1. Revert Git Repository
```bash
cd /opt/elrond
git log  # Find previous commit
git checkout <commit-hash>
```

### 2. Reinstall Previous Python Version
```bash
pip install -e ".[all]" --force-reinstall
```

### 3. Restore from Backup
Always create a backup before updating:
```bash
# Before update
sudo cp -r /opt/elrond /opt/elrond.backup.$(date +%Y%m%d)

# After failed update, restore
sudo rm -rf /opt/elrond
sudo mv /opt/elrond.backup.YYYYMMDD /opt/elrond
```

---

## Migration from Legacy update.sh

The old `update.sh` script has been replaced with a platform-aware Python updater. The legacy script is now a wrapper that calls the new updater.

**Changes**:
- ✅ **Cross-platform**: Works on Linux, macOS, Windows (not just Ubuntu)
- ✅ **Package manager detection**: Automatically detects apt/dnf/yum/pacman/brew
- ✅ **SIEM version checking**: Validates compatibility before updating
- ✅ **Better error handling**: Continues on non-critical errors
- ✅ **Progress reporting**: Clear status for each step
- ✅ **Command-line options**: `--quiet`, `--skip-siem`, `--skip-repos`

**Removed** (Ubuntu-specific):
- ❌ Hardcoded `/opt/elrond` path (now platform-aware)
- ❌ Hardcoded `apt` commands (now uses detected package manager)
- ❌ Hardcoded Elasticsearch 7.x (now uses version compatibility)
- ❌ Hardcoded Splunk 9.0.5 (now uses latest compatible version)
- ❌ User profile detection via UID 1000 (now uses current user)

---

## Update Summary Example

```
🚀 ===================================================================
elrond Platform-Aware Update
======================================================================== 🚀

Platform: linux
Package Manager: apt
Install Root: /opt/elrond

======================================================================
STEP 1: Updating System Packages
======================================================================
Running: sudo apt update
... [output]

======================================================================
STEP 2: Updating elrond Repository
======================================================================
Running: git pull origin main
... [output]

======================================================================
STEP 3: Updating Python Dependencies
======================================================================
Running: /usr/bin/python3 -m pip install -e /opt/elrond[all] --upgrade
... [output]

======================================================================
STEP 4: Updating Forensic Tools
======================================================================
Running: sudo apt install -y ewf-tools yara clamav sleuthkit ...
... [output]

======================================================================
STEP 5: Checking SIEM Tools
======================================================================
  Checking splunk...
    Installed: 9.2.0
    Compatible: True - Version 9.2.0 is compatible with ubuntu_22.04
  ... [more output]

======================================================================
STEP 6: Updating Additional Repositories
======================================================================
  USN-Journal-Parser...
    ✓ Updated
  KStrike...
    ✓ Updated
  ... [more output]

======================================================================
STEP 7: Updating ClamAV Signatures
======================================================================
Running: sudo freshclam
... [output]

======================================================================
STEP 8: Setting Permissions
======================================================================
Running: sudo chown -R ben:ben /opt/elrond
... [output]

======================================================================
UPDATE SUMMARY
======================================================================

  ✓ All updates completed successfully!

  Recommended: Restart your system to apply all changes.

  🎉 Update complete! Enjoy the latest elrond.
```

---

*Document created: October 2025*
*elrond v2.1 - Platform-Aware Update System*
