"""Unit tests for helper functions."""

import pytest
from pathlib import Path

from elrond.utils.helpers import (
    format_elapsed_time,
    calculate_elapsed_time,
    generate_mount_points,
    is_excluded_extension,
    format_file_size,
    sanitize_case_id,
    truncate_string,
    chunk_list,
)


class TestTimeFormatting:
    """Test time formatting functions."""

    def test_format_seconds(self):
        """Test formatting seconds only."""
        assert format_elapsed_time(1) == "1 second"
        assert format_elapsed_time(30) == "30 seconds"
        assert format_elapsed_time(59) == "59 seconds"

    def test_format_minutes(self):
        """Test formatting minutes."""
        assert format_elapsed_time(60) == "1 minute"
        assert format_elapsed_time(90) == "1 minute and 30 seconds"
        assert format_elapsed_time(120) == "2 minutes"
        assert format_elapsed_time(150) == "2 minutes and 30 seconds"

    def test_format_hours(self):
        """Test formatting hours."""
        assert format_elapsed_time(3600) == "1 hour"
        assert format_elapsed_time(3660) == "1 hour and 1 minute"
        assert format_elapsed_time(3661) == "1 hour, 1 minute and 1 second"
        assert format_elapsed_time(7200) == "2 hours"
        assert format_elapsed_time(7265) == "2 hours, 1 minute and 5 seconds"

    def test_calculate_elapsed_time(self):
        """Test elapsed time calculation."""
        start = "2025-01-01T10:00:00.000000"
        end = "2025-01-01T10:01:30.000000"

        seconds, formatted = calculate_elapsed_time(start, end)

        assert seconds == 90
        assert "1 minute and 30 seconds" in formatted


class TestMountPoints:
    """Test mount point generation."""

    def test_generate_mount_points_default(self):
        """Test default mount point generation."""
        points = generate_mount_points("elrond")
        assert len(points) == 20
        assert points[0] == "/mnt/elrond_mount00"
        assert points[19] == "/mnt/elrond_mount19"

    def test_generate_mount_points_custom_count(self):
        """Test custom count."""
        points = generate_mount_points("ewf", count=5)
        assert len(points) == 5
        assert points[0] == "/mnt/ewf_mount00"
        assert points[4] == "/mnt/ewf_mount04"

    def test_generate_mount_points_custom_base(self):
        """Test custom base path."""
        points = generate_mount_points("test", count=2, base_path="/tmp")
        assert len(points) == 2
        assert points[0] == "/tmp/test_mount00"
        assert points[1] == "/tmp/test_mount01"


class TestFileOperations:
    """Test file operation helpers."""

    def test_is_excluded_extension_true(self):
        """Test excluded extension detection."""
        excluded = [".FA", ".FB", ".FC"]

        assert is_excluded_extension("image.FA", excluded)
        assert is_excluded_extension("image.fa", excluded)  # Case insensitive
        assert is_excluded_extension("test.FB", excluded)

    def test_is_excluded_extension_false(self):
        """Test non-excluded extensions."""
        excluded = [".FA", ".FB", ".FC"]

        assert not is_excluded_extension("image.E01", excluded)
        assert not is_excluded_extension("image.vmdk", excluded)

    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(500) == "500.00 B"
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1048576) == "1.00 MB"
        assert format_file_size(1073741824) == "1.00 GB"
        assert format_file_size(1099511627776) == "1.00 TB"


class TestStringOperations:
    """Test string manipulation helpers."""

    def test_sanitize_case_id_basic(self):
        """Test basic case ID sanitization."""
        assert sanitize_case_id("Case123") == "Case123"
        assert sanitize_case_id("case-456") == "case-456"

    def test_sanitize_case_id_special_chars(self):
        """Test sanitization of special characters."""
        assert sanitize_case_id("Case:123") == "Case_123"
        assert sanitize_case_id('Case"456') == "Case_456"
        assert sanitize_case_id("Case/Test") == "Case_Test"
        assert sanitize_case_id("Case\\Test") == "Case_Test"
        assert sanitize_case_id("Case<>Test") == "Case__Test"

    def test_sanitize_case_id_whitespace(self):
        """Test whitespace handling."""
        assert sanitize_case_id("  Case123  ") == "Case123"
        assert sanitize_case_id(" . Case . ") == "Case"

    def test_truncate_string_no_truncation(self):
        """Test string that doesn't need truncation."""
        text = "Short text"
        assert truncate_string(text, 50) == text

    def test_truncate_string_with_truncation(self):
        """Test string truncation."""
        text = "This is a very long string that needs truncation"
        result = truncate_string(text, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_string_custom_suffix(self):
        """Test custom suffix."""
        text = "This is a long string"
        result = truncate_string(text, 15, suffix=">>")
        assert len(result) == 15
        assert result.endswith(">>")

    def test_chunk_list(self):
        """Test list chunking."""
        data = [1, 2, 3, 4, 5, 6, 7]

        chunks = chunk_list(data, 3)
        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]
        assert chunks[1] == [4, 5, 6]
        assert chunks[2] == [7]

    def test_chunk_list_exact_fit(self):
        """Test chunking with exact fit."""
        data = [1, 2, 3, 4]
        chunks = chunk_list(data, 2)
        assert len(chunks) == 2
        assert chunks[0] == [1, 2]
        assert chunks[1] == [3, 4]
