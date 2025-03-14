"""
Tests for the list_notes Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch

import boto3
from moto import mock_dynamodb

# Import the Lambda handler
from lambdas.functions.list_notes.app import lambda_handler


class TestListNotes(unittest.TestCase):
    """Test cases for the list_notes Lambda function."""

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

        # Add some test data
        self.user_id = "test-user-123"
        self.notes = [
            {
                "userId": self.user_id,
                "noteId": f"note-{i}",
                "title": f"Test Note {i}",
                "createdAt": f"2023-05-{i+1:02d}T12:00:00Z",
                "updatedAt": f"2023-05-{i+1:02d}T12:00:00Z",
                "tags": ["test", f"tag-{i}"],
                "contentType": "text/markdown",
                "contentLength": 100 + i,
                "contentHash": f"hash-{i}",
                "embeddings": [0.1, 0.2, 0.3]
            }
            for i in range(10)
        ]

        for note in self.notes:
            self.table.put_item(Item=note)

    def tearDown(self):
        """Tear down test fixtures."""
        self.dynamodb_mock.stop()
        self.env_patcher.stop()

    def test_list_notes_success(self):
        """Test successful listing of notes."""
        # Create a mock API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "queryStringParameters": None
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 10)
        self.assertIn("pagination", body)
        self.assertIsNone(body["pagination"]["nextToken"])

    def test_list_notes_with_pagination(self):
        """Test listing notes with pagination."""
        # Create a mock API Gateway event with limit
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "queryStringParameters": {
                "limit": "3"
            }
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 3)
        self.assertIn("pagination", body)
        self.assertIsNotNone(body["pagination"]["nextToken"])

        # Use the nextToken to get the next page
        next_token = body["pagination"]["nextToken"]
        event["queryStringParameters"]["nextToken"] = next_token

        response = lambda_handler(event, {})
        body = json.loads(response["body"])

        self.assertEqual(len(body["notes"]), 3)
        self.assertIsNotNone(body["pagination"]["nextToken"])

        # Verify we get different notes in the second page
        first_page_ids = set(note["noteId"] for note in json.loads(response["body"])["notes"])
        second_page_ids = set(note["noteId"] for note in body["notes"])
        self.assertEqual(len(first_page_ids.intersection(second_page_ids)), 0)

    def test_list_notes_missing_user_id(self):
        """Test listing notes with missing user ID."""
        # Create a mock API Gateway event without user ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {}
                }
            },
            "queryStringParameters": None
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 400)

        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_list_notes_empty_result(self):
        """Test listing notes with no results."""
        # Create a mock API Gateway event with a different user ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "different-user-id"
                    }
                }
            },
            "queryStringParameters": None
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 0)
        self.assertIn("pagination", body)
        self.assertIsNone(body["pagination"]["nextToken"])

    def test_list_notes_with_tag_filter(self):
        """Test listing notes with tag filter."""
        # Create a mock API Gateway event with tag filter
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "queryStringParameters": {
                "tag": "tag-5"
            }
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 1)
        self.assertEqual(body["notes"][0]["noteId"], "note-5")

    def test_list_notes_with_date_filter(self):
        """Test listing notes with date filter."""
        # Create a mock API Gateway event with date filter
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "queryStringParameters": {
                "fromDate": "2023-05-05T00:00:00Z",
                "toDate": "2023-05-07T23:59:59Z"
            }
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 3)  # Notes 5, 6, 7

        note_ids = [note["noteId"] for note in body["notes"]]
        self.assertIn("note-5", note_ids)
        self.assertIn("note-6", note_ids)
        self.assertIn("note-7", note_ids)


if __name__ == "__main__":
    unittest.main()
