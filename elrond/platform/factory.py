"""Factory function for creating platform adapters."""

import platform
from typing import Optional

from elrond.utils.exceptions import PlatformNotSupportedError
from .base import PlatformAdapter
from .linux import LinuxAdapter
from .windows import WindowsAdapter
from .macos import MacOSAdapter


_platform_adapter: Optional[PlatformAdapter] = None


def get_platform_adapter(force_reload: bool = False) -> PlatformAdapter:
    """
    Factory function to return the appropriate platform adapter.

    Args:
        force_reload: Force creation of new adapter instance

    Returns:
        PlatformAdapter instance for the current platform

    Raises:
        PlatformNotSupportedError: If platform is not supported
    """
    global _platform_adapter

    if _platform_adapter is not None and not force_reload:
        return _platform_adapter

    system = platform.system().lower()

    if system == "linux":
        _platform_adapter = LinuxAdapter()
    elif system == "darwin":
        _platform_adapter = MacOSAdapter()
    elif system == "windows":
        _platform_adapter = WindowsAdapter()
    else:
        raise PlatformNotSupportedError(system)

    return _platform_adapter
