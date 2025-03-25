"""
API utility functions for Lambda handlers.

This module provides utilities for handling Lambda function responses to API Gateway
and standardizing error handling across Lambda functions.
"""
import functools
import json
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast, get_type_hints

from .logging_util import log_event, log_response, log_error
from .response_util import (
    success_response,
    error_response,
    validation_error,
    not_found_error,
    unauthorized_error,
    server_error
)

# Define type variables for the decorator
F = TypeVar('F', bound=Callable[..., Dict[str, Any]])
EventType = Dict[str, Any]
ContextType = Any


class ApiError(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code for client reference
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class ValidationError(ApiError):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the validation error.
        
        Args:
            message: Validation error message
            details: Validation error details
        """
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(ApiError):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str = "Resource not found"
    ):
        """
        Initialize the not found error.
        
        Args:
            message: Not found error message
        """
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )


class UnauthorizedError(ApiError):
    """Exception for unauthorized access errors."""
    
    def __init__(
        self,
        message: str = "Unauthorized"
    ):
        """
        Initialize the unauthorized error.
        
        Args:
            message: Unauthorized error message
        """
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )


class ServerError(ApiError):
    """Exception for server errors."""
    
    def __init__(
        self,
        message: str = "Internal server error"
    ):
        """
        Initialize the server error.
        
        Args:
            message: Server error message
        """
        super().__init__(
            message=message,
            status_code=500,
            error_code="SERVER_ERROR"
        )


def _extract_path_parameters(event: EventType, required_params: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Extract all path parameters from the event.
    
    Args:
        event: The Lambda event
        required_params: List of required parameter names
        
    Returns:
        Dictionary of path parameters
        
    Raises:
        ValidationError: If any required parameters are missing
    """
    try:
        path_parameters = event.get('pathParameters', {}) or {}
        
        # Check for required parameters
        if required_params:
            missing_params = [param for param in required_params if param not in path_parameters]
            if missing_params:
                raise ValidationError(
                    f"Missing required path parameters: {', '.join(missing_params)}"
                )
        
        return path_parameters
    except (AttributeError, TypeError):
        raise ValidationError("Invalid or missing path parameters")


def _extract_query_parameters(event: EventType, required_params: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Extract all query parameters from the event.
    
    Args:
        event: The Lambda event
        required_params: List of required parameter names
        
    Returns:
        Dictionary of query parameters
        
    Raises:
        ValidationError: If any required parameters are missing
    """
    try:
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        # Check for required parameters
        if required_params:
            missing_params = [param for param in required_params if param not in query_parameters]
            if missing_params:
                raise ValidationError(
                    f"Missing required query parameters: {', '.join(missing_params)}"
                )
        
        return query_parameters
    except (AttributeError, TypeError):
        raise ValidationError("Invalid or missing query parameters")


def api_handler(
    func: Optional[F] = None,
    *,
    extract_path_params: bool = False,
    extract_query_params: bool = False,
    extract_user_id_param: bool = False,
    extract_body_param: bool = False,
    required_path_params: Optional[List[str]] = None,
    required_query_params: Optional[List[str]] = None,
    required_body: bool = False
) -> Union[F, Callable[[F], F]]:
    """
    Decorator for Lambda handlers that standardizes API Gateway responses and error handling.
    
    This decorator:
    1. Logs the incoming event
    2. Extracts and validates parameters (path, query, body, user ID)
    3. Handles exceptions and converts them to appropriate API responses
    4. Logs the response
    5. Formats the response for API Gateway
    
    Args:
        func: The Lambda handler function to decorate
        extract_path_params: Whether to extract path parameters
        extract_query_params: Whether to extract query parameters
        extract_user_id_param: Whether to extract user ID
        extract_body_param: Whether to extract request body
        required_path_params: List of required path parameters
        required_query_params: List of required query parameters
        required_body: Whether the request body is required
        
    Returns:
        The decorated function
    """
    def decorator(handler_func: F) -> F:
        @functools.wraps(handler_func)
        def wrapper(event: EventType, context: ContextType) -> Dict[str, Any]:
            try:
                # Log the incoming event
                log_event(event, context)
                
                # Prepare parameters to pass to the handler function
                kwargs = {}
                
                # Extract path parameters if requested
                if extract_path_params:
                    path_params = _extract_path_parameters(event, required_path_params)
                    
                    # Check if the function has a parameter named exactly "path_params"
                    # If so, pass all path parameters as a dictionary
                    # Otherwise, try to map each path parameter to a function parameter
                    if "path_params" in get_type_hints(handler_func):
                        kwargs["path_params"] = path_params
                    else:
                        for param_name, param_value in path_params.items():
                            kwargs[param_name] = param_value
                
                # Extract query parameters if requested
                if extract_query_params:
                    query_params = _extract_query_parameters(event, required_query_params)
                    
                    # Similar logic as with path parameters
                    if "query_params" in get_type_hints(handler_func):
                        kwargs["query_params"] = query_params
                    else:
                        for param_name, param_value in query_params.items():
                            kwargs[param_name] = param_value
                
                # Extract user ID if requested
                if extract_user_id_param:
                    kwargs["user_id"] = extract_user_id(event)
                
                # Extract request body if requested
                if extract_body_param:
                    kwargs["body"] = extract_body(event, required=required_body)
                
                # Always pass context
                kwargs["context"] = context
                
                # If not using any parameter extraction, pass the event as is
                if not any([extract_path_params, extract_query_params, extract_user_id_param, extract_body_param]):
                    kwargs = {"event": event, "context": context}
                
                # Call the handler function with extracted parameters
                result = handler_func(**kwargs)
                
                # Process the result:
                # 1. If it's already a full API Gateway response (with statusCode and body), return it directly
                # 2. If it contains special fields like 'statusCode', 'headers', etc., extract and use them
                # 3. Otherwise, wrap it in a standard success response
                
                # Check if it's a complete API Gateway response
                if isinstance(result, dict) and all(k in result for k in ['statusCode', 'headers', 'body']):
                    log_response(result)
                    return result
                
                # Extract special fields if present
                status_code = result.pop('statusCode', 200) if isinstance(result, dict) else 200
                message = result.pop('message', None) if isinstance(result, dict) else None
                headers = result.pop('headers', None) if isinstance(result, dict) else None
                
                # Create a success response with the remaining data
                response = success_response(
                    status_code=status_code,
                    data=result,
                    message=message,
                    headers=headers
                )
                
                log_response(response)
                return response
                
            except ValidationError as e:
                response = validation_error(e.message, e.details)
                log_error(f"Validation error: {e.message}", event, context)
                return response
                
            except NotFoundError as e:
                response = not_found_error(e.message)
                log_error(f"Not found error: {e.message}", event, context)
                return response
                
            except UnauthorizedError as e:
                response = unauthorized_error(e.message)
                log_error(f"Unauthorized error: {e.message}", event, context)
                return response
                
            except ApiError as e:
                response = error_response(
                    e.status_code,
                    e.message,
                    e.error_code,
                    e.details
                )
                log_error(f"API error: {e.message}", event, context)
                return response
                
            except Exception as e:
                # Get the stack trace
                stack_trace = traceback.format_exc()
                
                # Log the error with stack trace
                log_error(f"Unhandled exception: {str(e)}\n{stack_trace}", event, context)
                
                # Return a server error response
                return server_error(str(e))
        
        return cast(F, wrapper)
    
    # Handle both @api_handler and @api_handler() syntax
    if func is None:
        return decorator
    return decorator(func)


def extract_path_parameter(event: Dict[str, Any], param_name: str) -> str:
    """
    Extract a path parameter from the event.
    
    Args:
        event: The Lambda event
        param_name: The name of the path parameter
        
    Returns:
        The path parameter value
        
    Raises:
        ValidationError: If the path parameter is missing
    """
    try:
        path_parameters = event.get('pathParameters', {}) or {}
        param_value = path_parameters.get(param_name)
        
        if not param_value:
            raise ValidationError(f"Missing {param_name} in path parameters")
            
        return param_value
    except (AttributeError, TypeError):
        raise ValidationError(f"Invalid or missing path parameters")


def extract_query_parameter(
    event: Dict[str, Any],
    param_name: str,
    required: bool = False,
    default: Any = None
) -> Any:
    """
    Extract a query parameter from the event.
    
    Args:
        event: The Lambda event
        param_name: The name of the query parameter
        required: Whether the parameter is required
        default: Default value if the parameter is not provided
        
    Returns:
        The query parameter value or default
        
    Raises:
        ValidationError: If the parameter is required but missing
    """
    try:
        query_parameters = event.get('queryStringParameters', {}) or {}
        param_value = query_parameters.get(param_name, default)
        
        if required and param_value is None:
            raise ValidationError(f"Missing required query parameter: {param_name}")
            
        return param_value
    except (AttributeError, TypeError):
        if required:
            raise ValidationError(f"Invalid or missing query parameters")
        return default


def extract_body(event: Dict[str, Any], required: bool = True) -> Dict[str, Any]:
    """
    Extract and parse the request body from the event.
    
    Args:
        event: The Lambda event
        required: Whether the body is required
        
    Returns:
        The parsed request body
        
    Raises:
        ValidationError: If the body is required but missing or invalid
    """
    try:
        body = event.get('body')
        
        if not body:
            if required:
                raise ValidationError("Missing request body")
            return {}
            
        if isinstance(body, str):
            return json.loads(body)
        elif isinstance(body, dict):
            return body
        else:
            raise ValidationError("Invalid request body format")
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON in request body")
    except (AttributeError, TypeError):
        if required:
            raise ValidationError("Invalid or missing request body")
        return {}


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract the user ID from the event.
    
    Args:
        event: The Lambda event
        
    Returns:
        The user ID
        
    Raises:
        UnauthorizedError: If the user ID is missing
    """
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        user_id = authorizer.get('userId')
        
        if not user_id:
            raise UnauthorizedError("User ID is required")
            
        return user_id
    except (AttributeError, TypeError):
        raise UnauthorizedError("Invalid or missing authorization context") 