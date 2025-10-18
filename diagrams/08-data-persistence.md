# Diagram 08: Data Persistence Layer

## Purpose
Shows RDS PostgreSQL, OpenSearch, DynamoDB, and S3 architecture with tenant partitioning.

## AWS Services
- Amazon RDS PostgreSQL, Amazon OpenSearch, Amazon DynamoDB, Amazon S3

## Diagram

```mermaid
flowchart TB
    subgraph Writers["Data Writers"]
        SynthesisLambda["Synthesis Lambda<br/>From orchestrator"]
        IngestHandler["Ingest Handler<br/>Image upload"]
    end
    
    subgraph PostgreSQL["Amazon RDS PostgreSQL"]
        IncidentsTable["incidents table<br/>Partitioned by tenant_id<br/>Structured JSON data"]
        ImagesTable["image_evidence table<br/>Partitioned by tenant_id<br/>S3 references"]
    end
    
    subgraph OpenSearch["Amazon OpenSearch"]
        EmbeddingsIndex["incident_embeddings index<br/>Vector search<br/>Tenant filtered"]
    end
    
    subgraph DynamoDB["Amazon DynamoDB"]
        SessionsTable["user_sessions<br/>PK user_id"]
        ConfigsTable["configurations<br/>PK tenant_id"]
    end
    
    subgraph S3["Amazon S3"]
        EvidenceBucket["Evidence Bucket<br/>Prefix tenant_id domain_id<br/>Image files"]
    end
    
    SynthesisLambda -->|INSERT structured data| IncidentsTable
    SynthesisLambda -->|CREATE embeddings| EmbeddingsIndex
    SynthesisLambda -->|INSERT metadata| ImagesTable
    
    IngestHandler -->|UPLOAD images| EvidenceBucket
    IngestHandler -->|INSERT reference| ImagesTable
    
    IncidentsTable -.->|Foreign key| ImagesTable
    ImagesTable -.->|References| EvidenceBucket

    classDef writerBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef rdsBox fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    classDef osBox fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    classDef ddbBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    classDef s3Box fill:#e0f7fa,stroke:#00838f,stroke-width:3px
    
    class Writers writerBox
    class PostgreSQL rdsBox
    class OpenSearch osBox
    class DynamoDB ddbBox
    class S3 s3Box
```

## PostgreSQL Schema

```sql
CREATE TABLE incidents (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  domain_id VARCHAR(100) NOT NULL,
  raw_text TEXT NOT NULL,
  structured_data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID NOT NULL,
  INDEX idx_tenant_domain (tenant_id, domain_id),
  INDEX idx_created (created_at),
  INDEX idx_structured_gin (structured_data) USING GIN
) PARTITION BY LIST (tenant_id);

CREATE TABLE image_evidence (
  id UUID PRIMARY KEY,
  incident_id UUID REFERENCES incidents(id),
  tenant_id UUID NOT NULL,
  s3_bucket VARCHAR(200),
  s3_key VARCHAR(500),
  uploaded_at TIMESTAMP DEFAULT NOW()
) PARTITION BY LIST (tenant_id);
```

## OpenSearch Index

```json
{
  "mappings": {
    "properties": {
      "incident_id": {"type": "keyword"},
      "tenant_id": {"type": "keyword"},
      "text_embedding": {
        "type": "knn_vector",
        "dimension": 1536
      },
      "text_content": {"type": "text"},
      "created_at": {"type": "date"}
    }
  }
}
```

## S3 Structure

```
s3://tenant-uuid-evidence/
  /civic-complaints/
    /incident-uuid-1/
      /image_001.jpg
      /image_002.png
```
