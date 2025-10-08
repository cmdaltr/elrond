#!/bin/bash
#
# Automated installation script for elrond on macOS
# Requires Homebrew (will install if missing)
# Works on both Intel and Apple Silicon (ARM64)
#
# Usage:
#   ./install_macos.sh                 # Install all tools
#   ./install_macos.sh --required-only # Install required tools only
#   ./install_macos.sh --check         # Check what's installed
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
            echo "elrond macOS Installation Script"
            echo ""
            echo "Usage:"
            echo "  ./install_macos.sh                 Install all tools"
            echo "  ./install_macos.sh --required-only Install required tools only"
            echo "  ./install_macos.sh --check         Check installed tools"
            echo ""
            exit 0
            ;;
    esac
done

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    ARCH_NAME="Apple Silicon (ARM64)"
    BREW_PREFIX="/opt/homebrew"
else
    ARCH_NAME="Intel (x86_64)"
    BREW_PREFIX="/usr/local"
fi

echo "=========================================="
echo "elrond macOS Installation"
echo "Architecture: $ARCH_NAME"
echo "=========================================="
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to install Homebrew if missing
install_homebrew() {
    if command_exists brew; then
        echo -e "${GREEN}✓${NC} Homebrew is installed"
        return
    fi

    if [ "$CHECK_ONLY" = true ]; then
        echo -e "${RED}✗${NC} Homebrew is not installed"
        echo "  Install from: https://brew.sh"
        return
    fi

    echo -e "${YELLOW}!${NC} Homebrew not found"
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH
    if [ "$ARCH" = "arm64" ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.bash_profile
        eval "$(/usr/local/bin/brew shellenv)"
    fi

    echo -e "${GREEN}✓${NC} Homebrew installed"
}

# Function to install a Homebrew package
install_brew_package() {
    local package=$1
    local description=$2

    if [ "$CHECK_ONLY" = true ]; then
        if brew list "$package" &> /dev/null; then
            echo -e "${GREEN}✓${NC} $description ($package) - installed"
        else
            echo -e "${YELLOW}✗${NC} $description ($package) - not installed"
        fi
        return
    fi

    echo "Installing $description ($package)..."
    if brew list "$package" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $description already installed"
    else
        if brew install "$package"; then
            echo -e "${GREEN}✓${NC} $description installed"
        else
            echo -e "${RED}✗${NC} Failed to install $description"
        fi
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

    echo "Installing $description via pip..."
    if pip3 install "$package"; then
        echo -e "${GREEN}✓${NC} $description installed"
    else
        echo -e "${RED}✗${NC} Failed to install $description"
    fi
}

# Install/check Homebrew
install_homebrew

# Update Homebrew
if [ "$CHECK_ONLY" = false ]; then
    echo ""
    echo "Updating Homebrew..."
    brew update || true
    echo ""
fi

echo "=========================================="
echo "Required Tools"
echo "=========================================="

# Python 3 (usually pre-installed on macOS)
if command_exists python3; then
    echo -e "${GREEN}✓${NC} Python 3 is installed"
    python3 --version
else
    install_brew_package python3 "Python 3"
fi

# pip3
if command_exists pip3; then
    echo -e "${GREEN}✓${NC} pip3 is installed"
else
    echo "Installing pip3..."
    python3 -m ensurepip
fi

# EWF Tools (E01 images) - REQUIRED
install_brew_package libewf "Expert Witness Format Tools"

# Volatility 3 - REQUIRED
install_pip_package volatility3 "Volatility 3 Memory Forensics"

if [ "$REQUIRED_ONLY" = false ]; then
    echo ""
    echo "=========================================="
    echo "Optional Tools"
    echo "=========================================="

    # QEMU (for VMDK mounting)
    install_brew_package qemu "QEMU (VMDK support)"

    # The Sleuth Kit
    install_brew_package sleuthkit "The Sleuth Kit (filesystem tools)"

    # YARA
    install_brew_package yara "YARA pattern matching"

    # ClamAV
    install_brew_package clamav "ClamAV antivirus"

    # foremost (file carving)
    install_brew_package foremost "foremost file carving"

    # Python tools
    echo ""
    echo "Installing Python forensic tools..."

    install_pip_package analyzeMFT "analyzeMFT"
    install_pip_package python-evtx "python-evtx (Windows Event Logs)"

    # Plaso (may have issues on ARM64)
    if [ "$ARCH" = "arm64" ]; then
        echo -e "${YELLOW}!${NC} Plaso on ARM64 may require Rosetta 2 for some dependencies"
        echo "  Attempting installation..."
    fi
    install_pip_package plaso "Plaso timeline analysis"

    echo ""
    echo "=========================================="
    echo "Manual Installation Required"
    echo "=========================================="

    # Volatility 2 (legacy)
    echo -e "${BLUE}→${NC} Volatility 2 (legacy)"
    echo "  GitHub: https://github.com/volatilityfoundation/volatility"
    echo ""

    # RegRipper (requires Perl)
    echo -e "${BLUE}→${NC} RegRipper (Windows Registry parser)"
    if command_exists perl; then
        echo -e "  ${GREEN}✓${NC} Perl is installed (required)"
    else
        echo -e "  ${YELLOW}!${NC} Perl not found - installing..."
        install_brew_package perl "Perl"
    fi
    echo "  GitHub: https://github.com/keydet89/RegRipper3.0"
    echo ""

    # ShimCacheParser
    echo -e "${BLUE}→${NC} ShimCacheParser"
    echo "  GitHub: https://github.com/mandiant/ShimCacheParser"
    echo ""
fi

# macOS-specific notes
echo "=========================================="
echo "macOS-Specific Notes"
echo "=========================================="

if [ "$ARCH" = "arm64" ]; then
    echo -e "${GREEN}✓${NC} Running on Apple Silicon (ARM64)"
    echo "  Most forensic tools work natively on ARM64"
    echo "  If you encounter issues, try running with Rosetta 2:"
    echo "    arch -x86_64 brew install <package>"
    echo ""
fi

echo -e "${GREEN}✓${NC} Native APFS support (no apfs-fuse needed)"
echo -e "${GREEN}✓${NC} Native DMG mounting (hdiutil)"
echo -e "${YELLOW}!${NC} libvshadow not available (Linux-only)"
echo ""

# Verify elrond dependencies
if [ "$CHECK_ONLY" = false ]; then
    echo "=========================================="
    echo "Installing elrond Python dependencies"
    echo "=========================================="

    # Check if we're in the elrond directory
    if [ -f "pyproject.toml" ]; then
        echo "Installing elrond in development mode..."
        pip3 install -e .
        echo ""
        echo "Installing macOS-specific requirements..."
        pip3 install -r requirements/macos.txt || pip3 install -r requirements/base.txt
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

# Add reminder about PATH
if [ "$ARCH" = "arm64" ]; then
    echo ""
    echo -e "${YELLOW}Reminder:${NC} Make sure Homebrew is in your PATH"
    echo "Add to ~/.zprofile:"
    echo '  eval "$(/opt/homebrew/bin/brew shellenv)"'
fi
