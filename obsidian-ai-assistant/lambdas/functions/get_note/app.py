"""
Lambda function for retrieving a note.
"""
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

# Import common utilities
from common_tools import (
    log_event,
    log_response,
    log_error,
    success_response,
    not_found_error,
    server_error,
    DynamoDBUtil,
    S3Util
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for retrieving a note.

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
            return not_found_error("User ID is required")

        # Extract note ID from the path parameters
        path_parameters = event.get("pathParameters", {}) or {}
        note_id = path_parameters.get("id")
        if not note_id:
            return not_found_error("Note ID is required")

        # Get note metadata from DynamoDB
        note_item = dynamodb_util.get_item({
            "id": note_id,
            "userId": user_id
        })

        if not note_item:
            return not_found_error("Note not found")

        try:
            # Get note content from S3
            s3_key = note_item["s3Key"]
            content = s3_util.get_object_content(s3_key)

            # Add content to note item
            note_item["content"] = content

            # Return the note
            response = success_response(
                data=note_item,
                message="Note retrieved successfully"
            )

            # Log the response
            log_response(response)
            return response

        except FileNotFoundError:
            return not_found_error("Note content not found")

    except ClientError as e:
        # Log the error
        log_error(e, context)
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ResourceNotFoundException":
            return not_found_error("Note not found")
        return server_error("Error retrieving note")

    except Exception as e:
        # Log the error
        log_error(e, context)
        return server_error("Error retrieving note") 