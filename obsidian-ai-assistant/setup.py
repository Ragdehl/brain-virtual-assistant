from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="obsidian-ai-assistant",
    version="0.1.0",
    author="Obsidian AI Team",
    author_email="info@obsidianai.com",
    description="AI-powered assistant for Obsidian note-taking platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ragdehl/brain-virtual-assistant",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.11",
    install_requires=[
        "boto3>=1.26.0",
        "pydantic>=2.0.0",
        "fastapi>=0.95.0",
        "mangum>=0.17.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "pytest-cov>=4.1.0",
            "black>=23.3.0",
            "ruff>=0.0.262",
            "mypy>=1.2.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.1",
        ],
    },
) 