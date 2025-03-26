"""
Pytest tests for the get_note Lambda function.
"""
import json
import os
from typing import Dict, Any

import pytest
from pytest_mock import MockerFixture

# Import the Lambda handler
from app import lambda_handler


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    os.environ["DYNAMODB_TABLE"] = "test-table"
    os.environ["S3_BUCKET"] = "test-bucket"
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
        "pathParameters": {
            "id": "test-note-id"
        }
    }


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "get-note"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:get-note"

    return MockContext()


@pytest.fixture
def mock_note_item():
    """Create a sample DynamoDB note item."""
    return {
        "userId": "test-user",
        "noteId": "test-note-id",
        "title": "Test Note",
        "s3Key": "notes/test-user/test-note-id.md",
        "createdAt": "2023-01-01T00:00:00Z",
        "updatedAt": "2023-01-01T00:00:00Z",
        "tags": ["test", "example"],
        "folder": "test-folder"
    }


@pytest.fixture
def mock_s3_content():
    """Create sample S3 content."""
    return "This is the content of the test note."


def test_get_note_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_note_item,
    mock_s3_content,
    mocker: MockerFixture
):
    """Test successful note retrieval."""
    # Mock DynamoDBUtil.get_item to return the mock note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_note_item
    
    # Mock S3Util.get_object_content to return the mock content
    mock_s3_get = mocker.patch("app.s3_util.get_object_content")
    mock_s3_get.return_value = mock_s3_content
    
    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert response["message"] == "Note retrieved successfully"
    assert response["noteId"] == "test-note-id"
    assert response["title"] == "Test Note"
    assert response["content"] == "This is the content of the test note."
    assert response["tags"] == ["test", "example"]
    assert response["folder"] == "test-folder"
    
    # Verify DynamoDBUtil.get_item was called with correct parameters
    mock_dynamodb_get.assert_called_once_with(
        key={"userId": "test-user", "noteId": "test-note-id"}
    )
    
    # Verify S3Util.get_object_content was called with correct parameters
    mock_s3_get.assert_called_once_with("notes/test-user/test-note-id.md")


def test_get_note_not_found(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test note retrieval when note is not found."""
    # Mock DynamoDBUtil.get_item to raise NotFoundError
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    
    # Create a NotFoundError exception
    not_found_error = mocker.patch("app.NotFoundError")
    mock_dynamodb_get.side_effect = not_found_error
    
    # Call the Lambda handler, expecting NotFoundError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_get_note_content_not_found(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_note_item,
    mocker: MockerFixture
):
    """Test note retrieval when content is not found in S3."""
    # Mock DynamoDBUtil.get_item to return the mock note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_note_item
    
    # Mock S3Util.get_object_content to raise NotFoundError
    mock_s3_get = mocker.patch("app.s3_util.get_object_content")
    
    # Create a NotFoundError exception
    not_found_error = mocker.patch("app.NotFoundError")
    mock_s3_get.side_effect = not_found_error
    
    # Call the Lambda handler, expecting NotFoundError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_get_note_dynamodb_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test note retrieval with DynamoDB error."""
    # Mock DynamoDBUtil.get_item to raise ServerError
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    
    # Create a ServerError exception
    server_error = mocker.patch("app.ServerError")
    mock_dynamodb_get.side_effect = server_error
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_get_note_s3_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_note_item,
    mocker: MockerFixture
):
    """Test note retrieval with S3 error."""
    # Mock DynamoDBUtil.get_item to return the mock note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_note_item
    
    # Mock S3Util.get_object_content to raise ServerError
    mock_s3_get = mocker.patch("app.s3_util.get_object_content")
    
    # Create a ServerError exception
    server_error = mocker.patch("app.ServerError")
    mock_s3_get.side_effect = server_error
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_get_note_missing_id(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note retrieval with missing note ID."""
    # Create an event with missing ID
    event_missing_id = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "pathParameters": {}  # Missing id
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_id, sample_context)
    
    # Verify ValidationError was called with correct message
    mock_validation_error.assert_called_once() 