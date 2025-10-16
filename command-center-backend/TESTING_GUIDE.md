# API Testing Guide

## Quick Test (Recommended)

Test all endpoints quickly:

```bash
npm run test:quick
```

or

```bash
bash scripts/quick-test.sh
```

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║              Quick API Test                                ║
╚════════════════════════════════════════════════════════════╝

API Endpoint: https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
API Key: tJw8W0scWI...

[1/3] Testing GET /data/updates
✓ Status: 200 OK
  Events returned: 300

[2/3] Testing POST /agent/query
✓ Status: 200 OK
  Response preview: {"chatResponse":"..."}

[3/3] Testing POST /agent/action
✓ Status: 200 OK
  Response preview: {"events":[...]}

════════════════════════════════════════════════════════════
✓ Quick test complete!
```

---

## Comprehensive Test Suite

Run full test suite with validation:

```bash
npm run test:api
```

or

```bash
bash scripts/test-api.sh
```

**Tests 12 scenarios:**
1. ✓ GET /data/updates - Valid request
2. ✓ GET /data/updates - With domain filter
3. ✓ GET /data/updates - Missing required parameter (400)
4. ✓ GET /data/updates - Invalid date format (400)
5. ✓ POST /agent/query - Valid request
6. ✓ POST /agent/query - Empty text (400)
7. ✓ POST /agent/query - Missing text field (400)
8. ✓ POST /agent/action - Valid action
9. ✓ POST /agent/action - Invalid action ID (400)
10. ✓ POST /agent/action - Missing actionId (400)
11. ✓ GET /data/updates - No API key (403)
12. ✓ GET /data/updates - Invalid API key (403)

**Output:**
```
╔════════════════════════════════════════════════════════════╗
║              Command Center API Test Suite                ║
╚════════════════════════════════════════════════════════════╝

API Endpoint: https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
Testing with API Key: tJw8W0scWI...

═══════════════════════════════════════════════════════════
                    Running Tests
═══════════════════════════════════════════════════════════

[Test 1] GET /data/updates - Valid request
  Method: GET
  Endpoint: data/updates?since=2023-02-06T00:00:00Z
  Status: 200
  ✓ PASSED
  ✓ Valid JSON response
  Response: {"events":[...],"count":300}

[Test 2] GET /data/updates - With domain filter
  Method: GET
  Endpoint: data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL
  Status: 200
  ✓ PASSED
  ✓ Valid JSON response
  Response: {"events":[...],"count":60}

...

═══════════════════════════════════════════════════════════
                    Test Summary
═══════════════════════════════════════════════════════════

Total Tests: 12
Passed: 12
Failed: 0

✓ All tests passed!
```

---

## Manual Testing

### Test Individual Endpoints

#### 1. GET /data/updates

```bash
source .env.local

# Basic request
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}" | jq

# With domain filter
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
  -H "x-api-key: ${API_KEY}" | jq

# With limit (if implemented)
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z&limit=10" \
  -H "x-api-key: ${API_KEY}" | jq
```

**Expected Response:**
```json
{
  "events": [
    {
      "eventId": "evt_001",
      "timestamp": "2023-02-06T08:15:23.456Z",
      "domain": "MEDICAL",
      "severity": "CRITICAL",
      "summary": "Building collapse - Kahramanmaraş",
      "geojson": "{\"type\":\"Point\",\"coordinates\":[37.014,37.226]}"
    }
  ],
  "count": 300,
  "lastUpdate": "2023-02-12T23:59:59.999Z"
}
```

#### 2. POST /agent/query

```bash
source .env.local

# Natural language query
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the most urgent needs?"}' | jq

# Specific query
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "Show me all medical incidents in Kahramanmaraş"}' | jq

# Map-focused query
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "Show critical incidents on the map"}' | jq
```

**Expected Response:**
```json
{
  "chatResponse": "There are 12 critical medical incidents in the affected area...",
  "mapAction": "REPLACE",
  "mapLayers": [
    {
      "type": "FeatureCollection",
      "features": [...]
    }
  ],
  "viewState": {
    "latitude": 37.226,
    "longitude": 37.014,
    "zoom": 10
  },
  "uiContext": {
    "suggestedActions": ["View medical facilities", "Check supply status"]
  }
}
```

#### 3. POST /agent/action

```bash
source .env.local

# Show critical incidents
curl -X POST "${API_ENDPOINT}agent/action" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"actionId": "SHOW_CRITICAL_INCIDENTS"}' | jq

# Show medical facilities
curl -X POST "${API_ENDPOINT}agent/action" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"actionId": "SHOW_MEDICAL_FACILITIES"}' | jq
```

**Expected Response:**
```json
{
  "events": [...],
  "mapLayers": [...],
  "viewState": {...}
}
```

---

## Testing After Code Changes

### Workflow

```bash
# 1. Make changes to Lambda handlers
vim lib/lambdas/updatesHandler.ts

# 2. Build
npm run build

# 3. Deploy
bash scripts/full-deploy.sh --skip-populate

# 4. Test
npm run test:quick

# 5. If issues, check logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow
```

---

## Debugging Failed Tests

### Check Lambda Logs

```bash
# View real-time logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler \
  --filter-pattern "ERROR"

# View recent logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --since 10m
```

### Check DynamoDB Data

```bash
# Count items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --select COUNT

# Sample items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --limit 5 | jq
```

### Test API Gateway Directly

```bash
# Test without API key (should fail with 403)
curl -X GET "https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/data/updates?since=2023-02-06T00:00:00Z"

# Test with wrong API key (should fail with 403)
curl -X GET "https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: wrong-key"
```

---

## Common Issues

### Issue: "Internal server error"

**Check:**
1. Lambda logs: `aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow`
2. DynamoDB permissions
3. Environment variables

### Issue: "Forbidden" (403)

**Causes:**
- Missing API key
- Wrong API key
- API key not in header

**Fix:**
```bash
# Ensure header is correct
-H "x-api-key: YOUR_KEY"
```

### Issue: Empty response

**Check:**
1. Database has data: `aws dynamodb scan --table-name TABLE_NAME --select COUNT`
2. Query parameters are correct
3. Lambda logs for errors

### Issue: "Bad Request" (400)

**Causes:**
- Missing required parameters
- Invalid parameter format
- Invalid JSON body

**Fix:**
- Check request format
- Validate JSON
- Check required fields

---

## Performance Testing

### Load Test with Apache Bench

```bash
source .env.local

# Test updates endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 \
  -H "x-api-key: ${API_KEY}" \
  "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z"
```

### Monitor Performance

```bash
# Watch CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=CommandCenterBackend-Dev-UpdatesHandler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

---

## Automated Testing in CI/CD

### GitHub Actions Example

```yaml
name: Test API

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Run API tests
        run: |
          cd command-center-backend
          npm run test:api
```

---

## Summary

### Quick Test
```bash
npm run test:quick
```
**Time:** 10-15 seconds  
**Tests:** 3 endpoints

### Full Test Suite
```bash
npm run test:api
```
**Time:** 30-60 seconds  
**Tests:** 12 scenarios

### Manual Testing
```bash
source .env.local
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}" | jq
```

### After Code Changes
```bash
npm run build
bash scripts/full-deploy.sh --skip-populate
npm run test:quick
```

**Your APIs are fully tested!** ✅
