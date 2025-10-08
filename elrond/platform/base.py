"""Abstract base class for platform-specific operations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple


class PlatformAdapter(ABC):
    """Abstract base class for platform-specific operations."""

    @abstractmethod
    def mount_image(
        self, image_path: Path, mount_point: Path, image_type: str = "auto", **kwargs
    ) -> bool:
        """
        Mount a disk image.

        Args:
            image_path: Path to the image file
            mount_point: Path where the image should be mounted
            image_type: Type of image (e01, vmdk, raw, etc.) or 'auto' for detection
            **kwargs: Additional platform-specific options

        Returns:
            True if successful, False otherwise

        Raises:
            MountError: If mounting fails
        """
        pass

    @abstractmethod
    def unmount_image(self, mount_point: Path, force: bool = False) -> bool:
        """
        Unmount a disk image.

        Args:
            mount_point: Path where the image is mounted
            force: Force unmount even if busy

        Returns:
            True if successful, False otherwise

        Raises:
            UnmountError: If unmounting fails
        """
        pass

    @abstractmethod
    def get_mount_points(self) -> List[Path]:
        """
        Get list of available mount points.

        Returns:
            List of mount point paths
        """
        pass

    @abstractmethod
    def is_mounted(self, mount_point: Path) -> bool:
        """
        Check if a mount point is currently in use.

        Args:
            mount_point: Path to check

        Returns:
            True if mounted, False otherwise
        """
        pass

    @abstractmethod
    def check_permissions(self) -> Tuple[bool, str]:
        """
        Check if running with appropriate permissions for forensic operations.

        Returns:
            Tuple of (has_permissions, message)
        """
        pass

    @abstractmethod
    def get_temp_directory(self) -> Path:
        """
        Get platform-specific temporary directory.

        Returns:
            Path to temporary directory
        """
        pass

    @abstractmethod
    def clear_screen(self):
        """Clear the terminal screen."""
        pass

    @abstractmethod
    def identify_image_type(self, image_path: Path) -> str:
        """
        Identify the type of disk image.

        Args:
            image_path: Path to image file

        Returns:
            Image type identifier (e01, vmdk, raw, etc.)
        """
        pass

    @abstractmethod
    def get_image_info(self, image_path: Path) -> dict:
        """
        Get metadata information about an image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image metadata
        """
        pass

    def validate_image_path(self, image_path: Path) -> bool:
        """
        Validate that an image path exists and is accessible.

        Args:
            image_path: Path to validate

        Returns:
            True if valid, False otherwise
        """
        return image_path.exists() and image_path.is_file()

    def get_available_disk_space(self, path: Path) -> int:
        """
        Get available disk space at the given path.

        Args:
            path: Path to check

        Returns:
            Available space in bytes
        """
        import shutil

        stat = shutil.disk_usage(path)
        return stat.free
