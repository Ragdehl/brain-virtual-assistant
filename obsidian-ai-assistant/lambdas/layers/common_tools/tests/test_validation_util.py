"""
Pytest tests for validation utilities in the common tools layer.
"""
import sys
import os
import pytest
from typing import Dict, Any, List

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))

from lib.validation_util import (
    validate_required_fields,
    validate_string_length,
    validate_field_type,
    validate_numeric_range,
    validate_regex,
    validate_enum
)
from lib.exceptions import ValidationError


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "string_field": "test string",
        "int_field": 42,
        "float_field": 3.14,
        "bool_field": True,
        "list_field": [1, 2, 3],
        "dict_field": {"key": "value"}
    }


class TestValidateRequiredFields:
    """Tests for the validate_required_fields function."""

    def test_validate_required_fields_success(self, sample_data):
        """Test validate_required_fields with valid data."""
        # Test with a single required field
        result = validate_required_fields(sample_data, ["string_field"])
        assert result is True

        # Test with multiple required fields
        result = validate_required_fields(sample_data, ["string_field", "int_field", "float_field"])
        assert result is True

    def test_validate_required_fields_missing(self, sample_data):
        """Test validate_required_fields with missing fields."""
        with pytest.raises(ValidationError) as excinfo:
            validate_required_fields(sample_data, ["missing_field"])
        assert "Missing required fields" in str(excinfo.value)
        assert "missing_field" in str(excinfo.value)

        # Test with one existing and one missing field
        with pytest.raises(ValidationError) as excinfo:
            validate_required_fields(sample_data, ["string_field", "missing_field"])
        assert "Missing required fields" in str(excinfo.value)
        assert "missing_field" in str(excinfo.value)
        assert "string_field" not in str(excinfo.value)

    def test_validate_required_fields_not_dict(self):
        """Test validate_required_fields with non-dict data."""
        with pytest.raises(ValidationError) as excinfo:
            validate_required_fields("not a dict", ["field"])
        assert "Data must be a dictionary" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_required_fields(None, ["field"])
        assert "Data must be a dictionary" in str(excinfo.value)

    def test_validate_required_fields_empty(self, sample_data):
        """Test validate_required_fields with empty required fields."""
        # Empty required fields should pass
        result = validate_required_fields(sample_data, [])
        assert result is True


class TestValidateStringLength:
    """Tests for the validate_string_length function."""

    def test_validate_string_length_success(self, sample_data):
        """Test validate_string_length with valid strings."""
        # Test with min_length only
        result = validate_string_length(sample_data, "string_field", min_length=1)
        assert result is True

        # Test with max_length only
        result = validate_string_length(sample_data, "string_field", max_length=20)
        assert result is True

        # Test with both min and max length
        result = validate_string_length(sample_data, "string_field", min_length=1, max_length=20)
        assert result is True

        # Test with exact length
        result = validate_string_length(sample_data, "string_field", min_length=11, max_length=11)
        assert result is True

    def test_validate_string_length_invalid(self, sample_data):
        """Test validate_string_length with invalid strings."""
        # Too short
        with pytest.raises(ValidationError) as excinfo:
            validate_string_length(sample_data, "string_field", min_length=20)
        assert "must be at least" in str(excinfo.value)

        # Too long
        with pytest.raises(ValidationError) as excinfo:
            validate_string_length(sample_data, "string_field", max_length=5)
        assert "must be at most" in str(excinfo.value)

    def test_validate_string_length_missing_field(self, sample_data):
        """Test validate_string_length with missing field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_string_length(sample_data, "missing_field", min_length=1)
        assert "Field 'missing_field' is required" in str(excinfo.value)

    def test_validate_string_length_not_string(self, sample_data):
        """Test validate_string_length with non-string field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_string_length(sample_data, "int_field", min_length=1)
        assert "Field 'int_field' must be a string" in str(excinfo.value)


class TestValidateFieldType:
    """Tests for the validate_field_type function."""

    def test_validate_field_type_success(self, sample_data):
        """Test validate_field_type with valid types."""
        # Test with string
        result = validate_field_type(sample_data, "string_field", str)
        assert result is True

        # Test with int
        result = validate_field_type(sample_data, "int_field", int)
        assert result is True

        # Test with float
        result = validate_field_type(sample_data, "float_field", float)
        assert result is True

        # Test with bool
        result = validate_field_type(sample_data, "bool_field", bool)
        assert result is True

        # Test with list
        result = validate_field_type(sample_data, "list_field", list)
        assert result is True

        # Test with dict
        result = validate_field_type(sample_data, "dict_field", dict)
        assert result is True

        # Test with multiple types (int or float)
        result = validate_field_type(sample_data, "int_field", (int, float))
        assert result is True
        result = validate_field_type(sample_data, "float_field", (int, float))
        assert result is True

    def test_validate_field_type_invalid(self, sample_data):
        """Test validate_field_type with invalid types."""
        with pytest.raises(ValidationError) as excinfo:
            validate_field_type(sample_data, "string_field", int)
        assert "must be of type" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_field_type(sample_data, "int_field", str)
        assert "must be of type" in str(excinfo.value)

    def test_validate_field_type_missing_field(self, sample_data):
        """Test validate_field_type with missing field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_field_type(sample_data, "missing_field", str)
        assert "Field 'missing_field' is required" in str(excinfo.value)


class TestValidateNumericRange:
    """Tests for the validate_numeric_range function."""

    def test_validate_numeric_range_success(self, sample_data):
        """Test validate_numeric_range with valid numbers."""
        # Test with min_value only
        result = validate_numeric_range(sample_data, "int_field", min_value=0)
        assert result is True

        # Test with max_value only
        result = validate_numeric_range(sample_data, "int_field", max_value=100)
        assert result is True

        # Test with both min and max value
        result = validate_numeric_range(sample_data, "int_field", min_value=0, max_value=100)
        assert result is True

        # Test with exact value
        result = validate_numeric_range(sample_data, "int_field", min_value=42, max_value=42)
        assert result is True

        # Test with float
        result = validate_numeric_range(sample_data, "float_field", min_value=0, max_value=5)
        assert result is True

    def test_validate_numeric_range_invalid(self, sample_data):
        """Test validate_numeric_range with invalid numbers."""
        # Too small
        with pytest.raises(ValidationError) as excinfo:
            validate_numeric_range(sample_data, "int_field", min_value=100)
        assert "must be at least" in str(excinfo.value)

        # Too large
        with pytest.raises(ValidationError) as excinfo:
            validate_numeric_range(sample_data, "int_field", max_value=10)
        assert "must be at most" in str(excinfo.value)

    def test_validate_numeric_range_missing_field(self, sample_data):
        """Test validate_numeric_range with missing field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_numeric_range(sample_data, "missing_field", min_value=0)
        assert "Field 'missing_field' is required" in str(excinfo.value)

    def test_validate_numeric_range_not_number(self, sample_data):
        """Test validate_numeric_range with non-numeric field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_numeric_range(sample_data, "string_field", min_value=0)
        assert "Field 'string_field' must be a number" in str(excinfo.value)


class TestValidateRegex:
    """Tests for the validate_regex function."""

    def test_validate_regex_success(self, sample_data):
        """Test validate_regex with valid patterns."""
        # Test with simple pattern
        result = validate_regex(sample_data, "string_field", r"test")
        assert result is True

        # Test with start and end anchors
        result = validate_regex(sample_data, "string_field", r"^test string$")
        assert result is True

        # Test with character class
        result = validate_regex(sample_data, "string_field", r"^[a-z\s]+$")
        assert result is True

    def test_validate_regex_invalid(self, sample_data):
        """Test validate_regex with invalid patterns."""
        with pytest.raises(ValidationError) as excinfo:
            validate_regex(sample_data, "string_field", r"pattern_not_found")
        assert "must match the pattern" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_regex(sample_data, "string_field", r"^invalid$")
        assert "must match the pattern" in str(excinfo.value)

    def test_validate_regex_missing_field(self, sample_data):
        """Test validate_regex with missing field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_regex(sample_data, "missing_field", r"test")
        assert "Field 'missing_field' is required" in str(excinfo.value)

    def test_validate_regex_not_string(self, sample_data):
        """Test validate_regex with non-string field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_regex(sample_data, "int_field", r"test")
        assert "Field 'int_field' must be a string" in str(excinfo.value)


class TestValidateEnum:
    """Tests for the validate_enum function."""

    def test_validate_enum_success(self, sample_data):
        """Test validate_enum with valid values."""
        # Test with string in allowed values
        result = validate_enum(sample_data, "string_field", ["test string", "other value"])
        assert result is True

        # Test with int in allowed values
        result = validate_enum(sample_data, "int_field", [0, 42, 100])
        assert result is True

        # Test with mixed types in allowed values
        result = validate_enum(sample_data, "int_field", ["string", 42, True])
        assert result is True

    def test_validate_enum_invalid(self, sample_data):
        """Test validate_enum with invalid values."""
        with pytest.raises(ValidationError) as excinfo:
            validate_enum(sample_data, "string_field", ["not in enum", "other value"])
        assert "must be one of" in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validate_enum(sample_data, "int_field", [0, 1, 2])
        assert "must be one of" in str(excinfo.value)

    def test_validate_enum_missing_field(self, sample_data):
        """Test validate_enum with missing field."""
        with pytest.raises(ValidationError) as excinfo:
            validate_enum(sample_data, "missing_field", ["value1", "value2"])
        assert "Field 'missing_field' is required" in str(excinfo.value)

    def test_validate_enum_empty_allowed_values(self, sample_data):
        """Test validate_enum with empty allowed values."""
        with pytest.raises(ValidationError) as excinfo:
            validate_enum(sample_data, "string_field", [])
        assert "Allowed values cannot be empty" in str(excinfo.value) 