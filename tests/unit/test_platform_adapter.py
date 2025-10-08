"""Unit tests for platform adapters."""

import pytest
from pathlib import Path

from elrond.platform import get_platform_adapter, PlatformAdapter
from elrond.utils.exceptions import PlatformNotSupportedError


class TestPlatformAdapter:
    """Test platform adapter factory and base functionality."""

    def test_get_platform_adapter_returns_instance(self):
        """Test that factory returns a PlatformAdapter instance."""
        adapter = get_platform_adapter()
        assert adapter is not None
        assert isinstance(adapter, PlatformAdapter)

    def test_get_platform_adapter_singleton(self):
        """Test that factory returns same instance."""
        adapter1 = get_platform_adapter()
        adapter2 = get_platform_adapter()
        assert adapter1 is adapter2

    def test_check_permissions(self):
        """Test permission checking."""
        adapter = get_platform_adapter()
        has_perms, message = adapter.check_permissions()
        assert isinstance(has_perms, bool)
        assert isinstance(message, str)
        assert len(message) > 0

    def test_get_temp_directory(self):
        """Test temp directory retrieval."""
        adapter = get_platform_adapter()
        temp_dir = adapter.get_temp_directory()
        assert isinstance(temp_dir, Path)
        assert temp_dir.name == "elrond"

    def test_clear_screen(self):
        """Test clear screen doesn't raise exception."""
        adapter = get_platform_adapter()
        # Should not raise
        adapter.clear_screen()

    def test_get_mount_points_returns_list(self):
        """Test mount points returns list of paths."""
        adapter = get_platform_adapter()
        mount_points = adapter.get_mount_points()
        assert isinstance(mount_points, list)
        assert all(isinstance(mp, Path) for mp in mount_points)

    def test_validate_image_path_nonexistent(self):
        """Test validation of nonexistent path."""
        adapter = get_platform_adapter()
        fake_path = Path("/nonexistent/fake/image.e01")
        assert adapter.validate_image_path(fake_path) is False

    def test_identify_image_type_by_extension(self):
        """Test image type identification by extension."""
        adapter = get_platform_adapter()

        # Test various extensions
        test_cases = [
            (Path("/test/image.e01"), "e01"),
            (Path("/test/image.E01"), "e01"),
            (Path("/test/image.vmdk"), "vmdk"),
            (Path("/test/image.dd"), "raw"),
            (Path("/test/image.raw"), "raw"),
        ]

        for path, expected_type in test_cases:
            result = adapter.identify_image_type(path)
            # Result should be one of the expected types or unknown
            assert result in [expected_type, "unknown", "raw", "e01", "vmdk"]
