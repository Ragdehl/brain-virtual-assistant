"""
Pytest tests for the search_notes Lambda function.
"""
import json
import os
from typing import Dict, Any, List
import numpy as np

import pytest
from pytest_mock import MockerFixture

# Import the Lambda handler and related functions
from app import lambda_handler, perform_text_search, perform_semantic_search, generate_embeddings, cosine_similarity


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    os.environ["DYNAMODB_TABLE"] = "test-table"
    os.environ["EMBEDDING_FUNCTION"] = "test-embedding-function"
    yield
    # Clean up environment variables if needed
    # os.environ.pop("DYNAMODB_TABLE", None)
    # os.environ.pop("EMBEDDING_FUNCTION", None)


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "search-notes"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:search-notes"

    return MockContext()


@pytest.fixture
def sample_text_search_event():
    """Create a sample event for text search."""
    return {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "searchType": "text",
            "query": "test query",
            "tags": ["test", "example"],
            "fromDate": "2021-01-01T00:00:00Z",
            "toDate": "2021-12-31T23:59:59Z",
            "limit": 20
        })
    }


@pytest.fixture
def sample_semantic_search_event():
    """Create a sample event for semantic search."""
    return {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "searchType": "semantic",
            "query": "test query",
            "limit": 10
        })
    }


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
                "folder": "test-folder",
                "embeddings": [0.1, 0.2, 0.3]
            },
            {
                "userId": "test-user",
                "noteId": "note-2",
                "title": "Test Note 2",
                "s3Key": "notes/test-user/note-2.md",
                "createdAt": "2021-01-02T00:00:00Z",
                "updatedAt": "2021-01-02T00:00:00Z",
                "tags": ["test"],
                "folder": "test-folder",
                "embeddings": [0.4, 0.5, 0.6]
            }
        ]
    }


@pytest.fixture
def mock_lambda_response():
    """Create a sample Lambda invoke response for embeddings."""
    class MockPayload:
        def read(self):
            return json.dumps({"embeddings": [0.7, 0.8, 0.9]}).encode()

    return {
        "StatusCode": 200,
        "Payload": MockPayload()
    }


def test_cosine_similarity():
    """Test the cosine_similarity function."""
    # Test with valid vectors
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    assert cosine_similarity(vec1, vec2) == 0.0
    
    vec3 = [1.0, 0.0, 0.0]
    vec4 = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec3, vec4) == 1.0
    
    vec5 = [1.0, 1.0, 0.0]
    vec6 = [1.0, 0.0, 1.0]
    similarity = cosine_similarity(vec5, vec6)
    assert 0.0 < similarity < 1.0
    
    # Test with zero vector
    zero_vec = [0.0, 0.0, 0.0]
    assert cosine_similarity(zero_vec, vec1) == 0.0


def test_generate_embeddings(mock_env_vars, mocker: MockerFixture, mock_lambda_response):
    """Test the generate_embeddings function."""
    # Mock the Lambda invoke method
    mock_invoke = mocker.patch("app.lambda_client.invoke")
    mock_invoke.return_value = mock_lambda_response
    
    # Call the function
    embeddings = generate_embeddings("test text")
    
    # Assert the result
    assert embeddings == [0.7, 0.8, 0.9]
    
    # Verify Lambda was called correctly
    mock_invoke.assert_called_once()
    args = mock_invoke.call_args[1]
    assert args["FunctionName"] == "test-embedding-function"
    assert args["InvocationType"] == "RequestResponse"
    assert json.loads(args["Payload"]) == {"text": "test text"}
    
    # Test error handling
    mock_invoke.side_effect = Exception("Lambda error")
    embeddings = generate_embeddings("test text")
    assert len(embeddings) == 3
    assert all(e == 0.0 for e in embeddings)


def test_perform_text_search(mock_env_vars, mocker: MockerFixture, mock_dynamodb_response):
    """Test the perform_text_search function."""
    # Mock DynamoDBUtil.scan
    mock_scan = mocker.patch("app.dynamodb_util.scan")
    mock_scan.return_value = mock_dynamodb_response["Items"]
    
    # Call the function
    results = perform_text_search(
        user_id="test-user",
        query="test",
        tags=["example"],
        from_date="2021-01-01T00:00:00Z",
        to_date="2021-12-31T23:59:59Z",
        limit=10
    )
    
    # Assert the results
    assert len(results) == 2
    assert results[0]["noteId"] == "note-1"  # Should be first due to relevance scoring
    
    # Verify scan was called with correct parameters
    mock_scan.assert_called_once()
    args = mock_scan.call_args[0][0]
    assert args["FilterExpression"] == "userId = :userId AND contains(title, :query) AND (contains(tags, :tag0))"
    assert args["ExpressionAttributeValues"][":userId"] == "test-user"
    assert args["ExpressionAttributeValues"][":query"] == "test"
    assert args["ExpressionAttributeValues"][":tag0"] == "example"
    assert args["ExpressionAttributeValues"][":fromDate"] == "2021-01-01T00:00:00Z"
    assert args["ExpressionAttributeValues"][":toDate"] == "2021-12-31T23:59:59Z"


def test_perform_semantic_search(mock_env_vars, mocker: MockerFixture, mock_dynamodb_response):
    """Test the perform_semantic_search function."""
    # Mock generate_embeddings and DynamoDBUtil.scan
    mock_generate_embeddings = mocker.patch("app.generate_embeddings")
    mock_generate_embeddings.return_value = [0.9, 0.8, 0.7]
    
    mock_scan = mocker.patch("app.dynamodb_util.scan")
    mock_scan.return_value = mock_dynamodb_response["Items"]
    
    # Call the function
    results = perform_semantic_search(
        user_id="test-user",
        query="semantic query",
        limit=10
    )
    
    # Assert the results
    assert len(results) == 2
    # note-2 should be first due to higher cosine similarity with the query embeddings
    assert results[0]["noteId"] == "note-2"
    
    # Verify generate_embeddings was called
    mock_generate_embeddings.assert_called_once_with("semantic query")
    
    # Verify scan was called with correct parameters
    mock_scan.assert_called_once()
    args = mock_scan.call_args[0][0]
    assert args["FilterExpression"] == "userId = :userId"
    assert args["ExpressionAttributeValues"][":userId"] == "test-user"


def test_lambda_handler_text_search(
    mock_env_vars,
    sample_text_search_event,
    sample_context,
    mocker: MockerFixture
):
    """Test the lambda_handler with text search."""
    # Mock perform_text_search
    mock_text_search = mocker.patch("app.perform_text_search")
    mock_text_search.return_value = [
        {
            "userId": "test-user",
            "noteId": "note-1",
            "title": "Test Note 1",
            "s3Key": "notes/test-user/note-1.md",
            "createdAt": "2021-01-01T00:00:00Z",
            "updatedAt": "2021-01-01T00:00:00Z",
            "tags": ["test", "example"],
            "folder": "test-folder"
        }
    ]
    
    # Call the lambda_handler
    response = lambda_handler(sample_text_search_event, sample_context)
    
    # Assert the response
    assert "notes" in response
    assert len(response["notes"]) == 1
    assert response["notes"][0]["noteId"] == "note-1"
    assert "pagination" in response
    assert response["pagination"]["nextToken"] is None
    
    # Verify perform_text_search was called with correct parameters
    mock_text_search.assert_called_once_with(
        "test-user",
        "test query",
        ["test", "example"],
        "2021-01-01T00:00:00Z",
        "2021-12-31T23:59:59Z",
        20
    )


def test_lambda_handler_semantic_search(
    mock_env_vars,
    sample_semantic_search_event,
    sample_context,
    mocker: MockerFixture
):
    """Test the lambda_handler with semantic search."""
    # Mock perform_semantic_search
    mock_semantic_search = mocker.patch("app.perform_semantic_search")
    mock_semantic_search.return_value = [
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
    ]
    
    # Call the lambda_handler
    response = lambda_handler(sample_semantic_search_event, sample_context)
    
    # Assert the response
    assert "notes" in response
    assert len(response["notes"]) == 1
    assert response["notes"][0]["noteId"] == "note-2"
    assert "pagination" in response
    assert response["pagination"]["nextToken"] is None
    
    # Verify perform_semantic_search was called with correct parameters
    mock_semantic_search.assert_called_once_with(
        "test-user",
        "test query",
        None,
        None,
        None,
        10
    )


def test_lambda_handler_invalid_search_type(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test the lambda_handler with an invalid search type."""
    # Create an event with invalid search type
    invalid_event = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "searchType": "invalid",
            "query": "test query"
        })
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the lambda_handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(invalid_event, sample_context)


def test_lambda_handler_missing_query(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test the lambda_handler with missing query."""
    # Create an event with missing query
    invalid_event = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "searchType": "text"
            # Missing query
        })
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the lambda_handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(invalid_event, sample_context) 