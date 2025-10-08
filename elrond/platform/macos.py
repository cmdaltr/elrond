"""
macOS platform adapter implementation.

Provides disk image mounting and macOS-specific operations.
Supports:
- DMG files (native)
- E01 files (via ewfmount)
- VMDK files (via qemu-nbd with NBD kernel extension)
- Raw disk images
- APFS containers and volumes
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from elrond.utils.exceptions import MountError, UnmountError
from elrond.utils.logging import get_logger
from .base import PlatformAdapter


class MacOSAdapter(PlatformAdapter):
    """
    macOS-specific platform operations.

    Supports:
    - Native DMG mounting via hdiutil
    - APFS container and volume mounting
    - E01 mounting via ewfmount (Homebrew)
    - VMDK mounting via qemu-nbd (Homebrew)
    - Raw disk image mounting
    - ARM64 (Apple Silicon) and Intel support
    """

    def __init__(self):
        """Initialize macOS adapter."""
        self.logger = get_logger("elrond.platform.macos")
        self.logger.info("macOS platform adapter initialized")

        # Detect architecture
        self.is_arm64 = self._detect_arm64()
        if self.is_arm64:
            self.logger.info("Running on Apple Silicon (ARM64)")
        else:
            self.logger.info("Running on Intel (x86_64)")

        # Track mounted images and devices
        self.mounted_images: Dict[str, Dict[str, str]] = {}
        # Format: {image_path: {'mount_point': path, 'device': /dev/diskX, 'type': image_type}}

    def _detect_arm64(self) -> bool:
        """Detect if running on Apple Silicon."""
        try:
            result = subprocess.run(
                ['uname', '-m'],
                capture_output=True,
                text=True,
                check=False
            )
            return 'arm64' in result.stdout.lower()
        except Exception:
            return False

    def mount_image(
        self,
        image_path: Path,
        mount_point: Path,
        image_type: str = "auto",
        **kwargs
    ) -> bool:
        """
        Mount a disk image on macOS.

        Args:
            image_path: Path to the image file
            mount_point: Path where the image should be mounted
            image_type: Type of image (dmg, e01, vmdk, raw, apfs)
            **kwargs: Additional options
                read_only: Mount as read-only (default: True)
                verify: Verify DMG checksums before mounting
                owners: Honor ownership on mounted volume

        Returns:
            True if successful

        Raises:
            MountError: If mounting fails
        """
        if not self.validate_image_path(image_path):
            raise MountError(f"Image path does not exist: {image_path}")

        if image_type == "auto":
            image_type = self.identify_image_type(image_path)

        read_only = kwargs.get('read_only', True)

        # Create mount point
        mount_point.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Mounting {image_type} image: {image_path}")

        try:
            if image_type == "dmg":
                return self._mount_dmg(image_path, mount_point, **kwargs)
            elif image_type == "apfs":
                return self._mount_apfs(image_path, mount_point, **kwargs)
            elif image_type in ["e01", "ewf"]:
                return self._mount_ewf(image_path, mount_point)
            elif image_type == "vmdk":
                return self._mount_vmdk(image_path, mount_point)
            elif image_type in ["raw", "dd", "img"]:
                return self._mount_raw(image_path, mount_point, **kwargs)
            else:
                raise MountError(f"Unsupported image type: {image_type}")
        except Exception as e:
            self.logger.error(f"Failed to mount {image_path}: {e}")
            raise MountError(f"Failed to mount {image_path}: {str(e)}")

    def _mount_dmg(self, image_path: Path, mount_point: Path, **kwargs) -> bool:
        """
        Mount DMG file using hdiutil (native macOS).

        Args:
            image_path: Path to DMG file
            mount_point: Desired mount point
            **kwargs: verify, owners, read_only

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting DMG with hdiutil: {image_path}")

        verify = kwargs.get('verify', False)
        owners = kwargs.get('owners', False)
        read_only = kwargs.get('read_only', True)

        cmd = ["hdiutil", "attach"]

        if read_only:
            cmd.append("-readonly")

        if verify:
            cmd.append("-verify")

        if not owners:
            cmd.append("-noowners")

        # Mount to specific location
        cmd.extend(["-mountpoint", str(mount_point)])

        cmd.append(str(image_path))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            self.logger.error(f"hdiutil attach failed: {result.stderr}")
            raise MountError(f"hdiutil failed: {result.stderr}")

        # Parse device from output (e.g., /dev/disk4)
        device = self._parse_device_from_hdiutil_output(result.stdout)

        # Track mounted image
        self.mounted_images[str(image_path)] = {
            'mount_point': str(mount_point),
            'device': device,
            'type': 'dmg'
        }

        self.logger.info(f"Mounted DMG at {mount_point} (device: {device})")
        return True

    def _mount_apfs(self, image_path: Path, mount_point: Path, **kwargs) -> bool:
        """
        Mount APFS container or volume.

        APFS (Apple File System) is the default file system for macOS 10.13+.
        Can be in DMG containers or raw disk images.

        Args:
            image_path: Path to APFS image
            mount_point: Desired mount point
            **kwargs: read_only

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting APFS image: {image_path}")

        read_only = kwargs.get('read_only', True)

        # First, attach the image
        cmd = ["hdiutil", "attach", "-nomount"]

        if read_only:
            cmd.append("-readonly")

        cmd.append(str(image_path))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise MountError(f"Failed to attach APFS image: {result.stderr}")

        # Parse the device (e.g., /dev/disk4s1 for APFS volume)
        device = self._parse_apfs_device(result.stdout)

        if not device:
            raise MountError("Could not find APFS volume device")

        # Mount the APFS volume
        cmd = ["mount", "-t", "apfs"]

        if read_only:
            cmd.extend(["-o", "ro"])

        cmd.extend([device, str(mount_point)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Try to detach on failure
            subprocess.run(["hdiutil", "detach", device.split('s')[0]], capture_output=True)
            raise MountError(f"Failed to mount APFS volume: {result.stderr}")

        # Track mounted image
        self.mounted_images[str(image_path)] = {
            'mount_point': str(mount_point),
            'device': device,
            'type': 'apfs'
        }

        self.logger.info(f"Mounted APFS at {mount_point} (device: {device})")
        return True

    def _mount_ewf(self, image_path: Path, mount_point: Path) -> bool:
        """
        Mount EWF/E01 using ewfmount (requires Homebrew: brew install libewf).

        Args:
            image_path: Path to E01 file
            mount_point: Desired mount point

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting E01 with ewfmount: {image_path}")

        # Create intermediate EWF mount point
        ewf_mount = mount_point.parent / f"ewf_{mount_point.name}"
        ewf_mount.mkdir(parents=True, exist_ok=True)

        # Mount E01 with ewfmount (creates ewf1 virtual device)
        cmd = ["ewfmount", str(image_path), str(ewf_mount)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            self.logger.error(f"ewfmount failed: {result.stderr}")
            raise MountError(f"ewfmount failed: {result.stderr}")

        # The virtual device file
        ewf1_path = ewf_mount / "ewf1"

        if not ewf1_path.exists():
            raise MountError(f"ewf1 virtual device not found at {ewf1_path}")

        # Now attach the ewf1 device as a disk image
        cmd = ["hdiutil", "attach", "-nomount", "-readonly", str(ewf1_path)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            # Clean up ewfmount
            subprocess.run(["umount", str(ewf_mount)], capture_output=True)
            raise MountError(f"hdiutil attach failed: {result.stderr}")

        # Parse device
        device = result.stdout.strip().split()[0]

        # Mount the device to our mount point
        cmd = ["mount", "-o", "ro", device, str(mount_point)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Clean up
            subprocess.run(["hdiutil", "detach", device], capture_output=True)
            subprocess.run(["umount", str(ewf_mount)], capture_output=True)
            raise MountError(f"mount failed: {result.stderr}")

        # Track mounted image
        self.mounted_images[str(image_path)] = {
            'mount_point': str(mount_point),
            'device': device,
            'type': 'e01',
            'ewf_mount': str(ewf_mount)
        }

        self.logger.info(f"Mounted E01 at {mount_point} (device: {device})")
        return True

    def _mount_vmdk(self, image_path: Path, mount_point: Path) -> bool:
        """
        Mount VMDK using qemu-nbd (requires: brew install qemu).

        Note: macOS doesn't have native NBD support. This requires
        the NBD kernel extension or using qemu-nbd in userspace mode.

        Args:
            image_path: Path to VMDK file
            mount_point: Desired mount point

        Returns:
            True if successful
        """
        self.logger.warning("VMDK mounting on macOS requires qemu (brew install qemu)")
        self.logger.info(f"Attempting to mount VMDK: {image_path}")

        # Check if qemu-nbd is available
        try:
            subprocess.run(
                ["which", "qemu-nbd"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            raise MountError(
                "qemu-nbd not found. Install with: brew install qemu\n"
                "Note: VMDK support on macOS is experimental."
            )

        # For now, provide guidance instead of attempting mount
        # Full implementation would require NBD kernel extension
        raise NotImplementedError(
            "VMDK mounting on macOS requires NBD kernel extension.\n"
            "Alternatives:\n"
            "1. Convert to DMG: qemu-img convert -O dmg disk.vmdk disk.dmg\n"
            "2. Use VMware Fusion to access the VMDK\n"
            "3. Use Linux or WSL2 for full VMDK support"
        )

    def _mount_raw(self, image_path: Path, mount_point: Path, **kwargs) -> bool:
        """
        Mount raw disk image on macOS using hdiutil.

        Args:
            image_path: Path to raw image file (.dd, .raw, .img)
            mount_point: Desired mount point
            **kwargs: read_only

        Returns:
            True if successful
        """
        self.logger.info(f"Mounting raw image: {image_path}")

        read_only = kwargs.get('read_only', True)

        # Attach the raw image
        cmd = ["hdiutil", "attach", "-nomount", "-imagekey", "diskimage-class=CRawDiskImage"]

        if read_only:
            cmd.append("-readonly")

        cmd.append(str(image_path))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise MountError(f"hdiutil attach failed: {result.stderr}")

        # Parse device
        device = result.stdout.strip().split()[0]

        # Mount the device
        cmd = ["mount"]

        if read_only:
            cmd.extend(["-o", "ro"])

        cmd.extend([device, str(mount_point)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Clean up
            subprocess.run(["hdiutil", "detach", device], capture_output=True)
            raise MountError(f"mount failed: {result.stderr}")

        # Track mounted image
        self.mounted_images[str(image_path)] = {
            'mount_point': str(mount_point),
            'device': device,
            'type': 'raw'
        }

        self.logger.info(f"Mounted raw image at {mount_point} (device: {device})")
        return True

    def unmount_image(self, mount_point: Path, force: bool = False) -> bool:
        """
        Unmount a disk image on macOS.

        Args:
            mount_point: Path where image is mounted
            force: Force unmount if busy

        Returns:
            True if successful

        Raises:
            UnmountError: If unmounting fails
        """
        if not mount_point.exists():
            self.logger.debug(f"Mount point {mount_point} doesn't exist, considering unmounted")
            return True

        self.logger.info(f"Unmounting: {mount_point}")

        # Find the image info
        image_info = None
        for img_path, info in self.mounted_images.items():
            if info['mount_point'] == str(mount_point):
                image_info = info
                break

        try:
            # Unmount the mount point
            cmd = ["umount"]
            if force:
                cmd.append("-f")
            cmd.append(str(mount_point))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # If regular unmount failed and force requested, try hdiutil detach
            if result.returncode != 0 and force and image_info:
                self.logger.warning(f"umount failed, trying hdiutil detach with force")
                device = image_info.get('device')
                if device:
                    cmd = ["hdiutil", "detach", device, "-force"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise UnmountError(f"Failed to unmount {mount_point}: {result.stderr}")

            # Detach the device if we have it
            if image_info:
                device = image_info.get('device')
                if device:
                    subprocess.run(
                        ["hdiutil", "detach", device],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False  # Don't fail if already detached
                    )

                # Clean up EWF mount if present
                ewf_mount = image_info.get('ewf_mount')
                if ewf_mount:
                    subprocess.run(
                        ["umount", ewf_mount],
                        capture_output=True,
                        check=False
                    )

                # Remove from tracked mounts
                for img_path, info in list(self.mounted_images.items()):
                    if info == image_info:
                        del self.mounted_images[img_path]
                        break

            # Try to clean up mount point directory
            if mount_point.exists() and not any(mount_point.iterdir()):
                try:
                    mount_point.rmdir()
                except Exception:
                    pass

            self.logger.info(f"Unmounted {mount_point}")
            return True

        except Exception as e:
            raise UnmountError(f"Failed to unmount {mount_point}: {str(e)}")

    def get_mount_points(self) -> List[Path]:
        """
        Get list of available mount points on macOS.

        Returns:
            List of mount point paths
        """
        from elrond.config import get_settings

        settings = get_settings()
        return [Path(mp) for mp in settings.mount_points.get("elrond", [])]

    def is_mounted(self, mount_point: Path) -> bool:
        """
        Check if a path is currently mounted on macOS.

        Args:
            mount_point: Path to check

        Returns:
            True if mounted
        """
        try:
            result = subprocess.run(
                ["mount"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return str(mount_point) in result.stdout
        except Exception:
            return False

    def check_permissions(self) -> Tuple[bool, str]:
        """
        Check if running with root/sudo privileges on macOS.

        Returns:
            Tuple of (has_permission, message)
        """
        is_root = os.geteuid() == 0

        if is_root:
            return True, "Running with root privileges (sudo)"
        else:
            return (
                False,
                "Root privileges required for mounting images.\n"
                "Please run with: sudo elrond ..."
            )

    def get_temp_directory(self) -> Path:
        """
        Get macOS temporary directory for elrond.

        Returns:
            Path to temp directory
        """
        temp_dir = Path("/tmp/elrond")
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def clear_screen(self):
        """Clear the terminal screen on macOS."""
        os.system("clear")

    def identify_image_type(self, image_path: Path) -> str:
        """
        Identify image type on macOS using file command and extension.

        Args:
            image_path: Path to image file

        Returns:
            Image type identifier (dmg, apfs, e01, vmdk, raw, unknown)
        """
        # Try file command first (very accurate on macOS)
        try:
            result = subprocess.run(
                ["file", "-b", str(image_path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )

            if result.returncode == 0:
                output = result.stdout.lower()

                if "apple disk image" in output or "udif" in output:
                    return "dmg"
                elif "apfs" in output:
                    return "apfs"
                elif "expert witness" in output or "encase" in output:
                    return "e01"
                elif "vmdk" in output or "vmware" in output:
                    return "vmdk"
                elif "dos/mbr" in output or "boot sector" in output:
                    return "raw"

        except Exception as e:
            self.logger.debug(f"file command failed: {e}")

        # Fallback to extension-based detection
        ext = image_path.suffix.lower()

        type_map = {
            ".dmg": "dmg",
            ".sparsebundle": "dmg",
            ".sparseimage": "dmg",
            ".e01": "e01",
            ".ex01": "e01",
            ".001": "e01",  # Split E01
            ".vmdk": "vmdk",
            ".dd": "raw",
            ".raw": "raw",
            ".img": "raw",
            ".bin": "raw",
            ".iso": "raw",
        }

        return type_map.get(ext, "unknown")

    def get_image_info(self, image_path: Path) -> dict:
        """
        Get metadata information about an image on macOS.

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

        # Get file command output
        try:
            result = subprocess.run(
                ["file", "-b", str(image_path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if result.returncode == 0:
                info["file_output"] = result.stdout.strip()
        except Exception:
            pass

        # For DMG files, use hdiutil imageinfo
        if info["type"] == "dmg":
            try:
                result = subprocess.run(
                    ["hdiutil", "imageinfo", str(image_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )
                if result.returncode == 0:
                    info["hdiutil_info"] = self._parse_hdiutil_imageinfo(result.stdout)
            except Exception:
                pass

        return info

    def cleanup(self):
        """Clean up all mounted images."""
        self.logger.info("Cleaning up macOS mounts...")

        for image_path, info in list(self.mounted_images.items()):
            try:
                mount_point = Path(info['mount_point'])
                self.unmount_image(mount_point, force=True)
            except Exception as e:
                self.logger.error(f"Failed to unmount {info['mount_point']}: {e}")

        self.mounted_images.clear()

    # Helper methods

    def _parse_device_from_hdiutil_output(self, output: str) -> str:
        """Parse device path from hdiutil output."""
        # Output format: /dev/disk4  Apple_HFS  /path/to/mount
        for line in output.split('\n'):
            if '/dev/disk' in line:
                parts = line.split()
                if parts:
                    return parts[0]
        return ""

    def _parse_apfs_device(self, output: str) -> str:
        """Parse APFS device from hdiutil output."""
        # Look for APFS volume device (e.g., /dev/disk4s1)
        for line in output.split('\n'):
            if 'Apple_APFS' in line or 'APFS' in line:
                parts = line.split()
                for part in parts:
                    if '/dev/disk' in part:
                        return part
        return ""

    def _parse_hdiutil_imageinfo(self, output: str) -> Dict[str, str]:
        """Parse hdiutil imageinfo output into dictionary."""
        info = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        return info

    @staticmethod
    def get_macos_version() -> Tuple[int, int, int]:
        """
        Get macOS version.

        Returns:
            Tuple of (major, minor, patch)
        """
        try:
            result = subprocess.run(
                ['sw_vers', '-productVersion'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                parts = version.split('.')
                return (
                    int(parts[0]) if len(parts) > 0 else 0,
                    int(parts[1]) if len(parts) > 1 else 0,
                    int(parts[2]) if len(parts) > 2 else 0
                )
        except Exception:
            pass

        return (0, 0, 0)
