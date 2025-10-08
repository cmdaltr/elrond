"""
Unit tests for Windows platform adapter.

Note: Some tests require Windows environment to run properly.
Tests are designed to be skipped on non-Windows platforms.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != 'win32',
    reason="Windows-specific tests require Windows platform"
)

from elrond.platform.windows import WindowsAdapter
from elrond.utils.exceptions import MountError, UnmountError


class TestWindowsAdapterInitialization:
    """Test Windows adapter initialization."""

    def test_adapter_creation(self):
        """Test that adapter can be created."""
        adapter = WindowsAdapter()
        assert adapter is not None
        assert adapter.logger is not None
        assert isinstance(adapter.mounted_images, dict)

    def test_arsenal_detection(self):
        """Test Arsenal Image Mounter detection."""
        adapter = WindowsAdapter()
        # Result depends on whether Arsenal is installed
        assert isinstance(adapter.has_arsenal, bool)

    def test_powershell_detection(self):
        """Test PowerShell detection."""
        adapter = WindowsAdapter()
        # PowerShell should be available on Windows
        assert adapter.has_powershell is True


class TestImageTypeIdentification:
    """Test image type identification."""

    def test_e01_identification(self):
        """Test E01 image identification."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("evidence.e01")) == "e01"
        assert adapter.identify_image_type(Path("evidence.E01")) == "e01"
        assert adapter.identify_image_type(Path("evidence.ex01")) == "e01"

    def test_vmdk_identification(self):
        """Test VMDK image identification."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("disk.vmdk")) == "vmdk"

    def test_vhd_identification(self):
        """Test VHD/VHDX identification."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("disk.vhd")) == "vhd"
        assert adapter.identify_image_type(Path("disk.vhdx")) == "vhdx"

    def test_raw_identification(self):
        """Test raw image identification."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("disk.dd")) == "raw"
        assert adapter.identify_image_type(Path("disk.raw")) == "raw"
        assert adapter.identify_image_type(Path("disk.img")) == "raw"

    def test_iso_identification(self):
        """Test ISO image identification."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("disk.iso")) == "iso"

    def test_unknown_identification(self):
        """Test unknown image type."""
        adapter = WindowsAdapter()
        assert adapter.identify_image_type(Path("disk.xyz")) == "unknown"


class TestDriveLetterManagement:
    """Test drive letter management functions."""

    def test_get_mount_points(self):
        """Test getting available mount points."""
        adapter = WindowsAdapter()
        mount_points = adapter.get_mount_points()

        # Should return list of Path objects
        assert isinstance(mount_points, list)

        # All should be drive letters from E: onwards
        for mp in mount_points:
            assert isinstance(mp, Path)
            drive_letter = str(mp)[0]
            assert drive_letter >= 'E'  # Should start from E:
            assert drive_letter <= 'Z'

    def test_is_mounted(self):
        """Test checking if drive is mounted."""
        adapter = WindowsAdapter()

        # C: drive should exist on Windows
        assert adapter.is_mounted(Path("C:\\")) is True

        # Z: drive probably doesn't exist
        # (unless user has many drives)
        # Can't assert False as some systems might have it

    def test_get_available_drive_letter(self):
        """Test getting next available drive letter."""
        adapter = WindowsAdapter()
        letter = adapter.get_available_drive_letter()

        if letter:  # Might be None if no drives available
            assert len(letter) == 1
            assert letter.isalpha()
            assert letter >= 'E'


class TestPathHandling:
    """Test Windows path handling."""

    def test_normalize_path_forward_slash(self):
        """Test normalizing path with forward slashes."""
        result = WindowsAdapter.normalize_path(Path("C:/Users/test"))
        assert '\\' in str(result)
        assert '/' not in str(result)

    def test_normalize_path_backslash(self):
        """Test normalizing path with backslashes."""
        result = WindowsAdapter.normalize_path(Path("C:\\Users\\test"))
        assert '\\' in str(result)

    def test_is_unc_path_true(self):
        """Test UNC path detection (positive)."""
        assert WindowsAdapter.is_unc_path(Path("\\\\server\\share")) is True
        assert WindowsAdapter.is_unc_path(Path("\\\\192.168.1.1\\data")) is True

    def test_is_unc_path_false(self):
        """Test UNC path detection (negative)."""
        assert WindowsAdapter.is_unc_path(Path("C:\\Users")) is False
        assert WindowsAdapter.is_unc_path(Path("D:\\data")) is False


class TestPermissionChecking:
    """Test permission checking."""

    def test_check_permissions(self):
        """Test checking administrator privileges."""
        adapter = WindowsAdapter()
        has_perms, message = adapter.check_permissions()

        # Should return tuple
        assert isinstance(has_perms, bool)
        assert isinstance(message, str)
        assert len(message) > 0

        # Message should be informative
        if has_perms:
            assert "Administrator" in message or "privileges" in message.lower()
        else:
            assert "Administrator" in message or "admin" in message.lower()


class TestImageInfo:
    """Test getting image information."""

    def test_get_image_info_nonexistent(self):
        """Test getting info for non-existent image."""
        adapter = WindowsAdapter()
        info = adapter.get_image_info(Path("C:\\nonexistent.e01"))

        assert isinstance(info, dict)
        assert info['exists'] is False
        assert info['type'] == 'e01'
        assert info['size'] == 0

    @pytest.mark.skipif(
        not Path("C:\\Windows\\System32\\config\\SAM").exists(),
        reason="Requires Windows SAM file for testing"
    )
    def test_get_image_info_existing(self):
        """Test getting info for existing file."""
        adapter = WindowsAdapter()
        # Use a known Windows file
        test_file = Path("C:\\Windows\\System32\\config\\SAM")

        info = adapter.get_image_info(test_file)

        assert isinstance(info, dict)
        assert info['exists'] is True
        assert info['size'] > 0


class TestTempDirectory:
    """Test temporary directory creation."""

    def test_get_temp_directory(self):
        """Test getting Windows temp directory."""
        adapter = WindowsAdapter()
        temp_dir = adapter.get_temp_directory()

        assert isinstance(temp_dir, Path)
        assert temp_dir.exists()
        assert 'elrond' in str(temp_dir).lower()


class TestMountingWithMocks:
    """Test mounting functionality with mocked dependencies."""

    @patch('subprocess.run')
    def test_mount_image_no_tools(self, mock_run):
        """Test mounting when no tools available."""
        adapter = WindowsAdapter()
        adapter.has_arsenal = False
        adapter.has_powershell = False

        with pytest.raises(MountError) as exc_info:
            adapter.mount_image(
                Path("C:\\test.e01"),
                Path("E:\\"),
                image_type="e01"
            )

        assert "Unable to mount" in str(exc_info.value)

    def test_mount_image_nonexistent_file(self):
        """Test mounting non-existent file."""
        adapter = WindowsAdapter()

        with pytest.raises(MountError) as exc_info:
            adapter.mount_image(
                Path("C:\\nonexistent.e01"),
                Path("E:\\"),
                image_type="e01"
            )

        assert "not found" in str(exc_info.value)

    @patch('subprocess.run')
    def test_arsenal_mount_success(self, mock_run):
        """Test successful mount with Arsenal Image Mounter."""
        # Mock Arsenal CLI success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Mounted as E:",
            stderr=""
        )

        adapter = WindowsAdapter()
        adapter.has_arsenal = True

        # Create a fake test file
        with patch.object(Path, 'exists', return_value=True):
            result = adapter._mount_with_arsenal(
                Path("C:\\test.e01"),
                Path("E:\\"),
                read_only=True
            )

        assert result is True
        assert len(adapter.mounted_images) > 0


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_empty(self):
        """Test cleanup with no mounts."""
        adapter = WindowsAdapter()
        # Should not raise exception
        adapter.cleanup()
        assert len(adapter.mounted_images) == 0

    @patch.object(WindowsAdapter, 'unmount_image')
    def test_cleanup_with_mounts(self, mock_unmount):
        """Test cleanup with mounted images."""
        adapter = WindowsAdapter()

        # Add fake mounts
        adapter.mounted_images = {
            "C:\\test1.e01": Path("E:\\"),
            "C:\\test2.vmdk": Path("F:\\")
        }

        adapter.cleanup()

        # Should have tried to unmount both
        assert mock_unmount.call_count == 2
        assert len(adapter.mounted_images) == 0


# Only run these tests on actual Windows
class TestWindowsOnly:
    """Tests that only run on Windows."""

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires actual Windows environment"
    )
    def test_c_drive_exists(self):
        """Test that C: drive exists."""
        adapter = WindowsAdapter()
        assert adapter.is_mounted(Path("C:\\")) is True

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires actual Windows environment"
    )
    def test_powershell_available(self):
        """Test that PowerShell is available."""
        adapter = WindowsAdapter()
        assert adapter.has_powershell is True
