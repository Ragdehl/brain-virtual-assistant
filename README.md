# Brain Virtual Assistant Platform

A modular AI-powered platform for building intelligent virtual assistants, with a focus on knowledge management and natural language processing.

## 📋 Overview

Brain Virtual Assistant is a cloud-based platform that leverages AI to create specialized virtual assistants. Built on AWS serverless architecture, it provides a foundation for developing AI-powered applications with features like semantic search, embeddings generation, and natural language processing.

## 🌟 Core Platform Features

- **Modular Architecture**: Easy to extend with new virtual assistant projects
- **AI Processing**: Built-in support for embeddings and semantic analysis
- **Serverless Infrastructure**: Scalable AWS-based architecture
- **Secure Data Management**: Encrypted storage and secure API access
- **Common Utilities**: Shared libraries for AWS services integration
- **Developer-Friendly**: Comprehensive documentation and testing tools

## 🏗️ Platform Architecture

The platform follows a modular, serverless architecture:

```
📦 brain-virtual-assistant
├── 📂 common/               # Shared Platform Utilities
│   ├── 📜 dynamo_helper.py    # DynamoDB interactions
│   ├── 📜 s3_helper.py        # S3 operations
│   ├── 📜 opensearch_helper.py # Search functionality
│   ├── 📜 agent_core.py       # Core assistant logic
│   ├── 📜 embeddings.py       # Vector embeddings
│   ├── 📜 config.py           # Configuration management
│   ├── 📜 utils.py           # General utilities
│   └── 📜 logging.py         # Logging system
│
├── 📂 projects/              # Virtual Assistant Projects
│   ├── 📂 obsidian/         # Obsidian Note Management Assistant
│   └── 📂 future-projects/  # Placeholder for future assistants
│
├── 📂 infrastructure/        # Shared AWS Infrastructure
│   ├── 📜 dynamodb.tf       # Database tables
│   ├── 📜 s3.tf            # Storage buckets
│   ├── 📜 opensearch.tf    # Search service
│   └── 📜 lambda_layers.tf # Shared Lambda layers
│
├── 📂 tests/                # Platform-wide Tests
├── 📜 .gitignore
└── 📜 README.md
```

## 🚀 Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.8+
- Node.js 14+ (for infrastructure management)
- AWS CLI configured
- Terraform or AWS CDK (for infrastructure)

### Platform Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/brain-virtual-assistant.git
cd brain-virtual-assistant
```

2. Install platform dependencies:
```bash
pip install -r requirements.txt
npm install
```

3. Deploy shared infrastructure:
```bash
cd infrastructure
terraform init
terraform apply
```

## 🛠️ Development

### Platform Components

- **Common Libraries**: Reusable utilities for AWS services
- **Infrastructure**: Shared AWS resources definitions
- **Projects**: Individual virtual assistant implementations
- **Tests**: Platform-wide testing suite

### Available Platform Scripts

- **setup_platform.sh**: Initializes the platform infrastructure
- **create_project.sh**: Scaffolds a new virtual assistant project
- **deploy_common.sh**: Updates shared components
- **run_platform_tests.sh**: Executes platform-wide tests

## 🔒 Security

- AWS IAM roles with least privilege principle
- Data encryption at rest and in transit
- Secure configuration management
- API authentication and authorization
- Regular security audits

## 📦 Current Projects

### [Obsidian AI Assistant](./projects/obsidian/README.md)
An intelligent note-taking and knowledge management assistant that helps users organize, search, and analyze their notes using AI capabilities.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or support:
- Open an issue on GitHub
- Check our [documentation](./docs)
- Contact the maintainers
