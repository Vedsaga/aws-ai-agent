# DomainFlow Hackathon Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Chat UI     │  │  Mode Switch │  │  Mapbox Map          │  │
│  │  (Messages)  │  │  (3 modes)   │  │  (GeoJSON markers)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (No Auth)                       │
│  POST /orchestrate  │  GET /reports                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Lambda: domainflow-orchestrator                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Route by mode:                                          │   │
│  │  • ingestion  → handle_ingestion()                       │   │
│  │  • query      → handle_query()                           │   │
│  │  • management → handle_management()                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  invoke_bedrock()                                        │   │
│  │  • System prompt (agent-specific)                        │   │
│  │  • User message                                          │   │
│  │  • Conversation history                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                    │                        │
                    │                        │
                    ↓                        ↓
    ┌───────────────────────┐   ┌──────────────────────┐
    │  Bedrock (Claude)     │   │  EventBridge         │
    │  Claude 3.5 Sonnet    │   │  (Status events)     │
    └───────────────────────┘   └──────────────────────┘
                    │
                    ↓
    ┌───────────────────────────────────────┐
    │  DynamoDB: civic-reports              │
    │  PK: report_id                        │
    │  Attributes:                          │
    │  • location, geo_coordinates          │
    │  • entity, severity                   │
    │  • assignee, status, due_at           │
    │  • created_at, updated_at             │
    └───────────────────────────────────────┘
```

## Data Flow

### 1. Ingestion Flow

```
User: "Street light broken near post office"
  ↓
Lambda: mode=ingestion
  ↓
Bedrock: Analyze with Data-Ingestion prompt
  ↓
Response: {needs_clarification: true, question: "Can you confirm address?"}
  ↓
User: "Yes, 123 Main Street"
  ↓
Bedrock: Re-analyze with conversation history
  ↓
Response: {location: "123 Main St", geo: [-74, 40.7], entity: "streetlight", severity: "high"}
  ↓
DynamoDB: Save report
  ↓
EventBridge: Emit "completed" status
  ↓
Frontend: Show confirmation + update map
```

### 2. Query Flow

```
User: "Show me all high-priority issues"
  ↓
Lambda: mode=query
  ↓
Bedrock: Parse query with Data-Query prompt
  ↓
Response: {query_filters: {severity: "high"}}
  ↓
DynamoDB: Scan with filters
  ↓
Lambda: Build GeoJSON from results
  ↓
EventBridge: Emit "completed" status
  ↓
Frontend: Update map with filtered markers
```

### 3. Management Flow

```
User: "Assign this to Team B, due in 48 hours"
  ↓
Lambda: mode=management, report_id=abc-123
  ↓
Bedrock: Parse command with Data-Management prompt
  ↓
Response: {updates: {assignee: "Team B", due_at: "2025-10-25T..."}}
  ↓
DynamoDB: Update report
  ↓
EventBridge: Emit "completed" status
  ↓
Frontend: Show confirmation
```

## Agent Prompts

### Data-Ingestion Agent

**Purpose:** Extract structured data from unstructured text

**System Prompt:**
```
You are a civic complaint intake specialist.

Extract:
1. LOCATION (address, landmark, area)
2. ENTITY (what's broken)
3. SEVERITY (low, medium, high, critical)

If location is vague, ask for clarification.

Output JSON with: location, geo_coordinates, entity, severity, confidence
```

**Tools:** None (demo uses mock geocoding)

**Output Schema:**
```json
{
  "location": "string",
  "geo_coordinates": [longitude, latitude],
  "entity": "string",
  "severity": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "needs_clarification": boolean,
  "clarification_question": "string|null"
}
```

### Data-Query Agent

**Purpose:** Answer questions about existing data

**System Prompt:**
```
You are a civic data analyst.

Parse natural language queries into database filters.

Examples:
- "Show high-priority potholes" → {entity: "pothole", severity: "high"}
- "What's on Main Street?" → {location: "Main Street"}

Output JSON with: query_filters, summary
```

**Tools:** DynamoDB scan (would use GSI in production)

**Output Schema:**
```json
{
  "query_filters": {
    "severity": "string",
    "entity": "string",
    "location": "string"
  },
  "summary": "string"
}
```

### Data-Management Agent

**Purpose:** Update existing reports

**System Prompt:**
```
You are a task management specialist.

Parse commands to update reports:
- Assign to teams
- Update status
- Set due dates

Output JSON with: report_id, updates, confirmation
```

**Tools:** DynamoDB update

**Output Schema:**
```json
{
  "report_id": "string",
  "updates": {
    "assignee": "string",
    "status": "pending|in_progress|resolved|closed",
    "due_at": "ISO 8601 timestamp"
  },
  "confirmation": "string"
}
```

## Real-Time Status Events

EventBridge events emitted during execution:

```json
{
  "Source": "domainflow.orchestrator",
  "DetailType": "AgentStatus",
  "Detail": {
    "session_id": "uuid",
    "agent_id": "data-ingestion|data-query|data-management",
    "status": "running|clarification|completed|error",
    "message": "Human-readable status",
    "data": {},
    "timestamp": "ISO 8601"
  }
}
```

**Status Types:**
- `running`: Agent started processing
- `clarification`: Needs user input
- `completed`: Task finished successfully
- `error`: Something failed

## DynamoDB Schema

**Table:** `civic-reports`

**Primary Key:** `report_id` (String)

**Attributes:**
```json
{
  "report_id": "uuid",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601",
  
  // Ingestion data
  "location": "string",
  "geo_coordinates": [longitude, latitude],
  "entity": "string",
  "severity": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "raw_text": "string",
  
  // Management data
  "assignee": "string",
  "status": "pending|in_progress|resolved|closed",
  "due_at": "ISO 8601",
  "priority": "number",
  
  // Metadata
  "session_id": "uuid",
  "user_id": "string"
}
```

**Indexes:** None (demo uses scan)

**In production would add:**
- GSI on `severity` + `created_at`
- GSI on `assignee` + `status`
- GSI on `geo_coordinates` (geohash)

## Security (Demo vs Production)

### Demo (Current)
- ❌ No authentication
- ❌ No authorization
- ❌ No rate limiting
- ❌ No input validation
- ❌ No tenant isolation

### Production (Would Add)
- ✅ Cognito authorizer on API Gateway
- ✅ IAM roles with least privilege
- ✅ API Gateway throttling
- ✅ Input validation in Lambda
- ✅ Tenant ID in DynamoDB partition key
- ✅ VPC for Lambda + RDS
- ✅ Secrets Manager for credentials
- ✅ CloudWatch alarms

## Cost Estimate (Demo Usage)

**Assumptions:**
- 100 requests/day
- 30 days/month
- Average 2 Bedrock calls per request

**Monthly costs:**
- API Gateway: $0.01 (3,000 requests)
- Lambda: $0.20 (6,000 invocations, 512MB, 5s avg)
- DynamoDB: $0.25 (on-demand, 100 items)
- Bedrock: $6.00 (6,000 calls, Claude 3.5 Sonnet)
- EventBridge: $0.00 (free tier)

**Total: ~$6.50/month**

## Scaling Considerations

### Current Limits
- DynamoDB: Scan is slow (use GSI in production)
- Lambda: 60s timeout (increase if needed)
- Bedrock: 5 req/sec (request quota increase)
- No caching (add ElastiCache for queries)

### Production Optimizations
1. Add DynamoDB GSIs for common queries
2. Implement caching layer (ElastiCache)
3. Use Step Functions for complex orchestration
4. Add SQS for async processing
5. Implement connection pooling for RDS
6. Use CloudFront for frontend
7. Add WAF for API protection

## Monitoring

### CloudWatch Metrics
- Lambda invocations, duration, errors
- DynamoDB read/write capacity
- API Gateway 4xx/5xx errors
- Bedrock throttling

### CloudWatch Logs
- Lambda execution logs
- API Gateway access logs
- Bedrock request/response logs

### Alarms (Would Add)
- Lambda error rate > 5%
- API Gateway latency > 3s
- DynamoDB throttling
- Bedrock quota exceeded
