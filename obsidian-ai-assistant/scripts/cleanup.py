#!/usr/bin/env python3
"""
Cleanup script for the Obsidian AI Assistant.

This script removes unused files from S3, DynamoDB, and OpenSearch.
"""

import os
import boto3
import sys
import argparse
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
opensearch = boto3.client('opensearch')

def cleanup_s3(bucket_name, days_old=30):
    """
    Delete objects from S3 that are older than the specified number of days.
    
    Args:
        bucket_name: The name of the S3 bucket
        days_old: Delete objects older than this many days
    """
    logger.info(f"Cleaning up S3 bucket: {bucket_name}")
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    try:
        # List objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        deleted_count = 0
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # Check if object is older than cutoff date
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    deleted_count += 1
                    logger.debug(f"Deleted S3 object: {obj['Key']}")
        
        logger.info(f"Deleted {deleted_count} objects from S3 bucket {bucket_name}")
    except Exception as e:
        logger.error(f"Error cleaning up S3 bucket {bucket_name}: {str(e)}")

def cleanup_dynamodb(table_name, days_old=30):
    """
    Delete items from DynamoDB that are older than the specified number of days.
    
    Args:
        table_name: The name of the DynamoDB table
        days_old: Delete items older than this many days
    """
    logger.info(f"Cleaning up DynamoDB table: {table_name}")
    
    # Calculate cutoff timestamp (assuming 'timestamp' attribute in items)
    cutoff_timestamp = int((datetime.now() - timedelta(days=days_old)).timestamp())
    
    try:
        table = dynamodb.Table(table_name)
        
        # Scan for old items
        response = table.scan(
            FilterExpression="timestamp < :cutoff",
            ExpressionAttributeValues={
                ":cutoff": cutoff_timestamp
            }
        )
        
        deleted_count = 0
        for item in response.get('Items', []):
            table.delete_item(
                Key={
                    'id': item['id']
                }
            )
            deleted_count += 1
            logger.debug(f"Deleted DynamoDB item: {item['id']}")
        
        logger.info(f"Deleted {deleted_count} items from DynamoDB table {table_name}")
    except Exception as e:
        logger.error(f"Error cleaning up DynamoDB table {table_name}: {str(e)}")

def cleanup_opensearch(domain_name, index_name, days_old=30):
    """
    Delete documents from OpenSearch that are older than the specified number of days.
    
    Args:
        domain_name: The OpenSearch domain name
        index_name: The name of the index
        days_old: Delete documents older than this many days
    """
    logger.info(f"Cleaning up OpenSearch index: {index_name}")
    
    # This is a placeholder - actual implementation would use the OpenSearch Python client
    # or make direct API calls to delete old documents
    try:
        # Get domain endpoint
        response = opensearch.describe_domain(DomainName=domain_name)
        endpoint = response['DomainStatus']['Endpoint']
        
        logger.info(f"OpenSearch cleanup would connect to: {endpoint}")
        logger.info(f"Would delete documents older than {days_old} days from index {index_name}")
        
        # Actual implementation would:
        # 1. Connect to OpenSearch
        # 2. Query for documents with timestamp < cutoff_date
        # 3. Delete matching documents
    except Exception as e:
        logger.error(f"Error cleaning up OpenSearch index {index_name}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Clean up unused resources for Obsidian AI Assistant')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--dynamodb-table', help='DynamoDB table name')
    parser.add_argument('--opensearch-domain', help='OpenSearch domain name')
    parser.add_argument('--opensearch-index', help='OpenSearch index name')
    parser.add_argument('--days', type=int, default=30, help='Delete resources older than this many days')
    
    args = parser.parse_args()
    
    # Get values from environment variables if not provided as arguments
    s3_bucket = args.s3_bucket or os.environ.get('S3_BUCKET')
    dynamodb_table = args.dynamodb_table or os.environ.get('DYNAMODB_TABLE')
    opensearch_domain = args.opensearch_domain or os.environ.get('OPENSEARCH_DOMAIN')
    opensearch_index = args.opensearch_index or 'notes'
    
    if s3_bucket:
        cleanup_s3(s3_bucket, args.days)
    
    if dynamodb_table:
        cleanup_dynamodb(dynamodb_table, args.days)
    
    if opensearch_domain and opensearch_index:
        cleanup_opensearch(opensearch_domain, opensearch_index, args.days)
    
    logger.info("Cleanup completed!")

if __name__ == "__main__":
    main() 