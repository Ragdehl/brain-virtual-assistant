#!/bin/bash
# Deploy the Obsidian AI Assistant to AWS

# Set environment variables
export STAGE=${1:-dev}
export REGION=${2:-us-east-1}

echo "Deploying Project-Obsidian to AWS..."

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t layers/common/python

# Package Lambda layers
echo "Packaging Lambda layers..."
mkdir -p .serverless/layers

# Package common layer
cd layers/common
zip -r ../../.serverless/layers/common.zip .
cd ../..

# Deploy with Serverless Framework
echo "Deploying with Serverless Framework..."
serverless deploy --stage $STAGE --region $REGION

# OR deploy using AWS CDK (if applicable)
# cdk deploy

echo "Deployment completed!" 