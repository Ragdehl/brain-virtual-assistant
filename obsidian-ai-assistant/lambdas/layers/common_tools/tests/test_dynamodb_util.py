"""
Pytest tests for DynamoDBUtil in the common tools layer.
"""
import sys
import os
import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))

from lib.dynamodb_util import DynamoDBUtil
from lib.exceptions import NotFoundError, ServerError


@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client."""
    return MagicMock()


@pytest.fixture
def mock_dynamodb_resource():
    """Create a mock DynamoDB resource."""
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    return mock_resource


@pytest.fixture
def dynamodb_util(mock_dynamodb_resource):
    """Create a DynamoDBUtil instance with a mock DynamoDB resource."""
    with patch("boto3.resource") as mock_boto3_resource:
        mock_boto3_resource.return_value = mock_dynamodb_resource
        util = DynamoDBUtil("test-table")
        # Set the mock table directly to avoid the boto3 call in __init__
        util.table = mock_dynamodb_resource.Table.return_value
        return util


@pytest.fixture
def sample_item():
    """Create a sample DynamoDB item."""
    return {
        "userId": "test-user",
        "noteId": "test-note-id",
        "title": "Test Note",
        "content": "This is a test note.",
        "createdAt": "2023-01-01T00:00:00Z",
        "updatedAt": "2023-01-01T00:00:00Z"
    }


class TestDynamoDBUtil:
    """Tests for the DynamoDBUtil class."""

    def test_get_item_success(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test get_item with a successful response."""
        # Mock the DynamoDB table get_item method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.get_item.return_value = {"Item": sample_item}

        # Call the get_item method
        result = dynamodb_util.get_item(key={"userId": "test-user", "noteId": "test-note-id"})

        # Assert the result matches the sample item
        assert result == sample_item

        # Verify the table.get_item method was called with the correct parameters
        mock_table.get_item.assert_called_once_with(Key={"userId": "test-user", "noteId": "test-note-id"})

    def test_get_item_not_found(self, dynamodb_util, mock_dynamodb_resource):
        """Test get_item when the item is not found."""
        # Mock the DynamoDB table get_item method to return no Item
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.get_item.return_value = {}

        # Call the get_item method and expect a NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            dynamodb_util.get_item(key={"userId": "test-user", "noteId": "not-found"})

        # Assert the error message contains "not found"
        assert "not found" in str(excinfo.value)

    def test_get_item_client_error(self, dynamodb_util, mock_dynamodb_resource):
        """Test get_item with a client error."""
        # Mock the DynamoDB table get_item method to raise a ClientError
        mock_table = mock_dynamodb_resource.Table.return_value
        
        # Create a ClientError-like exception
        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
        
        error_response = {
            "Error": {
                "Code": "InternalServerError",
                "Message": "Internal server error"
            }
        }
        mock_table.get_item.side_effect = ClientError(error_response, "GetItem")

        # Call the get_item method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.get_item(key={"userId": "test-user", "noteId": "test-note-id"})

        # Assert the error message contains the original error message
        assert "Internal server error" in str(excinfo.value)

    def test_put_item_success(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test put_item with a successful response."""
        # Mock the DynamoDB table put_item method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Call the put_item method
        result = dynamodb_util.put_item(item=sample_item)

        # Assert the result is True (success)
        assert result is True

        # Verify the table.put_item method was called with the correct parameters
        mock_table.put_item.assert_called_once_with(Item=sample_item)

    def test_put_item_error(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test put_item with an error."""
        # Mock the DynamoDB table put_item method to raise an exception
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.put_item.side_effect = Exception("DynamoDB put_item error")

        # Call the put_item method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.put_item(item=sample_item)

        # Assert the error message contains the original error message
        assert "DynamoDB put_item error" in str(excinfo.value)

    def test_update_item_success(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test update_item with a successful response."""
        # Mock the DynamoDB table update_item method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.update_item.return_value = {"Attributes": sample_item}

        # Prepare the key and updates
        key = {"userId": "test-user", "noteId": "test-note-id"}
        updates = {"title": "Updated Title", "content": "Updated content"}

        # Call the update_item method
        result = dynamodb_util.update_item(key=key, updates=updates)

        # Assert the result matches the sample item
        assert result == sample_item

        # Verify the table.update_item method was called
        mock_table.update_item.assert_called_once()
        # Check that the key is in the call arguments
        call_args = mock_table.update_item.call_args[1]
        assert call_args["Key"] == key
        # The UpdateExpression should include all update fields
        assert "title" in call_args["UpdateExpression"]
        assert "content" in call_args["UpdateExpression"]

    def test_update_item_error(self, dynamodb_util, mock_dynamodb_resource):
        """Test update_item with an error."""
        # Mock the DynamoDB table update_item method to raise an exception
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.update_item.side_effect = Exception("DynamoDB update_item error")

        # Prepare the key and updates
        key = {"userId": "test-user", "noteId": "test-note-id"}
        updates = {"title": "Updated Title"}

        # Call the update_item method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.update_item(key=key, updates=updates)

        # Assert the error message contains the original error message
        assert "DynamoDB update_item error" in str(excinfo.value)

    def test_delete_item_success(self, dynamodb_util, mock_dynamodb_resource):
        """Test delete_item with a successful response."""
        # Mock the DynamoDB table delete_item method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.delete_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Prepare the key
        key = {"userId": "test-user", "noteId": "test-note-id"}

        # Call the delete_item method
        result = dynamodb_util.delete_item(key=key)

        # Assert the result is True (success)
        assert result is True

        # Verify the table.delete_item method was called with the correct parameters
        mock_table.delete_item.assert_called_once_with(Key=key)

    def test_delete_item_error(self, dynamodb_util, mock_dynamodb_resource):
        """Test delete_item with an error."""
        # Mock the DynamoDB table delete_item method to raise an exception
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.delete_item.side_effect = Exception("DynamoDB delete_item error")

        # Prepare the key
        key = {"userId": "test-user", "noteId": "test-note-id"}

        # Call the delete_item method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.delete_item(key=key)

        # Assert the error message contains the original error message
        assert "DynamoDB delete_item error" in str(excinfo.value)

    def test_query_success(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test query with a successful response."""
        # Mock the DynamoDB table query method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.query.return_value = {
            "Items": [sample_item],
            "Count": 1,
            "ScannedCount": 1
        }

        # Prepare the query parameters
        query_params = {
            "KeyConditionExpression": "userId = :userId",
            "ExpressionAttributeValues": {
                ":userId": "test-user"
            }
        }

        # Call the query method
        result = dynamodb_util.query(query_params=query_params)

        # Assert the result contains the expected items
        assert len(result) == 1
        assert result[0] == sample_item

        # Verify the table.query method was called with the correct parameters
        mock_table.query.assert_called_once_with(**query_params)

    def test_query_error(self, dynamodb_util, mock_dynamodb_resource):
        """Test query with an error."""
        # Mock the DynamoDB table query method to raise an exception
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.query.side_effect = Exception("DynamoDB query error")

        # Prepare the query parameters
        query_params = {
            "KeyConditionExpression": "userId = :userId",
            "ExpressionAttributeValues": {
                ":userId": "test-user"
            }
        }

        # Call the query method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.query(query_params=query_params)

        # Assert the error message contains the original error message
        assert "DynamoDB query error" in str(excinfo.value)

    def test_scan_success(self, dynamodb_util, mock_dynamodb_resource, sample_item):
        """Test scan with a successful response."""
        # Mock the DynamoDB table scan method
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.scan.return_value = {
            "Items": [sample_item],
            "Count": 1,
            "ScannedCount": 1
        }

        # Prepare the scan parameters
        scan_params = {
            "FilterExpression": "userId = :userId",
            "ExpressionAttributeValues": {
                ":userId": "test-user"
            }
        }

        # Call the scan method
        result = dynamodb_util.scan(scan_params=scan_params)

        # Assert the result contains the expected items
        assert len(result) == 1
        assert result[0] == sample_item

        # Verify the table.scan method was called with the correct parameters
        mock_table.scan.assert_called_once_with(**scan_params)

    def test_scan_error(self, dynamodb_util, mock_dynamodb_resource):
        """Test scan with an error."""
        # Mock the DynamoDB table scan method to raise an exception
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.scan.side_effect = Exception("DynamoDB scan error")

        # Prepare the scan parameters
        scan_params = {
            "FilterExpression": "userId = :userId",
            "ExpressionAttributeValues": {
                ":userId": "test-user"
            }
        }

        # Call the scan method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            dynamodb_util.scan(scan_params=scan_params)

        # Assert the error message contains the original error message
        assert "DynamoDB scan error" in str(excinfo.value) 