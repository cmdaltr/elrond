# elrond Installation Guide

## Quick Start

### Linux (Ubuntu/Debian)
```bash
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
chmod +x scripts/install_linux.sh
sudo ./scripts/install_linux.sh
```

### macOS (Intel or Apple Silicon)
```bash
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
chmod +x scripts/install_macos.sh
./scripts/install_macos.sh
```

### Windows (WSL2 - Recommended)
```powershell
# PowerShell as Administrator
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
.\scripts\install_windows_wsl.ps1
```

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Platform-Specific Guides](#platform-specific-guides)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Manual Installation](#manual-installation)

---

## Prerequisites

### All Platforms

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** (for cloning repository)
- **10GB+ disk space** (for tools and dependencies)
- **Internet connection** (for downloading tools)

### Platform-Specific

#### Linux
- **Package manager**: apt-get (Ubuntu/Debian) or yum (RHEL/CentOS)
- **sudo access** (for installing system tools)
- **FUSE support** (kernel module, usually pre-installed)

#### macOS
- **Homebrew** (install from https://brew.sh)
- **Xcode Command Line Tools**: `xcode-select --install`
- **macOS 11+** recommended (older versions may work)

#### Windows
- **Windows 10 version 2004+** or **Windows 11** (for WSL2)
- **Administrator privileges**
- **Virtualization enabled in BIOS** (for WSL2)

---

## Installation Methods

### Method 1: Automated Installation (Recommended)

The automated installation scripts handle all dependencies and tools.

#### Choose Your Platform:

<details>
<summary><b>Linux</b></summary>

```bash
# Clone repository
git clone https://github.com/cyberg3cko/elrond.git
cd elrond

# Install everything (requires sudo)
chmod +x scripts/install_linux.sh
sudo ./scripts/install_linux.sh

# Or install required tools only
sudo ./scripts/install_linux.sh --required-only

# Check what would be installed (no sudo needed)
./scripts/install_linux.sh --check
```

**What gets installed:**
- ✅ Python 3 and pip
- ✅ ewf-tools (E01 image support)
- ✅ Volatility 3 (memory forensics)
- ✅ qemu-utils (VMDK support)
- ✅ The Sleuth Kit, YARA, ClamAV, foremost
- ✅ plaso, analyzeMFT, python-evtx
- ✅ elrond Python package

</details>

<details>
<summary><b>macOS</b></summary>

```bash
# Clone repository
git clone https://github.com/cyberg3cko/elrond.git
cd elrond

# Install everything
chmod +x scripts/install_macos.sh
./scripts/install_macos.sh

# Or install required tools only
./scripts/install_macos.sh --required-only

# Check what's installed
./scripts/install_macos.sh --check
```

**What gets installed:**
- ✅ Homebrew (if not already installed)
- ✅ libewf (E01 image support)
- ✅ Volatility 3 (memory forensics)
- ✅ qemu (VMDK support)
- ✅ The Sleuth Kit, YARA, ClamAV, foremost
- ✅ plaso, analyzeMFT, python-evtx
- ✅ elrond Python package

**Apple Silicon (M1/M2/M3) Notes:**
- All tools work natively on ARM64
- No Rosetta 2 needed for core functionality
- Plaso may show warnings but works correctly

</details>

<details>
<summary><b>Windows (WSL2)</b></summary>

```powershell
# PowerShell as Administrator
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
.\scripts\install_windows_wsl.ps1

# Or check current status
.\scripts\install_windows_wsl.ps1 -CheckOnly

# Or install required tools only
.\scripts\install_windows_wsl.ps1 -RequiredOnly
```

**What gets installed:**
1. WSL2 (Windows Subsystem for Linux)
2. Ubuntu 22.04 LTS
3. All Linux forensic tools (same as Linux installation)
4. elrond Python package

**After Installation:**
```powershell
# Run elrond from Windows
wsl elrond --check-dependencies

# Process Windows evidence
wsl elrond -C -c CASE-001 -s /mnt/c/evidence

# Access WSL shell
wsl
```

</details>

### Method 2: Python Package Installation

Install elrond via Python package manager (tools installed separately).

```bash
# Install from repository
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
pip3 install -e .

# Install platform-specific requirements
pip3 install -r requirements/linux.txt    # Linux
pip3 install -r requirements/macos.txt    # macOS
pip3 install -r requirements/base.txt     # Minimum requirements

# Use built-in installer for tools
elrond --install
```

### Method 3: Using elrond --install Command

After installing the Python package, use the built-in installer:

```bash
# Install all tools
elrond --install

# Interactive mode (prompts for each tool)
elrond --install --interactive

# Dry run (show what would be installed)
elrond --install --dry-run

# Install required tools only
elrond --install --required-only

# Windows: Show WSL setup instructions
elrond --install --wsl
```

---

## Platform-Specific Guides

### Linux Installation (Detailed)

#### Ubuntu/Debian (apt)

```bash
# Update package manager
sudo apt-get update

# Install required tools
sudo apt-get install -y \
    python3 \
    python3-pip \
    ewf-tools \
    git

# Install optional tools
sudo apt-get install -y \
    qemu-utils \
    libvshadow-utils \
    sleuthkit \
    yara \
    clamav \
    foremost

# Install Python forensic tools
pip3 install \
    volatility3 \
    plaso \
    analyzeMFT \
    python-evtx

# Install elrond
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
pip3 install -e .
pip3 install -r requirements/linux.txt
```

#### RHEL/CentOS (yum)

```bash
# Update package manager
sudo yum check-update

# Install required tools
sudo yum install -y \
    python3 \
    python3-pip \
    libewf \
    git

# Install optional tools
sudo yum install -y \
    qemu-img \
    sleuthkit \
    yara \
    clamav

# Install Python tools (same as Ubuntu)
pip3 install volatility3 plaso analyzeMFT python-evtx

# Install elrond
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
pip3 install -e .
pip3 install -r requirements/linux.txt
```

### macOS Installation (Detailed)

#### Step 1: Install Homebrew

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH
# For Apple Silicon (M1/M2/M3):
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# For Intel Macs:
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.bash_profile
eval "$(/usr/local/bin/brew shellenv)"
```

#### Step 2: Install Tools

```bash
# Update Homebrew
brew update

# Install required tools
brew install \
    python3 \
    libewf \
    git

# Install optional tools
brew install \
    qemu \
    sleuthkit \
    yara \
    clamav \
    foremost

# Install Python forensic tools
pip3 install \
    volatility3 \
    plaso \
    analyzeMFT \
    python-evtx
```

#### Step 3: Install elrond

```bash
# Clone repository
git clone https://github.com/cyberg3cko/elrond.git
cd elrond

# Install elrond
pip3 install -e .
pip3 install -r requirements/macos.txt
```

#### Apple Silicon Notes

All tools work on ARM64, but if you encounter issues:

```bash
# Force x86_64 installation (rare, Rosetta 2 required)
arch -x86_64 brew install <package>

# Check architecture
uname -m  # Should show "arm64" for Apple Silicon
```

### Windows Installation (Detailed)

#### Option 1: WSL2 (Recommended - 100% Tool Compatibility)

**Step 1: Install WSL2**

```powershell
# PowerShell as Administrator

# One-command installation (Windows 11 or Windows 10 2004+)
wsl --install -d Ubuntu-22.04

# Restart computer
Restart-Computer
```

**Step 2: Complete Ubuntu Setup**

After restart:
1. Open "Ubuntu 22.04" from Start menu
2. Create username and password
3. Wait for setup to complete

**Step 3: Install elrond in WSL**

```bash
# In Ubuntu (WSL) terminal

# Update packages
sudo apt-get update

# Install elrond
cd /opt
sudo git clone https://github.com/cyberg3cko/elrond.git
sudo chown -R $USER:$USER elrond
cd elrond

# Run installation script
chmod +x scripts/install_linux.sh
sudo ./scripts/install_linux.sh
```

**Step 4: Use elrond from Windows**

```powershell
# Check installation
wsl elrond --check-dependencies

# Process evidence on C: drive
wsl elrond -C -c CASE-001 -s /mnt/c/evidence

# Process evidence on D: drive
wsl elrond -C -c CASE-001 -s /mnt/d/cases/evidence
```

**WSL Path Mapping:**
- `C:\evidence` → `/mnt/c/evidence` (in WSL)
- `D:\cases` → `/mnt/d/cases` (in WSL)
- Windows user home → `/mnt/c/Users/YourName`

#### Option 2: Native Windows (Limited - 50% Tool Compatibility)

⚠️ **Not Recommended** - Many forensic tools don't work on native Windows.

Only works for:
- ✅ Volatility 3 (memory analysis)
- ✅ Python-based artifact parsers
- ❌ No disk image mounting
- ❌ No Unix-based tools

```powershell
# Install Python 3.9+
# Download from: https://www.python.org/downloads/

# Install elrond
git clone https://github.com/cyberg3cko/elrond.git
cd elrond
pip install -e .
pip install -r requirements\base.txt

# Install limited tools
pip install volatility3 analyzeMFT python-evtx
```

---

## Verification

After installation, verify everything works:

```bash
# Check all dependencies
elrond --check-dependencies

# Or run directly
python3 -m elrond.cli --check-dependencies
```

**Expected Output:**

```
======================================================================
Elrond Dependency Checker
======================================================================

Platform: linux
Architecture: x86_64

✓ Permissions: Running as root

Available Tools (15):
----------------------------------------------------------------------
  ✓ [DISK_IMAGING ] Expert Witness Format Tools /usr/bin/ewfmount
  ✓ [MEMORY      ] Volatility 3              /usr/local/bin/vol.py
  ✓ [FILESYSTEM  ] The Sleuth Kit            /usr/bin/fls
  ...

======================================================================
Summary: 15/15 tools available
✓ All required tools are available.
======================================================================
```

### Test Installation

```bash
# Create test directory
mkdir -p /tmp/test_evidence

# Test elrond help
elrond --help

# Test version
elrond --version

# Test with dummy case (will fail gracefully without evidence)
elrond -C -c TEST-001 -s /tmp/test_evidence
```

---

## Troubleshooting

### Common Issues

<details>
<summary><b>Issue: "command not found: elrond"</b></summary>

**Solution:**

```bash
# Check if installed
pip3 show elrond-dfir

# If not installed
cd /path/to/elrond
pip3 install -e .

# Add to PATH (if needed)
export PATH=$PATH:~/.local/bin

# Or run directly
python3 -m elrond.cli --help
```

</details>

<details>
<summary><b>Issue: "Module not found: yaml"</b></summary>

**Solution:**

```bash
# Install PyYAML
pip3 install pyyaml

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements/base.txt
```

</details>

<details>
<summary><b>Issue: "Permission denied" when mounting images</b></summary>

**Solution:**

```bash
# Linux: Need sudo for mounting
sudo elrond -C -c CASE-001 -s /evidence

# macOS: May need to allow FUSE in System Preferences
# System Preferences → Security & Privacy → Allow osxfuse

# Or run check
sudo elrond --check-dependencies
```

</details>

<details>
<summary><b>Issue: WSL installation fails on Windows</b></summary>

**Solution:**

1. **Check Windows version:**
   ```powershell
   winver  # Must be 2004 (build 19041) or higher
   ```

2. **Enable virtualization in BIOS:**
   - Restart computer
   - Enter BIOS (usually F2, F10, or Del during boot)
   - Enable VT-x (Intel) or AMD-V (AMD)

3. **Manual WSL installation:**
   ```powershell
   # Enable WSL
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

   # Enable Virtual Machine Platform
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

   # Restart
   Restart-Computer

   # Download WSL2 kernel update
   # https://aka.ms/wsl2kernel

   # Set WSL2 as default
   wsl --set-default-version 2

   # Install Ubuntu from Microsoft Store
   ```

</details>

<details>
<summary><b>Issue: Homebrew installation fails on macOS</b></summary>

**Solution:**

```bash
# Install Xcode Command Line Tools first
xcode-select --install

# Then retry Homebrew installation
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# For Apple Silicon, add to PATH
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
source ~/.zprofile
```

</details>

<details>
<summary><b>Issue: "Tool not found" errors</b></summary>

**Solution:**

```bash
# Check which tools are missing
elrond --check-dependencies

# Install missing tool manually
# Example for ewftools:
sudo apt-get install ewf-tools  # Linux
brew install libewf             # macOS

# Or use automated installer
elrond --install --interactive
```

</details>

---

## Manual Installation

For advanced users or custom setups.

### 1. Install Python Dependencies

```bash
# Clone repository
git clone https://github.com/cyberg3cko/elrond.git
cd elrond

# Install base dependencies
pip3 install -r requirements/base.txt

# Install platform-specific dependencies
pip3 install -r requirements/linux.txt    # Linux
pip3 install -r requirements/macos.txt    # macOS

# Install development dependencies (optional)
pip3 install -r requirements/dev.txt
```

### 2. Install Forensic Tools Manually

See [TOOL_COMPATIBILITY.md](TOOL_COMPATIBILITY.md) for complete tool list and installation methods.

**Required Tools:**
- ewftools (libewf): E01 image support
- Volatility 3: Memory forensics

**Optional but Recommended:**
- qemu: VMDK mounting
- The Sleuth Kit: Filesystem analysis
- YARA: Malware detection
- plaso: Timeline analysis

### 3. Configure elrond

```bash
# Install elrond in development mode
pip3 install -e .

# Or install as package
python3 setup.py install

# Configure (if needed)
# Edit ~/.elrond/config.yaml
```

### 4. Verify Installation

```bash
# Check dependencies
elrond --check-dependencies

# Run tests (if dev dependencies installed)
pytest tests/
```

---

## Updating elrond

```bash
# Navigate to elrond directory
cd /path/to/elrond

# Pull latest changes
git pull

# Update dependencies
pip3 install -r requirements/base.txt

# Update tools
elrond --install  # Re-run to get new tools
```

---

## Uninstalling

### Remove elrond

```bash
# Uninstall Python package
pip3 uninstall elrond-dfir

# Remove repository
rm -rf /path/to/elrond
```

### Remove Forensic Tools

#### Linux
```bash
sudo apt-get remove ewf-tools qemu-utils sleuthkit yara clamav foremost
pip3 uninstall volatility3 plaso analyzeMFT python-evtx
```

#### macOS
```bash
brew uninstall libewf qemu sleuthkit yara clamav foremost
pip3 uninstall volatility3 plaso analyzeMFT python-evtx
```

#### Windows (WSL)
```powershell
# Uninstall WSL distribution
wsl --unregister Ubuntu-22.04

# Or keep WSL, just remove elrond
wsl
sudo rm -rf /opt/elrond
pip3 uninstall elrond-dfir
```

---

## Next Steps

After successful installation:

1. **Read Documentation**: See [README.md](README.md) for usage
2. **Check Compatibility**: See [TOOL_COMPATIBILITY.md](TOOL_COMPATIBILITY.md)
3. **Run First Case**: Try processing test evidence
4. **Report Issues**: https://github.com/cyberg3cko/elrond/issues

---

## Getting Help

- **Documentation**: See [docs/](docs/) directory
- **Issues**: https://github.com/cyberg3cko/elrond/issues
- **Discussions**: https://github.com/cyberg3cko/elrond/discussions

---

**elrond v2.0** - Cross-platform digital forensics automation
