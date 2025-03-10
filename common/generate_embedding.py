"""
Lambda function to generate embeddings for a note.

This function:
1. Retrieves note content from S3
2. Calls Amazon Bedrock to generate embeddings
3. Passes the embeddings to the indexing function
"""

import json
import os
import boto3
from typing import Dict, Any, List, Optional

# Import from layers
import common.s3_helper as s3
import common.logging as logging

logger = logging.get_logger()

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

MODEL_ID: str = os.environ.get('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate embeddings for a note using Amazon Bedrock.
    
    Args:
        event: Event containing note information
            {
                "note_id": "uuid-of-note",
                "s3_key": "notes/uuid-of-note.md"
            }
        context: Lambda Context runtime methods and attributes
    
    Returns:
        Dict containing note ID, embedding vector, and content
            {
                "note_id": "uuid-of-note",
                "embedding": [...],  # Vector of floats
                "content": "Note content"
            }
            
    Raises:
        Exception: If there's an error during embedding generation
    """
    try:
        # Get note ID and S3 key from event
        note_id: str = event.get('note_id')
        s3_key: str = event.get('s3_key', f"notes/{note_id}.md")
        
        # Get note content from S3
        content: str = s3.get_file_content(s3_key)
        
        # Generate embeddings using Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'inputText': content
            })
        )
        
        # Parse response
        response_body: Dict[str, Any] = json.loads(response['body'].read())
        embedding: List[float] = response_body.get('embedding')
        
        # Prepare event for indexing function
        index_event: Dict[str, Any] = {
            'note_id': note_id,
            'embedding': embedding,
            'content': content
        }
        
        # Return embedding for next step in workflow
        return index_event
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise