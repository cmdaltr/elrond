"""Tool management system for discovering and verifying forensic tools."""

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from elrond.utils.exceptions import ToolNotFoundError
from elrond.utils.logging import get_logger
from .definitions import ToolDefinition, ToolPlatform


class ToolManager:
    """Manages discovery, verification, and installation guidance for forensic tools."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize ToolManager.

        Args:
            config_file: Path to tools config YAML file (optional)
        """
        self.logger = get_logger("elrond.tools")
        self.platform_name = platform.system().lower()
        self.discovered_tools: Dict[str, str] = {}

        # Load tool definitions
        if config_file is None:
            # Use bundled config
            config_file = Path(__file__).parent / "config.yaml"

        self.tools = self._load_tool_definitions(config_file)
        self.logger.debug(f"Loaded {len(self.tools)} tool definitions")

    def _load_tool_definitions(self, config_file: Path) -> Dict[str, ToolDefinition]:
        """
        Load tool definitions from YAML configuration file.

        Args:
            config_file: Path to YAML config file

        Returns:
            Dictionary of tool name to ToolDefinition
        """
        tools = {}

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            if "tools" not in config:
                self.logger.warning("No tools section found in config file")
                return tools

            for tool_id, tool_data in config["tools"].items():
                # Parse platforms
                platforms = []
                for platform_str in tool_data.get("platforms", ["all"]):
                    try:
                        if platform_str == "all":
                            platforms = [ToolPlatform.ALL]
                            break
                        else:
                            platforms.append(ToolPlatform(platform_str))
                    except ValueError:
                        self.logger.warning(f"Unknown platform: {platform_str}")

                # Get executables (may be single string or list)
                executables = tool_data.get("executables", [])
                if isinstance(executables, str):
                    executables = [executables]
                elif not executables:
                    executables = [tool_id]  # Use tool_id as default

                # Create ToolDefinition
                tool_def = ToolDefinition(
                    name=tool_data.get("name", tool_id),
                    description=tool_data.get("description", ""),
                    platforms=platforms,
                    executable_name=executables[0],  # Use first as primary
                    common_paths=tool_data.get("common_paths", {}),
                    install_methods=tool_data.get("install_methods", {}),
                    version_command=tool_data.get("version_check"),
                    required=tool_data.get("required", False),
                    category=tool_data.get("category", "general"),
                )

                tools[tool_id] = tool_def

        except FileNotFoundError:
            self.logger.error(f"Tool config file not found: {config_file}")
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML config: {e}")
        except Exception as e:
            self.logger.error(f"Error loading tool definitions: {e}")

        return tools

    def discover_tool(self, tool_name: str) -> Optional[str]:
        """
        Discover tool location on the system.

        Args:
            tool_name: Name/ID of the tool

        Returns:
            Full path to executable or None if not found
        """
        # Check cache first
        if tool_name in self.discovered_tools:
            return self.discovered_tools[tool_name]

        tool = self.tools.get(tool_name)
        if not tool:
            self.logger.warning(f"Unknown tool: {tool_name}")
            return None

        # Check if tool is available for this platform
        if not self._is_platform_supported(tool):
            self.logger.debug(f"Tool {tool_name} not supported on {self.platform_name}")
            return None

        # Check common paths for this platform
        platform_key = self._get_platform_key()
        common_paths = tool.common_paths.get(platform_key, [])

        for path_str in common_paths:
            path = Path(path_str) / tool.executable_name
            if path.exists() and path.is_file():
                self.discovered_tools[tool_name] = str(path)
                self.logger.debug(f"Found {tool_name} at {path}")
                return str(path)

        # Check system PATH
        system_path = shutil.which(tool.executable_name)
        if system_path:
            self.discovered_tools[tool_name] = system_path
            self.logger.debug(f"Found {tool_name} in PATH: {system_path}")
            return system_path

        # Not found
        self.logger.debug(f"Tool {tool_name} not found on system")
        return None

    def verify_tool(self, tool_name: str) -> Tuple[bool, str]:
        """
        Verify tool is available and optionally check version.

        Args:
            tool_name: Name/ID of the tool

        Returns:
            Tuple of (is_available, message)
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Unknown tool: {tool_name}"

        # Check platform support
        if not self._is_platform_supported(tool):
            return False, f"{tool_name} not supported on {self.platform_name}"

        # Discover tool location
        tool_path = self.discover_tool(tool_name)
        if not tool_path:
            return False, f"{tool_name} not found on system"

        # Optionally verify version
        if tool.version_command:
            try:
                result = subprocess.run(
                    [tool_path, tool.version_command],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split("\n")[0]
                    return True, f"{tool_name} found at {tool_path} ({version})"
            except Exception as e:
                self.logger.debug(f"Version check failed for {tool_name}: {e}")

        return True, f"{tool_name} found at {tool_path}"

    def check_all_dependencies(self, required_only: bool = False) -> Dict[str, dict]:
        """
        Check all tool dependencies.

        Args:
            required_only: Only check required tools

        Returns:
            Dictionary of results with tool status
        """
        results = {}

        for tool_id, tool in self.tools.items():
            # Skip if not required and we're only checking required
            if required_only and not tool.required:
                continue

            # Skip if not supported on this platform
            if not self._is_platform_supported(tool):
                continue

            is_available, message = self.verify_tool(tool_id)
            tool_path = self.discover_tool(tool_id)

            results[tool_id] = {
                "name": tool.name,
                "available": is_available,
                "required": tool.required,
                "message": message,
                "path": tool_path,
                "category": tool.category,
            }

        return results

    def suggest_installation(self, tool_name: str) -> str:
        """
        Provide installation instructions for a tool.

        Args:
            tool_name: Name/ID of the tool

        Returns:
            Installation suggestion string
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Unknown tool: {tool_name}"

        platform_key = self._get_platform_key()
        method = tool.install_methods.get(platform_key)

        if method:
            return f"To install {tool.name}:\n  {method}"
        else:
            return f"No installation method defined for {tool.name} on {self.platform_name}"

    def get_tool_path(
        self, tool_name: str, raise_if_missing: bool = False
    ) -> Optional[str]:
        """
        Get the path to a tool's executable.

        Args:
            tool_name: Name/ID of the tool
            raise_if_missing: Raise ToolNotFoundError if not found

        Returns:
            Path to tool or None

        Raises:
            ToolNotFoundError: If tool not found and raise_if_missing is True
        """
        tool_path = self.discover_tool(tool_name)

        if tool_path is None and raise_if_missing:
            suggestion = self.suggest_installation(tool_name)
            raise ToolNotFoundError(tool_name, suggestion)

        return tool_path

    def _is_platform_supported(self, tool: ToolDefinition) -> bool:
        """Check if tool is supported on current platform."""
        if ToolPlatform.ALL in tool.platforms:
            return True

        platform_map = {
            "windows": ToolPlatform.WINDOWS,
            "linux": ToolPlatform.LINUX,
            "darwin": ToolPlatform.MACOS,
        }

        current_platform = platform_map.get(self.platform_name)
        return current_platform in tool.platforms if current_platform else False

    def _get_platform_key(self) -> str:
        """Get platform key for config lookups."""
        if self.platform_name == "darwin":
            return "macos"
        return self.platform_name

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Get list of tool IDs in a category.

        Args:
            category: Category name

        Returns:
            List of tool IDs
        """
        return [
            tool_id for tool_id, tool in self.tools.items() if tool.category == category
        ]

    def get_missing_required_tools(self) -> List[str]:
        """
        Get list of required tools that are not available.

        Returns:
            List of missing tool names
        """
        missing = []

        for tool_id, tool in self.tools.items():
            if tool.required and self._is_platform_supported(tool):
                if not self.discover_tool(tool_id):
                    missing.append(tool.name)

        return missing


# Global tool manager instance
_global_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """
    Get or create global ToolManager instance.

    Returns:
        ToolManager instance
    """
    global _global_tool_manager
    if _global_tool_manager is None:
        _global_tool_manager = ToolManager()
    return _global_tool_manager
