"""
Windows platform adapter implementation.

Provides disk image mounting and Windows-specific operations.
Supports multiple mounting methods:
1. Arsenal Image Mounter (recommended, free)
2. Windows native Mount-DiskImage (VHD/VHDX/ISO only)
3. FTK Imager CLI (commercial)
4. Manual mounting with guidance
"""

import os
import re
import string
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from elrond.utils.exceptions import MountError, UnmountError, ElrondError
from elrond.utils.logging import get_logger
from .base import PlatformAdapter


class WindowsAdapter(PlatformAdapter):
    """
    Windows-specific platform operations.

    Supports:
    - Arsenal Image Mounter integration
    - Windows native VHD/VHDX mounting
    - Drive letter management
    - Administrator permission checking
    - Windows path handling (UNC paths, drive letters)
    """

    def __init__(self):
        """Initialize Windows adapter."""
        self.logger = get_logger("elrond.platform.windows")
        self.logger.info("Windows platform adapter initialized")

        # Detect available mounting tools
        self.has_arsenal = self._check_arsenal_image_mounter()
        self.has_powershell = self._check_powershell()

        if self.has_arsenal:
            self.logger.info("Arsenal Image Mounter detected")
        else:
            self.logger.warning("Arsenal Image Mounter not detected - mounting support limited")

        # Track mounted images
        self.mounted_images: Dict[str, Path] = {}

    def _check_arsenal_image_mounter(self) -> bool:
        """Check if Arsenal Image Mounter is installed."""
        try:
            # Check if Arsenal Image Mounter CLI is available
            result = subprocess.run(
                ["aim_cli", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            # Try checking for PowerShell module
            try:
                ps_check = subprocess.run(
                    ["powershell", "-Command", "Get-Module -ListAvailable -Name ArsenalImageMounter"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return "ArsenalImageMounter" in ps_check.stdout
            except FileNotFoundError:
                return False

    def _check_powershell(self) -> bool:
        """Check if PowerShell is available."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "echo 'test'"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def mount_image(
        self,
        image_path: Path,
        mount_point: Path,
        image_type: str = "auto",
        **kwargs
    ) -> bool:
        """
        Mount a disk image on Windows.

        Tries multiple methods in order:
        1. Arsenal Image Mounter (if available)
        2. Windows native Mount-DiskImage (VHD/VHDX/ISO only)
        3. Provides manual mounting guidance

        Args:
            image_path: Path to the image file
            mount_point: Drive letter (e.g., Path('E:\\')) - will auto-assign if needed
            image_type: Type of image (e01, vmdk, vhd, vhdx, raw)
            **kwargs: Additional options
                read_only: Mount as read-only (default: True)

        Returns:
            True if successful

        Raises:
            MountError: If mounting fails
        """
        if not image_path.exists():
            raise MountError(f"Image file not found: {image_path}")

        # Auto-detect image type if needed
        if image_type == "auto":
            image_type = self.identify_image_type(image_path)

        read_only = kwargs.get('read_only', True)

        self.logger.info(f"Mounting {image_type} image: {image_path}")

        # Try Arsenal Image Mounter first
        if self.has_arsenal and image_type in ('e01', 'vmdk', 'raw', 'vhd', 'vhdx'):
            try:
                return self._mount_with_arsenal(image_path, mount_point, read_only)
            except Exception as e:
                self.logger.warning(f"Arsenal Image Mounter failed: {e}")
                # Fall through to try other methods

        # Try Windows native mounting for VHD/VHDX/ISO
        if image_type in ('vhd', 'vhdx', 'iso'):
            try:
                return self._mount_with_powershell(image_path, read_only)
            except Exception as e:
                self.logger.warning(f"PowerShell Mount-DiskImage failed: {e}")

        # If we get here, no mounting method worked
        raise MountError(
            f"Unable to mount {image_type} image on Windows.\n"
            f"Options:\n"
            f"1. Install Arsenal Image Mounter (free): https://arsenalrecon.com/downloads/\n"
            f"2. Use WSL2: wsl elrond -C -c CASE-001 -s /mnt/c/evidence\n"
            f"3. Mount manually and use --reorganise mode\n"
            f"4. For VHD/VHDX, use PowerShell: Mount-DiskImage -ImagePath '{image_path}'"
        )

    def _mount_with_arsenal(self, image_path: Path, mount_point: Path, read_only: bool) -> bool:
        """
        Mount image using Arsenal Image Mounter.

        Args:
            image_path: Path to image
            mount_point: Desired mount point (drive letter)
            read_only: Mount as read-only

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting with Arsenal Image Mounter: {image_path}")

        try:
            # Try CLI first
            cmd = ["aim_cli", "mount", str(image_path)]
            if read_only:
                cmd.append("--readonly")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                # Parse output to find assigned drive letter
                # Arsenal typically outputs: "Mounted as X:"
                match = re.search(r'([A-Z]:)', result.stdout)
                if match:
                    actual_mount = Path(match.group(1))
                    self.mounted_images[str(image_path)] = actual_mount
                    self.logger.info(f"Mounted at {actual_mount}")
                    return True

        except FileNotFoundError:
            pass

        # Try PowerShell module
        if self.has_powershell:
            ps_script = f"""
            Import-Module ArsenalImageMounter
            $device = Mount-AimDisk -ImagePath '{image_path}' -ReadOnly:${str(read_only).lower()}
            $device.DevicePath
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0 and result.stdout.strip():
                # Find the drive letter from the device path
                device_path = result.stdout.strip()
                self.logger.info(f"Arsenal mounted: {device_path}")

                # Device path is like \\?\PhysicalDrive1
                # We need to find which drive letter it's assigned
                # This happens automatically in Windows, scan for new drives
                drive_letter = self._find_new_drive_letter()
                if drive_letter:
                    self.mounted_images[str(image_path)] = drive_letter
                    self.logger.info(f"Accessible at drive {drive_letter}")
                    return True

        raise MountError("Arsenal Image Mounter mounting failed")

    def _mount_with_powershell(self, image_path: Path, read_only: bool) -> bool:
        """
        Mount VHD/VHDX/ISO using Windows native Mount-DiskImage.

        Args:
            image_path: Path to image (VHD/VHDX/ISO only)
            read_only: Mount as read-only

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting with PowerShell Mount-DiskImage: {image_path}")

        access_mode = "ReadOnly" if read_only else "ReadWrite"

        ps_script = f"""
        $img = Mount-DiskImage -ImagePath '{image_path}' -Access {access_mode} -PassThru
        $img | Get-DiskImage | Select-Object -ExpandProperty DevicePath
        """

        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            device_path = result.stdout.strip()
            self.logger.info(f"Mounted: {device_path}")

            # Find the drive letter
            drive_letter = self._find_new_drive_letter()
            if drive_letter:
                self.mounted_images[str(image_path)] = drive_letter
                self.logger.info(f"Accessible at drive {drive_letter}")
                return True

        return False

    def _find_new_drive_letter(self) -> Optional[Path]:
        """
        Find a newly appeared drive letter (after mounting).

        Returns:
            Path to new drive letter or None
        """
        import time
        time.sleep(1)  # Wait for Windows to assign drive letter

        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:\\")
            if drive.exists() and str(drive) not in [str(v) for v in self.mounted_images.values()]:
                return drive

        return None

    def unmount_image(self, mount_point: Path, force: bool = False) -> bool:
        """
        Unmount a disk image on Windows.

        Args:
            mount_point: Drive letter or mount path to unmount
            force: Force unmount if busy

        Returns:
            True if successful

        Raises:
            UnmountError: If unmounting fails
        """
        self.logger.info(f"Unmounting: {mount_point}")

        # Find the image path that was mounted at this point
        image_path = None
        for img_path, mnt_point in self.mounted_images.items():
            if mnt_point == mount_point:
                image_path = img_path
                break

        # Try Arsenal Image Mounter
        if self.has_arsenal:
            try:
                if image_path:
                    # Unmount by image path
                    cmd = ["aim_cli", "unmount", image_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        del self.mounted_images[image_path]
                        self.logger.info(f"Unmounted: {mount_point}")
                        return True
            except Exception as e:
                self.logger.warning(f"Arsenal unmount failed: {e}")

        # Try PowerShell for native mounts
        if self.has_powershell and image_path:
            try:
                ps_script = f"Dismount-DiskImage -ImagePath '{image_path}'"
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    if image_path in self.mounted_images:
                        del self.mounted_images[image_path]
                    self.logger.info(f"Unmounted: {mount_point}")
                    return True
            except Exception as e:
                self.logger.warning(f"PowerShell unmount failed: {e}")

        if force:
            self.logger.warning("Force unmount not implemented on Windows")

        raise UnmountError(f"Failed to unmount {mount_point}")

    def get_mount_points(self) -> List[Path]:
        """
        Get list of available drive letters on Windows.

        Returns:
            List of available drive letter paths
        """
        # Get used drive letters
        used_drives = set()
        for letter in string.ascii_uppercase:
            if Path(f"{letter}:\\").exists():
                used_drives.add(letter)

        # Return available letters starting from D:
        # (C: is usually system, D: often optical, start from E:)
        available = [
            Path(f"{letter}:\\")
            for letter in string.ascii_uppercase
            if letter not in used_drives and ord(letter) >= ord("E")
        ]

        return available

    def is_mounted(self, mount_point: Path) -> bool:
        """
        Check if a drive letter or mount point is in use on Windows.

        Args:
            mount_point: Path to check

        Returns:
            True if mounted/in use
        """
        return mount_point.exists()

    def check_permissions(self) -> Tuple[bool, str]:
        """
        Check if running with Administrator privileges on Windows.

        Returns:
            Tuple of (has_permission, message)
        """
        try:
            import ctypes

            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin:
                return True, "Running with Administrator privileges"
            else:
                return (
                    False,
                    "Administrator privileges required for mounting images.\n"
                    "Please run as Administrator or use WSL2."
                )
        except Exception as e:
            self.logger.error(f"Failed to check permissions: {e}")
            return False, f"Unable to determine permissions: {e}"

    def get_temp_directory(self) -> Path:
        """
        Get Windows temporary directory for elrond.

        Returns:
            Path to temp directory
        """
        temp = os.environ.get("TEMP", os.environ.get("TMP", "C:\\Temp"))
        elrond_temp = Path(temp) / "elrond"
        elrond_temp.mkdir(parents=True, exist_ok=True)
        return elrond_temp

    def clear_screen(self):
        """Clear the terminal screen on Windows."""
        os.system("cls")

    def identify_image_type(self, image_path: Path) -> str:
        """
        Identify image type on Windows by file extension.

        Args:
            image_path: Path to image file

        Returns:
            Image type identifier (e01, vmdk, vhd, vhdx, raw, iso, unknown)
        """
        ext = image_path.suffix.lower()

        type_map = {
            ".e01": "e01",
            ".ex01": "e01",
            ".001": "e01",  # Split E01
            ".vmdk": "vmdk",
            ".dd": "raw",
            ".raw": "raw",
            ".img": "raw",
            ".bin": "raw",
            ".vhd": "vhd",
            ".vhdx": "vhdx",
            ".iso": "iso",
        }

        return type_map.get(ext, "unknown")

    def get_image_info(self, image_path: Path) -> dict:
        """
        Get metadata information about an image on Windows.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image metadata
        """
        info = {
            "path": str(image_path),
            "size": image_path.stat().st_size if image_path.exists() else 0,
            "type": self.identify_image_type(image_path),
            "exists": image_path.exists(),
        }

        # Try to get more info using PowerShell for VHD/VHDX
        image_type = info["type"]
        if image_type in ("vhd", "vhdx") and self.has_powershell:
            try:
                ps_script = f"""
                $img = Get-DiskImage -ImagePath '{image_path}'
                @{{
                    Size = $img.Size
                    Attached = $img.Attached
                    LogicalSectorSize = $img.LogicalSectorSize
                }} | ConvertTo-Json
                """
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    import json
                    ps_info = json.loads(result.stdout)
                    info.update(ps_info)
            except Exception as e:
                self.logger.debug(f"Could not get PowerShell image info: {e}")

        return info

    def cleanup(self):
        """Clean up all mounted images."""
        self.logger.info("Cleaning up Windows mounts...")

        for image_path, mount_point in list(self.mounted_images.items()):
            try:
                self.unmount_image(mount_point)
            except Exception as e:
                self.logger.error(f"Failed to unmount {mount_point}: {e}")

        self.mounted_images.clear()

    @staticmethod
    def normalize_path(path: Path) -> Path:
        """
        Normalize Windows path (handle UNC paths, drive letters, etc.).

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        # Convert forward slashes to backslashes
        path_str = str(path).replace('/', '\\')

        # Handle UNC paths (\\\\server\\share)
        if path_str.startswith('\\\\'):
            return Path(path_str)

        # Handle drive letters
        if len(path_str) >= 2 and path_str[1] == ':':
            return Path(path_str)

        # Resolve to absolute path
        return Path(path_str).resolve()

    @staticmethod
    def is_unc_path(path: Path) -> bool:
        """
        Check if path is a UNC path.

        Args:
            path: Path to check

        Returns:
            True if UNC path
        """
        return str(path).startswith('\\\\')

    def get_available_drive_letter(self) -> Optional[str]:
        """
        Get next available drive letter.

        Returns:
            Drive letter (e.g., 'E') or None if none available
        """
        mount_points = self.get_mount_points()
        if mount_points:
            # Return just the letter from first available
            return str(mount_points[0])[0]
        return None


# Windows-specific utility functions

def check_arsenal_image_mounter_installed() -> bool:
    """
    Check if Arsenal Image Mounter is installed.

    Returns:
        True if installed
    """
    adapter = WindowsAdapter()
    return adapter.has_arsenal


def get_installation_guidance() -> str:
    """
    Get guidance for installing required Windows tools.

    Returns:
        Formatted guidance string
    """
    return """
Windows Forensic Tools Installation Guide
==========================================

For best experience on Windows, install:

1. Arsenal Image Mounter (FREE - Recommended)
   - Download: https://arsenalrecon.com/downloads/
   - Supports: E01, VMDK, VHD, VHDX, raw images
   - Installation: Run installer, reboot
   - Verification: Run 'aim_cli --version' in Command Prompt

2. Eric Zimmerman Tools (FREE)
   - Download: https://ericzimmerman.github.io/
   - Tools: Registry Explorer, Timeline Explorer, etc.
   - Installation: Extract to C:\\Tools\\ZimmermanTools
   - Add to PATH for CLI access

3. Alternative: Use WSL2 (100% tool compatibility)
   - PowerShell (Admin): wsl --install -d Ubuntu-22.04
   - After install: wsl elrond --install
   - Run: wsl elrond -C -c CASE-001 -s /mnt/c/evidence

For VHD/VHDX only (limited):
   - Use built-in PowerShell: Mount-DiskImage -ImagePath 'C:\\image.vhdx'
   - Or run: elrond (will use PowerShell automatically)

Recommended: Use WSL2 for full functionality
"""
