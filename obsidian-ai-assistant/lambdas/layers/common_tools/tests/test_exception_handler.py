"""
Pytest tests for exception_handler decorator in the common tools layer.
"""
import sys
import os
import pytest
import json
from unittest.mock import MagicMock, patch

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))

from lib.exception_handler import exception_handler
from lib.exceptions import ValidationError, NotFoundError, ServerError


# Sample lambda_context for testing
class LambdaContext:
    def __init__(self):
        self.function_name = "test-function"
        self.aws_request_id = "test-request-id"


@pytest.fixture
def lambda_context():
    """Create a sample Lambda context for testing."""
    return LambdaContext()


class TestExceptionHandler:
    """Tests for the exception_handler decorator."""

    def test_successful_execution(self, lambda_context):
        """Test that the decorator passes through successful responses."""
        # Define a handler function that returns a successful response
        @exception_handler
        def test_handler(event, context):
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Success"}),
                "headers": {"Content-Type": "application/json"}
            }

        # Call the decorated handler
        event = {"body": json.dumps({"test": "data"})}
        response = test_handler(event, lambda_context)

        # Assert the response is unchanged
        assert response["statusCode"] == 200
        assert json.loads(response["body"]) == {"message": "Success"}
        assert response["headers"]["Content-Type"] == "application/json"

    def test_validation_error(self, lambda_context):
        """Test that ValidationError is properly handled."""
        # Define a handler that raises a ValidationError
        @exception_handler
        def test_handler(event, context):
            raise ValidationError("Invalid request parameters")

        # Call the decorated handler
        event = {"body": json.dumps({"test": "data"})}
        response = test_handler(event, lambda_context)

        # Assert the response is a 400 Bad Request
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "error" in response_body
        assert "Invalid request parameters" in response_body["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_not_found_error(self, lambda_context):
        """Test that NotFoundError is properly handled."""
        # Define a handler that raises a NotFoundError
        @exception_handler
        def test_handler(event, context):
            raise NotFoundError("Resource not found")

        # Call the decorated handler
        event = {"body": json.dumps({"test": "data"})}
        response = test_handler(event, lambda_context)

        # Assert the response is a 404 Not Found
        assert response["statusCode"] == 404
        response_body = json.loads(response["body"])
        assert "error" in response_body
        assert "Resource not found" in response_body["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_server_error(self, lambda_context):
        """Test that ServerError is properly handled."""
        # Define a handler that raises a ServerError
        @exception_handler
        def test_handler(event, context):
            raise ServerError("Internal server error")

        # Call the decorated handler
        event = {"body": json.dumps({"test": "data"})}
        response = test_handler(event, lambda_context)

        # Assert the response is a 500 Internal Server Error
        assert response["statusCode"] == 500
        response_body = json.loads(response["body"])
        assert "error" in response_body
        assert "Internal server error" in response_body["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_generic_exception(self, lambda_context):
        """Test that generic exceptions are properly handled."""
        # Define a handler that raises a generic Exception
        @exception_handler
        def test_handler(event, context):
            raise Exception("Unexpected error")

        # Call the decorated handler
        event = {"body": json.dumps({"test": "data"})}
        response = test_handler(event, lambda_context)

        # Assert the response is a 500 Internal Server Error
        assert response["statusCode"] == 500
        response_body = json.loads(response["body"])
        assert "error" in response_body
        assert "Unexpected error" in response_body["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_malformed_json_event(self, lambda_context):
        """Test handling of events with malformed JSON in body."""
        # Define a handler that processes the event body
        @exception_handler
        def test_handler(event, context):
            # This would raise a JSONDecodeError if the decorator didn't handle it
            body = json.loads(event.get("body", "{}"))
            return {
                "statusCode": 200,
                "body": json.dumps({"received": body}),
                "headers": {"Content-Type": "application/json"}
            }

        # Call the decorated handler with malformed JSON
        event = {"body": "{invalid_json:"}
        response = test_handler(event, lambda_context)

        # Assert the response is a 400 Bad Request
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "error" in response_body
        assert "Invalid JSON" in response_body["error"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_missing_event_body(self, lambda_context):
        """Test handling of events with missing body."""
        # Define a handler that expects a body
        @exception_handler
        def test_handler(event, context):
            body = json.loads(event.get("body", "{}"))
            return {
                "statusCode": 200,
                "body": json.dumps({"received": body}),
                "headers": {"Content-Type": "application/json"}
            }

        # Call the decorated handler with no body
        event = {}
        response = test_handler(event, lambda_context)

        # Assert the response is successful with an empty object
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["received"] == {}
        assert response["headers"]["Content-Type"] == "application/json"

    def test_logging_on_error(self, lambda_context):
        """Test that errors are logged."""
        # Mock the logger
        with patch("lib.exception_handler.logger") as mock_logger:
            # Define a handler that raises an exception
            @exception_handler
            def test_handler(event, context):
                raise ValidationError("Test error")

            # Call the decorated handler
            event = {"body": json.dumps({"test": "data"})}
            test_handler(event, lambda_context)

            # Assert that the logger was called with the error
            mock_logger.error.assert_called_once()
            # Check that the error message is in the log
            assert "Test error" in mock_logger.error.call_args[0][0] 