# Diagram 12: RAG Integration Layer

## Purpose
RAG engine for semantic search and context retrieval using OpenSearch.

## Diagram

```mermaid
flowchart TB
    QueryAgent["Query Agent<br/>Needs context"]
    
    RAGEngine["RAG Engine Lambda<br/>Retrieve and generate"]
    
    OpenSearch[("OpenSearch<br/>Vector embeddings<br/>Semantic search")]
    
    PostgreSQL[("PostgreSQL<br/>Structured data<br/>Full text")]
    
    Bedrock["AWS Bedrock<br/>Claude 3<br/>Context generation"]
    
    QueryAgent -->|Step 1 Request context| RAGEngine
    RAGEngine -->|Step 2 Create query embedding| Bedrock
    Bedrock -->|Step 3 Return embedding| RAGEngine
    RAGEngine -->|Step 4 Vector search| OpenSearch
    OpenSearch -->|Step 5 Similar docs| RAGEngine
    RAGEngine -->|Step 6 Get full data| PostgreSQL
    PostgreSQL -->|Step 7 Return records| RAGEngine
    RAGEngine -->|Step 8 Generate context| Bedrock
    Bedrock -->|Step 9 Contextual response| RAGEngine
    RAGEngine -->|Step 10 Return context| QueryAgent

    classDef agentBox fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef ragBox fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    classDef dataBox fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef bedrockBox fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    
    class QueryAgent agentBox
    class RAGEngine ragBox
    class OpenSearch,PostgreSQL dataBox
    class Bedrock bedrockBox
```

## RAG Flow

1. Query agent needs context for question
2. RAG engine creates embedding of question
3. Vector search in OpenSearch finds similar incidents
4. Full incident data retrieved from PostgreSQL
5. Context generated using Bedrock with retrieved data
6. Contextual response returned to query agent
