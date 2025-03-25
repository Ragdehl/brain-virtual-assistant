"""
Lambda function for deleting a note.

This function deletes a note and its associated content.
"""
import os
import sys
from typing import Any, Dict

# Add common_tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lambdas/layers/common_tools/python"))

# Import common utilities
from lib import (  # type: ignore
    DynamoDBUtil,
    S3Util,
    api_handler,
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))


@api_handler(
    extract_user_id_param=True,
    extract_path_params=True,
    required_path_params=["noteId"]
)
def lambda_handler(user_id: str, noteId: str, context: Any) -> Dict[str, Any]:
    """
    Handle the Lambda event for deleting a note.
    
    Args:
        user_id: The user ID from the authorization context
        noteId: The note ID from the path parameters
        context: The Lambda context object
        
    Returns:
        A formatted API Gateway response
    """
    # Check if the note exists (will raise NotFoundError if not found)
    dynamodb_util.get_item({
        'userId': user_id,
        'noteId': noteId
    })

    # Delete the note from DynamoDB
    dynamodb_util.delete_item({
        'userId': user_id,
        'noteId': noteId
    })

    # Delete the note content from S3
    s3_util.delete_object(f"notes/{user_id}/{noteId}.md")

    return {
        "message": "Note deleted successfully"
    }
