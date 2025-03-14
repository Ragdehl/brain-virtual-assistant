import logging
from datetime import datetime

import boto3
import jwt
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
ssm = boto3.client('ssm')

def get_api_key(api_key):
    """Retrieve and validate API key from AWS Systems Manager Parameter Store.
    
    Args:
        api_key (str): The API key to validate
        
    Returns:
        dict: User information if valid, None if invalid
    """
    try:
        # Get the stored API key from Parameter Store
        parameter_name = f"/obsidian-ai-assistant/api-keys/{api_key}"
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )

        # Parameter value should be JSON string containing user info
        user_info = jwt.decode(
            response['Parameter']['Value'],
            options={"verify_signature": False}
        )

        return user_info
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            return None
        logger.error(f"Error retrieving API key: {str(e)}")
        raise
    except jwt.DecodeError:
        logger.error("Invalid JWT token stored for API key")
        return None

def authenticate(headers):
    """Authenticate request using API key from headers.
    
    Args:
        headers (dict): Request headers
        
    Returns:
        dict: User information if authenticated, None if not
    """
    # Extract API key from headers
    api_key = headers.get('X-Api-Key')
    if not api_key:
        auth_header = headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            api_key = auth_header.split(' ')[1]

    if not api_key:
        return None

    # Validate API key and get user info
    user_info = get_api_key(api_key)
    if not user_info:
        return None

    # Check if API key is expired
    expiry = user_info.get('exp')
    if expiry and datetime.fromtimestamp(expiry) < datetime.utcnow():
        return None

    return user_info
