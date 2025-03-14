#!/usr/bin/env python3
"""
Backup notes from S3 to another S3 bucket.

This script creates a backup of all notes from the main S3 bucket
to a backup bucket, preserving the folder structure.
"""

import os
import sys
import boto3
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')

def backup_object(source_bucket: str, backup_bucket: str, key: str, add_timestamp: bool = False) -> bool:
    """
    Backup a single object from source bucket to backup bucket.
    
    Args:
        source_bucket: The source S3 bucket name
        backup_bucket: The backup S3 bucket name
        key: The S3 object key
        add_timestamp: Whether to add a timestamp to the backup key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Modify key if timestamp is requested
        if add_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename, extension = os.path.splitext(key)
            backup_key = f"{filename}_{timestamp}{extension}"
        else:
            backup_key = key
        
        # Copy the object
        s3.copy_object(
            Bucket=backup_bucket,
            CopySource={'Bucket': source_bucket, 'Key': key},
            Key=backup_key
        )
        
        logger.info(f"Backed up {key} to {backup_key}")
        return True
    except Exception as e:
        logger.error(f"Error backing up {key}: {str(e)}")
        return False

def backup_s3(source_bucket: str, backup_bucket: str, prefix: str = '', 
              add_timestamp: bool = False, max_workers: int = 10) -> None:
    """
    Backup all objects from source bucket to backup bucket.
    
    Args:
        source_bucket: The source S3 bucket name
        backup_bucket: The backup S3 bucket name
        prefix: Only backup objects with this prefix
        add_timestamp: Whether to add a timestamp to backup filenames
        max_workers: Maximum number of concurrent workers
    """
    logger.info(f"Backing up objects from {source_bucket} to {backup_bucket}")
    
    try:
        # Ensure backup bucket exists
        try:
            s3.head_bucket(Bucket=backup_bucket)
        except:
            logger.info(f"Creating backup bucket {backup_bucket}")
            s3.create_bucket(Bucket=backup_bucket)
        
        # List all objects in the source bucket
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=source_bucket, Prefix=prefix)
        
        objects_to_backup = []
        
        # Collect all objects
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                objects_to_backup.append(obj['Key'])
        
        total_count = len(objects_to_backup)
        logger.info(f"Found {total_count} objects to backup")
        
        if total_count == 0:
            logger.warning(f"No objects found in {source_bucket} with prefix '{prefix}'")
            return
        
        # Backup objects in parallel
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(backup_object, source_bucket, backup_bucket, key, add_timestamp): key
                for key in objects_to_backup
            }
            
            # Process results as they complete
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing {key}: {str(e)}")
        
        logger.info(f"Backup complete. Successfully backed up {success_count} of {total_count} objects.")
    except Exception as e:
        logger.error(f"Error backing up bucket {source_bucket}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Backup notes from S3 to another S3 bucket')
    parser.add_argument('--source-bucket', required=True, help='Source S3 bucket name')
    parser.add_argument('--backup-bucket', required=True, help='Backup S3 bucket name')
    parser.add_argument('--prefix', default='', help='Only backup objects with this prefix')
    parser.add_argument('--add-timestamp', action='store_true', help='Add timestamp to backup filenames')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of concurrent workers')
    
    args = parser.parse_args()
    
    backup_s3(
        args.source_bucket,
        args.backup_bucket,
        args.prefix,
        args.add_timestamp,
        args.max_workers
    )

if __name__ == "__main__":
    main() 