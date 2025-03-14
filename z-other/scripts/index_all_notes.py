#!/usr/bin/env python3
"""
Index all notes in OpenSearch.

This script retrieves all Markdown files from S3 and indexes them in OpenSearch,
including generating embeddings for vector search.
"""

import os
import sys
import boto3
import json
import argparse
import logging
import requests
from requests_aws4auth import AWS4Auth
from typing import Dict, List, Any, Optional

# Add the common layer to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

# Import helpers from common layer
try:
    import s3_helper
    import opensearch_helper
except ImportError:
    print("Error: Could not import helper modules. Make sure the common layer is available.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text using the embeddings Lambda function.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        The embedding vector as a list of floats
    """
    try:
        # Call the embeddings Lambda function
        response = lambda_client.invoke(
            FunctionName=os.environ.get('EMBEDDINGS_FUNCTION', 'obsidian-ai-assistant-embeddings'),
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'text': text
            })
        )
        
        # Parse the response
        result = json.loads(response['Payload'].read().decode('utf-8'))
        
        if 'embedding' in result:
            return result['embedding']
        else:
            logger.error(f"Error getting embedding: {result.get('error', 'Unknown error')}")
            return []
    except Exception as e:
        logger.error(f"Error calling embeddings Lambda: {str(e)}")
        return []

def index_note(bucket_name: str, key: str, opensearch_domain: str, index_name: str) -> bool:
    """
    Index a single note in OpenSearch.
    
    Args:
        bucket_name: The S3 bucket name
        key: The S3 object key
        opensearch_domain: The OpenSearch domain name
        index_name: The OpenSearch index name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the note content from S3
        response = s3.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Extract title from filename
        title = os.path.splitext(os.path.basename(key))[0]
        
        # Generate embedding for the content
        embedding = get_embedding(content)
        
        if not embedding:
            logger.warning(f"Could not generate embedding for {key}, skipping")
            return False
        
        # Prepare document for indexing
        document = {
            'id': key,
            'title': title,
            'content': content,
            'embedding': embedding
        }
        
        # Index the document in OpenSearch
        region = os.environ.get('AWS_REGION', 'us-east-1')
        service = 'es'
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token
        )
        
        endpoint = f'https://{opensearch_domain}.{region}.es.amazonaws.com'
        url = f'{endpoint}/{index_name}/_doc/{key.replace("/", "_")}'
        
        response = requests.put(
            url,
            auth=awsauth,
            json=document,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Successfully indexed {key}")
            return True
        else:
            logger.error(f"Error indexing {key}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error processing {key}: {str(e)}")
        return False

def index_all_notes(bucket_name: str, opensearch_domain: str, index_name: str = 'notes') -> None:
    """
    Index all notes from S3 in OpenSearch.
    
    Args:
        bucket_name: The S3 bucket name
        opensearch_domain: The OpenSearch domain name
        index_name: The OpenSearch index name
    """
    logger.info(f"Indexing all notes from bucket {bucket_name} to OpenSearch index {index_name}")
    
    # Ensure the index exists
    try:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        service = 'es'
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token
        )
        
        endpoint = f'https://{opensearch_domain}.{region}.es.amazonaws.com'
        
        # Check if index exists
        response = requests.head(
            f'{endpoint}/{index_name}',
            auth=awsauth
        )
        
        # Create index if it doesn't exist
        if response.status_code != 200:
            logger.info(f"Creating index {index_name}")
            
            # Index mapping with vector field
            mapping = {
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
            
            response = requests.put(
                f'{endpoint}/{index_name}',
                auth=awsauth,
                json=mapping,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Successfully created index {index_name}")
            else:
                logger.error(f"Error creating index {index_name}: {response.text}")
                return
    except Exception as e:
        logger.error(f"Error setting up OpenSearch index: {str(e)}")
        return
    
    # List all objects in the bucket
    try:
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        total_count = 0
        success_count = 0
        
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Only process Markdown files
                if key.endswith('.md'):
                    total_count += 1
                    if index_note(bucket_name, key, opensearch_domain, index_name):
                        success_count += 1
        
        logger.info(f"Indexing complete. Successfully indexed {success_count} of {total_count} notes.")
    except Exception as e:
        logger.error(f"Error listing objects in bucket {bucket_name}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Index all notes in OpenSearch')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--opensearch-domain', help='OpenSearch domain name')
    parser.add_argument('--index-name', default='notes', help='OpenSearch index name')
    
    args = parser.parse_args()
    
    # Get values from environment variables if not provided as arguments
    s3_bucket = args.s3_bucket or os.environ.get('S3_BUCKET')
    opensearch_domain = args.opensearch_domain or os.environ.get('OPENSEARCH_DOMAIN')
    index_name = args.index_name
    
    if not s3_bucket:
        logger.error("S3 bucket name is required")
        sys.exit(1)
    
    if not opensearch_domain:
        logger.error("OpenSearch domain name is required")
        sys.exit(1)
    
    index_all_notes(s3_bucket, opensearch_domain, index_name)

if __name__ == "__main__":
    main() 