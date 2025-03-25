"""
Example of using the API utilities in Lambda functions.

This module demonstrates how to use the API utilities to handle Lambda responses
and standardize error handling across Lambda functions.
"""
import json
from typing import Dict, Any

# Import the API utilities from the common tools layer
from lib import (
    api_handler,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    extract_path_parameter,
    extract_query_parameter,
    extract_body,
    extract_user_id
)


@api_handler
def get_note_handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example Lambda handler for getting a note.
    
    This handler demonstrates how to use the API utilities to:
    1. Extract parameters from the event
    2. Handle errors using custom exceptions
    3. Return a standardized response
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        The note data
    """
    # Extract the user ID from the event
    user_id = extract_user_id(event)
    
    # Extract the note ID from the path parameters
    note_id = extract_path_parameter(event, 'noteId')
    
    # Extract optional query parameters
    include_content = extract_query_parameter(
        event, 'includeContent', required=False, default='false'
    )
    
    # Convert string boolean to actual boolean
    include_content = include_content.lower() == 'true'
    
    # Simulate retrieving a note from the database
    # In a real handler, this would be a call to a database service
    note = get_note_from_database(user_id, note_id, include_content)
    
    # Return the note data
    # The @api_handler decorator will automatically format this as a success response
    return note


def get_note_from_database(
    user_id: str, note_id: str, include_content: bool
) -> Dict[str, Any]:
    """
    Simulate retrieving a note from the database.
    
    Args:
        user_id: The user ID
        note_id: The note ID
        include_content: Whether to include the note content
        
    Returns:
        The note data
        
    Raises:
        NotFoundError: If the note is not found
        UnauthorizedError: If the user is not authorized to access the note
    """
    # Simulate a note not found error
    if note_id == 'non-existent-note':
        raise NotFoundError(f"Note with ID {note_id} not found")
    
    # Simulate an unauthorized error
    if user_id != 'authorized-user' and note_id == 'private-note':
        raise UnauthorizedError("You are not authorized to access this note")
    
    # Simulate a validation error
    if not note_id or len(note_id) < 3:
        raise ValidationError(
            "Invalid note ID",
            details={"noteId": "Note ID must be at least 3 characters long"}
        )
    
    # Return a mock note
    note = {
        "id": note_id,
        "title": "Example Note",
        "tags": ["example", "demo"],
        "createdAt": "2023-06-15T12:00:00Z",
        "updatedAt": "2023-06-15T12:00:00Z"
    }
    
    # Include content if requested
    if include_content:
        note["content"] = "This is an example note content."
    
    return note


@api_handler
def create_note_handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example Lambda handler for creating a note.
    
    This handler demonstrates how to use the API utilities to:
    1. Extract and validate the request body
    2. Handle errors using custom exceptions
    3. Return a standardized response
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        The created note data
    """
    # Extract the user ID from the event
    user_id = extract_user_id(event)
    
    # Extract and parse the request body
    body = extract_body(event)
    
    # Validate required fields
    if 'title' not in body:
        raise ValidationError(
            "Missing required field",
            details={"title": "Title is required"}
        )
    
    # Validate field types
    if not isinstance(body.get('title'), str):
        raise ValidationError(
            "Invalid field type",
            details={"title": "Title must be a string"}
        )
    
    # Validate string length
    if len(body.get('title', '')) > 100:
        raise ValidationError(
            "Invalid field length",
            details={"title": "Title must be at most 100 characters long"}
        )
    
    # Simulate creating a note in the database
    # In a real handler, this would be a call to a database service
    note = create_note_in_database(user_id, body)
    
    # Return the created note data
    # The @api_handler decorator will automatically format this as a success response
    return note


def create_note_in_database(user_id: str, note_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate creating a note in the database.
    
    Args:
        user_id: The user ID
        note_data: The note data
        
    Returns:
        The created note data
    """
    # Return a mock created note
    return {
        "id": "new-note-id",
        "title": note_data.get('title'),
        "content": note_data.get('content', ''),
        "tags": note_data.get('tags', []),
        "createdAt": "2023-06-15T12:00:00Z",
        "updatedAt": "2023-06-15T12:00:00Z"
    }


# Example of how the Lambda handler would be invoked by AWS Lambda
def lambda_handler(event, context):
    """
    Example Lambda handler that would be invoked by AWS Lambda.
    
    This function demonstrates how to use the API utilities in a real Lambda handler.
    
    Args:
        event: The Lambda event
        context: The Lambda context
        
    Returns:
        The API Gateway response
    """
    # Determine which handler to call based on the HTTP method
    http_method = event.get('httpMethod', '')
    
    if http_method == 'GET':
        return get_note_handler(event, context)
    elif http_method == 'POST':
        return create_note_handler(event, context)
    else:
        # Return a method not allowed error
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Method not allowed',
                'message': f'HTTP method {http_method} is not supported'
            })
        } 