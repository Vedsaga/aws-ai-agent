# 🚨 URGENT API FIX PLAN - 4 HOURS REMAINING

**Created:** 2025-10-20  
**Time Critical:** < 4 hours to working APIs  
**Current Status:** 🔴 All APIs returning 500 errors, AWS CLI experiencing connectivity issues  
**Goal:** Get at least 3 core APIs working for demo

---

## 🎯 PRIORITY TARGETS

### Must Work (P0 - Critical for Demo):
1. **Config API - List Agents** - Show pre-built agents
2. **Config API - Create Agent** - Create custom agent
3. **Ingest API** - Submit a report (even if it just stores to DynamoDB)

### Nice to Have (P1):
4. **Query API** - Ask a question
5. **Data API - Retrieve** - Show stored reports

### Skip for Now (P2):
- Complex analytics
- Vector search
- Real-time subscriptions
- Tool registry (can demo with hardcoded list)

---

## 🔍 DIAGNOSIS CHECKLIST

### AWS Connectivity Issues (CURRENT PROBLEM)

**Symptoms:**
- `ServiceUnavailableException` when calling Lambda
- `Could not connect to the endpoint URL` for DynamoDB
- AWS CLI commands timing out

**Possible Causes:**
1. **AWS Region Outage** - Check: https://status.aws.amazon.com/
2. **Local Network Issues** - VPN, firewall, DNS problems
3. **AWS Credentials Expired** - Check: `aws sts get-caller-identity`
4. **Rate Limiting** - Too many API calls

**IMMEDIATE ACTIONS:**

```bash
# 1. Check AWS Status
curl -s https://status.aws.amazon.com/ | grep -i "us-east-1"

# 2. Verify credentials
aws sts get-caller-identity --region us-east-1

# 3. Check if it's a timeout issue - increase timeout
aws lambda list-functions --region us-east-1 --cli-read-timeout 60

# 4. Try different region as test
aws lambda list-functions --region us-west-2 --max-items 1

# 5. Check network connectivity
ping dynamodb.us-east-1.amazonaws.com
nslookup dynamodb.us-east-1.amazonaws.com

# 6. If VPN, try without VPN
# If no VPN, try with different DNS (8.8.8.8)
```

**WORKAROUND if AWS CLI is down:**
Use AWS Console in browser:
1. Open: https://console.aws.amazon.com/lambda
2. Manually check Lambda functions
3. View CloudWatch logs
4. Test functions manually

---

## 🛠️ FIX STRATEGY (Once AWS Access Restored)

### PHASE 1: Get Lambda Logs (15 minutes)

**Via AWS Console:**
1. Go to CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
2. Find log group: `/aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler`
3. Check latest log stream
4. Look for error messages

**Via CLI (if working):**
```bash
# Get latest error
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --since 1h \
  --region us-east-1 \
  --format short \
  | grep -i error -A 5 -B 5 > lambda_errors.txt

cat lambda_errors.txt
```

**Common Error Patterns & Fixes:**

| Error Message | Root Cause | Fix |
|--------------|------------|-----|
| `Unable to import module 'config_handler'` | Missing dependencies or wrong handler path | Check handler name in Lambda config |
| `Connection timeout` to RDS | VPC/Security Group issue | Use DynamoDB only for demo |
| `Table does not exist` | DynamoDB table name mismatch | Check environment variable |
| `Access Denied` | IAM permissions missing | Add DynamoDB/Secrets permissions to Lambda role |
| `Module not found: psycopg2` | Missing Lambda layer | Remove RDS code, use DynamoDB only |
| `KeyError: 'CONFIGURATIONS_TABLE'` | Missing env var | Add env var to Lambda |

---

### PHASE 2: Quick Fix - DynamoDB Only Mode (30 minutes)

**The config_handler.py is already set up for DynamoDB!** Just need to ensure:

1. **Check Lambda Environment Variable:**

```bash
# Via AWS Console:
# Lambda → Functions → MultiAgentOrchestration-dev-Api-ConfigApiHandler 
# → Configuration → Environment variables
# Should have: CONFIGURATIONS_TABLE = MultiAgentOrchestration-dev-Data-Configurations

# Via CLI:
aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --region us-east-1 \
  --query 'Environment.Variables'
```

**If missing, add it:**

```bash
aws lambda update-function-configuration \
  --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --environment "Variables={CONFIGURATIONS_TABLE=MultiAgentOrchestration-dev-Data-Configurations}" \
  --region us-east-1
```

2. **Verify DynamoDB Table Has Data:**

```bash
# Check table exists
aws dynamodb describe-table \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --region us-east-1

# Check data exists
aws dynamodb scan \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --limit 5 \
  --region us-east-1
```

**If no data, seed it:**

```bash
cd infrastructure/lambda/config-api

# Seed civic complaints domain
aws dynamodb put-item \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --item file://seed_civic_domain.json \
  --region us-east-1
```

3. **Check Lambda IAM Role Has DynamoDB Permissions:**

```bash
# Get Lambda role ARN
ROLE_ARN=$(aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --query 'Role' \
  --output text \
  --region us-east-1)

echo "Role: $ROLE_ARN"

# Check attached policies
aws iam list-attached-role-policies \
  --role-name $(echo $ROLE_ARN | cut -d'/' -f2) \
  --region us-east-1
```

**Should include DynamoDB access. If not:**

```bash
# Create inline policy
aws iam put-role-policy \
  --role-name $(echo $ROLE_ARN | cut -d'/' -f2) \
  --policy-name DynamoDBAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:847272187168:table/MultiAgentOrchestration-*"
    }]
  }'
```

---

### PHASE 3: Test Config API (15 minutes)

**Get JWT Token:**

```bash
# Via CLI
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo "Token: $TOKEN"
```

**Via AWS Console if CLI fails:**
1. Go to Cognito User Pools
2. Use "Test your user pool API" feature
3. Or use this online JWT generator with user pool details

**Test Endpoints:**

```bash
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# 1. List agents (should return built-in agents)
curl -X GET "$API_URL/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -v

# Expected: 200 OK with list of agents

# 2. Create custom agent
curl -X POST "$API_URL/api/v1/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Test Agent",
      "agent_type": "custom",
      "system_prompt": "You are a test agent",
      "tools": ["bedrock"],
      "output_schema": {
        "result": "string",
        "confidence": "number"
      }
    }
  }' \
  -v

# Expected: 201 Created with agent details

# 3. List domains
curl -X GET "$API_URL/api/v1/config?type=domain_template" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -v

# Expected: 200 OK with civic_complaints domain
```

---

### PHASE 4: Fix Ingest API (30 minutes)

**Ingest API needs to:**
1. Accept text input
2. Store to DynamoDB (simplest for demo)
3. Return job_id and status

**Simplified Ingest Handler:**

```python
# infrastructure/lambda/orchestration/ingest_handler_simple.py
import json
import uuid
from datetime import datetime
import boto3

dynamodb = boto3.resource("dynamodb")
incidents_table = dynamodb.Table("MultiAgentOrchestration-dev-Data-Incidents")

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        domain_id = body.get("domain_id")
        text = body.get("text")
        
        if not domain_id or not text:
            return error_response(400, "Missing domain_id or text")
        
        # Create incident record
        incident_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        incident = {
            "id": incident_id,
            "tenant_id": "default-tenant",
            "domain_id": domain_id,
            "raw_text": text,
            "job_id": job_id,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save to DynamoDB
        incidents_table.put_item(Item=incident)
        
        return {
            "statusCode": 202,
            "headers": cors_headers(),
            "body": json.dumps({
                "job_id": job_id,
                "status": "processing",
                "message": "Report submitted successfully"
            })
        }
    except Exception as e:
        return error_response(500, str(e))

def error_response(code, message):
    return {
        "statusCode": code,
        "headers": cors_headers(),
        "body": json.dumps({"error": message})
    }

def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }
```

**Deploy Updated Lambda:**

```bash
cd infrastructure/lambda/orchestration

# Package
zip deployment.zip ingest_handler_simple.py

# Deploy
aws lambda update-function-code \
  --function-name MultiAgentOrchestration-dev-Api-IngestHandler \
  --zip-file fileb://deployment.zip \
  --region us-east-1

# Wait for update
aws lambda wait function-updated \
  --function-name MultiAgentOrchestration-dev-Api-IngestHandler \
  --region us-east-1
```

**Test:**

```bash
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "There is a broken streetlight on Oak Avenue"
  }' \
  -v

# Expected: 202 Accepted with job_id
```

---

### PHASE 5: Fix Query API (30 minutes)

**Simplified Query Handler:**

```python
# infrastructure/lambda/orchestration/query_handler_simple.py
import json
import uuid
from datetime import datetime

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        domain_id = body.get("domain_id")
        question = body.get("question")
        
        if not domain_id or not question:
            return error_response(400, "Missing domain_id or question")
        
        job_id = str(uuid.uuid4())
        
        # For demo: return mock analysis
        mock_answer = {
            "job_id": job_id,
            "status": "completed",
            "question": question,
            "domain_id": domain_id,
            "agent_results": {
                "what_agent": {
                    "answer": "The most common complaints are infrastructure issues (45%) and public safety concerns (30%).",
                    "confidence": 0.85
                },
                "when_agent": {
                    "answer": "Peak complaint times are Monday mornings and Friday afternoons.",
                    "confidence": 0.78
                }
            },
            "summary": "Analysis shows infrastructure and public safety are primary concerns with clear temporal patterns.",
            "confidence_score": 0.82
        }
        
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(mock_answer)
        }
    except Exception as e:
        return error_response(500, str(e))
```

---

## 📝 TESTING CHECKLIST

### Manual Testing (Use Postman or curl)

- [ ] **Config API - List Agents**
  - GET `/api/v1/config?type=agent`
  - Expected: 200, list of built-in agents
  
- [ ] **Config API - Create Agent**
  - POST `/api/v1/config` with agent data
  - Expected: 201, agent created with ID
  
- [ ] **Config API - Get Agent**
  - GET `/api/v1/config/agent/{agent_id}`
  - Expected: 200, agent details

- [ ] **Ingest API - Submit Report**
  - POST `/api/v1/ingest` with text
  - Expected: 202, job_id returned

- [ ] **Query API - Ask Question**
  - POST `/api/v1/query` with question
  - Expected: 202 or 200, answer returned

### Automated Testing

```bash
# Run test suite
cd ~/hackathon/aws-ai-agent
python3 test_api.py

# Should see pass rate > 80%
```

---

## 🚨 IF STILL BROKEN - EMERGENCY BACKUP PLAN

### Option 1: Mock API Gateway (30 minutes)

Create static responses in API Gateway:

1. Go to API Gateway console
2. For each route, add Mock integration
3. Configure response templates
4. Deploy API
5. At least shows proper response format

### Option 2: Local Flask API (45 minutes)

Create local Python Flask API that works:

```python
# local_api.py
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/v1/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        return jsonify({
            "configs": [
                {"agent_id": "geo_agent", "agent_name": "Geo Agent"},
                {"agent_id": "temporal_agent", "agent_name": "Temporal Agent"}
            ],
            "count": 2
        })
    return jsonify({"agent_id": "new_agent"}), 201

@app.route('/api/v1/ingest', methods=['POST'])
def ingest():
    return jsonify({"job_id": "demo-123", "status": "processing"}), 202

if __name__ == '__main__':
    app.run(port=8000)
```

Run: `python3 local_api.py`

### Option 3: Use Existing Infrastructure, Show Architecture (1 hour)

If APIs can't be fixed in time:
1. Screenshot AWS Console showing deployed resources
2. Show CloudWatch logs (even if errors)
3. Walk through code and explain architecture
4. Use Postman with mock responses
5. Focus on design quality and documentation

---

## 🎬 DEMO STRATEGY

### Scenario 1: APIs Working (Best Case)

**3-Minute Demo Flow:**
1. (30s) Show architecture diagram, explain orchestration
2. (1m) Live demo: Create agent, show configuration
3. (1m) Live demo: Submit report, show it gets processed
4. (30s) Show query results or data retrieval

### Scenario 2: APIs Partially Working (Realistic)

**3-Minute Demo Flow:**
1. (30s) Architecture and design overview
2. (1m) Show working Config API (agents list)
3. (45s) Use Postman to show API contract
4. (45s) Show code quality and infrastructure

### Scenario 3: APIs Not Working (Backup)

**3-Minute Demo Flow:**
1. (45s) Architecture walkthrough
2. (1m) AWS Console tour (Lambda, DynamoDB, API Gateway deployed)
3. (45s) Code walkthrough showing implementation
4. (30s) Documentation and design quality

---

## 📊 SUCCESS METRICS

### Minimum for Submission:
- [ ] 1 API endpoint returns 200 (not 500)
- [ ] Can demonstrate request/response flow
- [ ] Architecture documented
- [ ] Demo video recorded

### Good Submission:
- [ ] 3+ API endpoints working
- [ ] Can create agent and show in list
- [ ] Can submit report and get job_id
- [ ] Live demo with real requests

### Excellent Submission:
- [ ] All core APIs working
- [ ] End-to-end flow: Create domain → Submit report → Query results
- [ ] Real agent orchestration
- [ ] Polished demo

---

## ⏱️ TIME ALLOCATION (4 Hours)

| Time | Task | Output |
|------|------|--------|
| **Hour 1** | Diagnose AWS issues, get logs | Root cause identified |
| **Hour 2** | Fix Config API, deploy, test | 1 API working |
| **Hour 3** | Fix Ingest API, test both | 2 APIs working |
| **Hour 3.5** | Record demo video | Video uploaded |
| **Hour 4** | Submit to DevPost | Submitted! |

---

## 🆘 ESCALATION PATHS

### If AWS CLI Won't Work:
→ Use AWS Console exclusively
→ Manual testing via console

### If Lambda Won't Deploy:
→ Use API Gateway mock responses
→ Show architecture and code

### If Nothing Works:
→ Local Flask API for demo
→ Focus on documentation quality
→ Honest presentation of design

---

## 📞 QUICK COMMANDS REFERENCE

```bash
# Get Token
TOKEN=$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id 6gobbpage9af3nd7ahm3lchkct --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! --region us-east-1 --query 'AuthenticationResult.IdToken' --output text)

# Test Config API
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent" -H "Authorization: Bearer $TOKEN"

# Check Lambda Logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler --follow --region us-east-1

# Update Lambda
cd infrastructure/lambda/config-api && zip deployment.zip config_handler.py && aws lambda update-function-code --function-name MultiAgentOrchestration-dev-Api-ConfigApiHandler --zip-file fileb://deployment.zip --region us-east-1

# Check DynamoDB
aws dynamodb scan --table-name MultiAgentOrchestration-dev-Data-Configurations --limit 5 --region us-east-1
```

---

## 🎯 FINAL CHECKLIST BEFORE DEMO

- [ ] At least 1 API returns 200 (not 500)
- [ ] Can get JWT token from Cognito
- [ ] Have screenshots of working requests
- [ ] Demo script prepared (DEMO_SCRIPT.md)
- [ ] Video recording software ready (OBS/Loom)
- [ ] GitHub repo is public
- [ ] README has clear setup instructions
- [ ] Architecture diagram included

---

## 💡 REMEMBER

- **Done > Perfect** - Working demo of 1 feature beats broken demo of 10 features
- **Honesty Wins** - Judges respect transparency about issues
- **Architecture Matters** - Well-designed system with issues > poorly designed working system
- **Documentation Counts** - Your docs show thinking quality

**YOU HAVE THE INFRASTRUCTURE. YOU HAVE THE CODE. NOW FIX THE CONNECTION!**

**START NOW! Check AWS status, then dive into CloudWatch logs!**