# Bedrock Agent Testing Guide

## Overview

This guide provides instructions for testing the Command Center Bedrock Agent after deployment.
The agent is configured with Claude 3 Sonnet and has access to the databaseQueryTool Action Group.

## Prerequisites

1. Deploy the CDK stack: `npm run deploy`
2. Populate the DynamoDB table with simulation data
3. Note the Bedrock Agent ID and Alias ID from the CDK outputs

## Testing in AWS Bedrock Console

### Access the Agent

1. Navigate to AWS Console → Amazon Bedrock → Agents
2. Find the agent named `{stackName}-Agent`
3. Click on the agent to view details
4. Click "Test" button to open the testing playground

### Basic Query Tests

Test these queries to verify basic functionality:

#### Test 1: Simple Domain Query
**Query:** "Show me all medical incidents"

**Expected Behavior:**
- Agent should invoke databaseQueryTool with domain="MEDICAL"
- Should return a list of medical incidents
- Response should include natural language summary

#### Test 2: Severity Filter Query
**Query:** "What are the critical incidents right now?"

**Expected Behavior:**
- Agent should invoke databaseQueryTool with severity="CRITICAL"
- Should return critical incidents across all domains
- Response should highlight urgency

#### Test 3: Time Range Query
**Query:** "Show me incidents from the last 6 hours"

**Expected Behavior:**
- Agent should calculate time range
- Should invoke databaseQueryTool with appropriate startTime/endTime
- Should return recent incidents

#### Test 4: Location-Based Query
**Query:** "What incidents are near Nurdağı?"

**Expected Behavior:**
- Agent should invoke databaseQueryTool with location filter
- Should return incidents in the specified area
- Response should include geographic context


#### Test 5: Complex Multi-Filter Query
**Query:** "Show me critical medical incidents from the past 12 hours"

**Expected Behavior:**
- Agent should combine multiple filters
- Should invoke databaseQueryTool with domain="MEDICAL", severity="CRITICAL", and time range
- Response should be specific and actionable

### Tool Invocation Verification

In the Bedrock console test interface, you should see:

1. **Trace View**: Shows the agent's reasoning process
2. **Tool Calls**: Displays when databaseQueryTool is invoked
3. **Tool Parameters**: Shows the parameters passed to the tool
4. **Tool Response**: Shows the data returned from DynamoDB
5. **Final Response**: The agent's synthesized natural language answer

### Verifying Action Group Configuration

Check that the Action Group is properly configured:

1. In the agent details, navigate to "Action Groups"
2. Verify "databaseQueryTool" is listed and ENABLED
3. Check that the Lambda function is correctly associated
4. Review the OpenAPI schema is properly loaded


## Testing via API (After Task 7 Implementation)

Once the queryHandlerLambda is implemented, test via API:

```bash
# Test natural language query
curl -X POST https://your-api-endpoint/agent/query \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "text": "Show me all critical medical incidents",
    "sessionId": "test-session-1"
  }'
```

## Common Issues and Troubleshooting

### Issue: Agent doesn't invoke the tool
**Solution:** 
- Check that the Action Group is ENABLED
- Verify Lambda permissions allow Bedrock to invoke it
- Review agent instruction prompt for clarity

### Issue: Tool returns empty results
**Solution:**
- Verify DynamoDB table has data
- Check that databaseQueryToolLambda is implemented (task 5)
- Review CloudWatch logs for the tool Lambda

### Issue: Agent gives generic responses
**Solution:**
- Refine the instruction prompt to be more specific
- Add more examples of good responses
- Ensure tool description is clear


## Instruction Prompt Refinement

Based on testing results, you may need to refine the instruction prompt. Key areas to adjust:

1. **Specificity**: Make instructions more specific if agent is too vague
2. **Examples**: Add more examples for complex query types
3. **Map Control**: Clarify map visualization guidelines if needed
4. **Response Format**: Ensure agent understands the expected structure

To update the instruction prompt:
1. Edit `command-center-backend/lib/command-center-backend-stack.ts`
2. Modify the `instructionPrompt` variable in `createBedrockAgent` method
3. Redeploy: `npm run deploy`
4. Test again in Bedrock console

## Performance Benchmarks

Expected performance metrics:

- **Simple queries** (single filter): < 2 seconds
- **Complex queries** (multiple filters): < 3 seconds
- **Tool invocation overhead**: ~500ms
- **Agent reasoning time**: 1-2 seconds

## Next Steps

After successful testing:

1. Document any prompt refinements made
2. Note common query patterns that work well
3. Identify edge cases that need handling
4. Proceed to implement queryHandlerLambda (task 7)
5. Implement actionHandlerLambda (task 8)
