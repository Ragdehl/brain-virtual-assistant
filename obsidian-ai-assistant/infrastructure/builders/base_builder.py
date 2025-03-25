"""
Base builder class for AWS resources.
"""
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from aws_cdk import RemovalPolicy, Stack
from constructs import Construct


class BaseBuilder(ABC):
    """
    Base builder class for AWS resources.
    
    All resource builders should inherit from this class and implement
    the build method.
    """
    
    def __init__(
        self, 
        scope: Construct, 
        id_prefix: str,
        environment: str,
        removal_policy: Optional[RemovalPolicy] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the base builder.
        
        Args:
            scope: The CDK construct scope
            id_prefix: Prefix for resource IDs
            environment: Deployment environment (dev, test, prod)
            removal_policy: AWS CDK removal policy
            tags: Tags to apply to all resources
        """
        self.scope = scope
        self.id_prefix = id_prefix
        self.environment = environment
        self.removal_policy = removal_policy or RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN
        self.tags = tags or {}
        
        # Add default tags
        self.tags.update({
            "Project": "ObsidianAIAssistant",
            "Environment": environment,
            "ManagedBy": "CDK"
        })
    
    def get_resource_id(self, resource_name: str) -> str:
        """
        Generate a standardized resource ID.
        
        Args:
            resource_name: The name of the resource
            
        Returns:
            Standardized resource ID with prefix and environment
        """
        return f"{self.id_prefix}-{resource_name}-{self.environment}"
    
    def get_resource_name(self, resource_name: str) -> str:
        """
        Generate a standardized resource name.
        
        Args:
            resource_name: The name of the resource
            
        Returns:
            Standardized resource name with prefix and environment
        """
        return f"{self.id_prefix}-{resource_name}-{self.environment}"
    
    def apply_tags(self, resource: Any) -> None:
        """
        Apply tags to a resource.
        
        Args:
            resource: The AWS resource to tag
        """
        for key, value in self.tags.items():
            Stack.of(self.scope).tag_resource(resource, key, value)
    
    @abstractmethod
    def build(self) -> Any:
        """
        Build the AWS resource.
        
        This method must be implemented by all child builders.
        
        Returns:
            The built AWS resource
        """
        pass 