"""
Lambda function to retrieve a note.

This function:
1. Gets note metadata from DynamoDB
2. Retrieves note content from S3
3. Returns combined data
"""

import json
import os
from typing import Dict, Any, Optional

# Import from layers
import common.dynamo_helper as dynamo
import common.s3_helper as s3
import common.logging as logging

logger = logging.get_logger()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Retrieve a note by ID.
    
    Args:
        event: API Gateway Lambda Proxy Input Format
            {
                "pathParameters": {
                    "id": "note-uuid"
                }
            }
        context: Lambda Context runtime methods and attributes
    
    Returns:
        API Gateway Lambda Proxy Output Format
            {
                "statusCode": int,
                "body": string (JSON containing note data)
            }
            
    Raises:
        Exception: If there's an error during note retrieval
    """
    try:
        # Get note ID from path parameters
        note_id: str = event['pathParameters']['id']
        
        # Get note metadata from DynamoDB
        note_item: Optional[Dict[str, Any]] = dynamo.get_item(note_id)
        
        if not note_item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Note not found'})
            }
        
        # Get note content from S3
        s3_key: str = f"notes/{note_id}.md"
        content: str = s3.get_file_content(s3_key)
        
        # Combine metadata and content
        response: Dict[str, Any] = {**note_item, 'content': content}
        
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving note: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to retrieve note'})
        } 