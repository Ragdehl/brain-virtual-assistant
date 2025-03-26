"""
Pytest tests for the generate_embeddings Lambda function.
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
    os.environ["OPENAI_API_KEY"] = "fake-api-key"
    yield
    # Clean up environment variables if needed
    # os.environ.pop("DYNAMODB_TABLE", None)


@pytest.fixture
def sample_event():
    """Create a sample API Gateway event."""
    return {
        "noteId": "test-note-id",
        "userId": "test-user",
        "content": "This is the content of the test note."
    }


@pytest.fixture
def sample_context():
    """Create a sample Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = "generate-embeddings"
            self.aws_request_id = "test-request-id"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:generate-embeddings"

    return MockContext()


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings."""
    return [0.1, 0.2, 0.3, 0.4, 0.5]


def test_generate_embeddings_success(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_embeddings,
    mocker: MockerFixture
):
    """Test successful embedding generation."""
    # Mock the OpenAI client
    mock_openai = mocker.patch("app.OpenAI")
    mock_openai_instance = mock_openai.return_value
    mock_embeddings_response = mocker.MagicMock()
    mock_embeddings_response.data = [mocker.MagicMock(embedding=mock_embeddings)]
    mock_openai_instance.embeddings.create.return_value = mock_embeddings_response
    
    # Mock DynamoDBUtil.update_item
    mock_dynamodb_update = mocker.patch("app.dynamodb_util.update_item")
    
    # Call the Lambda handler
    response = lambda_handler(sample_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "message" in response
    assert response["message"] == "Embeddings generated successfully"
    assert "embeddings" in response
    assert response["embeddings"] == mock_embeddings
    
    # Verify OpenAI client was initialized with the correct API key
    mock_openai.assert_called_once_with(api_key="fake-api-key")
    
    # Verify OpenAI embeddings.create was called with correct parameters
    mock_openai_instance.embeddings.create.assert_called_once_with(
        input="This is the content of the test note.",
        model="text-embedding-ada-002"
    )
    
    # Verify DynamoDBUtil.update_item was called with correct parameters
    mock_dynamodb_update.assert_called_once()
    update_args = mock_dynamodb_update.call_args[1]
    assert update_args["key"]["userId"] == "test-user"
    assert update_args["key"]["noteId"] == "test-note-id"
    assert "embeddings" in update_args["updates"]
    assert update_args["updates"]["embeddings"] == mock_embeddings


def test_generate_embeddings_missing_required_fields(
    mock_env_vars,
    sample_context,
    mocker: MockerFixture
):
    """Test embedding generation with missing required fields."""
    # Create an event with missing fields
    incomplete_event = {
        "noteId": "test-note-id",
        # Missing userId and content
    }
    
    # Mock the ValidationError
    mock_validation_error = mocker.patch("app.ValidationError")
    
    # Call the Lambda handler, expecting ValidationError
    with pytest.raises(Exception):
        lambda_handler(incomplete_event, sample_context)
    
    # Verify ValidationError was called
    mock_validation_error.assert_called_once()


def test_generate_embeddings_openai_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mocker: MockerFixture
):
    """Test embedding generation with OpenAI API error."""
    # Mock the OpenAI client to raise an exception
    mock_openai = mocker.patch("app.OpenAI")
    mock_openai_instance = mock_openai.return_value
    mock_openai_instance.embeddings.create.side_effect = Exception("OpenAI API error")
    
    # Mock the ServerError
    mock_server_error = mocker.patch("app.ServerError")
    
    # Call the Lambda handler, expecting ServerError
    with pytest.raises(Exception):
        lambda_handler(sample_event, sample_context)
    
    # Verify ServerError was called with correct message
    mock_server_error.assert_called_once()


def test_generate_embeddings_dynamodb_error(
    mock_env_vars,
    sample_event,
    sample_context,
    mock_embeddings,
    mocker: MockerFixture
):
    """Test embedding generation with DynamoDB error."""
    # Mock the OpenAI client
    mock_openai = mocker.patch("app.OpenAI")
    mock_openai_instance = mock_openai.return_value
    mock_embeddings_response = mocker.MagicMock()
    mock_embeddings_response.data = [mocker.MagicMock(embedding=mock_embeddings)]
    mock_openai_instance.embeddings.create.return_value = mock_embeddings_response
    
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


def test_generate_embeddings_direct_invocation(
    mock_env_vars,
    sample_context,
    mock_embeddings,
    mocker: MockerFixture
):
    """Test embedding generation with direct invocation (text parameter)."""
    # Create a direct invocation event
    direct_event = {
        "text": "This is some text to generate embeddings for."
    }
    
    # Mock the OpenAI client
    mock_openai = mocker.patch("app.OpenAI")
    mock_openai_instance = mock_openai.return_value
    mock_embeddings_response = mocker.MagicMock()
    mock_embeddings_response.data = [mocker.MagicMock(embedding=mock_embeddings)]
    mock_openai_instance.embeddings.create.return_value = mock_embeddings_response
    
    # No need to mock DynamoDBUtil.update_item since it shouldn't be called
    
    # Call the Lambda handler
    response = lambda_handler(direct_event, sample_context)
    
    # Assert the response structure
    assert isinstance(response, dict)
    assert "embeddings" in response
    assert response["embeddings"] == mock_embeddings
    
    # Verify OpenAI embeddings.create was called with correct parameters
    mock_openai_instance.embeddings.create.assert_called_once_with(
        input="This is some text to generate embeddings for.",
        model="text-embedding-ada-002"
    ) 