"""Custom exceptions for elrond."""


class ElrondError(Exception):
    """Base exception for elrond."""

    pass


class ToolNotFoundError(ElrondError):
    """Raised when a required forensic tool is not found."""

    def __init__(self, tool_name: str, suggestion: str = ""):
        self.tool_name = tool_name
        self.suggestion = suggestion
        message = f"Tool '{tool_name}' not found."
        if suggestion:
            message += f"\n{suggestion}"
        super().__init__(message)


class MountError(ElrondError):
    """Raised when image mounting fails."""

    pass


class UnmountError(ElrondError):
    """Raised when image unmounting fails."""

    pass


class ProcessingError(ElrondError):
    """Raised when artifact processing fails."""

    pass


class CollectionError(ElrondError):
    """Raised when artifact collection fails."""

    pass


class AnalysisError(ElrondError):
    """Raised when forensic analysis fails."""

    pass


class PlatformNotSupportedError(ElrondError):
    """Raised when the current platform is not supported."""

    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(
            f"Platform '{platform}' is not supported. "
            f"Supported platforms: Linux, Windows, macOS"
        )


class ConfigurationError(ElrondError):
    """Raised when there's a configuration error."""

    pass


class PermissionError(ElrondError):
    """Raised when required permissions are not available."""

    pass
