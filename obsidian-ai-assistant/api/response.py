import json
from typing import Any, Dict, Optional, Union

def _create_response(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Create a standardized API Gateway response.
    
    Args:
        status_code (int): HTTP status code
        body (dict): Response body
        headers (dict, optional): Additional headers to include
        
    Returns:
        dict: Formatted API Gateway response
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Enable CORS
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

def success_response(status_code: int = 200, data: Optional[Any] = None, message: Optional[str] = None) -> Dict[str, Any]:
    """Format a successful API response.
    
    Args:
        status_code (int): HTTP status code (default: 200)
        data (Any, optional): Response data
        message (str, optional): Success message
        
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
        
    return _create_response(status_code, body)

def error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Union[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Format an error API response.
    
    Args:
        status_code (int): HTTP status code
        message (str): Error message
        error_code (str, optional): Error code for client reference
        details (Union[str, dict], optional): Additional error details
        
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
        
    return _create_response(status_code, body)

def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format a validation error response.
    
    Args:
        message (str): Validation error message
        details (dict, optional): Validation error details
        
    Returns:
        dict: Formatted validation error response
    """
    return error_response(
        400,
        message,
        error_code="VALIDATION_ERROR",
        details=details
    ) 