"""
Lambda function for searching notes.

This function supports both text-based and semantic search for notes.
"""
import json
import os
from typing import Any, Dict, List, Optional

import boto3
import numpy as np

# Import shared models and utilities
from lambdas.models.note import NoteListResponse, NoteResponse, SearchNotesRequest
from lambdas.utils.response import format_error, format_response, format_validation_error

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Get environment variables
table_name = os.environ.get('DYNAMODB_TABLE', 'obsidian-ai-assistant-notes-dev')
embedding_function_name = os.environ.get('EMBEDDING_FUNCTION', 'obsidian-ai-assistant-generate-embeddings-dev')

# Initialize resources
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[Any, Any], context: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Handle the Lambda event for searching notes.
    
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

        # Parse request body
        try:
            if not event.get('body'):
                return format_validation_error("Missing request body")

            body = json.loads(event['body'])
            search_request = SearchNotesRequest(**body)
        except json.JSONDecodeError:
            return format_validation_error("Invalid JSON in request body")
        except Exception as e:
            return format_validation_error(f"Invalid request body: {str(e)}")

        # Validate search type
        if search_request.searchType not in ['text', 'semantic']:
            return format_validation_error("Invalid search type. Must be 'text' or 'semantic'")

        # Perform the search
        if search_request.searchType == 'text':
            notes = perform_text_search(
                user_id,
                search_request.query,
                search_request.tags,
                search_request.fromDate,
                search_request.toDate,
                search_request.limit
            )
        else:  # semantic search
            notes = perform_semantic_search(
                user_id,
                search_request.query,
                search_request.tags,
                search_request.fromDate,
                search_request.toDate,
                search_request.limit
            )

        # Format the response
        note_list_response = NoteListResponse(
            notes=[NoteResponse.from_dynamodb_item(note) for note in notes],
            pagination={"nextToken": None}  # Pagination not supported for search yet
        )

        return format_response(note_list_response.model_dump())

    except Exception as e:
        # Log the error for debugging
        print(f"Error searching notes: {str(e)}")
        return format_error(str(e))


def perform_text_search(
    user_id: str,
    query: str,
    tags: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Perform a text-based search for notes.
    
    Args:
        user_id: The user ID
        query: The search query
        tags: Optional list of tags to filter by
        from_date: Optional start date to filter by
        to_date: Optional end date to filter by
        limit: Maximum number of results to return
        
    Returns:
        A list of matching notes
    """
    # Build the scan parameters
    scan_params = {
        'FilterExpression': 'userId = :userId',
        'ExpressionAttributeValues': {
            ':userId': user_id
        }
    }

    # Add query filter
    if query:
        # Search in title
        scan_params['FilterExpression'] += ' AND contains(title, :query)'
        scan_params['ExpressionAttributeValues'][':query'] = query

    # Add tag filter
    if tags and len(tags) > 0:
        tag_filter_parts = []
        for i, tag in enumerate(tags):
            tag_filter_parts.append(f'contains(tags, :tag{i})')
            scan_params['ExpressionAttributeValues'][f':tag{i}'] = tag

        tag_filter = ' AND '.join(tag_filter_parts)
        scan_params['FilterExpression'] += f' AND ({tag_filter})'

    # Add date filter
    if from_date or to_date:
        if from_date:
            scan_params['FilterExpression'] += ' AND createdAt >= :fromDate'
            scan_params['ExpressionAttributeValues'][':fromDate'] = from_date

        if to_date:
            scan_params['FilterExpression'] += ' AND createdAt <= :toDate'
            scan_params['ExpressionAttributeValues'][':toDate'] = to_date

    # Scan the table
    response = table.scan(**scan_params)
    notes = response.get('Items', [])

    # Sort by relevance (simple contains check for now)
    def relevance_score(note):
        score = 0
        if query.lower() in note.get('title', '').lower():
            score += 10
        for tag in note.get('tags', []):
            if query.lower() in tag.lower():
                score += 5
        return score

    notes.sort(key=relevance_score, reverse=True)

    # Limit the results
    return notes[:limit]


def perform_semantic_search(
    user_id: str,
    query: str,
    tags: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Perform a semantic search for notes using embeddings.
    
    Args:
        user_id: The user ID
        query: The search query
        tags: Optional list of tags to filter by
        from_date: Optional start date to filter by
        to_date: Optional end date to filter by
        limit: Maximum number of results to return
        
    Returns:
        A list of matching notes
    """
    # Generate embeddings for the query
    query_embedding = generate_embeddings(query)

    # Scan all notes for the user
    scan_params = {
        'FilterExpression': 'userId = :userId',
        'ExpressionAttributeValues': {
            ':userId': user_id
        }
    }

    # Add tag filter
    if tags and len(tags) > 0:
        tag_filter_parts = []
        for i, tag in enumerate(tags):
            tag_filter_parts.append(f'contains(tags, :tag{i})')
            scan_params['ExpressionAttributeValues'][f':tag{i}'] = tag

        tag_filter = ' AND '.join(tag_filter_parts)
        scan_params['FilterExpression'] += f' AND ({tag_filter})'

    # Add date filter
    if from_date or to_date:
        if from_date:
            scan_params['FilterExpression'] += ' AND createdAt >= :fromDate'
            scan_params['ExpressionAttributeValues'][':fromDate'] = from_date

        if to_date:
            scan_params['FilterExpression'] += ' AND createdAt <= :toDate'
            scan_params['ExpressionAttributeValues'][':toDate'] = to_date

    # Scan the table
    response = table.scan(**scan_params)
    notes = response.get('Items', [])

    # Calculate cosine similarity for each note
    notes_with_scores = []
    for note in notes:
        if 'embeddings' in note:
            note_embedding = note['embeddings']
            similarity = cosine_similarity(query_embedding, note_embedding)
            notes_with_scores.append((note, similarity))

    # Sort by similarity score
    notes_with_scores.sort(key=lambda x: x[1], reverse=True)

    # Return the top results
    return [note for note, score in notes_with_scores[:limit]]


def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for the given text using the embedding Lambda function.
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        A list of embedding values
    """
    try:
        response = lambda_client.invoke(
            FunctionName=embedding_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'text': text
            })
        )

        payload = json.loads(response['Payload'].read().decode())
        return payload.get('embeddings', [])
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        # Return a default embedding if there's an error
        return [0.0] * 3  # Assuming 3D embeddings for simplicity


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate the cosine similarity between two vectors.
    
    Args:
        vec1: The first vector
        vec2: The second vector
        
    Returns:
        The cosine similarity (between -1 and 1)
    """
    # Convert to numpy arrays
    a = np.array(vec1)
    b = np.array(vec2)

    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
