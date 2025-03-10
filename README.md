# Obsidian AI Assistant

A powerful AI-powered note-taking and knowledge management platform built on AWS serverless architecture.

## 📋 Overview

Obsidian AI Assistant is a cloud-based note management system that leverages AI to help you organize, search, and gain insights from your notes. The platform uses semantic search, embeddings, and natural language processing to provide an intelligent note-taking experience.

## ✨ Features

- **Markdown Notes**: Create and edit notes using Markdown syntax
- **Semantic Search**: Find notes based on meaning, not just keywords
- **AI-Powered Insights**: Get suggestions and connections between your notes
- **Secure Cloud Storage**: All notes are securely stored in AWS S3
- **Responsive Web Interface**: Access your notes from any device
- **API Access**: Integrate with other tools and services

## 🏗️ Architecture

The project follows a modular, serverless architecture:

```
📦 ai-assistant-platform
├── 📂 common/               # Shared utilities & Lambda Layers
│   ├── 📜 dynamo_helper.py
│   ├── 📜 s3_helper.py
│   ├── 📜 opensearch_helper.py
│   ├── 📜 agent_core.py       # Common logic for virtual agents
│   ├── 📜 embeddings.py
│   ├── 📜 config.py
│   ├── 📜 utils.py
│   └── 📜 logging.py
│
├── 📂 project-obsidian/      # First project (current one)
│   ├── 📂 lambdas/
│   ├── 📂 api/
│   ├── 📂 scripts/
│   ├── 📜 serverless.yml
│   ├── 📜 requirements.txt
│   └── 📜 README.md
│
├── 📂 project-x/             # Second project (related one)
│   ├── 📂 lambdas/
│   ├── 📂 api/
│   ├── 📂 scripts/
│   ├── 📜 serverless.yml
│   ├── 📜 requirements.txt
│   └── 📜 README.md
│
├── 📂 infrastructure/        # Shared Terraform/CDK resources
│   ├── 📜 dynamodb.tf
│   ├── 📜 s3.tf
│   ├── 📜 opensearch.tf
│   └── 📜 lambda_layers.tf
│
├── 📂 tests/                 # Global unit and integration tests
├── 📜 .gitignore
└── 📜 README.md
```

### Core Components

- **Lambda Functions**: Serverless functions for CRUD operations on notes
- **DynamoDB**: Stores note metadata and user information
- **S3**: Stores the actual note content
- **OpenSearch**: Provides semantic search capabilities
- **API Gateway**: RESTful API for interacting with the system
- **Lambda Layers**: Shared code and dependencies

## 🚀 Getting Started

### Prerequisites

- AWS Account
- Node.js 14+ and npm
- Python 3.8+
- AWS CLI configured
- Serverless Framework

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/obsidian-ai-assistant.git
   cd obsidian-ai-assistant
   ```

2. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

3. Deploy to AWS:
   ```bash
   cd scripts
   ./deploy.sh
   ```

## 🛠️ Development

### Project Structure

- **lambdas/**: Contains all Lambda functions
  - **notes/**: CRUD operations for notes
  - **embeddings/**: Generates embeddings for semantic search
- **layers/common/**: Shared utilities used across Lambda functions
- **infrastructure/**: Infrastructure as Code (IaC) definitions
- **scripts/**: Utility scripts for deployment, testing, and maintenance
- **tests/**: Unit and integration tests

### Available Scripts

- **deploy.sh**: Deploys the project to AWS
- **cleanup.py**: Cleans up unused resources
- **index_all_notes.py**: Indexes all existing notes into OpenSearch
- **update_config.py**: Updates AWS configuration settings
- **reprocess_embeddings.py**: Recomputes embeddings for all notes
- **backup_s3.py**: Creates a backup of S3 notes
- **restore_s3.py**: Restores backups from S3
- **test_api.py**: Runs tests against API Gateway
- **generate_sample_data.py**: Generates sample notes for testing

## 📝 API Documentation

### Notes API

- `GET /notes`: List all notes
- `POST /notes`: Create a new note
- `GET /notes/{id}`: Get a specific note
- `PUT /notes/{id}`: Update a note
- `DELETE /notes/{id}`: Delete a note
- `GET /notes/search`: Search notes

## 🧪 Testing

Run the test suite:

```bash
cd tests
python -m unittest discover
```

Generate sample data for testing:

```bash
cd scripts
python generate_sample_data.py --s3-bucket your-bucket --dynamodb-table your-table
```

## 🔒 Security

- All data is encrypted at rest and in transit
- API Gateway uses API keys for authentication
- IAM roles follow the principle of least privilege
- Sensitive configuration is stored in AWS Systems Manager Parameter Store

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

For questions or support, please open an issue on GitHub or contact the maintainers directly.
