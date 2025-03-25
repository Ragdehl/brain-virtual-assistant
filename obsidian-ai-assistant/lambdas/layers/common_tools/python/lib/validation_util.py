"""
Validation utility functions for Lambda functions.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from lib import ValidationError


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that all required fields are present in the data dictionary.
    
    Args:
        data: The data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        bool: True if all required fields are present, False otherwise
    """
    try:
        # Check if data is a dictionary
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")

        # Check each required field
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        # If any fields are missing, raise ValidationError
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        return True

    except ValidationError:
        # Re-raise ValidationError as is
        raise
    except Exception as e:
        # Convert other exceptions to ValidationError
        raise ValidationError(f"Validation error: {str(e)}") 


def validate_field_type(data: Dict[str, Any], field: str, expected_type: type) -> bool:
    """
    Validate that a field is of the expected type.

    Args:
        data (dict): Data to validate
        field (str): Field name
        expected_type (type): Expected type

    Returns:
        bool: True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    try:
        if field not in data:
            return True  # Skip validation if field is not present

        value = data[field]
        if not isinstance(value, expected_type):
            raise ValidationError(f"Field '{field}' must be of type {expected_type.__name__}")
        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


def validate_string_length(data: Dict[str, Any], field: str, min_length: int = 0, max_length: Optional[int] = None) -> bool:
    """
    Validate that a string field has a length within the specified range.

    Args:
        data (dict): Data to validate
        field (str): Field name
        min_length (int): Minimum length
        max_length (int, optional): Maximum length

    Returns:
        bool: True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    try:
        if field not in data or data[field] is None:
            return True  # Skip validation if field is not present

        value = data[field]
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field}' must be a string")

        if len(value) < min_length:
            raise ValidationError(f"Field '{field}' must be at least {min_length} characters long")

        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"Field '{field}' must be at most {max_length} characters long")

        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


def validate_numeric_range(data: Dict[str, Any], field: str, min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None) -> bool:
    """
    Validate that a numeric field is within the specified range.

    Args:
        data (dict): Data to validate
        field (str): Field name
        min_value (int/float, optional): Minimum value
        max_value (int/float, optional): Maximum value

    Returns:
        bool: True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    try:
        if field not in data or data[field] is None:
            return True  # Skip validation if field is not present

        value = data[field]
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Field '{field}' must be a number")

        if min_value is not None and value < min_value:
            raise ValidationError(f"Field '{field}' must be at least {min_value}")

        if max_value is not None and value > max_value:
            raise ValidationError(f"Field '{field}' must be at most {max_value}")

        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


def validate_regex(data: Dict[str, Any], field: str, pattern: str) -> bool:
    """
    Validate that a string field matches a regex pattern.

    Args:
        data (dict): Data to validate
        field (str): Field name
        pattern (str): Regex pattern

    Returns:
        bool: True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    try:
        if field not in data or data[field] is None:
            return True  # Skip validation if field is not present

        value = data[field]
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field}' must be a string")

        if not re.match(pattern, value):
            raise ValidationError(f"Field '{field}' does not match the required pattern")

        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


def validate_enum(data: Dict[str, Any], field: str, allowed_values: List[Any]) -> bool:
    """
    Validate that a field's value is one of the allowed values.

    Args:
        data (dict): Data to validate
        field (str): Field name
        allowed_values (list): List of allowed values

    Returns:
        bool: True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    try:
        if field not in data or data[field] is None:
            return True  # Skip validation if field is not present

        value = data[field]
        if value not in allowed_values:
            raise ValidationError(f"Field '{field}' must be one of: {', '.join(map(str, allowed_values))}")

        return True

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error: {str(e)}")


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
