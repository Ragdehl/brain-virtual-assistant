"""
Pytest configuration file for the Obsidian AI Assistant project.
"""
import os
import sys

import boto3
import pytest
from moto import mock_dynamodb, mock_lambda, mock_s3

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    """DynamoDB mock fixture."""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """S3 mock fixture."""
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture(scope="function")
def lambda_client(aws_credentials):
    """Lambda mock fixture."""
    with mock_lambda():
        yield boto3.client("lambda", region_name="us-east-1")


@pytest.fixture(scope="function")
def notes_table(dynamodb):
    """Create a mock notes table."""
    table_name = "obsidian-ai-assistant-notes-test"
    os.environ["DYNAMODB_TABLE"] = table_name

    table = dynamodb.create_table(
        TableName=table_name,
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

    return table


@pytest.fixture(scope="function")
def content_bucket(s3):
    """Create a mock content bucket."""
    bucket_name = "obsidian-ai-assistant-content-test"
    os.environ["S3_BUCKET"] = bucket_name

    s3.create_bucket(Bucket=bucket_name)

    return bucket_name


@pytest.fixture(scope="function")
def embedding_function(lambda_client):
    """Create a mock embedding function."""
    function_name = "obsidian-ai-assistant-generate-embeddings-test"
    os.environ["EMBEDDING_FUNCTION"] = function_name

    lambda_client.create_function(
        FunctionName=function_name,
        Runtime="python3.11",
        Role="arn:aws:iam::123456789012:role/lambda-role",
        Handler="app.lambda_handler",
        Code={"ZipFile": b"def lambda_handler(event, context): return {'embeddings': [0.1, 0.2, 0.3]}"},
        Description="Mock embedding function",
    )

    return function_name


@pytest.fixture(scope="function")
def test_environment(notes_table, content_bucket, embedding_function):
    """Set up the test environment with all AWS resources."""
    os.environ["STAGE"] = "test"

    yield

    # Clean up environment variables
    for env_var in ["DYNAMODB_TABLE", "S3_BUCKET", "EMBEDDING_FUNCTION", "STAGE"]:
        if env_var in os.environ:
            del os.environ[env_var]
