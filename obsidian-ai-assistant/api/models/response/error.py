"""
Error response models.
"""
from typing import Any, Dict, Optional, Union


def format_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Union[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Format an error response.

    Args:
        message (str): Error message
        error_code (str, optional): Error code
        details (Union[str, dict], optional): Additional error details

    Returns:
        dict: Formatted error response
    """
    error = {
        "message": message
    }

    if error_code:
        error["code"] = error_code

    if details:
        error["details"] = details

    return {
        "success": False,
        "error": error
    }


# Common error responses
VALIDATION_ERROR = {
    "code": "VALIDATION_ERROR",
    "message": "Validation error"
}

NOT_FOUND_ERROR = {
    "code": "NOT_FOUND",
    "message": "Resource not found"
}

UNAUTHORIZED_ERROR = {
    "code": "UNAUTHORIZED",
    "message": "Unauthorized"
}

SERVER_ERROR = {
    "code": "SERVER_ERROR",
    "message": "Internal server error"
}
