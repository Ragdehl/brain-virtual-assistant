# Common Tools Layer

This layer provides common utilities for Lambda functions in the Obsidian AI Assistant project.

## API Utilities

The API utilities provide a standardized way to handle Lambda responses to API Gateway and manage errors raised in Lambda functions.

### API Handler Decorator

The `api_handler` decorator standardizes API Gateway responses and error handling:

```python
from lib import api_handler

@api_handler
def my_lambda_handler(event, context):
    # Your handler logic here
    return result  # Will be automatically formatted as a success response
```

The decorator:
1. Logs the incoming event
2. Handles exceptions and converts them to appropriate API responses
3. Logs the response
4. Formats the response for API Gateway

### Error Classes

The API utilities provide several error classes that can be raised in Lambda functions:

```python
from lib import ValidationError, NotFoundError, UnauthorizedError, ServerError, ApiError

# Validation error (400)
raise ValidationError("Invalid input", details={"field": "error message"})

# Not found error (404)
raise NotFoundError("Resource not found")

# Unauthorized error (401)
raise UnauthorizedError("Unauthorized access")

# Server error (500)
raise ServerError("Internal server error")

# Custom API error
raise ApiError("Custom error", status_code=403, error_code="FORBIDDEN", details={})
```

### Parameter Extraction

The API utilities provide functions to extract parameters from the Lambda event:

```python
from lib import extract_path_parameter, extract_query_parameter, extract_body, extract_user_id

# Extract path parameter
note_id = extract_path_parameter(event, 'noteId')

# Extract query parameter (optional)
include_content = extract_query_parameter(event, 'includeContent', required=False, default='false')

# Extract and parse request body
body = extract_body(event, required=True)

# Extract user ID from authorizer
user_id = extract_user_id(event)
```

## Example Usage

See the [API Utilities Example](examples/api_util_example.py) for a complete example of how to use the API utilities in Lambda functions.

## Other Utilities

The common tools layer also provides other utilities:

- **DynamoDB Utilities**: Functions for interacting with DynamoDB
- **Logging Utilities**: Functions for logging events, responses, and errors
- **Response Utilities**: Functions for creating standardized API responses
- **S3 Utilities**: Functions for interacting with S3
- **Validation Utilities**: Functions for validating input data 