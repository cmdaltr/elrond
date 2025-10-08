"""Unit tests for ToolManager."""

import pytest
from pathlib import Path

from elrond.tools.manager import ToolManager
from elrond.tools.definitions import ToolDefinition, ToolPlatform


class TestToolManager:
    """Test ToolManager functionality."""

    def test_tool_manager_initialization(self, mock_tool_config):
        """Test ToolManager initializes correctly."""
        tm = ToolManager(config_file=mock_tool_config)
        assert tm is not None
        assert isinstance(tm.tools, dict)

    def test_load_tool_definitions(self, mock_tool_config):
        """Test loading tool definitions from config."""
        tm = ToolManager(config_file=mock_tool_config)
        assert "test_tool" in tm.tools
        assert tm.tools["test_tool"].name == "Test Tool"

    def test_discover_tool_in_path(self, mock_tool_config):
        """Test discovering a tool in system PATH."""
        tm = ToolManager(config_file=mock_tool_config)

        # Try to discover 'python' which should exist
        # First need to add it to our test config
        # For now, test the logic with a known tool

        # This test would need a tool that actually exists
        # For unit tests, we'd use mocks
        # For integration tests, we'd use real tools

        # Test with nonexistent tool
        result = tm.discover_tool("nonexistent_tool_12345")
        assert result is None

    def test_verify_tool(self, mock_tool_config):
        """Test tool verification."""
        tm = ToolManager(config_file=mock_tool_config)

        # Test with nonexistent tool
        is_available, message = tm.verify_tool("test_tool")
        assert isinstance(is_available, bool)
        assert isinstance(message, str)

    def test_suggest_installation(self, mock_tool_config):
        """Test installation suggestions."""
        tm = ToolManager(config_file=mock_tool_config)
        suggestion = tm.suggest_installation("test_tool")
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

    def test_check_all_dependencies(self, mock_tool_config):
        """Test checking all dependencies."""
        tm = ToolManager(config_file=mock_tool_config)
        results = tm.check_all_dependencies()
        assert isinstance(results, dict)

        # Check structure of results
        for tool_id, status in results.items():
            assert "name" in status
            assert "available" in status
            assert "required" in status
            assert "message" in status
            assert isinstance(status["available"], bool)
            assert isinstance(status["required"], bool)

    def test_get_missing_required_tools(self, mock_tool_config):
        """Test getting missing required tools."""
        tm = ToolManager(config_file=mock_tool_config)
        missing = tm.get_missing_required_tools()
        assert isinstance(missing, list)
