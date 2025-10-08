"""Unit tests for configuration management."""

import pytest
from pathlib import Path

from elrond.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_settings_initialization(self):
        """Test Settings initializes correctly."""
        settings = Settings()
        assert settings is not None
        assert hasattr(settings, "platform_name")
        assert hasattr(settings, "base_dir")
        assert hasattr(settings, "tools_dir")

    def test_get_settings_singleton(self):
        """Test get_settings returns same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_platform_detection(self):
        """Test platform detection."""
        settings = Settings()
        assert settings.platform_name in ["linux", "darwin", "windows"]

    def test_mount_points_generated(self):
        """Test mount points are generated."""
        settings = Settings()
        assert "elrond" in settings.mount_points
        assert "ewf" in settings.mount_points
        assert isinstance(settings.mount_points["elrond"], list)
        assert len(settings.mount_points["elrond"]) > 0

    def test_is_admin(self):
        """Test admin check."""
        settings = Settings()
        is_admin = settings.is_admin()
        assert isinstance(is_admin, bool)

    def test_platform_properties(self):
        """Test platform boolean properties."""
        settings = Settings()

        # Exactly one should be True
        platform_checks = [settings.is_linux, settings.is_windows, settings.is_macos]
        assert sum(platform_checks) == 1

    def test_base_directory_exists_or_creatable(self):
        """Test base directory."""
        settings = Settings()
        assert isinstance(settings.base_dir, Path)
        # Either exists or would be created in standard location
        assert "elrond" in str(settings.base_dir).lower()
