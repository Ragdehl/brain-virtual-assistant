"""
Lambda function for deleting a note.

This function deletes a note and its associated content.
"""
import json
import os
import boto3
from typing import Dict, Any

# Import shared models and utilities
from lambdas.utils.response import (
    format_response,
    format_error,
    format_validation_error,
    format_not_found_error
)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

# Get environment variables
table_name = os.environ.get('DYNAMODB_TABLE', 'obsidian-ai-assistant-notes-dev')
bucket_name = os.environ.get('S3_BUCKET', 'obsidian-ai-assistant-content-dev')

# Initialize resources
table = dynamodb.Table(table_name)
bucket = s3.Bucket(bucket_name)


def lambda_handler(event: Dict[Any, Any], context: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Handle the Lambda event for deleting a note.
    
    Args:
        event: The Lambda event object from API Gateway
        context: The Lambda context object
        
    Returns:
        A formatted API Gateway response
    """
    try:
        # Extract user ID from the authorizer context
        try:
            user_id = event['requestContext']['authorizer']['claims']['sub']
        except KeyError:
            return format_validation_error("Missing user ID in request context")
        
        # Extract note ID from path parameters
        try:
            note_id = event['pathParameters']['noteId']
        except (KeyError, TypeError):
            return format_validation_error("Missing note ID in path parameters")
        
        # Check if the note exists
        existing_note = table.get_item(
            Key={
                'userId': user_id,
                'noteId': note_id
            }
        ).get('Item')
        
        if not existing_note:
            return format_not_found_error(f"Note with ID {note_id} not found")
        
        # Delete the note from DynamoDB
        table.delete_item(
            Key={
                'userId': user_id,
                'noteId': note_id
            }
        )
        
        # Delete the note content from S3
        try:
            s3.Object(bucket_name, f"{user_id}/{note_id}").delete()
        except Exception as e:
            # Log the error but continue with the deletion
            print(f"Error deleting note content from S3: {str(e)}")
        
        # Return a success response with no content
        return {
            'statusCode': 204,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': ''
        }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error deleting note: {str(e)}")
        return format_error(str(e)) 