"""
Lambda function for listing notes.

This function retrieves a list of notes for a user, with optional filtering and pagination.
"""
import base64
import json
import os
from typing import Any, Dict

import boto3

# Import shared models and utilities
from lambdas.models.note import NoteListResponse, NoteResponse
from lambdas.utils.response import format_error, format_response, format_validation_error

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'obsidian-ai-assistant-notes-dev'))


def lambda_handler(event: Dict[Any, Any], context: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Handle the Lambda event for listing notes.
    
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

        # Extract query parameters
        query_params = event.get('queryStringParameters', {}) or {}

        # Parse pagination parameters
        limit = int(query_params.get('limit', '50'))
        if limit < 1 or limit > 100:
            limit = 50

        next_token = query_params.get('nextToken')

        # Parse filter parameters
        tag = query_params.get('tag')
        from_date = query_params.get('fromDate')
        to_date = query_params.get('toDate')

        # Build the query parameters
        query_params = {
            'KeyConditionExpression': 'userId = :userId',
            'ExpressionAttributeValues': {
                ':userId': user_id
            },
            'Limit': limit
        }

        # Add pagination token if provided
        if next_token:
            try:
                last_evaluated_key = json.loads(base64.b64decode(next_token).decode('utf-8'))
                query_params['ExclusiveStartKey'] = last_evaluated_key
            except (json.JSONDecodeError, base64.binascii.Error):
                return format_validation_error("Invalid pagination token")

        # Add date range filter if provided
        if from_date or to_date:
            # Use the createdAtIndex GSI
            query_params['IndexName'] = 'createdAtIndex'

            if from_date and to_date:
                query_params['KeyConditionExpression'] += ' AND createdAt BETWEEN :fromDate AND :toDate'
                query_params['ExpressionAttributeValues'][':fromDate'] = from_date
                query_params['ExpressionAttributeValues'][':toDate'] = to_date
            elif from_date:
                query_params['KeyConditionExpression'] += ' AND createdAt >= :fromDate'
                query_params['ExpressionAttributeValues'][':fromDate'] = from_date
            elif to_date:
                query_params['KeyConditionExpression'] += ' AND createdAt <= :toDate'
                query_params['ExpressionAttributeValues'][':toDate'] = to_date

        # Add tag filter if provided
        if tag:
            query_params['FilterExpression'] = 'contains(tags, :tag)'
            query_params['ExpressionAttributeValues'][':tag'] = tag

        # Query the DynamoDB table
        response = table.query(**query_params)

        # Process the results
        notes = response.get('Items', [])

        # Generate the next pagination token if there are more results
        pagination = {"nextToken": None}
        if 'LastEvaluatedKey' in response:
            next_token = base64.b64encode(json.dumps(response['LastEvaluatedKey']).encode('utf-8')).decode('utf-8')
            pagination["nextToken"] = next_token

        # Format the response
        note_list_response = NoteListResponse(
            notes=[NoteResponse.from_dynamodb_item(note) for note in notes],
            pagination=pagination
        )

        return format_response(note_list_response.model_dump())

    except Exception as e:
        # Log the error for debugging
        print(f"Error listing notes: {str(e)}")
        return format_error(str(e))
