"""
Pytest tests for the update_note Lambda function.
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
    os.environ["EMBEDDINGS_FUNCTION"] = "test-embeddings-function"
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
        },
        "body": json.dumps({
            "title": "Updated Test Note",
            "content": "This is an updated test note.",
            "tags": ["test", "updated"],
            "folder": "test-folder-updated"
        })
    }


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "update-note"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:update-note"

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


def test_update_note_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test successful note update."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock DynamoDBUtil.update_item
    mock_dynamodb_update = mocker.patch("app.dynamodb_util.update_item")
    mock_dynamodb_update.return_value = {
        **mock_existing_note,
        "title": "Updated Test Note",
        "tags": ["test", "updated"],
        "folder": "test-folder-updated",
        "updatedAt": "2023-01-02T00:00:00Z"
    }
    
    # Mock S3Util.put_object
    mock_s3_put = mocker.patch("app.s3_util.put_object")
    
    # Mock the current time
    mock_time = mocker.patch("app.datetime")
    mock_time.utcnow.return_value.isoformat.return_value = "2023-01-02T00:00:00Z"
    
    # Mock Lambda client
    mock_lambda_invoke = mocker.patch("app.lambda_client.invoke")
    
    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert response["message"] == "Note updated successfully"
    assert response["noteId"] == "test-note-id"
    assert response["title"] == "Updated Test Note"
    assert response["tags"] == ["test", "updated"]
    assert response["folder"] == "test-folder-updated"
    assert response["updatedAt"] == "2023-01-02T00:00:00Z"
    
    # Verify DynamoDBUtil.get_item was called with correct parameters
    mock_dynamodb_get.assert_called_once_with(
        key={"userId": "test-user", "noteId": "test-note-id"}
    )
    
    # Verify DynamoDBUtil.update_item was called with correct parameters
    mock_dynamodb_update.assert_called_once()
    update_args = mock_dynamodb_update.call_args[1]
    assert update_args["key"]["userId"] == "test-user"
    assert update_args["key"]["noteId"] == "test-note-id"
    assert "title" in update_args["updates"]
    assert update_args["updates"]["title"] == "Updated Test Note"
    assert "tags" in update_args["updates"]
    assert update_args["updates"]["tags"] == ["test", "updated"]
    assert "folder" in update_args["updates"]
    assert update_args["updates"]["folder"] == "test-folder-updated"
    assert "updatedAt" in update_args["updates"]
    assert update_args["updates"]["updatedAt"] == "2023-01-02T00:00:00Z"
    
    # Verify S3Util.put_object was called with correct parameters
    mock_s3_put.assert_called_once()
    s3_args = mock_s3_put.call_args[1]
    assert s3_args["key"] == "notes/test-user/test-note-id.md"
    assert s3_args["body"] == "This is an updated test note."
    assert s3_args["content_type"] == "text/markdown"
    
    # Verify Lambda invoke was called for generating embeddings
    mock_lambda_invoke.assert_called_once()
    lambda_args = mock_lambda_invoke.call_args[1]
    assert lambda_args["FunctionName"] == "test-embeddings-function"
    assert lambda_args["InvocationType"] == "Event"
    payload = json.loads(lambda_args["Payload"])
    assert payload["noteId"] == "test-note-id"
    assert payload["userId"] == "test-user"
    assert payload["content"] == "This is an updated test note."


def test_update_note_not_found(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test note update when note is not found."""
    # Mock DynamoDBUtil.get_item to raise NotFoundError
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    
    # Create a NotFoundError exception
    not_found_error = mocker.patch("app.NotFoundError")
    mock_dynamodb_get.side_effect = not_found_error
    
    # Call the Lambda handler, expecting NotFoundError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)


def test_update_note_missing_id(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note update with missing note ID."""
    # Create an event with missing ID
    event_missing_id = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "pathParameters": {},  # Missing id
        "body": json.dumps({
            "title": "Updated Test Note",
            "content": "This is an updated test note."
        })
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_id, sample_context)


def test_update_note_missing_title(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note update with missing title."""
    # Create an event with missing title
    event_missing_title = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "pathParameters": {
            "id": "test-note-id"
        },
        "body": json.dumps({
            "content": "This is an updated test note."
        })
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_title, sample_context)


def test_update_note_missing_content(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note update with missing content."""
    # Create an event with missing content
    event_missing_content = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "pathParameters": {
            "id": "test-note-id"
        },
        "body": json.dumps({
            "title": "Updated Test Note"
        })
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_content, sample_context)


def test_update_note_s3_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test note update with S3 error."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock S3Util.put_object to raise an exception
    mock_s3_put = mocker.patch("app.s3_util.put_object")
    mock_s3_put.side_effect = Exception("S3 error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called
    mock_server_error.assert_called_once()


def test_update_note_dynamodb_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_existing_note,
    mocker: MockerFixture
):
    """Test note update with DynamoDB error."""
    # Mock DynamoDBUtil.get_item to return the existing note
    mock_dynamodb_get = mocker.patch("app.dynamodb_util.get_item")
    mock_dynamodb_get.return_value = mock_existing_note
    
    # Mock S3Util.put_object
    mocker.patch("app.s3_util.put_object")
    
    # Mock DynamoDBUtil.update_item to raise an exception
    mock_dynamodb_update = mocker.patch("app.dynamodb_util.update_item")
    mock_dynamodb_update.side_effect = Exception("DynamoDB error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called
    mock_server_error.assert_called_once() 