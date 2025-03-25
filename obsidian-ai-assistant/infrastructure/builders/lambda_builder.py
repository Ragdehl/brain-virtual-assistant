"""
Lambda function builder for AWS resources.
"""
import os
from typing import Any, Dict, List, Optional

from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct

from .base_builder import BaseBuilder


class LambdaBuilder(BaseBuilder):
    """
    Builder for AWS Lambda functions.
    """
    
    def __init__(
        self,
        scope: Construct,
        id_prefix: str,
        environment: str,
        code_dir: str,
        handler: str,
        runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_11,
        memory_size: int = 256,
        timeout: Duration = Duration.seconds(30),
        environment_vars: Optional[Dict[str, str]] = None,
        layers: Optional[List[lambda_.LayerVersion]] = None,
        role: Optional[iam.Role] = None,
        log_retention: logs.RetentionDays = logs.RetentionDays.ONE_WEEK,
        removal_policy: Optional[RemovalPolicy] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Lambda builder.
        
        Args:
            scope: The CDK construct scope
            id_prefix: Prefix for resource IDs
            environment: Deployment environment (dev, test, prod)
            code_dir: Directory containing the Lambda code
            handler: Handler function (e.g., "app.lambda_handler")
            runtime: Lambda runtime
            memory_size: Lambda memory size in MB
            timeout: Lambda timeout duration
            environment_vars: Environment variables for the Lambda
            layers: Lambda layers to attach
            role: IAM role for the Lambda
            log_retention: CloudWatch logs retention period
            removal_policy: AWS CDK removal policy
            tags: Tags to apply to the Lambda
        """
        super().__init__(scope, id_prefix, environment, removal_policy, tags)
        self.code_dir = code_dir
        self.handler = handler
        self.runtime = runtime
        self.memory_size = memory_size
        self.timeout = timeout
        self.environment_vars = environment_vars or {}
        self.layers = layers or []
        self.role = role
        self.log_retention = log_retention
        
        # Extract function name from code_dir
        self.function_name = os.path.basename(os.path.normpath(code_dir))
    
    def build(self) -> lambda_.Function:
        """
        Build the Lambda function.
        
        Returns:
            AWS Lambda function resource
        """
        # Create function name
        function_id = self.get_resource_id(self.function_name)
        function_name = self.get_resource_name(self.function_name)
        
        # Create default role if not provided
        if self.role is None:
            self.role = iam.Role(
                self.scope,
                f"{function_id}-Role",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    )
                ],
            )
        
        # Create the Lambda function
        lambda_function = lambda_.Function(
            self.scope,
            function_id,
            function_name=function_name,
            code=lambda_.Code.from_asset(self.code_dir),
            handler=self.handler,
            runtime=self.runtime,
            memory_size=self.memory_size,
            timeout=self.timeout,
            environment=self.environment_vars,
            layers=self.layers,
            role=self.role,
            log_retention=self.log_retention,
            removal_policy=self.removal_policy,
        )
        
        # Apply tags
        self.apply_tags(lambda_function)
        
        return lambda_function 