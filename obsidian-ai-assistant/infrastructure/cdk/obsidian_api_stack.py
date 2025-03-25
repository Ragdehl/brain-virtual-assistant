"""
CDK stack for the Obsidian AI Assistant API.
"""
import os
from typing import Any, Dict, List, Optional

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct

from ..builders import (
    ApiGatewayBuilder,
    LambdaBuilder,
    LayerBuilder,
    S3Builder,
)


class ObsidianApiStack(Stack):
    """
    CDK stack for the Obsidian AI Assistant API.
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        **kwargs
    ) -> None:
        """
        Initialize the stack.
        
        Args:
            scope: CDK app scope
            construct_id: CDK construct ID
            environment: Deployment environment (dev, test, prod)
            **kwargs: Additional arguments to pass to the Stack constructor
        """
        super().__init__(scope, construct_id, **kwargs)
        
        # Set common properties
        self.environment = environment
        self.id_prefix = "obsidian"
        self.removal_policy = RemovalPolicy.DESTROY if environment != "prod" else RemovalPolicy.RETAIN
        
        # Set paths
        self.lambda_functions_dir = os.path.join(os.path.dirname(__file__), "../../lambdas/functions")
        self.lambda_layers_dir = os.path.join(os.path.dirname(__file__), "../../lambdas/layers")
        
        # Create resources
        self.create_s3_bucket()
        self.create_common_tools_layer()
        self.create_lambda_functions()
        self.create_api_gateway()
        self.create_outputs()
    
    def create_s3_bucket(self) -> None:
        """
        Create the S3 bucket for note content storage.
        """
        s3_builder = S3Builder(
            self,
            self.id_prefix,
            self.environment,
            "notes-content",
            versioned=True,
            cors_enabled=True,
            removal_policy=self.removal_policy,
        )
        
        self.content_bucket = s3_builder.build()
    
    def create_common_tools_layer(self) -> None:
        """
        Create the common tools Lambda layer.
        """
        layer_builder = LayerBuilder(
            self,
            self.id_prefix,
            self.environment,
            "common-tools",
            code_dir=os.path.join(self.lambda_layers_dir, "common_tools"),
            removal_policy=self.removal_policy,
        )
        
        self.common_tools_layer = layer_builder.build()
    
    def create_lambda_functions(self) -> None:
        """
        Create all Lambda functions for the API.
        """
        # Common environment variables for all Lambda functions
        common_env_vars = {
            "DYNAMODB_TABLE": f"{self.id_prefix}-notes-{self.environment}",
            "S3_BUCKET": self.content_bucket.bucket_name,
        }
        
        # Define Lambda function configurations
        lambda_configs = [
            {
                "name": "create_note",
                "handler": "app.lambda_handler",
                "timeout": 10,
                "memory_size": 256,
                "env_vars": {},
            },
            {
                "name": "get_note",
                "handler": "app.lambda_handler",
                "timeout": 10,
                "memory_size": 256,
                "env_vars": {},
            },
            {
                "name": "list_notes",
                "handler": "app.lambda_handler",
                "timeout": 10,
                "memory_size": 256,
                "env_vars": {},
            },
            {
                "name": "update_note",
                "handler": "app.lambda_handler",
                "timeout": 10,
                "memory_size": 256,
                "env_vars": {
                    "EMBEDDING_FUNCTION": f"{self.id_prefix}-generate-embeddings-{self.environment}",
                },
            },
            {
                "name": "delete_note",
                "handler": "app.lambda_handler",
                "timeout": 10,
                "memory_size": 256,
                "env_vars": {},
            },
            {
                "name": "search_notes",
                "handler": "app.lambda_handler",
                "timeout": 30,
                "memory_size": 512,
                "env_vars": {},
            },
            {
                "name": "generate_embeddings",
                "handler": "app.lambda_handler",
                "timeout": 60,
                "memory_size": 512,
                "env_vars": {},
            },
        ]
        
        # Create Lambda functions
        self.lambda_functions = {}
        for config in lambda_configs:
            # Merge common environment variables with function-specific ones
            env_vars = {**common_env_vars, **config["env_vars"]}
            
            lambda_builder = LambdaBuilder(
                self,
                self.id_prefix,
                self.environment,
                code_dir=os.path.join(self.lambda_functions_dir, config["name"]),
                handler=config["handler"],
                timeout=Duration.seconds(config["timeout"]),
                memory_size=config["memory_size"],
                environment_vars=env_vars,
                layers=[self.common_tools_layer],
                removal_policy=self.removal_policy,
            )
            
            # Build the Lambda function
            lambda_function = lambda_builder.build()
            
            # Grant S3 permissions
            self.content_bucket.grant_read_write(lambda_function)
            
            # Store the function for later use
            self.lambda_functions[config["name"]] = lambda_function
    
    def create_api_gateway(self) -> None:
        """
        Create the API Gateway for the Obsidian AI Assistant API.
        """
        # Create the API Gateway
        api_builder = ApiGatewayBuilder(
            self,
            self.id_prefix,
            self.environment,
            "api",
            description=f"Obsidian AI Assistant API - {self.environment} environment",
            cors_enabled=True,
            metrics_enabled=True,
            logging_level=apigw.MethodLoggingLevel.INFO,
            removal_policy=self.removal_policy,
        )
        
        self.api = api_builder.build()
        
        # Add Lambda integrations
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["create_note"],
            "/notes",
            "POST",
        )
        
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["get_note"],
            "/notes/{id}",
            "GET",
        )
        
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["list_notes"],
            "/notes",
            "GET",
        )
        
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["update_note"],
            "/notes/{id}",
            "PUT",
        )
        
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["delete_note"],
            "/notes/{id}",
            "DELETE",
        )
        
        api_builder.add_lambda_integration(
            self.api,
            self.lambda_functions["search_notes"],
            "/notes/search",
            "POST",
        )
    
    def create_outputs(self) -> None:
        """
        Create CloudFormation outputs.
        """
        CfnOutput(
            self,
            "ApiEndpoint",
            description="API Gateway endpoint URL",
            value=self.api.url,
        )
        
        CfnOutput(
            self,
            "ContentBucketName",
            description="S3 bucket for note content",
            value=self.content_bucket.bucket_name,
        ) 