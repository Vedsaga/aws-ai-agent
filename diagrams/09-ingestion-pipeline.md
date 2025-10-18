# Diagram 09: Ingestion Pipeline End-to-End Flow

## Purpose
Complete flow from user submission to data storage with real-time status updates.

## Diagram

```mermaid
flowchart TB
    User["User submits report<br/>Text plus images<br/>Domain selected"]
    
    APIGW["API Gateway<br/>POST /api/v1/ingest"]
    
    IngestHandler["Ingest Handler Lambda<br/>Upload images to S3<br/>Start Step Functions"]
    
    StepFunctions["Step Functions<br/>Load playbook<br/>Build execution plan"]
    
    ParallelAgents["Execute Parallel Agents<br/>Geo Temporal Entity"]
    
    DependentAgent["Execute Dependent Agent<br/>Severity Classifier<br/>Waits for Entity"]
    
    Validate["Validate Outputs<br/>Check schemas<br/>Max 5 keys"]
    
    Synthesize["Synthesize Results<br/>Merge into JSON"]
    
    SaveData["Save to RDS<br/>Create embeddings<br/>Store in OpenSearch"]
    
    AppSync["AppSync broadcasts<br/>Real-time status<br/>To user chat"]
    
    MapUpdate["EventBridge triggers<br/>Map update<br/>New marker"]
    
    User -->|Step 1| APIGW
    APIGW -->|Step 2| IngestHandler
    IngestHandler -->|Step 3| StepFunctions
    StepFunctions -->|Step 4| ParallelAgents
    ParallelAgents -->|Step 5| DependentAgent
    DependentAgent -->|Step 6| Validate
    Validate -->|Step 7| Synthesize
    Synthesize -->|Step 8| SaveData
    SaveData -->|Step 9| MapUpdate
    
    StepFunctions -.->|Status updates| AppSync
    ParallelAgents -.->|Status updates| AppSync
    DependentAgent -.->|Status updates| AppSync
    Validate -.->|Status updates| AppSync
    Synthesize -.->|Status updates| AppSync
    AppSync -.->|WebSocket| User

    classDef userBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef processBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef statusBox fill:#e0f7fa,stroke:#00838f,stroke-width:2px
    
    class User userBox
    class APIGW,IngestHandler,StepFunctions,ParallelAgents,DependentAgent,Validate,Synthesize,SaveData,MapUpdate processBox
    class AppSync statusBox
```

## Flow Steps

1. User selects domain and submits text with images
2. API Gateway validates JWT and routes to ingest handler
3. Handler uploads images to S3, starts Step Functions
4. Step Functions loads playbook and dependency graph
5. Parallel agents execute (Geo, Temporal, Entity)
6. Dependent agent waits for parent (Severity waits for Entity)
7. Validator checks all outputs against schemas
8. Synthesizer merges into single JSON document
9. Data saved to RDS, embeddings to OpenSearch
10. EventBridge triggers map update
11. Real-time status via AppSync throughout

## Example Status Messages

```
- "Loading agents for civic-complaints domain"
- "Invoking Geo Agent"
- "Geo Agent calling Amazon Location"
- "Geo Agent complete"
- "Invoking Entity Agent"
- "Entity Agent calling AWS Comprehend"
- "Entity Agent complete"
- "Waiting for Entity Agent before Severity Classifier"
- "Invoking Severity Classifier"
- "Severity Classifier complete"
- "Validating outputs"
- "Synthesizing results"
- "Saving to database"
- "Complete - Incident ID: uuid"
```
