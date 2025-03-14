"""
Notes resource for the API.
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from ..models.request.create_note import validate_create_note_request
from ..models.response.note import format_note_response, format_note_list_response
from ..models.response.error import format_error_response


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")

# Get environment variables
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "obsidian-notes")
S3_BUCKET = os.environ.get("S3_BUCKET", "obsidian-notes-content")
EMBEDDINGS_FUNCTION = os.environ.get("EMBEDDINGS_FUNCTION", "obsidian-generate-embeddings")


def create_note(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Create a new note.

    Args:
        body (dict): Request body
        user_id (str): User ID

    Returns:
        dict: API response
    """
    # Validate request
    validation_errors = validate_create_note_request(body)
    if validation_errors:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Validation error",
                    "details": validation_errors
                }
            })
        }

    try:
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
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=content.encode("utf-8"),
            ContentType="text/markdown"
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
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(Item=note_item)

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
            print(f"Error invoking embeddings function: {str(e)}")

        # Return the created note
        note_response = format_note_response({**note_item, "content": content})
        return {
            "statusCode": 201,
            "body": json.dumps({
                "success": True,
                "data": note_response
            })
        }

    except Exception as e:
        print(f"Error creating note: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Error creating note"
                }
            })
        }


def get_note(note_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get a note by ID.

    Args:
        note_id (str): Note ID
        user_id (str): User ID

    Returns:
        dict: API response
    """
    try:
        # Get note metadata from DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(
            Key={
                "id": note_id,
                "userId": user_id
            }
        )

        note_item = response.get("Item")
        if not note_item:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Note not found"
                    }
                })
            }

        # Get note content from S3
        s3_key = note_item["s3Key"]
        s3_response = s3.get_object(
            Bucket=S3_BUCKET,
            Key=s3_key
        )
        content = s3_response["Body"].read().decode("utf-8")

        # Add content to note item
        note_item["content"] = content

        # Format and return the note
        note_response = format_note_response(note_item)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "data": note_response
            })
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "success": False,
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "Note content not found"
                    }
                })
            }
        print(f"Error getting note: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Error getting note"
                }
            })
        }
    except Exception as e:
        print(f"Error getting note: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Error getting note"
                }
            })
        }


def generate_note_id() -> str:
    """
    Generate a unique ID for a note.

    Returns:
        str: Unique ID
    """
    import uuid
    return str(uuid.uuid4()) 