"""
Lambda function for creating a note.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

# Import common utilities
from common_tools import (
    log_event,
    log_response,
    log_error,
    success_response,
    validation_error,
    server_error,
    validate_request_body,
    validate_required_fields,
    validate_string_length,
    DynamoDBUtil,
    S3Util
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))
lambda_client = boto3.client("lambda")

# Get environment variables
EMBEDDINGS_FUNCTION = os.environ.get("EMBEDDINGS_FUNCTION", "obsidian-generate-embeddings")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for creating a note.

    Args:
        event (dict): Lambda event
        context (object): Lambda context

    Returns:
        dict: API Gateway response
    """
    # Log the request
    log_event(event, context)

    try:
        # Extract user ID from the event
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("userId")
        if not user_id:
            return validation_error("User ID is required")

        # Validate and parse request body
        is_valid, body, error_message = validate_request_body(event)
        if not is_valid:
            return validation_error(error_message or "Invalid request body")

        # Validate required fields
        is_valid, error_message = validate_required_fields(body, ["title", "content"])
        if not is_valid:
            return validation_error(error_message)

        # Validate title length
        is_valid, error_message = validate_string_length(body, "title", min_length=1, max_length=200)
        if not is_valid:
            return validation_error(error_message)

        # Validate content length
        is_valid, error_message = validate_string_length(body, "content", min_length=1)
        if not is_valid:
            return validation_error(error_message)

        # Generate a unique ID for the note
        note_id = generate_note_id()
        current_time = datetime.utcnow().isoformat()

        # Extract data from request
        title = body["title"]
        content = body["content"]
        tags = body.get("tags", [])
        folder = body.get("folder", "")

        # Create S3 key for note content
        s3_key = f"notes/{user_id}/{note_id}.md"

        # Upload content to S3
        s3_util.put_object(
            key=s3_key,
            body=content,
            content_type="text/markdown"
        )

        # Create note item in DynamoDB
        note_item = {
            "id": note_id,
            "userId": user_id,
            "title": title,
            "s3Key": s3_key,
            "createdAt": current_time,
            "updatedAt": current_time
        }

        if tags:
            note_item["tags"] = tags

        if folder:
            note_item["folder"] = folder

        # Store note metadata in DynamoDB
        dynamodb_util.put_item(note_item)

        # Trigger embedding generation asynchronously
        try:
            lambda_client.invoke(
                FunctionName=EMBEDDINGS_FUNCTION,
                InvocationType="Event",
                Payload=json.dumps({
                    "noteId": note_id,
                    "userId": user_id,
                    "content": content
                })
            )
        except Exception as e:
            # Log error but don't fail the request
            log_error(e, context)

        # Return the created note
        response = success_response(
            status_code=201,
            data={
                "id": note_id,
                "title": title,
                "content": content,
                "tags": tags,
                "folder": folder,
                "createdAt": current_time,
                "updatedAt": current_time
            },
            message="Note created successfully"
        )

        # Log the response
        log_response(response)
        return response

    except Exception as e:
        # Log the error
        log_error(e, context)
        return server_error("Error creating note")


def generate_note_id() -> str:
    """
    Generate a unique ID for a note.

    Returns:
        str: Unique ID
    """
    return dynamodb_util.generate_id() 