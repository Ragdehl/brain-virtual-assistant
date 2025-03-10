"""
Helper functions for interacting with DynamoDB.

This module provides a simplified interface for common DynamoDB operations
for the Obsidian AI Assistant application.
"""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from typing import Dict, List, Any, Optional, Union

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name: str = os.environ.get('DYNAMODB_TABLE')
table = dynamodb.Table(table_name)

def get_item(note_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an item from DynamoDB by ID.
    
    Args:
        note_id: The unique identifier of the note
        
    Returns:
        The item from DynamoDB, or None if not found
        
    Raises:
        ClientError: If there's an error communicating with DynamoDB
    """
    response = table.get_item(
        Key={'id': note_id}
    )
    return response.get('Item')

def put_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert or update an item in DynamoDB.
    
    Args:
        item: The item to store in DynamoDB
        
    Returns:
        The response from DynamoDB
        
    Raises:
        ClientError: If there's an error communicating with DynamoDB
    """
    return table.put_item(Item=item)

def delete_item(note_id: str) -> Dict[str, Any]:
    """
    Delete an item from DynamoDB by ID.
    
    Args:
        note_id: The unique identifier of the note
        
    Returns:
        The response from DynamoDB
        
    Raises:
        ClientError: If there's an error communicating with DynamoDB
    """
    return table.delete_item(
        Key={'id': note_id}
    )

def query_items(key_condition: Key, filter_expression: Optional[Attr] = None) -> List[Dict[str, Any]]:
    """
    Query items from DynamoDB.
    
    Args:
        key_condition: The key condition expression
        filter_expression: The filter expression (optional)
        
    Returns:
        The matching items from DynamoDB
        
    Raises:
        ClientError: If there's an error communicating with DynamoDB
    """
    params: Dict[str, Any] = {
        'KeyConditionExpression': key_condition
    }
    
    if filter_expression:
        params['FilterExpression'] = filter_expression
    
    response = table.query(**params)
    return response.get('Items', [])

def scan_items(filter_expression: Optional[Attr] = None) -> List[Dict[str, Any]]:
    """
    Scan all items in the DynamoDB table.
    
    Args:
        filter_expression: The filter expression (optional)
        
    Returns:
        All matching items from DynamoDB
        
    Raises:
        ClientError: If there's an error communicating with DynamoDB
    """
    params: Dict[str, Any] = {}
    
    if filter_expression:
        params['FilterExpression'] = filter_expression
    
    response = table.scan(**params)
    return response.get('Items', []) 