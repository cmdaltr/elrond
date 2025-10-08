#!/usr/bin/env python3
"""
Verification script for Phase 1 & 2 implementation.
Run this to verify that all new modules are working correctly.
"""

import sys
from pathlib import Path

# Add elrond to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all new modules can be imported."""
    print("=" * 70)
    print("Testing Module Imports")
    print("=" * 70)

    modules = [
        ("elrond.utils.exceptions", "Custom exceptions"),
        ("elrond.utils.logging", "Logging system"),
        ("elrond.utils.constants", "Constants"),
        ("elrond.config.settings", "Configuration"),
        ("elrond.platform.base", "Platform base"),
        ("elrond.platform.factory", "Platform factory"),
        ("elrond.platform.linux", "Linux adapter"),
        ("elrond.platform.windows", "Windows adapter"),
        ("elrond.platform.macos", "macOS adapter"),
        ("elrond.tools.definitions", "Tool definitions"),
        ("elrond.tools.manager", "Tool manager"),
        ("elrond.core.executor", "Command executor"),
        ("elrond.cli", "CLI interface"),
    ]

    success = 0
    failed = []

    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {description:30} ({module_name})")
            success += 1
        except ImportError as e:
            print(f"  ✗ {description:30} ({module_name})")
            print(f"     Error: {e}")
            failed.append((module_name, str(e)))

    print()
    print(f"Results: {success}/{len(modules)} modules imported successfully")

    if failed:
        print("\nFailed imports:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        return False

    return True


def test_platform_adapter():
    """Test platform adapter functionality."""
    print()
    print("=" * 70)
    print("Testing Platform Adapter")
    print("=" * 70)

    try:
        from elrond.platform import get_platform_adapter

        adapter = get_platform_adapter()
        print(f"  ✓ Platform adapter created: {type(adapter).__name__}")

        has_perms, msg = adapter.check_permissions()
        print(f"  ℹ Permissions: {msg}")

        temp_dir = adapter.get_temp_directory()
        print(f"  ℹ Temp directory: {temp_dir}")

        mount_points = adapter.get_mount_points()
        print(f"  ℹ Mount points available: {len(mount_points)}")

        return True

    except Exception as e:
        print(f"  ✗ Platform adapter test failed: {e}")
        return False


def test_tool_manager():
    """Test tool manager functionality."""
    print()
    print("=" * 70)
    print("Testing Tool Manager")
    print("=" * 70)

    try:
        from elrond.tools import get_tool_manager

        tm = get_tool_manager()
        print(f"  ✓ Tool manager created")
        print(f"  ℹ Tools defined: {len(tm.tools)}")

        # Check a few dependencies
        results = tm.check_all_dependencies()
        available = sum(1 for s in results.values() if s["available"])
        print(f"  ℹ Tools available: {available}/{len(results)}")

        # Show a few examples
        print()
        print("  Sample tool status:")
        for i, (tool_id, status) in enumerate(list(results.items())[:5]):
            symbol = "✓" if status["available"] else "✗"
            print(f"    {symbol} {status['name']:30} {status.get('path', 'Not found')}")

        return True

    except Exception as e:
        print(f"  ✗ Tool manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config():
    """Test configuration system."""
    print()
    print("=" * 70)
    print("Testing Configuration System")
    print("=" * 70)

    try:
        from elrond.config import get_settings

        settings = get_settings()
        print(f"  ✓ Settings loaded")
        print(f"  ℹ Platform: {settings.platform_name}")
        print(f"  ℹ Architecture: {settings.architecture}")
        print(f"  ℹ Base directory: {settings.base_dir}")
        print(f"  ℹ Is admin: {settings.is_admin()}")

        return True

    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_logging():
    """Test logging system."""
    print()
    print("=" * 70)
    print("Testing Logging System")
    print("=" * 70)

    try:
        from elrond.utils.logging import get_logger

        logger = get_logger("test", verbosity="normal")
        print(f"  ✓ Logger created")

        logger.info("This is an info message")
        logger.debug("This is a debug message (should not appear)")

        # Test verbose mode
        from elrond.utils.logging import set_verbosity

        set_verbosity("verbose")
        logger.debug("This is a debug message (should appear)")

        return True

    except Exception as e:
        print(f"  ✗ Logging test failed: {e}")
        return False


def test_executor():
    """Test command executor."""
    print()
    print("=" * 70)
    print("Testing Command Executor")
    print("=" * 70)

    try:
        from elrond.core import get_executor

        executor = get_executor()
        print(f"  ✓ Executor created")

        # Test with a command that should exist (python)
        available = executor.check_tool_available("python")
        print(f"  ℹ Python available: {available}")

        return True

    except Exception as e:
        print(f"  ✗ Executor test failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " Elrond Phase 1 & 2 Implementation Verification ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        ("Import Test", test_imports),
        ("Platform Adapter", test_platform_adapter),
        ("Tool Manager", test_tool_manager),
        ("Configuration", test_config),
        ("Logging System", test_logging),
        ("Command Executor", test_executor),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ {name} crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Summary
    print()
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {name}")

    print()
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("🎉 All tests passed! Phase 1 & 2 implementation is working correctly.")
        print()
        print("Next steps:")
        print("  1. Run: elrond --check-dependencies")
        print("  2. Run: pytest tests/")
        print("  3. Read: PHASE1_2_IMPLEMENTATION.md")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
