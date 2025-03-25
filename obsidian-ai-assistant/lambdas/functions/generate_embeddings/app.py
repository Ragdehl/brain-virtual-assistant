"""
Lambda function for generating embeddings.

This function generates embeddings for text or note content and optionally
updates the note in DynamoDB with the generated embeddings.
"""
import os
import sys
from typing import Any, Dict, List

import boto3
import numpy as np
import requests

# Add common_tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lambdas/layers/common_tools/python"))

# Import common utilities
from lib import (  # type: ignore
    api_handler,
    NotFoundError,
    ValidationError
)

# Import shared models and utilities
from lambdas.utils.response import (
    format_error,
    format_not_found_error,
    format_response,
    format_validation_error,
)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
table_name = os.environ.get('DYNAMODB_TABLE', 'obsidian-ai-assistant-notes-dev')

# Initialize resources
table = dynamodb.Table(table_name)


@api_handler
def lambda_handler(event: Dict[Any, Any], context: Any) -> Dict[str, Any]:
    """
    Handle the Lambda event for generating embeddings.
    
    Args:
        event: The Lambda event object
        context: The Lambda context object
        
    Returns:
        A formatted API Gateway response
    """
    try:
        # Check if this is a direct text embedding request
        if 'text' in event:
            # Generate embeddings for the provided text
            embeddings = generate_embeddings(event['text'])

            # Return the embeddings
            return format_response({'embeddings': embeddings})

        # Otherwise, this should be a note embedding request
        elif all(key in event for key in ['userId', 'noteId', 'content']):
            user_id = event['userId']
            note_id = event['noteId']
            content = event['content']

            # Check if the note exists
            existing_note = table.get_item(
                Key={
                    'userId': user_id,
                    'noteId': note_id
                }
            ).get('Item')

            if not existing_note:
                return format_not_found_error(f"Note with ID {note_id} not found")

            # Generate embeddings for the note content
            embeddings = generate_embeddings(content)

            # Update the note with the embeddings
            table.update_item(
                Key={
                    'userId': user_id,
                    'noteId': note_id
                },
                UpdateExpression='SET embeddings = :embeddings',
                ExpressionAttributeValues={
                    ':embeddings': embeddings
                }
            )

            # Return the embeddings
            return format_response({'embeddings': embeddings})

        else:
            return format_validation_error("Missing required parameters. Either 'text' or 'userId', 'noteId', and 'content' must be provided.")

    except Exception as e:
        # Log the error for debugging
        print(f"Error generating embeddings: {str(e)}")
        return format_error(str(e))


def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for the given text.
    
    In a production environment, this would use a real embedding model like:
    - Amazon Bedrock with Titan Embeddings
    - OpenAI Embeddings API
    - Hugging Face Sentence Transformers
    
    For this example, we'll use a simple mock implementation.
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        A list of embedding values
    """
    # For demonstration purposes, we'll generate a simple mock embedding
    # In a real implementation, this would call an embedding model API

    # Check if we should use a real embedding service based on environment
    embedding_api_key = os.environ.get('EMBEDDING_API_KEY')
    embedding_api_url = os.environ.get('EMBEDDING_API_URL')

    if embedding_api_key and embedding_api_url:
        # Use a real embedding service
        try:
            response = requests.post(
                embedding_api_url,
                headers={
                    'Authorization': f'Bearer {embedding_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'input': text,
                    'model': 'text-embedding-ada-002'  # Example model
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('data', [{}])[0].get('embedding', [])
            else:
                print(f"Error from embedding API: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error calling embedding API: {str(e)}")

    # Fall back to mock embeddings if real service is not available or fails
    # This is a very simple mock that creates a deterministic embedding based on the text
    # It's not suitable for real semantic search but works for testing

    # Create a simple hash of the text
    text_hash = sum(ord(c) for c in text)

    # Use the hash as a seed for numpy's random number generator
    np.random.seed(text_hash)

    # Generate a random embedding vector (dimension 5 for simplicity)
    embedding_dim = int(os.environ.get('EMBEDDING_DIM', '5'))
    embeddings = np.random.rand(embedding_dim).tolist()

    # Normalize the embeddings to unit length
    norm = np.linalg.norm(embeddings)
    if norm > 0:
        embeddings = [e / norm for e in embeddings]

    return embeddings
