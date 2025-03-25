# Obsidian AI Assistant

An AI-powered assistant for the Obsidian note-taking platform, providing intelligent note management, semantic search, and content generation capabilities.

## Project Overview

The Obsidian AI Assistant is a serverless application built on AWS that enhances the Obsidian note-taking experience with AI capabilities. It provides:

- Secure storage and management of notes
- Semantic search using embeddings
- Text-based search
- Tagging and organization
- Content generation and summarization (coming soon)

## Architecture

The application is built using a serverless architecture on AWS:

- **API Layer**: AWS API Gateway + Lambda functions
- **Storage Layer**: DynamoDB for metadata, S3 for content
- **Search Layer**: Vector embeddings stored in DynamoDB
- **Authentication**: Amazon Cognito

### DynamoDB Table Structure

The `obsidian-notes` table stores note metadata with the following schema:

**Primary Key:**
- `userId` (String, Hash Key) - The user's unique identifier
- `noteId` (String, Range Key) - The note's unique identifier

**Attributes:**
- `title` (String) - The note's title
- `s3Key` (String) - The S3 key where the note's content is stored
- `createdAt` (String) - ISO 8601 timestamp of when the note was created
- `updatedAt` (String) - ISO 8601 timestamp of when the note was last modified
- `tags` (List, Optional) - List of tags associated with the note
- `folder` (String, Optional) - The folder path where the note is stored

**Global Secondary Indexes:**
- `createdAtIndex`
  - Hash Key: `userId`
  - Range Key: `createdAt`
  - Projection: ALL
  - Used for listing notes in chronological order

**Notes:**
- The table uses on-demand (PAY_PER_REQUEST) billing mode
- Content is stored in S3, with the `s3Key` attribute referencing the object
- Timestamps are stored in ISO 8601 format with UTC timezone (e.g., "2024-03-14T12:00:00Z")

### Directory Structure

```
obsidian-ai-assistant/
├── .github/                    # GitHub Actions workflows
│   └── workflows/              # CI/CD pipeline configurations
├── lambdas/                    # Lambda functions
│   ├── functions/              # Individual Lambda functions
│   │   ├── create_note/        # Create note function
│   │   ├── get_note/           # Get note function
│   │   ├── list_notes/         # List notes function
│   │   ├── update_note/        # Update note function
│   │   ├── delete_note/        # Delete note function
│   │   ├── search_notes/       # Search notes function
│   │   └── generate_embeddings/ # Generate embeddings function
│   ├── models/                 # Shared data models
│   └── utils/                  # Shared utilities
├── tests/                      # Integration tests
├── pyproject.toml              # Python project configuration
├── setup.py                    # Package setup
├── requirements.txt            # Dependencies
└── serverless.yml              # Serverless Framework configuration
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 14+ (for Serverless Framework)
- AWS CLI configured with appropriate credentials
- Serverless Framework installed globally

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/obsidian-ai/obsidian-ai-assistant.git
   cd obsidian-ai-assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install -r dev-requirements.txt
   ```

4. Install pre-commit hooks:
   ```
   pre-commit install
   ```

### Local Development

To run tests:
```
pytest
```

To lint the code:
```
ruff check .
black --check .
```

### Deployment

The application can be deployed using the Serverless Framework:

```
serverless deploy --stage dev
```

For production deployment:
```
serverless deploy --stage prod
```

## API Documentation

### Endpoints

- `POST /notes` - Create a new note
- `GET /notes/{noteId}` - Get a note by ID
- `GET /notes` - List notes with optional filtering and pagination
- `PUT /notes/{noteId}` - Update a note
- `DELETE /notes/{noteId}` - Delete a note
- `POST /notes/search` - Search notes (text or semantic search)

### Authentication

All API endpoints require authentication using JWT tokens from Amazon Cognito. Include the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Obsidian team for creating an amazing note-taking platform
- The AWS Serverless community for excellent tools and documentation
