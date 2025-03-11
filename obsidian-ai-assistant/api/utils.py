import json
import logging
import os
from typing import Any, Dict, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_request(event: Dict[str, Any]) -> None:
    """Log API request details.
    
    Args:
        event (dict): API Gateway event
    """
    # Create a sanitized copy of the event to avoid logging sensitive data
    sanitized_event = event.copy()
    
    # Remove sensitive headers
    if "headers" in sanitized_event:
        headers = sanitized_event["headers"].copy()
        sensitive_headers = ["Authorization", "X-Api-Key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"
        sanitized_event["headers"] = headers
    
    logger.info(f"API Request: {json.dumps(sanitized_event, indent=2)}")

def get_config(param_name: str, default: Optional[Any] = None) -> Any:
    """Get configuration value from environment variable or default.
    
    Args:
        param_name (str): Parameter name
        default (Any, optional): Default value if not found
        
    Returns:
        Any: Configuration value
    """
    return os.environ.get(param_name, default)

def validate_request_body(body: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate request body has all required fields.
    
    Args:
        body (dict): Request body to validate
        required_fields (list): List of required field names
        
    Returns:
        str: Error message if validation fails, None if successful
    """
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None

def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent injection attacks.
    
    Args:
        value (str): String to sanitize
        
    Returns:
        str: Sanitized string
    """
    # Remove any control characters
    return ''.join(char for char in value if ord(char) >= 32)

def parse_query_params(params: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """Parse and validate query parameters.
    
    Args:
        params (dict): Query parameters from API Gateway event
        
    Returns:
        dict: Parsed and validated parameters
    """
    if not params:
        return {}
        
    result = {}
    
    # Parse pagination parameters
    if 'limit' in params:
        try:
            result['limit'] = min(int(params['limit']), 100)  # Max 100 items per page
        except ValueError:
            result['limit'] = 10  # Default limit
    
    if 'cursor' in params:
        result['cursor'] = sanitize_string(params['cursor'])
    
    # Parse search parameters
    if 'query' in params:
        result['query'] = sanitize_string(params['query'])
    
    if 'tags' in params:
        result['tags'] = [
            sanitize_string(tag.strip())
            for tag in params['tags'].split(',')
            if tag.strip()
        ]
    
    return result 