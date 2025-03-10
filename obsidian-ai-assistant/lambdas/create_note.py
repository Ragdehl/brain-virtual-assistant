"""
Lambda function to create a new note.

This function:
1. Receives note data from API Gateway
2. Creates a record in DynamoDB with metadata
3. Stores the note content in S3
4. Triggers the embedding generation process
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import from layers
import common.dynamo_helper as dynamo
import common.s3_helper as s3
import common.logging as logging

logger = logging.get_logger()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Create a new note with metadata in DynamoDB and content in S3.
    
    Args:
        event: API Gateway Lambda Proxy Input Format
            {
                "body": "{"title": "Note Title", "content": "Note content in markdown", "tags": ["tag1", "tag2"]}"
            }
        context: Lambda Context runtime methods and attributes
    
    Returns:
        API Gateway Lambda Proxy Output Format
            {
                "statusCode": int,
                "body": string
            }
            
    Raises:
        Exception: If there's an error during note creation
    """
    try:
        # Parse request body
        body: Dict[str, Any] = json.loads(event.get('body', '{}'))
        
        # Generate a unique ID for the note
        note_id: str = str(uuid.uuid4())
        timestamp: str = datetime.now(datetime.UTC).isoformat()
        
        # Create note metadata
        note_item: Dict[str, Any] = {
            'id': note_id,
            'title': body.get('title', 'Untitled'),
            'created_at': timestamp,
            'updated_at': timestamp,
            'tags': body.get('tags', [])
        }
        
        # Store note content in S3
        content: str = body.get('content', '')
        s3_key: str = f"notes/{note_id}.md"
        s3.upload_file_content(s3_key, content)
        
        # Store metadata in DynamoDB
        dynamo.put_item(note_item)
        
        # Return success response
        return {
            'statusCode': 201,
            'body': json.dumps({'id': note_id, 'message': 'Note created successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to create note'})
        } 