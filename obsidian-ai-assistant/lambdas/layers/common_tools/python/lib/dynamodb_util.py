"""
DynamoDB utility functions for Lambda functions.
"""
import os
import uuid
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError


class DynamoDBUtil:
    """
    Utility class for DynamoDB operations.
    """

    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize the DynamoDB utility.

        Args:
            table_name (str, optional): DynamoDB table name
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("DYNAMODB_TABLE")
        if not self.table_name:
            raise ValueError("DynamoDB table name is required")
        self.table = self.dynamodb.Table(self.table_name)

    def get_item(self, key: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get an item from DynamoDB.

        Args:
            key (dict): Primary key of the item to get

        Returns:
            dict: Item from DynamoDB

        Raises:
            NotFoundError: If the item is not found
            ServerError: If there's an error accessing DynamoDB
        """
        try:
            response = self.table.get_item(Key=key)
            item = response.get("Item")
            
            if not item:
                raise NotFoundError(f"Item not found with key: {key}")
                
            return item
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise NotFoundError(f"Table {self.table_name} not found")
            raise ServerError(f"Error accessing DynamoDB: {str(e)}")
        except Exception as e:
            raise ServerError(f"Unexpected error: {str(e)}")

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Put an item into DynamoDB.

        Args:
            item (dict): Item to put

        Returns:
            dict: Response from DynamoDB
        """
        try:
            response = self.table.put_item(Item=item)
            return response
        except ClientError:
            raise

    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        condition_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an item in DynamoDB.

        Args:
            key (dict): Primary key of the item to update
            update_expression (str): Update expression
            expression_attribute_values (dict): Expression attribute values
            expression_attribute_names (dict, optional): Expression attribute names
            condition_expression (str, optional): Condition expression

        Returns:
            dict: Response from DynamoDB
        """
        update_args = {
            "Key": key,
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ReturnValues": "ALL_NEW"
        }

        if expression_attribute_names:
            update_args["ExpressionAttributeNames"] = expression_attribute_names

        if condition_expression:
            update_args["ConditionExpression"] = condition_expression

        try:
            response = self.table.update_item(**update_args)
            return response
        except ClientError:
            raise

    def delete_item(self, key: Dict[str, Any], condition_expression: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete an item from DynamoDB.

        Args:
            key (dict): Primary key of the item to delete
            condition_expression (str, optional): Condition expression

        Returns:
            dict: Response from DynamoDB
        """
        delete_args = {
            "Key": key,
            "ReturnValues": "ALL_OLD"
        }

        if condition_expression:
            delete_args["ConditionExpression"] = condition_expression

        try:
            response = self.table.delete_item(**delete_args)
            return response
        except ClientError:
            raise

    def query(
        self,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        filter_expression: Optional[str] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
        scan_index_forward: bool = True
    ) -> Dict[str, Any]:
        """
        Query items from DynamoDB.

        Args:
            key_condition_expression (str): Key condition expression
            expression_attribute_values (dict): Expression attribute values
            expression_attribute_names (dict, optional): Expression attribute names
            filter_expression (str, optional): Filter expression
            index_name (str, optional): Index name
            limit (int, optional): Maximum number of items to return
            exclusive_start_key (dict, optional): Exclusive start key for pagination
            scan_index_forward (bool): Whether to scan index forward

        Returns:
            dict: Response from DynamoDB
        """
        query_args = {
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ScanIndexForward": scan_index_forward
        }

        if expression_attribute_names:
            query_args["ExpressionAttributeNames"] = expression_attribute_names

        if filter_expression:
            query_args["FilterExpression"] = filter_expression

        if index_name:
            query_args["IndexName"] = index_name

        if limit:
            query_args["Limit"] = limit

        if exclusive_start_key:
            query_args["ExclusiveStartKey"] = exclusive_start_key

        try:
            response = self.table.query(**query_args)
            return response
        except ClientError:
            raise

    def scan(
        self,
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        expression_attribute_names: Optional[Dict[str, str]] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scan items from DynamoDB.

        Args:
            filter_expression (str, optional): Filter expression
            expression_attribute_values (dict, optional): Expression attribute values
            expression_attribute_names (dict, optional): Expression attribute names
            index_name (str, optional): Index name
            limit (int, optional): Maximum number of items to return
            exclusive_start_key (dict, optional): Exclusive start key for pagination

        Returns:
            dict: Response from DynamoDB
        """
        scan_args = {}

        if filter_expression:
            scan_args["FilterExpression"] = filter_expression

        if expression_attribute_values:
            scan_args["ExpressionAttributeValues"] = expression_attribute_values

        if expression_attribute_names:
            scan_args["ExpressionAttributeNames"] = expression_attribute_names

        if index_name:
            scan_args["IndexName"] = index_name

        if limit:
            scan_args["Limit"] = limit

        if exclusive_start_key:
            scan_args["ExclusiveStartKey"] = exclusive_start_key

        try:
            response = self.table.scan(**scan_args)
            return response
        except ClientError:
            raise

    @staticmethod
    def generate_id() -> str:
        """
        Generate a unique ID for a DynamoDB item.

        Returns:
            str: Unique ID
        """
        return str(uuid.uuid4())
