# API Changes and Testing Guide

## Making API Changes

### Is it seamless? YES! ✅

CDK makes API changes seamless. Here's how:

---

## Scenario 1: Add New API Endpoint

### Example: Add `/data/stats` endpoint

**Step 1: Create Lambda Handler**

```typescript
// lib/lambdas/statsHandler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({
      totalEvents: 1000,
      criticalEvents: 50,
      domains: ['MEDICAL', 'FIRE', 'STRUCTURAL']
    }),
  };
};
```

**Step 2: Add Lambda Function to Stack**

```typescript
// In lib/command-center-backend-stack.ts

private createStatsHandlerLambda(config: EnvironmentConfig): lambda.Function {
  const logGroup = new logs.LogGroup(this, 'StatsHandlerLogGroup', {
    logGroupName: `/aws/lambda/${config.stackName}-StatsHandler`,
    retention: logs.RetentionDays.TWO_WEEKS,
    removalPolicy: cdk.RemovalPolicy.DESTROY,
  });

  const statsLambda = new lambda.Function(this, 'StatsHandlerLambda', {
    functionName: `${config.stackName}-StatsHandler`,
    runtime: lambda.Runtime.NODEJS_20_X,
    handler: 'lib/lambdas/statsHandler.handler',
    code: lambda.Code.fromAsset('dist'),
    role: this.updatesLambdaRole, // Reuse existing role
    environment: {
      TABLE_NAME: this.table.tableName,
      LOG_LEVEL: config.stage === 'prod' ? 'INFO' : 'DEBUG',
    },
    timeout: cdk.Duration.seconds(30),
    memorySize: 512,
    description: 'Handles GET /data/stats endpoint',
    logGroup: logGroup,
  });

  return statsLambda;
}
```

**Step 3: Add API Route**

```typescript
// In configureAPIRoutes method

const statsResource = dataResource.addResource('stats');
const statsIntegration = new apigateway.LambdaIntegration(this.statsHandlerLambda!, {
  proxy: true,
  allowTestInvoke: true,
});

statsResource.addMethod('GET', statsIntegration, {
  apiKeyRequired: true,
  methodResponses: [
    {
      statusCode: '200',
      responseParameters: {
        'method.response.header.Access-Control-Allow-Origin': true,
      },
    },
  ],
});
```

**Step 4: Deploy**

```bash
npm run build
bash scripts/full-deploy.sh --skip-populate
```

**Time:** 1-2 minutes (only updates API Gateway and adds Lambda)

**Result:**
- ✅ New endpoint: `GET /data/stats`
- ✅ Old endpoints still work
- ✅ No downtime

---

## Scenario 2: Change Request/Response Format

### Example: Add `limit` parameter to `/data/updates`

**Step 1: Update Lambda Handler**

```typescript
// lib/lambdas/updatesHandler.ts

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const since = event.queryStringParameters?.since;
  const domain = event.queryStringParameters?.domain;
  const limit = parseInt(event.queryStringParameters?.limit || '100'); // NEW
  
  // Query DynamoDB with limit
  const params = {
    TableName: process.env.TABLE_NAME!,
    Limit: limit, // NEW
    // ... rest of query
  };
  
  // ... rest of handler
};
```

**Step 2: Update API Gateway (Optional)**

```typescript
// In configureAPIRoutes method

updatesResource.addMethod('GET', updatesIntegration, {
  apiKeyRequired: true,
  requestParameters: {
    'method.request.querystring.since': true,
    'method.request.querystring.domain': false,
    'method.request.querystring.limit': false, // NEW
  },
  // ... rest of config
});
```

**Step 3: Deploy**

```bash
npm run build
bash scripts/full-deploy.sh --skip-populate
```

**Time:** 1-2 minutes

**Result:**
- ✅ New parameter works: `?limit=50`
- ✅ Old requests still work (default limit=100)
- ✅ Backward compatible

---

## Scenario 3: Change Response Structure

### Example: Add metadata to response

**Before:**
```json
{
  "events": [...]
}
```

**After:**
```json
{
  "events": [...],
  "metadata": {
    "count": 10,
    "timestamp": "2023-02-06T08:15:00Z"
  }
}
```

**Step 1: Update Lambda**

```typescript
return {
  statusCode: 200,
  body: JSON.stringify({
    events: events,
    metadata: {  // NEW
      count: events.length,
      timestamp: new Date().toISOString(),
    },
  }),
};
```

**Step 2: Deploy**

```bash
npm run build
bash scripts/full-deploy.sh --skip-populate
```

**Result:**
- ✅ New response format
- ✅ Old clients can ignore new fields
- ✅ Backward compatible (if clients don't expect exact structure)

---

## Will Old API Be Overridden?

### YES - And that's OK! ✅

**How it works:**
1. CDK updates the Lambda function code
2. API Gateway routes remain the same
3. New code is deployed
4. Old behavior is replaced

**Deployment process:**
- ✅ Zero downtime (Lambda updates are atomic)
- ✅ Instant switchover
- ✅ No manual intervention

**If you need versioning:**
- Use different routes: `/v1/data/updates`, `/v2/data/updates`
- Or use Lambda versions/aliases

---

## Testing APIs

### Fix Your Current Error

**Issue:** Double slash in URL

```bash
# WRONG (double slash)
curl -X GET "https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev//data/updates?since=2023-02-06T00:00:00Z"

# CORRECT (single slash)
curl -X GET "https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/data/updates?since=2023-02-06T00:00:00Z"
```

### Test Commands

#### 1. Test Updates Endpoint

```bash
# Load credentials
source .env.local

# Test with correct URL
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}" | jq

# With domain filter
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
  -H "x-api-key: ${API_KEY}" | jq
```

#### 2. Test Query Endpoint

```bash
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the most urgent needs?"}' | jq
```

#### 3. Test Action Endpoint

```bash
curl -X POST "${API_ENDPOINT}agent/action" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"actionId": "SHOW_CRITICAL_INCIDENTS"}' | jq
```

### Check Lambda Logs

```bash
# View recent logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler \
  --filter-pattern "ERROR"
```

### Test DynamoDB Directly

```bash
# Count items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --select COUNT

# Get sample items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --limit 5 | jq

# Query specific day
aws dynamodb query \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --key-condition-expression "Day = :day" \
  --expression-attribute-values '{":day":{"S":"DAY_0"}}' \
  --limit 10 | jq
```

---

## Deployment Workflow for API Changes

### Quick Changes (Code Only)

```bash
# 1. Make changes to Lambda handlers
# 2. Build
npm run build

# 3. Deploy (skips database population)
bash scripts/full-deploy.sh --skip-populate

# 4. Test
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
```

**Time:** 1-2 minutes

### Infrastructure Changes (New Routes)

```bash
# 1. Add Lambda function to stack
# 2. Add API Gateway route
# 3. Build
npm run build

# 4. Deploy
bash scripts/full-deploy.sh --skip-populate

# 5. Test new endpoint
curl -X GET "${API_ENDPOINT}data/new-endpoint" \
  -H "x-api-key: ${API_KEY}"
```

**Time:** 2-3 minutes

---

## Common API Patterns

### 1. Add Query Parameter

```typescript
// Lambda handler
const newParam = event.queryStringParameters?.newParam || 'default';
```

**Deploy:** Code change only (1-2 min)

### 2. Add Request Body Field

```typescript
// Lambda handler
const body = JSON.parse(event.body || '{}');
const newField = body.newField || 'default';
```

**Deploy:** Code change only (1-2 min)

### 3. Add Response Field

```typescript
// Lambda handler
return {
  statusCode: 200,
  body: JSON.stringify({
    existingField: data,
    newField: additionalData, // NEW
  }),
};
```

**Deploy:** Code change only (1-2 min)

### 4. Add New Endpoint

```typescript
// 1. Create Lambda handler
// 2. Add to stack
// 3. Add API Gateway route
```

**Deploy:** Infrastructure change (2-3 min)

---

## Troubleshooting API Issues

### Issue: "Internal server error"

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow
```

**Common causes:**
- Missing environment variables
- DynamoDB permissions
- Code errors

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

### Issue: "Not Found" (404)

**Causes:**
- Wrong URL
- Endpoint doesn't exist
- Double slash in URL

**Fix:**
```bash
# Check URL format
${API_ENDPOINT}data/updates  # Correct
${API_ENDPOINT}/data/updates # Wrong (double slash)
```

### Issue: Empty Response

**Check:**
1. Database has data: `aws dynamodb scan --table-name TABLE_NAME --select COUNT`
2. Query parameters are correct
3. Lambda logs for errors

---

## Best Practices

### 1. Backward Compatibility

✅ **DO:**
- Add optional parameters
- Add new response fields
- Keep existing fields

❌ **DON'T:**
- Remove required parameters
- Change field types
- Remove response fields

### 2. Versioning

If breaking changes needed:

```typescript
// Option 1: Version in path
/v1/data/updates
/v2/data/updates

// Option 2: Version in header
X-API-Version: 2
```

### 3. Testing

Always test after deployment:

```bash
# 1. Deploy
bash scripts/full-deploy.sh --skip-populate

# 2. Test all endpoints
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" -H "x-api-key: ${API_KEY}"
curl -X POST "${API_ENDPOINT}agent/query" -H "x-api-key: ${API_KEY}" -d '{"text":"test"}'
curl -X POST "${API_ENDPOINT}agent/action" -H "x-api-key: ${API_KEY}" -d '{"actionId":"TEST"}'

# 3. Check logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --since 5m
```

---

## Summary

### API Changes Are Seamless ✅

| Change Type | Time | Downtime | Old API |
|-------------|------|----------|---------|
| Code only | 1-2 min | None | Overridden |
| New endpoint | 2-3 min | None | Unchanged |
| New parameter | 1-2 min | None | Overridden |
| Response format | 1-2 min | None | Overridden |

### Deployment Process

```bash
# 1. Make changes
# 2. Build
npm run build

# 3. Deploy
bash scripts/full-deploy.sh --skip-populate

# 4. Test
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
```

### Testing

```bash
# Fix your URL (remove double slash)
curl -X GET "https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: tJw8W0scWIaX5vvGBJzTa6zWA2uamUBI4ytmt6xO"

# Check logs if errors
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow
```

**Your API changes are seamless and fast!** 🚀
