# Command Center Backend - Testing Guide

This guide explains how to test the Command Center Backend to verify all requirements are met.

## Prerequisites

Before running tests, ensure:

1. **Project is built:**
   ```bash
   npm run build
   ```

2. **For E2E tests, stack must be deployed:**
   ```bash
   npm run deploy
   ```

3. **Database must be populated:**
   ```bash
   npm run generate-data
   npm run populate-db
   ```

4. **Environment variables set for E2E tests:**
   ```bash
   export API_ENDPOINT="https://xxx.execute-api.us-east-1.amazonaws.com/prod"
   export API_KEY="your-api-key-here"
   ```

## Test Suites

### 1. Unit Tests

Tests individual functions without external dependencies.

**Run:**
```bash
npm run test:unit
```

**What it tests:**
- Data transformation functions
- GeoJSON conversion
- Event validation
- Query helper functions
- Alert extraction
- Timestamp calculations

**Expected output:**
```
================================================================================
UNIT TESTS
================================================================================

✅ eventToGeoJSONFeature - converts EventItem to GeoJSON Feature
✅ eventToGeoJSONFeature - handles invalid GeoJSON gracefully
✅ eventsToMapLayers - groups events by domain and layer type
...

================================================================================
SUMMARY
================================================================================
Total: 15
Passed: 15 ✅
Failed: 0 ❌
Pass Rate: 100.0%
```

### 2. End-to-End Tests

Tests the complete system including API Gateway, Lambda, DynamoDB, and Bedrock Agent.

**Run:**
```bash
# Set environment variables first
export API_ENDPOINT="https://xxx.execute-api.us-east-1.amazonaws.com/prod"
export API_KEY="your-api-key-here"

# Run E2E tests
npm run test:e2e
```

**What it tests:**

#### Updates Endpoint Tests:
1. ✅ Basic query with `since` parameter
2. ✅ Query with domain filter (MEDICAL)
3. ✅ Invalid parameters (should return 400)
4. ✅ Future timestamp (should return empty)
5. ✅ GeoJSON structure validation

#### Agent Query Tests (if Bedrock Agent is deployed):
6. ✅ Simple natural language query
7. ✅ Complex query with filters
8. ✅ Invalid request handling
9. ✅ Query with map context

#### Agent Action Tests:
10. ✅ Execute pre-defined action (SHOW_CRITICAL_MEDICAL)
11. ✅ Invalid action ID handling
12. ✅ Multiple sequential actions

**Expected output:**
```
================================================================================
COMMAND CENTER BACKEND - END-TO-END TEST SUITE
================================================================================
API Endpoint: https://xxx.execute-api.us-east-1.amazonaws.com/prod
API Key: ***1234
Skip Agent Tests: false
================================================================================

Starting tests...

✅ PASS - GET /data/updates - Basic query (245ms)
✅ PASS - GET /data/updates - With domain filter (MEDICAL) (198ms)
✅ PASS - GET /data/updates - Invalid parameters (156ms)
...

================================================================================
TEST SUMMARY
================================================================================
Total Tests: 12
Passed: 12 ✅
Failed: 0 ❌
Pass Rate: 100.0%
```

### 3. Skip Agent Tests

If Bedrock Agent is not yet deployed, you can skip agent-related tests:

```bash
export SKIP_AGENT_TESTS=true
npm run test:e2e
```

This will only test the `/data/updates` endpoint.

## Manual Testing

### Test 1: Verify Database Has Data

```bash
# Get table name from CDK output
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name CommandCenterBackend \
  --query 'Stacks[0].Outputs[?OutputKey==`TableName`].OutputValue' \
  --output text)

# Scan table to verify data exists
aws dynamodb scan \
  --table-name $TABLE_NAME \
  --max-items 10 \
  --output json
```

**Expected:** Should return 10 items with proper structure (Day, Timestamp, eventId, domain, etc.)

### Test 2: Test Updates Endpoint Directly

```bash
# Get API endpoint and key
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name CommandCenterBackend \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text)

API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name CommandCenterBackend \
  --query 'Stacks[0].Outputs[?OutputKey==`APIKeyId`].OutputValue' \
  --output text)

# Get API key value
API_KEY=$(aws apigateway get-api-key \
  --api-key $API_KEY_ID \
  --include-value \
  --query 'value' \
  --output text)

# Test updates endpoint
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" | jq
```

**Expected response:**
```json
{
  "latestTimestamp": "2023-02-12T23:59:59Z",
  "mapUpdates": {
    "mapAction": "APPEND",
    "mapLayers": [
      {
        "layerId": "medical-alerts-layer",
        "layerName": "Medical Alerts",
        "geometryType": "Point",
        "style": {
          "icon": "MEDICAL_FACILITY",
          "color": "#DC2626",
          "size": 12
        },
        "data": {
          "type": "FeatureCollection",
          "features": [...]
        }
      }
    ]
  },
  "criticalAlerts": [
    {
      "alertId": "uuid",
      "timestamp": "2023-02-06T04:00:00Z",
      "severity": "CRITICAL",
      "title": "MEDICAL - CRITICAL",
      "summary": "Building collapse with casualties",
      "location": {
        "lat": 37.15,
        "lon": 37.12
      }
    }
  ]
}
```

### Test 3: Test Bedrock Agent in AWS Console

1. Go to AWS Bedrock console
2. Navigate to Agents
3. Find "CommandCenterBackend-Agent"
4. Click "Test" button
5. Enter query: "What are the critical incidents?"
6. Verify:
   - Agent invokes the `databaseQueryTool`
   - Tool returns event data
   - Agent synthesizes a natural language response

### Test 4: Test Query Endpoint

```bash
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Show me all critical medical incidents"
  }' | jq
```

**Expected response:**
```json
{
  "simulationTime": "Day 0, 04:00",
  "timestamp": "2024-10-15T10:30:00Z",
  "chatResponse": "There are 12 critical medical incidents...",
  "mapAction": "REPLACE",
  "mapLayers": [...],
  "viewState": {
    "center": { "lat": 37.15, "lon": 37.12 },
    "zoom": 10
  },
  "uiContext": {
    "suggestedActions": [
      {
        "label": "Show resource gaps",
        "actionId": "SHOW_RESOURCE_GAPS"
      }
    ]
  }
}
```

### Test 5: Test Action Endpoint

```bash
curl -X POST "${API_ENDPOINT}agent/action" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "actionId": "SHOW_CRITICAL_MEDICAL"
  }' | jq
```

**Expected:** Similar response to query endpoint with map layers showing critical medical incidents.

## Troubleshooting

### Issue: "Cannot find module 'aws-lambda'"

**Solution:**
```bash
npm install --save-dev @types/aws-lambda
npm run build
```

### Issue: "TABLE_NAME environment variable is not set"

**Cause:** Lambda function doesn't have the environment variable.

**Solution:** Redeploy the stack:
```bash
npm run deploy
```

### Issue: "No data returned from /data/updates"

**Cause:** Database is empty.

**Solution:** Populate the database:
```bash
npm run generate-data
npm run populate-db
```

### Issue: "Bedrock Agent not found"

**Cause:** Agent not deployed or IAM permissions missing.

**Solution:**
1. Check if agent exists:
   ```bash
   aws bedrock-agent list-agents
   ```

2. Verify IAM role has permissions:
   ```bash
   aws iam get-role --role-name CommandCenterBackend-BedrockAgentRole
   ```

3. Redeploy if needed:
   ```bash
   npm run deploy
   ```

### Issue: "AccessDeniedException when invoking agent"

**Cause:** Lambda role doesn't have permission to invoke Bedrock Agent.

**Solution:** Check IAM policy in `lib/command-center-backend-stack.ts` includes:
```typescript
actions: [
  'bedrock:InvokeAgent',
  'bedrock:InvokeModel',
]
```

### Issue: "Agent timeout"

**Cause:** Agent taking too long to respond (>55 seconds).

**Solution:**
1. Check agent configuration in Bedrock console
2. Verify tool Lambda is responding quickly
3. Consider simplifying the query
4. Check CloudWatch logs for the tool Lambda

## Performance Benchmarks

Expected performance metrics:

| Endpoint | P50 Latency | P95 Latency | P99 Latency |
|----------|-------------|-------------|-------------|
| GET /data/updates | <200ms | <500ms | <1000ms |
| POST /agent/query | <5s | <15s | <30s |
| POST /agent/action | <5s | <15s | <30s |

**Note:** Agent endpoints are slower due to LLM processing time.

## Continuous Integration

To integrate tests into CI/CD:

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '20'
      - run: npm install
      - run: npm run build
      - run: npm run test:unit
      
      # E2E tests only on main branch
      - name: E2E Tests
        if: github.ref == 'refs/heads/main'
        env:
          API_ENDPOINT: ${{ secrets.API_ENDPOINT }}
          API_KEY: ${{ secrets.API_KEY }}
        run: npm run test:e2e
```

## Test Coverage Goals

- **Unit Tests:** 80%+ code coverage
- **Integration Tests:** All API endpoints
- **E2E Tests:** All user workflows
- **Load Tests:** 100 concurrent users

## Next Steps

After all tests pass:

1. ✅ Run load tests to verify scalability
2. ✅ Set up monitoring and alerting
3. ✅ Document API for frontend team
4. ✅ Create deployment runbook
5. ✅ Schedule regular testing cadence

## Support

For issues or questions:
- Check CloudWatch Logs for Lambda functions
- Review API Gateway execution logs
- Test Bedrock Agent in AWS console
- Verify DynamoDB has data
- Check IAM permissions

---

**Last Updated:** 2024-10-15
