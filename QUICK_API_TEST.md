# Quick API Testing Guide

## Get JWT Token
```bash
COGNITO_USERNAME=testuser COGNITO_PASSWORD=TestPassword123! ./get_jwt_token.sh
```

## Export Token
```bash
export JWT_TOKEN='<your_token_here>'
```

## Test All APIs
```bash
source venv/bin/activate
python test_all_apis.py
```

## Manual API Tests

### 1. List Agents
```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent"
```

### 2. Submit Incident Report
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","text":"Pothole on Main Street"}' \
  "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest"
```

### 3. Ask Question
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","question":"What are the most common complaints?"}' \
  "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/query"
```

### 4. List Tools
```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/tools"
```

### 5. Retrieve Data
```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/data?type=retrieval"
```

## Expected Results

All APIs should return:
- Config API: 200 OK with agent/domain list
- Ingest API: 202 Accepted with job_id
- Query API: 202 Accepted with job_id
- Tools API: 200 OK with tools list
- Data API: 200 OK with data array

## Deployment Status

✅ All Lambda functions deployed today (Oct 20, 2025)
✅ Correct handlers configured
✅ All tests passing (6/6)
