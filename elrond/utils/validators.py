"""Validation functions for elrond arguments and inputs."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from elrond.utils.constants import SUPPORTED_IMAGE_EXTENSIONS


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_mode_flags(collect: bool, gandalf: bool, reorganise: bool) -> str:
    """
    Validate that exactly one mode flag is set.

    Args:
        collect: Collect mode flag
        gandalf: Gandalf mode flag
        reorganise: Reorganise mode flag

    Returns:
        The active mode ('collect', 'gandalf', or 'reorganise')

    Raises:
        ValidationError: If validation fails
    """
    modes = []
    if collect:
        modes.append("collect")
    if gandalf:
        modes.append("gandalf")
    if reorganise:
        modes.append("reorganise")

    if len(modes) == 0:
        raise ValidationError(
            "You MUST use one of: collect (-C), gandalf (-G), or reorganise (-R)\n"
            "  -C: Process acquired disk and/or memory images\n"
            "  -G: Process artefacts collected using gandalf\n"
            "  -R: Reorganise previously collected artefacts"
        )

    if len(modes) > 1:
        raise ValidationError(
            f"Cannot use multiple mode flags: {', '.join(modes)}\n"
            "Please choose only one: -C, -G, or -R"
        )

    return modes[0]


def validate_memory_options(volatility: bool, process: bool, memorytimeline: bool) -> None:
    """
    Validate memory-related options.

    Args:
        volatility: Memory analysis flag
        process: Process flag
        memorytimeline: Memory timeline flag

    Raises:
        ValidationError: If validation fails
    """
    if volatility and not process:
        raise ValidationError(
            "Memory analysis (-M) requires the process flag (-P)\n"
            "Usage: -M -P"
        )

    if memorytimeline and not volatility:
        raise ValidationError(
            "Memory timeline (-t) requires the volatility flag (-M)\n"
            "Usage: -M -t"
        )


def validate_mode_specific_flags(
    mode: str,
    collect: bool,
    gandalf: bool,
    vss: bool,
    collectfiles: bool,
    imageinfo: bool,
    symlinks: bool,
    timeline: bool,
    userprofiles: bool,
) -> None:
    """
    Validate that mode-specific flags are only used with appropriate mode.

    Args:
        mode: Current mode ('collect', 'gandalf', 'reorganise')
        collect: Collect flag
        gandalf: Gandalf flag
        vss: VSS flag
        collectfiles: Collect files flag
        imageinfo: Image info flag
        symlinks: Symlinks flag
        timeline: Timeline flag
        userprofiles: User profiles flag

    Raises:
        ValidationError: If validation fails
    """
    collect_only_flags = []

    if (not collect or gandalf) and vss:
        collect_only_flags.append("vss (-c)")
    if (not collect or gandalf) and collectfiles:
        collect_only_flags.append("collectfiles (-F)")
    if (not collect or gandalf) and imageinfo:
        collect_only_flags.append("imageinfo (-i)")
    if (not collect or gandalf) and symlinks:
        collect_only_flags.append("symlinks (-s)")
    if (not collect or gandalf) and timeline:
        collect_only_flags.append("timeline (-T)")
    if (not collect or gandalf) and userprofiles:
        collect_only_flags.append("userprofiles (-U)")

    if collect_only_flags:
        mode_name = "gandalf (-G)" if gandalf else "reorganise (-R)"
        raise ValidationError(
            f"The following flags require collect mode (-C):\n"
            f"  {', '.join(collect_only_flags)}\n"
            f"You cannot use them with {mode_name}"
        )


def validate_analysis_options(analysis: bool, process: bool) -> None:
    """
    Validate analysis options.

    Args:
        analysis: Analysis flag
        process: Process flag

    Raises:
        ValidationError: If validation fails
    """
    if analysis and not process:
        raise ValidationError(
            "Analysis (-A) requires the process flag (-P)\n" "Usage: -A -P"
        )


def validate_navigator_options(navigator: bool, splunk: bool) -> None:
    """
    Validate MITRE Navigator options.

    Args:
        navigator: Navigator flag
        splunk: Splunk flag

    Raises:
        ValidationError: If validation fails
    """
    if navigator and not splunk:
        raise ValidationError(
            "Navigator (-N) requires Splunk (-S)\n"
            "The MITRE ATT&CK Navigator integration works with Splunk indexing.\n"
            "Usage: -N -S"
        )


def validate_nsrl_options(
    metacollected: bool, nsrl: bool, superquick: bool, quick: bool
) -> None:
    """
    Validate NSRL hash checking options.

    Args:
        metacollected: Metacollected flag
        nsrl: NSRL flag
        superquick: Super quick flag
        quick: Quick flag

    Raises:
        ValidationError: If validation fails
    """
    if not metacollected and nsrl and (superquick or quick):
        raise ValidationError(
            "NSRL checking (-n) with quick modes requires metacollected (-m)\n"
            "Either:\n"
            "  1. Use: -m -n (with or without -Q/-q)\n"
            "  2. Or remove -Q/-q flags to enable full hashing"
        )


def validate_directory(
    directory: str, check_images: bool = True
) -> Tuple[Path, Optional[str]]:
    """
    Validate input directory.

    Args:
        directory: Directory path
        check_images: Check for valid image files

    Returns:
        Tuple of (validated_path, error_message)

    Raises:
        ValidationError: If validation fails
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        raise ValidationError(f"Directory does not exist: {directory}")

    if not dir_path.is_dir():
        raise ValidationError(f"Path is not a directory: {directory}")

    if check_images:
        # Check for valid image files
        files = list(dir_path.rglob("*"))
        image_files = [
            f
            for f in files
            if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]

        if not image_files:
            raise ValidationError(
                f"No valid forensic images found in: {directory}\n"
                f"Supported formats: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
            )

    return dir_path, None


def validate_yara_directory(yara_dir: str) -> Path:
    """
    Validate YARA rules directory.

    Args:
        yara_dir: Path to YARA directory

    Returns:
        Validated Path object

    Raises:
        ValidationError: If validation fails
    """
    yara_path = Path(yara_dir)

    if not yara_path.exists():
        raise ValidationError(f"YARA directory does not exist: {yara_dir}")

    if not yara_path.is_dir():
        raise ValidationError(f"YARA path is not a directory: {yara_dir}")

    # Check for .yara or .yar files
    yara_files = list(yara_path.rglob("*.yara")) + list(yara_path.rglob("*.yar"))

    if not yara_files:
        raise ValidationError(
            f"No YARA rule files found in: {yara_dir}\n"
            "Expected files with .yara or .yar extension"
        )

    return yara_path


def validate_keyword_file(keyword_file: str) -> Path:
    """
    Validate keyword file.

    Args:
        keyword_file: Path to keyword file

    Returns:
        Validated Path object

    Raises:
        ValidationError: If validation fails
    """
    keyword_path = Path(keyword_file)

    if not keyword_path.exists():
        raise ValidationError(f"Keyword file does not exist: {keyword_file}")

    if not keyword_path.is_file():
        raise ValidationError(f"Keyword path is not a file: {keyword_file}")

    # Check file has content
    if keyword_path.stat().st_size == 0:
        raise ValidationError(f"Keyword file is empty: {keyword_file}")

    return keyword_path


def validate_collectfiles_argument(collectfiles_arg: str) -> Tuple[str, Optional[Path]]:
    """
    Validate and parse collectfiles argument.

    Args:
        collectfiles_arg: Collect files argument string

    Returns:
        Tuple of (mode, file_path) where mode is 'include', 'exclude', or 'all'

    Raises:
        ValidationError: If validation fails
    """
    if collectfiles_arg == True or collectfiles_arg is None:
        # Just the flag, no file
        return "all", None

    if not isinstance(collectfiles_arg, str):
        return "all", None

    if not collectfiles_arg.startswith("include:") and not collectfiles_arg.startswith(
        "exclude:"
    ):
        raise ValidationError(
            "Collectfiles argument must start with 'include:' or 'exclude:'\n"
            "Example: -F include:/path/to/file.txt"
        )

    mode = "include" if collectfiles_arg.startswith("include:") else "exclude"
    file_path_str = collectfiles_arg[8:]  # Remove prefix

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise ValidationError(f"Collectfiles list does not exist: {file_path_str}")

    if not file_path.is_file():
        raise ValidationError(f"Collectfiles path is not a file: {file_path_str}")

    return mode, file_path


def validate_all_arguments(args) -> dict:
    """
    Validate all command-line arguments.

    Args:
        args: Parsed arguments from argparse

    Returns:
        Dictionary of validated arguments

    Raises:
        ValidationError: If any validation fails
        SystemExit: On validation error (prints message and exits)
    """
    try:
        # Validate mode flags
        mode = validate_mode_flags(args.Collect, args.Gandalf, args.Reorganise)

        # Validate memory options
        validate_memory_options(args.Memory, args.Process, args.memorytimeline)

        # Validate mode-specific flags
        validate_mode_specific_flags(
            mode,
            args.Collect,
            args.Gandalf,
            args.vss,
            args.collectFiles,
            args.imageinfo,
            args.symlinks,
            args.Timeline,
            args.Userprofiles,
        )

        # Validate analysis options
        validate_analysis_options(args.Analysis, args.Process)

        # Validate navigator options
        validate_navigator_options(args.Navigator, args.Splunk)

        # Validate NSRL options
        validate_nsrl_options(
            args.metacollected, args.nsrl, args.superQuick, args.quick
        )

        # Validate directory
        directory_path, _ = validate_directory(args.directory[0])

        # Validate optional arguments
        validated = {
            "mode": mode,
            "directory": directory_path,
        }

        if args.Yara:
            validated["yara_dir"] = validate_yara_directory(args.Yara[0])

        if args.Keywords:
            validated["keyword_file"] = validate_keyword_file(args.Keywords[0])

        if args.collectFiles:
            mode, file_path = validate_collectfiles_argument(args.collectFiles)
            validated["collectfiles_mode"] = mode
            validated["collectfiles_path"] = file_path

        return validated

    except ValidationError as e:
        print(f"\n❌ Validation Error:\n{str(e)}\n", file=sys.stderr)
        sys.exit(1)
