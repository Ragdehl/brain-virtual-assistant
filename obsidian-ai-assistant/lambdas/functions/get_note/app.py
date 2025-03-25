"""
Lambda function for retrieving a note.
"""
import os
import sys
from typing import Any, Dict

from botocore.exceptions import ClientError

# Add common_tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lambdas/layers/common_tools/python"))

# Import common utilities
from lib import (  # type: ignore
    DynamoDBUtil,
    S3Util,
    api_handler,
    NotFoundError,
)

# Initialize AWS clients
dynamodb_util = DynamoDBUtil(os.environ.get("DYNAMODB_TABLE", "obsidian-notes"))
s3_util = S3Util(os.environ.get("S3_BUCKET", "obsidian-notes-content"))


@api_handler(
    extract_path_params=True,
    extract_user_id_param=True,
    required_path_params=["id"]
)
def lambda_handler(user_id: str, id: str, context: Any) -> Dict[str, Any]:
    """
    Lambda handler for retrieving a note.

    Args:
        user_id: The user ID from the authorization context
        id: The note ID from the path parameters
        context: Lambda context

    Returns:
        The note data
    """
    # Get note metadata from DynamoDB
    note_item = dynamodb_util.get_item({
        "id": id,
        "userId": user_id
    })

    # Get note content from S3
    s3_key = note_item["s3Key"]
    content = s3_util.get_object_content(s3_key)

    # Add content to note item
    note_item["content"] = content

    # Return the note
    return {
        "message": "Note retrieved successfully",
        **note_item
    }
