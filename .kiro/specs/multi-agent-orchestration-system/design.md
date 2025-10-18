# Design Document

## Overview

The Multi-Agent Orchestration System is a serverless, event-driven architecture built entirely on AWS services. The system processes unstructured text reports through specialized AI agents, stores structured data, and enables natural language querying with multi-perspective analysis. The design emphasizes reproducibility, scalability, and clear demonstration of agentic workflows for hackathon evaluation.

The architecture consists of 16 interconnected components, each designed as an isolated, modular subsystem. All diagrams use Mermaid flowchart format and explicitly show AWS services to facilitate Infrastructure as Code implementation.

## Architecture

### High-Level Architecture Principles

1. **Serverless-First**: All compute uses AWS Lambda for automatic scaling and cost optimization
2. **API-Driven**: All interactions go through API Gateway with no direct database access
3. **Event-Driven**: AppSync and EventBridge provide real-time updates and async processing
4. **Multi-Tenant**: Data partitioned by tenant_id across all storage layers
5. **Single-Level Dependencies**: Agent dependency graphs limited to one parent per agent
6. **Interrogative Analysis**: Query agents organized by question words (When, Where, Why, etc.)

### Technology Stack

**Frontend:**
- Next.js web application
- Mapbox GL JS for geospatial visualization (80% of UI)
- AppSync client for WebSocket real-time updates
- Chat interface (20% of UI)

**Backend:**
- AWS API Gateway (REST + WebSocket)
- AWS Lambda (Python 3.11 for agents)
- AWS Bedrock (Claude 3 for LLM capabilities)
- AWS Comprehend (entity extraction)
- Amazon Location Service (geocoding)

**Data Layer:**
- Amazon RDS PostgreSQL (structured data, tenant-partitioned)
- Amazon OpenSearch Service (vector embeddings for RAG)
- Amazon DynamoDB (session store, configuration store)
- Amazon S3 (image evidence storage)

**Integration:**
- AWS Cognito (authentication)
- AWS AppSync (real-time WebSocket)
- Amazon EventBridge (async events)
- AWS Step Functions (orchestration)

**Deployment:**
- AWS CDK (Infrastructure as Code)
- AWS CloudFormation (stack management)

## Components and Interfaces

### Component Diagram References

The system is decomposed into 16 detailed component diagrams stored in the `diagrams/` folder:

1. `01-authentication-multitenancy.md` - Cognito JWT flow and tenant isolation
2. `02-api-gateway-endpoints.md` - API Gateway with 5 versioned endpoints
3. `03-unified-orchestrator.md` - Step Functions orchestration engine
4. `04-agent-library.md` - Lambda-based agent architecture
5. `05-tool-registry.md` - Centralized tool catalog with ACL
6. `06-configuration-management.md` - DynamoDB configuration store
7. `07-data-access-layer.md` - Four data service APIs
8. `08-data-persistence.md` - RDS, OpenSearch, DynamoDB, S3 architecture
9. `09-ingestion-pipeline.md` - End-to-end data processing flow
10. `10-query-pipeline.md` - End-to-end query analysis flow
11. `11-realtime-status.md` - AppSync WebSocket broadcasting
12. `12-rag-integration.md` - RAG engine with OpenSearch
13. `13-domain-configuration.md` - Domain templates and playbooks
14. `14-system-overview.md` - High-level component relationships
15. `15-dependency-graph-viz.md` - n8n-style visual editor
16. `16-response-formation.md` - Bullet point and summary generation

### Interface Specifications

#### API Gateway Endpoints

**Base URL:** `https://api.{domain}/api/v1`

**Authentication:** All endpoints require `Authorization: Bearer {JWT_TOKEN}` header

**Endpoints:**

1. **POST /ingest**
   - Request: `{ "domain_id": "string", "text": "string", "images": ["base64_string"] }`
   - Response: `{ "job_id": "string", "status": "processing" }`
   - Triggers: Ingestion pipeline via Step Functions

2. **POST /query**
   - Request: `{ "domain_id": "string", "question": "string" }`
   - Response: `{ "job_id": "string", "status": "processing" }`
   - Triggers: Query pipeline via Step Functions

3. **GET /data**
   - Query params: `?type={retrieval|aggregation|spatial|analytics}&filters={json}`
   - Response: `{ "data": [...], "pagination": {...} }`
   - Access: Direct data retrieval

4. **POST /config**
   - Request: `{ "type": "agent|playbook|dependency|tool", "config": {...} }`
   - Response: `{ "config_id": "string", "status": "created" }`
   - Purpose: Create/update configurations

5. **GET /config/{type}/{id}**
   - Response: `{ "config": {...} }`
   - Purpose: Retrieve configurations

#### AppSync WebSocket

**Connection:** `wss://realtime.{domain}/graphql`

**Subscription:**
```graphql
subscription OnStatusUpdate($userId: ID!) {
  onStatusUpdate(userId: $userId) {
    jobId
    agentName
    status
    message
    timestamp
  }
}
```

**Status Messages:**
- `loading_agents` - Orchestrator loading playbook
- `invoking_{agent_name}` - Agent starting execution
- `calling_{tool_name}` - Agent invoking tool
- `agent_complete_{agent_name}` - Agent finished
- `validating` - Validation layer processing
- `synthesizing` - Synthesis layer merging outputs
- `complete` - Job finished

#### Agent Interface

All agents implement a standard Lambda handler interface:

**Input Event:**
```python
{
  "job_id": "string",
  "tenant_id": "string",
  "raw_text": "string",
  "parent_output": {...},  # Optional, if agent has dependency
  "agent_config": {
    "system_prompt": "string",
    "tools": ["tool_name"],
    "output_schema": {...}
  }
}
```

**Output:**
```python
{
  "agent_name": "string",
  "output": {
    "key1": "value1",  # Max 5 keys
    "key2": "value2"
  },
  "status": "success|error",
  "execution_time_ms": 1234
}
```

#### Tool Interface

Tools are invoked via Lambda function URLs or API endpoints:

**Request:**
```json
{
  "tool_name": "string",
  "parameters": {...},
  "tenant_id": "string"
}
```

**Response:**
```json
{
  "result": {...},
  "status": "success|error",
  "error_message": "string"  # If error
}
```

**Built-in Tools:**

1. **Amazon Location Service**
   - Function: Geocoding, reverse geocoding
   - Input: `{ "address": "string" }` or `{ "coordinates": [lat, lng] }`
   - Output: `{ "location": {...}, "coordinates": [...] }`

2. **AWS Comprehend**
   - Function: Entity extraction, sentiment analysis
   - Input: `{ "text": "string", "language": "en" }`
   - Output: `{ "entities": [...], "sentiment": "string" }`

3. **Web Search API**
   - Function: External information retrieval
   - Input: `{ "query": "string", "max_results": 5 }`
   - Output: `{ "results": [...] }`

4. **Data Query APIs**
   - Function: Internal data retrieval
   - Input: `{ "api_type": "retrieval|aggregation|spatial|analytics", "filters": {...} }`
   - Output: `{ "data": [...] }`

5. **Vector Search**
   - Function: Semantic similarity search
   - Input: `{ "query_text": "string", "top_k": 10 }`
   - Output: `{ "results": [...] }`

6. **Custom Domain APIs**
   - Function: User-defined integrations
   - Input: User-defined schema
   - Output: User-defined schema

## Data Models

### Database Schema (PostgreSQL)

**Table: incidents**
```sql
CREATE TABLE incidents (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  domain_id VARCHAR(100) NOT NULL,
  raw_text TEXT NOT NULL,
  structured_data JSONB NOT NULL,  -- Agent outputs
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_by UUID NOT NULL,
  
  -- Indexes
  INDEX idx_tenant_domain (tenant_id, domain_id),
  INDEX idx_created_at (created_at),
  INDEX idx_structured_data_gin (structured_data) USING GIN
) PARTITION BY LIST (tenant_id);
```

**Table: image_evidence**
```sql
CREATE TABLE image_evidence (
  id UUID PRIMARY KEY,
  incident_id UUID REFERENCES incidents(id),
  tenant_id UUID NOT NULL,
  s3_key VARCHAR(500) NOT NULL,
  s3_bucket VARCHAR(200) NOT NULL,
  content_type VARCHAR(100),
  file_size_bytes INTEGER,
  uploaded_at TIMESTAMP DEFAULT NOW(),
  
  INDEX idx_incident (incident_id)
) PARTITION BY LIST (tenant_id);
```

### DynamoDB Tables

**Table: user_sessions**
```
Partition Key: user_id (String)
Sort Key: session_id (String)

Attributes:
- tenant_id (String)
- chat_id (String)
- connection_id (String)  -- AppSync connection
- created_at (Number)
- expires_at (Number)
- last_activity (Number)

TTL: expires_at
GSI: tenant_id-index
```

**Table: configurations**
```
Partition Key: tenant_id (String)
Sort Key: config_type#config_id (String)

Attributes:
- config_type (String)  -- agent|playbook|dependency|tool|schema|template
- config_data (Map)
- version (Number)
- created_at (Number)
- updated_at (Number)
- created_by (String)

GSI: config_type-index
```

**Table: agent_configs**
```
Partition Key: tenant_id (String)
Sort Key: agent_id (String)

Attributes:
- agent_name (String)
- agent_type (String)  -- ingestion|query|custom
- system_prompt (String)
- tools (List<String>)
- output_schema (Map)
- dependency_parent (String)  -- Optional, single parent agent_id
- interrogative (String)  -- For query agents: when|where|why|how|what|who|which|how_many|how_much|from_where|what_kind
- is_builtin (Boolean)
- created_at (Number)
```

**Table: playbook_configs**
```
Partition Key: tenant_id (String)
Sort Key: playbook_id (String)

Attributes:
- domain_id (String)
- playbook_type (String)  -- ingestion|query
- agent_ids (List<String>)
- description (String)
- created_at (Number)
```

**Table: dependency_graphs**
```
Partition Key: tenant_id (String)
Sort Key: graph_id (String)

Attributes:
- playbook_id (String)
- edges (List<Map>)  -- [{ "from": "agent_id", "to": "agent_id" }]
- created_at (Number)
```

### OpenSearch Index Schema

**Index: incident_embeddings**
```json
{
  "mappings": {
    "properties": {
      "incident_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "domain_id": { "type": "keyword" },
      "text_embedding": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "text_content": { "type": "text" },
      "structured_data": { "type": "object" },
      "created_at": { "type": "date" }
    }
  }
}
```

### S3 Bucket Structure

**Bucket: {tenant-id}-evidence**
```
/{tenant_id}/
  /{domain_id}/
    /{incident_id}/
      /image_001.jpg
      /image_002.png
```

**Bucket: {tenant-id}-config-backups**
```
/{tenant_id}/
  /agents/
    /{agent_id}_v{version}.json
  /playbooks/
    /{playbook_id}_v{version}.json
```

## Error Handling

### Error Categories

1. **Authentication Errors (401)**
   - Invalid JWT token
   - Expired token
   - Missing authorization header
   - Response: `{ "error": "unauthorized", "message": "..." }`

2. **Authorization Errors (403)**
   - Tenant mismatch
   - Configuration not found for tenant
   - Response: `{ "error": "forbidden", "message": "..." }`

3. **Validation Errors (400)**
   - Invalid domain_id
   - Missing required fields
   - Schema validation failure
   - Response: `{ "error": "validation_error", "fields": [...] }`

4. **Agent Execution Errors (500)**
   - Agent timeout (>5 minutes)
   - Tool invocation failure
   - Output schema mismatch
   - Response: `{ "error": "agent_error", "agent_name": "...", "message": "..." }`

5. **Dependency Errors (400)**
   - Circular dependency detected
   - Multi-level dependency attempted
   - Parent agent not found
   - Response: `{ "error": "dependency_error", "message": "..." }`

### Error Handling Strategy

**Agent Level:**
- Each agent wrapped in try-catch with timeout (5 minutes)
- Failed agents publish error status via AppSync
- Orchestrator continues with remaining agents
- Final synthesis includes partial results with error annotations

**Orchestrator Level:**
- Step Functions catch states for each agent invocation
- Retry logic: 3 attempts with exponential backoff
- Dead letter queue (SQS) for failed jobs
- CloudWatch alarms for error rate thresholds

**API Level:**
- API Gateway request validation
- Lambda authorizer for JWT validation
- Rate limiting: 100 requests/minute per user
- Circuit breaker pattern for downstream services

**Data Level:**
- PostgreSQL transaction rollback on validation failure
- S3 versioning for image evidence
- DynamoDB conditional writes for configuration updates
- OpenSearch bulk indexing with error handling

### Monitoring and Observability

**CloudWatch Metrics:**
- Agent execution time (per agent)
- Agent success/failure rate
- API Gateway latency (p50, p95, p99)
- Step Functions execution duration
- AppSync connection count
- Database connection pool utilization

**CloudWatch Logs:**
- Agent execution logs (structured JSON)
- API Gateway access logs
- Lambda function logs
- Step Functions execution history

**X-Ray Tracing:**
- End-to-end request tracing
- Agent dependency visualization
- Performance bottleneck identification

## Testing Strategy

### Unit Testing

**Agent Testing:**
- Mock tool responses
- Test output schema compliance
- Test dependency input handling
- Test error scenarios (timeout, invalid input)
- Coverage target: 80%

**API Testing:**
- Test all endpoint request/response formats
- Test authentication/authorization
- Test validation logic
- Test error responses

### Integration Testing

**Pipeline Testing:**
- Test ingestion pipeline end-to-end with sample data
- Test query pipeline with various interrogatives
- Test dependency graph execution order
- Test real-time status broadcasting

**AWS Service Integration:**
- Test Cognito authentication flow
- Test AppSync WebSocket connections
- Test Bedrock API calls
- Test Comprehend entity extraction
- Test Location Service geocoding
- Test RDS queries
- Test OpenSearch vector search
- Test S3 image upload/retrieval

### Performance Testing

**Load Testing:**
- Simulate 100 concurrent users
- Test agent execution under load
- Test database query performance
- Test AppSync connection limits

**Scalability Testing:**
- Test Lambda concurrency limits
- Test Step Functions execution limits
- Test API Gateway throttling
- Test database connection pooling

### Demo Testing

**End-to-End Scenarios:**
1. **Civic Complaint Submission:**
   - User selects "Civic Complaints" domain
   - Submits "Pothole on Main Street" with image
   - Verify real-time status updates
   - Verify structured data extraction
   - Verify map marker placement

2. **Multi-Perspective Query:**
   - User asks "What are the trends in pothole complaints?"
   - Verify query agents execute (What, Where, When, Why)
   - Verify bullet point response format
   - Verify summary generation
   - Verify map visualization update

3. **Custom Agent Creation:**
   - User creates "Severity Classifier" agent
   - Configures tools and output schema
   - Adds to "Civic Complaints" playbook
   - Submits test report
   - Verify custom agent executes

4. **Dependency Graph:**
   - User creates "Priority Agent" depending on "Severity Classifier"
   - Visualizes dependency in n8n-style editor
   - Submits test report
   - Verify execution order (Severity → Priority)

## Deployment Architecture

### Infrastructure as Code (AWS CDK)

**Stack Structure:**
```
/infrastructure
  /lib
    /stacks
      - auth-stack.ts          # Cognito user pool
      - api-stack.ts           # API Gateway + Lambda authorizer
      - agent-stack.ts         # Lambda functions for agents
      - orchestration-stack.ts # Step Functions state machines
      - data-stack.ts          # RDS, OpenSearch, DynamoDB
      - storage-stack.ts       # S3 buckets
      - realtime-stack.ts      # AppSync API
      - monitoring-stack.ts    # CloudWatch dashboards
    /constructs
      - agent-construct.ts     # Reusable agent Lambda
      - api-endpoint.ts        # Reusable API endpoint
  /bin
    - app.ts                   # CDK app entry point
```

**Deployment Steps:**
1. `npm install` - Install CDK dependencies
2. `cdk bootstrap` - Bootstrap CDK environment
3. `cdk deploy --all` - Deploy all stacks (~25 minutes)
4. `npm run seed-data` - Load sample domains and agents
5. `npm run test-deployment` - Run smoke tests

### Environment Configuration

**Parameters (SSM Parameter Store):**
- `/app/bedrock/model-id` - Claude 3 model identifier
- `/app/cognito/user-pool-id` - Cognito user pool
- `/app/database/connection-string` - RDS connection
- `/app/opensearch/endpoint` - OpenSearch domain
- `/app/s3/evidence-bucket` - S3 bucket name

**Secrets (AWS Secrets Manager):**
- `/app/database/credentials` - RDS master password
- `/app/api-keys/web-search` - External API keys

### Multi-Region Considerations

**Primary Region:** us-east-1 (for demo)

**Future Multi-Region:**
- DynamoDB Global Tables for configuration
- S3 Cross-Region Replication for images
- RDS Read Replicas in secondary regions
- Route 53 for DNS failover

## Security Considerations

### Authentication and Authorization

- Cognito user pools with MFA support
- JWT tokens with 1-hour expiration
- Refresh tokens with 30-day expiration
- Lambda authorizer validates all API requests

### Data Encryption

- RDS encryption at rest (AES-256)
- S3 encryption at rest (SSE-S3)
- DynamoDB encryption at rest
- TLS 1.2+ for all data in transit

### Network Security

- API Gateway with AWS WAF
- Lambda functions in VPC (for RDS access)
- Security groups restricting database access
- VPC endpoints for AWS service access

### Tenant Isolation

- Database row-level security by tenant_id
- S3 bucket policies by tenant prefix
- DynamoDB partition key includes tenant_id
- Lambda execution role scoped to tenant resources

### Audit Logging

- CloudTrail for all API calls
- Database audit logs for data access
- Configuration change history in DynamoDB
- S3 access logs for image evidence

## Diagram File Structure

All 16 detailed component diagrams are stored in:

```
.kiro/specs/multi-agent-orchestration-system/diagrams/
  01-authentication-multitenancy.md
  02-api-gateway-endpoints.md
  03-unified-orchestrator.md
  04-agent-library.md
  05-tool-registry.md
  06-configuration-management.md
  07-data-access-layer.md
  08-data-persistence.md
  09-ingestion-pipeline.md
  10-query-pipeline.md
  11-realtime-status.md
  12-rag-integration.md
  13-domain-configuration.md
  14-system-overview.md
  15-dependency-graph-viz.md
  16-response-formation.md
```

Each diagram file contains:
- Mermaid flowchart with AWS services explicitly labeled
- Component descriptions
- Data flow annotations
- AWS service configuration notes
