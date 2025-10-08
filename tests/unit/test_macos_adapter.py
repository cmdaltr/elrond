"""
Unit tests for macOS platform adapter.

Note: Some tests require macOS environment to run properly.
Tests are designed to be skipped on non-macOS platforms.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason="macOS-specific tests require macOS platform"
)

from elrond.platform.macos import MacOSAdapter
from elrond.utils.exceptions import MountError, UnmountError


class TestMacOSAdapterInitialization:
    """Test macOS adapter initialization."""

    def test_adapter_creation(self):
        """Test that adapter can be created."""
        adapter = MacOSAdapter()
        assert adapter is not None
        assert adapter.logger is not None
        assert isinstance(adapter.mounted_images, dict)

    def test_arm64_detection(self):
        """Test ARM64 architecture detection."""
        adapter = MacOSAdapter()
        # Result depends on hardware
        assert isinstance(adapter.is_arm64, bool)

    @patch('subprocess.run')
    def test_arm64_detection_mocked(self, mock_run):
        """Test ARM64 detection with mocked output."""
        # Mock ARM64 response
        mock_run.return_value = Mock(stdout="arm64\n", returncode=0)
        adapter = MacOSAdapter()
        assert adapter.is_arm64 is True

        # Mock Intel response
        mock_run.return_value = Mock(stdout="x86_64\n", returncode=0)
        adapter = MacOSAdapter()
        assert adapter.is_arm64 is False


class TestImageTypeIdentification:
    """Test image type identification."""

    @patch('subprocess.run')
    def test_dmg_identification_via_file_command(self, mock_run):
        """Test DMG identification via file command."""
        mock_run.return_value = Mock(
            stdout="Apple Disk Image",
            returncode=0
        )

        adapter = MacOSAdapter()
        image_type = adapter.identify_image_type(Path("test.dmg"))
        assert image_type == "dmg"

    @patch('subprocess.run')
    def test_apfs_identification(self, mock_run):
        """Test APFS identification."""
        mock_run.return_value = Mock(
            stdout="APFS filesystem",
            returncode=0
        )

        adapter = MacOSAdapter()
        image_type = adapter.identify_image_type(Path("test.img"))
        assert image_type == "apfs"

    @patch('subprocess.run')
    def test_e01_identification(self, mock_run):
        """Test E01 identification."""
        mock_run.return_value = Mock(
            stdout="Expert Witness Compression Format",
            returncode=0
        )

        adapter = MacOSAdapter()
        image_type = adapter.identify_image_type(Path("test.e01"))
        assert image_type == "e01"

    def test_extension_based_identification(self):
        """Test extension-based type identification."""
        adapter = MacOSAdapter()

        assert adapter.identify_image_type(Path("test.dmg")) == "dmg"
        assert adapter.identify_image_type(Path("test.sparsebundle")) == "dmg"
        assert adapter.identify_image_type(Path("test.e01")) == "e01"
        assert adapter.identify_image_type(Path("test.vmdk")) == "vmdk"
        assert adapter.identify_image_type(Path("test.dd")) == "raw"
        assert adapter.identify_image_type(Path("test.raw")) == "raw"


class TestMountPointOperations:
    """Test mount point operations."""

    def test_get_mount_points(self):
        """Test getting available mount points."""
        adapter = MacOSAdapter()
        mount_points = adapter.get_mount_points()

        assert isinstance(mount_points, list)
        # All should be Path objects
        for mp in mount_points:
            assert isinstance(mp, Path)

    @patch('subprocess.run')
    def test_is_mounted_true(self, mock_run):
        """Test checking if path is mounted (positive)."""
        mock_run.return_value = Mock(
            stdout="/dev/disk1 on /mnt/test (read-only)",
            returncode=0
        )

        adapter = MacOSAdapter()
        assert adapter.is_mounted(Path("/mnt/test")) is True

    @patch('subprocess.run')
    def test_is_mounted_false(self, mock_run):
        """Test checking if path is mounted (negative)."""
        mock_run.return_value = Mock(
            stdout="/dev/disk1 on /Volumes/Data",
            returncode=0
        )

        adapter = MacOSAdapter()
        assert adapter.is_mounted(Path("/mnt/test")) is False


class TestPermissionChecking:
    """Test permission checking."""

    @patch('os.geteuid')
    def test_check_permissions_as_root(self, mock_geteuid):
        """Test permission check when running as root."""
        mock_geteuid.return_value = 0

        adapter = MacOSAdapter()
        has_perms, message = adapter.check_permissions()

        assert has_perms is True
        assert "root" in message.lower()

    @patch('os.geteuid')
    def test_check_permissions_as_user(self, mock_geteuid):
        """Test permission check when running as regular user."""
        mock_geteuid.return_value = 501  # Regular user UID

        adapter = MacOSAdapter()
        has_perms, message = adapter.check_permissions()

        assert has_perms is False
        assert "sudo" in message.lower() or "root" in message.lower()


class TestImageInfo:
    """Test getting image information."""

    @patch('subprocess.run')
    def test_get_image_info_dmg(self, mock_run):
        """Test getting info for DMG image."""
        # Mock file command
        mock_run.return_value = Mock(
            stdout="Apple Disk Image",
            returncode=0
        )

        adapter = MacOSAdapter()

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 1024 * 1024  # 1MB
                info = adapter.get_image_info(Path("/tmp/test.dmg"))

        assert info['type'] == 'dmg'
        assert info['exists'] is True
        assert info['size'] == 1024 * 1024

    def test_get_image_info_nonexistent(self):
        """Test getting info for non-existent image."""
        adapter = MacOSAdapter()
        info = adapter.get_image_info(Path("/nonexistent/test.dmg"))

        assert info['exists'] is False
        assert info['size'] == 0


class TestTempDirectory:
    """Test temporary directory operations."""

    def test_get_temp_directory(self):
        """Test getting macOS temp directory."""
        adapter = MacOSAdapter()
        temp_dir = adapter.get_temp_directory()

        assert isinstance(temp_dir, Path)
        assert str(temp_dir) == "/tmp/elrond"
        assert temp_dir.exists()  # Should be created


class TestMountingWithMocks:
    """Test mounting functionality with mocked dependencies."""

    def test_mount_nonexistent_image(self):
        """Test mounting non-existent image."""
        adapter = MacOSAdapter()

        with pytest.raises(MountError):
            adapter.mount_image(
                Path("/nonexistent/test.dmg"),
                Path("/mnt/test"),
                image_type="dmg"
            )

    @patch('subprocess.run')
    @patch.object(Path, 'exists', return_value=True)
    @patch.object(Path, 'mkdir')
    def test_mount_dmg_success(self, mock_mkdir, mock_exists, mock_run):
        """Test successful DMG mount."""
        # Mock hdiutil attach success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="/dev/disk4  Apple_HFS  /mnt/test\n",
            stderr=""
        )

        adapter = MacOSAdapter()
        result = adapter.mount_image(
            Path("/tmp/test.dmg"),
            Path("/mnt/test"),
            image_type="dmg"
        )

        assert result is True
        assert len(adapter.mounted_images) == 1

    @patch('subprocess.run')
    @patch.object(Path, 'exists', return_value=True)
    @patch.object(Path, 'mkdir')
    def test_mount_dmg_failure(self, mock_mkdir, mock_exists, mock_run):
        """Test failed DMG mount."""
        # Mock hdiutil attach failure
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="hdiutil: attach failed - image not recognized"
        )

        adapter = MacOSAdapter()

        with pytest.raises(MountError):
            adapter.mount_image(
                Path("/tmp/test.dmg"),
                Path("/mnt/test"),
                image_type="dmg"
            )

    def test_mount_unsupported_type(self):
        """Test mounting unsupported image type."""
        adapter = MacOSAdapter()

        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(MountError) as exc_info:
                adapter.mount_image(
                    Path("/tmp/test.xyz"),
                    Path("/mnt/test"),
                    image_type="unknown"
                )

            assert "Unsupported" in str(exc_info.value)

    @patch('subprocess.run')
    def test_mount_vmdk_not_implemented(self, mock_run):
        """Test that VMDK mounting raises NotImplementedError."""
        # Mock which command to show qemu-nbd exists
        mock_run.return_value = Mock(returncode=0)

        adapter = MacOSAdapter()

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'mkdir'):
                with pytest.raises(NotImplementedError) as exc_info:
                    adapter._mount_vmdk(Path("/tmp/test.vmdk"), Path("/mnt/test"))

                assert "NBD kernel extension" in str(exc_info.value)


class TestUnmounting:
    """Test unmount functionality."""

    def test_unmount_nonexistent_path(self):
        """Test unmounting non-existent path."""
        adapter = MacOSAdapter()

        # Should return True (already unmounted)
        result = adapter.unmount_image(Path("/nonexistent/mount"))
        assert result is True

    @patch('subprocess.run')
    @patch.object(Path, 'exists', return_value=True)
    @patch.object(Path, 'iterdir', return_value=[])
    def test_unmount_success(self, mock_iterdir, mock_exists, mock_run):
        """Test successful unmount."""
        # Mock umount success
        mock_run.return_value = Mock(returncode=0, stderr="")

        adapter = MacOSAdapter()
        # Add fake mount
        adapter.mounted_images["/tmp/test.dmg"] = {
            'mount_point': '/mnt/test',
            'device': '/dev/disk4',
            'type': 'dmg'
        }

        result = adapter.unmount_image(Path("/mnt/test"))
        assert result is True

    @patch('subprocess.run')
    @patch.object(Path, 'exists', return_value=True)
    def test_unmount_with_force(self, mock_exists, mock_run):
        """Test force unmount."""
        # Mock umount failure, then hdiutil success
        mock_run.side_effect = [
            Mock(returncode=1, stderr="busy"),  # umount fails
            Mock(returncode=0, stderr="")        # hdiutil detach succeeds
        ]

        adapter = MacOSAdapter()
        adapter.mounted_images["/tmp/test.dmg"] = {
            'mount_point': '/mnt/test',
            'device': '/dev/disk4',
            'type': 'dmg'
        }

        result = adapter.unmount_image(Path("/mnt/test"), force=True)
        assert result is True


class TestCleanup:
    """Test cleanup functionality."""

    def test_cleanup_empty(self):
        """Test cleanup with no mounts."""
        adapter = MacOSAdapter()
        adapter.cleanup()
        assert len(adapter.mounted_images) == 0

    @patch.object(MacOSAdapter, 'unmount_image')
    def test_cleanup_with_mounts(self, mock_unmount):
        """Test cleanup with mounted images."""
        adapter = MacOSAdapter()

        # Add fake mounts
        adapter.mounted_images = {
            "/tmp/test1.dmg": {
                'mount_point': '/mnt/test1',
                'device': '/dev/disk4',
                'type': 'dmg'
            },
            "/tmp/test2.e01": {
                'mount_point': '/mnt/test2',
                'device': '/dev/disk5',
                'type': 'e01'
            }
        }

        adapter.cleanup()

        # Should have tried to unmount both
        assert mock_unmount.call_count == 2
        assert len(adapter.mounted_images) == 0


class TestHelperMethods:
    """Test helper methods."""

    def test_parse_device_from_hdiutil_output(self):
        """Test parsing device from hdiutil output."""
        adapter = MacOSAdapter()

        output = "/dev/disk4  Apple_HFS  /Volumes/Data"
        device = adapter._parse_device_from_hdiutil_output(output)
        assert device == "/dev/disk4"

    def test_parse_apfs_device(self):
        """Test parsing APFS device."""
        adapter = MacOSAdapter()

        output = "/dev/disk4s1  Apple_APFS  Container disk4"
        device = adapter._parse_apfs_device(output)
        assert device == "/dev/disk4s1"

    def test_parse_hdiutil_imageinfo(self):
        """Test parsing hdiutil imageinfo output."""
        adapter = MacOSAdapter()

        output = """Format: UDIF read-only
Class Name: CUDIFDiskImage
Checksum Type: CRC32"""

        info = adapter._parse_hdiutil_imageinfo(output)

        assert "Format" in info
        assert info["Format"] == "UDIF read-only"
        assert "Class Name" in info


class TestMacOSVersion:
    """Test macOS version detection."""

    @patch('subprocess.run')
    def test_get_macos_version(self, mock_run):
        """Test getting macOS version."""
        mock_run.return_value = Mock(
            stdout="14.2.1\n",
            returncode=0
        )

        version = MacOSAdapter.get_macos_version()
        assert version == (14, 2, 1)

    @patch('subprocess.run')
    def test_get_macos_version_failure(self, mock_run):
        """Test version detection failure."""
        mock_run.return_value = Mock(returncode=1)

        version = MacOSAdapter.get_macos_version()
        assert version == (0, 0, 0)


# Only run these tests on actual macOS
class TestMacOSOnly:
    """Tests that only run on macOS."""

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires actual macOS environment"
    )
    def test_root_volume_exists(self):
        """Test that root volume is accessible."""
        adapter = MacOSAdapter()
        assert Path("/").exists()

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires actual macOS environment"
    )
    def test_temp_directory_creation(self):
        """Test that temp directory can be created."""
        adapter = MacOSAdapter()
        temp = adapter.get_temp_directory()
        assert temp.exists()

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires actual macOS environment"
    )
    def test_macos_version_detection(self):
        """Test actual macOS version detection."""
        version = MacOSAdapter.get_macos_version()
        # Should have valid version on macOS
        assert version[0] > 0  # Major version should be > 0
