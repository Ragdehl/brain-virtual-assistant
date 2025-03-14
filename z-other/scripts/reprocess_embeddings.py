#!/usr/bin/env python3
"""
Recompute embeddings for all notes.

This script regenerates embeddings for all notes in S3 and updates
the corresponding entries in OpenSearch.
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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def update_note_embedding(bucket_name: str, key: str, opensearch_domain: str, index_name: str) -> bool:
    """
    Update the embedding for a single note.
    
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
        
        # Generate new embedding for the content
        embedding = get_embedding(content)
        
        if not embedding:
            logger.warning(f"Could not generate embedding for {key}, skipping")
            return False
        
        # Set up AWS authentication for OpenSearch
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
        doc_id = key.replace("/", "_")
        
        # First, check if the document exists
        check_url = f'{endpoint}/{index_name}/_doc/{doc_id}'
        check_response = requests.head(check_url, auth=awsauth)
        
        if check_response.status_code == 200:
            # Document exists, get current document
            get_response = requests.get(check_url, auth=awsauth)
            current_doc = get_response.json().get('_source', {})
            
            # Update the embedding
            current_doc['embedding'] = embedding
            
            # Update the document in OpenSearch
            update_response = requests.put(
                check_url,
                auth=awsauth,
                json=current_doc,
                headers={'Content-Type': 'application/json'}
            )
            
            if update_response.status_code >= 200 and update_response.status_code < 300:
                logger.info(f"Successfully updated embedding for {key}")
                return True
            else:
                logger.error(f"Error updating embedding for {key}: {update_response.text}")
                return False
        else:
            # Document doesn't exist, create a new one
            new_doc = {
                'id': key,
                'title': title,
                'content': content,
                'embedding': embedding
            }
            
            create_response = requests.put(
                check_url,
                auth=awsauth,
                json=new_doc,
                headers={'Content-Type': 'application/json'}
            )
            
            if create_response.status_code >= 200 and create_response.status_code < 300:
                logger.info(f"Created new document with embedding for {key}")
                return True
            else:
                logger.error(f"Error creating document for {key}: {create_response.text}")
                return False
    except Exception as e:
        logger.error(f"Error processing {key}: {str(e)}")
        return False

def reprocess_all_embeddings(bucket_name: str, opensearch_domain: str, index_name: str = 'notes', max_workers: int = 5) -> None:
    """
    Reprocess embeddings for all notes in S3.
    
    Args:
        bucket_name: The S3 bucket name
        opensearch_domain: The OpenSearch domain name
        index_name: The OpenSearch index name
        max_workers: Maximum number of concurrent workers
    """
    logger.info(f"Reprocessing embeddings for all notes in bucket {bucket_name}")
    
    try:
        # List all objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        markdown_files = []
        
        # Collect all Markdown files
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Only process Markdown files
                if key.endswith('.md'):
                    markdown_files.append(key)
        
        total_count = len(markdown_files)
        logger.info(f"Found {total_count} Markdown files to process")
        
        # Process files in parallel
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(update_note_embedding, bucket_name, key, opensearch_domain, index_name): key
                for key in markdown_files
            }
            
            # Process results as they complete
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing {key}: {str(e)}")
        
        logger.info(f"Reprocessing complete. Successfully updated {success_count} of {total_count} notes.")
    except Exception as e:
        logger.error(f"Error listing objects in bucket {bucket_name}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Recompute embeddings for all notes')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--opensearch-domain', help='OpenSearch domain name')
    parser.add_argument('--index-name', default='notes', help='OpenSearch index name')
    parser.add_argument('--max-workers', type=int, default=5, help='Maximum number of concurrent workers')
    
    args = parser.parse_args()
    
    # Get values from environment variables if not provided as arguments
    s3_bucket = args.s3_bucket or os.environ.get('S3_BUCKET')
    opensearch_domain = args.opensearch_domain or os.environ.get('OPENSEARCH_DOMAIN')
    index_name = args.index_name
    max_workers = args.max_workers
    
    if not s3_bucket:
        logger.error("S3 bucket name is required")
        sys.exit(1)
    
    if not opensearch_domain:
        logger.error("OpenSearch domain name is required")
        sys.exit(1)
    
    reprocess_all_embeddings(s3_bucket, opensearch_domain, index_name, max_workers)

if __name__ == "__main__":
    main() 