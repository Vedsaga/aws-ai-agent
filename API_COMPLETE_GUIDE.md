# Complete API Guide - Multi-Agent Orchestration System

## Base URL
```
https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1
```

## Authentication
All endpoints require JWT token in Authorization header:
```bash
Authorization: Bearer <JWT_TOKEN>
```

### Get JWT Token
```bash
# Set password first
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_7QZ7Y6Gbl \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1

# Get token
COGNITO_USERNAME=testuser COGNITO_PASSWORD=TestPassword123! ./get_jwt_token.sh
export JWT_TOKEN='<your_token>'
```

---

## 1. Config API - Agent & Domain Configuration

### 1.1 List Configurations by Type
**Endpoint:** `GET /api/v1/config?type={type}`

**Query Parameters:**
- `type` (required): `agent`, `domain_template`, `playbook`, or `dependency_graph`

**Request:**
```bash
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "configs": [
    {
      "agent_id": "geo_agent",
      "agent_name": "Geo Agent",
      "agent_type": "geo",
      "is_builtin": true,
      "created_by_me": false
    },
    {
      "agent_id": "temporal_agent",
      "agent_name": "Temporal Agent",
      "agent_type": "temporal",
      "is_builtin": true,
      "created_by_me": false
    }
  ],
  "count": 2
}
```

### 1.2 Get Specific Configuration
**Endpoint:** `GET /api/v1/config/{type}/{id}`

**Request:**
```bash
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config/agent/geo_agent" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "agent_id": "geo_agent",
  "agent_name": "Geo Agent",
  "agent_type": "geo",
  "description": "Extracts geographic information",
  "is_builtin": true,
  "created_at": "2025-10-20T10:00:00Z",
  "version": 1
}
```

### 1.3 Create Configuration
**Endpoint:** `POST /api/v1/config`

**Request Body:**
```json
{
  "type": "agent",
  "config": {
    "agent_name": "Custom Agent",
    "agent_type": "custom",
    "description": "My custom agent",
    "capabilities": ["analysis", "extraction"]
  }
}
```

**Request:**
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Custom Agent",
      "agent_type": "custom"
    }
  }'
```

**Response (201 Created):**
```json
{
  "agent_id": "agent_custom_agent_a1b2c3d4",
  "agent_name": "Custom Agent",
  "agent_type": "custom",
  "is_builtin": false,
  "created_at": "2025-10-20T12:00:00Z",
  "created_by": "demo-user",
  "version": 1
}
```

### 1.4 Update Configuration
**Endpoint:** `PUT /api/v1/config/{type}/{id}`

**Request:**
```bash
curl -X PUT "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config/agent/agent_custom_agent_a1b2c3d4" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agent_name": "Updated Agent",
      "description": "Updated description"
    }
  }'
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_custom_agent_a1b2c3d4",
  "agent_name": "Updated Agent",
  "description": "Updated description",
  "updated_at": "2025-10-20T12:30:00Z",
  "version": 2
}
```

### 1.5 Delete Configuration
**Endpoint:** `DELETE /api/v1/config/{type}/{id}`

**Request:**
```bash
curl -X DELETE "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config/agent/agent_custom_agent_a1b2c3d4" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "message": "agent deleted successfully"
}
```

---

## 2. Ingest API - Submit Reports

### 2.1 Submit Report for Processing
**Endpoint:** `POST /api/v1/ingest`

**Request Body:**
```json
{
  "domain_id": "incident_reports",
  "text": "Fire reported at 123 Main St at 2:30 PM. Multiple units responding.",
  "images": ["s3://bucket/image1.jpg"],
  "source": "web",
  "priority": "high",
  "reporter_contact": "john@example.com"
}
```

**Required Fields:**
- `domain_id` (string): Domain identifier
- `text` (string): Report text (max 10,000 characters)

**Optional Fields:**
- `images` (array): Image URLs (max 5)
- `source` (string): Source of report (default: "web")
- `priority` (string): Priority level (default: "normal")
- `reporter_contact` (string): Contact information

**Request:**
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "incident_reports",
    "text": "Fire reported at 123 Main St at 2:30 PM"
  }'
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_5012ff79dd5d467e87e5d9471ac50815",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "2025-10-20T12:04:15.531065",
  "estimated_completion_seconds": 30
}
```

---

## 3. Query API - Ask Questions

### 3.1 Submit Natural Language Query
**Endpoint:** `POST /api/v1/query`

**Request Body:**
```json
{
  "domain_id": "incident_reports",
  "question": "How many fires were reported this week?",
  "filters": {
    "date_range": "last_7_days",
    "location": "downtown"
  },
  "include_visualizations": true
}
```

**Required Fields:**
- `domain_id` (string): Domain identifier
- `question` (string): Natural language question (max 1,000 characters)

**Optional Fields:**
- `filters` (object): Query filters
- `include_visualizations` (boolean): Include charts/graphs (default: false)

**Request:**
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "incident_reports",
    "question": "How many fires were reported this week?"
  }'
```

**Response (202 Accepted):**
```json
{
  "job_id": "query_5f1d74c27c0c401d997a1e79cec99342",
  "status": "accepted",
  "message": "Question submitted for processing",
  "timestamp": "2025-10-20T12:04:16.302781",
  "estimated_completion_seconds": 10
}
```

---

## 4. Tools API - Tool Registry

### 4.1 List Available Tools
**Endpoint:** `GET /api/v1/tools`

**Request:**
```bash
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/tools" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "tools": [
    {
      "tool_name": "bedrock",
      "tool_type": "llm",
      "is_builtin": true
    }
  ],
  "count": 1
}
```

### 4.2 Register New Tool
**Endpoint:** `POST /api/v1/tools`

**Request Body:**
```json
{
  "tool_name": "custom_analyzer",
  "tool_type": "analysis",
  "description": "Custom analysis tool",
  "endpoint": "https://api.example.com/analyze"
}
```

**Request:**
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/tools" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "custom_analyzer",
    "tool_type": "analysis"
  }'
```

**Response (201 Created):**
```json
{
  "tool_name": "custom_analyzer",
  "tool_type": "analysis",
  "is_builtin": false,
  "created_at": "2025-10-20T12:00:00Z"
}
```

---

## 5. Data API - Retrieve Data

### 5.1 Retrieve Data
**Endpoint:** `GET /api/v1/data?type={type}&filters={filters}`

**Query Parameters:**
- `type` (optional): Data type to retrieve
- `filters` (optional): JSON-encoded filters

**Request:**
```bash
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/data?type=retrieval" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [],
  "count": 0
}
```

---

## 6. WebSocket API - Real-time Updates (AppSync GraphQL)

### Status: NOT DEPLOYED
The WebSocket/AppSync stack is defined but not currently deployed.

### Schema Definition
```graphql
type StatusUpdate {
  jobId: ID!
  userId: ID!
  agentName: String
  status: String!
  message: String!
  timestamp: AWSDateTime!
  metadata: AWSJSON
}

type Mutation {
  publishStatus(
    jobId: ID!
    userId: ID!
    agentName: String
    status: String!
    message: String!
    metadata: AWSJSON
  ): StatusUpdate
}

type Subscription {
  onStatusUpdate(userId: ID!): StatusUpdate
    @aws_subscribe(mutations: ["publishStatus"])
}
```

### How to Deploy WebSocket API
```bash
cd infrastructure
npm run deploy:realtime
```

### Usage (Once Deployed)
```javascript
// Subscribe to status updates
const subscription = API.graphql(
  graphqlOperation(onStatusUpdate, { userId: "user123" })
).subscribe({
  next: ({ value }) => {
    console.log('Status update:', value.data.onStatusUpdate);
  }
});

// Publish status update
await API.graphql(
  graphqlOperation(publishStatus, {
    jobId: "job_123",
    userId: "user123",
    status: "processing",
    message: "Agent started processing"
  })
);
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": "Error message",
  "timestamp": "2025-10-20T12:00:00Z",
  "error_code": "ERR_400"
}
```

### Common Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `202 Accepted` - Request accepted for processing
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `405 Method Not Allowed` - Invalid HTTP method
- `500 Internal Server Error` - Server error

---

## Testing All APIs

Run the complete test suite:
```bash
# Set credentials
export JWT_TOKEN=$(COGNITO_USERNAME=testuser COGNITO_PASSWORD=TestPassword123! ./get_jwt_token.sh | grep "export JWT_TOKEN" | cut -d"'" -f2)

# Run tests
python3 test_all_apis.py
```

### Test Results (Latest Run)
```
✓ Config API - List Agents: 200 OK
✓ Config API - List Domain Templates: 200 OK
✓ Ingest API - Submit Report: 202 Accepted
✓ Query API - Ask Question: 202 Accepted
✓ Tools API - List Tools: 200 OK
✓ Data API - Retrieve Data: 200 OK

Passed: 6/6
```

---

## Quick Reference

| Endpoint | Method | Purpose | Status Code |
|----------|--------|---------|-------------|
| `/api/v1/config?type=agent` | GET | List agents | 200 |
| `/api/v1/config/{type}/{id}` | GET | Get config | 200 |
| `/api/v1/config` | POST | Create config | 201 |
| `/api/v1/config/{type}/{id}` | PUT | Update config | 200 |
| `/api/v1/config/{type}/{id}` | DELETE | Delete config | 200 |
| `/api/v1/ingest` | POST | Submit report | 202 |
| `/api/v1/query` | POST | Ask question | 202 |
| `/api/v1/tools` | GET | List tools | 200 |
| `/api/v1/tools` | POST | Register tool | 201 |
| `/api/v1/data` | GET | Retrieve data | 200 |

---

## Notes

1. **Authentication**: All endpoints require valid JWT token from Cognito
2. **CORS**: Enabled for all origins (`*`)
3. **Rate Limiting**: Not currently implemented
4. **Async Processing**: Ingest and Query APIs return job IDs for async processing
5. **WebSocket**: Real-time updates via AppSync (not deployed yet)
6. **Multi-tenancy**: Tenant ID extracted from JWT token
