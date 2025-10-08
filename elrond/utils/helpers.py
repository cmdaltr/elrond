"""Helper functions and utilities for common operations."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple


def format_elapsed_time(seconds: int) -> str:
    """
    Format elapsed time in human-readable format.

    Args:
        seconds: Number of seconds elapsed

    Returns:
        Formatted time string (e.g., "2 hours, 15 minutes and 30 seconds")

    Examples:
        >>> format_elapsed_time(45)
        '45 seconds'
        >>> format_elapsed_time(90)
        '1 minute and 30 seconds'
        >>> format_elapsed_time(3665)
        '1 hour, 1 minute and 5 seconds'
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"

    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    if len(parts) > 2:
        return f"{', '.join(parts[:-1])} and {parts[-1]}"
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return parts[0] if parts else "0 seconds"


def calculate_elapsed_time(start_time: str, end_time: str) -> Tuple[int, str]:
    """
    Calculate elapsed time between two ISO format timestamps.

    Args:
        start_time: Start timestamp in ISO format
        end_time: End timestamp in ISO format

    Returns:
        Tuple of (total_seconds, formatted_string)

    Examples:
        >>> start = "2025-01-01T10:00:00.000000"
        >>> end = "2025-01-01T12:30:45.000000"
        >>> seconds, formatted = calculate_elapsed_time(start, end)
        >>> seconds
        9045
        >>> formatted
        '2 hours, 30 minutes and 45 seconds'
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    st = datetime.strptime(start_time, fmt)
    et = datetime.strptime(end_time, fmt)

    total_seconds = int(round((et - st).total_seconds()))
    formatted = format_elapsed_time(total_seconds)

    return total_seconds, formatted


def generate_mount_points(prefix: str, count: int = 20, base_path: str = "/mnt") -> List[str]:
    """
    Generate a list of mount point paths.

    Args:
        prefix: Prefix for mount points (e.g., 'elrond', 'ewf')
        count: Number of mount points to generate
        base_path: Base directory for mount points

    Returns:
        List of mount point paths

    Examples:
        >>> generate_mount_points('elrond', 3)
        ['/mnt/elrond_mount00', '/mnt/elrond_mount01', '/mnt/elrond_mount02']
    """
    return [f"{base_path}/{prefix}_mount{i:02d}" for i in range(count)]


def is_excluded_extension(filename: str, excluded_extensions: List[str]) -> bool:
    """
    Check if a filename has an excluded extension.

    Args:
        filename: Filename to check
        excluded_extensions: List of extensions to exclude

    Returns:
        True if extension should be excluded

    Examples:
        >>> excluded = ['.FA', '.FB', '.FC']
        >>> is_excluded_extension('image.FA', excluded)
        True
        >>> is_excluded_extension('image.E01', excluded)
        False
    """
    filename_upper = filename.upper()
    return any(ext in filename_upper for ext in excluded_extensions)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string

    Examples:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
        >>> format_file_size(1073741824)
        '1.00 GB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        True if directory exists or was created

    Raises:
        PermissionError: If insufficient permissions
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        raise PermissionError(f"Cannot create directory: {path}. Insufficient permissions.")


def validate_output_directory(
    output_dir: str, auto: bool = False, create_if_missing: bool = True
) -> Path:
    """
    Validate and optionally create output directory.

    Args:
        output_dir: Path to output directory
        auto: Automatic mode (skip prompts)
        create_if_missing: Create directory if it doesn't exist

    Returns:
        Path object for validated directory

    Raises:
        ValueError: If directory invalid and user declines to create
        PermissionError: If cannot create directory
    """
    path = Path(output_dir)

    if path.exists():
        if not path.is_dir():
            raise ValueError(f"'{output_dir}' exists but is not a directory")
        return path

    if not create_if_missing:
        raise ValueError(f"Directory does not exist: {output_dir}")

    # Ask user if not in auto mode
    if not auto:
        response = input(
            f"  Output directory '{output_dir}' does not exist.\n"
            f"    Create it? Y/n [Y] "
        )
        if response.lower() == "n":
            raise ValueError("User declined to create output directory")

    # Create directory
    ensure_directory(path)
    print(f"  Created output directory: {path.resolve()}")

    return path


def sanitize_case_id(case_id: str) -> str:
    """
    Sanitize case ID to be filesystem-safe.

    Args:
        case_id: Raw case ID

    Returns:
        Sanitized case ID

    Examples:
        >>> sanitize_case_id("Case #123: Test/Incident")
        'Case_123_Test_Incident'
    """
    import re

    # Replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", case_id)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")
    return sanitized


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks

    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def truncate_string(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        Truncated string

    Examples:
        >>> truncate_string("This is a very long string", 15)
        'This is a ve...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def parse_include_exclude_file(file_path: str) -> Tuple[str, List[str]]:
    """
    Parse include/exclude file argument.

    Args:
        file_path: Argument string (e.g., "include:/path/to/file")

    Returns:
        Tuple of (mode, file_contents_list)

    Raises:
        ValueError: If format is invalid

    Examples:
        >>> parse_include_exclude_file("include:/tmp/test.txt")
        ('include', ['line1', 'line2', ...])
    """
    if not file_path.startswith("include:") and not file_path.startswith("exclude:"):
        raise ValueError(
            "Include/exclude file must start with 'include:' or 'exclude:'\n"
            "Example: include:/path/to/file.txt"
        )

    mode = "include" if file_path.startswith("include:") else "exclude"
    path = file_path[8:]  # Remove "include:" or "exclude:"

    file_obj = Path(path)
    if not file_obj.exists():
        raise ValueError(f"File not found: {path}")

    with open(file_obj, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    return mode, lines


def format_list_for_display(
    items: List[str], prefix: str = "  - ", max_items: int = 10
) -> str:
    """
    Format a list of items for display with optional truncation.

    Args:
        items: List of items to format
        prefix: Prefix for each item
        max_items: Maximum items to display before truncating

    Returns:
        Formatted string

    Examples:
        >>> format_list_for_display(['item1', 'item2'], prefix='* ')
        '* item1\\n* item2'
    """
    if not items:
        return f"{prefix}(none)"

    if len(items) <= max_items:
        return "\n".join(f"{prefix}{item}" for item in items)

    displayed = items[:max_items]
    remaining = len(items) - max_items

    result = "\n".join(f"{prefix}{item}" for item in displayed)
    result += f"\n{prefix}... and {remaining} more"

    return result


def yes_no_prompt(question: str, default: bool = True, auto: bool = False) -> bool:
    """
    Ask a yes/no question with optional automatic response.

    Args:
        question: Question to ask
        default: Default response (True = Yes, False = No)
        auto: If True, return default without prompting

    Returns:
        True for yes, False for no

    Examples:
        >>> yes_no_prompt("Continue?", default=True, auto=True)
        True
        >>> # In interactive mode: yes_no_prompt("Continue?")
        Continue? Y/n [Y] y
        True
    """
    if auto:
        return default

    default_str = "[Y]" if default else "[N]"
    prompt_str = f"{question} Y/n {default_str} " if default else f"{question} y/N {default_str} "

    response = input(prompt_str).strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]
