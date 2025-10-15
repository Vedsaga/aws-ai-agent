# Task 9 Implementation: Set up API Gateway

## Overview
Successfully implemented a complete API Gateway configuration with REST API endpoints, Lambda integrations, CORS support, and API key authentication.

## Implementation Details

### 9.1 Create REST API in CDK ✅

**What was implemented:**
- Defined API Gateway REST API resource with comprehensive configuration
- Configured API name and description for the Command Center Backend
- Set up deployment options with proper logging, tracing, and metrics
- Configured throttling limits (50 requests/sec rate, 100 burst)
- Set up regional endpoint configuration
- Enabled CloudWatch role for API Gateway logging

**Key Configuration:**
```typescript
const api = new apigateway.RestApi(this, 'CommandCenterAPI', {
  restApiName: `${config.stackName}-API`,
  description: `Command Center Backend API for disaster response - ${config.stage} environment`,
  deployOptions: {
    stageName: config.stage,
    loggingLevel: apigateway.MethodLoggingLevel.INFO,
    dataTraceEnabled: true,
    metricsEnabled: true,
    tracingEnabled: true,
    throttlingBurstLimit: 100,
    throttlingRateLimit: 50,
  },
  cloudWatchRole: true,
  endpointConfiguration: {
    types: [apigateway.EndpointType.REGIONAL],
  },
});
```

### 9.2 Configure API routes and integrations ✅

**What was implemented:**
- Created `/data/updates` resource with GET method → `updatesHandlerLambda`
- Created `/agent/query` resource with POST method → `queryHandlerLambda`
- Created `/agent/action` resource with POST method → `actionHandlerLambda`
- Configured Lambda proxy integrations for all endpoints
- Added request validators for POST endpoints
- Configured request parameters (required `since`, optional `domain` for updates endpoint)
- Set up method responses with proper status codes (200, 400, 500)
- Created API Key and Usage Plan for authentication

**API Structure:**
```
/
├── /data
│   └── /updates (GET) → updatesHandlerLambda
└── /agent
    ├── /query (POST) → queryHandlerLambda
    └── /action (POST) → actionHandlerLambda
```

**Lambda Integrations:**
- All integrations use Lambda proxy mode for simplified request/response handling
- Test invocation enabled for all integrations
- API key required for all endpoints

**Usage Plan:**
- Rate limit: 50 requests/second
- Burst limit: 100 requests
- Daily quota: 10,000 requests
- API key authentication enforced

### 9.3 Set up CORS configuration ✅

**What was implemented:**
- Configured default CORS preflight options at the API level
- Environment-specific CORS origins (all origins for dev/staging, specific domain for prod)
- Allowed methods: GET, POST, OPTIONS
- Allowed headers: Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token
- CORS credentials disabled for security
- Max age: 1 hour for preflight caching
- CORS headers included in all method responses

**CORS Configuration:**
```typescript
defaultCorsPreflightOptions: {
  allowOrigins: config.stage === 'prod' 
    ? ['https://your-production-domain.com']
    : apigateway.Cors.ALL_ORIGINS,
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  allowHeaders: [
    'Content-Type',
    'X-Amz-Date',
    'Authorization',
    'X-Api-Key',
    'X-Amz-Security-Token',
  ],
  allowCredentials: false,
  maxAge: cdk.Duration.hours(1),
}
```

## Requirements Satisfied

✅ **Requirement 1.1**: Secure REST API exposed through Amazon API Gateway  
✅ **Requirement 1.2**: API stages configured (dev, prod via config.stage)  
✅ **Requirement 1.3**: CORS properly handled with appropriate origins  
✅ **Requirement 1.4**: Three specific endpoints provided:
- `GET /data/updates`
- `POST /agent/query`
- `POST /agent/action`

## Outputs Added

The following CloudFormation outputs were added:
- `APIKeyId`: API Key ID for retrieving the actual key value from AWS Console

## Testing Recommendations

1. **Deploy the stack:**
   ```bash
   cd command-center-backend
   npm run deploy
   ```

2. **Retrieve API Key value:**
   ```bash
   aws apigateway get-api-key --api-key <APIKeyId> --include-value
   ```

3. **Test GET /data/updates:**
   ```bash
   curl -X GET \
     "https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/data/updates?since=2023-02-06T00:00:00Z" \
     -H "x-api-key: <your-api-key>"
   ```

4. **Test POST /agent/query:**
   ```bash
   curl -X POST \
     "https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/agent/query" \
     -H "x-api-key: <your-api-key>" \
     -H "Content-Type: application/json" \
     -d '{"text": "Show me all critical medical incidents"}'
   ```

5. **Test POST /agent/action:**
   ```bash
   curl -X POST \
     "https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/agent/action" \
     -H "x-api-key: <your-api-key>" \
     -H "Content-Type: application/json" \
     -d '{"actionId": "GENERATE_AREA_BRIEFING", "payload": {"area": "Nurdağı"}}'
   ```

## Security Features

1. **API Key Authentication**: All endpoints require valid API key
2. **Usage Plan**: Rate limiting and quotas prevent abuse
3. **Request Validation**: POST endpoints validate request body structure
4. **Throttling**: Burst and rate limits configured
5. **CORS**: Restricted origins in production environment
6. **CloudWatch Logging**: Full request/response logging enabled

## Next Steps

- Update production CORS origin in the CDK code when production domain is known
- Configure custom domain name for the API (optional)
- Set up API Gateway access logs to S3 for long-term retention (task 10.1)
- Create CloudWatch dashboard for API metrics (task 10.2)
- Test integration with Command Center Dashboard (task 12.3)

## Notes

- The API Key value must be retrieved from AWS Console or CLI after deployment
- Production CORS origin is currently set to a placeholder and should be updated
- All Lambda functions must be deployed and functional before testing the API
- Request validators ensure proper JSON structure for POST endpoints
