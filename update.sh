#!/bin/bash
#
# elrond Update Script (Legacy Wrapper)
#
# This script now calls the platform-aware Python updater.
# The old bash-based update script has been replaced with a
# cross-platform Python implementation that works on Linux,
# macOS, and Windows.
#
# For advanced options, run: python3 update_elrond.py --help
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "========================================================================"
echo "  elrond Update Script"
echo "========================================================================"
echo ""
echo "  This script will update elrond and all dependencies."
echo "  Platform: $(uname -s)"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not found."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Run the Python updater
echo "  Starting platform-aware update..."
echo ""

python3 "$SCRIPT_DIR/update_elrond.py"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "  ✓ Update Complete!"
    echo "========================================================================"
    echo ""
    echo "  Recommended next steps:"
    echo "    1. Restart your terminal or run: source ~/.bashrc"
    echo "    2. Verify installation: elrond --version"
    echo "    3. Check dependencies: elrond --check-dependencies"
    echo ""
else
    echo ""
    echo "========================================================================"
    echo "  ⚠  Update completed with errors"
    echo "========================================================================"
    echo ""
    echo "  Some components may not have updated successfully."
    echo "  Please check the output above for details."
    echo ""
fi

exit $exit_code
