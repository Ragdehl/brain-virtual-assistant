"""
Tests for the generate_embeddings Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch

import boto3
from moto import mock_dynamodb

# Import the Lambda handler
from lambdas.functions.generate_embeddings.app import lambda_handler


class TestGenerateEmbeddings(unittest.TestCase):
    """Test cases for the generate_embeddings Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_patcher = patch.dict(os.environ, {
            "DYNAMODB_TABLE": "obsidian-ai-assistant-notes-test",
            "STAGE": "test"
        })
        self.env_patcher.start()

        # Set up mock DynamoDB
        self.dynamodb_mock = mock_dynamodb()
        self.dynamodb_mock.start()

        # Create the mock table
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        self.table = self.dynamodb.create_table(
            TableName="obsidian-ai-assistant-notes-test",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "noteId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "noteId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "createdAtIndex",
                    "KeySchema": [
                        {"AttributeName": "userId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Add a test note to DynamoDB
        self.user_id = "test-user-123"
        self.note_id = "test-note-123"
        self.note = {
            "userId": self.user_id,
            "noteId": self.note_id,
            "title": "Test Note",
            "createdAt": "2023-05-01T12:00:00Z",
            "updatedAt": "2023-05-01T12:00:00Z",
            "tags": ["test", "embeddings"],
            "contentType": "text/markdown",
            "contentLength": 100,
            "contentHash": "test-hash"
            # No embeddings yet
        }

        self.table.put_item(Item=self.note)

    def tearDown(self):
        """Tear down test fixtures."""
        self.dynamodb_mock.stop()
        self.env_patcher.stop()

    @patch('lambdas.functions.generate_embeddings.app.generate_embeddings')
    def test_generate_embeddings_for_note(self, mock_generate_embeddings):
        """Test generating embeddings for a note."""
        # Mock the embedding generation function
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_generate_embeddings.return_value = mock_embeddings

        # Create a mock event
        event = {
            'userId': self.user_id,
            'noteId': self.note_id,
            'content': "# Test Note\n\nThis is a test note for generating embeddings."
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['embeddings'], mock_embeddings)

        # Verify the DynamoDB item was updated
        updated_item = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        ).get("Item")

        self.assertIn("embeddings", updated_item)
        self.assertEqual(updated_item["embeddings"], mock_embeddings)

    @patch('lambdas.functions.generate_embeddings.app.generate_embeddings')
    def test_generate_embeddings_for_text(self, mock_generate_embeddings):
        """Test generating embeddings for arbitrary text."""
        # Mock the embedding generation function
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_generate_embeddings.return_value = mock_embeddings

        # Create a mock event
        event = {
            'text': "This is some text to generate embeddings for."
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['embeddings'], mock_embeddings)

    def test_generate_embeddings_missing_parameters(self):
        """Test generating embeddings with missing parameters."""
        # Create a mock event with neither note info nor text
        event = {}

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        self.assertIn("error", json.loads(response['body']))

    @patch('lambdas.functions.generate_embeddings.app.generate_embeddings')
    def test_generate_embeddings_note_not_found(self, mock_generate_embeddings):
        """Test generating embeddings for a non-existent note."""
        # Mock the embedding generation function
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_generate_embeddings.return_value = mock_embeddings

        # Create a mock event with non-existent note
        event = {
            'userId': self.user_id,
            'noteId': "non-existent-note",
            'content': "This note doesn't exist."
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        self.assertIn("error", json.loads(response['body']))

    @patch('lambdas.functions.generate_embeddings.app.generate_embeddings')
    def test_generate_embeddings_error_handling(self, mock_generate_embeddings):
        """Test error handling during embedding generation."""
        # Mock the embedding generation function to raise an exception
        mock_generate_embeddings.side_effect = Exception("Embedding generation failed")

        # Create a mock event
        event = {
            'text': "This should fail."
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        self.assertIn("error", json.loads(response['body']))


if __name__ == "__main__":
    unittest.main()
