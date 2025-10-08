"""Unit tests for validation functions."""

import pytest
from pathlib import Path

from elrond.utils.validators import (
    ValidationError,
    validate_mode_flags,
    validate_memory_options,
    validate_analysis_options,
    validate_navigator_options,
    validate_nsrl_options,
    sanitize_case_id,
)


class TestModeValidation:
    """Test mode flag validation."""

    def test_validate_mode_collect(self):
        """Test collect mode validation."""
        mode = validate_mode_flags(collect=True, gandalf=False, reorganise=False)
        assert mode == "collect"

    def test_validate_mode_gandalf(self):
        """Test gandalf mode validation."""
        mode = validate_mode_flags(collect=False, gandalf=True, reorganise=False)
        assert mode == "gandalf"

    def test_validate_mode_reorganise(self):
        """Test reorganise mode validation."""
        mode = validate_mode_flags(collect=False, gandalf=False, reorganise=True)
        assert mode == "reorganise"

    def test_validate_mode_none_selected(self):
        """Test error when no mode selected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_mode_flags(collect=False, gandalf=False, reorganise=False)
        assert "MUST use one of" in str(exc_info.value)

    def test_validate_mode_multiple_selected(self):
        """Test error when multiple modes selected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_mode_flags(collect=True, gandalf=True, reorganise=False)
        assert "multiple mode flags" in str(exc_info.value)


class TestMemoryOptions:
    """Test memory-related option validation."""

    def test_memory_requires_process(self):
        """Test that memory analysis requires process flag."""
        # Should raise error
        with pytest.raises(ValidationError) as exc_info:
            validate_memory_options(volatility=True, process=False, memorytimeline=False)
        assert "requires the process flag" in str(exc_info.value)

    def test_memory_with_process_valid(self):
        """Test valid memory + process combination."""
        # Should not raise
        validate_memory_options(volatility=True, process=True, memorytimeline=False)

    def test_memorytimeline_requires_volatility(self):
        """Test that memory timeline requires volatility."""
        with pytest.raises(ValidationError) as exc_info:
            validate_memory_options(volatility=False, process=True, memorytimeline=True)
        assert "requires the volatility flag" in str(exc_info.value)

    def test_valid_memory_timeline(self):
        """Test valid memory timeline configuration."""
        # Should not raise
        validate_memory_options(volatility=True, process=True, memorytimeline=True)


class TestAnalysisOptions:
    """Test analysis option validation."""

    def test_analysis_requires_process(self):
        """Test that analysis requires process flag."""
        with pytest.raises(ValidationError) as exc_info:
            validate_analysis_options(analysis=True, process=False)
        assert "requires the process flag" in str(exc_info.value)

    def test_analysis_with_process_valid(self):
        """Test valid analysis + process combination."""
        # Should not raise
        validate_analysis_options(analysis=True, process=True)

    def test_no_analysis_valid(self):
        """Test that no analysis is valid."""
        validate_analysis_options(analysis=False, process=False)
        validate_analysis_options(analysis=False, process=True)


class TestNavigatorOptions:
    """Test MITRE Navigator option validation."""

    def test_navigator_requires_splunk(self):
        """Test that Navigator requires Splunk."""
        with pytest.raises(ValidationError) as exc_info:
            validate_navigator_options(navigator=True, splunk=False)
        assert "requires Splunk" in str(exc_info.value)

    def test_navigator_with_splunk_valid(self):
        """Test valid Navigator + Splunk combination."""
        # Should not raise
        validate_navigator_options(navigator=True, splunk=True)

    def test_no_navigator_valid(self):
        """Test that no Navigator is valid."""
        validate_navigator_options(navigator=False, splunk=False)
        validate_navigator_options(navigator=False, splunk=True)


class TestNSRLOptions:
    """Test NSRL option validation."""

    def test_nsrl_quick_without_metacollected(self):
        """Test that NSRL + quick without metacollected is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            validate_nsrl_options(
                metacollected=False, nsrl=True, superquick=True, quick=False
            )
        assert "requires metacollected" in str(exc_info.value)

    def test_nsrl_quick_with_metacollected_valid(self):
        """Test valid NSRL + quick + metacollected combination."""
        # Should not raise
        validate_nsrl_options(
            metacollected=True, nsrl=True, superquick=True, quick=False
        )

    def test_nsrl_without_quick_valid(self):
        """Test NSRL without quick flags is valid."""
        # Should not raise
        validate_nsrl_options(metacollected=False, nsrl=True, superquick=False, quick=False)
