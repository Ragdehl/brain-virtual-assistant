"""
Lambda function for updating a note.

This function updates an existing note's metadata and/or content.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict

import boto3

# Import shared models and utilities
from lambdas.models.note import NoteResponse, UpdateNoteRequest
from lambdas.utils.response import (
    format_error,
    format_not_found_error,
    format_response,
    format_validation_error,
)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3 = boto3.resource("s3")
lambda_client = boto3.client("lambda")

# Get environment variables
table_name = os.environ.get("DYNAMODB_TABLE", "obsidian-ai-assistant-notes-dev")
bucket_name = os.environ.get("S3_BUCKET", "obsidian-ai-assistant-content-dev")
embedding_function_name = os.environ.get(
    "EMBEDDING_FUNCTION", "obsidian-ai-assistant-generate-embeddings-dev"
)

# Initialize resources
table = dynamodb.Table(table_name)
bucket = s3.Bucket(bucket_name)


def lambda_handler(event: Dict[Any, Any], context: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Handle the Lambda event for updating a note.

    Args:
        event: The Lambda event object from API Gateway
        context: The Lambda context object

    Returns:
        A formatted API Gateway response
    """
    try:
        # Extract user ID from the authorizer context
        try:
            user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
        except KeyError:
            return format_validation_error("Missing user ID in request context")

        # Extract note ID from path parameters
        try:
            note_id = event["pathParameters"]["noteId"]
        except (KeyError, TypeError):
            return format_validation_error("Missing note ID in path parameters")

        # Parse request body
        try:
            if not event.get("body"):
                return format_validation_error("Missing request body")

            body = json.loads(event["body"])
            update_request = UpdateNoteRequest(**body)
        except json.JSONDecodeError:
            return format_validation_error("Invalid JSON in request body")
        except Exception as e:
            return format_validation_error(f"Invalid request body: {str(e)}")

        # Check if the note exists
        existing_note = table.get_item(Key={"userId": user_id, "noteId": note_id}).get("Item")

        if not existing_note:
            return format_not_found_error(f"Note with ID {note_id} not found")

        # Prepare update expression and attribute values
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        # Always update the updatedAt timestamp
        current_time = datetime.utcnow().isoformat() + "Z"
        update_expression_parts.append("SET #updatedAt = :updatedAt")
        expression_attribute_names["#updatedAt"] = "updatedAt"
        expression_attribute_values[":updatedAt"] = current_time

        # Update title if provided
        if update_request.title is not None:
            update_expression_parts.append("#title = :title")
            expression_attribute_names["#title"] = "title"
            expression_attribute_values[":title"] = update_request.title

        # Update tags if provided
        if update_request.tags is not None:
            update_expression_parts.append("#tags = :tags")
            expression_attribute_names["#tags"] = "tags"
            expression_attribute_values[":tags"] = update_request.tags

        # Update content if provided
        content_updated = False
        if update_request.content is not None:
            content_updated = True
            content = update_request.content

            # Calculate content hash and length
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            content_length = len(content.encode("utf-8"))

            # Update content metadata
            update_expression_parts.append(
                "#contentHash = :contentHash, #contentLength = :contentLength"
            )
            expression_attribute_names["#contentHash"] = "contentHash"
            expression_attribute_names["#contentLength"] = "contentLength"
            expression_attribute_values[":contentHash"] = content_hash
            expression_attribute_values[":contentLength"] = content_length

            # Upload content to S3
            s3.Object(bucket_name, f"{user_id}/{note_id}").put(
                Body=content, ContentType=existing_note.get("contentType", "text/markdown")
            )

            # Generate embeddings asynchronously
            try:
                lambda_client.invoke(
                    FunctionName=embedding_function_name,
                    InvocationType="Event",  # Asynchronous invocation
                    Payload=json.dumps({"userId": user_id, "noteId": note_id, "content": content}),
                )
            except Exception as e:
                print(f"Error invoking embedding function: {str(e)}")
                # Continue with the update even if embedding generation fails

        # Update the note in DynamoDB
        update_expression = " ".join(update_expression_parts)

        response = table.update_item(
            Key={"userId": user_id, "noteId": note_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )

        updated_note = response.get("Attributes", {})

        # Format the response
        note_response = NoteResponse.from_dynamodb_item(updated_note)

        return format_response({"note": note_response.model_dump()})

    except Exception as e:
        # Log the error for debugging
        print(f"Error updating note: {str(e)}")
        return format_error(str(e))
