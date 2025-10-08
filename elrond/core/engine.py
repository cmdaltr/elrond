"""
Refactored elrond engine - gradual replacement for main.py monolithic function.

This module provides a cleaner, more maintainable interface to elrond's functionality
while maintaining backward compatibility with the original implementation.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from elrond.config import get_settings
from elrond.platform import get_platform_adapter
from elrond.tools import get_tool_manager
from elrond.core.executor import get_executor
from elrond.utils.logging import get_logger
from elrond.utils.helpers import (
    calculate_elapsed_time,
    format_elapsed_time,
    generate_mount_points,
    sanitize_case_id,
    yes_no_prompt,
)
from elrond.utils.constants import ONE_GB, EXCLUDED_EXTENSIONS


class ElrondEngine:
    """
    Main elrond forensics engine.

    This class orchestrates the entire forensic analysis workflow,
    providing a cleaner interface than the original monolithic main() function.
    """

    def __init__(
        self,
        case_id: str,
        source_directory: Path,
        output_directory: Optional[Path] = None,
        verbosity: str = "normal",
    ):
        """
        Initialize elrond engine.

        Args:
            case_id: Case/incident identifier
            source_directory: Directory containing forensic images
            output_directory: Output directory (defaults to current directory)
            verbosity: Logging verbosity (quiet, normal, verbose, veryverbose)
        """
        self.case_id = sanitize_case_id(case_id)
        self.source_dir = Path(source_directory)
        self.output_dir = Path(output_directory) if output_directory else Path.cwd()

        # Initialize components
        self.logger = get_logger("elrond.engine", verbosity=verbosity)
        self.settings = get_settings()
        self.platform = get_platform_adapter()
        self.tool_manager = get_tool_manager()
        self.executor = get_executor()

        # State
        self.start_time = datetime.now().isoformat()
        self.images: Dict[str, str] = {}
        self.mounted_images: List[str] = []

        self.logger.info(f"Initialized elrond engine for case: {self.case_id}")
        self.logger.debug(f"Source: {self.source_dir}")
        self.logger.debug(f"Output: {self.output_dir}")

    def check_permissions(self) -> bool:
        """
        Check if running with appropriate permissions.

        Returns:
            True if permissions are adequate
        """
        has_perms, message = self.platform.check_permissions()
        if has_perms:
            self.logger.info(f"✓ {message}")
        else:
            self.logger.warning(f"⚠ {message}")
            self.logger.warning("Some operations may fail without elevated privileges")
        return has_perms

    def check_dependencies(self, required_only: bool = True) -> bool:
        """
        Check forensic tool dependencies.

        Args:
            required_only: Only check required tools

        Returns:
            True if all required tools are available
        """
        self.logger.info("Checking forensic tool dependencies...")

        results = self.tool_manager.check_all_dependencies(required_only=required_only)

        available = sum(1 for s in results.values() if s["available"])
        total = len(results)

        self.logger.info(f"Tools available: {available}/{total}")

        missing_required = [
            name
            for name, status in results.items()
            if status["required"] and not status["available"]
        ]

        if missing_required:
            self.logger.error("Missing required tools:")
            for tool_name in missing_required:
                suggestion = self.tool_manager.suggest_installation(tool_name)
                self.logger.error(f"  ✗ {tool_name}")
                self.logger.info(f"    {suggestion}")
            return False

        self.logger.info("✓ All required tools available")
        return True

    def identify_images(self) -> Dict[str, dict]:
        """
        Identify forensic images in source directory.

        Returns:
            Dictionary of image paths and their metadata
        """
        self.logger.info(f"Scanning for images in: {self.source_dir}")

        images = {}
        excluded_patterns = EXCLUDED_EXTENSIONS

        for path in self.source_dir.rglob("*"):
            if not path.is_file():
                continue

            # Skip excluded extensions (E01 split files)
            if any(ext in path.name.upper() for ext in excluded_patterns):
                continue

            # Check file size (must be > 1GB for forensic images)
            size = path.stat().st_size
            if size < ONE_GB:
                continue

            # Identify image type
            image_type = self.platform.identify_image_type(path)

            if image_type != "unknown":
                images[str(path)] = {
                    "path": path,
                    "type": image_type,
                    "size": size,
                    "name": path.name,
                }
                self.logger.info(f"  Found {image_type} image: {path.name}")

        self.logger.info(f"Identified {len(images)} forensic image(s)")
        return images

    def mount_image(
        self, image_path: Path, mount_point: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Mount a forensic image.

        Args:
            image_path: Path to image file
            mount_point: Optional mount point (auto-generated if not provided)

        Returns:
            Path to mount point if successful, None otherwise
        """
        if mount_point is None:
            # Auto-generate mount point
            mount_points = generate_mount_points("elrond")
            for mp in mount_points:
                mp_path = Path(mp)
                if not self.platform.is_mounted(mp_path):
                    mount_point = mp_path
                    break

        if mount_point is None:
            self.logger.error("No available mount points")
            return None

        self.logger.info(f"Mounting {image_path.name} to {mount_point}")

        try:
            success = self.platform.mount_image(
                image_path, mount_point, image_type="auto", read_only=True
            )

            if success:
                self.mounted_images.append(str(mount_point))
                self.logger.info(f"✓ Mounted successfully")
                return mount_point
            else:
                self.logger.error(f"✗ Mount failed")
                return None

        except Exception as e:
            self.logger.error(f"Mount error: {e}")
            return None

    def unmount_all(self) -> bool:
        """
        Unmount all mounted images.

        Returns:
            True if all unmounts successful
        """
        if not self.mounted_images:
            return True

        self.logger.info("Unmounting all images...")
        success = True

        for mount_point in self.mounted_images:
            try:
                self.platform.unmount_image(Path(mount_point))
                self.logger.debug(f"  Unmounted: {mount_point}")
            except Exception as e:
                self.logger.error(f"  Failed to unmount {mount_point}: {e}")
                success = False

        self.mounted_images.clear()
        return success

    def get_elapsed_time(self) -> str:
        """
        Get formatted elapsed time since engine start.

        Returns:
            Formatted time string
        """
        end_time = datetime.now().isoformat()
        seconds, formatted = calculate_elapsed_time(self.start_time, end_time)
        return formatted

    def cleanup(self):
        """Cleanup resources and unmount images."""
        self.logger.info("Cleaning up...")
        self.unmount_all()
        self.logger.info("Cleanup complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        return False  # Don't suppress exceptions


class LegacyBridge:
    """
    Bridge class to gradually integrate new engine with original code.

    This allows the original elrond.py to use new functionality while
    maintaining backward compatibility.
    """

    @staticmethod
    def create_engine_from_args(args) -> ElrondEngine:
        """
        Create ElrondEngine from original argparse arguments.

        Args:
            args: Parsed arguments from original elrond.py

        Returns:
            ElrondEngine instance
        """
        case_id = args.case[0] if isinstance(args.case, list) else args.case
        source_dir = args.directory[0]

        output_dir = None
        if len(args.directory) > 1:
            output_dir = args.directory[1]

        # Determine verbosity
        verbosity = "normal"
        if hasattr(args, "superQuick") and args.superQuick:
            verbosity = "quiet"
        elif hasattr(args, "verbose") and args.verbose:
            verbosity = "verbose"

        return ElrondEngine(case_id, source_dir, output_dir, verbosity)

    @staticmethod
    def convert_mount_points(elrond_mount: List[str]) -> List[str]:
        """
        Convert original mount points to use new generator.

        Args:
            elrond_mount: Original mount point list

        Returns:
            Generated mount points
        """
        return generate_mount_points("elrond", count=len(elrond_mount))

    @staticmethod
    def check_tool_availability(tool_name: str) -> bool:
        """
        Check if a forensic tool is available.

        Args:
            tool_name: Name of tool to check

        Returns:
            True if available
        """
        tool_manager = get_tool_manager()
        is_available, _ = tool_manager.verify_tool(tool_name)
        return is_available
