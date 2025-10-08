"""
Version Compatibility Utilities

Utilities for checking version compatibility of tools against the host platform.
"""

import platform
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict
from packaging import version

from elrond.utils.logger import get_logger
from elrond.tools.manager import ToolManager

logger = get_logger(__name__)


class VersionCompatibilityChecker:
    """Check version compatibility of tools with the host platform."""

    def __init__(self):
        """Initialize the version compatibility checker."""
        self.tool_manager = ToolManager()
        self.os_info = self._get_os_info()

    def _get_os_info(self) -> Dict[str, str]:
        """
        Get detailed OS information.

        Returns:
            Dictionary with os_type, os_version, os_version_name

        Example:
            {
                'os_type': 'linux',
                'os_version': '22.04',
                'os_version_name': 'ubuntu_22.04',
                'darwin_version': None  # or '14.0.0' for macOS
            }
        """
        os_type = platform.system().lower()
        os_info = {
            'os_type': os_type,
            'os_version': '',
            'os_version_name': '',
            'darwin_version': None
        }

        if os_type == 'linux':
            # Try to get distribution info
            try:
                # Try reading /etc/os-release (standard on modern Linux)
                with open('/etc/os-release', 'r') as f:
                    os_release = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_release[key] = value.strip('"')

                    dist_id = os_release.get('ID', '').lower()
                    dist_version = os_release.get('VERSION_ID', '')

                    os_info['os_version'] = dist_version
                    os_info['os_version_name'] = f"{dist_id}_{dist_version}"

            except Exception as e:
                logger.warning(f"Could not determine Linux distribution: {e}")
                os_info['os_version_name'] = 'linux_unknown'

        elif os_type == 'darwin':
            # macOS version
            mac_version = platform.mac_ver()[0]
            os_info['os_version'] = mac_version
            os_info['darwin_version'] = mac_version

            # Convert to macOS version number
            major = int(mac_version.split('.')[0])
            os_info['os_version_name'] = f"macos_{major}"

        elif os_type == 'windows':
            # Windows version
            win_version = platform.version()
            win_release = platform.release()

            if 'Server' in platform.platform():
                # Windows Server
                if '2019' in platform.platform():
                    os_info['os_version_name'] = 'windows_server_2019'
                elif '2022' in platform.platform():
                    os_info['os_version_name'] = 'windows_server_2022'
                else:
                    os_info['os_version_name'] = 'windows_server_unknown'
            else:
                # Windows Desktop
                if win_release == '10':
                    os_info['os_version_name'] = 'windows_10'
                elif win_release == '11':
                    os_info['os_version_name'] = 'windows_11'
                else:
                    os_info['os_version_name'] = f'windows_{win_release}'

            os_info['os_version'] = win_version

        return os_info

    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """
        Get the installed version of a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Version string or None if not found
        """
        tool_config = self.tool_manager.tools.get(tool_name)
        if not tool_config:
            logger.warning(f"Tool {tool_name} not found in configuration")
            return None

        tool_path = self.tool_manager.find_tool(tool_name)
        if not tool_path:
            logger.debug(f"Tool {tool_name} not installed")
            return None

        version_check = tool_config.get('version_check')
        if not version_check:
            logger.debug(f"No version check command for {tool_name}")
            return None

        try:
            # Run version check command
            cmd = [str(tool_path), version_check]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout + result.stderr

            # Extract version number from output
            # Common patterns: "Version 8.2.1", "v8.2.1", "8.2.1"
            version_patterns = [
                r'[Vv]ersion[:\s]+(\d+\.\d+(?:\.\d+)?)',
                r'v(\d+\.\d+(?:\.\d+)?)',
                r'^(\d+\.\d+(?:\.\d+)?)',
                r'(\d+\.\d+(?:\.\d+)?)'
            ]

            for pattern in version_patterns:
                match = re.search(pattern, output)
                if match:
                    return match.group(1)

            logger.debug(f"Could not extract version from output: {output[:100]}")
            return None

        except subprocess.TimeoutExpired:
            logger.warning(f"Version check timed out for {tool_name}")
            return None
        except Exception as e:
            logger.warning(f"Error checking version for {tool_name}: {e}")
            return None

    def is_version_compatible(
        self,
        tool_name: str,
        tool_version: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a tool version is compatible with the current platform.

        Args:
            tool_name: Name of the tool
            tool_version: Version to check (if None, will detect installed version)

        Returns:
            Tuple of (is_compatible, reason)
            - is_compatible: True if compatible, False otherwise
            - reason: Explanation string
        """
        tool_config = self.tool_manager.tools.get(tool_name)
        if not tool_config:
            return False, f"Tool {tool_name} not found in configuration"

        # Get tool version if not provided
        if tool_version is None:
            tool_version = self.get_tool_version(tool_name)
            if tool_version is None:
                return False, f"Could not determine version of {tool_name}"

        # Check if tool has version compatibility requirements
        version_compat = tool_config.get('version_compatibility')
        if not version_compat:
            # No compatibility requirements specified - assume compatible
            return True, "No specific version requirements"

        # Get platform-specific compatibility
        os_type = self.os_info['os_type']
        os_version_name = self.os_info['os_version_name']

        platform_compat = version_compat.get(os_type, {})
        if not platform_compat:
            return True, f"No compatibility requirements for {os_type}"

        version_requirement = platform_compat.get(os_version_name)
        if not version_requirement:
            # Try to find a compatible version by checking all versions
            logger.debug(
                f"No exact match for {os_version_name}, checking all {os_type} versions"
            )
            # Just return True if no specific requirement
            return True, f"No specific requirement for {os_version_name}"

        # Parse version requirement (e.g., ">=8.1.0,<10.0.0")
        try:
            tool_ver = version.parse(tool_version)
            requirements = version_requirement.split(',')

            for req in requirements:
                req = req.strip()
                if req.startswith('>='):
                    min_ver = version.parse(req[2:])
                    if tool_ver < min_ver:
                        return False, f"Version {tool_version} is below minimum {min_ver} for {os_version_name}"
                elif req.startswith('>'):
                    min_ver = version.parse(req[1:])
                    if tool_ver <= min_ver:
                        return False, f"Version {tool_version} must be greater than {min_ver} for {os_version_name}"
                elif req.startswith('<='):
                    max_ver = version.parse(req[2:])
                    if tool_ver > max_ver:
                        return False, f"Version {tool_version} exceeds maximum {max_ver} for {os_version_name}"
                elif req.startswith('<'):
                    max_ver = version.parse(req[1:])
                    if tool_ver >= max_ver:
                        return False, f"Version {tool_version} must be less than {max_ver} for {os_version_name}"
                elif req.startswith('=='):
                    exact_ver = version.parse(req[2:])
                    if tool_ver != exact_ver:
                        return False, f"Version {tool_version} does not match required {exact_ver} for {os_version_name}"

            return True, f"Version {tool_version} is compatible with {os_version_name}"

        except Exception as e:
            logger.error(f"Error parsing version requirement '{version_requirement}': {e}")
            return False, f"Error checking compatibility: {e}"

    def check_elasticsearch_kibana_match(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Elasticsearch and Kibana versions match.

        Elasticsearch and Kibana must have matching major.minor versions.

        Returns:
            Tuple of (versions_match, message)
        """
        es_version = self.get_tool_version('elasticsearch')
        kibana_version = self.get_tool_version('kibana')

        if not es_version:
            return True, "Elasticsearch not installed, no version check needed"
        if not kibana_version:
            return True, "Kibana not installed, no version check needed"

        try:
            es_ver = version.parse(es_version)
            kibana_ver = version.parse(kibana_version)

            # Extract major.minor
            es_major_minor = f"{es_ver.major}.{es_ver.minor}"
            kibana_major_minor = f"{kibana_ver.major}.{kibana_ver.minor}"

            if es_major_minor != kibana_major_minor:
                return False, (
                    f"Elasticsearch {es_version} and Kibana {kibana_version} "
                    f"have mismatched versions. Major.minor must match: "
                    f"{es_major_minor} != {kibana_major_minor}"
                )

            return True, f"Elasticsearch {es_version} and Kibana {kibana_version} versions match"

        except Exception as e:
            logger.error(f"Error comparing Elasticsearch/Kibana versions: {e}")
            return False, f"Error checking version compatibility: {e}"

    def check_all_siem_tools(self) -> Dict[str, Dict[str, any]]:
        """
        Check compatibility of all SIEM tools (Splunk, Elasticsearch, Kibana).

        Returns:
            Dictionary with tool compatibility information
        """
        results = {}

        for tool_name in ['splunk', 'elasticsearch', 'kibana']:
            tool_version = self.get_tool_version(tool_name)
            is_installed = tool_version is not None

            if is_installed:
                is_compat, reason = self.is_version_compatible(tool_name, tool_version)
                results[tool_name] = {
                    'installed': True,
                    'version': tool_version,
                    'compatible': is_compat,
                    'reason': reason
                }
            else:
                results[tool_name] = {
                    'installed': False,
                    'version': None,
                    'compatible': None,
                    'reason': 'Not installed'
                }

        # Check Elasticsearch/Kibana version match
        if results['elasticsearch']['installed'] and results['kibana']['installed']:
            es_kibana_match, match_msg = self.check_elasticsearch_kibana_match()
            results['elasticsearch_kibana_match'] = {
                'match': es_kibana_match,
                'message': match_msg
            }

        return results

    def get_recommended_versions(self, tool_name: str) -> Optional[str]:
        """
        Get recommended version for a tool on the current platform.

        Args:
            tool_name: Name of the tool

        Returns:
            Recommended version string or None
        """
        tool_config = self.tool_manager.tools.get(tool_name)
        if not tool_config:
            return None

        version_compat = tool_config.get('version_compatibility')
        if not version_compat:
            return None

        os_type = self.os_info['os_type']
        os_version_name = self.os_info['os_version_name']

        platform_compat = version_compat.get(os_type, {})
        version_requirement = platform_compat.get(os_version_name)

        if not version_requirement:
            return None

        # Extract recommended version from requirement
        # e.g., ">=8.1.0,<10.0.0" -> recommend "8.1.0" (minimum compatible)
        min_version_match = re.search(r'>=(\d+\.\d+\.\d+)', version_requirement)
        if min_version_match:
            return min_version_match.group(1)

        return None


def check_siem_compatibility() -> None:
    """
    CLI utility to check SIEM tool compatibility.

    Prints compatibility report for Splunk, Elasticsearch, and Kibana.
    """
    checker = VersionCompatibilityChecker()

    print("\n" + "=" * 70)
    print("SIEM Tool Version Compatibility Report")
    print("=" * 70)

    print(f"\nHost Platform: {checker.os_info['os_type']} ({checker.os_info['os_version_name']})")
    print(f"OS Version: {checker.os_info['os_version']}")

    results = checker.check_all_siem_tools()

    print("\n" + "-" * 70)
    print("Tool Status:")
    print("-" * 70)

    for tool_name, info in results.items():
        if tool_name == 'elasticsearch_kibana_match':
            continue

        print(f"\n{tool_name.upper()}:")
        print(f"  Installed: {info['installed']}")

        if info['installed']:
            print(f"  Version: {info['version']}")
            print(f"  Compatible: {info['compatible']}")
            print(f"  Reason: {info['reason']}")

            if not info['compatible']:
                recommended = checker.get_recommended_versions(tool_name)
                if recommended:
                    print(f"  Recommended: {recommended}")
        else:
            recommended = checker.get_recommended_versions(tool_name)
            if recommended:
                print(f"  Recommended Version: {recommended}")

    # Check Elasticsearch/Kibana version match
    if 'elasticsearch_kibana_match' in results:
        print("\n" + "-" * 70)
        print("Elasticsearch <-> Kibana Version Match:")
        print("-" * 70)
        match_info = results['elasticsearch_kibana_match']
        print(f"  Match: {match_info['match']}")
        print(f"  {match_info['message']}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    check_siem_compatibility()
