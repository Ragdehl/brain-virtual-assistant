"""
Pytest tests for the create_note Lambda function.
"""
import json
import os
import uuid
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
        "body": json.dumps({
            "title": "Test Note",
            "content": "This is a test note.",
            "tags": ["test", "example"],
            "folder": "test-folder"
        })
    }


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "create-note"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:create-note"

    return MockContext()


@pytest.fixture
def mock_uuid(mocker: MockerFixture):
    """Mock uuid4 to return a predictable value."""
    mock = mocker.patch('uuid.uuid4')
    mock.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    return mock


def test_create_note_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_uuid,
    mocker: MockerFixture
):
    """Test successful note creation."""
    # Mock the DynamoDBUtil and S3Util methods
    mock_s3_put = mocker.patch("app.s3_util.put_object")
    mock_dynamodb_put = mocker.patch("app.dynamodb_util.put_item")
    mock_lambda_invoke = mocker.patch("app.lambda_client.invoke")
    
    # Mock the current time
    mock_time = mocker.patch("app.datetime")
    mock_time.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00Z"
    
    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert "noteId" in response
    assert response["noteId"] == "12345678-1234-5678-1234-567812345678"
    assert response["title"] == "Test Note"
    
    # Verify S3 put_object was called with correct parameters
    mock_s3_put.assert_called_once()
    s3_args = mock_s3_put.call_args[1]
    assert s3_args["key"] == "notes/test-user/12345678-1234-5678-1234-567812345678.md"
    assert s3_args["body"] == "This is a test note."
    assert s3_args["content_type"] == "text/markdown"
    
    # Verify DynamoDB put_item was called with correct parameters
    mock_dynamodb_put.assert_called_once()
    dynamodb_args = mock_dynamodb_put.call_args[1]
    assert dynamodb_args["item"]["userId"] == "test-user"
    assert dynamodb_args["item"]["noteId"] == "12345678-1234-5678-1234-567812345678"
    assert dynamodb_args["item"]["title"] == "Test Note"
    assert dynamodb_args["item"]["s3Key"] == "notes/test-user/12345678-1234-5678-1234-567812345678.md"
    assert dynamodb_args["item"]["createdAt"] == "2023-01-01T00:00:00Z"
    assert dynamodb_args["item"]["tags"] == ["test", "example"]
    assert dynamodb_args["item"]["folder"] == "test-folder"
    
    # Verify Lambda invoke was called for generating embeddings
    mock_lambda_invoke.assert_called_once()
    lambda_args = mock_lambda_invoke.call_args[1]
    assert lambda_args["FunctionName"] == "test-embeddings-function"
    assert lambda_args["InvocationType"] == "Event"
    payload = json.loads(lambda_args["Payload"])
    assert payload["noteId"] == "12345678-1234-5678-1234-567812345678"
    assert payload["userId"] == "test-user"
    assert payload["content"] == "This is a test note."


def test_create_note_missing_title(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note creation with missing title."""
    # Create an event with missing title
    event_missing_title = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "content": "This is a test note."
        })
    }
    
    # Mock the ValidationError
    mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_title, sample_context)


def test_create_note_missing_content(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test note creation with missing content."""
    # Create an event with missing content
    event_missing_content = {
        "requestContext": {
            "authorizer": {
                "userId": "test-user"
            }
        },
        "body": json.dumps({
            "title": "Test Note"
        })
    }
    
    # Mock the ValidationError
    mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(event_missing_content, sample_context)


def test_create_note_s3_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_uuid,
    mocker: MockerFixture
):
    """Test note creation with S3 error."""
    # Mock S3Util.put_object to raise an exception
    mock_s3_put = mocker.patch("app.s3_util.put_object")
    mock_s3_put.side_effect = Exception("S3 error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called with correct message
    mock_server_error.assert_called_once()


def test_create_note_dynamodb_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_uuid,
    mocker: MockerFixture
):
    """Test note creation with DynamoDB error."""
    # Mock S3Util.put_object
    mocker.patch("app.s3_util.put_object")
    
    # Mock DynamoDBUtil.put_item to raise an exception
    mock_dynamodb_put = mocker.patch("app.dynamodb_util.put_item")
    mock_dynamodb_put.side_effect = Exception("DynamoDB error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called with correct message
    mock_server_error.assert_called_once() 