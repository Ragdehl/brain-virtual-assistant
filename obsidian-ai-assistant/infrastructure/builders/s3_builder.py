"""
S3 bucket builder for AWS resources.
"""
from typing import Any, Dict, List, Optional

from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct

from .base_builder import BaseBuilder


class S3Builder(BaseBuilder):
    """
    Builder for AWS S3 buckets.
    """
    
    def __init__(
        self,
        scope: Construct,
        id_prefix: str,
        environment: str,
        bucket_name: str,
        versioned: bool = False,
        encryption: s3.BucketEncryption = s3.BucketEncryption.S3_MANAGED,
        block_public_access: bool = True,
        cors_enabled: bool = False,
        lifecycle_rules: Optional[List[s3.LifecycleRule]] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        auto_delete_objects: bool = False,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the S3 builder.
        
        Args:
            scope: The CDK construct scope
            id_prefix: Prefix for resource IDs
            environment: Deployment environment (dev, test, prod)
            bucket_name: Name of the S3 bucket
            versioned: Whether to enable versioning
            encryption: Encryption configuration
            block_public_access: Whether to block public access
            cors_enabled: Whether to enable CORS
            lifecycle_rules: Lifecycle rules for the bucket
            removal_policy: AWS CDK removal policy
            auto_delete_objects: Whether to automatically delete objects on bucket removal
            tags: Tags to apply to the bucket
        """
        super().__init__(scope, id_prefix, environment, removal_policy, tags)
        self.bucket_name = bucket_name
        self.versioned = versioned
        self.encryption = encryption
        self.block_public_access = block_public_access
        self.cors_enabled = cors_enabled
        self.lifecycle_rules = lifecycle_rules or []
        self.auto_delete_objects = auto_delete_objects
        
        # Don't auto delete in prod unless explicitly specified
        if environment == "prod" and auto_delete_objects is None:
            self.auto_delete_objects = False
    
    def build(self) -> s3.Bucket:
        """
        Build the S3 bucket.
        
        Returns:
            AWS S3 bucket resource
        """
        # Create bucket name
        bucket_id = self.get_resource_id(self.bucket_name)
        bucket_name = self.get_resource_name(self.bucket_name)
        
        # Configure CORS if enabled
        cors_config = None
        if self.cors_enabled:
            cors_config = [
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=Duration.days(1),
                )
            ]
        
        # Configure public access block
        block_public_access = s3.BlockPublicAccess.BLOCK_ALL if self.block_public_access else None
        
        # Create the S3 bucket
        bucket = s3.Bucket(
            self.scope,
            bucket_id,
            bucket_name=bucket_name,
            versioned=self.versioned,
            encryption=self.encryption,
            block_public_access=block_public_access,
            cors=cors_config,
            lifecycle_rules=self.lifecycle_rules,
            removal_policy=self.removal_policy,
            auto_delete_objects=self.auto_delete_objects,
        )
        
        # Apply tags
        self.apply_tags(bucket)
        
        return bucket 