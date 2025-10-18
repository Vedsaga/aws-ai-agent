# Diagram 14: System Overview - All Components

## Purpose
High-level view showing how all 13 component diagrams connect together.

## Diagram

```mermaid
flowchart TB
    subgraph UI["User Interface Layer"]
        WebApp["Next.js Web App<br/>Map 80% Chat 20%<br/>See Diagram 01"]
    end
    
    subgraph Auth["Authentication"]
        Cognito["AWS Cognito<br/>JWT Tokens<br/>See Diagram 01"]
    end
    
    subgraph API["API Gateway"]
        APIGW["5 Endpoints<br/>ingest query data config tools<br/>See Diagram 02"]
    end
    
    subgraph Orchestration["Orchestration"]
        StepFunctions["Step Functions<br/>Unified orchestrator<br/>See Diagram 03"]
    end
    
    subgraph Agents["Agent Library"]
        IngestionAgents["Ingestion Agents<br/>Geo Temporal Entity<br/>See Diagram 04"]
        QueryAgents["Query Agents<br/>11 Interrogatives<br/>See Diagram 04"]
    end
    
    subgraph Tools["Tool Registry"]
        ToolACL["Tool Access Control<br/>6 Built-in Tools<br/>See Diagram 05"]
    end
    
    subgraph Config["Configuration"]
        ConfigStore["8 Config Types<br/>DynamoDB<br/>See Diagram 06"]
    end
    
    subgraph DataAccess["Data Access"]
        DataAPIs["4 Data APIs<br/>Retrieval Aggregation Spatial Analytics<br/>See Diagram 07"]
    end
    
    subgraph Storage["Data Storage"]
        RDS["PostgreSQL<br/>See Diagram 08"]
        OpenSearch["OpenSearch<br/>See Diagram 08"]
        S3["S3 Images<br/>See Diagram 08"]
    end
    
    subgraph Realtime["Real-Time"]
        AppSync["AppSync WebSocket<br/>Status streaming<br/>See Diagram 11"]
    end
    
    subgraph RAG["RAG"]
        RAGEngine["RAG Engine<br/>Context retrieval<br/>See Diagram 12"]
    end
    
    subgraph Templates["Templates"]
        DomainTemplates["Domain Templates<br/>Civic Agriculture Disaster<br/>See Diagram 13"]
    end
    
    %% Main Flows
    WebApp -->|Login| Cognito
    WebApp -->|API calls| APIGW
    APIGW -->|Route| StepFunctions
    
    StepFunctions -->|Load config| ConfigStore
    StepFunctions -->|Invoke| IngestionAgents
    StepFunctions -->|Invoke| QueryAgents
    
    IngestionAgents -->|Use tools| ToolACL
    QueryAgents -->|Use tools| ToolACL
    QueryAgents -->|Query data| DataAPIs
    
    DataAPIs -->|Access| RDS
    DataAPIs -->|Search| OpenSearch
    
    IngestionAgents -->|Save| RDS
    IngestionAgents -->|Embed| OpenSearch
    WebApp -->|Upload| S3
    
    StepFunctions -.->|Status| AppSync
    AppSync -.->|Push| WebApp
    
    QueryAgents -.->|Context| RAGEngine
    RAGEngine -.->|Search| OpenSearch
    
    DomainTemplates -.->|Initialize| ConfigStore
    
    %% Diagram References
    WebApp -.->|Ingestion Flow| IngestionAgents
    WebApp -.->|Query Flow| QueryAgents
    IngestionAgents -.->|See Diagram 09| StepFunctions
    QueryAgents -.->|See Diagram 10| StepFunctions
    ConfigStore -.->|See Diagram 15| WebApp

    classDef uiBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef authBox fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef apiBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef orchestrationBox fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    classDef agentBox fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef toolBox fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    classDef configBox fill:#fff8e1,stroke:#f9a825,stroke-width:2px
    classDef dataBox fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef realtimeBox fill:#e0f7fa,stroke:#00838f,stroke-width:2px
    
    class UI uiBox
    class Auth authBox
    class API apiBox
    class Orchestration orchestrationBox
    class Agents agentBox
    class Tools toolBox
    class Config configBox
    class DataAccess,Storage dataBox
    class Realtime realtimeBox
    class RAG,Templates configBox
```

## Component Diagram Index

1. **Authentication & Multi-Tenancy** - Cognito JWT flow, tenant isolation
2. **API Gateway & Endpoints** - 5 REST endpoints with WAF
3. **Unified Orchestrator** - Step Functions dependency graph execution
4. **Agent Library** - Ingestion, Query (11 interrogatives), Custom agents
5. **Tool Registry** - 6 built-in tools with ACL
6. **Configuration Management** - 8 config types in DynamoDB
7. **Data Access Layer** - 4 data service APIs
8. **Data Persistence** - RDS, OpenSearch, DynamoDB, S3
9. **Ingestion Pipeline** - End-to-end data processing flow
10. **Query Pipeline** - End-to-end query analysis flow
11. **Real-Time Status** - AppSync WebSocket broadcasting
12. **RAG Integration** - Semantic search and context retrieval
13. **Domain Configuration** - Pre-built templates
14. **System Overview** - This diagram
15. **Dependency Graph Visualization** - n8n-style editor
16. **Response Formation** - Bullet points and summary generation

## Data Flow Summary

**Ingestion**: User → API Gateway → Step Functions → Agents (parallel + dependent) → Validation → Synthesis → RDS/OpenSearch → Map Update

**Query**: User → API Gateway → Step Functions → Query Agents (parallel) → Data APIs → RDS/OpenSearch → Response Formatter → Bullets + Summary → User

**Real-Time**: All steps publish status → AppSync → WebSocket → User UI

## AWS Services Used

- **Compute**: Lambda, Step Functions
- **API**: API Gateway, AppSync
- **Auth**: Cognito
- **Storage**: RDS PostgreSQL, OpenSearch, DynamoDB, S3
- **AI/ML**: Bedrock (Claude 3), Comprehend, Location Service
- **Integration**: EventBridge
- **Security**: WAF, Secrets Manager, IAM
- **Monitoring**: CloudWatch, X-Ray
