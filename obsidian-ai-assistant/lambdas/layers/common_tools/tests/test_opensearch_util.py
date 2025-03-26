"""
Pytest tests for OpenSearchUtil in the common tools layer.
"""
import sys
import os
import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))

from lib.opensearch_util import OpenSearchUtil
from lib.exceptions import ServerError


@pytest.fixture
def mock_opensearch_client():
    """Create a mock OpenSearch client."""
    return MagicMock()


@pytest.fixture
def opensearch_util(mock_opensearch_client):
    """Create an OpenSearchUtil instance with a mock client."""
    with patch("opensearchpy.OpenSearch") as mock_opensearch:
        mock_opensearch.return_value = mock_opensearch_client
        util = OpenSearchUtil(
            hosts=[{"host": "localhost", "port": 9200}],
            http_auth=("username", "password"),
            use_ssl=True,
            verify_certs=False,
            index_name="test-index"
        )
        # Replace the client with our mock
        util.client = mock_opensearch_client
        return util


class TestOpenSearchUtil:
    """Tests for the OpenSearchUtil class."""

    def test_create_index_success(self, opensearch_util, mock_opensearch_client):
        """Test create_index with a successful response."""
        # Mock the OpenSearch client indices.exists and indices.create methods
        mock_opensearch_client.indices.exists.return_value = False
        mock_opensearch_client.indices.create.return_value = {"acknowledged": True}

        # Define index mappings
        mappings = {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "embedding": {"type": "dense_vector", "dims": 1536}
            }
        }

        # Call the create_index method
        result = opensearch_util.create_index(mappings)

        # Assert the result is True (success)
        assert result is True

        # Verify the client.indices.exists method was called with the correct parameters
        mock_opensearch_client.indices.exists.assert_called_once_with(index="test-index")

        # Verify the client.indices.create method was called with the correct parameters
        mock_opensearch_client.indices.create.assert_called_once_with(
            index="test-index",
            body={"mappings": mappings}
        )

    def test_create_index_already_exists(self, opensearch_util, mock_opensearch_client):
        """Test create_index when the index already exists."""
        # Mock the OpenSearch client indices.exists method to return True
        mock_opensearch_client.indices.exists.return_value = True

        # Define index mappings
        mappings = {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"}
            }
        }

        # Call the create_index method
        result = opensearch_util.create_index(mappings)

        # Assert the result is True (success)
        assert result is True

        # Verify the client.indices.exists method was called with the correct parameters
        mock_opensearch_client.indices.exists.assert_called_once_with(index="test-index")

        # Verify the client.indices.create method was not called
        mock_opensearch_client.indices.create.assert_not_called()

    def test_create_index_error(self, opensearch_util, mock_opensearch_client):
        """Test create_index with an error."""
        # Mock the OpenSearch client indices.exists and indices.create methods
        mock_opensearch_client.indices.exists.return_value = False
        mock_opensearch_client.indices.create.side_effect = Exception("OpenSearch create_index error")

        # Define index mappings
        mappings = {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"}
            }
        }

        # Call the create_index method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.create_index(mappings)

        # Assert the error message contains the original error message
        assert "OpenSearch create_index error" in str(excinfo.value)

    def test_index_document_success(self, opensearch_util, mock_opensearch_client):
        """Test index_document with a successful response."""
        # Mock the OpenSearch client index method
        mock_opensearch_client.index.return_value = {"_id": "test-id", "result": "created"}

        # Prepare document and ID
        document = {"title": "Test Title", "content": "Test Content", "embedding": [0.1, 0.2, 0.3]}
        doc_id = "test-id"

        # Call the index_document method
        result = opensearch_util.index_document(document, doc_id)

        # Assert the result is True (success)
        assert result is True

        # Verify the client.index method was called with the correct parameters
        mock_opensearch_client.index.assert_called_once_with(
            index="test-index",
            body=document,
            id=doc_id,
            refresh=True
        )

    def test_index_document_error(self, opensearch_util, mock_opensearch_client):
        """Test index_document with an error."""
        # Mock the OpenSearch client index method to raise an exception
        mock_opensearch_client.index.side_effect = Exception("OpenSearch index_document error")

        # Prepare document and ID
        document = {"title": "Test Title", "content": "Test Content"}
        doc_id = "test-id"

        # Call the index_document method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.index_document(document, doc_id)

        # Assert the error message contains the original error message
        assert "OpenSearch index_document error" in str(excinfo.value)

    def test_get_document_success(self, opensearch_util, mock_opensearch_client):
        """Test get_document with a successful response."""
        # Mock the OpenSearch client get method
        mock_opensearch_client.get.return_value = {
            "_id": "test-id",
            "_source": {"title": "Test Title", "content": "Test Content"}
        }

        # Prepare document ID
        doc_id = "test-id"

        # Call the get_document method
        result = opensearch_util.get_document(doc_id)

        # Assert the result contains the expected document
        assert result == {"title": "Test Title", "content": "Test Content"}

        # Verify the client.get method was called with the correct parameters
        mock_opensearch_client.get.assert_called_once_with(
            index="test-index",
            id=doc_id
        )

    def test_get_document_not_found(self, opensearch_util, mock_opensearch_client):
        """Test get_document when the document is not found."""
        # Create a NotFoundError-like exception for OpenSearch
        class NotFoundError(Exception):
            pass

        # Mock the OpenSearch client get method to raise a NotFoundError
        mock_opensearch_client.get.side_effect = NotFoundError()

        # Prepare document ID
        doc_id = "non-existent-id"

        # Call the get_document method
        result = opensearch_util.get_document(doc_id)

        # Assert the result is None
        assert result is None

    def test_get_document_error(self, opensearch_util, mock_opensearch_client):
        """Test get_document with an error."""
        # Mock the OpenSearch client get method to raise a generic exception
        mock_opensearch_client.get.side_effect = Exception("OpenSearch get_document error")

        # Prepare document ID
        doc_id = "test-id"

        # Call the get_document method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.get_document(doc_id)

        # Assert the error message contains the original error message
        assert "OpenSearch get_document error" in str(excinfo.value)

    def test_delete_document_success(self, opensearch_util, mock_opensearch_client):
        """Test delete_document with a successful response."""
        # Mock the OpenSearch client delete method
        mock_opensearch_client.delete.return_value = {"_id": "test-id", "result": "deleted"}

        # Prepare document ID
        doc_id = "test-id"

        # Call the delete_document method
        result = opensearch_util.delete_document(doc_id)

        # Assert the result is True (success)
        assert result is True

        # Verify the client.delete method was called with the correct parameters
        mock_opensearch_client.delete.assert_called_once_with(
            index="test-index",
            id=doc_id,
            refresh=True
        )

    def test_delete_document_not_found(self, opensearch_util, mock_opensearch_client):
        """Test delete_document when the document is not found."""
        # Create a NotFoundError-like exception for OpenSearch
        class NotFoundError(Exception):
            pass

        # Mock the OpenSearch client delete method to raise a NotFoundError
        mock_opensearch_client.delete.side_effect = NotFoundError()

        # Prepare document ID
        doc_id = "non-existent-id"

        # Call the delete_document method
        result = opensearch_util.delete_document(doc_id)

        # Assert the result is False (failure due to not found)
        assert result is False

    def test_delete_document_error(self, opensearch_util, mock_opensearch_client):
        """Test delete_document with an error."""
        # Mock the OpenSearch client delete method to raise a generic exception
        mock_opensearch_client.delete.side_effect = Exception("OpenSearch delete_document error")

        # Prepare document ID
        doc_id = "test-id"

        # Call the delete_document method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.delete_document(doc_id)

        # Assert the error message contains the original error message
        assert "OpenSearch delete_document error" in str(excinfo.value)

    def test_update_document_success(self, opensearch_util, mock_opensearch_client):
        """Test update_document with a successful response."""
        # Mock the OpenSearch client update method
        mock_opensearch_client.update.return_value = {"_id": "test-id", "result": "updated"}

        # Prepare document ID and updated fields
        doc_id = "test-id"
        updated_fields = {"title": "Updated Title", "content": "Updated Content"}

        # Call the update_document method
        result = opensearch_util.update_document(doc_id, updated_fields)

        # Assert the result is True (success)
        assert result is True

        # Verify the client.update method was called with the correct parameters
        mock_opensearch_client.update.assert_called_once_with(
            index="test-index",
            id=doc_id,
            body={"doc": updated_fields},
            refresh=True
        )

    def test_update_document_not_found(self, opensearch_util, mock_opensearch_client):
        """Test update_document when the document is not found."""
        # Create a NotFoundError-like exception for OpenSearch
        class NotFoundError(Exception):
            pass

        # Mock the OpenSearch client update method to raise a NotFoundError
        mock_opensearch_client.update.side_effect = NotFoundError()

        # Prepare document ID and updated fields
        doc_id = "non-existent-id"
        updated_fields = {"title": "Updated Title"}

        # Call the update_document method
        result = opensearch_util.update_document(doc_id, updated_fields)

        # Assert the result is False (failure due to not found)
        assert result is False

    def test_update_document_error(self, opensearch_util, mock_opensearch_client):
        """Test update_document with an error."""
        # Mock the OpenSearch client update method to raise a generic exception
        mock_opensearch_client.update.side_effect = Exception("OpenSearch update_document error")

        # Prepare document ID and updated fields
        doc_id = "test-id"
        updated_fields = {"title": "Updated Title"}

        # Call the update_document method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.update_document(doc_id, updated_fields)

        # Assert the error message contains the original error message
        assert "OpenSearch update_document error" in str(excinfo.value)

    def test_search_documents_success(self, opensearch_util, mock_opensearch_client):
        """Test search_documents with a successful response."""
        # Mock the OpenSearch client search method
        mock_search_response = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_id": "doc1",
                        "_score": 0.9,
                        "_source": {"title": "Document 1", "content": "Content 1"}
                    },
                    {
                        "_id": "doc2",
                        "_score": 0.8,
                        "_source": {"title": "Document 2", "content": "Content 2"}
                    }
                ]
            }
        }
        mock_opensearch_client.search.return_value = mock_search_response

        # Prepare search query
        query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }

        # Call the search_documents method
        result = opensearch_util.search_documents(query)

        # Assert the result contains the expected hits
        assert len(result) == 2
        assert result[0]["_id"] == "doc1"
        assert result[0]["_source"]["title"] == "Document 1"
        assert result[1]["_id"] == "doc2"
        assert result[1]["_source"]["title"] == "Document 2"

        # Verify the client.search method was called with the correct parameters
        mock_opensearch_client.search.assert_called_once_with(
            index="test-index",
            body=query
        )

    def test_search_documents_no_results(self, opensearch_util, mock_opensearch_client):
        """Test search_documents when no documents match the query."""
        # Mock the OpenSearch client search method to return no hits
        mock_search_response = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }
        mock_opensearch_client.search.return_value = mock_search_response

        # Prepare search query
        query = {
            "query": {
                "match": {
                    "content": "nonexistent"
                }
            }
        }

        # Call the search_documents method
        result = opensearch_util.search_documents(query)

        # Assert the result is an empty list
        assert result == []

    def test_search_documents_error(self, opensearch_util, mock_opensearch_client):
        """Test search_documents with an error."""
        # Mock the OpenSearch client search method to raise a generic exception
        mock_opensearch_client.search.side_effect = Exception("OpenSearch search_documents error")

        # Prepare search query
        query = {
            "query": {
                "match": {
                    "content": "test"
                }
            }
        }

        # Call the search_documents method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.search_documents(query)

        # Assert the error message contains the original error message
        assert "OpenSearch search_documents error" in str(excinfo.value)

    def test_vector_search_success(self, opensearch_util, mock_opensearch_client):
        """Test vector_search with a successful response."""
        # Mock the OpenSearch client search method
        mock_search_response = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_id": "doc1",
                        "_score": 0.95,
                        "_source": {"title": "Document 1", "content": "Content 1"}
                    },
                    {
                        "_id": "doc2",
                        "_score": 0.85,
                        "_source": {"title": "Document 2", "content": "Content 2"}
                    }
                ]
            }
        }
        mock_opensearch_client.search.return_value = mock_search_response

        # Prepare vector query parameters
        embedding = [0.1, 0.2, 0.3]  # Sample embedding vector
        k = 2
        field_name = "embedding"

        # Call the vector_search method
        result = opensearch_util.vector_search(embedding, k, field_name)

        # Assert the result contains the expected hits
        assert len(result) == 2
        assert result[0]["_id"] == "doc1"
        assert result[0]["_source"]["title"] == "Document 1"
        assert result[1]["_id"] == "doc2"
        assert result[1]["_source"]["title"] == "Document 2"

        # Verify the client.search method was called with a query containing knn
        mock_opensearch_client.search.assert_called_once()
        search_call_args = mock_opensearch_client.search.call_args[1]
        assert search_call_args["index"] == "test-index"
        assert "knn" in search_call_args["body"]["query"]
        assert search_call_args["body"]["query"]["knn"][field_name]["vector"] == embedding
        assert search_call_args["body"]["query"]["knn"][field_name]["k"] == k

    def test_vector_search_no_results(self, opensearch_util, mock_opensearch_client):
        """Test vector_search when no documents match the query."""
        # Mock the OpenSearch client search method to return no hits
        mock_search_response = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }
        mock_opensearch_client.search.return_value = mock_search_response

        # Prepare vector query parameters
        embedding = [0.1, 0.2, 0.3]  # Sample embedding vector
        k = 5
        field_name = "embedding"

        # Call the vector_search method
        result = opensearch_util.vector_search(embedding, k, field_name)

        # Assert the result is an empty list
        assert result == []

    def test_vector_search_error(self, opensearch_util, mock_opensearch_client):
        """Test vector_search with an error."""
        # Mock the OpenSearch client search method to raise a generic exception
        mock_opensearch_client.search.side_effect = Exception("OpenSearch vector_search error")

        # Prepare vector query parameters
        embedding = [0.1, 0.2, 0.3]  # Sample embedding vector
        k = 5
        field_name = "embedding"

        # Call the vector_search method and expect a ServerError
        with pytest.raises(ServerError) as excinfo:
            opensearch_util.vector_search(embedding, k, field_name)

        # Assert the error message contains the original error message
        assert "OpenSearch vector_search error" in str(excinfo.value) 