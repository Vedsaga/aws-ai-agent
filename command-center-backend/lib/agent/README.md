# Bedrock Agent Configuration

## Overview

This directory contains configuration files for the Amazon Bedrock Agent used in the Command Center Backend.

## Files

### action-group-schema.json

OpenAPI 3.0 schema that defines the `databaseQueryTool` Action Group. This schema describes:

- **Endpoint**: POST /query
- **Parameters**:
  - `domain`: Filter by event domain (MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION)
  - `severity`: Filter by severity level (CRITICAL, HIGH, MEDIUM, LOW)
  - `startTime`: Start of time range (ISO 8601)
  - `endTime`: End of time range (ISO 8601)
  - `location`: Geographic filter with lat, lon, and optional radiusKm
  - `limit`: Maximum number of results (1-100, default 50)

- **Response**: Array of events with full event details

## Agent Configuration

The Bedrock Agent is configured in `command-center-backend-stack.ts` with:

- **Model**: Claude 3 Sonnet (anthropic.claude-3-sonnet-20240229-v1:0)
- **Instruction Prompt**: Detailed persona and guidelines for disaster response queries
- **Action Group**: databaseQueryTool for querying the simulation database
- **Timeout**: 10 minutes idle session TTL

## Usage

The agent is automatically deployed when you run `cdk deploy`. After deployment:

1. Test in AWS Bedrock Console (see BEDROCK_AGENT_TESTING.md)
2. Invoke via queryHandlerLambda (task 7)
3. Invoke via actionHandlerLambda (task 8)

## Modifying the Schema

If you need to add new query capabilities:

1. Update `action-group-schema.json` with new parameters
2. Update the databaseQueryToolLambda implementation (task 5)
3. Redeploy the stack
4. Test the new functionality

## Security

- Agent role has minimal permissions (only InvokeModel)
- Tool Lambda has read-only DynamoDB access
- All invocations are logged to CloudWatch
