"""
macOS-specific utility functions for elrond.

Provides macOS-specific functionality including:
- Keychain access and export
- Unified Logging (log command) access
- Property List (plist) parsing
- macOS artifact collection
- System information gathering
- Code signing verification
"""

import os
import plistlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from elrond.utils.exceptions import ElrondError
from elrond.utils.logging import get_logger


class MacOSUtilityError(ElrondError):
    """Raised when macOS utility operation fails."""
    pass


class MacOSKeychainHelper:
    """Helper for macOS Keychain operations."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.macos.keychain")

    def export_keychain(self, keychain_path: Path, output_file: Path, password: Optional[str] = None) -> bool:
        """
        Export keychain to file.

        Args:
            keychain_path: Path to keychain file
            output_file: Path to output file
            password: Keychain password (if locked)

        Returns:
            True if successful

        Note:
            Requires user authorization for keychain access.
        """
        try:
            cmd = ["security", "export", str(keychain_path), "-o", str(output_file)]

            if password:
                cmd.extend(["-p", password])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"Keychain export failed: {result.stderr}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to export keychain: {e}")
            return False

    def list_keychains(self) -> List[Path]:
        """
        List all accessible keychains.

        Returns:
            List of keychain paths
        """
        try:
            result = subprocess.run(
                ["security", "list-keychains"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return []

            # Parse output (format: "path" "path")
            keychains = []
            for line in result.stdout.split('\n'):
                line = line.strip().strip('"')
                if line and Path(line).exists():
                    keychains.append(Path(line))

            return keychains

        except Exception as e:
            self.logger.error(f"Failed to list keychains: {e}")
            return []

    def dump_keychain_info(self, keychain_path: Path) -> Dict[str, Any]:
        """
        Get information about a keychain.

        Args:
            keychain_path: Path to keychain file

        Returns:
            Dictionary with keychain information
        """
        info = {
            "path": str(keychain_path),
            "exists": keychain_path.exists(),
            "size": keychain_path.stat().st_size if keychain_path.exists() else 0,
        }

        try:
            # Get keychain info
            result = subprocess.run(
                ["security", "show-keychain-info", str(keychain_path)],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                info["keychain_info"] = result.stdout

        except Exception as e:
            self.logger.debug(f"Could not get keychain info: {e}")

        return info


class MacOSUnifiedLogHelper:
    """Helper for macOS Unified Logging system."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.macos.unifiedlog")

    def collect_logs(
        self,
        output_file: Path,
        predicate: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        process: Optional[str] = None,
        subsystem: Optional[str] = None
    ) -> bool:
        """
        Collect unified logs using macOS 'log' command.

        Args:
            output_file: Path to output file
            predicate: NSPredicate-style filter
            start_time: Start time for log collection
            end_time: End time for log collection
            process: Filter by process name
            subsystem: Filter by subsystem

        Returns:
            True if successful
        """
        try:
            cmd = ["log", "collect", "--output", str(output_file)]

            # Add time range
            if start_time:
                start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                cmd.extend(["--start", start_str])

            if end_time:
                end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
                cmd.extend(["--end", end_str])

            # Add filters
            if predicate:
                cmd.extend(["--predicate", predicate])

            if process:
                cmd.extend(["--process", process])

            if subsystem:
                cmd.extend(["--subsystem", subsystem])

            self.logger.info(f"Collecting unified logs: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"Log collection failed: {result.stderr}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to collect logs: {e}")
            return False

    def show_logs(
        self,
        predicate: Optional[str] = None,
        last: Optional[str] = "1h",
        style: str = "syslog"
    ) -> str:
        """
        Show unified logs.

        Args:
            predicate: NSPredicate-style filter
            last: Time period (e.g., "1h", "1d", "1w")
            style: Output style (syslog, json, compact)

        Returns:
            Log output as string
        """
        try:
            cmd = ["log", "show"]

            if last:
                cmd.extend(["--last", last])

            if predicate:
                cmd.extend(["--predicate", predicate])

            if style:
                cmd.extend(["--style", style])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )

            if result.returncode == 0:
                return result.stdout

            return ""

        except Exception as e:
            self.logger.error(f"Failed to show logs: {e}")
            return ""


class MacOSPlistHelper:
    """Helper for Property List (plist) operations."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.macos.plist")

    def read_plist(self, plist_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read and parse a plist file.

        Supports both XML and binary plists.

        Args:
            plist_path: Path to plist file

        Returns:
            Dictionary with plist contents or None if failed
        """
        if not plist_path.exists():
            self.logger.error(f"Plist file not found: {plist_path}")
            return None

        try:
            # Try reading with plistlib (handles both XML and binary)
            with open(plist_path, 'rb') as f:
                return plistlib.load(f)

        except Exception as e:
            self.logger.error(f"Failed to read plist {plist_path}: {e}")

            # Try using plutil as fallback
            try:
                result = subprocess.run(
                    ["plutil", "-convert", "xml1", "-o", "-", str(plist_path)],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    return plistlib.loads(result.stdout.encode())

            except Exception as e2:
                self.logger.error(f"plutil fallback also failed: {e2}")

            return None

    def convert_plist(self, plist_path: Path, output_path: Path, format: str = "xml1") -> bool:
        """
        Convert plist to different format.

        Args:
            plist_path: Path to input plist
            output_path: Path to output file
            format: Output format (xml1, binary1, json)

        Returns:
            True if successful
        """
        try:
            cmd = [
                "plutil",
                "-convert", format,
                "-o", str(output_path),
                str(plist_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Failed to convert plist: {e}")
            return False

    def extract_plist_value(self, plist_path: Path, key_path: str) -> Optional[Any]:
        """
        Extract specific value from plist using key path.

        Args:
            plist_path: Path to plist file
            key_path: Key path (e.g., "CFBundleVersion" or "Dict.SubDict.Key")

        Returns:
            Value at key path or None
        """
        plist_data = self.read_plist(plist_path)

        if not plist_data:
            return None

        # Navigate key path
        keys = key_path.split('.')
        current = plist_data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current


class MacOSArtifactCollector:
    """Collect macOS-specific forensic artifacts."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.macos.artifacts")

    def collect_user_artifacts(self, mount_point: Path, user: str, output_dir: Path) -> Dict[str, Path]:
        """
        Collect artifacts for a specific user.

        Args:
            mount_point: Mount point of macOS volume
            user: Username
            output_dir: Output directory for artifacts

        Returns:
            Dictionary mapping artifact type to output path
        """
        user_dir = mount_point / "Users" / user
        artifacts = {}

        if not user_dir.exists():
            self.logger.warning(f"User directory not found: {user_dir}")
            return artifacts

        # Create output directory
        user_output = output_dir / user
        user_output.mkdir(parents=True, exist_ok=True)

        # Collect various artifacts
        artifact_map = {
            "bash_history": ".bash_history",
            "zsh_history": ".zsh_history",
            "ssh_known_hosts": ".ssh/known_hosts",
            "ssh_config": ".ssh/config",
            "downloads_plist": "Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2",
            "recent_items": "Library/Application Support/com.apple.sharedfilelist/RecentApplications.sfl2",
            "safari_history": "Library/Safari/History.db",
            "chrome_history": "Library/Application Support/Google/Chrome/Default/History",
            "firefox_places": "Library/Application Support/Firefox/Profiles/*/places.sqlite",
        }

        for artifact_name, artifact_path in artifact_map.items():
            source = user_dir / artifact_path

            if source.exists():
                dest = user_output / artifact_name
                try:
                    if source.is_file():
                        import shutil
                        shutil.copy2(source, dest)
                        artifacts[artifact_name] = dest
                        self.logger.info(f"Collected {artifact_name}")
                except Exception as e:
                    self.logger.error(f"Failed to collect {artifact_name}: {e}")

        return artifacts

    def collect_system_artifacts(self, mount_point: Path, output_dir: Path) -> Dict[str, Path]:
        """
        Collect system-wide artifacts.

        Args:
            mount_point: Mount point of macOS volume
            output_dir: Output directory

        Returns:
            Dictionary mapping artifact type to output path
        """
        artifacts = {}

        system_artifacts = {
            "system_log": "var/log/system.log",
            "install_log": "var/log/install.log",
            "wifi_log": "var/log/wifi.log",
            "fsck_hfs_log": "var/log/fsck_hfs.log",
            "launchd_log": "var/log/com.apple.launchd.log",
            "system_version": "System/Library/CoreServices/SystemVersion.plist",
            "preference_panes": "Library/PreferencePanes",
            "launch_agents": "Library/LaunchAgents",
            "launch_daemons": "Library/LaunchDaemons",
        }

        for artifact_name, artifact_path in system_artifacts.items():
            source = mount_point / artifact_path

            if source.exists():
                dest = output_dir / artifact_name
                try:
                    if source.is_file():
                        import shutil
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        artifacts[artifact_name] = dest
                except Exception as e:
                    self.logger.error(f"Failed to collect {artifact_name}: {e}")

        return artifacts


class MacOSSystemInfo:
    """Get macOS system information."""

    @staticmethod
    def get_system_version() -> Dict[str, str]:
        """
        Get macOS version information.

        Returns:
            Dictionary with version details
        """
        info = {}

        try:
            # Get product version
            result = subprocess.run(
                ["sw_vers", "-productVersion"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                info["version"] = result.stdout.strip()

            # Get product name
            result = subprocess.run(
                ["sw_vers", "-productName"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                info["product_name"] = result.stdout.strip()

            # Get build version
            result = subprocess.run(
                ["sw_vers", "-buildVersion"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                info["build"] = result.stdout.strip()

        except Exception:
            pass

        return info

    @staticmethod
    def get_hardware_info() -> Dict[str, str]:
        """
        Get hardware information.

        Returns:
            Dictionary with hardware details
        """
        info = {}

        try:
            # Get model identifier
            result = subprocess.run(
                ["sysctl", "-n", "hw.model"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                info["model"] = result.stdout.strip()

            # Get CPU info
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                info["cpu"] = result.stdout.strip()

            # Get memory size
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                mem_bytes = int(result.stdout.strip())
                info["memory_gb"] = f"{mem_bytes / (1024**3):.2f} GB"

        except Exception:
            pass

        return info

    @staticmethod
    def is_apple_silicon() -> bool:
        """
        Check if running on Apple Silicon (ARM64).

        Returns:
            True if Apple Silicon
        """
        try:
            result = subprocess.run(
                ["uname", "-m"],
                capture_output=True,
                text=True,
                check=False
            )
            return "arm64" in result.stdout.lower()
        except Exception:
            return False


class MacOSCodeSignHelper:
    """Helper for code signing verification."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.macos.codesign")

    def verify_signature(self, app_path: Path) -> Dict[str, Any]:
        """
        Verify code signature of an application.

        Args:
            app_path: Path to application bundle

        Returns:
            Dictionary with verification results
        """
        info = {
            "path": str(app_path),
            "signed": False,
            "valid": False,
        }

        try:
            # Check signature
            result = subprocess.run(
                ["codesign", "--verify", "--verbose", str(app_path)],
                capture_output=True,
                text=True,
                check=False
            )

            info["signed"] = result.returncode == 0
            info["verify_output"] = result.stderr  # codesign outputs to stderr

            # Get signature details
            result = subprocess.run(
                ["codesign", "-dv", str(app_path)],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                info["signature_details"] = result.stderr

        except Exception as e:
            self.logger.error(f"Failed to verify signature: {e}")

        return info


# Convenience functions

def is_macos() -> bool:
    """Check if running on macOS."""
    return os.uname().sysname == 'Darwin'


def get_macos_version() -> str:
    """
    Get macOS version string.

    Returns:
        Version string (e.g., "14.2.1")
    """
    info = MacOSSystemInfo.get_system_version()
    return info.get("version", "Unknown")


def is_sip_enabled() -> bool:
    """
    Check if System Integrity Protection (SIP) is enabled.

    Returns:
        True if SIP is enabled
    """
    try:
        result = subprocess.run(
            ["csrutil", "status"],
            capture_output=True,
            text=True,
            check=False
        )
        return "enabled" in result.stdout.lower()
    except Exception:
        return True  # Assume enabled if can't check


def get_current_user_home() -> Path:
    """
    Get current user's home directory.

    Returns:
        Path to home directory
    """
    return Path.home()


def get_applications_dir() -> Path:
    """
    Get Applications directory.

    Returns:
        Path to /Applications
    """
    return Path("/Applications")


def get_library_dir() -> Path:
    """
    Get Library directory.

    Returns:
        Path to /Library
    """
    return Path("/Library")
