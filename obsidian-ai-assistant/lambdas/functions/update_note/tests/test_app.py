"""
Tests for the update_note Lambda function.
"""

import json
import os
import unittest
from unittest.mock import patch

import boto3
from moto import mock_dynamodb, mock_lambda, mock_s3

# Import the Lambda handler
from lambdas.functions.update_note.app import lambda_handler


class TestUpdateNote(unittest.TestCase):
    """Test cases for the update_note Lambda function."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_patcher = patch.dict(
            os.environ,
            {
                "DYNAMODB_TABLE": "obsidian-ai-assistant-notes-test",
                "S3_BUCKET": "obsidian-ai-assistant-content-test",
                "EMBEDDING_FUNCTION": "obsidian-ai-assistant-generate-embeddings-test",
                "STAGE": "test",
            },
        )
        self.env_patcher.start()

        # Set up mock AWS services
        self.dynamodb_mock = mock_dynamodb()
        self.dynamodb_mock.start()

        self.s3_mock = mock_s3()
        self.s3_mock.start()

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

        # Create the mock S3 bucket
        self.s3 = boto3.resource("s3", region_name="us-east-1")
        self.s3.create_bucket(Bucket="obsidian-ai-assistant-content-test")

        # Create the mock Lambda function
        self.lambda_client = boto3.client("lambda", region_name="us-east-1")
        self.lambda_client.create_function(
            FunctionName="obsidian-ai-assistant-generate-embeddings-test",
            Runtime="python3.11",
            Role="arn:aws:iam::123456789012:role/lambda-role",
            Handler="app.lambda_handler",
            Code={
                "ZipFile": b"def lambda_handler(event, context): return {'embeddings': [0.1, 0.2, 0.3]}"
            },
            Description="Mock embedding function",
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
            "tags": ["test", "initial"],
            "contentType": "text/markdown",
            "contentLength": 100,
            "contentHash": "initial-hash",
            "embeddings": [0.1, 0.2, 0.3],
        }

        self.table.put_item(Item=self.note)

        # Add test content to S3
        self.s3_client = boto3.client("s3", region_name="us-east-1")
        self.s3_client.put_object(
            Bucket="obsidian-ai-assistant-content-test",
            Key=f"{self.user_id}/{self.note_id}",
            Body="# Test Note\n\nThis is the initial content of the test note.",
        )

    def tearDown(self):
        """Tear down test fixtures."""
        self.dynamodb_mock.stop()
        self.s3_mock.stop()
        self.lambda_mock.stop()
        self.env_patcher.stop()

    def test_update_note_success(self):
        """Test successful update of a note."""
        # Create a mock API Gateway event
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {"noteId": self.note_id},
            "body": json.dumps(
                {
                    "title": "Updated Test Note",
                    "tags": ["test", "updated"],
                    "content": "# Updated Test Note\n\nThis is the updated content of the test note.",
                }
            ),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("note", body)
        self.assertEqual(body["note"]["title"], "Updated Test Note")
        self.assertEqual(body["note"]["tags"], ["test", "updated"])

        # Verify the DynamoDB item was updated
        updated_item = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        ).get("Item")

        self.assertEqual(updated_item["title"], "Updated Test Note")
        self.assertEqual(updated_item["tags"], ["test", "updated"])
        self.assertNotEqual(updated_item["updatedAt"], self.note["updatedAt"])

        # Verify the S3 object was updated
        s3_object = self.s3_client.get_object(
            Bucket="obsidian-ai-assistant-content-test", Key=f"{self.user_id}/{self.note_id}"
        )

        content = s3_object["Body"].read().decode("utf-8")
        self.assertEqual(
            content, "# Updated Test Note\n\nThis is the updated content of the test note."
        )

    def test_update_note_missing_user_id(self):
        """Test updating a note with missing user ID."""
        # Create a mock API Gateway event without user ID
        event = {
            "requestContext": {"authorizer": {"claims": {}}},
            "pathParameters": {"noteId": self.note_id},
            "body": json.dumps({"title": "Updated Test Note"}),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 400)

        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_update_note_missing_note_id(self):
        """Test updating a note with missing note ID."""
        # Create a mock API Gateway event without note ID
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {},
            "body": json.dumps({"title": "Updated Test Note"}),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 400)

        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_update_note_not_found(self):
        """Test updating a non-existent note."""
        # Create a mock API Gateway event with non-existent note ID
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {"noteId": "non-existent-note"},
            "body": json.dumps({"title": "Updated Test Note"}),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 404)

        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_update_note_invalid_request(self):
        """Test updating a note with invalid request body."""
        # Create a mock API Gateway event with invalid JSON body
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {"noteId": self.note_id},
            "body": "invalid-json",
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 400)

        body = json.loads(response["body"])
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")

    def test_update_note_title_only(self):
        """Test updating only the title of a note."""
        # Create a mock API Gateway event with only title update
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {"noteId": self.note_id},
            "body": json.dumps({"title": "Title Only Update"}),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        body = json.loads(response["body"])
        self.assertIn("note", body)
        self.assertEqual(body["note"]["title"], "Title Only Update")

        # Verify the DynamoDB item was updated
        updated_item = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        ).get("Item")

        self.assertEqual(updated_item["title"], "Title Only Update")
        self.assertEqual(updated_item["tags"], self.note["tags"])  # Tags should remain unchanged

        # Verify the S3 object was not updated
        s3_object = self.s3_client.get_object(
            Bucket="obsidian-ai-assistant-content-test", Key=f"{self.user_id}/{self.note_id}"
        )

        content = s3_object["Body"].read().decode("utf-8")
        self.assertEqual(content, "# Test Note\n\nThis is the initial content of the test note.")

    def test_update_note_content_only(self):
        """Test updating only the content of a note."""
        # Create a mock API Gateway event with only content update
        event = {
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "pathParameters": {"noteId": self.note_id},
            "body": json.dumps(
                {"content": "# Content Only Update\n\nThis is a content-only update."}
            ),
        }

        # Call the Lambda handler
        response = lambda_handler(event, {})

        # Verify the response
        self.assertEqual(response["statusCode"], 200)

        # Verify the S3 object was updated
        s3_object = self.s3_client.get_object(
            Bucket="obsidian-ai-assistant-content-test", Key=f"{self.user_id}/{self.note_id}"
        )

        content = s3_object["Body"].read().decode("utf-8")
        self.assertEqual(content, "# Content Only Update\n\nThis is a content-only update.")

        # Verify the DynamoDB item was updated (contentHash and contentLength)
        updated_item = self.table.get_item(
            Key={"userId": self.user_id, "noteId": self.note_id}
        ).get("Item")

        self.assertNotEqual(updated_item["contentHash"], self.note["contentHash"])
        self.assertNotEqual(updated_item["contentLength"], self.note["contentLength"])


if __name__ == "__main__":
    unittest.main()
