```mermaid
graph TB
    subgraph Client
        O[Obsidian Client]
        API[API Client]
    end

    subgraph AWS
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

        subgraph External Services
            OAI[OpenAI API]
        end
    end

    %% Client connections
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

    %% Lambda to External Services
    GE -->|Generate embeddings| OAI

    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px;
    classDef lambda fill:#FF9900,stroke:#232F3E,stroke-width:2px;
    classDef storage fill:#FF9900,stroke:#232F3E,stroke-width:2px;
    classDef external fill:#FF9900,stroke:#232F3E,stroke-width:2px;
    
    class AWS,API Gateway,Lambda Functions,Storage,External Services aws;
    class CN,GN,UN,DN,GE,SN,LN lambda;
    class DDB,S3,OS storage;
    class OAI external;
```