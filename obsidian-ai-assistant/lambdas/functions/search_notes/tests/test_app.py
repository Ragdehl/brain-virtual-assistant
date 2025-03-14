"""
Tests for the search_notes Lambda function.
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import boto3
import pytest
from moto import mock_dynamodb, mock_lambda

# Import the Lambda handler
from lambdas.functions.search_notes.app import lambda_handler


class TestSearchNotes(unittest.TestCase):
    """Test cases for the search_notes Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_patcher = patch.dict(os.environ, {
            "DYNAMODB_TABLE": "obsidian-ai-assistant-notes-test",
            "EMBEDDING_FUNCTION": "obsidian-ai-assistant-generate-embeddings-test",
            "STAGE": "test"
        })
        self.env_patcher.start()
        
        # Set up mock AWS services
        self.dynamodb_mock = mock_dynamodb()
        self.dynamodb_mock.start()
        
        self.lambda_mock = mock_lambda()
        self.lambda_mock.start()
        
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
        
        # Create the mock Lambda function for embeddings
        self.lambda_client = boto3.client("lambda", region_name="us-east-1")
        self.lambda_client.create_function(
            FunctionName="obsidian-ai-assistant-generate-embeddings-test",
            Runtime="python3.9",
            Role="arn:aws:iam::123456789012:role/lambda-role",
            Handler="app.lambda_handler",
            Code={"ZipFile": b"def lambda_handler(event, context): return {'embeddings': [0.1, 0.2, 0.3]}"},
            Description="Mock embedding function",
        )
        
        # Add test notes to DynamoDB
        self.user_id = "test-user-123"
        self.notes = [
            {
                "userId": self.user_id,
                "noteId": "note-1",
                "title": "Python Programming",
                "createdAt": "2023-05-01T12:00:00Z",
                "updatedAt": "2023-05-01T12:00:00Z",
                "tags": ["programming", "python"],
                "contentType": "text/markdown",
                "contentLength": 100,
                "contentHash": "hash-1",
                "embeddings": [0.1, 0.2, 0.3]
            },
            {
                "userId": self.user_id,
                "noteId": "note-2",
                "title": "JavaScript Basics",
                "createdAt": "2023-05-02T12:00:00Z",
                "updatedAt": "2023-05-02T12:00:00Z",
                "tags": ["programming", "javascript"],
                "contentType": "text/markdown",
                "contentLength": 150,
                "contentHash": "hash-2",
                "embeddings": [0.2, 0.3, 0.4]
            },
            {
                "userId": self.user_id,
                "noteId": "note-3",
                "title": "AWS Lambda Functions",
                "createdAt": "2023-05-03T12:00:00Z",
                "updatedAt": "2023-05-03T12:00:00Z",
                "tags": ["aws", "serverless"],
                "contentType": "text/markdown",
                "contentLength": 200,
                "contentHash": "hash-3",
                "embeddings": [0.3, 0.4, 0.5]
            },
            {
                "userId": self.user_id,
                "noteId": "note-4",
                "title": "Machine Learning with Python",
                "createdAt": "2023-05-04T12:00:00Z",
                "updatedAt": "2023-05-04T12:00:00Z",
                "tags": ["machine-learning", "python", "ai"],
                "contentType": "text/markdown",
                "contentLength": 250,
                "contentHash": "hash-4",
                "embeddings": [0.4, 0.5, 0.6]
            },
            {
                "userId": self.user_id,
                "noteId": "note-5",
                "title": "React Frontend Development",
                "createdAt": "2023-05-05T12:00:00Z",
                "updatedAt": "2023-05-05T12:00:00Z",
                "tags": ["frontend", "javascript", "react"],
                "contentType": "text/markdown",
                "contentLength": 300,
                "contentHash": "hash-5",
                "embeddings": [0.5, 0.6, 0.7]
            }
        ]
        
        for note in self.notes:
            self.table.put_item(Item=note)
        
        # Add a note for a different user
        self.table.put_item(Item={
            "userId": "different-user",
            "noteId": "note-6",
            "title": "Private Note",
            "createdAt": "2023-05-06T12:00:00Z",
            "updatedAt": "2023-05-06T12:00:00Z",
            "tags": ["private"],
            "contentType": "text/markdown",
            "contentLength": 100,
            "contentHash": "hash-6",
            "embeddings": [0.6, 0.7, 0.8]
        })

    def tearDown(self):
        """Tear down test fixtures."""
        self.dynamodb_mock.stop()
        self.lambda_mock.stop()
        self.env_patcher.stop()

    @patch('lambdas.functions.search_notes.app.lambda_client.invoke')
    def test_search_notes_text_search(self, mock_invoke):
        """Test text-based search for notes."""
        # Mock the Lambda invoke response
        mock_invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=MagicMock(return_value=json.dumps({
                'embeddings': [0.4, 0.5, 0.6]
            }).encode()))
        }
        
        # Create a mock API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "query": "python",
                "searchType": "text"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 200)
        
        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 2)  # Should find the two Python notes
        
        # Verify the correct notes were found
        note_ids = [note["noteId"] for note in body["notes"]]
        self.assertIn("note-1", note_ids)
        self.assertIn("note-4", note_ids)

    @patch('lambdas.functions.search_notes.app.lambda_client.invoke')
    def test_search_notes_semantic_search(self, mock_invoke):
        """Test semantic search for notes."""
        # Mock the Lambda invoke response
        mock_invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=MagicMock(return_value=json.dumps({
                'embeddings': [0.4, 0.5, 0.6]
            }).encode()))
        }
        
        # Create a mock API Gateway event
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "query": "machine learning and artificial intelligence",
                "searchType": "semantic"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 200)
        
        body = json.loads(response["body"])
        self.assertIn("notes", body)
        
        # Since we're mocking the embeddings, we can't test the actual semantic search results
        # But we can verify that the function returns notes and doesn't error
        self.assertGreaterEqual(len(body["notes"]), 1)

    def test_search_notes_missing_user_id(self):
        """Test searching notes with missing user ID."""
        # Create a mock API Gateway event without user ID
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {}
                }
            },
            "body": json.dumps({
                "query": "python",
                "searchType": "text"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 400)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_search_notes_missing_query(self):
        """Test searching notes with missing query."""
        # Create a mock API Gateway event without query
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "searchType": "text"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 400)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_search_notes_invalid_search_type(self):
        """Test searching notes with invalid search type."""
        # Create a mock API Gateway event with invalid search type
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "query": "python",
                "searchType": "invalid"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 400)
        
        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    @patch('lambdas.functions.search_notes.app.lambda_client.invoke')
    def test_search_notes_with_tag_filter(self, mock_invoke):
        """Test searching notes with tag filter."""
        # Mock the Lambda invoke response
        mock_invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=MagicMock(return_value=json.dumps({
                'embeddings': [0.4, 0.5, 0.6]
            }).encode()))
        }
        
        # Create a mock API Gateway event with tag filter
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "query": "javascript",
                "searchType": "text",
                "tags": ["react"]
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 200)
        
        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 1)  # Should find only the React note
        self.assertEqual(body["notes"][0]["noteId"], "note-5")

    @patch('lambdas.functions.search_notes.app.lambda_client.invoke')
    def test_search_notes_with_date_filter(self, mock_invoke):
        """Test searching notes with date filter."""
        # Mock the Lambda invoke response
        mock_invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock(read=MagicMock(return_value=json.dumps({
                'embeddings': [0.4, 0.5, 0.6]
            }).encode()))
        }
        
        # Create a mock API Gateway event with date filter
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": self.user_id
                    }
                }
            },
            "body": json.dumps({
                "query": "programming",
                "searchType": "text",
                "fromDate": "2023-05-01T00:00:00Z",
                "toDate": "2023-05-02T23:59:59Z"
            })
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, {})
        
        # Verify the response
        self.assertEqual(response["statusCode"], 200)
        
        body = json.loads(response["body"])
        self.assertIn("notes", body)
        self.assertEqual(len(body["notes"]), 2)  # Should find notes from May 1-2
        
        note_ids = [note["noteId"] for note in body["notes"]]
        self.assertIn("note-1", note_ids)
        self.assertIn("note-2", note_ids)


if __name__ == "__main__":
    unittest.main() 