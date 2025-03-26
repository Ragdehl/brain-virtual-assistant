"""
Pytest configuration file for common tools tests.
This file contains shared fixtures and configuration for all tests.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the python directory to the path so we can import the lib modules
sys.path.append(os.path.join(os.path.dirname(__file__), "../python"))


@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    return {
        "string_field": "test string",
        "int_field": 42,
        "float_field": 3.14,
        "bool_field": True,
        "list_field": [1, 2, 3],
        "dict_field": {"key": "value"},
        "empty_string": "",
        "zero_int": 0,
        "zero_float": 0.0,
        "false_bool": False,
        "empty_list": [],
        "empty_dict": {},
        "nested": {
            "nested_string": "nested value",
            "nested_int": 100
        }
    }


@pytest.fixture
def mock_uuid():
    """Mock the uuid module to return a fixed UUID."""
    class MockUUID:
        def __init__(self):
            self.hex = "00000000000000000000000000000000"
            
    return MockUUID()


@pytest.fixture
def mock_aws_credentials():
    """Provide mocked AWS credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    

@pytest.fixture
def lambda_context():
    """Create a sample Lambda context for testing."""
    class LambdaContext:
        def __init__(self):
            self.function_name = "test-function"
            self.aws_request_id = "test-request-id"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:us-east-1:123456789012:function:test-function"
            )
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "2022/01/01/[$LATEST]abcdef123456"
            
    return LambdaContext()


@pytest.fixture
def event_body():
    """Provide a sample event body for testing."""
    return {
        "field1": "value1",
        "field2": "value2",
        "numeric_field": 42,
        "nested_field": {
            "nested1": "nested_value1",
            "nested2": 99
        }
    }


@pytest.fixture
def api_gateway_event(event_body):
    """Create a sample API Gateway event for testing."""
    import json
    
    return {
        "body": json.dumps(event_body),
        "resource": "/{proxy+}",
        "path": "/path/to/resource",
        "httpMethod": "POST",
        "isBase64Encoded": False,
        "queryStringParameters": {"param1": "value1", "param2": "value2"},
        "pathParameters": {"proxy": "path/to/resource"},
        "stageVariables": {"baz": "qux"},
        "headers": {
            "Accept": "text/html,application/json",
            "Content-Type": "application/json"
        },
        "requestContext": {
            "resourceId": "123456",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "extendedRequestId": "request-id",
            "requestTime": "09/Apr/2020:12:34:56 +0000",
            "path": "/prod/path/to/resource",
            "accountId": "123456789012",
            "protocol": "HTTP/1.1",
            "stage": "prod",
            "requestTimeEpoch": 1586433296000,
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "sourceIp": "127.0.0.1",
                "principalOrgId": None,
                "accessKey": None,
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None
            },
            "domainName": "example.com",
            "apiId": "1234567890"
        }
    } 