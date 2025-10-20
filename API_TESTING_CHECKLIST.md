# API Testing Checklist - Quick Reference

**Time Critical:** Use this for rapid manual testing when automated tests fail

---

## 🚀 Quick Start (5 Minutes)

### 1. Get JWT Token

```bash
# Get authentication token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Verify token
echo "Token obtained: ${#TOKEN} characters"
```

### 2. Test Config API (CRITICAL)

```bash
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# List agents
curl -X GET "$API_URL/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq

# Expected: 200 OK with list of agents
```

### 3. Test Ingest API (CRITICAL)

```bash
# Submit report
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "Test report: Broken streetlight on Main St"
  }' | jq

# Expected: 202 Accepted with job_id
```

### 4. Test Query API (CRITICAL)

```bash
# Ask question
curl -X POST "$API_URL/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints?"
  }' | jq

# Expected: 202 Accepted with job_id
```

---

## ✅ Detailed Testing Checklist

### Authentication Tests

- [ ] **No Auth Header**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=agent"
  # Expected: 401 Unauthorized
  ```

- [ ] **Invalid Token**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=agent" \
    -H "Authorization: Bearer invalid_token"
  # Expected: 401 Unauthorized
  ```

- [ ] **Valid Token**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=agent" \
    -H "Authorization: Bearer $TOKEN"
  # Expected: 200 OK
  ```

---

### Config API Tests

#### List Configurations

- [ ] **List Agents**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=agent" \
    -H "Authorization: Bearer $TOKEN" | jq
  ```
  **Expected Response:**
  ```json
  {
    "configs": [
      {
        "agent_id": "geo_agent",
        "agent_name": "Geo Agent",
        "is_builtin": true,
        "output_schema": {...}
      }
    ],
    "count": 11
  }
  ```

- [ ] **List Domain Templates**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=domain_template" \
    -H "Authorization: Bearer $TOKEN" | jq
  ```
  **Expected:** 200 OK with civic_complaints domain

- [ ] **List Playbooks**
  ```bash
  curl -X GET "$API_URL/api/v1/config?type=playbook" \
    -H "Authorization: Bearer $TOKEN" | jq
  ```
  **Expected:** 200 OK with ingest/query playbooks

#### Create Configuration

- [ ] **Create Custom Agent**
  ```bash
  curl -X POST "$API_URL/api/v1/config" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "agent",
      "config": {
        "agent_name": "My Custom Agent",
        "agent_type": "custom",
        "system_prompt": "You are a helpful assistant",
        "tools": ["bedrock"],
        "output_schema": {
          "result": "string",
          "confidence": "number"
        }
      }
    }' | jq
  ```
  **Expected Response:**
  ```json
  {
    "tenant_id": "default-tenant",
    "config_key": "agent_my_custom_agent_abc123",
    "agent_id": "agent_my_custom_agent_abc123",
    "agent_name": "My Custom Agent",
    "created_at": "2025-01-20T12:00:00",
    "version": 1
  }
  ```
  **Status Code:** 201 Created

- [ ] **Create Domain Template**
  ```bash
  curl -X POST "$API_URL/api/v1/config" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "domain_template",
      "config": {
        "template_name": "Test Domain",
        "domain_id": "test_domain",
        "description": "Test domain for demo",
        "ingest_agent_ids": ["geo_agent", "temporal_agent"],
        "query_agent_ids": ["what_agent", "where_agent"]
      }
    }' | jq
  ```
  **Expected:** 201 Created

#### Get Configuration

- [ ] **Get Specific Agent**
  ```bash
  # Replace {agent_id} with actual ID from create response
  curl -X GET "$API_URL/api/v1/config/agent/{agent_id}" \
    -H "Authorization: Bearer $TOKEN" | jq
  ```
  **Expected:** 200 OK with agent details

#### Update Configuration

- [ ] **Update Agent**
  ```bash
  curl -X PUT "$API_URL/api/v1/config/agent/{agent_id}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "config": {
        "agent_name": "Updated Agent Name",
        "system_prompt": "Updated prompt"
      }
    }' | jq
  ```
  **Expected:** 200 OK with updated agent

#### Delete Configuration

- [ ] **Delete Agent**
  ```bash
  curl -X DELETE "$API_URL/api/v1/config/agent/{agent_id}" \
    -H "Authorization: Bearer $TOKEN" | jq
  ```
  **Expected:** 200 OK with deletion message

---

### Ingest API Tests

- [ ] **Submit Text Report**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "text": "Pothole on Oak Street causing traffic issues"
    }' | jq
  ```
  **Expected Response:**
  ```json
  {
    "job_id": "job_abc123",
    "status": "accepted",
    "message": "Report submitted for processing",
    "timestamp": "2025-01-20T12:00:00",
    "estimated_completion_seconds": 30
  }
  ```
  **Status Code:** 202 Accepted

- [ ] **Submit Report with Priority**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "text": "Emergency: Gas leak reported",
      "priority": "high"
    }' | jq
  ```
  **Expected:** 202 Accepted

- [ ] **Submit Report with Contact**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "text": "Street sign fallen down",
      "reporter_contact": "test@example.com"
    }' | jq
  ```
  **Expected:** 202 Accepted

#### Error Cases

- [ ] **Missing Domain ID**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "text": "Test report"
    }' | jq
  ```
  **Expected:** 400 Bad Request

- [ ] **Missing Text**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints"
    }' | jq
  ```
  **Expected:** 400 Bad Request

- [ ] **Text Too Long**
  ```bash
  curl -X POST "$API_URL/api/v1/ingest" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"domain_id\": \"civic_complaints\",
      \"text\": \"$(python3 -c 'print("A" * 10001)')\"
    }" | jq
  ```
  **Expected:** 400 Bad Request

---

### Query API Tests

- [ ] **Ask Simple Question**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "question": "What complaints were reported today?"
    }' | jq
  ```
  **Expected Response:**
  ```json
  {
    "job_id": "query_abc123",
    "status": "accepted",
    "message": "Question submitted for processing",
    "timestamp": "2025-01-20T12:00:00",
    "estimated_completion_seconds": 10
  }
  ```
  **Status Code:** 202 Accepted

- [ ] **Ask Complex Question**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "question": "What are the top 5 complaint categories in downtown during the last 30 days?"
    }' | jq
  ```
  **Expected:** 202 Accepted

- [ ] **Query with Filters**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints",
      "question": "How many infrastructure complaints?",
      "filters": {
        "date_range": {
          "start": "2025-01-01",
          "end": "2025-01-31"
        },
        "category": "infrastructure"
      }
    }' | jq
  ```
  **Expected:** 202 Accepted

#### Error Cases

- [ ] **Missing Domain ID**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "question": "Test question"
    }' | jq
  ```
  **Expected:** 400 Bad Request

- [ ] **Missing Question**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "domain_id": "civic_complaints"
    }' | jq
  ```
  **Expected:** 400 Bad Request

- [ ] **Question Too Long**
  ```bash
  curl -X POST "$API_URL/api/v1/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"domain_id\": \"civic_complaints\",
      \"question\": \"$(python3 -c 'print("A" * 1001)')\"
    }" | jq
  ```
  **Expected:** 400 Bad Request

---

## 🔍 Debugging Commands

### Check CloudWatch Logs

```bash
# Config API logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --follow --region us-east-1

# Ingest API logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-IngestHandler \
  --follow --region us-east-1

# Query API logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-QueryHandler \
  --follow --region us-east-1
```

### Check DynamoDB Data

```bash
# List configurations
aws dynamodb scan \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --limit 10 \
  --region us-east-1

# Check specific agent
aws dynamodb get-item \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --key '{"tenant_id":{"S":"default-tenant"},"config_key":{"S":"geo_agent"}}' \
  --region us-east-1
```

### Check Lambda Configuration

```bash
# Get environment variables
aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --query 'Environment.Variables' \
  --region us-east-1

# Get IAM role
aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --query 'Role' \
  --region us-east-1
```

---

## 📊 Success Criteria

### Minimum Viable (MVP)
- [ ] Can get JWT token
- [ ] Config API returns 200 (not 500)
- [ ] Can list at least built-in agents
- [ ] Can create a custom agent

### Good Demo
- [ ] All Config API endpoints work
- [ ] Ingest API accepts reports
- [ ] Query API accepts questions
- [ ] Error handling returns proper 400/404

### Excellent Demo
- [ ] All APIs working
- [ ] Can create domain
- [ ] Can submit report
- [ ] Can query data
- [ ] End-to-end flow works

---

## 🆘 Quick Fixes

### If Getting 500 Errors

1. **Check Lambda has DynamoDB access:**
   ```bash
   ROLE=$(aws lambda get-function-configuration \
     --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
     --query 'Role' --output text --region us-east-1)
   
   aws iam list-attached-role-policies \
     --role-name $(basename $ROLE) \
     --region us-east-1
   ```

2. **Check environment variables:**
   ```bash
   aws lambda get-function-configuration \
     --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
     --region us-east-1
   ```

3. **Check CloudWatch logs for specific error**

### If Getting 401 Errors

1. **Verify token is still valid:**
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq
   ```

2. **Get fresh token:**
   ```bash
   TOKEN=$(aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id 6gobbpage9af3nd7ahm3lchkct \
     --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
     --region us-east-1 \
     --query 'AuthenticationResult.IdToken' \
     --output text)
   ```

### If No Built-in Agents

1. **Seed DynamoDB with sample data:**
   ```bash
   cd infrastructure/lambda/config-api
   
   # Create seed script or manually add via console
   aws dynamodb put-item \
     --table-name MultiAgentOrchestration-dev-Data-Configurations \
     --item file://seed_civic_domain.json \
     --region us-east-1
   ```

---

## 📝 Test Results Template

```
API Test Results - [Date/Time]
================================

Authentication:
[ ] Token generation: ___
[ ] Auth rejection (401): ___

Config API:
[ ] List agents: ___
[ ] Create agent: ___
[ ] Get agent: ___
[ ] Update agent: ___
[ ] Delete agent: ___

Ingest API:
[ ] Submit report: ___
[ ] Error handling: ___

Query API:
[ ] Ask question: ___
[ ] Error handling: ___

Overall Status: ___/15 tests passing
Pass Rate: ___%

Ready for Demo: YES / NO / PARTIAL
```

---

## 🎯 Priority Order

1. **CRITICAL (Must Work):**
   - Get JWT token
   - Config API - List agents (show built-ins)
   - Config API - Create agent

2. **HIGH (Should Work):**
   - Ingest API - Submit report
   - Query API - Ask question

3. **MEDIUM (Nice to Have):**
   - Config API - Update/Delete
   - Error handling (400, 404)

4. **LOW (Skip if needed):**
   - Complex queries
   - Advanced features

**Focus on getting CRITICAL items working first!**