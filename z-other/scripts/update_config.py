#!/usr/bin/env python3
"""
Update AWS configuration settings for the Obsidian AI Assistant.

This script updates environment variables and configuration settings
stored in AWS Systems Manager Parameter Store.
"""

import os
import sys
import boto3
import json
import argparse
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize AWS clients
ssm = boto3.client('ssm')
lambda_client = boto3.client('lambda')

def update_ssm_parameter(name: str, value: str, description: Optional[str] = None) -> bool:
    """
    Update a parameter in AWS Systems Manager Parameter Store.
    
    Args:
        name: The parameter name
        value: The parameter value
        description: Optional description for the parameter
        
    Returns:
        True if successful, False otherwise
    """
    try:
        params = {
            'Name': name,
            'Value': value,
            'Type': 'String',
            'Overwrite': True
        }
        
        if description:
            params['Description'] = description
        
        ssm.put_parameter(**params)
        logger.info(f"Updated parameter {name} to {value}")
        return True
    except Exception as e:
        logger.error(f"Error updating parameter {name}: {str(e)}")
        return False

def update_lambda_environment(function_name: str, variables: Dict[str, str]) -> bool:
    """
    Update environment variables for a Lambda function.
    
    Args:
        function_name: The name of the Lambda function
        variables: Dictionary of environment variables to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current configuration
        response = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        
        # Merge with existing environment variables
        current_vars = response.get('Environment', {}).get('Variables', {})
        updated_vars = {**current_vars, **variables}
        
        # Update the function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': updated_vars
            }
        )
        
        logger.info(f"Updated environment variables for {function_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating Lambda environment for {function_name}: {str(e)}")
        return False

def list_parameters(path: str) -> None:
    """
    List all parameters under a specific path in Parameter Store.
    
    Args:
        path: The parameter path prefix
    """
    try:
        paginator = ssm.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(
            Path=path,
            Recursive=True,
            WithDecryption=True
        )
        
        logger.info(f"Parameters under {path}:")
        for page in page_iterator:
            for param in page.get('Parameters', []):
                logger.info(f"  {param['Name']}: {param['Value']}")
    except Exception as e:
        logger.error(f"Error listing parameters under {path}: {str(e)}")

def update_config_from_file(config_file: str) -> None:
    """
    Update configuration settings from a JSON file.
    
    Args:
        config_file: Path to the JSON configuration file
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Update SSM parameters
        if 'parameters' in config:
            for param_name, param_config in config['parameters'].items():
                update_ssm_parameter(
                    param_name,
                    param_config['value'],
                    param_config.get('description')
                )
        
        # Update Lambda environments
        if 'lambda_environments' in config:
            for function_name, variables in config['lambda_environments'].items():
                update_lambda_environment(function_name, variables)
        
        logger.info(f"Successfully updated configuration from {config_file}")
    except Exception as e:
        logger.error(f"Error updating configuration from {config_file}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Update AWS configuration settings')
    parser.add_argument('--parameter', '-p', action='append', nargs=2, metavar=('NAME', 'VALUE'),
                        help='Update a parameter (can be used multiple times)')
    parser.add_argument('--function', '-f', action='append', nargs=3, metavar=('FUNCTION', 'KEY', 'VALUE'),
                        help='Update a Lambda function environment variable (can be used multiple times)')
    parser.add_argument('--config-file', '-c', help='JSON configuration file')
    parser.add_argument('--list', '-l', help='List parameters under a path')
    
    args = parser.parse_args()
    
    if args.list:
        list_parameters(args.list)
    
    if args.parameter:
        for name, value in args.parameter:
            update_ssm_parameter(name, value)
    
    if args.function:
        function_vars = {}
        for function, key, value in args.function:
            if function not in function_vars:
                function_vars[function] = {}
            function_vars[function][key] = value
        
        for function, variables in function_vars.items():
            update_lambda_environment(function, variables)
    
    if args.config_file:
        update_config_from_file(args.config_file)
    
    if not any([args.parameter, args.function, args.config_file, args.list]):
        parser.print_help()

if __name__ == "__main__":
    main() 