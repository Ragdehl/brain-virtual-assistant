"""
Pytest tests for the list_notes Lambda function.
"""
import json
import os
from typing import Dict, Any
import base64

import pytest
from pytest_mock import MockerFixture

# Import the Lambda handler
from app import lambda_handler


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    os.environ["DYNAMODB_TABLE"] = "test-table"
    yield
    # Clean up environment variables if needed
    # os.environ.pop("DYNAMODB_TABLE", None)


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "queryStringParameters": {
            "limit": "20",
            "tag": "test"
        }
    }


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "list-notes"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:list-notes"

    return MockContext()


@pytest.fixture
def mock_dynamodb_response():
    """Create a sample DynamoDB response."""
    return {
        "Items": [
            {
                "userId": "test-user",
                "noteId": "note-1",
                "title": "Test Note 1",
                "s3Key": "notes/test-user/note-1.md",
                "createdAt": "2021-01-01T00:00:00Z",
                "updatedAt": "2021-01-01T00:00:00Z",
                "tags": ["test", "example"],
                "folder": "test-folder"
            },
            {
                "userId": "test-user",
                "noteId": "note-2",
                "title": "Test Note 2",
                "s3Key": "notes/test-user/note-2.md",
                "createdAt": "2021-01-02T00:00:00Z",
                "updatedAt": "2021-01-02T00:00:00Z",
                "tags": ["test"],
                "folder": "test-folder"
            }
        ],
        "Count": 2,
        "ScannedCount": 2,
        "LastEvaluatedKey": {
            "userId": "test-user",
            "noteId": "note-2"
        }
    }


def test_list_notes_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_dynamodb_response,
    mocker: MockerFixture
):
    """Test successful notes listing."""
    # Mock DynamoDBUtil.query to return mock_dynamodb_response
    mock_query = mocker.patch("app.dynamodb_util.query")
    mock_query.return_value = mock_dynamodb_response

    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)

    # Assert the response structure
    assert isinstance(response, dict)
    assert "notes" in response
    assert "pagination" in response
    
    # Check notes array
    assert len(response["notes"]) == 2
    assert response["notes"][0]["noteId"] == "note-1"
    assert response["notes"][1]["noteId"] == "note-2"
    
    # Check pagination token
    assert response["pagination"]["nextToken"] is not None
    
    # Verify DynamoDBUtil.query was called with correct parameters
    mock_query.assert_called_once()
    args = mock_query.call_args[0][0]
    assert args["KeyConditionExpression"] == "userId = :userId"
    assert args["ExpressionAttributeValues"][":userId"] == "test-user"
    assert args["FilterExpression"] == "contains(tags, :tag)"
    assert args["ExpressionAttributeValues"][":tag"] == "test"
    assert args["Limit"] == 20


def test_list_notes_no_results(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test listing when no notes are found."""
    # Mock DynamoDBUtil.query to return empty response
    mock_query = mocker.patch("app.dynamodb_util.query")
    mock_query.return_value = {"Items": []}

    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)

    # Assert the response structure
    assert isinstance(response, dict)
    assert "notes" in response
    assert "pagination" in response
    
    # Check notes array is empty
    assert len(response["notes"]) == 0
    
    # Check pagination token is None
    assert response["pagination"]["nextToken"] is None


def test_list_notes_with_next_token(
    mock_env_vars,
    sample_context,
    mock_dynamodb_response,
    mocker: MockerFixture
):
    """Test listing notes with pagination token."""
    # Create a token for testing
    exclusive_start_key = {"userId": "test-user", "noteId": "start-note"}
    next_token = base64.b64encode(json.dumps(exclusive_start_key).encode('utf-8')).decode('utf-8')
    
    # Create event with next token
    event_with_token = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "queryStringParameters": {
            "nextToken": next_token
        }
    }
    
    # Mock DynamoDBUtil.query to return mock_dynamodb_response
    mock_query = mocker.patch("app.dynamodb_util.query")
    mock_query.return_value = mock_dynamodb_response

    # Call the Lambda handler
    response = lambda_handler(event_with_token, sample_context)

    # Verify DynamoDBUtil.query was called with correct parameters including ExclusiveStartKey
    mock_query.assert_called_once()
    args = mock_query.call_args[0][0]
    assert "ExclusiveStartKey" in args
    assert args["ExclusiveStartKey"] == exclusive_start_key


def test_list_notes_invalid_pagination_token(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test listing notes with invalid pagination token."""
    # Create event with invalid token
    event_with_invalid_token = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "queryStringParameters": {
            "nextToken": "invalid-token"
        }
    }
    
    # Mock ValidationError to verify it's raised
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError to be raised
    with pytest.raises(Exception):
        lambda_handler(event_with_invalid_token, sample_context)
        
    # Verify ValidationError was called with correct message
    mock_validation_error.assert_called_with("Invalid pagination token")


def test_list_notes_date_filter(
    mock_env_vars,
    sample_context,
    mock_dynamodb_response,
    mocker: MockerFixture
):
    """Test listing notes with date filters."""
    # Create event with date filters
    event_with_dates = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "queryStringParameters": {
            "fromDate": "2021-01-01T00:00:00Z",
            "toDate": "2021-01-31T23:59:59Z"
        }
    }
    
    # Mock DynamoDBUtil.query
    mock_query = mocker.patch("app.dynamodb_util.query")
    mock_query.return_value = mock_dynamodb_response

    # Call the Lambda handler
    lambda_handler(event_with_dates, sample_context)

    # Verify DynamoDBUtil.query was called with correct parameters
    mock_query.assert_called_once()
    args = mock_query.call_args[0][0]
    assert "IndexName" in args
    assert args["IndexName"] == "createdAtIndex"
    assert args["KeyConditionExpression"] == "userId = :userId AND createdAt BETWEEN :fromDate AND :toDate"
    assert args["ExpressionAttributeValues"][":fromDate"] == "2021-01-01T00:00:00Z"
    assert args["ExpressionAttributeValues"][":toDate"] == "2021-01-31T23:59:59Z"


def test_list_notes_invalid_limit(
    mock_env_vars,
    sample_context,
    mock_dynamodb_response,
    mocker: MockerFixture
):
    """Test listing notes with invalid limit parameter."""
    # Create event with invalid limit
    event_with_invalid_limit = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "queryStringParameters": {
            "limit": "999" # Too high
        }
    }
    
    # Mock DynamoDBUtil.query
    mock_query = mocker.patch("app.dynamodb_util.query")
    mock_query.return_value = mock_dynamodb_response

    # Call the Lambda handler
    lambda_handler(event_with_invalid_limit, sample_context)

    # Verify DynamoDBUtil.query was called with corrected limit of 50
    mock_query.assert_called_once()
    args = mock_query.call_args[0][0]
    assert args["Limit"] == 50 