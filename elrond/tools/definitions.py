"""Tool definitions and data classes."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ToolPlatform(Enum):
    """Supported platforms for tools."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ALL = "all"


@dataclass
class ToolDefinition:
    """Defines a forensic tool's requirements and locations."""

    name: str
    description: str
    platforms: List[ToolPlatform]
    executable_name: str
    common_paths: Dict[str, List[str]] = field(default_factory=dict)
    install_methods: Dict[str, str] = field(default_factory=dict)
    version_command: Optional[str] = None
    min_version: Optional[str] = None
    required: bool = True
    category: str = "general"

    def __post_init__(self):
        """Validate and convert platform strings to enums if needed."""
        if self.platforms and isinstance(self.platforms[0], str):
            self.platforms = [ToolPlatform(p) for p in self.platforms]
