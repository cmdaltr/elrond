"""Platform abstraction layer for cross-platform compatibility."""

from .base import PlatformAdapter
from .factory import get_platform_adapter
from .linux import LinuxAdapter
from .windows import WindowsAdapter
from .macos import MacOSAdapter

__all__ = [
    "PlatformAdapter",
    "get_platform_adapter",
    "LinuxAdapter",
    "WindowsAdapter",
    "MacOSAdapter",
]
