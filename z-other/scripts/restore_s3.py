#!/usr/bin/env python3
"""
Restore notes from a backup S3 bucket.

This script restores notes from a backup S3 bucket to the main bucket,
preserving the folder structure.
"""

import os
import sys
import boto3
import argparse
import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
s3 = boto3.client('s3')

def restore_object(backup_bucket: str, target_bucket: str, key: str, overwrite: bool = False) -> bool:
    """
    Restore a single object from backup bucket to target bucket.
    
    Args:
        backup_bucket: The backup S3 bucket name
        target_bucket: The target S3 bucket name
        key: The S3 object key
        overwrite: Whether to overwrite existing objects
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if object already exists in target bucket
        if not overwrite:
            try:
                s3.head_object(Bucket=target_bucket, Key=key)
                logger.warning(f"Object {key} already exists in {target_bucket}, skipping (use --overwrite to force)")
                return False
            except:
                # Object doesn't exist, proceed with restore
                pass
        
        # Copy the object
        s3.copy_object(
            Bucket=target_bucket,
            CopySource={'Bucket': backup_bucket, 'Key': key},
            Key=key
        )
        
        logger.info(f"Restored {key} to {target_bucket}")
        return True
    except Exception as e:
        logger.error(f"Error restoring {key}: {str(e)}")
        return False

def restore_s3(backup_bucket: str, target_bucket: str, prefix: str = '', 
               overwrite: bool = False, max_workers: int = 10) -> None:
    """
    Restore all objects from backup bucket to target bucket.
    
    Args:
        backup_bucket: The backup S3 bucket name
        target_bucket: The target S3 bucket name
        prefix: Only restore objects with this prefix
        overwrite: Whether to overwrite existing objects
        max_workers: Maximum number of concurrent workers
    """
    logger.info(f"Restoring objects from {backup_bucket} to {target_bucket}")
    
    try:
        # Ensure target bucket exists
        try:
            s3.head_bucket(Bucket=target_bucket)
        except:
            logger.info(f"Creating target bucket {target_bucket}")
            s3.create_bucket(Bucket=target_bucket)
        
        # List all objects in the backup bucket
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=backup_bucket, Prefix=prefix)
        
        objects_to_restore = []
        
        # Collect all objects
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                objects_to_restore.append(obj['Key'])
        
        total_count = len(objects_to_restore)
        logger.info(f"Found {total_count} objects to restore")
        
        if total_count == 0:
            logger.warning(f"No objects found in {backup_bucket} with prefix '{prefix}'")
            return
        
        # Restore objects in parallel
        success_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(restore_object, backup_bucket, target_bucket, key, overwrite): key
                for key in objects_to_restore
            }
            
            # Process results as they complete
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing {key}: {str(e)}")
        
        logger.info(f"Restore complete. Successfully restored {success_count} of {total_count} objects.")
    except Exception as e:
        logger.error(f"Error restoring from bucket {backup_bucket}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Restore notes from a backup S3 bucket')
    parser.add_argument('--backup-bucket', required=True, help='Backup S3 bucket name')
    parser.add_argument('--target-bucket', required=True, help='Target S3 bucket name')
    parser.add_argument('--prefix', default='', help='Only restore objects with this prefix')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing objects')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of concurrent workers')
    
    args = parser.parse_args()
    
    restore_s3(
        args.backup_bucket,
        args.target_bucket,
        args.prefix,
        args.overwrite,
        args.max_workers
    )

if __name__ == "__main__":
    main() 