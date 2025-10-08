"""Centralized configuration management for elrond."""

import os
import platform
from pathlib import Path
from typing import Dict, List, Optional

from elrond.utils.constants import DEFAULT_MOUNT_COUNT


class Settings:
    """Centralized configuration management with platform awareness."""

    def __init__(self):
        """Initialize settings based on current platform."""
        self.platform_name = platform.system().lower()
        self.architecture = platform.machine().lower()

        # Base directories
        self.base_dir = self._get_base_directory()
        self.tools_dir = self.base_dir / "tools"
        self.temp_dir = self._get_temp_directory()
        self.config_dir = self._get_config_directory()

        # Mount points
        self.mount_points = self._generate_mount_points()

        # Ensure directories exist
        self._ensure_directories()

    def _get_base_directory(self) -> Path:
        """
        Get elrond base directory based on platform.

        Returns:
            Path to base directory
        """
        if self.platform_name == "windows":
            # Use PROGRAMFILES or fallback
            program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
            return Path(program_files) / "elrond"
        else:
            # Linux and macOS use /opt/elrond
            return Path("/opt/elrond")

    def _get_temp_directory(self) -> Path:
        """
        Get temporary directory for elrond operations.

        Returns:
            Path to temp directory
        """
        if self.platform_name == "windows":
            temp_base = os.environ.get("TEMP", "C:\\Temp")
            return Path(temp_base) / "elrond"
        else:
            return Path("/tmp/elrond")

    def _get_config_directory(self) -> Path:
        """
        Get configuration directory.

        Returns:
            Path to config directory
        """
        if self.platform_name == "windows":
            appdata = os.environ.get("APPDATA", "C:\\Users\\Public")
            return Path(appdata) / "elrond"
        elif self.platform_name == "darwin":
            # macOS
            home = Path.home()
            return home / "Library" / "Application Support" / "elrond"
        else:
            # Linux
            xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
            return Path(xdg_config) / "elrond"

    def _generate_mount_points(self, count: int = DEFAULT_MOUNT_COUNT) -> Dict[str, List[str]]:
        """
        Generate mount points based on platform.

        Args:
            count: Number of mount points to generate

        Returns:
            Dictionary with 'elrond' and 'ewf' mount point lists
        """
        if self.platform_name == "windows":
            # Use available drive letters (D: through Z:)
            # We'll check which are available at runtime
            all_letters = [f"{chr(i)}:\\" for i in range(ord("D"), ord("Z") + 1)]
            return {"elrond": all_letters[:count], "ewf": all_letters[count : count * 2]}
        else:
            # Linux and macOS use /mnt/ structure
            return {
                "elrond": [f"/mnt/elrond_mount{i:02d}" for i in range(count)],
                "ewf": [f"/mnt/ewf_mount{i:02d}" for i in range(count)],
            }

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [self.temp_dir, self.config_dir]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Log warning but don't fail - we'll handle permissions later
                pass

    def get_available_mount_points(self) -> List[str]:
        """
        Get currently available mount points.

        Returns:
            List of available mount point paths
        """
        if self.platform_name == "windows":
            # Check which drive letters are available
            import string

            used_drives = set()
            for drive in Path("/").iterdir():
                if drive.is_dir() and len(drive.name) == 2 and drive.name[1] == ":":
                    used_drives.add(drive.name[0].upper())

            available = [
                f"{letter}:\\"
                for letter in string.ascii_uppercase
                if letter not in used_drives and ord(letter) >= ord("D")
            ]
            return available
        else:
            # On Unix, return configured mount points
            # Actual availability checked when mounting
            return self.mount_points["elrond"]

    def is_admin(self) -> bool:
        """
        Check if running with administrator/root privileges.

        Returns:
            True if running as admin/root
        """
        if self.platform_name == "windows":
            try:
                import ctypes

                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0

    @property
    def is_arm(self) -> bool:
        """Check if running on ARM architecture."""
        return "aarch" in self.architecture or "arm" in self.architecture

    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.platform_name == "linux"

    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.platform_name == "windows"

    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.platform_name == "darwin"


# Global settings instance
_global_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create global settings instance.

    Returns:
        Settings instance
    """
    global _global_settings
    if _global_settings is None:
        _global_settings = Settings()
    return _global_settings
