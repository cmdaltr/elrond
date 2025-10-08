# elrond Windows Installation Script (WSL2)
#
# This script sets up WSL2 with Ubuntu and installs elrond with all tools
# Requires Windows 10 version 2004+ or Windows 11
#
# Usage (PowerShell as Administrator):
#   .\install_windows_wsl.ps1                 # Full installation
#   .\install_windows_wsl.ps1 -CheckOnly      # Check current status
#   .\install_windows_wsl.ps1 -RequiredOnly   # Install required tools only
#

param(
    [switch]$CheckOnly = $false,
    [switch]$RequiredOnly = $false,
    [switch]$Help = $false
)

# Check if running as Administrator
function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Display help
if ($Help) {
    Write-Host "elrond Windows Installation Script (WSL2)"
    Write-Host ""
    Write-Host "Usage (PowerShell as Administrator):"
    Write-Host "  .\install_windows_wsl.ps1                 Full installation"
    Write-Host "  .\install_windows_wsl.ps1 -CheckOnly      Check current status"
    Write-Host "  .\install_windows_wsl.ps1 -RequiredOnly   Install required tools only"
    Write-Host ""
    Write-Host "Requirements:"
    Write-Host "  - Windows 10 version 2004+ or Windows 11"
    Write-Host "  - Administrator privileges"
    Write-Host "  - Internet connection"
    Write-Host ""
    exit 0
}

Write-Host "=========================================="
Write-Host "elrond Windows Installation (WSL2)"
Write-Host "=========================================="
Write-Host ""

# Check Windows version
$winVersion = [System.Environment]::OSVersion.Version
Write-Host "Windows Version: $($winVersion.Major).$($winVersion.Minor).$($winVersion.Build)"

if ($winVersion.Build -lt 19041) {
    Write-Host "ERROR: Windows 10 version 2004 (build 19041) or higher required" -ForegroundColor Red
    Write-Host "Your build: $($winVersion.Build)"
    Write-Host ""
    Write-Host "Please update Windows or use Linux/macOS for elrond"
    exit 1
}
Write-Host "✓ Windows version compatible" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
if (-not $CheckOnly -and -not (Test-Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

# Function to check if WSL is installed
function Test-WSL {
    try {
        $wslVersion = wsl --version 2>&1
        return $true
    } catch {
        return $false
    }
}

# Function to check if a WSL distribution is installed
function Test-WSLDistribution {
    param([string]$DistroName)

    $distros = wsl --list --quiet
    return $distros -contains $DistroName
}

Write-Host "=========================================="
Write-Host "Checking WSL Status"
Write-Host "=========================================="

# Check if WSL is installed
if (Test-WSL) {
    Write-Host "✓ WSL is installed" -ForegroundColor Green

    # Check WSL version
    $wslList = wsl --list --verbose
    Write-Host ""
    Write-Host "Installed distributions:"
    Write-Host $wslList
    Write-Host ""
} else {
    Write-Host "✗ WSL is not installed" -ForegroundColor Yellow

    if ($CheckOnly) {
        Write-Host ""
        Write-Host "To install WSL, run this script without -CheckOnly as Administrator"
        exit 0
    }

    Write-Host ""
    Write-Host "Installing WSL2..."
    Write-Host ""

    # Install WSL
    Write-Host "Step 1: Installing WSL and Ubuntu..."
    wsl --install -d Ubuntu-22.04

    Write-Host ""
    Write-Host "=========================================="
    Write-Host "WSL Installation Complete"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "IMPORTANT: You must restart your computer now!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restart:"
    Write-Host "  1. Open 'Ubuntu 22.04' from Start menu"
    Write-Host "  2. Create a username and password"
    Write-Host "  3. Run this script again to install elrond tools"
    Write-Host ""

    $restart = Read-Host "Restart now? (Y/n)"
    if ($restart -ne 'n' -and $restart -ne 'N') {
        Restart-Computer -Force
    }

    exit 0
}

# Check if Ubuntu is installed
if (Test-WSLDistribution "Ubuntu-22.04") {
    Write-Host "✓ Ubuntu 22.04 is installed" -ForegroundColor Green
} elseif (Test-WSLDistribution "Ubuntu") {
    Write-Host "✓ Ubuntu is installed" -ForegroundColor Green
    $ubuntuName = "Ubuntu"
} else {
    Write-Host "✗ Ubuntu is not installed" -ForegroundColor Yellow

    if ($CheckOnly) {
        Write-Host ""
        Write-Host "To install Ubuntu, run:"
        Write-Host "  wsl --install -d Ubuntu-22.04"
        exit 0
    }

    Write-Host ""
    Write-Host "Installing Ubuntu 22.04..."
    wsl --install -d Ubuntu-22.04

    Write-Host ""
    Write-Host "Please complete Ubuntu setup:"
    Write-Host "  1. Open 'Ubuntu 22.04' from Start menu"
    Write-Host "  2. Create a username and password"
    Write-Host "  3. Run this script again"
    exit 0
}

# At this point, WSL and Ubuntu are installed
Write-Host ""
Write-Host "=========================================="
Write-Host "Installing elrond in WSL"
Write-Host "=========================================="
Write-Host ""

# Create installation script for WSL
$wslInstallScript = @'
#!/bin/bash
set -e

echo "=========================================="
echo "elrond WSL Installation"
echo "=========================================="
echo ""

# Update apt
echo "Updating package lists..."
sudo apt-get update

# Install required packages
echo ""
echo "Installing required tools..."
sudo apt-get install -y python3 python3-pip git

# Install forensic tools
if [ "$1" = "--required-only" ]; then
    echo ""
    echo "Installing required forensic tools only..."
    sudo apt-get install -y ewf-tools
    pip3 install volatility3
else
    echo ""
    echo "Installing all forensic tools..."
    sudo apt-get install -y \
        ewf-tools \
        qemu-utils \
        libvshadow-utils \
        sleuthkit \
        yara \
        clamav \
        foremost

    # Python tools
    pip3 install \
        volatility3 \
        plaso \
        analyzeMFT \
        python-evtx
fi

# Clone or update elrond repository
echo ""
echo "Setting up elrond..."
if [ -d "/opt/elrond" ]; then
    echo "Updating existing elrond installation..."
    cd /opt/elrond
    git pull
else
    echo "Cloning elrond repository..."
    sudo mkdir -p /opt
    sudo chown $USER:$USER /opt
    cd /opt
    git clone https://github.com/cyberg3cko/elrond.git
    cd elrond
fi

# Install elrond Python dependencies
echo ""
echo "Installing elrond Python dependencies..."
pip3 install -e .
pip3 install -r requirements/linux.txt

# Add elrond to PATH
echo ""
echo "Configuring PATH..."
if ! grep -q "export PATH=\$PATH:/opt/elrond" ~/.bashrc; then
    echo 'export PATH=$PATH:/opt/elrond' >> ~/.bashrc
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Verify installation:"
echo "  wsl elrond --check-dependencies"
echo ""
echo "Access Windows files from WSL:"
echo "  cd /mnt/c/Users/YourName/evidence"
echo ""
echo "Run elrond from Windows:"
echo "  wsl elrond -C -c CASE-001 -s /mnt/c/evidence"
echo ""
'@

# Save script to temp file
$tempScript = "$env:TEMP\install_elrond_wsl.sh"
$wslInstallScript | Out-File -FilePath $tempScript -Encoding ASCII

# Copy script to WSL and execute
Write-Host "Running installation in WSL..."
Write-Host ""

$requiredFlag = if ($RequiredOnly) { "--required-only" } else { "" }

wsl bash -c "cat > /tmp/install_elrond.sh << 'EOFINSTALL'
$wslInstallScript
EOFINSTALL
chmod +x /tmp/install_elrond.sh
/tmp/install_elrond.sh $requiredFlag
"

Write-Host ""
Write-Host "=========================================="
Write-Host "Windows Setup Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "✓ WSL2 installed" -ForegroundColor Green
Write-Host "✓ Ubuntu 22.04 installed" -ForegroundColor Green
Write-Host "✓ elrond and tools installed" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start:"
Write-Host "  # Check dependencies"
Write-Host "  wsl elrond --check-dependencies"
Write-Host ""
Write-Host "  # Run elrond on Windows evidence"
Write-Host "  wsl elrond -C -c CASE-001 -s /mnt/c/evidence"
Write-Host ""
Write-Host "  # Access WSL shell"
Write-Host "  wsl"
Write-Host ""
Write-Host "Evidence Path Mapping:"
Write-Host "  C:\evidence  →  /mnt/c/evidence (in WSL)"
Write-Host "  D:\cases     →  /mnt/d/cases (in WSL)"
Write-Host ""
Write-Host "For more information, see TOOL_COMPATIBILITY.md"
Write-Host ""
