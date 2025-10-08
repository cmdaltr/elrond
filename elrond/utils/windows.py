"""
Windows-specific utility functions for elrond.

Provides Windows-specific functionality including:
- Registry access utilities
- Event Log utilities
- Windows path handling
- Privilege management
- Process management
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from elrond.utils.exceptions import ElrondError
from elrond.utils.logging import get_logger


class WindowsUtilityError(ElrondError):
    """Raised when Windows utility operation fails."""
    pass


class WindowsPrivilegeManager:
    """Manage Windows privileges and permissions."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.windows.privileges")

    def is_admin(self) -> bool:
        """
        Check if running with Administrator privileges.

        Returns:
            True if running as Administrator
        """
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def request_elevation(self, script_path: Optional[Path] = None) -> bool:
        """
        Request UAC elevation (re-launch with Administrator privileges).

        Args:
            script_path: Path to script to re-launch (default: current script)

        Returns:
            True if elevation successful (doesn't return if successful)

        Note:
            This will re-launch the application with elevated privileges
            and exit the current process.
        """
        if self.is_admin():
            return True

        import sys
        import ctypes

        if script_path is None:
            script_path = sys.argv[0]

        try:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script_path}" {" ".join(sys.argv[1:])}',
                None,
                1  # SW_SHOWNORMAL
            )
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"Failed to request elevation: {e}")
            return False


class WindowsPathHandler:
    """Handle Windows-specific path operations."""

    @staticmethod
    def normalize_path(path: Path) -> Path:
        """
        Normalize Windows path.

        Handles:
        - Forward slash to backslash conversion
        - UNC paths
        - Drive letters
        - Long path prefix (\\\\?\\)

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        path_str = str(path).replace('/', '\\')

        # Remove long path prefix if present
        if path_str.startswith('\\\\?\\'):
            path_str = path_str[4:]

        # Handle UNC paths
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
            True if UNC path (\\\\server\\share format)
        """
        path_str = str(path)
        return path_str.startswith('\\\\') and not path_str.startswith('\\\\?\\')

    @staticmethod
    def to_unc_path(path: Path) -> str:
        """
        Convert local path to UNC format if applicable.

        Args:
            path: Path to convert

        Returns:
            UNC path string or original path

        Example:
            C:\\Users\\test -> \\\\localhost\\C$\\Users\\test
        """
        path_str = str(path)

        # Already UNC
        if path_str.startswith('\\\\'):
            return path_str

        # Drive letter path
        if len(path_str) >= 2 and path_str[1] == ':':
            drive = path_str[0]
            rest = path_str[2:].replace('\\', '/')
            return f"\\\\localhost\\{drive}${rest}"

        return path_str

    @staticmethod
    def get_drive_letter(path: Path) -> Optional[str]:
        """
        Extract drive letter from Windows path.

        Args:
            path: Path to extract from

        Returns:
            Drive letter (e.g., 'C') or None
        """
        path_str = str(path)
        if len(path_str) >= 2 and path_str[1] == ':':
            return path_str[0].upper()
        return None

    @staticmethod
    def is_valid_drive_letter(letter: str) -> bool:
        """
        Check if string is a valid drive letter.

        Args:
            letter: Letter to check

        Returns:
            True if valid drive letter (A-Z)
        """
        return len(letter) == 1 and letter.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class WindowsRegistryHelper:
    """Helper for Windows Registry operations."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.windows.registry")

    def query_value(self, key_path: str, value_name: str) -> Optional[str]:
        """
        Query Windows Registry value.

        Args:
            key_path: Registry key path (e.g., "HKLM\\SOFTWARE\\Microsoft")
            value_name: Value name to query

        Returns:
            Value data as string or None if not found
        """
        try:
            import winreg

            # Split key path into root and subkey
            parts = key_path.split('\\', 1)
            if len(parts) != 2:
                return None

            root_name, subkey = parts

            # Map root names to winreg constants
            root_map = {
                'HKLM': winreg.HKEY_LOCAL_MACHINE,
                'HKCU': winreg.HKEY_CURRENT_USER,
                'HKCR': winreg.HKEY_CLASSES_ROOT,
                'HKU': winreg.HKEY_USERS,
                'HKCC': winreg.HKEY_CURRENT_CONFIG,
            }

            root = root_map.get(root_name)
            if root is None:
                return None

            # Open key and query value
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return str(value)

        except Exception as e:
            self.logger.debug(f"Failed to query registry: {e}")
            return None

    def export_key(self, key_path: str, output_file: Path) -> bool:
        """
        Export registry key to .reg file.

        Args:
            key_path: Registry key path to export
            output_file: Path to output .reg file

        Returns:
            True if successful
        """
        try:
            cmd = [
                'reg', 'export',
                key_path,
                str(output_file),
                '/y'  # Overwrite
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Failed to export registry key: {e}")
            return False


class WindowsEventLogHelper:
    """Helper for Windows Event Log operations."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.windows.eventlog")

    def export_log(self, log_name: str, output_file: Path, format: str = 'evtx') -> bool:
        """
        Export Windows Event Log to file.

        Args:
            log_name: Event log name (e.g., 'System', 'Security', 'Application')
            output_file: Path to output file
            format: Output format ('evtx' or 'csv')

        Returns:
            True if successful
        """
        try:
            if format == 'evtx':
                # Use wevtutil to export
                cmd = [
                    'wevtutil', 'epl',
                    log_name,
                    str(output_file)
                ]
            elif format == 'csv':
                # Use PowerShell to export as CSV
                ps_script = f"""
                Get-WinEvent -LogName '{log_name}' |
                    Select-Object TimeCreated, Id, LevelDisplayName, Message |
                    Export-Csv -Path '{output_file}' -NoTypeInformation
                """
                cmd = ['powershell', '-Command', ps_script]
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=300  # 5 minute timeout for large logs
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Failed to export event log: {e}")
            return False

    def list_logs(self) -> List[str]:
        """
        List available Windows Event Logs.

        Returns:
            List of log names
        """
        try:
            result = subprocess.run(
                ['wevtutil', 'el'],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                return [log.strip() for log in result.stdout.split('\n') if log.strip()]

            return []

        except Exception as e:
            self.logger.error(f"Failed to list event logs: {e}")
            return []


class WindowsProcessHelper:
    """Helper for Windows process management."""

    def __init__(self):
        self.logger = get_logger("elrond.utils.windows.process")

    def get_running_processes(self) -> List[Dict[str, str]]:
        """
        Get list of running processes.

        Returns:
            List of dictionaries with process info
        """
        try:
            result = subprocess.run(
                ['tasklist', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return []

            processes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                # Parse CSV line (name, PID, session, mem)
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 4:
                    processes.append({
                        'name': parts[0],
                        'pid': parts[1],
                        'session': parts[2],
                        'memory': parts[3]
                    })

            return processes

        except Exception as e:
            self.logger.error(f"Failed to get running processes: {e}")
            return []

    def is_process_running(self, process_name: str) -> bool:
        """
        Check if a process is running.

        Args:
            process_name: Process name (e.g., 'notepad.exe')

        Returns:
            True if process is running
        """
        processes = self.get_running_processes()
        return any(p['name'].lower() == process_name.lower() for p in processes)

    def kill_process(self, process_name: str, force: bool = False) -> bool:
        """
        Kill a process by name.

        Args:
            process_name: Process name to kill
            force: Force kill (/F flag)

        Returns:
            True if successful
        """
        try:
            cmd = ['taskkill', '/IM', process_name]
            if force:
                cmd.append('/F')

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Failed to kill process: {e}")
            return False


class WindowsSystemInfo:
    """Get Windows system information."""

    @staticmethod
    def get_windows_version() -> Dict[str, str]:
        """
        Get Windows version information.

        Returns:
            Dictionary with version info
        """
        try:
            result = subprocess.run(
                ['ver'],
                capture_output=True,
                text=True,
                shell=True,
                check=False
            )

            info = {
                'version_string': result.stdout.strip()
            }

            # Also try to get detailed info via PowerShell
            ps_script = """
            $os = Get-CimInstance Win32_OperatingSystem
            @{
                Version = $os.Version
                BuildNumber = $os.BuildNumber
                Caption = $os.Caption
                Architecture = $os.OSArchitecture
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                import json
                ps_info = json.loads(result.stdout)
                info.update(ps_info)

            return info

        except Exception:
            return {'version_string': 'Unknown'}

    @staticmethod
    def get_computer_name() -> str:
        """
        Get Windows computer name.

        Returns:
            Computer name
        """
        return os.environ.get('COMPUTERNAME', 'UNKNOWN')

    @staticmethod
    def get_username() -> str:
        """
        Get current Windows username.

        Returns:
            Username
        """
        return os.environ.get('USERNAME', 'UNKNOWN')

    @staticmethod
    def is_domain_joined() -> bool:
        """
        Check if computer is domain-joined.

        Returns:
            True if domain-joined
        """
        try:
            domain = os.environ.get('USERDOMAIN', '')
            computer = os.environ.get('COMPUTERNAME', '')
            return domain != computer and domain not in ('', 'WORKGROUP')
        except Exception:
            return False


# Convenience functions

def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == 'nt'


def get_windows_temp() -> Path:
    """Get Windows temp directory."""
    temp = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp'))
    return Path(temp)


def get_program_files() -> Path:
    """Get Program Files directory."""
    pf = os.environ.get('ProgramFiles', 'C:\\Program Files')
    return Path(pf)


def get_appdata() -> Path:
    """Get AppData directory."""
    appdata = os.environ.get('APPDATA', '')
    if appdata:
        return Path(appdata)
    # Fallback
    return Path.home() / 'AppData' / 'Roaming'


def requires_admin(func):
    """
    Decorator to require Administrator privileges for a function.

    Raises:
        WindowsUtilityError: If not running as Administrator
    """
    def wrapper(*args, **kwargs):
        if not WindowsPrivilegeManager().is_admin():
            raise WindowsUtilityError(
                "Administrator privileges required. "
                "Please run as Administrator or use: runas /user:Administrator cmd"
            )
        return func(*args, **kwargs)
    return wrapper
