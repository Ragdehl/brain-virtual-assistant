"""
Logging utility functions for Lambda functions.
"""
import json
import logging
import os
from typing import Any, Dict, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def sanitize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive information from an API Gateway event.

    Args:
        event (dict): API Gateway event

    Returns:
        dict: Sanitized event
    """
    sanitized_event = event.copy()

    # Sanitize headers
    if "headers" in sanitized_event:
        headers = sanitized_event["headers"].copy()
        sensitive_headers = ["Authorization", "X-Api-Key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"
        sanitized_event["headers"] = headers

    # Sanitize request body if it contains sensitive information
    if "body" in sanitized_event and sanitized_event["body"]:
        try:
            body = json.loads(sanitized_event["body"])
            if isinstance(body, dict):
                sensitive_fields = ["password", "apiKey", "token", "secret"]
                for field in sensitive_fields:
                    if field in body:
                        body[field] = "[REDACTED]"
                sanitized_event["body"] = json.dumps(body)
        except (json.JSONDecodeError, TypeError):
            # If body is not valid JSON, leave it as is
            pass

    return sanitized_event


def log_event(event: Dict[str, Any], context: Optional[Any] = None) -> None:
    """
    Log an API Gateway event with sensitive information redacted.

    Args:
        event (dict): API Gateway event
        context (object, optional): Lambda context
    """
    sanitized_event = sanitize_event(event)

    # Extract useful information for structured logging
    method = sanitized_event.get("httpMethod", "UNKNOWN")
    path = sanitized_event.get("path", "UNKNOWN")
    query_params = sanitized_event.get("queryStringParameters", {})
    source_ip = sanitized_event.get("requestContext", {}).get("identity", {}).get("sourceIp", "UNKNOWN")

    # Create structured log entry
    log_entry = {
        "method": method,
        "path": path,
        "sourceIp": source_ip,
        "queryParams": query_params,
        "event": sanitized_event
    }

    # Add request ID from context if available
    if context:
        log_entry["requestId"] = getattr(context, "aws_request_id", "UNKNOWN")

    logger.info(f"API Request: {json.dumps(log_entry)}")


def log_response(response: Dict[str, Any]) -> None:
    """
    Log an API Gateway response.

    Args:
        response (dict): API Gateway response
    """
    status_code = response.get("statusCode", 0)

    # Parse body if it's a string
    body = response.get("body", "{}")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {"raw": body}

    # Create structured log entry
    log_entry = {
        "statusCode": status_code,
        "isSuccess": 200 <= status_code < 300,
        "bodySize": len(response.get("body", "")) if isinstance(response.get("body"), str) else 0,
        "hasError": "error" in body if isinstance(body, dict) else False
    }

    logger.info(f"API Response: {json.dumps(log_entry)}")


def log_error(error: Exception, context: Optional[Any] = None) -> None:
    """
    Log an exception with context information.

    Args:
        error (Exception): The exception to log
        context (object, optional): Lambda context
    """
    error_type = type(error).__name__
    error_message = str(error)

    # Create structured log entry
    log_entry = {
        "errorType": error_type,
        "errorMessage": error_message
    }

    # Add request ID from context if available
    if context:
        log_entry["requestId"] = getattr(context, "aws_request_id", "UNKNOWN")

    logger.error(f"Error: {json.dumps(log_entry)}", exc_info=True)
