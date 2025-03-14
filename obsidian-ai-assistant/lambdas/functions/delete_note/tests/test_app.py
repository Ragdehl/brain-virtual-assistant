"""
Tests for the delete_note Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import boto3
import pytest
from moto import mock_dynamodb, mock_s3

# Import the Lambda handler
from lambdas.functions.delete_note.app import lambda_handler


class TestDeleteNote(unittest.TestCase):
    """Test cases for the delete_note Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_patcher = patch.dict(os.environ, {
            "DYNAMODB_TABLE": "obsidian-ai-assistant-notes-test",
            "S3_BUCKET": "obsidian-ai-assistant-content-test",
            "STAGE": "test"
        })
        self.env_patcher.start()
        
        # Set up mock AWS services
        self.dynamodb_mock = mock_dynamodb()
        self.dynamodb_mock.start()
        
        self.s3_mock = mock_s3()
        self.s3_mock.start()
        
        # Create the mock DynamoDB table
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
        
        # Create the mock S3 bucket
        self.s3 = boto3.resource("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket="obsidian-ai-assistant-content-test")
        
        # Add a test note to DynamoDB
        self.user_id = "test-user-123"
        self.note_id = "test-note-123"
        self.note = {
            "userId": self.user_id,
            "noteId": self.note_id,
            "title": "Test Note",
            "createdAt": "2023-05-01T12:00:00Z",
            "updatedAt": "2023-05-01T12:00:00Z",
            "tags": ["test", "delete"],
            "contentType": "text/markdown",
            "contentLength": 100,
            "contentHash": "test-hash",
            "embeddings": [0.1, 0.2, 0.3]
        }
        
        self.table.put_item(Item=self.note)
        
        # Add test content to S3
        self.s3_client = boto3.client("s3", region_name="us-east-1")
        self.s3_client.put_object(
            Bucket="obsidian-ai-assistant-content-test",
            Key=f"{self.user_id}/{self.note_id}",
            Body="# Test Note\n\nThis is a test note that will be deleted."
        )

    def tearDown(self):
        """Tear down test fixtures."""
        self.dynamodb_mock.stop()
        self.s3_mock.stop()
        self.env_patcher.stop()

    def test_delete_note_success(self):
        """Test successful deletion of a note."""
        # Create a mock API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "pathParameters": {
                "noteId": self.note_id
            }
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 204)
        
        # Verify the DynamoDB item was deleted
        response = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        )
        self.assertNotIn("Item", response)
        
        # Verify the S3 object was deleted
        with self.assertRaises(self.s3_client.exceptions.NoSuchKey):
            self.s3_client.get_object(
                Bucket="obsidian-ai-assistant-content-test",
                Key=f"{self.user_id}/{self.note_id}"
            )

    def test_delete_note_missing_user_id(self):
        """Test deleting a note with missing user ID."""
        # Create a mock API Gateway event without user ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {}
                }
            },
            "pathParameters": {
                "noteId": self.note_id
            }
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 400)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        
        # Verify the DynamoDB item was not deleted
        response = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        )
        self.assertIn("Item", response)

    def test_delete_note_missing_note_id(self):
        """Test deleting a note with missing note ID."""
        # Create a mock API Gateway event without note ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "pathParameters": {}
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 400)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        
        # Verify the DynamoDB item was not deleted
        response = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        )
        self.assertIn("Item", response)

    def test_delete_note_not_found(self):
        """Test deleting a non-existent note."""
        # Create a mock API Gateway event with non-existent note ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "pathParameters": {
                "noteId": "non-existent-note"
            }
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 404)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_delete_note_wrong_user(self):
        """Test deleting a note that belongs to another user."""
        # Create a mock API Gateway event with a different user ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "different-user-id"
                    }
                }
            },
            "pathParameters": {
                "noteId": self.note_id
            }
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 404)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "NOT_FOUND")
        
        # Verify the DynamoDB item was not deleted
        response = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        )
        self.assertIn("Item", response)


if __name__ == "__main__":
    unittest.main() 