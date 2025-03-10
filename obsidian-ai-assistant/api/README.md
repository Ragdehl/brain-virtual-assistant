# Obsidian AI Assistant API

This directory contains the API server for the Obsidian AI Assistant platform.

## Overview

The API provides RESTful endpoints for managing notes, including:

- Creating, reading, updating, and deleting notes
- Searching notes (both text-based and semantic search)
- Authentication via API keys

## Architecture

The API is built using Express.js and follows a modular architecture:

- `index.js` - Main entry point
- `routes/` - API route definitions
- `controllers/` - Business logic for handling requests
- `models/` - Data models
- `middleware/` - Express middleware
- `utils/` - Utility functions
- `swagger.yaml` - API documentation

## Getting Started

### Prerequisites

- Node.js 14+
- AWS account with appropriate permissions
- AWS CLI configured

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set environment variables:
   ```bash
   export DYNAMODB_TABLE=ObsidianNotes
   export S3_BUCKET=obsidian-notes-bucket
   export EMBEDDINGS_FUNCTION=obsidian-ai-assistant-embeddings
   export OPENSEARCH_DOMAIN=obsidian-search
   export API_KEYS_PARAMETER=/obsidian-ai-assistant/api-keys
   ```

3. Start the server:
   ```bash
   npm start
   ```

   For development with auto-reload:
   ```bash
   npm run dev
   ```

### API Documentation

When running in development mode, Swagger UI is available at:
http://localhost:3000/api-docs

## Authentication

The API uses API keys for authentication. API keys are stored in AWS Systems Manager Parameter Store.

To authenticate requests, include the API key in the `x-api-key` header:

```
x-api-key: your-api-key
```

## Development

### Testing

Run tests:
```bash
npm test
```

### Linting

Run ESLint:
```bash
npm run lint
```

## Deployment

The API is designed to be deployed as a Lambda function or as a containerized application.

For Lambda deployment, see the main project README for instructions using the Serverless Framework.

For container deployment, a Dockerfile is provided in the root directory. 