"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_tool_config(tmp_path):
    """Create a minimal tool configuration for testing."""
    config_content = """
tools:
  test_tool:
    name: "Test Tool"
    description: "A test tool"
    category: "test"
    platforms: [all]
    executables:
      - test_tool
    common_paths:
      linux:
        - /usr/bin
      macos:
        - /usr/local/bin
      windows:
        - C:\\\\Windows\\\\System32
    install_methods:
      linux: "apt-get install test-tool"
      macos: "brew install test-tool"
      windows: "Download from example.com"
    required: false
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file
