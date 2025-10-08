"""Unified command execution with platform awareness and error handling."""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from elrond.platform import get_platform_adapter
from elrond.tools import get_tool_manager
from elrond.utils.constants import DEFAULT_COMMAND_TIMEOUT
from elrond.utils.exceptions import ToolNotFoundError
from elrond.utils.logging import get_logger


class CommandExecutor:
    """Unified command execution with tool discovery and error handling."""

    def __init__(self):
        """Initialize CommandExecutor."""
        self.logger = get_logger("elrond.executor")
        self.tool_manager = get_tool_manager()
        self.platform = get_platform_adapter()

    def execute_tool(
        self,
        tool_name: str,
        args: List[str],
        input_data: Optional[str] = None,
        timeout: int = DEFAULT_COMMAND_TIMEOUT,
        check: bool = True,
        capture_output: bool = True,
    ) -> Tuple[int, str, str]:
        """
        Execute a forensic tool with error handling.

        Args:
            tool_name: Name/ID of the tool to execute
            args: List of command arguments
            input_data: Optional stdin input
            timeout: Command timeout in seconds
            check: Raise exception on non-zero return code
            capture_output: Capture stdout/stderr

        Returns:
            Tuple of (returncode, stdout, stderr)

        Raises:
            ToolNotFoundError: If tool not found
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails and check=True
        """
        # Discover tool path
        tool_path = self.tool_manager.get_tool_path(tool_name, raise_if_missing=True)

        if not tool_path:
            # This shouldn't happen due to raise_if_missing, but just in case
            suggestion = self.tool_manager.suggest_installation(tool_name)
            raise ToolNotFoundError(tool_name, suggestion)

        # Build command
        cmd = [tool_path] + args

        self.logger.debug(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
            )

            self.logger.debug(f"Command completed with return code {result.returncode}")
            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            raise

        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"Command failed with code {e.returncode}: {' '.join(cmd)}\n{e.stderr}"
            )
            if check:
                raise
            return e.returncode, e.stdout, e.stderr

        except Exception as e:
            self.logger.error(f"Unexpected error executing {tool_name}: {str(e)}")
            raise

    def execute_command(
        self,
        command: List[str],
        input_data: Optional[str] = None,
        timeout: int = DEFAULT_COMMAND_TIMEOUT,
        check: bool = True,
        capture_output: bool = True,
        cwd: Optional[Path] = None,
    ) -> Tuple[int, str, str]:
        """
        Execute a generic command (not a managed tool).

        Args:
            command: Command and arguments as list
            input_data: Optional stdin input
            timeout: Command timeout in seconds
            check: Raise exception on non-zero return code
            capture_output: Capture stdout/stderr
            cwd: Working directory

        Returns:
            Tuple of (returncode, stdout, stderr)

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails and check=True
        """
        self.logger.debug(f"Executing command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                input=input_data,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
                cwd=str(cwd) if cwd else None,
            )

            return result.returncode, result.stdout, result.stderr

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            raise

        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"Command failed with code {e.returncode}: {' '.join(command)}\n{e.stderr}"
            )
            if check:
                raise
            return e.returncode, e.stdout, e.stderr

        except Exception as e:
            self.logger.error(f"Unexpected error executing command: {str(e)}")
            raise

    def execute_tool_quiet(
        self, tool_name: str, args: List[str], timeout: int = DEFAULT_COMMAND_TIMEOUT
    ) -> bool:
        """
        Execute a tool and return True/False for success/failure.
        Silently catches all errors.

        Args:
            tool_name: Tool name/ID
            args: Arguments
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            returncode, _, _ = self.execute_tool(
                tool_name, args, timeout=timeout, check=False
            )
            return returncode == 0
        except Exception as e:
            self.logger.debug(f"Tool {tool_name} failed: {e}")
            return False

    def check_tool_available(self, tool_name: str) -> bool:
        """
        Check if a tool is available without executing it.

        Args:
            tool_name: Tool name/ID

        Returns:
            True if available, False otherwise
        """
        tool_path = self.tool_manager.discover_tool(tool_name)
        return tool_path is not None


# Global executor instance
_global_executor: Optional[CommandExecutor] = None


def get_executor() -> CommandExecutor:
    """
    Get or create global CommandExecutor instance.

    Returns:
        CommandExecutor instance
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = CommandExecutor()
    return _global_executor
