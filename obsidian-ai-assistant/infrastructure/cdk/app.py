"""
CDK app for the Obsidian AI Assistant.
"""
import os

from aws_cdk import App, Environment, Tags

from .obsidian_api_stack import ObsidianApiStack


def get_environment() -> str:
    """
    Get the deployment environment.
    
    Returns:
        The deployment environment (dev, test, prod)
    """
    return os.environ.get("ENVIRONMENT", "dev")


def main() -> None:
    """
    Create and deploy the CDK app.
    """
    # Get the environment
    environment = get_environment()
    
    # Create the CDK app
    app = App()
    
    # Set AWS environment
    aws_env = Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    )
    
    # Create the stack
    stack = ObsidianApiStack(
        app,
        f"ObsidianAiAssistant-{environment}",
        environment=environment,
        env=aws_env,
    )
    
    # Add common tags
    Tags.of(app).add("Project", "ObsidianAIAssistant")
    Tags.of(app).add("Environment", environment)
    Tags.of(app).add("ManagedBy", "CDK")
    
    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main() 