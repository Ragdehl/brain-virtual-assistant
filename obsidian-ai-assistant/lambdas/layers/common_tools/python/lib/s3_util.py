"""
S3 utility functions for Lambda functions.
"""
import os
from typing import Any, Dict, Optional, Union

import boto3
from botocore.exceptions import ClientError


class S3Util:
    """
    Utility class for S3 operations.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize the S3 utility.

        Args:
            bucket_name (str, optional): S3 bucket name
        """
        self.s3 = boto3.client("s3")
        self.bucket_name = bucket_name or os.environ.get("S3_BUCKET")
        if not self.bucket_name:
            raise ValueError("S3 bucket name is required")

    def get_object(self, key: str) -> Dict[str, Any]:
        """
        Get an object from S3.

        Args:
            key (str): S3 object key

        Returns:
            dict: S3 object
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {key}")
            raise

    def get_object_content(self, key: str) -> str:
        """
        Get an object's content from S3 as a string.

        Args:
            key (str): S3 object key

        Returns:
            str: Object content
        """
        response = self.get_object(key)
        return response["Body"].read().decode("utf-8")

    def put_object(
        self,
        key: str,
        body: Union[str, bytes],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Put an object into S3.

        Args:
            key (str): S3 object key
            body (str/bytes): Object content
            content_type (str, optional): Content type
            metadata (dict, optional): Object metadata

        Returns:
            dict: Response from S3
        """
        put_args = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": body if isinstance(body, bytes) else body.encode("utf-8")
        }

        if content_type:
            put_args["ContentType"] = content_type

        if metadata:
            put_args["Metadata"] = metadata

        try:
            response = self.s3.put_object(**put_args)
            return response
        except ClientError:
            raise

    def delete_object(self, key: str) -> Dict[str, Any]:
        """
        Delete an object from S3.

        Args:
            key (str): S3 object key

        Returns:
            dict: Response from S3
        """
        try:
            response = self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            return response
        except ClientError:
            raise

    def list_objects(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List objects in S3.

        Args:
            prefix (str, optional): Object key prefix
            max_keys (int): Maximum number of keys to return
            continuation_token (str, optional): Continuation token for pagination

        Returns:
            dict: Response from S3
        """
        list_args = {
            "Bucket": self.bucket_name,
            "MaxKeys": max_keys
        }

        if prefix:
            list_args["Prefix"] = prefix

        if continuation_token:
            list_args["ContinuationToken"] = continuation_token

        try:
            response = self.s3.list_objects_v2(**list_args)
            return response
        except ClientError:
            raise

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for an S3 object.

        Args:
            key (str): S3 object key
            expiration (int): URL expiration time in seconds
            http_method (str): HTTP method

        Returns:
            str: Presigned URL
        """
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key
                },
                ExpiresIn=expiration,
                HttpMethod=http_method
            )
            return url
        except ClientError:
            raise

    def copy_object(
        self,
        source_key: str,
        destination_key: str,
        source_bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        metadata_directive: str = "COPY"
    ) -> Dict[str, Any]:
        """
        Copy an object within S3.

        Args:
            source_key (str): Source object key
            destination_key (str): Destination object key
            source_bucket (str, optional): Source bucket name (defaults to same bucket)
            metadata (dict, optional): Object metadata
            metadata_directive (str): Metadata directive (COPY or REPLACE)

        Returns:
            dict: Response from S3
        """
        source_bucket = source_bucket or self.bucket_name
        copy_source = {
            "Bucket": source_bucket,
            "Key": source_key
        }

        copy_args = {
            "Bucket": self.bucket_name,
            "Key": destination_key,
            "CopySource": copy_source,
            "MetadataDirective": metadata_directive
        }

        if metadata and metadata_directive == "REPLACE":
            copy_args["Metadata"] = metadata

        try:
            response = self.s3.copy_object(**copy_args)
            return response
        except ClientError:
            raise
