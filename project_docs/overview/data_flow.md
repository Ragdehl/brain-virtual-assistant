# Data Flow

This document describes how data flows through the Obsidian AI Assistant system, including the movement of notes, metadata, embeddings, and other data types between different components.

## System Data Flow Diagram

```mermaid
graph TB
    subgraph Client
        O[Obsidian Client]
        API[API Client]
    end

    subgraph API Gateway
        AG[API Gateway]
    end

    subgraph Lambda Functions
        CN[Create Note]
        GN[Get Note]
        UN[Update Note]
        DN[Delete Note]
        GE[Generate Embeddings]
        SN[Search Notes]
        LN[List Notes]
    end

    subgraph Storage
        DDB[(DynamoDB)]
        S3[(S3)]
        OS[(OpenSearch)]
    end

    subgraph External
        OAI[OpenAI API]
    end

    %% Client to API Gateway
    O -->|HTTP| AG
    API -->|HTTP| AG

    %% API Gateway to Lambda
    AG -->|POST /notes| CN
    AG -->|GET /notes/{id}| GN
    AG -->|PUT /notes/{id}| UN
    AG -->|DELETE /notes/{id}| DN
    AG -->|POST /embeddings| GE
    AG -->|GET /search| SN
    AG -->|GET /notes| LN

    %% Lambda to Storage
    CN -->|Store metadata| DDB
    CN -->|Store content| S3
    CN -->|Store embeddings| OS
    
    GN -->|Get metadata| DDB
    GN -->|Get content| S3
    
    UN -->|Update metadata| DDB
    UN -->|Update content| S3
    UN -->|Update embeddings| OS
    
    DN -->|Delete metadata| DDB
    DN -->|Delete content| S3
    DN -->|Delete embeddings| OS
    
    SN -->|Search| OS
    LN -->|List| DDB

    %% Lambda to External
    GE -->|Generate embeddings| OAI
```

## Data Types

### 1. Note Data

#### Structure
```json
{
    "note_id": "uuid",
    "title": "string",
    "content": "markdown",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "tags": ["string"],
    "metadata": {
        "author": "string",
        "category": "string",
        "status": "string"
    }
}
```

#### Flow
1. **Creation**:
   - Client → API Gateway → Create Note Lambda
   - Lambda → DynamoDB (metadata)
   - Lambda → S3 (content)
   - Lambda → Generate Embeddings Lambda
   - Generate Embeddings → OpenSearch

2. **Retrieval**:
   - Client → API Gateway → Get Note Lambda
   - Lambda → DynamoDB (metadata)
   - Lambda → S3 (content)
   - Response to client

### 2. Embedding Data

#### Structure
```json
{
    "note_id": "uuid",
    "embedding": [float],
    "model": "string",
    "created_at": "timestamp",
    "version": "string"
}
```

#### Flow
1. **Generation**:
   - Note Creation/Update → Generate Embeddings Lambda
   - Lambda → OpenAI API
   - Lambda → OpenSearch
   - Lambda → DynamoDB (metadata)

2. **Usage**:
   - Search Request → Search Lambda
   - Lambda → OpenSearch (vector search)
   - Lambda → DynamoDB (metadata)
   - Response to client

### 3. Search Data

#### Structure
```json
{
    "query": "string",
    "filters": {
        "tags": ["string"],
        "date_range": {
            "start": "timestamp",
            "end": "timestamp"
        }
    },
    "results": [{
        "note_id": "uuid",
        "score": float,
        "metadata": {}
    }]
}
```

#### Flow
1. **Query Processing**:
   - Client → API Gateway → Search Lambda
   - Lambda → OpenSearch (vector + text search)
   - Lambda → DynamoDB (metadata)
   - Response to client

2. **Result Caching**:
   - Search Results → OpenSearch Cache
   - Cache → Subsequent Requests

## Data Storage

### 1. DynamoDB

#### Tables
- **notes_metadata**:
  - Partition key: note_id
  - Sort key: updated_at
  - GSIs for search and filtering

- **embeddings_metadata**:
  - Partition key: note_id
  - Sort key: created_at
  - GSI for model version

#### Data Flow
- Write: Lambda → DynamoDB
- Read: DynamoDB → Lambda
- Update: Lambda → DynamoDB
- Delete: Lambda → DynamoDB

### 2. S3

#### Buckets
- **note-content**:
  - Prefix: {environment}/notes/{note_id}
  - Versioning enabled
  - Lifecycle policies

#### Data Flow
- Write: Lambda → S3
- Read: S3 → Lambda
- Update: Lambda → S3 (new version)
- Delete: Lambda → S3 (delete marker)

### 3. OpenSearch

#### Indices
- **notes**:
  - Vector field for embeddings
  - Text fields for content
  - Metadata fields

#### Data Flow
- Write: Lambda → OpenSearch
- Read: OpenSearch → Lambda
- Update: Lambda → OpenSearch
- Delete: Lambda → OpenSearch

## Data Consistency

### 1. Write Operations

#### Note Creation
1. Write metadata to DynamoDB
2. Write content to S3
3. Generate embeddings
4. Write embeddings to OpenSearch
5. Update embedding metadata in DynamoDB

#### Note Update
1. Update metadata in DynamoDB
2. Update content in S3
3. Update embeddings in OpenSearch
4. Update embedding metadata in DynamoDB

### 2. Read Operations

#### Note Retrieval
1. Read metadata from DynamoDB
2. Read content from S3
3. Combine and return to client

#### Search
1. Query OpenSearch
2. Read metadata from DynamoDB
3. Read content from S3
4. Combine and return to client

## Data Security

### 1. Encryption

#### At Rest
- DynamoDB: AWS KMS
- S3: Server-side encryption
- OpenSearch: AWS KMS

#### In Transit
- API Gateway: TLS 1.2
- Lambda: TLS 1.2
- Storage: TLS 1.2

### 2. Access Control

#### IAM Roles
- Lambda execution roles
- Service roles
- User roles

#### Resource Policies
- S3 bucket policies
- DynamoDB table policies
- OpenSearch domain policies

## Data Monitoring

### 1. Metrics

#### Storage Metrics
- DynamoDB: Read/Write capacity
- S3: Request counts, latency
- OpenSearch: Search latency, indexing rate

#### Application Metrics
- Request latency
- Error rates
- Cache hit rates

### 2. Logging

#### Application Logs
- Lambda function logs
- API Gateway logs
- Service logs

#### Audit Logs
- Access logs
- Change logs
- Error logs 