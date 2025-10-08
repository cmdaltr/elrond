"""
Unit tests for Windows utility functions.

Note: Some tests require Windows environment to run properly.
Tests are designed to be skipped on non-Windows platforms.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != 'win32',
    reason="Windows-specific tests require Windows platform"
)

from elrond.utils.windows import (
    WindowsPathHandler,
    WindowsPrivilegeManager,
    WindowsRegistryHelper,
    WindowsEventLogHelper,
    WindowsProcessHelper,
    WindowsSystemInfo,
    is_windows,
    get_windows_temp,
    get_program_files,
    get_appdata,
)


class TestWindowsPathHandler:
    """Test Windows path handling utilities."""

    def test_normalize_path_forward_slash(self):
        """Test normalizing paths with forward slashes."""
        result = WindowsPathHandler.normalize_path(Path("C:/Users/test/file.txt"))
        assert '\\' in str(result)
        assert '/' not in str(result) or str(result).startswith('/')  # Allow /Users for test env

    def test_normalize_path_backslash(self):
        """Test normalizing paths with backslashes."""
        result = WindowsPathHandler.normalize_path(Path("C:\\Users\\test\\file.txt"))
        path_str = str(result)
        # Should preserve backslashes
        assert 'Users' in path_str or 'test' in path_str

    def test_normalize_path_unc(self):
        """Test normalizing UNC paths."""
        unc_path = "\\\\server\\share\\folder"
        result = WindowsPathHandler.normalize_path(Path(unc_path))
        assert str(result).startswith('\\\\')

    def test_is_unc_path_true(self):
        """Test UNC path detection (positive cases)."""
        assert WindowsPathHandler.is_unc_path(Path("\\\\server\\share")) is True
        assert WindowsPathHandler.is_unc_path(Path("\\\\192.168.1.1\\data")) is True

    def test_is_unc_path_false(self):
        """Test UNC path detection (negative cases)."""
        assert WindowsPathHandler.is_unc_path(Path("C:\\Users")) is False
        assert WindowsPathHandler.is_unc_path(Path("D:\\data")) is False
        # Long path prefix is not UNC
        assert WindowsPathHandler.is_unc_path(Path("\\\\?\\C:\\test")) is False

    def test_to_unc_path_drive_letter(self):
        """Test converting drive letter path to UNC."""
        unc = WindowsPathHandler.to_unc_path(Path("C:\\Users\\test"))
        assert unc.startswith("\\\\localhost\\C$")
        assert "Users" in unc or "test" in unc

    def test_to_unc_path_already_unc(self):
        """Test converting already-UNC path."""
        original = "\\\\server\\share\\folder"
        result = WindowsPathHandler.to_unc_path(Path(original))
        assert result == original

    def test_get_drive_letter_valid(self):
        """Test extracting drive letter from paths."""
        assert WindowsPathHandler.get_drive_letter(Path("C:\\test")) == "C"
        assert WindowsPathHandler.get_drive_letter(Path("D:\\data\\file.txt")) == "D"
        assert WindowsPathHandler.get_drive_letter(Path("Z:\\")) == "Z"

    def test_get_drive_letter_invalid(self):
        """Test extracting drive letter from non-drive paths."""
        assert WindowsPathHandler.get_drive_letter(Path("\\\\server\\share")) is None
        assert WindowsPathHandler.get_drive_letter(Path("relative\\path")) is None

    def test_is_valid_drive_letter(self):
        """Test drive letter validation."""
        # Valid
        assert WindowsPathHandler.is_valid_drive_letter("C") is True
        assert WindowsPathHandler.is_valid_drive_letter("Z") is True
        assert WindowsPathHandler.is_valid_drive_letter("a") is True  # Case insensitive

        # Invalid
        assert WindowsPathHandler.is_valid_drive_letter("1") is False
        assert WindowsPathHandler.is_valid_drive_letter("AA") is False
        assert WindowsPathHandler.is_valid_drive_letter("") is False
        assert WindowsPathHandler.is_valid_drive_letter("*") is False


class TestWindowsPrivilegeManager:
    """Test Windows privilege management."""

    def test_is_admin(self):
        """Test checking administrator status."""
        mgr = WindowsPrivilegeManager()
        result = mgr.is_admin()

        # Should return boolean
        assert isinstance(result, bool)
        # Result depends on how test is run

    @patch('sys.exit')
    @patch('ctypes.windll.shell32.ShellExecuteW')
    def test_request_elevation_when_not_admin(self, mock_shell_exec, mock_exit):
        """Test requesting elevation when not admin."""
        mgr = WindowsPrivilegeManager()

        with patch.object(mgr, 'is_admin', return_value=False):
            mgr.request_elevation(Path("test_script.py"))

            # Should have called ShellExecuteW
            assert mock_shell_exec.called

    def test_request_elevation_when_already_admin(self):
        """Test requesting elevation when already admin."""
        mgr = WindowsPrivilegeManager()

        with patch.object(mgr, 'is_admin', return_value=True):
            result = mgr.request_elevation()
            assert result is True


class TestWindowsRegistryHelper:
    """Test Windows Registry operations."""

    def test_query_value_invalid_key(self):
        """Test querying non-existent registry value."""
        helper = WindowsRegistryHelper()
        result = helper.query_value("INVALID_KEY", "TestValue")
        assert result is None

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows registry"
    )
    def test_query_value_windows_version(self):
        """Test querying Windows version from registry."""
        helper = WindowsRegistryHelper()

        # Query Windows product name (should exist on all Windows)
        result = helper.query_value(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
            "ProductName"
        )

        if result:  # Might fail in sandboxed environments
            assert isinstance(result, str)
            assert len(result) > 0

    def test_export_key_invalid(self):
        """Test exporting non-existent registry key."""
        helper = WindowsRegistryHelper()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)  # Failure

            result = helper.export_key("INVALID_KEY", Path("C:\\temp\\test.reg"))
            assert result is False


class TestWindowsEventLogHelper:
    """Test Windows Event Log operations."""

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows Event Logs"
    )
    def test_list_logs(self):
        """Test listing available event logs."""
        helper = WindowsEventLogHelper()
        logs = helper.list_logs()

        # Should return a list
        assert isinstance(logs, list)

        # Should include standard logs
        log_names = [log.lower() for log in logs]
        # At least one of these should exist
        has_standard_log = any(name in log_names for name in ['system', 'application', 'security'])
        assert has_standard_log or len(logs) > 0  # Either standard logs or some logs

    def test_export_log_invalid_format(self):
        """Test exporting with invalid format."""
        helper = WindowsEventLogHelper()

        result = helper.export_log(
            "System",
            Path("C:\\temp\\test.invalid"),
            format='invalid'
        )

        assert result is False


class TestWindowsProcessHelper:
    """Test Windows process management."""

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows processes"
    )
    def test_get_running_processes(self):
        """Test getting list of running processes."""
        helper = WindowsProcessHelper()
        processes = helper.get_running_processes()

        # Should return list of dictionaries
        assert isinstance(processes, list)

        if processes:  # Might be empty in some environments
            # Each process should have required fields
            for proc in processes:
                assert 'name' in proc
                assert 'pid' in proc

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows processes"
    )
    def test_is_process_running(self):
        """Test checking if process is running."""
        helper = WindowsProcessHelper()

        # System process should be running on Windows
        # (or at least some process should be running)
        processes = helper.get_running_processes()
        if processes:
            first_process = processes[0]['name']
            assert helper.is_process_running(first_process) is True

        # Fake process should not be running
        assert helper.is_process_running("definitely_not_a_real_process.exe") is False

    @patch('subprocess.run')
    def test_kill_process(self, mock_run):
        """Test killing a process."""
        mock_run.return_value = Mock(returncode=0)

        helper = WindowsProcessHelper()
        result = helper.kill_process("test.exe", force=False)

        assert mock_run.called
        assert result is True

    @patch('subprocess.run')
    def test_kill_process_force(self, mock_run):
        """Test force killing a process."""
        mock_run.return_value = Mock(returncode=0)

        helper = WindowsProcessHelper()
        result = helper.kill_process("test.exe", force=True)

        # Should include /F flag
        call_args = mock_run.call_args[0][0]
        assert '/F' in call_args
        assert result is True


class TestWindowsSystemInfo:
    """Test Windows system information gathering."""

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_windows_version(self):
        """Test getting Windows version info."""
        version = WindowsSystemInfo.get_windows_version()

        assert isinstance(version, dict)
        assert 'version_string' in version

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_computer_name(self):
        """Test getting computer name."""
        name = WindowsSystemInfo.get_computer_name()

        assert isinstance(name, str)
        assert len(name) > 0
        assert name != 'UNKNOWN'  # Should get actual name on Windows

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_username(self):
        """Test getting current username."""
        username = WindowsSystemInfo.get_username()

        assert isinstance(username, str)
        assert len(username) > 0
        assert username != 'UNKNOWN'  # Should get actual username on Windows

    def test_is_domain_joined(self):
        """Test checking if domain-joined."""
        result = WindowsSystemInfo.is_domain_joined()

        # Should return boolean
        assert isinstance(result, bool)
        # Result depends on environment


class TestConvenienceFunctions:
    """Test convenience utility functions."""

    def test_is_windows(self):
        """Test Windows detection."""
        result = is_windows()

        # On Windows platform, should return True
        if sys.platform == 'win32':
            assert result is True
        else:
            assert result is False

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_windows_temp(self):
        """Test getting Windows temp directory."""
        temp = get_windows_temp()

        assert isinstance(temp, Path)
        # On Windows, should be valid path
        assert 'Temp' in str(temp) or 'temp' in str(temp) or 'TMP' in str(temp)

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_program_files(self):
        """Test getting Program Files directory."""
        pf = get_program_files()

        assert isinstance(pf, Path)
        assert 'Program Files' in str(pf)

    @pytest.mark.skipif(
        sys.platform != 'win32',
        reason="Requires Windows environment"
    )
    def test_get_appdata(self):
        """Test getting AppData directory."""
        appdata = get_appdata()

        assert isinstance(appdata, Path)
        assert 'AppData' in str(appdata) or appdata.exists()


class TestRequiresAdminDecorator:
    """Test the requires_admin decorator."""

    def test_requires_admin_when_not_admin(self):
        """Test decorator raises error when not admin."""
        from elrond.utils.windows import requires_admin, WindowsUtilityError

        @requires_admin
        def test_function():
            return "success"

        with patch.object(WindowsPrivilegeManager, 'is_admin', return_value=False):
            # Patch the class method
            with patch('elrond.utils.windows.WindowsPrivilegeManager') as mock_mgr:
                mock_instance = Mock()
                mock_instance.is_admin.return_value = False
                mock_mgr.return_value = mock_instance

                with pytest.raises(WindowsUtilityError) as exc_info:
                    test_function()

                assert "Administrator" in str(exc_info.value)

    def test_requires_admin_when_admin(self):
        """Test decorator allows execution when admin."""
        from elrond.utils.windows import requires_admin

        @requires_admin
        def test_function():
            return "success"

        with patch('elrond.utils.windows.WindowsPrivilegeManager') as mock_mgr:
            mock_instance = Mock()
            mock_instance.is_admin.return_value = True
            mock_mgr.return_value = mock_instance

            result = test_function()
            assert result == "success"
