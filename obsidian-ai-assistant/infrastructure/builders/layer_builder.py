"""
Lambda layer builder for AWS resources.
"""
import os
from typing import Any, Dict, List, Optional

from aws_cdk import (
    RemovalPolicy,
    aws_lambda as lambda_,
)
from constructs import Construct

from .base_builder import BaseBuilder


class LayerBuilder(BaseBuilder):
    """
    Builder for AWS Lambda layers.
    """
    
    def __init__(
        self,
        scope: Construct,
        id_prefix: str,
        environment: str,
        layer_name: str,
        code_dir: str,
        compatible_runtimes: Optional[List[lambda_.Runtime]] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Layer builder.
        
        Args:
            scope: The CDK construct scope
            id_prefix: Prefix for resource IDs
            environment: Deployment environment (dev, test, prod)
            layer_name: Name of the Lambda layer
            code_dir: Directory containing the layer code
            compatible_runtimes: List of compatible Lambda runtimes
            removal_policy: AWS CDK removal policy
            tags: Tags to apply to the layer
        """
        super().__init__(scope, id_prefix, environment, removal_policy, tags)
        self.layer_name = layer_name
        self.code_dir = code_dir
        self.compatible_runtimes = compatible_runtimes or [
            lambda_.Runtime.PYTHON_3_9,
            lambda_.Runtime.PYTHON_3_10,
            lambda_.Runtime.PYTHON_3_11,
        ]
    
    def build(self) -> lambda_.LayerVersion:
        """
        Build the Lambda layer.
        
        Returns:
            AWS Lambda layer resource
        """
        # Create layer name
        layer_id = self.get_resource_id(self.layer_name)
        layer_name = self.get_resource_name(self.layer_name)
        
        # Create the Lambda layer
        layer = lambda_.LayerVersion(
            self.scope,
            layer_id,
            layer_version_name=layer_name,
            code=lambda_.Code.from_asset(self.code_dir),
            compatible_runtimes=self.compatible_runtimes,
            removal_policy=self.removal_policy,
            description=f"Layer for {self.layer_name} - {self.environment} environment",
        )
        
        # Apply tags
        self.apply_tags(layer)
        
        return layer 