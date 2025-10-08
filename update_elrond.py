#!/usr/bin/env python3
"""
elrond Platform-Aware Update Script

Automatically updates elrond and all dependencies based on the host platform.
Replaces the legacy update.sh script with cross-platform support.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Import elrond modules
try:
    from elrond.utils.version_compat import VersionCompatibilityChecker
    from elrond.tools.siem_installer import SIEMInstaller
    from elrond.tools.manager import ToolManager
    from elrond.utils.logger import get_logger
except ImportError:
    # Fallback if running before elrond is installed
    print("WARNING: elrond modules not found. Running in standalone mode.")
    logger = None
    VersionCompatibilityChecker = None
    SIEMInstaller = None
    ToolManager = None


class ElrondUpdater:
    """Platform-aware elrond updater."""

    def __init__(self, verbose: bool = True):
        """Initialize the updater."""
        self.verbose = verbose
        self.platform_system = platform.system().lower()
        self.install_root = Path('/opt/elrond')

        # Detect platform details
        if self.platform_system == 'linux':
            self.package_manager = self._detect_package_manager()
        elif self.platform_system == 'darwin':
            self.package_manager = 'brew'
        elif self.platform_system == 'windows':
            self.package_manager = 'choco'  # or 'winget'
        else:
            self.package_manager = None

    def _detect_package_manager(self) -> str:
        """Detect Linux package manager."""
        if Path('/usr/bin/apt').exists() or Path('/usr/bin/apt-get').exists():
            return 'apt'
        elif Path('/usr/bin/dnf').exists():
            return 'dnf'
        elif Path('/usr/bin/yum').exists():
            return 'yum'
        elif Path('/usr/bin/pacman').exists():
            return 'pacman'
        else:
            return 'unknown'

    def _run_command(
        self,
        cmd: List[str],
        check: bool = True,
        capture_output: bool = False
    ) -> Tuple[bool, str]:
        """
        Run a shell command.

        Args:
            cmd: Command as list of arguments
            check: Raise exception on error
            capture_output: Capture stdout/stderr

        Returns:
            Tuple of (success, output)
        """
        try:
            if self.verbose and not capture_output:
                print(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True
            )

            if capture_output:
                return True, result.stdout
            return True, ""

        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(f"Command failed: {e}")
            return False, str(e)

    def update_system_packages(self) -> bool:
        """Update system package manager."""
        print("\n" + "="*70)
        print("STEP 1: Updating System Packages")
        print("="*70)

        if self.platform_system == 'linux':
            if self.package_manager == 'apt':
                success, _ = self._run_command(['sudo', 'apt', 'update'])
                if success:
                    self._run_command(['sudo', 'apt', 'upgrade', '-y'])
                return success
            elif self.package_manager in ['dnf', 'yum']:
                return self._run_command(['sudo', self.package_manager, 'update', '-y'])[0]
            elif self.package_manager == 'pacman':
                return self._run_command(['sudo', 'pacman', '-Syu', '--noconfirm'])[0]

        elif self.platform_system == 'darwin':
            success, _ = self._run_command(['brew', 'update'])
            if success:
                self._run_command(['brew', 'upgrade'])
            return success

        elif self.platform_system == 'windows':
            # Try chocolatey or winget
            if Path('C:\\ProgramData\\chocolatey\\bin\\choco.exe').exists():
                return self._run_command(['choco', 'upgrade', 'all', '-y'])[0]
            else:
                print("  No package manager found (Chocolatey recommended)")
                return True  # Don't fail if no package manager

        return False

    def update_elrond_repo(self) -> bool:
        """Update elrond repository from GitHub."""
        print("\n" + "="*70)
        print("STEP 2: Updating elrond Repository")
        print("="*70)

        if not self.install_root.exists():
            print(f"  elrond not found at {self.install_root}")
            print("  Cloning from GitHub...")
            success, _ = self._run_command([
                'sudo' if self.platform_system != 'windows' else '',
                'git', 'clone',
                'https://github.com/cyberg3cko/elrond.git',
                str(self.install_root)
            ])
            return success

        # Pull latest changes
        os.chdir(self.install_root)
        success, _ = self._run_command(['git', 'fetch', '--all'])
        if success:
            success, _ = self._run_command(['git', 'pull', 'origin', 'main'])

        return success

    def update_python_dependencies(self) -> bool:
        """Update Python dependencies."""
        print("\n" + "="*70)
        print("STEP 3: Updating Python Dependencies")
        print("="*70)

        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )

        if not in_venv:
            print("  WARNING: Not in a virtual environment")
            print("  Recommended: Create venv and install there")

        pyproject = self.install_root / 'pyproject.toml'
        if pyproject.exists():
            # Install in editable mode with all extras
            success, _ = self._run_command([
                sys.executable, '-m', 'pip', 'install', '-e',
                f"{self.install_root}[all]", '--upgrade'
            ])
            return success
        else:
            print("  No pyproject.toml found, skipping Python deps")
            return True

    def update_forensic_tools(self) -> bool:
        """Update forensic tools from package manager."""
        print("\n" + "="*70)
        print("STEP 4: Updating Forensic Tools")
        print("="*70)

        tools = []

        if self.platform_system == 'linux':
            if self.package_manager == 'apt':
                tools = [
                    'ewf-tools', 'yara', 'clamav', 'clamav-daemon',
                    'sleuthkit', 'qemu-utils', 'volatility3',
                    'libguestfs-tools', 'mlocate'
                ]
                success, _ = self._run_command([
                    'sudo', 'apt', 'install', '-y', *tools
                ])
                return success

        elif self.platform_system == 'darwin':
            tools = [
                'libewf', 'yara', 'clamav', 'sleuthkit',
                'qemu', 'volatility'
            ]
            success, _ = self._run_command([
                'brew', 'install', *tools
            ])
            return success

        return True

    def update_siem_tools(self) -> bool:
        """Update SIEM tools if installed."""
        print("\n" + "="*70)
        print("STEP 5: Checking SIEM Tools")
        print("="*70)

        if not VersionCompatibilityChecker or not SIEMInstaller:
            print("  Skipping (elrond modules not available)")
            return True

        checker = VersionCompatibilityChecker()
        installer = SIEMInstaller()

        # Check each SIEM tool
        for tool in ['splunk', 'elasticsearch', 'kibana']:
            print(f"\n  Checking {tool}...")

            version = checker.get_tool_version(tool)
            if not version:
                print(f"    {tool} not installed, skipping")
                continue

            # Check compatibility
            is_compat, reason = checker.is_version_compatible(tool, version)
            print(f"    Installed: {version}")
            print(f"    Compatible: {is_compat} - {reason}")

            if not is_compat:
                print(f"    Incompatible version detected!")
                response = input(f"    Update {tool} to compatible version? [y/N]: ").strip().lower()
                if response in ['y', 'yes']:
                    success, msg = installer.install_siem_tool(tool, force=True)
                    if success:
                        print(f"    ✓ {msg}")
                    else:
                        print(f"    ✗ {msg}")

        # Check Elasticsearch/Kibana version match
        if checker.get_tool_version('elasticsearch') and checker.get_tool_version('kibana'):
            match, msg = checker.check_elasticsearch_kibana_match()
            print(f"\n  Elasticsearch/Kibana version match: {match}")
            print(f"  {msg}")

        return True

    def update_git_repos(self) -> bool:
        """Update additional Git repositories."""
        print("\n" + "="*70)
        print("STEP 6: Updating Additional Repositories")
        print("="*70)

        repos = {
            'USN-Journal-Parser': 'https://github.com/PoorBillionaire/USN-Journal-Parser.git',
            'KStrike': 'https://github.com/cyberg3cko/KStrike.git',
            'plaso': 'https://github.com/log2timeline/plaso.git',
            'etl-parser': 'https://github.com/cyberg3cko/etl-parser',
            'gandalf': 'https://github.com/cyberg3cko/gandalf.git',
            'sigma': 'https://github.com/SigmaHQ/sigma.git',
            'DeepBlueCLI': 'https://github.com/sans-blue-team/DeepBlueCLI.git',
            'KAPE': 'https://github.com/EricZimmerman/KapeFiles.git',
            'attack-navigator': 'https://github.com/mitre-attack/attack-navigator.git',
        }

        opt_dir = Path('/opt')
        if not opt_dir.exists():
            opt_dir = Path.home() / 'opt'
            opt_dir.mkdir(exist_ok=True)

        for repo_name, repo_url in repos.items():
            repo_path = opt_dir / repo_name
            print(f"\n  {repo_name}...")

            if repo_path.exists():
                # Update existing repo
                try:
                    os.chdir(repo_path)
                    subprocess.run(['git', 'pull'], capture_output=True, timeout=30)
                    print(f"    ✓ Updated")
                except Exception as e:
                    print(f"    ✗ Update failed: {e}")
            else:
                # Clone new repo
                try:
                    if self.platform_system == 'windows':
                        subprocess.run(
                            ['git', 'clone', repo_url, str(repo_path)],
                            capture_output=True,
                            timeout=120
                        )
                    else:
                        subprocess.run(
                            ['sudo', 'git', 'clone', repo_url, str(repo_path)],
                            capture_output=True,
                            timeout=120
                        )
                    print(f"    ✓ Cloned")
                except Exception as e:
                    print(f"    ✗ Clone failed: {e}")

        return True

    def update_clamav_signatures(self) -> bool:
        """Update ClamAV virus signatures."""
        print("\n" + "="*70)
        print("STEP 7: Updating ClamAV Signatures")
        print("="*70)

        if self.platform_system == 'linux':
            # Stop freshclam service
            self._run_command(['sudo', 'systemctl', 'stop', 'clamav-freshclam'], check=False)
            # Update signatures
            success, _ = self._run_command(['sudo', 'freshclam'])
            # Restart service
            self._run_command(['sudo', 'systemctl', 'start', 'clamav-freshclam'], check=False)
            return success

        elif self.platform_system == 'darwin':
            return self._run_command(['freshclam'])[0]

        return True

    def set_permissions(self) -> bool:
        """Set correct permissions on elrond directory."""
        print("\n" + "="*70)
        print("STEP 8: Setting Permissions")
        print("="*70)

        if self.platform_system == 'windows':
            print("  Skipping (Windows)")
            return True

        if not self.install_root.exists():
            print(f"  {self.install_root} not found")
            return False

        # Get current user
        import pwd
        current_user = pwd.getpwuid(os.getuid()).pw_name

        # Set ownership
        success, _ = self._run_command([
            'sudo', 'chown', '-R', f'{current_user}:{current_user}',
            str(self.install_root)
        ])

        # Set permissions
        if success:
            self._run_command([
                'sudo', 'chmod', '-R', '755', str(self.install_root)
            ])

        # Make main script executable
        main_script = self.install_root / 'elrond' / 'elrond.py'
        if main_script.exists():
            self._run_command(['chmod', '+x', str(main_script)])

        return success

    def update_all(self) -> bool:
        """Run all update steps."""
        print("\n" + "🚀 " + "="*65)
        print("elrond Platform-Aware Update")
        print("="*68 + " 🚀")
        print(f"\nPlatform: {self.platform_system}")
        print(f"Package Manager: {self.package_manager}")
        print(f"Install Root: {self.install_root}\n")

        steps = [
            ("System Packages", self.update_system_packages),
            ("elrond Repository", self.update_elrond_repo),
            ("Python Dependencies", self.update_python_dependencies),
            ("Forensic Tools", self.update_forensic_tools),
            ("SIEM Tools", self.update_siem_tools),
            ("Additional Repositories", self.update_git_repos),
            ("ClamAV Signatures", self.update_clamav_signatures),
            ("Permissions", self.set_permissions),
        ]

        failed_steps = []
        for step_name, step_func in steps:
            try:
                success = step_func()
                if not success:
                    failed_steps.append(step_name)
                    print(f"\n  ⚠️  {step_name} update failed")
            except KeyboardInterrupt:
                print("\n\n  Update interrupted by user")
                return False
            except Exception as e:
                failed_steps.append(step_name)
                print(f"\n  ✗ {step_name} update error: {e}")

        # Summary
        print("\n" + "="*70)
        print("UPDATE SUMMARY")
        print("="*70)

        if failed_steps:
            print(f"\n  ⚠️  {len(failed_steps)} step(s) failed:")
            for step in failed_steps:
                print(f"    - {step}")
            print("\n  Some updates may not have completed successfully.")
            return False
        else:
            print("\n  ✓ All updates completed successfully!")
            print("\n  Recommended: Restart your system to apply all changes.")
            return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Update elrond and all dependencies (platform-aware)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress verbose output'
    )
    parser.add_argument(
        '--skip-siem',
        action='store_true',
        help='Skip SIEM tool updates'
    )
    parser.add_argument(
        '--skip-repos',
        action='store_true',
        help='Skip additional repository updates'
    )

    args = parser.parse_args()

    updater = ElrondUpdater(verbose=not args.quiet)

    # Run update
    success = updater.update_all()

    if success:
        print("\n  🎉 Update complete! Enjoy the latest elrond.\n")
        sys.exit(0)
    else:
        print("\n  ⚠️  Update completed with errors. Check output above.\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
