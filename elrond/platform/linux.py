"""Linux platform adapter implementation."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from elrond.utils.exceptions import MountError, UnmountError
from elrond.utils.logging import get_logger
from .base import PlatformAdapter


class LinuxAdapter(PlatformAdapter):
    """Linux-specific platform operations."""

    def __init__(self):
        """Initialize Linux adapter."""
        self.logger = get_logger("elrond.platform.linux")

    def mount_image(
        self,
        image_path: Path,
        mount_point: Path,
        image_type: str = "auto",
        read_only: bool = True,
        **kwargs,
    ) -> bool:
        """
        Mount a disk image on Linux.

        Args:
            image_path: Path to the image file
            mount_point: Path where the image should be mounted
            image_type: Type of image (e01, vmdk, raw, etc.) or 'auto'
            read_only: Mount as read-only (default True)
            **kwargs: Additional options (e.g., offset, sizelimit)

        Returns:
            True if successful

        Raises:
            MountError: If mounting fails
        """
        if not self.validate_image_path(image_path):
            raise MountError(f"Image path does not exist: {image_path}")

        # Auto-detect image type if needed
        if image_type == "auto":
            image_type = self.identify_image_type(image_path)

        # Create mount point if it doesn't exist
        mount_point.mkdir(parents=True, exist_ok=True)

        try:
            if image_type in ["e01", "ewf"]:
                return self._mount_ewf(image_path, mount_point, read_only)
            elif image_type == "vmdk":
                return self._mount_vmdk(image_path, mount_point, read_only)
            elif image_type in ["raw", "dd", "img"]:
                return self._mount_raw(image_path, mount_point, read_only, **kwargs)
            else:
                raise MountError(f"Unsupported image type: {image_type}")
        except Exception as e:
            raise MountError(f"Failed to mount {image_path}: {str(e)}")

    def _mount_ewf(self, image_path: Path, mount_point: Path, read_only: bool) -> bool:
        """Mount EWF/E01 image using ewfmount."""
        # Create intermediate mount point for ewfmount
        ewf_mount = mount_point.parent / f"ewf_{mount_point.name}"
        ewf_mount.mkdir(parents=True, exist_ok=True)

        # Mount the EWF file
        cmd = ["ewfmount", str(image_path), str(ewf_mount)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            self.logger.error(f"ewfmount failed: {result.stderr}")
            return False

        # Now mount the ewf1 file as a loop device
        ewf1_path = ewf_mount / "ewf1"
        if not ewf1_path.exists():
            self.logger.error(f"ewf1 not found at {ewf1_path}")
            return False

        mount_opts = ["ro"] if read_only else []
        cmd = ["mount", "-o", ",".join(mount_opts)] if mount_opts else ["mount"]
        cmd.extend([str(ewf1_path), str(mount_point)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            self.logger.error(f"mount failed: {result.stderr}")
            return False

        self.logger.debug(f"Mounted EWF image {image_path} at {mount_point}")
        return True

    def _mount_vmdk(self, image_path: Path, mount_point: Path, read_only: bool) -> bool:
        """Mount VMDK image using qemu-nbd."""
        # Find available nbd device
        nbd_device = self._find_available_nbd()
        if not nbd_device:
            raise MountError("No available NBD devices")

        # Connect VMDK to NBD device
        cmd = ["qemu-nbd", "--connect", nbd_device]
        if read_only:
            cmd.append("--read-only")
        cmd.append(str(image_path))

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            self.logger.error(f"qemu-nbd failed: {result.stderr}")
            return False

        # Give device time to initialize
        import time

        time.sleep(2)

        # Mount the device
        mount_opts = ["ro"] if read_only else []
        cmd = ["mount", "-o", ",".join(mount_opts)] if mount_opts else ["mount"]
        cmd.extend([nbd_device + "p1", str(mount_point)])  # Usually first partition

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            self.logger.error(f"mount failed: {result.stderr}")
            # Try to disconnect NBD
            subprocess.run(["qemu-nbd", "--disconnect", nbd_device], capture_output=True)
            return False

        self.logger.debug(f"Mounted VMDK image {image_path} at {mount_point}")
        return True

    def _mount_raw(
        self, image_path: Path, mount_point: Path, read_only: bool, **kwargs
    ) -> bool:
        """Mount raw disk image using loop device."""
        mount_opts = ["ro", "loop"] if read_only else ["loop"]

        # Add offset if provided
        if "offset" in kwargs:
            mount_opts.append(f"offset={kwargs['offset']}")

        # Add sizelimit if provided
        if "sizelimit" in kwargs:
            mount_opts.append(f"sizelimit={kwargs['sizelimit']}")

        cmd = ["mount", "-o", ",".join(mount_opts), str(image_path), str(mount_point)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            self.logger.error(f"mount failed: {result.stderr}")
            return False

        self.logger.debug(f"Mounted raw image {image_path} at {mount_point}")
        return True

    def _find_available_nbd(self) -> Optional[str]:
        """Find an available NBD device."""
        for i in range(16):  # Check /dev/nbd0 through /dev/nbd15
            nbd = f"/dev/nbd{i}"
            if Path(nbd).exists():
                # Check if it's in use
                result = subprocess.run(
                    ["lsblk", nbd], capture_output=True, text=True, timeout=5
                )
                # If lsblk shows nothing, it's available
                if result.returncode != 0 or not result.stdout.strip():
                    return nbd
        return None

    def unmount_image(self, mount_point: Path, force: bool = False) -> bool:
        """
        Unmount a disk image on Linux.

        Args:
            mount_point: Path where the image is mounted
            force: Force unmount even if busy

        Returns:
            True if successful

        Raises:
            UnmountError: If unmounting fails
        """
        if not mount_point.exists():
            return True  # Already unmounted

        try:
            cmd = ["umount"]
            if force:
                cmd.append("-f")
            cmd.append(str(mount_point))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                self.logger.error(f"umount failed: {result.stderr}")
                if not force:
                    # Try lazy unmount as fallback
                    result = subprocess.run(
                        ["umount", "-l", str(mount_point)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode != 0:
                        raise UnmountError(f"Failed to unmount {mount_point}")

            # Clean up mount point directory
            if mount_point.exists() and not any(mount_point.iterdir()):
                try:
                    mount_point.rmdir()
                except:
                    pass  # Don't fail if we can't remove the directory

            self.logger.debug(f"Unmounted {mount_point}")
            return True

        except Exception as e:
            raise UnmountError(f"Failed to unmount {mount_point}: {str(e)}")

    def get_mount_points(self) -> List[Path]:
        """Get list of available mount points on Linux."""
        from elrond.config import get_settings

        settings = get_settings()
        return [Path(mp) for mp in settings.mount_points["elrond"]]

    def is_mounted(self, mount_point: Path) -> bool:
        """Check if a path is a mount point on Linux."""
        result = subprocess.run(
            ["mountpoint", "-q", str(mount_point)], capture_output=True, timeout=5
        )
        return result.returncode == 0

    def check_permissions(self) -> Tuple[bool, str]:
        """Check if running as root on Linux."""
        is_root = os.geteuid() == 0
        if is_root:
            return True, "Running with root privileges"
        else:
            return False, "Root privileges required. Please run with sudo."

    def get_temp_directory(self) -> Path:
        """Get Linux temporary directory."""
        return Path("/tmp/elrond")

    def clear_screen(self):
        """Clear the terminal screen on Linux."""
        os.system("clear")

    def identify_image_type(self, image_path: Path) -> str:
        """
        Identify image type using the 'file' command.

        Args:
            image_path: Path to image file

        Returns:
            Image type identifier
        """
        result = subprocess.run(
            ["file", str(image_path)], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return "unknown"

        output = result.stdout.lower()

        if "expert witness" in output or "encase" in output:
            return "e01"
        elif "vmdk" in output or "vmware" in output:
            return "vmdk"
        elif "dos/mbr boot sector" in output:
            return "raw"
        elif "data" in output or "raw disk" in output:
            return "raw"
        else:
            # Check by extension as fallback
            ext = image_path.suffix.lower()
            if ext in [".e01", ".ex01"]:
                return "e01"
            elif ext == ".vmdk":
                return "vmdk"
            elif ext in [".dd", ".raw", ".img"]:
                return "raw"
            else:
                return "unknown"

    def get_image_info(self, image_path: Path) -> dict:
        """
        Get metadata information about an image on Linux.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image metadata
        """
        info = {
            "path": str(image_path),
            "size": image_path.stat().st_size if image_path.exists() else 0,
            "type": self.identify_image_type(image_path),
        }

        # Get file output
        result = subprocess.run(
            ["file", str(image_path)], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            info["file_output"] = result.stdout.strip()

        # If it's an E01, try to get ewfinfo
        if info["type"] == "e01":
            result = subprocess.run(
                ["ewfinfo", str(image_path)], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["ewf_info"] = result.stdout

        return info
