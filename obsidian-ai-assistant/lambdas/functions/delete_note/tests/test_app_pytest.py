"""
Pytest tests for the delete_note Lambda function.
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
            self.function_name = "delete-note"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:delete-note"

    return MockContext()


@pytest.fixture
def mock_existing_note():
    """Create a sample existing note in DynamoDB."""
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


def test_delete_note_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test successful note deletion."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock DynamoDBUtil.delete_item
    mock_dynamodb_delete = mocker.patch("app.dynamodb_util.delete_item")
    
    # Mock S3Util.delete_object
    mock_s3_delete = mocker.patch("app.s3_util.delete_object")
    
    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert response["message"] == "Note deleted successfully"
    
    # Verify DynamoDBUtil.get_item was called with correct parameters
    mock_dynamodb_get.assert_called_once_with(
        key={"userId": "test-user", "noteId": "test-note-id"}
    )
    
    # Verify DynamoDBUtil.delete_item was called with correct parameters
    mock_dynamodb_delete.assert_called_once_with(
        key={"userId": "test-user", "noteId": "test-note-id"}
    )
    
    # Verify S3Util.delete_object was called with correct parameters
    mock_s3_delete.assert_called_once_with("notes/test-user/test-note-id.md")


def test_delete_note_not_found(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test note deletion when note is not found."""
    # Mock DynamoDBUtil.get_item to raise NotFoundError
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    
    # Create a NotFoundError exception
    not_found_error = mocker.patch("app.NotFoundError")
    mock_dynamodb_get.side_effect = not_found_error
    
    # Call the Lambda handler, expecting NotFoundError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_delete_note_missing_id(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note deletion with missing note ID."""
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


def test_delete_note_dynamodb_get_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test note deletion with DynamoDB get error."""
    # Mock DynamoDBUtil.get_item to raise ServerError
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    
    # Create a ServerError exception
    server_error = mocker.patch("app.ServerError")
    mock_dynamodb_get.side_effect = server_error
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_delete_note_dynamodb_delete_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test note deletion with DynamoDB delete error."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock DynamoDBUtil.delete_item to raise an exception
    mock_dynamodb_delete = mocker.patch("app.dynamodb_util.delete_item")
    mock_dynamodb_delete.side_effect = Exception("DynamoDB delete error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called
    mock_server_error.assert_called_once()


def test_delete_note_s3_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test note deletion with S3 error but continuing."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock DynamoDBUtil.delete_item
    mock_dynamodb_delete = mocker.patch("app.dynamodb_util.delete_item")
    
    # Mock S3Util.delete_object to raise an exception but handled
    mock_s3_delete = mocker.patch("app.s3_util.delete_object")
    mock_s3_delete.side_effect = Exception("S3 error")
    
    # Mock print to capture the log
    mock_print = mocker.patch("builtins.print")
    
    # Call the Lambda handler - should still succeed since S3 errors are handled
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert response["message"] == "Note deleted successfully"
    
    # Verify S3Util.delete_object was called
    mock_s3_delete.assert_called_once()
    
    # Verify the error was logged
    mock_print.assert_called_once()
    assert "Error deleting note content from S3" in mock_print.call_args[0][0] 