# Task 8 Implementation: actionHandlerLambda

## Overview

This document describes the implementation of the `actionHandlerLambda` function, which handles the `POST /agent/action` endpoint for executing pre-defined actions in the Command Center Backend.

## Implementation Summary

### Files Created/Modified

1. **`lib/lambdas/actionHandler.ts`** (NEW)
   - Main Lambda handler for action execution
   - Validates actionIds against known actions
   - Maps actions to specific prompts
   - Invokes Bedrock Agent
   - Transforms agent output to API response format

2. **`lib/command-center-backend-stack.ts`** (MODIFIED)
   - Added `actionHandlerLambda` property
   - Created `createActionHandlerLambda()` method
   - Added CloudFormation output for Lambda ARN

## Key Features

### 1. Action Validation (Task 8.4)

The handler validates all incoming `actionId` values against a predefined list of known actions:

```typescript
const ACTION_MAPPINGS: Record<string, (payload?: any) => string> = {
  'GENERATE_AREA_BRIEFING': (payload) => { ... },
  'CALC_ROUTE': (payload) => { ... },
  'SHOW_CRITICAL_MEDICAL': () => { ... },
  'SHOW_RESOURCE_GAPS': () => { ... },
  'ANALYZE_DEMAND_ZONES': () => { ... },
  'SHOW_FIRE_INCIDENTS': () => { ... },
  'SHOW_STRUCTURAL_DAMAGE': () => { ... },
  'SHOW_LOGISTICS_STATUS': () => { ... },
  'SHOW_COMMUNICATION_STATUS': () => { ... },
  'HELP': () => { ... },
};
```

**Validation Logic:**
- If an unknown `actionId` is provided, the handler returns a `400 Bad Request` with error code `INVALID_ACTION`
- The error response includes a list of available actions for the client
- All action executions are logged with the actionId for debugging and auditing

### 2. Action-to-Prompt Mapping (Task 8.2)

Each action is mapped to a specific prompt that gets sent to the Bedrock Agent:

**Example: GENERATE_AREA_BRIEFING**
```typescript
'GENERATE_AREA_BRIEFING': (payload) => {
  const area = payload?.area || 'the affected region';
  return `Generate a comprehensive briefing for ${area}. Include all critical incidents, resource status, and urgent needs.`;
}
```

**Example: CALC_ROUTE**
```typescript
'CALC_ROUTE': (payload) => {
  const from = payload?.from || 'the logistics hub';
  const to = payload?.to || 'the destination';
  return `Calculate the optimal route from ${from} to ${to}. Consider road conditions, damaged infrastructure, and current traffic.`;
}
```

The prompt generator functions accept an optional `payload` parameter, allowing actions to be customized with user-provided data.

### 3. Bedrock Agent Invocation (Task 8.2)

The handler invokes the Bedrock Agent with the constructed prompt:

```typescript
const agentInput: InvokeAgentCommandInput = {
  agentId: AGENT_ID,
  agentAliasId: AGENT_ALIAS_ID,
  sessionId: `action-${actionId}-${Date.now()}-${Math.random().toString(36).substring(7)}`,
  inputText: prompt,
};
```

**Features:**
- Unique session ID per action execution
- 55-second timeout (Lambda timeout is 60s)
- Streaming response processing
- Timeout handling with partial response support

### 4. Response Transformation (Task 8.3)

The handler transforms the agent's response into the standard API response format:

```typescript
interface ActionResponse {
  simulationTime: string;
  timestamp: string;
  chatResponse: string;
  mapAction: 'REPLACE' | 'APPEND';
  mapLayers: MapLayer[];
  viewState?: ViewState;
  tabularData?: any;
  uiContext?: UIContext;
  clientStateHint?: ClientStateHint;
}
```

**Transformation Logic:**
- Attempts to parse structured JSON from agent response
- Extracts map layers, view state, and UI context
- Falls back to raw text if JSON parsing fails
- Ensures chatResponse is never empty

### 5. Error Handling

Comprehensive error handling for various scenarios:

**Configuration Errors:**
- Missing `AGENT_ID` or `AGENT_ALIAS_ID` → `500 CONFIGURATION_ERROR`

**Validation Errors:**
- Invalid request body → `400 INVALID_REQUEST`
- Unknown actionId → `400 INVALID_ACTION`

**Agent Errors:**
- Access denied → `403 AGENT_ERROR`
- Throttling → `429 RATE_LIMIT_EXCEEDED`
- Timeout → `504 TIMEOUT_ERROR`
- Service unavailable → `503 AGENT_ERROR`

**Timeout Handling:**
When an agent invocation times out, the handler returns a partial response:
```typescript
{
  chatResponse: "The action 'X' is taking longer than expected. Please try again or try a different action.",
  mapAction: 'REPLACE',
  mapLayers: [],
  uiContext: {
    suggestedActions: [
      { label: 'Try again', actionId: 'X', payload: {...} },
      { label: 'Get help', actionId: 'HELP' }
    ]
  }
}
```

### 6. Logging and Observability

All action executions are logged with:
- Request ID
- Action ID
- Payload keys (not values, for security)
- Invocation duration
- Response characteristics
- Error details

**Example Log:**
```json
{
  "message": "Executing action",
  "actionId": "SHOW_CRITICAL_MEDICAL",
  "hasPayload": false,
  "requestId": "abc-123-def-456"
}
```

## API Contract

### Request

**Endpoint:** `POST /agent/action`

**Headers:**
- `Content-Type: application/json`
- `X-Api-Key: <api-key>` (when API Gateway is configured)

**Body:**
```json
{
  "actionId": "GENERATE_AREA_BRIEFING",
  "payload": {
    "area": "Nurdağı city limits"
  }
}
```

### Response

**Success (200 OK):**
```json
{
  "simulationTime": "Day 3, 14:30",
  "timestamp": "2023-02-09T14:30:00Z",
  "chatResponse": "Here is a comprehensive briefing for Nurdağı city limits...",
  "mapAction": "REPLACE",
  "mapLayers": [
    {
      "layerId": "critical-incidents",
      "layerName": "Critical Incidents",
      "geometryType": "Point",
      "style": {
        "icon": "BUILDING_COLLAPSE",
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
    "zoom": 12
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

**Error (400 Bad Request - Invalid Action):**
```json
{
  "error": {
    "code": "INVALID_ACTION",
    "message": "Unknown actionId: INVALID_ACTION_ID",
    "details": {
      "actionId": "INVALID_ACTION_ID",
      "availableActions": [
        "GENERATE_AREA_BRIEFING",
        "CALC_ROUTE",
        "SHOW_CRITICAL_MEDICAL",
        ...
      ]
    }
  }
}
```

## Available Actions

| Action ID | Description | Payload Parameters |
|-----------|-------------|-------------------|
| `GENERATE_AREA_BRIEFING` | Generate comprehensive briefing for an area | `area` (string, optional) |
| `CALC_ROUTE` | Calculate optimal route between two points | `from` (string, optional), `to` (string, optional) |
| `SHOW_CRITICAL_MEDICAL` | Display all critical medical incidents | None |
| `SHOW_RESOURCE_GAPS` | Identify areas with critical resource shortages | None |
| `ANALYZE_DEMAND_ZONES` | Visualize demand zones with heat maps | None |
| `SHOW_FIRE_INCIDENTS` | Display all active fire incidents | None |
| `SHOW_STRUCTURAL_DAMAGE` | Show structural damage reports | None |
| `SHOW_LOGISTICS_STATUS` | Display logistics operations status | None |
| `SHOW_COMMUNICATION_STATUS` | Show communication infrastructure status | None |
| `HELP` | Provide system overview and help | None |

## Testing

### Manual Testing

Test the action handler with curl:

```bash
# Test valid action
curl -X POST https://api-endpoint/agent/action \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-api-key" \
  -d '{
    "actionId": "SHOW_CRITICAL_MEDICAL"
  }'

# Test action with payload
curl -X POST https://api-endpoint/agent/action \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-api-key" \
  -d '{
    "actionId": "GENERATE_AREA_BRIEFING",
    "payload": {
      "area": "Nurdağı city limits"
    }
  }'

# Test invalid action (should return 400)
curl -X POST https://api-endpoint/agent/action \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-api-key" \
  -d '{
    "actionId": "INVALID_ACTION"
  }'
```

### Integration Testing

The action handler can be tested locally using AWS SAM or by deploying to a test environment:

```bash
# Deploy to test environment
cd command-center-backend
npm run build
cdk deploy --context stage=test

# Test with AWS CLI
aws lambda invoke \
  --function-name CommandCenterBackend-test-ActionHandler \
  --payload '{"body": "{\"actionId\": \"SHOW_CRITICAL_MEDICAL\"}"}' \
  response.json

cat response.json
```

## Performance Considerations

- **Timeout:** 60 seconds (Lambda timeout)
- **Memory:** 512 MB
- **Cold Start:** ~2-3 seconds
- **Warm Invocation:** ~1-5 seconds (depending on agent response time)
- **Agent Timeout:** 55 seconds (allows 5 seconds for Lambda overhead)

## Security

- **IAM Role:** `actionLambdaRole` with least privilege
- **Permissions:** Bedrock Agent invoke only
- **Input Validation:** Zod schema validation
- **Action Validation:** Whitelist of known actions
- **Logging:** No sensitive data in logs (payload keys only, not values)

## Next Steps

Task 8 is now complete. The next task is:

**Task 9: Set up API Gateway**
- Create REST API routes
- Configure Lambda integrations
- Set up CORS
- Add API key authentication

## Requirements Satisfied

✅ **Requirement 1.4:** API endpoint infrastructure with POST /agent/action  
✅ **Requirement 4.1:** Map actionId to query intent  
✅ **Requirement 4.2:** Construct prompts for pre-defined actions  
✅ **Requirement 4.3:** Invoke Bedrock Agent with context  
✅ **Requirement 4.4:** Return structured JSON format  
✅ **Requirement 4.5:** Validate actionId and return clear errors  

## Conclusion

The `actionHandlerLambda` is fully implemented with:
- ✅ Action validation against known actions
- ✅ Action-to-prompt mapping with payload support
- ✅ Bedrock Agent invocation with timeout handling
- ✅ Response transformation to API format
- ✅ Comprehensive error handling
- ✅ Detailed logging for debugging and auditing

The implementation follows the same patterns as `queryHandlerLambda` for consistency and maintainability.
