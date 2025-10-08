"""Logging utilities for elrond."""

import logging
import sys
from pathlib import Path
from typing import Optional


class ElrondLogger:
    """Centralized logging for elrond with verbosity control."""

    def __init__(self, name: str = "elrond", verbosity: str = "normal"):
        """
        Initialize logger.

        Args:
            name: Logger name
            verbosity: Verbosity level (quiet, normal, verbose, veryverbose)
        """
        self.logger = logging.getLogger(name)
        self.verbosity = verbosity
        self.setup_logging(verbosity)

    def setup_logging(self, verbosity: str):
        """
        Configure logging based on verbosity level.

        Args:
            verbosity: One of: quiet, normal, verbose, veryverbose
        """
        level_map = {
            "quiet": logging.WARNING,
            "normal": logging.INFO,
            "verbose": logging.DEBUG,
            "veryverbose": logging.DEBUG,
        }

        level = level_map.get(verbosity, logging.INFO)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)

        # Formatter based on verbosity
        if verbosity in ["verbose", "veryverbose"]:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            fmt = "%(message)s"
            datefmt = None

        formatter = logging.Formatter(fmt, datefmt=datefmt)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def add_file_handler(self, log_file: Path, level: int = logging.DEBUG):
        """
        Add file logging handler.

        Args:
            log_file: Path to log file
            level: Logging level for file handler
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt, datefmt=datefmt)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)


# Global logger instance
_global_logger: Optional[ElrondLogger] = None


def get_logger(name: str = "elrond", verbosity: str = "normal") -> ElrondLogger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name
        verbosity: Verbosity level

    Returns:
        ElrondLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = ElrondLogger(name, verbosity)
    return _global_logger


def set_verbosity(verbosity: str):
    """
    Update global logger verbosity.

    Args:
        verbosity: New verbosity level
    """
    global _global_logger
    if _global_logger is not None:
        _global_logger.setup_logging(verbosity)
