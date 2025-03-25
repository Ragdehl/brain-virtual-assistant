"""
Response utility functions for Lambda functions.
"""
import json
from typing import Any, Dict, Optional, Union


def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.

    Args:
        status_code (int): HTTP status code
        body (dict): Response body
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted API Gateway response
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Api-Key,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE"
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body)
    }


def success_response(
    status_code: int = 200,
    data: Optional[Any] = None,
    message: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format a successful API response.

    Args:
        status_code (int): HTTP status code (default: 200)
        data (Any, optional): Response data
        message (str, optional): Success message
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted success response
    """
    body = {
        "success": True
    }

    if data is not None:
        body["data"] = data
    if message:
        body["message"] = message

    return create_response(status_code, body, headers)


def error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Union[str, Dict[str, Any]]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format an error API response.

    Args:
        status_code (int): HTTP status code
        message (str): Error message
        error_code (str, optional): Error code for client reference
        details (Union[str, dict], optional): Additional error details
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted error response
    """
    body = {
        "success": False,
        "error": {
            "message": message
        }
    }

    if error_code:
        body["error"]["code"] = error_code
    if details:
        body["error"]["details"] = details

    return create_response(status_code, body, headers)


def validation_error(
    message: str,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format a validation error response.

    Args:
        message (str): Validation error message
        details (dict, optional): Validation error details
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted validation error response
    """
    return error_response(
        400,
        message,
        error_code="VALIDATION_ERROR",
        details=details,
        headers=headers
    )


def not_found_error(
    message: str = "Resource not found",
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format a not found error response.

    Args:
        message (str): Not found error message
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted not found error response
    """
    return error_response(
        404,
        message,
        error_code="NOT_FOUND",
        headers=headers
    )


def unauthorized_error(
    message: str = "Unauthorized",
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format an unauthorized error response.

    Args:
        message (str): Unauthorized error message
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted unauthorized error response
    """
    return error_response(
        401,
        message,
        error_code="UNAUTHORIZED",
        headers=headers
    )


def server_error(
    message: str = "Internal server error",
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format a server error response.

    Args:
        message (str): Server error message
        headers (dict, optional): Additional headers to include

    Returns:
        dict: Formatted server error response
    """
    return error_response(
        500,
        message,
        error_code="SERVER_ERROR",
        headers=headers
    )
