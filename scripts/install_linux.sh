#!/bin/bash
#
# Automated installation script for elrond on Linux
# Supports Ubuntu/Debian (apt) and RHEL/CentOS (yum)
#
# Usage:
#   sudo ./install_linux.sh                 # Install all tools
#   sudo ./install_linux.sh --required-only # Install required tools only
#   ./install_linux.sh --check              # Check what's installed (no sudo)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_ONLY=false
CHECK_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --required-only)
            REQUIRED_ONLY=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "elrond Linux Installation Script"
            echo ""
            echo "Usage:"
            echo "  sudo ./install_linux.sh                 Install all tools"
            echo "  sudo ./install_linux.sh --required-only Install required tools only"
            echo "  ./install_linux.sh --check              Check installed tools (no sudo)"
            echo ""
            exit 0
            ;;
    esac
done

# Detect package manager
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
    UPDATE_CMD="apt-get update"
    INSTALL_CMD="apt-get install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="yum check-update"
    INSTALL_CMD="yum install -y"
else
    echo -e "${RED}Error: Neither apt-get nor yum found${NC}"
    echo "This script only supports Ubuntu/Debian (apt) and RHEL/CentOS (yum)"
    exit 1
fi

echo "=========================================="
echo "elrond Linux Installation"
echo "Package Manager: $PKG_MANAGER"
echo "=========================================="
echo ""

# Check if running as root (unless --check)
if [ "$CHECK_ONLY" = false ] && [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Usage: sudo $0"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install a package
install_package() {
    local package=$1
    local description=$2

    if [ "$CHECK_ONLY" = true ]; then
        if command_exists "$package"; then
            echo -e "${GREEN}✓${NC} $description ($package) - installed"
        else
            echo -e "${YELLOW}✗${NC} $description ($package) - not installed"
        fi
        return
    fi

    echo -e "Installing $description ($package)..."
    if $INSTALL_CMD "$package"; then
        echo -e "${GREEN}✓${NC} $description installed"
    else
        echo -e "${RED}✗${NC} Failed to install $description"
    fi
}

# Function to install Python package
install_pip_package() {
    local package=$1
    local description=$2

    if [ "$CHECK_ONLY" = true ]; then
        if pip3 show "$package" &> /dev/null; then
            echo -e "${GREEN}✓${NC} $description ($package) - installed"
        else
            echo -e "${YELLOW}✗${NC} $description ($package) - not installed"
        fi
        return
    fi

    echo -e "Installing $description via pip..."
    if pip3 install "$package"; then
        echo -e "${GREEN}✓${NC} $description installed"
    else
        echo -e "${RED}✗${NC} Failed to install $description"
    fi
}

# Update package manager
if [ "$CHECK_ONLY" = false ]; then
    echo "Updating package manager..."
    $UPDATE_CMD || true
    echo ""
fi

echo "=========================================="
echo "Required Tools"
echo "=========================================="

# Python 3 and pip
install_package python3 "Python 3"
install_package python3-pip "Python 3 pip"

# EWF Tools (E01 images) - REQUIRED
if [ "$PKG_MANAGER" = "apt" ]; then
    install_package ewf-tools "Expert Witness Format Tools"
else
    install_package libewf "Expert Witness Format Tools"
fi

# Volatility 3 - REQUIRED
install_pip_package volatility3 "Volatility 3 Memory Forensics"

if [ "$REQUIRED_ONLY" = false ]; then
    echo ""
    echo "=========================================="
    echo "Optional Tools"
    echo "=========================================="

    # QEMU (for VMDK mounting)
    if [ "$PKG_MANAGER" = "apt" ]; then
        install_package qemu-utils "QEMU utilities (VMDK support)"
    else
        install_package qemu-img "QEMU utilities (VMDK support)"
    fi

    # libvshadow (Volume Shadow Copy)
    if [ "$PKG_MANAGER" = "apt" ]; then
        install_package libvshadow-utils "libvshadow (VSS support)"
    fi

    # The Sleuth Kit
    install_package sleuthkit "The Sleuth Kit (filesystem tools)"

    # YARA
    install_package yara "YARA pattern matching"

    # ClamAV
    install_package clamav "ClamAV antivirus"

    # foremost (file carving)
    install_package foremost "foremost file carving"

    # Python tools
    install_pip_package plaso "Plaso timeline analysis"
    install_pip_package analyzeMFT "analyzeMFT"
    install_pip_package python-evtx "python-evtx (Windows Event Logs)"

    # Volatility 2 (legacy)
    echo "Note: Volatility 2 requires manual installation from GitHub"
    echo "See: https://github.com/volatilityfoundation/volatility"
    echo ""

    # RegRipper (requires Perl)
    if command_exists perl; then
        echo -e "${GREEN}✓${NC} Perl is installed (needed for RegRipper)"
    else
        echo -e "${YELLOW}!${NC} Perl not found - needed for RegRipper"
        install_package perl "Perl (for RegRipper)"
    fi

    echo "Note: RegRipper requires manual installation from GitHub"
    echo "See: https://github.com/keydet89/RegRipper3.0"
    echo ""
fi

# Check Python version
echo "=========================================="
echo "Python Version Check"
echo "=========================================="
python3 --version

# Verify elrond dependencies
if [ "$CHECK_ONLY" = false ]; then
    echo ""
    echo "=========================================="
    echo "Installing elrond Python dependencies"
    echo "=========================================="

    # Check if we're in the elrond directory
    if [ -f "pyproject.toml" ]; then
        echo "Installing elrond in development mode..."
        pip3 install -e .
        echo ""
        echo "Installing Linux-specific requirements..."
        pip3 install -r requirements/linux.txt
    else
        echo -e "${YELLOW}Warning: Not in elrond directory${NC}"
        echo "Skipping elrond installation"
        echo "Run this script from the elrond repository root"
    fi
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""

if [ "$CHECK_ONLY" = true ]; then
    echo "Run without --check to install missing tools"
else
    echo "Verify installation with:"
    echo "  elrond --check-dependencies"
    echo ""
    echo "Or run:"
    echo "  python3 -m elrond.cli --check-dependencies"
fi
