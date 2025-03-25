"""
API Gateway builder for AWS resources.
"""
from typing import Any, Dict, List, Optional, Union

from aws_cdk import (
    RemovalPolicy,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct

from .base_builder import BaseBuilder


class ApiGatewayBuilder(BaseBuilder):
    """
    Builder for AWS API Gateway.
    """
    
    def __init__(
        self,
        scope: Construct,
        id_prefix: str,
        environment: str,
        api_name: str,
        description: Optional[str] = None,
        cors_enabled: bool = True,
        authorization_type: Optional[apigw.AuthorizationType] = None,
        authorizer: Optional[apigw.IAuthorizer] = None,
        api_key_required: bool = False,
        metrics_enabled: bool = True,
        logging_level: Optional[apigw.MethodLoggingLevel] = None,
        throttling_rate_limit: Optional[float] = None,
        throttling_burst_limit: Optional[int] = None,
        default_method_options: Optional[Dict[str, Any]] = None,
        removal_policy: Optional[RemovalPolicy] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the API Gateway builder.
        
        Args:
            scope: The CDK construct scope
            id_prefix: Prefix for resource IDs
            environment: Deployment environment (dev, test, prod)
            api_name: Name of the API Gateway
            description: Description of the API Gateway
            cors_enabled: Whether to enable CORS
            authorization_type: Default authorization type for methods
            authorizer: Default authorizer for methods
            api_key_required: Whether an API key is required for methods
            metrics_enabled: Whether to enable CloudWatch metrics
            logging_level: CloudWatch logging level
            throttling_rate_limit: Default throttling rate limit
            throttling_burst_limit: Default throttling burst limit
            default_method_options: Default options for all methods
            removal_policy: AWS CDK removal policy
            tags: Tags to apply to the API Gateway
        """
        super().__init__(scope, id_prefix, environment, removal_policy, tags)
        self.api_name = api_name
        self.description = description or f"{api_name} API - {environment} environment"
        self.cors_enabled = cors_enabled
        self.authorization_type = authorization_type
        self.authorizer = authorizer
        self.api_key_required = api_key_required
        self.metrics_enabled = metrics_enabled
        self.logging_level = logging_level or apigw.MethodLoggingLevel.ERROR
        self.throttling_rate_limit = throttling_rate_limit
        self.throttling_burst_limit = throttling_burst_limit
        self.default_method_options = default_method_options or {}
        
        # Set default options if not provided
        if "authorizationType" not in self.default_method_options and self.authorization_type:
            self.default_method_options["authorizationType"] = self.authorization_type
        
        if "authorizer" not in self.default_method_options and self.authorizer:
            self.default_method_options["authorizer"] = self.authorizer
        
        if "apiKeyRequired" not in self.default_method_options:
            self.default_method_options["apiKeyRequired"] = self.api_key_required
        
        if "methodResponses" not in self.default_method_options:
            self.default_method_options["methodResponses"] = [
                {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                },
                {"statusCode": "400"},
                {"statusCode": "401"},
                {"statusCode": "403"},
                {"statusCode": "404"},
                {"statusCode": "500"},
            ]
    
    def build(self) -> apigw.RestApi:
        """
        Build the API Gateway.
        
        Returns:
            AWS API Gateway resource
        """
        # Create API Gateway name
        api_id = self.get_resource_id(self.api_name)
        api_name = self.get_resource_name(self.api_name)
        
        # Configure CORS if enabled
        cors_options = None
        if self.cors_enabled:
            cors_options = apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=apigw.Cors.DEFAULT_HEADERS + [
                    "Authorization",
                    "X-Api-Key",
                    "Content-Type",
                ],
                max_age=3600,
            )
        
        # Create default gateway responses
        gateway_responses = {
            apigw.DefaultResponseType.ACCESS_DENIED: {
                "responseParameters": {
                    "gatewayresponse.header.Access-Control-Allow-Origin": "'*'"
                }
            },
            apigw.DefaultResponseType.DEFAULT_4XX: {
                "responseParameters": {
                    "gatewayresponse.header.Access-Control-Allow-Origin": "'*'"
                }
            },
            apigw.DefaultResponseType.DEFAULT_5XX: {
                "responseParameters": {
                    "gatewayresponse.header.Access-Control-Allow-Origin": "'*'"
                }
            },
        }
        
        # Create the API Gateway
        api = apigw.RestApi(
            self.scope,
            api_id,
            rest_api_name=api_name,
            description=self.description,
            default_cors_preflight_options=cors_options,
            deploy_options=apigw.StageOptions(
                stage_name=self.environment,
                metrics_enabled=self.metrics_enabled,
                logging_level=self.logging_level,
                throttling_rate_limit=self.throttling_rate_limit,
                throttling_burst_limit=self.throttling_burst_limit,
            ),
            default_method_options=self.default_method_options,
            default_integration_options=apigw.IntegrationOptions(
                timeout=apigw.Duration.seconds(29)
            ),
            gateway_responses=gateway_responses,
        )
        
        # Apply tags
        self.apply_tags(api)
        
        return api
    
    def add_lambda_integration(
        self,
        api: apigw.RestApi,
        lambda_function: lambda_.Function,
        path: str,
        http_method: str,
        api_key_required: Optional[bool] = None,
        authorization_type: Optional[apigw.AuthorizationType] = None,
        authorizer: Optional[apigw.IAuthorizer] = None,
        request_parameters: Optional[Dict[str, bool]] = None,
        request_models: Optional[Dict[str, apigw.Model]] = None,
        method_responses: Optional[List[Dict[str, Any]]] = None,
    ) -> apigw.Method:
        """
        Add a Lambda integration to the API Gateway.
        
        Args:
            api: API Gateway instance
            lambda_function: Lambda function to integrate
            path: API path (e.g., /notes/{noteId})
            http_method: HTTP method (GET, POST, etc.)
            api_key_required: Whether an API key is required
            authorization_type: Authorization type for this method
            authorizer: Authorizer for this method
            request_parameters: Request parameters for this method
            request_models: Request models for this method
            method_responses: Method responses for this method
            
        Returns:
            API Gateway method with Lambda integration
        """
        # Parse the path into segments to create the resource path
        path_segments = [segment for segment in path.split("/") if segment]
        resource = api.root
        
        # Create resources for each path segment
        for segment in path_segments:
            existing_resource = next(
                (r for r in resource.resources if r.path_part == segment),
                None
            )
            if existing_resource:
                resource = existing_resource
            else:
                resource = resource.add_resource(segment)
        
        # Set default values from the builder if not provided
        if api_key_required is None:
            api_key_required = self.api_key_required
        
        if authorization_type is None and self.authorization_type:
            authorization_type = self.authorization_type
        
        if authorizer is None and self.authorizer:
            authorizer = self.authorizer
        
        if method_responses is None:
            method_responses = self.default_method_options.get("methodResponses")
        
        # Create the Lambda integration
        integration = apigw.LambdaIntegration(
            lambda_function,
            proxy=True,
            allow_test_invoke=True,
        )
        
        # Add method options
        method_options = {
            "apiKeyRequired": api_key_required,
        }
        
        if authorization_type:
            method_options["authorizationType"] = authorization_type
        
        if authorizer:
            method_options["authorizer"] = authorizer
        
        if request_parameters:
            method_options["requestParameters"] = request_parameters
        
        if request_models:
            method_options["requestModels"] = request_models
        
        if method_responses:
            method_options["methodResponses"] = method_responses
        
        # Add the method to the resource
        method = resource.add_method(http_method, integration, **method_options)
        
        # Grant the API Gateway permission to invoke the Lambda
        lambda_function.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        
        return method 