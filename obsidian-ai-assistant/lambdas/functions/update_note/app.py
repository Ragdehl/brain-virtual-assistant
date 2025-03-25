"""
Lambda function for updating a note.

This function updates an existing note's metadata and/or content.
"""

import hashlib
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
    NotFoundError,
    ValidationError,
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))
lambda_client = boto3.client("lambda")

# Get environment variables
embedding_function_name = os.environ.get(
    "EMBEDDING_FUNCTION", "obsidian-ai-assistant-generate-embeddings-dev"
)


@api_handler(
    extract_path_params=True,
    extract_user_id_param=True,
    extract_body_param=True,
    required_path_params=["id"],
    required_body=True
)
def lambda_handler(user_id: str, id: str, body: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating a note.

    Args:
        user_id: The user ID from the authorization context
        id: The note ID from the path parameters
        body: The request body containing note updates
        context: Lambda context

    Returns:
        The updated note data
    """
    # Validate required fields
    if "title" not in body and "content" not in body:
        raise ValidationError("At least one of 'title' or 'content' must be provided")

    # Check if the note exists (will raise NotFoundError if not found)
    existing_note = dynamodb_util.get_item({
        "userId": user_id,
        "noteId": id
    })

    # Update note metadata in DynamoDB
    update_expression = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    if "title" in body:
        update_expression.append("#title = :title")
        expression_attribute_values[":title"] = body["title"]
        expression_attribute_names["#title"] = "title"

    if "content" in body:
        # Update content in S3
        s3_key = f"notes/{user_id}/{id}.md"
        s3_util.put_object(
            key=s3_key,
            body=body["content"],
            content_type="text/markdown"
        )

        # Update s3Key in DynamoDB
        update_expression.append("#s3Key = :s3Key")
        expression_attribute_values[":s3Key"] = s3_key
        expression_attribute_names["#s3Key"] = "s3Key"

    # Update lastModified timestamp
    update_expression.append("#lastModified = :lastModified")
    expression_attribute_values[":lastModified"] = datetime.utcnow().isoformat() + "Z"
    expression_attribute_names["#lastModified"] = "lastModified"

    # Perform the update
    updated_note = dynamodb_util.update_item(
        key={"userId": user_id, "noteId": id},
        update_expression="SET " + ", ".join(update_expression),
        expression_attribute_values=expression_attribute_values,
        expression_attribute_names=expression_attribute_names
    )

    # Get the updated note content from S3
    s3_key = updated_note["s3Key"]
    content = s3_util.get_object_content(s3_key)
    updated_note["content"] = content

    return {
        "message": "Note updated successfully",
        **updated_note
    }
