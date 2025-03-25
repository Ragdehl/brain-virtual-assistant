"""
Lambda function for creating a note.
"""
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

import boto3

# Add common_tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lambdas/layers/common_tools/python"))

# Import common utilities
from lib import (  # type: ignore
    DynamoDBUtil,
    S3Util,
    api_handler,
    ValidationError,
    validate_required_fields,
    validate_string_length,
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))
lambda_client = boto3.client("lambda")

# Get environment variables
EMBEDDINGS_FUNCTION = os.environ.get("EMBEDDINGS_FUNCTION", "obsidian-ai-assistant-generate-embeddings-dev")


@api_handler(
    extract_user_id_param=True,
    extract_body_param=True,
    required_body=True
)
def lambda_handler(user_id: str, body: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for creating a note.

    Args:
        user_id: The user ID from the authorization context
        body: The parsed request body
        context: Lambda context

    Returns:
        The created note data
    """
    # Validate required fields
    validate_required_fields(body, ["title", "content"])

    # Validate title length
    validate_string_length(body, "title", min_length=1, max_length=200)

    # Validate content length
    validate_string_length(body, "content", min_length=1)

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
    except Exception:
        # Log error but don't fail the request
        pass

    # Return the created note with custom status code
    return {
        "statusCode": 201,
        "message": "Note created successfully",
        "headers": {
            "Location": f"/notes/{note_id}"
        },
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags,
        "folder": folder,
        "createdAt": current_time,
        "updatedAt": current_time
    }


def generate_note_id() -> str:
    """
    Generate a unique ID for a note.

    Returns:
        str: Unique ID
    """
    return dynamodb_util.generate_id()
