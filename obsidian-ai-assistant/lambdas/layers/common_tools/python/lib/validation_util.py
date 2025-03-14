"""
Validation utility functions for Lambda functions.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that all required fields are present in the data.

    Args:
        data (dict): Data to validate
        required_fields (list): List of required field names

    Returns:
        tuple: (is_valid, error_message)
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, None


def validate_field_type(data: Dict[str, Any], field: str, expected_type: type) -> Tuple[bool, Optional[str]]:
    """
    Validate that a field is of the expected type.

    Args:
        data (dict): Data to validate
        field (str): Field name
        expected_type (type): Expected type

    Returns:
        tuple: (is_valid, error_message)
    """
    if field not in data:
        return True, None  # Skip validation if field is not present

    value = data[field]
    if not isinstance(value, expected_type):
        return False, f"Field '{field}' must be of type {expected_type.__name__}"
    return True, None


def validate_string_length(data: Dict[str, Any], field: str, min_length: int = 0, max_length: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that a string field has a length within the specified range.

    Args:
        data (dict): Data to validate
        field (str): Field name
        min_length (int): Minimum length
        max_length (int, optional): Maximum length

    Returns:
        tuple: (is_valid, error_message)
    """
    if field not in data or data[field] is None:
        return True, None  # Skip validation if field is not present

    value = data[field]
    if not isinstance(value, str):
        return False, f"Field '{field}' must be a string"

    if len(value) < min_length:
        return False, f"Field '{field}' must be at least {min_length} characters long"

    if max_length is not None and len(value) > max_length:
        return False, f"Field '{field}' must be at most {max_length} characters long"

    return True, None


def validate_numeric_range(data: Dict[str, Any], field: str, min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that a numeric field is within the specified range.

    Args:
        data (dict): Data to validate
        field (str): Field name
        min_value (int/float, optional): Minimum value
        max_value (int/float, optional): Maximum value

    Returns:
        tuple: (is_valid, error_message)
    """
    if field not in data or data[field] is None:
        return True, None  # Skip validation if field is not present

    value = data[field]
    if not isinstance(value, (int, float)):
        return False, f"Field '{field}' must be a number"

    if min_value is not None and value < min_value:
        return False, f"Field '{field}' must be at least {min_value}"

    if max_value is not None and value > max_value:
        return False, f"Field '{field}' must be at most {max_value}"

    return True, None


def validate_regex(data: Dict[str, Any], field: str, pattern: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a string field matches a regex pattern.

    Args:
        data (dict): Data to validate
        field (str): Field name
        pattern (str): Regex pattern

    Returns:
        tuple: (is_valid, error_message)
    """
    if field not in data or data[field] is None:
        return True, None  # Skip validation if field is not present

    value = data[field]
    if not isinstance(value, str):
        return False, f"Field '{field}' must be a string"

    if not re.match(pattern, value):
        return False, f"Field '{field}' does not match the required pattern"

    return True, None


def validate_enum(data: Dict[str, Any], field: str, allowed_values: List[Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate that a field's value is one of the allowed values.

    Args:
        data (dict): Data to validate
        field (str): Field name
        allowed_values (list): List of allowed values

    Returns:
        tuple: (is_valid, error_message)
    """
    if field not in data or data[field] is None:
        return True, None  # Skip validation if field is not present

    value = data[field]
    if value not in allowed_values:
        return False, f"Field '{field}' must be one of: {', '.join(map(str, allowed_values))}"

    return True, None


def validate_json_string(json_string: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate that a string is valid JSON and parse it.

    Args:
        json_string (str): JSON string to validate

    Returns:
        tuple: (is_valid, parsed_json, error_message)
    """
    if not json_string:
        return False, None, "JSON string is empty"

    try:
        parsed_json = json.loads(json_string)
        return True, parsed_json, None
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing control characters.

    Args:
        value (str): String to sanitize

    Returns:
        str: Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Remove control characters
    return ''.join(char for char in value if ord(char) >= 32)


def validate_request_body(event: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and parse the request body from an API Gateway event.

    Args:
        event (dict): API Gateway event

    Returns:
        tuple: (is_valid, parsed_body, error_message)
    """
    body = event.get("body")
    if not body:
        return False, None, "Request body is required"

    return validate_json_string(body) 