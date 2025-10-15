# Bedrock Agent Configuration - Quick Reference

## ✅ Task 6 Complete

The Amazon Bedrock Agent has been fully configured in CDK and is ready for deployment.

## What's Ready

### 1. Agent Configuration
- **Model**: Claude 3 Sonnet (anthropic.claude-3-sonnet-20240229-v1:0)
- **Instruction Prompt**: Comprehensive disaster response assistant persona
- **Session Timeout**: 10 minutes
- **IAM Role**: Configured with minimal permissions

### 2. Action Group: databaseQueryTool
- **OpenAPI Schema**: `lib/agent/action-group-schema.json`
- **Lambda Handler**: `lib/lambdas/databaseQueryTool.ts` (placeholder)
- **Parameters**: domain, severity, startTime, endTime, location, limit
- **Status**: ENABLED

### 3. Infrastructure
- **CDK Stack**: Updated with Bedrock Agent resources
- **Lambda Placeholder**: Created for tool (needs Task 5 implementation)
- **Outputs**: Agent ID and Alias ID will be available after deployment

## Quick Deploy

```bash
cd command-center-backend
npm run build
cdk deploy
```

## Testing After Deployment

See `BEDROCK_AGENT_TESTING.md` for comprehensive testing guide.

Quick test in AWS Console:
1. Go to Amazon Bedrock → Agents
2. Find your agent
3. Click "Test"
4. Try: "Show me all critical medical incidents"

## What's Next

### Immediate Next Steps:
1. **Task 5**: Implement databaseQueryToolLambda (currently placeholder)
2. **Task 7**: Implement queryHandlerLambda to invoke agent from API
3. **Task 8**: Implement actionHandlerLambda for pre-defined actions

### Dependencies:
- Task 5 must be completed for the agent to return real data
- Tasks 7 & 8 enable API access to the agent
- Task 9 connects everything through API Gateway

## Key Files Reference

```
command-center-backend/
├── lib/
│   ├── agent/
│   │   ├── action-group-schema.json    # OpenAPI schema
│   │   └── README.md                   # Agent config docs
│   ├── lambdas/
│   │   └── databaseQueryTool.ts        # Tool Lambda (placeholder)
│   └── command-center-backend-stack.ts # CDK with agent config
├── BEDROCK_AGENT_TESTING.md            # Testing guide
└── TASK_6_IMPLEMENTATION.md            # Implementation details
```

## Agent Instruction Prompt Highlights

The agent is instructed to:
- Be concise and factual
- Include specific numbers and locations
- Autonomously control map visualization
- Use proper color coding (CRITICAL=#DC2626, HIGH=#F59E0B, etc.)
- Generate appropriate GeoJSON layers
- Provide suggested follow-up actions

## Cost Estimate

- **Agent invocations**: ~$0.003 per request (Claude 3 Sonnet)
- **Lambda executions**: Minimal (< $0.0001 per invocation)
- **DynamoDB reads**: Covered by on-demand pricing
- **Expected monthly cost**: < $10 for development/testing

## Support

For issues or questions:
1. Check `BEDROCK_AGENT_TESTING.md` troubleshooting section
2. Review CloudWatch logs for the agent and tool Lambda
3. Verify IAM permissions are correctly configured
