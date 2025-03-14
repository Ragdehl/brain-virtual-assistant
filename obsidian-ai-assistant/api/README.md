# Obsidian AI Assistant API

A serverless REST API for the Obsidian AI Assistant, built with Python and AWS Lambda. This API provides endpoints for managing notes, performing searches, and handling user authentication.

## Architecture

The API is built using a modular architecture with AWS Lambda and API Gateway. It consists of the following components:

### Core Components

- `api_handler.py` - Main Lambda handler for API Gateway requests
- `auth.py` - Authentication and API key management
- `response.py` - Standardized API response formatting
- `utils.py` - Utility functions for logging, configuration, and request handling

### Models

The `models/` directory contains JSON schemas for request and response validation:

- `models/request/` - Request validation schemas
  - `create_note.py` - Schema for note creation requests
  - `update_note.py` - Schema for note update requests
  - `search.py` - Schema for search requests

- `models/response/` - Response formatting schemas
  - `note.py` - Schema for note responses
  - `error.py` - Schema for error responses
  - `search.py` - Schema for search responses

### Resources

The `resources/` directory contains API endpoint definitions:

- `notes.py` - Note management endpoints
- `search.py` - Search endpoints
- `common.py` - Shared API utilities

## API Endpoints

### Notes Management

- `POST /notes` - Create a new note
- `GET /notes` - List notes (with pagination)
- `GET /notes/{note_id}` - Get a specific note
- `PUT /notes/{note_id}` - Update a note
- `DELETE /notes/{note_id}` - Delete a note

### Search & Discovery

- `GET /search` - Semantic search across notes
- `GET /notes/tags` - List all tags
- `GET /notes/related/{note_id}` - Find related notes

### System

- `GET /health` - Health check endpoint

## Authentication

The API uses API keys for authentication, which are stored in AWS Systems Manager Parameter Store. API keys can be provided in two ways:

1. Using the `X-Api-Key` header:
```
X-Api-Key: your-api-key
```

2. Using the `Authorization` header with Bearer token:
```
Authorization: Bearer your-api-key
```

## Request/Response Format

### Success Response

```json
{
    "success": true,
    "data": {
        // Response data here
    },
    "message": "Optional success message"
}
```

### Error Response

```json
{
    "success": false,
    "error": {
        "message": "Error message",
        "code": "ERROR_CODE",
        "details": {
            // Optional error details
        }
    }
}
```

## Query Parameters

### Pagination

- `limit` - Maximum number of items to return (default: 10, max: 100)
- `cursor` - Pagination cursor for fetching next page

### Search & Filtering

- `query` - Search query string
- `tags` - Comma-separated list of tags to filter by
- `sort` - Sort order (created_at, updated_at)
- `order` - Sort direction (asc, desc)

## Development

### Prerequisites

- Python 3.8+
- AWS credentials configured
- API key for authentication

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
export DYNAMODB_TABLE=your-notes-table
export S3_BUCKET=your-notes-bucket
export STAGE=dev
```

## Deployment

The API is designed to be deployed as an AWS Lambda function behind API Gateway. Deployment can be handled using AWS CDK, Serverless Framework, or other IaC tools.

### Required Resources

- API Gateway
- Lambda Function
- DynamoDB Table
- S3 Bucket
- Systems Manager Parameter Store (for API keys)

## Error Handling

The API implements standardized error responses with appropriate HTTP status codes:

- 400 - Bad Request (validation errors)
- 401 - Unauthorized (invalid/missing API key)
- 404 - Not Found
- 500 - Internal Server Error

## Security Features

1. API Key Authentication
2. Input Sanitization
3. Request Validation
4. Sensitive Data Redaction in Logs
5. CORS Headers
6. Maximum Pagination Limits

## Logging

All requests are logged with sensitive information (API keys, authorization headers) automatically redacted. Logs include:

- Request Path
- HTTP Method
- Query Parameters
- Request Body (if present)
- Response Status Code

## Type Safety

The codebase uses Python type hints throughout for better maintainability and IDE support.

## Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Include docstrings for all modules and functions
4. Write tests for new functionality
5. Update documentation as needed

## License

MIT 