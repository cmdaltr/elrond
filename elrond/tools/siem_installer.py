"""
SIEM Auto-Installer

Automatically downloads and installs the appropriate version of SIEM tools
(Splunk, Elasticsearch, Kibana) based on the host platform and version compatibility.
"""

import os
import platform
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple, Dict

from elrond.utils.logger import get_logger
from elrond.utils.version_compat import VersionCompatibilityChecker
from elrond.tools.manager import ToolManager

logger = get_logger(__name__)


class SIEMInstaller:
    """Automatically install SIEM tools with proper version matching."""

    def __init__(self):
        """Initialize the SIEM installer."""
        self.version_checker = VersionCompatibilityChecker()
        self.tool_manager = ToolManager()
        self.os_info = self.version_checker.os_info

    def _download_file(self, url: str, dest_path: Path) -> bool:
        """
        Download a file from URL to destination path.

        Args:
            url: Download URL
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading {url}...")

            # Create progress callback
            def reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(block_num * block_size * 100 / total_size, 100)
                    if block_num % 50 == 0:  # Update every 50 blocks
                        logger.info(f"  Download progress: {percent:.1f}%")

            urllib.request.urlretrieve(url, dest_path, reporthook=reporthook)
            logger.info(f"Downloaded to {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def _get_download_url(self, tool_name: str) -> Optional[str]:
        """
        Get the appropriate download URL for a tool based on platform.

        Args:
            tool_name: Name of the tool (splunk, elasticsearch, kibana)

        Returns:
            Download URL or None if not available
        """
        tool_config = self.tool_manager.tools.get(tool_name)
        if not tool_config:
            logger.error(f"Tool {tool_name} not found in configuration")
            return None

        download_urls = tool_config.get('download_urls', {})
        if not download_urls:
            logger.error(f"No download URLs configured for {tool_name}")
            return None

        os_type = self.os_info['os_type']
        os_version_name = self.os_info['os_version_name']

        platform_urls = download_urls.get(os_type, {})
        url = platform_urls.get(os_version_name)

        if not url:
            logger.warning(f"No download URL for {tool_name} on {os_version_name}")
            # Try to find a compatible version
            for key in platform_urls.keys():
                if key.startswith(os_type):
                    url = platform_urls[key]
                    logger.info(f"Using compatible URL from {key}")
                    break

        return url

    def _install_debian_package(self, deb_file: Path) -> bool:
        """
        Install a .deb package.

        Args:
            deb_file: Path to .deb file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {deb_file.name}...")

            # Check if running as root
            if os.geteuid() != 0:
                logger.warning("Installation requires sudo privileges")
                cmd = ['sudo', 'dpkg', '-i', str(deb_file)]
            else:
                cmd = ['dpkg', '-i', str(deb_file)]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"{deb_file.name} installed successfully")
                return True
            else:
                logger.error(f"Installation failed: {result.stderr}")
                # Try to fix dependencies
                logger.info("Attempting to fix dependencies...")
                subprocess.run(['sudo', 'apt-get', 'install', '-f', '-y'])
                return False

        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False

    def _install_rpm_package(self, rpm_file: Path) -> bool:
        """
        Install a .rpm package.

        Args:
            rpm_file: Path to .rpm file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {rpm_file.name}...")

            if os.geteuid() != 0:
                cmd = ['sudo', 'rpm', '-i', str(rpm_file)]
            else:
                cmd = ['rpm', '-i', str(rpm_file)]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"{rpm_file.name} installed successfully")
                return True
            else:
                logger.error(f"Installation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error installing package: {e}")
            return False

    def _install_macos_dmg(self, dmg_file: Path) -> bool:
        """
        Install a macOS .dmg file.

        Args:
            dmg_file: Path to .dmg file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {dmg_file.name}...")

            # Mount the DMG
            mount_result = subprocess.run(
                ['hdiutil', 'attach', str(dmg_file), '-nobrowse'],
                capture_output=True,
                text=True
            )

            if mount_result.returncode != 0:
                logger.error(f"Failed to mount DMG: {mount_result.stderr}")
                return False

            # Extract mount point
            mount_point = None
            for line in mount_result.stdout.split('\n'):
                if '/Volumes/' in line:
                    mount_point = line.split('\t')[-1].strip()
                    break

            if not mount_point:
                logger.error("Could not determine DMG mount point")
                return False

            logger.info(f"Mounted at {mount_point}")

            # Find and install .pkg or .app
            mount_path = Path(mount_point)
            pkg_files = list(mount_path.glob('*.pkg'))

            success = False
            if pkg_files:
                pkg_file = pkg_files[0]
                logger.info(f"Installing {pkg_file.name}...")
                result = subprocess.run(
                    ['sudo', 'installer', '-pkg', str(pkg_file), '-target', '/'],
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0

            # Unmount
            subprocess.run(['hdiutil', 'detach', mount_point], capture_output=True)

            return success

        except Exception as e:
            logger.error(f"Error installing DMG: {e}")
            return False

    def _install_windows_msi(self, msi_file: Path) -> bool:
        """
        Install a Windows .msi file.

        Args:
            msi_file: Path to .msi file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {msi_file.name}...")

            cmd = ['msiexec', '/i', str(msi_file), '/quiet', '/norestart']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"{msi_file.name} installed successfully")
                return True
            else:
                logger.error(f"Installation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error installing MSI: {e}")
            return False

    def _install_tarball(self, tar_file: Path, install_dir: Path) -> bool:
        """
        Extract and install a tarball.

        Args:
            tar_file: Path to .tar.gz file
            install_dir: Installation directory

        Returns:
            True if successful, False otherwise
        """
        try:
            import tarfile

            logger.info(f"Extracting {tar_file.name} to {install_dir}...")

            install_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(tar_file, 'r:gz') as tar:
                tar.extractall(install_dir)

            logger.info(f"Extracted successfully to {install_dir}")
            return True

        except Exception as e:
            logger.error(f"Error extracting tarball: {e}")
            return False

    def install_siem_tool(self, tool_name: str, force: bool = False) -> Tuple[bool, str]:
        """
        Install a SIEM tool (Splunk, Elasticsearch, or Kibana).

        Args:
            tool_name: Name of the tool
            force: Force reinstallation even if already installed

        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Installing {tool_name}...")

        # Check if already installed
        if not force:
            existing_version = self.version_checker.get_tool_version(tool_name)
            if existing_version:
                is_compat, reason = self.version_checker.is_version_compatible(
                    tool_name, existing_version
                )
                if is_compat:
                    msg = f"{tool_name} {existing_version} is already installed and compatible"
                    logger.info(msg)
                    return True, msg
                else:
                    logger.warning(f"{tool_name} {existing_version} is incompatible: {reason}")

        # Get download URL
        download_url = self._get_download_url(tool_name)
        if not download_url:
            msg = f"No download URL available for {tool_name} on {self.os_info['os_version_name']}"
            logger.error(msg)
            return False, msg

        # Download file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            filename = download_url.split('/')[-1]
            download_path = temp_path / filename

            if not self._download_file(download_url, download_path):
                msg = f"Failed to download {tool_name}"
                return False, msg

            # Install based on file extension
            success = False
            if filename.endswith('.deb'):
                success = self._install_debian_package(download_path)
            elif filename.endswith('.rpm'):
                success = self._install_rpm_package(download_path)
            elif filename.endswith('.dmg'):
                success = self._install_macos_dmg(download_path)
            elif filename.endswith('.msi'):
                success = self._install_windows_msi(download_path)
            elif filename.endswith('.tar.gz'):
                if tool_name == 'elasticsearch':
                    install_dir = Path('/usr/local/elasticsearch')
                elif tool_name == 'kibana':
                    install_dir = Path('/usr/local/kibana')
                else:
                    install_dir = Path(f'/usr/local/{tool_name}')
                success = self._install_tarball(download_path, install_dir)
            else:
                msg = f"Unsupported file type: {filename}"
                logger.error(msg)
                return False, msg

            if success:
                # Verify installation
                installed_version = self.version_checker.get_tool_version(tool_name)
                if installed_version:
                    msg = f"{tool_name} {installed_version} installed successfully"
                    logger.info(msg)
                    return True, msg
                else:
                    msg = f"{tool_name} installation completed but version could not be verified"
                    logger.warning(msg)
                    return True, msg
            else:
                msg = f"{tool_name} installation failed"
                return False, msg

    def install_elastic_stack(self, force: bool = False) -> Tuple[bool, str]:
        """
        Install Elasticsearch and Kibana with matching versions.

        Args:
            force: Force reinstallation even if already installed

        Returns:
            Tuple of (success, message)
        """
        logger.info("Installing Elastic Stack (Elasticsearch + Kibana)...")

        # Install Elasticsearch first
        es_success, es_msg = self.install_siem_tool('elasticsearch', force=force)
        if not es_success:
            return False, f"Elasticsearch installation failed: {es_msg}"

        # Get Elasticsearch version
        es_version = self.version_checker.get_tool_version('elasticsearch')
        if not es_version:
            return False, "Could not determine Elasticsearch version after installation"

        logger.info(f"Elasticsearch {es_version} installed, installing matching Kibana...")

        # Install Kibana
        kb_success, kb_msg = self.install_siem_tool('kibana', force=force)
        if not kb_success:
            return False, f"Kibana installation failed: {kb_msg}"

        # Verify version match
        kb_version = self.version_checker.get_tool_version('kibana')
        match, match_msg = self.version_checker.check_elasticsearch_kibana_match()

        if match:
            msg = f"Elastic Stack installed successfully: Elasticsearch {es_version}, Kibana {kb_version}"
            logger.info(msg)
            return True, msg
        else:
            msg = f"Elastic Stack installed but versions don't match: {match_msg}"
            logger.warning(msg)
            return False, msg

    def ensure_siem_installed(self, tool_name: str) -> bool:
        """
        Ensure a SIEM tool is installed, installing it if necessary.

        This is called automatically when elrond runs and detects that a SIEM
        tool is needed but not installed.

        Args:
            tool_name: Name of the tool (splunk, elasticsearch, kibana)

        Returns:
            True if tool is installed and compatible, False otherwise
        """
        tool_config = self.tool_manager.tools.get(tool_name)
        if not tool_config:
            logger.warning(f"Tool {tool_name} not configured")
            return False

        auto_install = tool_config.get('auto_install', False)
        if not auto_install:
            logger.info(f"{tool_name} does not have auto-installation enabled")
            return False

        logger.info(f"Checking {tool_name} installation...")

        # Check if already installed and compatible
        existing_version = self.version_checker.get_tool_version(tool_name)
        if existing_version:
            is_compat, reason = self.version_checker.is_version_compatible(
                tool_name, existing_version
            )
            if is_compat:
                logger.info(f"{tool_name} {existing_version} is already installed and compatible")
                return True
            else:
                logger.warning(f"{tool_name} {existing_version} is installed but incompatible: {reason}")
                logger.info(f"Will attempt to install compatible version...")

        # Prompt user for confirmation
        print(f"\n{'='*70}")
        print(f"{tool_name.upper()} is required but not installed (or incompatible)")
        print(f"Platform: {self.os_info['os_type']} ({self.os_info['os_version_name']})")

        recommended = self.version_checker.get_recommended_versions(tool_name)
        if recommended:
            print(f"Recommended version: {recommended}")

        print(f"{'='*70}")

        response = input(f"Would you like to automatically download and install {tool_name}? [Y/n]: ").strip().lower()

        if response in ['', 'y', 'yes']:
            # Special handling for Elastic Stack
            if tool_name == 'kibana':
                success, msg = self.install_elastic_stack()
            else:
                success, msg = self.install_siem_tool(tool_name)

            if success:
                print(f"\n✓ {msg}\n")
                return True
            else:
                print(f"\n✗ {msg}\n")
                return False
        else:
            logger.info(f"User declined automatic installation of {tool_name}")
            print(f"\nSkipping {tool_name} installation.")
            print(f"To install manually, visit: {tool_config.get('install_methods', {}).get(self.os_info['os_type'], 'N/A')}\n")
            return False


# Convenience function for runtime use
def ensure_siem_tools_installed(tools: list = None) -> Dict[str, bool]:
    """
    Ensure SIEM tools are installed, installing if necessary.

    Args:
        tools: List of tool names to check (default: ['splunk', 'elasticsearch', 'kibana'])

    Returns:
        Dictionary mapping tool names to installation success status
    """
    if tools is None:
        tools = ['splunk', 'elasticsearch', 'kibana']

    installer = SIEMInstaller()
    results = {}

    for tool in tools:
        results[tool] = installer.ensure_siem_installed(tool)

    return results
