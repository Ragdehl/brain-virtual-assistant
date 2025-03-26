"""
Pytest tests for S3Util in the common tools layer.
"""
import sys
import os
import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch
from io import BytesIO

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))

from lib.s3_util import S3Util
from lib.exceptions import NotFoundError, ServerError


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    return MagicMock()


@pytest.fixture
def s3_util(mock_s3_client):
    """Create an S3Util instance with a mock S3 client."""
    with patch("boto3.client") as mock_boto3_client:
        mock_boto3_client.return_value = mock_s3_client
        util = S3Util("test-bucket")
        # Set the mock client directly to avoid the boto3 call in __init__
        util.s3_client = mock_s3_client
        return util


class TestS3Util:
    """Tests for the S3Util class."""

    def test_put_object_success(self, s3_util, mock_s3_client):
        """Test put_object with a successful response."""
        # Mock the S3 client put_object method
        mock_s3_client.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Prepare the parameters
        key = "test-key"
        body = "Test content"
        content_type = "text/plain"

        # Call the put_object method
        result = s3_util.put_object(key=key, body=body, content_type=content_type)

        # Assert the result is True (success)
        assert result is True

        # Verify the s3_client.put_object method was called with the correct parameters
        mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key,
            Body=body,
            ContentType=content_type
        )

    def test_put_object_error(self, s3_util, mock_s3_client):
        """Test put_object with an error."""
        # Mock the S3 client put_object method to raise an exception
        mock_s3_client.put_object.side_effect = Exception("S3 put_object error")

        # Prepare the parameters
        key = "test-key"
        body = "Test content"
        content_type = "text/plain"

        # Call the put_object method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            s3_util.put_object(key=key, body=body, content_type=content_type)

        # Assert the error message contains the original error message
        assert "S3 put_object error" in str(excinfo.value)

    def test_get_object_success(self, s3_util, mock_s3_client):
        """Test get_object with a successful response."""
        # Mock the S3 client get_object method
        mock_body = MagicMock()
        mock_body.read.return_value = b"Test content"
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentType": "text/plain",
            "ContentLength": 12
        }

        # Prepare the parameters
        key = "test-key"

        # Call the get_object method
        result = s3_util.get_object(key=key)

        # Assert the result contains the expected body and content type
        assert result["Body"] == mock_body
        assert result["ContentType"] == "text/plain"
        assert result["ContentLength"] == 12

        # Verify the s3_client.get_object method was called with the correct parameters
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key
        )

    def test_get_object_not_found(self, s3_util, mock_s3_client):
        """Test get_object when the object is not found."""
        # Create a ClientError-like exception for S3
        class NoSuchKeyError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
        
        # Mock the S3 client get_object method to raise a NoSuchKey error
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist."
            }
        }
        mock_s3_client.get_object.side_effect = NoSuchKeyError(error_response, "GetObject")

        # Prepare the parameters
        key = "non-existent-key"

        # Call the get_object method and expect a NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            s3_util.get_object(key=key)

        # Assert the error message contains "not found"
        assert "not found" in str(excinfo.value)

    def test_get_object_error(self, s3_util, mock_s3_client):
        """Test get_object with a client error."""
        # Mock the S3 client get_object method to raise a generic exception
        mock_s3_client.get_object.side_effect = Exception("S3 get_object error")

        # Prepare the parameters
        key = "test-key"

        # Call the get_object method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            s3_util.get_object(key=key)

        # Assert the error message contains the original error message
        assert "S3 get_object error" in str(excinfo.value)

    def test_get_object_content_success(self, s3_util, mock_s3_client):
        """Test get_object_content with a successful response."""
        # Mock the S3 client get_object method
        mock_body = MagicMock()
        mock_body.read.return_value = b"Test content"
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentType": "text/plain"
        }

        # Prepare the parameters
        key = "test-key"

        # Call the get_object_content method
        result = s3_util.get_object_content(key=key)

        # Assert the result is the expected content string
        assert result == "Test content"

        # Verify the s3_client.get_object method was called with the correct parameters
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key
        )

    def test_get_object_content_not_found(self, s3_util, mock_s3_client):
        """Test get_object_content when the object is not found."""
        # Create a ClientError-like exception for S3
        class NoSuchKeyError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
        
        # Mock the S3 client get_object method to raise a NoSuchKey error
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist."
            }
        }
        mock_s3_client.get_object.side_effect = NoSuchKeyError(error_response, "GetObject")

        # Prepare the parameters
        key = "non-existent-key"

        # Call the get_object_content method and expect a NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            s3_util.get_object_content(key=key)

        # Assert the error message contains "not found"
        assert "not found" in str(excinfo.value)

    def test_delete_object_success(self, s3_util, mock_s3_client):
        """Test delete_object with a successful response."""
        # Mock the S3 client delete_object method
        mock_s3_client.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 204}}

        # Prepare the parameters
        key = "test-key"

        # Call the delete_object method
        result = s3_util.delete_object(key=key)

        # Assert the result is True (success)
        assert result is True

        # Verify the s3_client.delete_object method was called with the correct parameters
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key
        )

    def test_delete_object_not_found(self, s3_util, mock_s3_client):
        """Test delete_object when the object is not found."""
        # Create a ClientError-like exception for S3
        class NoSuchKeyError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
        
        # Mock the S3 client delete_object method to raise a NoSuchKey error
        error_response = {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist."
            }
        }
        mock_s3_client.delete_object.side_effect = NoSuchKeyError(error_response, "DeleteObject")

        # Prepare the parameters
        key = "non-existent-key"

        # Call the delete_object method and expect a NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            s3_util.delete_object(key=key)

        # Assert the error message contains "not found"
        assert "not found" in str(excinfo.value)

    def test_delete_object_error(self, s3_util, mock_s3_client):
        """Test delete_object with a client error."""
        # Mock the S3 client delete_object method to raise a generic exception
        mock_s3_client.delete_object.side_effect = Exception("S3 delete_object error")

        # Prepare the parameters
        key = "test-key"

        # Call the delete_object method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            s3_util.delete_object(key=key)

        # Assert the error message contains the original error message
        assert "S3 delete_object error" in str(excinfo.value)

    def test_list_objects_success(self, s3_util, mock_s3_client):
        """Test list_objects with a successful response."""
        # Mock the S3 client list_objects_v2 method
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "test-key-1", "LastModified": "2023-01-01T00:00:00Z", "Size": 100},
                {"Key": "test-key-2", "LastModified": "2023-01-02T00:00:00Z", "Size": 200}
            ],
            "KeyCount": 2,
            "IsTruncated": False
        }

        # Prepare the parameters
        prefix = "test-prefix"

        # Call the list_objects method
        result = s3_util.list_objects(prefix=prefix)

        # Assert the result contains the expected objects
        assert len(result) == 2
        assert result[0]["Key"] == "test-key-1"
        assert result[1]["Key"] == "test-key-2"

        # Verify the s3_client.list_objects_v2 method was called with the correct parameters
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix=prefix
        )

    def test_list_objects_no_contents(self, s3_util, mock_s3_client):
        """Test list_objects when there are no objects."""
        # Mock the S3 client list_objects_v2 method to return no Contents
        mock_s3_client.list_objects_v2.return_value = {
            "KeyCount": 0,
            "IsTruncated": False
        }

        # Prepare the parameters
        prefix = "test-prefix"

        # Call the list_objects method
        result = s3_util.list_objects(prefix=prefix)

        # Assert the result is an empty list
        assert result == []

    def test_list_objects_error(self, s3_util, mock_s3_client):
        """Test list_objects with a client error."""
        # Mock the S3 client list_objects_v2 method to raise a generic exception
        mock_s3_client.list_objects_v2.side_effect = Exception("S3 list_objects error")

        # Prepare the parameters
        prefix = "test-prefix"

        # Call the list_objects method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            s3_util.list_objects(prefix=prefix)

        # Assert the error message contains the original error message
        assert "S3 list_objects error" in str(excinfo.value) 