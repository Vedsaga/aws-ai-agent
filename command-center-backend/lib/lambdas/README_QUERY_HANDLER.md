# Query Handler Lambda

## Overview

The Query Handler Lambda (`queryHandler.ts`) processes natural language queries from the Command Center Dashboard by invoking Amazon Bedrock Agent and transforming the agent's response into a structured format.

## Endpoint

**POST /agent/query**

## Request Format

```json
{
  "text": "Show me all critical medical incidents in Nurdağı",
  "sessionId": "optional-session-id-for-continuity",
  "currentMapState": {
    "center": [37.15, 37.12],
    "zoom": 12
  }
}
```

### Request Fields

- `text` (required): Natural language query string
- `sessionId` (optional): Session ID for conversation continuity
- `currentMapState` (optional): Current map view context
  - `center`: [longitude, latitude]
  - `zoom`: Zoom level

## Response Format

```json
{
  "simulationTime": "Day 3, 14:30",
  "timestamp": "2024-02-09T14:30:00Z",
  "chatResponse": "There are 12 critical medical incidents in Nurdağı...",
  "mapAction": "REPLACE",
  "mapLayers": [
    {
      "layerId": "critical-medical",
      "layerName": "Critical Medical Incidents",
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
  ],
  "viewState": {
    "center": { "lat": 37.15, "lon": 37.12 },
    "zoom": 13
  },
  "uiContext": {
    "suggestedActions": [
      {
        "label": "Show resource allocation",
        "actionId": "SHOW_RESOURCES",
        "payload": { "domain": "MEDICAL" }
      }
    ]
  }
}
```

### Response Fields

- `simulationTime`: Human-readable simulation time (e.g., "Day 3, 14:30")
- `timestamp`: ISO 8601 timestamp
- `chatResponse`: Natural language answer from the agent
- `mapAction`: How to apply map updates ("REPLACE" or "APPEND")
- `mapLayers`: Array of map layers with GeoJSON data
- `viewState` (optional): Suggested map view (bounds, center, zoom)
- `tabularData` (optional): Structured data for tables
- `uiContext` (optional): UI hints and suggested actions
- `clientStateHint` (optional): Client state recommendations

## Error Responses

### Configuration Error (500)
```json
{
  "error": {
    "code": "CONFIGURATION_ERROR",
    "message": "Bedrock Agent is not properly configured",
    "details": {
      "shouldRetry": false,
      "requestId": "abc-123"
    }
  }
}
```

### Invalid Request (400)
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request body",
    "details": {
      "shouldRetry": false,
      "requestId": "abc-123"
    }
  }
}
```

### Timeout (504)
```json
{
  "error": {
    "code": "TIMEOUT_ERROR",
    "message": "Bedrock Agent request timed out. Please try a simpler query.",
    "details": {
      "shouldRetry": true,
      "requestId": "abc-123"
    }
  }
}
```

### Rate Limit (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests to Bedrock Agent. Please try again in a moment.",
    "details": {
      "shouldRetry": true,
      "requestId": "abc-123"
    }
  }
}
```

## Environment Variables

- `AGENT_ID`: Bedrock Agent ID (required)
- `AGENT_ALIAS_ID`: Bedrock Agent Alias ID (required)
- `LOG_LEVEL`: Logging verbosity (INFO or DEBUG)
- `AWS_REGION`: AWS region (default: us-east-1)

## Timeout Behavior

- **Lambda Timeout**: 60 seconds
- **Agent Invocation Timeout**: 55 seconds
- **Stream Processing**: Checks timeout during streaming

On timeout, the Lambda returns a partial response with a helpful message:

```json
{
  "simulationTime": "Day 3, 14:30",
  "timestamp": "2024-02-09T14:30:00Z",
  "chatResponse": "The query is taking longer than expected. Please try rephrasing your question or breaking it into smaller queries.",
  "mapAction": "REPLACE",
  "mapLayers": [],
  "uiContext": {
    "suggestedActions": [
      {
        "label": "Try a simpler query",
        "actionId": "HELP"
      }
    ]
  }
}
```

## Session Management

The Lambda supports conversation continuity through session IDs:

1. **First Request**: Omit `sessionId` or provide a new one
2. **Follow-up Requests**: Use the same `sessionId` to maintain context
3. **Session Timeout**: Bedrock Agent sessions expire after 10 minutes of inactivity

Example conversation:
```javascript
// First query
POST /agent/query
{
  "text": "Show me medical incidents",
  "sessionId": "user-123-session"
}

// Follow-up query (maintains context)
POST /agent/query
{
  "text": "Which ones are critical?",
  "sessionId": "user-123-session"
}
```

## Agent Response Processing

The Lambda handles various agent response formats:

### JSON in Markdown
```
Here's the information you requested:

```json
{
  "chatResponse": "There are 12 incidents...",
  "mapLayers": [...]
}
```
```

### Plain JSON
```json
{
  "chatResponse": "There are 12 incidents...",
  "mapLayers": [...]
}
```

### Plain Text
```
There are 12 critical medical incidents in Nurdağı.
```

## Logging

The Lambda logs structured information to CloudWatch:

### Request Logging
```json
{
  "message": "Query handler invoked",
  "requestId": "abc-123",
  "hasBody": true
}
```

### Validation Logging
```json
{
  "message": "Request validated",
  "textLength": 45,
  "hasSessionId": true,
  "hasMapState": false
}
```

### Agent Invocation Logging
```json
{
  "message": "Invoking Bedrock Agent",
  "agentId": "AGENT123",
  "agentAliasId": "ALIAS456",
  "sessionId": "session-789",
  "inputLength": 45
}
```

### Response Logging
```json
{
  "message": "Agent response processed",
  "responseLength": 1234,
  "processingDuration": 2500
}
```

### Error Logging
```json
{
  "message": "Error processing query request",
  "errorName": "ThrottlingException",
  "errorMessage": "Rate exceeded",
  "requestId": "abc-123",
  "timestamp": "2024-02-09T14:30:00Z"
}
```

## Performance Metrics

- **Cold Start**: ~2-3 seconds
- **Warm Invocation**: ~1-3 seconds (depending on agent processing)
- **Memory Usage**: ~200-300 MB
- **Typical Response Time**: 1-3 seconds for simple queries

## IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:agent/*",
        "arn:aws:bedrock:*::foundation-model/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Testing

### Local Testing
```bash
# Install dependencies
npm install

# Build
npm run build

# Test with SAM Local (if configured)
sam local invoke QueryHandlerLambda -e test-event.json
```

### Integration Testing
```bash
# Deploy to test environment
npm run deploy

# Test with curl
curl -X POST https://api-endpoint/agent/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "text": "Show me all critical incidents"
  }'
```

## Troubleshooting

### Agent Not Found (404)
- Verify AGENT_ID and AGENT_ALIAS_ID are correct
- Check agent exists in Bedrock console
- Verify agent is in the same region

### Access Denied (403)
- Check IAM role has bedrock:InvokeAgent permission
- Verify agent resource ARN in IAM policy
- Check agent's resource policy allows Lambda invocation

### Timeout (504)
- Query may be too complex
- Try breaking into smaller queries
- Check agent's tool Lambda performance
- Verify DynamoDB query performance

### Empty Response
- Check agent instruction prompt
- Verify agent's Action Group is configured
- Check tool Lambda logs for errors
- Test agent in Bedrock console

## Related Files

- `lib/types/api.ts`: Type definitions for request/response
- `lib/command-center-backend-stack.ts`: CDK infrastructure
- `lib/lambdas/databaseQueryTool.ts`: Agent's database query tool
- `TASK_7_IMPLEMENTATION.md`: Implementation details
