# API Documentation & Testing

**Base URL:** `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`  
**Authentication:** JWT Bearer Token (Cognito)  
**Test Status:** ✅ 11/11 tests passing (100% success rate)

---

## Authentication

All endpoints require JWT token in Authorization header:
```bash
Authorization: Bearer {JWT_TOKEN}
```

### Get JWT Token

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text
```

**Test Credentials:**
- Username: `testuser`
- Password: `TestPassword123!`
- User Pool ID: `us-east-1_7QZ7Y6Gbl`
- Client ID: `6gobbpage9af3nd7ahm3lchkct`

---

## API Endpoints

### 1. Configuration API

#### List Agents
```bash
GET /api/v1/config?type=agent
Authorization: Bearer {JWT_TOKEN}
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
  "count": 5
}
```

#### Create Agent
```bash
POST /api/v1/config
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "type": "agent",
  "config": {
    "agent_name": "Custom Agent",
    "agent_type": "custom",
    "system_prompt": "You are a helpful assistant",
    "tools": ["bedrock"],
    "output_schema": {
      "result": "string",
      "confidence": "number"
    }
  }
}
```

**Response (201 Created):**
```json
{
  "agent_id": "agent_abc123",
  "agent_name": "Custom Agent",
  "agent_type": "custom",
  "is_builtin": false,
  "created_at": "2025-10-21T10:00:00Z",
  "created_by": "testuser",
  "version": 1
}
```

#### Get Specific Agent
```bash
GET /api/v1/config/agent/{agent_id}
Authorization: Bearer {JWT_TOKEN}
```

**Response (200 OK):**
```json
{
  "agent_id": "geo_agent",
  "agent_name": "Geo Agent",
  "agent_type": "geo",
  "description": "Extracts geographic information",
  "is_builtin": true,
  "system_prompt": "Extract location data...",
  "tools": ["bedrock", "location_service"],
  "output_schema": {
    "location": "object",
    "coordinates": "array"
  }
}
```

#### Update Agent
```bash
PUT /api/v1/config/agent/{agent_id}
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "config": {
    "agent_name": "Updated Agent Name",
    "description": "Updated description"
  }
}
```

**Response (200 OK):**
```json
{
  "agent_id": "agent_abc123",
  "agent_name": "Updated Agent Name",
  "description": "Updated description",
  "updated_at": "2025-10-21T10:30:00Z",
  "version": 2
}
```

#### Delete Agent
```bash
DELETE /api/v1/config/agent/{agent_id}
Authorization: Bearer {JWT_TOKEN}
```

**Response (200 OK):**
```json
{
  "message": "agent deleted successfully"
}
```

#### List Domain Templates
```bash
GET /api/v1/config?type=domain_template
Authorization: Bearer {JWT_TOKEN}
```

**Response (200 OK):**
```json
{
  "configs": [
    {
      "domain_id": "civic_complaints",
      "domain_name": "Civic Complaints",
      "is_builtin": true
    }
  ],
  "count": 1
}
```

---

### 2. Ingest API

#### Submit Report
```bash
POST /api/v1/ingest
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "domain_id": "civic_complaints",
  "text": "Broken streetlight on Main Street near the library",
  "images": ["s3://bucket/image1.jpg"],
  "source": "web",
  "priority": "high"
}
```

**Required Fields:**
- `domain_id` (string): Domain identifier
- `text` (string): Report text (max 10,000 characters)

**Optional Fields:**
- `images` (array): Image URLs (max 5)
- `source` (string): Source of report (default: "web")
- `priority` (string): Priority level (default: "normal")

**Response (202 Accepted):**
```json
{
  "job_id": "job_abc123def456",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "2025-10-21T10:00:00Z",
  "estimated_completion_seconds": 30
}
```

---

### 3. Query API

#### Ask Question
```bash
POST /api/v1/query
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "domain_id": "civic_complaints",
  "question": "What are the most common complaints this month?",
  "filters": {
    "date_range": "last_30_days",
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
- `include_visualizations` (boolean): Include charts/graphs

**Response (202 Accepted):**
```json
{
  "job_id": "query_xyz789",
  "query_id": "qry_abc123",
  "status": "accepted",
  "message": "Query submitted for processing",
  "timestamp": "2025-10-21T10:00:00Z",
  "estimated_completion_seconds": 10
}
```

---

### 4. Tools API

#### List Tools
```bash
GET /api/v1/tools
Authorization: Bearer {JWT_TOKEN}
```

**Response (200 OK):**
```json
{
  "tools": [
    {
      "tool_name": "bedrock",
      "tool_type": "llm",
      "is_builtin": true,
      "description": "AWS Bedrock LLM service"
    }
  ],
  "count": 1
}
```

#### Register Tool
```bash
POST /api/v1/tools
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "tool_name": "custom_analyzer",
  "tool_type": "analysis",
  "description": "Custom analysis tool",
  "endpoint": "https://api.example.com/analyze"
}
```

**Response (201 Created):**
```json
{
  "tool_name": "custom_analyzer",
  "tool_type": "analysis",
  "is_builtin": false,
  "created_at": "2025-10-21T10:00:00Z"
}
```

---

### 5. Data API

#### Retrieve Data
```bash
GET /api/v1/data?type=retrieval&filters={filters}
Authorization: Bearer {JWT_TOKEN}
```

**Query Parameters:**
- `type` (optional): Data type to retrieve
- `filters` (optional): JSON-encoded filters

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "incident_id": "inc_123",
      "domain_id": "civic_complaints",
      "text": "Broken streetlight...",
      "extracted_data": {
        "location": "Main Street",
        "timestamp": "2025-10-21T10:00:00Z"
      }
    }
  ],
  "count": 1
}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": "Error message",
  "timestamp": "2025-10-21T10:00:00Z",
  "error_code": "ERR_400"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 202 | Accepted | Request accepted for processing |
| 400 | Bad Request | Invalid request |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

---

## Testing

### Automated Testing

Run the comprehensive test suite:

```bash
python3 TEST.py
```

**Test Coverage:**
1. ✅ Authentication (401 without token)
2. ✅ Config API - List Agents (200 OK)
3. ✅ Config API - List Domains (200 OK)
4. ✅ Config API - Create Agent (201 Created)
5. ✅ Config API - Get Agent (200 OK)
6. ✅ Config API - Update Agent (200 OK)
7. ✅ Config API - Delete Agent (200 OK)
8. ✅ Ingest API - Submit Report (202 Accepted)
9. ✅ Query API - Ask Question (202 Accepted)
10. ✅ Tools API - List Tools (200 OK)
11. ✅ Data API - Retrieve Data (200 OK)

**Expected Result:** 11/11 tests passed (100%)

### Manual Testing

#### Test Config API
```bash
# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# List agents
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

#### Test Ingest API
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "Test report - broken streetlight on Main Street"
  }' | jq .
```

#### Test Query API
```bash
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints?"
  }' | jq .
```

---

## Built-in Agents

The system includes 5 built-in agents:

1. **Geo Agent** (`geo_agent`)
   - Extracts geographic information
   - Tools: bedrock, location_service
   - Output: location, coordinates, address

2. **Temporal Agent** (`temporal_agent`)
   - Extracts time information
   - Tools: bedrock
   - Output: timestamp, date, time_of_day

3. **Entity Agent** (`entity_agent`)
   - Identifies entities
   - Tools: bedrock, comprehend
   - Output: entities, categories

4. **What Agent** (`what_agent`)
   - Answers "what" questions
   - Tools: bedrock
   - Output: answer, confidence

5. **Where Agent** (`where_agent`)
   - Answers "where" questions
   - Tools: bedrock, location_service
   - Output: location, answer

---

## Rate Limits

Currently no rate limits are enforced. For production:
- Recommended: 100 requests/minute per user
- Burst: 200 requests/minute
- Implement using API Gateway throttling

---

## Best Practices

### Authentication
- Store JWT tokens securely
- Refresh tokens before expiry
- Never commit tokens to version control

### Request Optimization
- Use pagination for large result sets
- Cache frequently accessed data
- Batch requests when possible

### Error Handling
- Always check HTTP status codes
- Implement retry logic with exponential backoff
- Log errors for debugging

### Data Validation
- Validate input before sending
- Check required fields
- Respect field length limits

---

## Frontend Integration

### API Client Example (TypeScript)

```typescript
import { Amplify, Auth } from 'aws-amplify';

// Configure Amplify
Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_7QZ7Y6Gbl',
    userPoolWebClientId: '6gobbpage9af3nd7ahm3lchkct',
  }
});

// Get JWT token
async function getToken() {
  const session = await Auth.currentSession();
  return session.getIdToken().getJwtToken();
}

// List agents
async function listAgents() {
  const token = await getToken();
  const response = await fetch(
    'https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return response.json();
}

// Submit report
async function submitReport(domainId: string, text: string) {
  const token = await getToken();
  const response = await fetch(
    'https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ domain_id: domainId, text })
    }
  );
  return response.json();
}
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause:** Missing or invalid JWT token

**Solution:**
```bash
# Get new token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1
```

### Issue: 500 Internal Server Error

**Cause:** Lambda function error

**Solution:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler \
  --follow --region us-east-1
```

### Issue: CORS Error

**Cause:** Frontend origin not allowed

**Solution:** CORS is configured for all origins (`*`). Check browser console for specific error.

---

## API Changelog

### Version 1.0 (Current)
- Initial release
- Config API (agents, domains)
- Ingest API (report submission)
- Query API (question processing)
- Tools API (tool registry)
- Data API (data retrieval)

---

## Support

**Test Script:** `python3 TEST.py`  
**Deployment Script:** `./DEPLOY.sh`  
**Documentation:** This file

**Quick Commands:**
```bash
# Test all APIs
python3 TEST.py

# Get JWT token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1

# View logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler --follow
```

---

**Status:** ✅ All APIs Working (100% test pass rate)  
**Last Updated:** October 21, 2025
