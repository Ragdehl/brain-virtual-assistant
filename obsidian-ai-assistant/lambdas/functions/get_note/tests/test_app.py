"""
Tests for the get_note Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import boto3
from botocore.stub import Stubber

# Import the Lambda handler
from app import lambda_handler


class TestGetNote(unittest.TestCase):
    """
    Test cases for the get_note Lambda function.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        # Mock environment variables
        os.environ["DYNAMODB_TABLE"] = "test-table"
        os.environ["S3_BUCKET"] = "test-bucket"

        # Create a sample event
        self.event = {
            "requestContext": {
                "authorizer": {
                    "userId": "test-user"
                }
            },
            "pathParameters": {
                "id": "test-note-id"
            }
        }

        # Create a sample context
        self.context = MagicMock()
        self.context.aws_request_id = "test-request-id"

        # Create a sample note
        self.note = {
            "id": "test-note-id",
            "userId": "test-user",
            "title": "Test Note",
            "s3Key": "notes/test-user/test-note-id.md",
            "createdAt": "2023-01-01T00:00:00.000Z",
            "updatedAt": "2023-01-01T00:00:00.000Z",
            "tags": ["test", "example"],
            "folder": "test-folder"
        }

        # Create a sample note content
        self.note_content = "This is a test note."

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    @patch("app.dynamodb_util")
    @patch("app.s3_util")
    def test_get_note_success(
        self,
        mock_s3_util,
        mock_dynamodb_util,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test successful note retrieval.
        """
        # Mock the DynamoDB get_item method
        mock_dynamodb_util.get_item.return_value = self.note

        # Mock the S3 get_object_content method
        mock_s3_util.get_object_content.return_value = self.note_content

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 200)
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

        # Assert that the DynamoDB get_item method was called
        mock_dynamodb_util.get_item.assert_called_once_with({
            "id": "test-note-id",
            "userId": "test-user"
        })

        # Assert that the S3 get_object_content method was called
        mock_s3_util.get_object_content.assert_called_once_with("notes/test-user/test-note-id.md")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    def test_get_note_missing_user_id(
        self,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note retrieval with missing user ID.
        """
        # Create an event with missing user ID
        event = {
            "requestContext": {
                "authorizer": {}
            },
            "pathParameters": {
                "id": "test-note-id"
            }
        }

        # Call the Lambda handler
        response = lambda_handler(event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "User ID is required")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    def test_get_note_missing_note_id(
        self,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note retrieval with missing note ID.
        """
        # Create an event with missing note ID
        event = {
            "requestContext": {
                "authorizer": {
                    "userId": "test-user"
                }
            },
            "pathParameters": {}
        }

        # Call the Lambda handler
        response = lambda_handler(event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Note ID is required")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    @patch("app.dynamodb_util")
    def test_get_note_not_found(
        self,
        mock_dynamodb_util,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note retrieval with non-existent note.
        """
        # Mock the DynamoDB get_item method to return None
        mock_dynamodb_util.get_item.return_value = None

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Note not found")

    @patch("app.log_event")
    @patch("app.log_response")
    @patch("app.log_error")
    @patch("app.dynamodb_util")
    @patch("app.s3_util")
    def test_get_note_content_not_found(
        self,
        mock_s3_util,
        mock_dynamodb_util,
        mock_log_error,
        mock_log_response,
        mock_log_event
    ):
        """
        Test note retrieval with non-existent note content.
        """
        # Mock the DynamoDB get_item method
        mock_dynamodb_util.get_item.return_value = self.note

        # Mock the S3 get_object_content method to raise FileNotFoundError
        mock_s3_util.get_object_content.side_effect = FileNotFoundError("Object not found")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Assert that the response is correct
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("body", response)

        # Parse the response body
        body = json.loads(response["body"])
        self.assertFalse(body["success"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["message"], "Note content not found")


if __name__ == "__main__":
    unittest.main() 