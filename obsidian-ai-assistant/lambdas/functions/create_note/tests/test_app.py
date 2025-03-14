"""
Tests for the create_note Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import boto3
from botocore.stub import Stubber

# Import the Lambda handler
from app import lambda_handler


class TestCreateNote(unittest.TestCase):
    """
    Test cases for the create_note Lambda function.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        # Mock environment variables
        os.environ["DYNAMODB_TABLE"] = "test-table"
        os.environ["S3_BUCKET"] = "test-bucket"
        os.environ["EMBEDDINGS_FUNCTION"] = "test-embeddings-function"

        # Create a sample event
        self.event = {
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

        # Create a sample context
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    @patch("app.dynamodb_util")
    @patch("app.s3_util")
    @patch("app.lambda_client")
    @patch("app.generate_note_id")
    def test_create_note_success(
        self,
        mock_generate_note_id,
        mock_lambda_client,
        mock_s3_util,
        mock_dynamodb_util,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test successful note creation.
        """
        # Mock the generate_note_id function
        mock_generate_note_id.return_value = "test-note-id"

        # Mock the S3 put_object method
        mock_s3_util.put_object.return_value = {}

        # Mock the DynamoDB put_item method
        mock_dynamodb_util.put_item.return_value = {}

        # Mock the Lambda invoke method
        mock_lambda_client.invoke.return_value = {}

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 201)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertTrue(body["success"])
        self.assertIn("data", body)
        self.assertEqual(body["data"]["id"], "test-note-id")
        self.assertEqual(body["data"]["title"], "Test Note")
        self.assertEqual(body["data"]["content"], "This is a test note.")
        self.assertEqual(body["data"]["tags"], ["test", "example"])
        self.assertEqual(body["data"]["folder"], "test-folder")

        # Assert that the S3 put_object method was called
        mock_s3_util.put_object.assert_called_once()
        args, kwargs = mock_s3_util.put_object.call_args
        self.assertEqual(kwargs["key"], "notes/test-user/test-note-id.md")
        self.assertEqual(kwargs["body"], "This is a test note.")
        self.assertEqual(kwargs["content_type"], "text/markdown")

        # Assert that the DynamoDB put_item method was called
        mock_dynamodb_util.put_item.assert_called_once()

        # Assert that the Lambda invoke method was called
        mock_lambda_client.invoke.assert_called_once()
        args, kwargs = mock_lambda_client.invoke.call_args
        self.assertEqual(kwargs["FunctionName"], "test-embeddings-function")
        self.assertEqual(kwargs["InvocationType"], "Event")
        payload = json.loads(kwargs["Payload"])
        self.assertEqual(payload["noteId"], "test-note-id")
        self.assertEqual(payload["userId"], "test-user")
        self.assertEqual(payload["content"], "This is a test note.")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    def test_create_note_missing_user_id(
        self,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note creation with missing user ID.
        """
        # Create an event with missing user ID
        event = {
            "requestContext": {
                "authorizer": {}
            },
            "body": json.dumps({
                "title": "Test Note",
                "content": "This is a test note."
            })
        }

        # Call the Lambda handler
        response = lambda_handler(event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "User ID is required")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    def test_create_note_missing_title(
        self,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note creation with missing title.
        """
        # Create an event with missing title
        event = {
            "requestContext": {
                "authorizer": {
                    "userId": "test-user"
                }
            },
            "body": json.dumps({
                "content": "This is a test note."
            })
        }

        # Call the Lambda handler
        response = lambda_handler(event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Validation error")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    def test_create_note_missing_content(
        self,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note creation with missing content.
        """
        # Create an event with missing content
        event = {
            "requestContext": {
                "authorizer": {
                    "userId": "test-user"
                }
            },
            "body": json.dumps({
                "title": "Test Note"
            })
        }

        # Call the Lambda handler
        response = lambda_handler(event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Validation error")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    @patch("app.dynamodb_util")
    @patch("app.s3_util")
    def test_create_note_s3_error(
        self,
        mock_s3_util,
        mock_dynamodb_util,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note creation with S3 error.
        """
        # Mock the S3 put_object method to raise an exception
        mock_s3_util.put_object.side_effect = Exception("S3 error")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Error creating note")

        # Assert that the log_error method was called
        mock_log_error.assert_called_once()


if __name__ == "__main__":
    unittest.main() 