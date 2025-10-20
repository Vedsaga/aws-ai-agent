# Quick API Reference Card

**Base URL:** `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`

## 🔐 Get Token (Required)
```bash
export TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)
```

---

## 📋 CONFIG API

### List Agents
```bash
curl -X GET "$API_URL/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN"
```
**Returns:** List of all agents (built-in + custom)

### Create Agent
```bash
curl -X POST "$API_URL/api/v1/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "My Agent",
      "agent_type": "custom",
      "system_prompt": "Your prompt here",
      "tools": ["bedrock"],
      "output_schema": {"field": "string"}
    }
  }'
```
**Returns:** `agent_id` (save this!)

### Get Agent
```bash
curl -X GET "$API_URL/api/v1/config/agent/{agent_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Agent
```bash
curl -X PUT "$API_URL/api/v1/config/agent/{agent_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"config": {"system_prompt": "Updated"}}'
```

### Delete Agent
```bash
curl -X DELETE "$API_URL/api/v1/config/agent/{agent_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📥 INGEST API

### Submit Report
```bash
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "Pothole on Main Street near library"
  }'
```
**Returns:** `job_id`, status: `accepted` (202)

### Submit with Priority
```bash
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "Emergency: Gas leak on Elm Street",
    "priority": "high",
    "reporter_contact": "555-1234"
  }'
```

---

## 🔍 QUERY API

### Ask Question
```bash
curl -X POST "$API_URL/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints?"
  }'
```
**Returns:** `job_id`, status: `accepted` (202)

### Query with Filters
```bash
curl -X POST "$API_URL/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What complaints were reported?",
    "filters": {
      "date_range": {"start": "2025-01-01", "end": "2025-01-31"},
      "category": "infrastructure"
    }
  }'
```

### Complex Query
```bash
curl -X POST "$API_URL/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are top 5 categories in downtown last 30 days?",
    "include_visualizations": true
  }'
```

---

## 🛠️ TOOLS API

### List Tools
```bash
curl -X GET "$API_URL/api/v1/tools" \
  -H "Authorization: Bearer $TOKEN"
```
**Returns:** Available tools (bedrock, osm_api, etc.)

---

## 📊 DATA API

### Get Data
```bash
curl -X GET "$API_URL/api/v1/data?domain_id=civic_complaints&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
**Returns:** List of incidents/reports

---

## ✅ Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET/PUT/DELETE) |
| 201 | Created (POST) |
| 202 | Accepted (async job started) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (no/bad token) |
| 403 | Forbidden (can't delete built-in) |
| 404 | Not Found |
| 500 | Server Error |

---

## ⚠️ Validation Rules

### Agent Config
- `agent_name`: 3-100 chars, required
- `system_prompt`: max 2000 chars, required
- `output_schema`: max 5 keys, required

### Ingest
- `domain_id`: required
- `text`: 10-10000 chars, required
- `images`: max 5, optional
- `priority`: low/normal/high/urgent

### Query
- `domain_id`: required
- `question`: 5-1000 chars, required

---

## 🎯 Common Workflows

### 1. Submit & Query
```bash
# Submit
RESPONSE=$(curl -X POST "$API_URL/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain_id":"civic_complaints","text":"Broken light"}')
JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

# Query
curl -X POST "$API_URL/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"domain_id":"civic_complaints","question":"What was reported?"}'
```

### 2. Create Custom Agent & Domain
```bash
# Create agent
AGENT=$(curl -X POST "$API_URL/api/v1/config" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"type":"agent","config":{...}}')
AGENT_ID=$(echo $AGENT | jq -r '.agent_id')

# Create domain using agent
curl -X POST "$API_URL/api/v1/config" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "type":"domain_template",
    "config":{
      "domain_id":"my_domain",
      "ingest_agent_ids":["'$AGENT_ID'","geo_agent"]
    }
  }'
```

---

## 🧪 Test All APIs
```bash
# Quick test script
./test_all_endpoints.py

# Expected: 33/35 tests pass (94.3%)
```

---

## 📱 Frontend Integration

```javascript
// Get token from Cognito
const token = await getAuthToken();

// Submit report
const response = await fetch(`${API_URL}/api/v1/ingest`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    domain_id: 'civic_complaints',
    text: reportText
  })
});

const { job_id } = await response.json();
```

---

## 🐛 Debug Commands

```bash
# Check logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --follow --region us-east-1

# Test without auth (should get 401)
curl -X GET "$API_URL/api/v1/config?type=agent"

# Check DynamoDB
aws dynamodb scan \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --limit 5 --region us-east-1
```

---

## ✅ Status: READY FOR DEMO
- All core APIs working ✅
- Validation working ✅
- Error handling working ✅
- 94.3% test pass rate ✅