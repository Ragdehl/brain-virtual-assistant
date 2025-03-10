"""
Helper functions for interacting with OpenSearch.

This module provides a simplified interface for common OpenSearch operations
for semantic search capabilities in the Obsidian AI Assistant application.
"""

import os
import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
from typing import Dict, List, Any, Optional, Union

# Initialize AWS credentials
region: str = os.environ.get('AWS_REGION', 'us-east-1')
service: str = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

# OpenSearch configuration
domain: str = os.environ.get('OPENSEARCH_DOMAIN')
index_name: str = 'notes'
endpoint: str = f'https://{domain}.{region}.es.amazonaws.com'

def create_index(index_name: str = index_name) -> Dict[str, Any]:
    """
    Create an OpenSearch index with vector search capabilities.
    
    Args:
        index_name: The name of the index to create
        
    Returns:
        The response from OpenSearch as a dictionary
        
    Raises:
        requests.RequestException: If there's an error communicating with OpenSearch
    """
    url: str = f'{endpoint}/{index_name}'
    
    # Index mapping with vector field
    mapping: Dict[str, Any] = {
        'mappings': {
            'properties': {
                'id': {'type': 'keyword'},
                'title': {'type': 'text'},
                'content': {'type': 'text'},
                'embedding': {
                    'type': 'knn_vector',
                    'dimension': 1536  # Titan embedding dimension
                }
            }
        }
    }
    
    response = requests.put(url, auth=awsauth, json=mapping, headers={'Content-Type': 'application/json'})
    response.raise_for_status()  # Raise exception for HTTP errors
    return response.json()

def index_document(doc_id: str, document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Index a document in OpenSearch.
    
    Args:
        doc_id: The document ID (note ID)
        document: The document to index, including embedding vector
        
    Returns:
        The response from OpenSearch as a dictionary
        
    Raises:
        requests.RequestException: If there's an error communicating with OpenSearch
    """
    url: str = f'{endpoint}/{index_name}/_doc/{doc_id}'
    response = requests.put(url, auth=awsauth, json=document, headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    return response.json()

def search_by_vector(vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for similar documents using vector similarity.
    
    Args:
        vector: The embedding vector to search with
        k: The number of results to return
        
    Returns:
        The matching documents, sorted by similarity
        
    Raises:
        requests.RequestException: If there's an error communicating with OpenSearch
    """
    url: str = f'{endpoint}/{index_name}/_search'
    
    query: Dict[str, Any] = {
        'size': k,
        'query': {
            'knn': {
                'embedding': {
                    'vector': vector,
                    'k': k
                }
            }
        }
    }
    
    response = requests.get(url, auth=awsauth, json=query, headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    results = response.json()
    
    return [hit['_source'] for hit in results.get('hits', {}).get('hits', [])]

def delete_document(doc_id: str) -> Dict[str, Any]:
    """
    Delete a document from OpenSearch.
    
    Args:
        doc_id: The document ID (note ID)
        
    Returns:
        The response from OpenSearch as a dictionary
        
    Raises:
        requests.RequestException: If there's an error communicating with OpenSearch
    """
    url: str = f'{endpoint}/{index_name}/_doc/{doc_id}'
    response = requests.delete(url, auth=awsauth)
    response.raise_for_status()
    return response.json()

def search_by_text(query_text: str, fields: List[str] = ['title', 'content'], size: int = 10) -> List[Dict[str, Any]]:
    """
    Search for documents using text query.
    
    Args:
        query_text: The text to search for
        fields: The fields to search in
        size: The number of results to return
        
    Returns:
        The matching documents, sorted by relevance
        
    Raises:
        requests.RequestException: If there's an error communicating with OpenSearch
    """
    url: str = f'{endpoint}/{index_name}/_search'
    
    query: Dict[str, Any] = {
        'size': size,
        'query': {
            'multi_match': {
                'query': query_text,
                'fields': fields
            }
        }
    }
    
    response = requests.get(url, auth=awsauth, json=query, headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    results = response.json()
    
    return [hit['_source'] for hit in results.get('hits', {}).get('hits', [])] 