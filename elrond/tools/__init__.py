"""Tool management system for external forensic tools."""

from .manager import ToolManager
from .definitions import ToolDefinition, ToolPlatform

__all__ = ["ToolManager", "ToolDefinition", "ToolPlatform"]
