"""
Common tools for Lambda functions.
"""
from .dynamodb_util import DynamoDBUtil
from .logging_util import log_error, log_event, log_response, sanitize_event
from .response_util import (
    error_response,
    not_found_error,
    server_error,
    success_response,
    unauthorized_error,
    validation_error,
)
from .s3_util import S3Util
from .validation_util import (
    sanitize_string,
    validate_enum,
    validate_field_type,
    validate_json_string,
    validate_numeric_range,
    validate_regex,
    validate_request_body,
    validate_required_fields,
    validate_string_length,
)
from .api_util import (
    api_handler,
    ApiError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ServerError,
    extract_path_parameter,
    extract_query_parameter,
    extract_body,
    extract_user_id,
)

__all__ = [
    # DynamoDB utilities
    "DynamoDBUtil",

    # Logging utilities
    "log_event",
    "log_response",
    "log_error",
    "sanitize_event",

    # Response utilities
    "success_response",
    "error_response",
    "validation_error",
    "not_found_error",
    "unauthorized_error",
    "server_error",

    # S3 utilities
    "S3Util",

    # Validation utilities
    "validate_required_fields",
    "validate_field_type",
    "validate_string_length",
    "validate_numeric_range",
    "validate_regex",
    "validate_enum",
    "validate_json_string",
    "sanitize_string",
    "validate_request_body",
    
    # API utilities
    "api_handler",
    "ApiError",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ServerError",
    "extract_path_parameter",
    "extract_query_parameter",
    "extract_body",
    "extract_user_id"
]
