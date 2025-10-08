"""
Automated tool installation for elrond.

Provides platform-specific installation of all forensic tools required by elrond.
Supports Linux (apt/yum), macOS (Homebrew), and Windows (WSL2 recommended).
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from elrond.utils.exceptions import ElrondError, PlatformNotSupportedError
from elrond.utils.logging import get_logger
from elrond.tools.manager import ToolManager


class InstallationError(ElrondError):
    """Raised when tool installation fails."""
    pass


class ToolInstaller:
    """
    Automated installation of forensic tools across platforms.

    Supports:
    - Linux: apt-get, yum, pip3
    - macOS: Homebrew, pip3
    - Windows: WSL2 setup + Ubuntu installation (recommended)
    - Windows: Native installation (limited, Python tools only)
    """

    def __init__(self, interactive: bool = False, dry_run: bool = False):
        """
        Initialize tool installer.

        Args:
            interactive: Prompt before installing each tool
            dry_run: Show what would be installed without actually installing
        """
        self.logger = get_logger("elrond.installer")
        self.interactive = interactive
        self.dry_run = dry_run
        self.tool_manager = ToolManager()

        # Detect platform
        self.platform_name = platform.system().lower()
        self.is_wsl = self._detect_wsl()
        self.is_arm64 = platform.machine().lower() in ('arm64', 'aarch64')

        # Track installation results
        self.installed: List[str] = []
        self.failed: List[str] = []
        self.skipped: List[str] = []

        self.logger.info(f"Platform: {self.platform_name}")
        if self.is_wsl:
            self.logger.info("Running in WSL2")
        if self.is_arm64:
            self.logger.info("ARM64 architecture detected")

    def _detect_wsl(self) -> bool:
        """Detect if running in Windows Subsystem for Linux."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except FileNotFoundError:
            return False

    def _has_command(self, command: str) -> bool:
        """Check if a command is available on the system."""
        try:
            result = subprocess.run(
                ['which', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _run_command(self, command: List[str], description: str,
                     check: bool = True, sudo: bool = False) -> Tuple[bool, str]:
        """
        Run a shell command.

        Args:
            command: Command and arguments as list
            description: Human-readable description for logging
            check: Raise exception on failure
            sudo: Use sudo for command

        Returns:
            Tuple of (success, output)
        """
        if sudo and os.geteuid() != 0:
            command = ['sudo'] + command

        self.logger.info(f"{description}...")

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would run: {' '.join(command)}")
            return True, "DRY RUN"

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=check,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                self.logger.debug(f"✓ {description} succeeded")
                return True, result.stdout
            else:
                self.logger.warning(f"✗ {description} failed: {result.stderr}")
                return False, result.stderr

        except subprocess.CalledProcessError as e:
            self.logger.error(f"✗ {description} failed: {e.stderr}")
            if check:
                raise InstallationError(f"{description} failed: {e.stderr}")
            return False, str(e.stderr)
        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ {description} timed out")
            return False, "Command timed out"

    def check_prerequisites(self) -> bool:
        """
        Check system prerequisites (package managers, Python, etc.).

        Returns:
            True if all prerequisites met
        """
        self.logger.info("Checking prerequisites...")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            self.logger.error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False

        self.logger.info(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

        # Check package manager
        if self.platform_name == 'linux':
            if self._has_command('apt-get'):
                self.package_manager = 'apt'
                self.logger.info("✓ Package manager: apt")
            elif self._has_command('yum'):
                self.package_manager = 'yum'
                self.logger.info("✓ Package manager: yum")
            else:
                self.logger.error("Neither apt-get nor yum found")
                return False

        elif self.platform_name == 'darwin':
            if not self._has_command('brew'):
                self.logger.error("Homebrew not installed")
                self.logger.info("Install from: https://brew.sh")
                return False
            self.package_manager = 'brew'
            self.logger.info("✓ Package manager: Homebrew")

        elif self.platform_name == 'windows':
            self.logger.error("Native Windows installation not yet supported")
            self.logger.info("Please use WSL2: elrond --install --wsl")
            return False

        # Check pip
        if not self._has_command('pip3'):
            self.logger.warning("pip3 not found, will try to install Python packages with pip")
        else:
            self.logger.info("✓ pip3 available")

        return True

    def install_system_tools(self, required_only: bool = False) -> Dict[str, bool]:
        """
        Install system-level forensic tools.

        Args:
            required_only: Only install tools marked as required

        Returns:
            Dict mapping tool name to success status
        """
        results = {}

        # Get tools for this platform
        tools = self.tool_manager.tools

        for tool_id, tool_info in tools.items():
            # Check if tool should be installed on this platform
            platforms = tool_info.get('platforms', [])
            if 'all' not in platforms and self.platform_name not in platforms:
                self.logger.debug(f"Skipping {tool_id} (not for {self.platform_name})")
                self.skipped.append(tool_id)
                continue

            # Skip optional tools if required_only
            is_required = tool_info.get('required', False)
            if required_only and not is_required:
                self.logger.debug(f"Skipping optional tool: {tool_id}")
                self.skipped.append(tool_id)
                continue

            # Check if already installed
            if self.tool_manager.discover_tool(tool_id):
                self.logger.info(f"✓ {tool_info['name']} already installed")
                self.installed.append(tool_id)
                results[tool_id] = True
                continue

            # Interactive prompt
            if self.interactive:
                req_str = "required" if is_required else "optional"
                response = input(f"Install {tool_info['name']} ({req_str})? [Y/n]: ")
                if response.lower() in ('n', 'no'):
                    self.logger.info(f"Skipped {tool_id} (user choice)")
                    self.skipped.append(tool_id)
                    continue

            # Install tool
            success = self._install_tool(tool_id, tool_info)
            results[tool_id] = success

            if success:
                self.installed.append(tool_id)
            else:
                self.failed.append(tool_id)

        return results

    def _install_tool(self, tool_id: str, tool_info: Dict) -> bool:
        """
        Install a single tool.

        Args:
            tool_id: Tool identifier
            tool_info: Tool metadata from config.yaml

        Returns:
            True if installation succeeded
        """
        install_methods = tool_info.get('install_methods', {})
        install_cmd = install_methods.get(self.platform_name)

        if not install_cmd:
            self.logger.warning(f"No installation method for {tool_id} on {self.platform_name}")
            return False

        tool_name = tool_info['name']
        self.logger.info(f"\nInstalling {tool_name}...")
        self.logger.info(f"Method: {install_cmd}")

        # Parse installation command
        if install_cmd.startswith('apt-get'):
            return self._install_apt(install_cmd, tool_name)
        elif install_cmd.startswith('yum'):
            return self._install_yum(install_cmd, tool_name)
        elif install_cmd.startswith('brew'):
            return self._install_brew(install_cmd, tool_name)
        elif install_cmd.startswith('pip'):
            return self._install_pip(install_cmd, tool_name)
        elif install_cmd.startswith('git clone') or 'github.com' in install_cmd:
            self.logger.info(f"Manual installation required: {install_cmd}")
            self.logger.info(f"See: {install_cmd}")
            return False
        elif install_cmd.startswith('Download from'):
            self.logger.info(f"Manual download required: {install_cmd}")
            return False
        else:
            self.logger.warning(f"Unknown installation method: {install_cmd}")
            return False

    def _install_apt(self, command: str, tool_name: str) -> bool:
        """Install via apt-get."""
        # Extract package name
        package = command.split()[-1]  # Last word is usually package name

        cmd = ['apt-get', 'install', '-y', package]
        success, _ = self._run_command(
            cmd,
            f"Installing {tool_name} via apt",
            check=False,
            sudo=True
        )
        return success

    def _install_yum(self, command: str, tool_name: str) -> bool:
        """Install via yum."""
        package = command.split()[-1]

        cmd = ['yum', 'install', '-y', package]
        success, _ = self._run_command(
            cmd,
            f"Installing {tool_name} via yum",
            check=False,
            sudo=True
        )
        return success

    def _install_brew(self, command: str, tool_name: str) -> bool:
        """Install via Homebrew."""
        # Extract formula name
        parts = command.split()
        if 'install' in parts:
            idx = parts.index('install')
            formula = parts[idx + 1] if idx + 1 < len(parts) else None
        else:
            formula = None

        if not formula:
            self.logger.error(f"Could not parse brew command: {command}")
            return False

        cmd = ['brew', 'install', formula]
        success, _ = self._run_command(
            cmd,
            f"Installing {tool_name} via Homebrew",
            check=False,
            sudo=False
        )
        return success

    def _install_pip(self, command: str, tool_name: str) -> bool:
        """Install via pip."""
        # Extract package name
        parts = command.split()
        if 'install' in parts:
            idx = parts.index('install')
            package = parts[idx + 1] if idx + 1 < len(parts) else None
        else:
            package = None

        if not package:
            self.logger.error(f"Could not parse pip command: {command}")
            return False

        # Use pip3 if available, otherwise pip
        pip_cmd = 'pip3' if self._has_command('pip3') else 'pip'

        cmd = [pip_cmd, 'install', package]
        success, _ = self._run_command(
            cmd,
            f"Installing {tool_name} via pip",
            check=False,
            sudo=False
        )
        return success

    def install_all(self, required_only: bool = False) -> bool:
        """
        Install all tools for this platform.

        Args:
            required_only: Only install required tools

        Returns:
            True if all installations succeeded
        """
        self.logger.info("="*60)
        self.logger.info("elrond Forensic Tools Installer")
        self.logger.info("="*60)

        # Check prerequisites
        if not self.check_prerequisites():
            self.logger.error("Prerequisites not met")
            return False

        # Update package manager
        self.logger.info("\nUpdating package manager...")
        if self.package_manager == 'apt':
            self._run_command(['apt-get', 'update'], "Updating apt cache", sudo=True, check=False)
        elif self.package_manager == 'brew':
            self._run_command(['brew', 'update'], "Updating Homebrew", check=False)

        # Install tools
        self.logger.info("\n" + "="*60)
        self.logger.info("Installing forensic tools...")
        self.logger.info("="*60 + "\n")

        results = self.install_system_tools(required_only=required_only)

        # Print summary
        self._print_summary()

        # Verify installations
        self.logger.info("\n" + "="*60)
        self.logger.info("Verifying installations...")
        self.logger.info("="*60 + "\n")

        # Re-check all tools
        from elrond.cli import check_dependencies
        check_dependencies()

        return len(self.failed) == 0

    def _print_summary(self):
        """Print installation summary."""
        self.logger.info("\n" + "="*60)
        self.logger.info("Installation Summary")
        self.logger.info("="*60)

        total = len(self.installed) + len(self.failed) + len(self.skipped)

        self.logger.info(f"\nTotal tools processed: {total}")
        self.logger.info(f"✓ Installed: {len(self.installed)}")
        self.logger.info(f"✗ Failed: {len(self.failed)}")
        self.logger.info(f"⊘ Skipped: {len(self.skipped)}")

        if self.installed:
            self.logger.info(f"\nSuccessfully installed:")
            for tool in self.installed:
                self.logger.info(f"  ✓ {tool}")

        if self.failed:
            self.logger.info(f"\nFailed to install:")
            for tool in self.failed:
                self.logger.info(f"  ✗ {tool}")

        if self.skipped:
            self.logger.info(f"\nSkipped:")
            for tool in self.skipped:
                self.logger.info(f"  ⊘ {tool}")

    @staticmethod
    def install_wsl() -> bool:
        """
        Install WSL2 on Windows and set up Ubuntu.

        This should be called from Windows PowerShell, not from Python.
        The function provides instructions for manual installation.

        Returns:
            False (instructions only, actual installation is manual)
        """
        print("="*60)
        print("WSL2 Installation Instructions for Windows")
        print("="*60)
        print()
        print("elrond works best on Windows with WSL2 (Windows Subsystem for Linux).")
        print()
        print("To install WSL2:")
        print()
        print("1. Open PowerShell as Administrator")
        print("2. Run: wsl --install -d Ubuntu-22.04")
        print("3. Restart your computer when prompted")
        print("4. After restart, open Ubuntu from Start menu")
        print("5. Create a username and password")
        print("6. Run: elrond --install")
        print()
        print("Alternatively, you can install manually:")
        print()
        print("1. Enable WSL:")
        print("   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart")
        print()
        print("2. Enable Virtual Machine Platform:")
        print("   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart")
        print()
        print("3. Restart computer")
        print()
        print("4. Download WSL2 kernel update:")
        print("   https://aka.ms/wsl2kernel")
        print()
        print("5. Set WSL2 as default:")
        print("   wsl --set-default-version 2")
        print()
        print("6. Install Ubuntu 22.04 from Microsoft Store")
        print()
        print("For more information: https://docs.microsoft.com/en-us/windows/wsl/install")
        print()

        return False


def install_tools(interactive: bool = False,
                 dry_run: bool = False,
                 required_only: bool = False,
                 wsl_setup: bool = False) -> bool:
    """
    Main entry point for tool installation.

    Args:
        interactive: Prompt before installing each tool
        dry_run: Show what would be installed without installing
        required_only: Only install required tools
        wsl_setup: Show WSL2 setup instructions (Windows only)

    Returns:
        True if installation succeeded
    """
    if wsl_setup:
        return ToolInstaller.install_wsl()

    installer = ToolInstaller(interactive=interactive, dry_run=dry_run)
    return installer.install_all(required_only=required_only)
