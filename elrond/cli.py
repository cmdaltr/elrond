"""Command-line interface for elrond v2.0."""

import sys
from pathlib import Path

from elrond.config import get_settings
from elrond.platform import get_platform_adapter
from elrond.tools import get_tool_manager
from elrond.utils.logging import get_logger


def check_dependencies():
    """Check all required dependencies and provide installation guidance."""
    logger = get_logger("elrond.cli")

    print("=" * 70)
    print("Elrond Dependency Checker")
    print("=" * 70)
    print()

    # Get system info
    settings = get_settings()
    platform_adapter = get_platform_adapter()

    print(f"Platform: {settings.platform_name}")
    print(f"Architecture: {settings.architecture}")
    print()

    # Check permissions
    has_perms, perm_msg = platform_adapter.check_permissions()
    if has_perms:
        print(f"✓ Permissions: {perm_msg}")
    else:
        print(f"✗ Permissions: {perm_msg}")
    print()

    # Check tools
    tool_manager = get_tool_manager()
    results = tool_manager.check_all_dependencies()

    if not results:
        print("No tools configured for this platform.")
        return False

    # Categorize results
    available = []
    missing_required = []
    missing_optional = []

    for tool_id, status in results.items():
        if status["available"]:
            available.append((tool_id, status))
        elif status["required"]:
            missing_required.append((tool_id, status))
        else:
            missing_optional.append((tool_id, status))

    # Print available tools
    if available:
        print(f"Available Tools ({len(available)}):")
        print("-" * 70)
        for tool_id, status in sorted(available, key=lambda x: x[1]["category"]):
            category = status["category"].upper().ljust(12)
            name = status["name"].ljust(30)
            path = status.get("path", "Unknown")
            print(f"  ✓ [{category}] {name} {path}")
        print()

    # Print missing required tools
    if missing_required:
        print(f"Missing Required Tools ({len(missing_required)}):")
        print("-" * 70)
        for tool_id, status in missing_required:
            category = status["category"].upper().ljust(12)
            name = status["name"].ljust(30)
            print(f"  ✗ [{category}] {name}")

            suggestion = tool_manager.suggest_installation(tool_id)
            print(f"     {suggestion}")
        print()

    # Print missing optional tools
    if missing_optional:
        print(f"Missing Optional Tools ({len(missing_optional)}):")
        print("-" * 70)
        for tool_id, status in missing_optional:
            category = status["category"].upper().ljust(12)
            name = status["name"].ljust(30)
            print(f"  - [{category}] {name}")
        print()

    # Summary
    print("=" * 70)
    total = len(results)
    avail_count = len(available)
    print(f"Summary: {avail_count}/{total} tools available")

    if missing_required:
        print(f"⚠️  {len(missing_required)} required tools are missing!")
        print("   Elrond may not function correctly.")
        return False
    else:
        print("✓ All required tools are available.")

    if missing_optional:
        print(f"ℹ️  {len(missing_optional)} optional tools are missing.")
        print("   Some features may not be available.")

    print("=" * 70)
    return len(missing_required) == 0


def main():
    """
    Main entry point for elrond CLI.

    This is a compatibility wrapper that imports and runs the original elrond.py
    while providing access to new v2.0 features.
    """
    import sys
    from pathlib import Path

    # For now, this is a compatibility wrapper
    # In Phase 3+, this will be replaced with the new CLI implementation

    print("\n" + "=" * 70)
    print("Elrond v2.0 - Digital Forensics Automation Tool")
    print("=" * 70)
    print()
    print("Note: You are running Elrond v2.0 with enhanced cross-platform support.")
    print()

    # Check for special commands
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check-dependencies":
            sys.exit(0 if check_dependencies() else 1)
        elif sys.argv[1] == "--install":
            from elrond.tools.installer import install_tools
            # Parse additional flags
            interactive = "--interactive" in sys.argv
            dry_run = "--dry-run" in sys.argv
            required_only = "--required-only" in sys.argv
            wsl_setup = "--wsl" in sys.argv
            success = install_tools(
                interactive=interactive,
                dry_run=dry_run,
                required_only=required_only,
                wsl_setup=wsl_setup
            )
            sys.exit(0 if success else 1)
        elif sys.argv[1] in ["--version", "-v"]:
            print("Elrond v2.0.0")
            print("Enhanced with cross-platform support")
            sys.exit(0)
        elif sys.argv[1] in ["--help", "-h", "help"]:
            print("Elrond v2.0 - Digital Forensics Automation Tool")
            print()
            print("New v2.0 Commands:")
            print("  --check-dependencies    Check all tool dependencies")
            print("  --install               Install all forensic tools")
            print("    --interactive         Prompt before installing each tool")
            print("    --dry-run            Show what would be installed")
            print("    --required-only      Only install required tools")
            print("    --wsl                Show WSL2 setup instructions (Windows)")
            print("  --version              Show version information")
            print()
            print("For full usage, see the original help below:")
            print("=" * 70)
            print()

    # Import and run original elrond
    try:
        # Add the elrond directory to the path
        elrond_dir = Path(__file__).parent
        if str(elrond_dir) not in sys.path:
            sys.path.insert(0, str(elrond_dir))

        # Import the original elrond.py
        # This maintains backward compatibility
        import elrond as original_elrond

        # The original elrond.py will handle argument parsing and execution
        # via its if __name__ == "__main__" block

    except ImportError as e:
        print(f"Error: Could not import original elrond module: {e}")
        print()
        print("Elrond v2.0 is currently in Phase 1 implementation.")
        print("The original elrond.py should be accessible for backward compatibility.")
        sys.exit(1)


if __name__ == "__main__":
    main()
