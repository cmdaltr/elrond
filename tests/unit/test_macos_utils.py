"""
Unit tests for macOS utility functions.

Note: Some tests require macOS environment to run properly.
Tests are designed to be skipped on non-macOS platforms.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Skip all tests if not on macOS
pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason="macOS-specific tests require macOS platform"
)

from elrond.utils.macos import (
    MacOSKeychainHelper,
    MacOSUnifiedLogHelper,
    MacOSPlistHelper,
    MacOSArtifactCollector,
    MacOSSystemInfo,
    MacOSCodeSignHelper,
    is_macos,
    get_macos_version,
    is_sip_enabled,
)


class TestMacOSKeychainHelper:
    """Test macOS Keychain operations."""

    def test_initialization(self):
        """Test keychain helper initialization."""
        helper = MacOSKeychainHelper()
        assert helper.logger is not None

    @patch('subprocess.run')
    def test_export_keychain_success(self, mock_run):
        """Test successful keychain export."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        helper = MacOSKeychainHelper()
        result = helper.export_keychain(
            Path("/tmp/test.keychain"),
            Path("/tmp/output.p12")
        )

        assert result is True
        assert mock_run.called

    @patch('subprocess.run')
    def test_export_keychain_failure(self, mock_run):
        """Test failed keychain export."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="error: unable to export keychain"
        )

        helper = MacOSKeychainHelper()
        result = helper.export_keychain(
            Path("/tmp/test.keychain"),
            Path("/tmp/output.p12")
        )

        assert result is False

    @patch('subprocess.run')
    def test_list_keychains(self, mock_run):
        """Test listing keychains."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='"/Users/test/Library/Keychains/login.keychain-db"\n"/Library/Keychains/System.keychain"\n'
        )

        helper = MacOSKeychainHelper()

        with patch.object(Path, 'exists', return_value=True):
            keychains = helper.list_keychains()

        assert len(keychains) == 2
        assert all(isinstance(k, Path) for k in keychains)

    @patch('subprocess.run')
    def test_dump_keychain_info(self, mock_run):
        """Test getting keychain info."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Keychain info output"
        )

        helper = MacOSKeychainHelper()

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 4096
                info = helper.dump_keychain_info(Path("/tmp/test.keychain"))

        assert info['exists'] is True
        assert info['size'] == 4096


class TestMacOSUnifiedLogHelper:
    """Test macOS Unified Logging operations."""

    def test_initialization(self):
        """Test log helper initialization."""
        helper = MacOSUnifiedLogHelper()
        assert helper.logger is not None

    @patch('subprocess.run')
    def test_collect_logs_success(self, mock_run):
        """Test successful log collection."""
        mock_run.return_value = Mock(returncode=0)

        helper = MacOSUnifiedLogHelper()
        result = helper.collect_logs(
            output_file=Path("/tmp/logs.logarchive"),
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now()
        )

        assert result is True
        assert mock_run.called

    @patch('subprocess.run')
    def test_collect_logs_with_filters(self, mock_run):
        """Test log collection with filters."""
        mock_run.return_value = Mock(returncode=0)

        helper = MacOSUnifiedLogHelper()
        result = helper.collect_logs(
            output_file=Path("/tmp/logs.logarchive"),
            predicate='eventMessage contains "error"',
            process="kernel",
            subsystem="com.apple.kernel"
        )

        assert result is True

        # Check that predicate was passed
        call_args = mock_run.call_args[0][0]
        assert "--predicate" in call_args
        assert "--process" in call_args
        assert "--subsystem" in call_args

    @patch('subprocess.run')
    def test_show_logs(self, mock_run):
        """Test showing logs."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Log entries here..."
        )

        helper = MacOSUnifiedLogHelper()
        logs = helper.show_logs(
            predicate='process == "kernel"',
            last="1h",
            style="json"
        )

        assert "Log entries" in logs


class TestMacOSPlistHelper:
    """Test Property List operations."""

    def test_initialization(self):
        """Test plist helper initialization."""
        helper = MacOSPlistHelper()
        assert helper.logger is not None

    def test_read_plist_nonexistent(self):
        """Test reading non-existent plist."""
        helper = MacOSPlistHelper()
        result = helper.read_plist(Path("/nonexistent.plist"))
        assert result is None

    @patch('builtins.open', create=True)
    @patch('plistlib.load')
    @patch.object(Path, 'exists', return_value=True)
    def test_read_plist_success(self, mock_exists, mock_plistload, mock_open):
        """Test successful plist reading."""
        mock_plistload.return_value = {"key": "value"}

        helper = MacOSPlistHelper()
        result = helper.read_plist(Path("/tmp/test.plist"))

        assert result == {"key": "value"}

    @patch('subprocess.run')
    def test_convert_plist_success(self, mock_run):
        """Test plist conversion."""
        mock_run.return_value = Mock(returncode=0)

        helper = MacOSPlistHelper()
        result = helper.convert_plist(
            Path("/tmp/input.plist"),
            Path("/tmp/output.xml"),
            format="xml1"
        )

        assert result is True

    @patch('builtins.open', create=True)
    @patch('plistlib.load')
    @patch.object(Path, 'exists', return_value=True)
    def test_extract_plist_value(self, mock_exists, mock_plistload, mock_open):
        """Test extracting value from plist."""
        mock_plistload.return_value = {
            "Level1": {
                "Level2": {
                    "TargetKey": "TargetValue"
                }
            }
        }

        helper = MacOSPlistHelper()
        value = helper.extract_plist_value(
            Path("/tmp/test.plist"),
            "Level1.Level2.TargetKey"
        )

        assert value == "TargetValue"

    @patch('builtins.open', create=True)
    @patch('plistlib.load')
    @patch.object(Path, 'exists', return_value=True)
    def test_extract_plist_value_nonexistent_key(self, mock_exists, mock_plistload, mock_open):
        """Test extracting non-existent key."""
        mock_plistload.return_value = {"key": "value"}

        helper = MacOSPlistHelper()
        value = helper.extract_plist_value(
            Path("/tmp/test.plist"),
            "NonExistent.Key"
        )

        assert value is None


class TestMacOSArtifactCollector:
    """Test macOS artifact collection."""

    def test_initialization(self):
        """Test artifact collector initialization."""
        collector = MacOSArtifactCollector()
        assert collector.logger is not None

    @patch.object(Path, 'exists', return_value=False)
    def test_collect_user_artifacts_no_user_dir(self, mock_exists):
        """Test collecting artifacts when user directory doesn't exist."""
        collector = MacOSArtifactCollector()
        artifacts = collector.collect_user_artifacts(
            mount_point=Path("/mnt/test"),
            user="nonexistent",
            output_dir=Path("/tmp/output")
        )

        assert len(artifacts) == 0

    @patch('shutil.copy2')
    @patch.object(Path, 'mkdir')
    @patch.object(Path, 'is_file', return_value=True)
    @patch.object(Path, 'exists')
    def test_collect_user_artifacts_success(self, mock_exists, mock_isfile, mock_mkdir, mock_copy):
        """Test successful artifact collection."""
        # Mock user directory exists, artifacts exist
        def exists_side_effect(path):
            path_str = str(path)
            # User dir and artifacts exist
            return "/Users/testuser" in path_str

        mock_exists.side_effect = lambda: True

        collector = MacOSArtifactCollector()

        with patch.object(Path, 'exists', side_effect=exists_side_effect):
            artifacts = collector.collect_user_artifacts(
                mount_point=Path("/mnt/test"),
                user="testuser",
                output_dir=Path("/tmp/output")
            )

        # Should have attempted to collect some artifacts
        assert isinstance(artifacts, dict)

    @patch('shutil.copy2')
    @patch.object(Path, 'mkdir')
    @patch.object(Path, 'is_file', return_value=True)
    @patch.object(Path, 'exists', return_value=True)
    def test_collect_system_artifacts(self, mock_exists, mock_isfile, mock_mkdir, mock_copy):
        """Test system artifact collection."""
        collector = MacOSArtifactCollector()
        artifacts = collector.collect_system_artifacts(
            mount_point=Path("/mnt/test"),
            output_dir=Path("/tmp/output")
        )

        assert isinstance(artifacts, dict)


class TestMacOSSystemInfo:
    """Test macOS system information gathering."""

    @patch('subprocess.run')
    def test_get_system_version(self, mock_run):
        """Test getting system version."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="14.2.1\n"),  # version
            Mock(returncode=0, stdout="macOS\n"),    # product name
            Mock(returncode=0, stdout="23C71\n")      # build
        ]

        info = MacOSSystemInfo.get_system_version()

        assert info["version"] == "14.2.1"
        assert info["product_name"] == "macOS"
        assert info["build"] == "23C71"

    @patch('subprocess.run')
    def test_get_hardware_info(self, mock_run):
        """Test getting hardware info."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="MacBookPro18,3\n"),  # model
            Mock(returncode=0, stdout="Apple M1 Pro\n"),     # CPU
            Mock(returncode=0, stdout="17179869184\n")       # memory (16GB)
        ]

        info = MacOSSystemInfo.get_hardware_info()

        assert info["model"] == "MacBookPro18,3"
        assert info["cpu"] == "Apple M1 Pro"
        assert "16.00 GB" in info["memory_gb"]

    @patch('subprocess.run')
    def test_is_apple_silicon_true(self, mock_run):
        """Test Apple Silicon detection (positive)."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="arm64\n"
        )

        result = MacOSSystemInfo.is_apple_silicon()
        assert result is True

    @patch('subprocess.run')
    def test_is_apple_silicon_false(self, mock_run):
        """Test Apple Silicon detection (negative)."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="x86_64\n"
        )

        result = MacOSSystemInfo.is_apple_silicon()
        assert result is False


class TestMacOSCodeSignHelper:
    """Test code signing verification."""

    def test_initialization(self):
        """Test code sign helper initialization."""
        helper = MacOSCodeSignHelper()
        assert helper.logger is not None

    @patch('subprocess.run')
    def test_verify_signature_valid(self, mock_run):
        """Test verifying valid signature."""
        mock_run.side_effect = [
            Mock(returncode=0, stderr="valid on disk"),  # verify
            Mock(returncode=0, stderr="Identifier=com.apple.Safari")  # details
        ]

        helper = MacOSCodeSignHelper()
        info = helper.verify_signature(Path("/Applications/Safari.app"))

        assert info["signed"] is True
        assert "valid" in info["verify_output"]

    @patch('subprocess.run')
    def test_verify_signature_invalid(self, mock_run):
        """Test verifying invalid signature."""
        mock_run.side_effect = [
            Mock(returncode=1, stderr="code object is not signed at all"),
            Mock(returncode=1, stderr="")
        ]

        helper = MacOSCodeSignHelper()
        info = helper.verify_signature(Path("/tmp/unsigned.app"))

        assert info["signed"] is False


class TestConvenienceFunctions:
    """Test convenience utility functions."""

    def test_is_macos(self):
        """Test macOS detection."""
        result = is_macos()

        # On macOS platform, should return True
        if sys.platform == 'darwin':
            assert result is True
        else:
            assert result is False

    @patch('subprocess.run')
    def test_get_macos_version(self, mock_run):
        """Test getting macOS version string."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="14.2.1\n"
        )

        version = get_macos_version()
        assert version == "14.2.1"

    @patch('subprocess.run')
    def test_is_sip_enabled_true(self, mock_run):
        """Test SIP status (enabled)."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="System Integrity Protection status: enabled."
        )

        result = is_sip_enabled()
        assert result is True

    @patch('subprocess.run')
    def test_is_sip_enabled_false(self, mock_run):
        """Test SIP status (disabled)."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="System Integrity Protection status: disabled."
        )

        result = is_sip_enabled()
        assert result is False


class TestMacOSPaths:
    """Test macOS path utilities."""

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires macOS"
    )
    def test_get_applications_dir(self):
        """Test getting Applications directory."""
        from elrond.utils.macos import get_applications_dir

        apps_dir = get_applications_dir()
        assert apps_dir == Path("/Applications")

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires macOS"
    )
    def test_get_library_dir(self):
        """Test getting Library directory."""
        from elrond.utils.macos import get_library_dir

        lib_dir = get_library_dir()
        assert lib_dir == Path("/Library")

    @pytest.mark.skipif(
        sys.platform != 'darwin',
        reason="Requires macOS"
    )
    def test_get_current_user_home(self):
        """Test getting user home directory."""
        from elrond.utils.macos import get_current_user_home

        home = get_current_user_home()
        assert isinstance(home, Path)
        assert home.exists()
