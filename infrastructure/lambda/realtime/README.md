# Real-Time Status Broadcasting System

This module implements real-time status updates for the Multi-Agent Orchestration System using AWS AppSync GraphQL API with WebSocket support.

## Overview

The real-time status system provides live updates to users as their requests are processed through the orchestration pipeline. Status messages are published at key checkpoints during agent execution, tool invocation, validation, synthesis, and completion.

## Architecture

### Components

1. **AppSync GraphQL API** - Provides WebSocket connections for real-time subscriptions
2. **Status Publisher Lambda** - Accepts status messages and publishes to AppSync
3. **Status Utils Module** - Helper functions for publishing status from orchestrator and agents
4. **DynamoDB User Sessions Table** - Tracks active user connections

### GraphQL Schema

```graphql
type StatusUpdate {
  jobId: ID!
  userId: ID!
  agentName: String
  status: String!
  message: String!
  timestamp: AWSDateTime!
  metadata: AWSJSON
}

type Mutation {
  publishStatus(...): StatusUpdate
}

type Subscription {
  onStatusUpdate(userId: ID!): StatusUpdate
    @aws_subscribe(mutations: ["publishStatus"])
}
```

## Status Types

### Orchestrator Status Messages

- `loading_agents` - Loading playbook configuration
- `validating` - Validating agent outputs
- `synthesizing` - Merging agent outputs
- `complete` - Processing complete
- `error` - Processing failed

### Agent Status Messages

- `agent_invoking` - Agent starting execution
- `agent_complete` - Agent finished successfully
- `agent_error` - Agent execution failed
- `calling_tool` - Agent invoking a tool

## Usage

### Publishing Status from Orchestrator

```python
from status_utils import publish_orchestrator_status

publish_orchestrator_status(
    job_id='job-123',
    user_id='user-456',
    tenant_id='tenant-789',
    status='loading_agents',
    message='Loading ingestion playbook for domain civic-complaints'
)
```

### Publishing Status from Agents

```python
from status_utils import publish_agent_status, publish_tool_status

# Agent completion
publish_agent_status(
    job_id='job-123',
    user_id='user-456',
    tenant_id='tenant-789',
    agent_name='Geo Agent',
    status='complete',
    message='Completed successfully',
    execution_time_ms=1234
)

# Tool invocation
publish_tool_status(
    job_id='job-123',
    user_id='user-456',
    tenant_id='tenant-789',
    agent_name='Geo Agent',
    tool_name='location',
    reason='Geocoding address from user input'
)
```

### Subscribing to Status Updates (Client-Side)

```javascript
import { AWSAppSyncClient } from 'aws-appsync';

const client = new AWSAppSyncClient({
  url: APPSYNC_API_URL,
  region: AWS_REGION,
  auth: {
    type: 'API_KEY',
    apiKey: APPSYNC_API_KEY
  }
});

const subscription = client.subscribe({
  query: gql`
    subscription OnStatusUpdate($userId: ID!) {
      onStatusUpdate(userId: $userId) {
        jobId
        agentName
        status
        message
        timestamp
        metadata
      }
    }
  `,
  variables: { userId: currentUserId }
}).subscribe({
  next: (data) => {
    console.log('Status update:', data);
    // Update UI with status message
  },
  error: (error) => {
    console.error('Subscription error:', error);
  }
});
```

## Environment Variables

### Status Publisher Lambda

- `APPSYNC_API_URL` - AppSync GraphQL API endpoint
- `APPSYNC_API_ID` - AppSync API identifier
- `USER_SESSIONS_TABLE` - DynamoDB table for user sessions
- `AWS_REGION` - AWS region

### Orchestrator and Agent Lambdas

- `STATUS_PUBLISHER_FUNCTION` - ARN of status publisher Lambda function

## Error Handling

Status publishing is designed to fail gracefully:

- If status publisher Lambda fails, the main operation continues
- Status messages are invoked asynchronously (Event invocation type)
- Missing connection_id results in a warning, not an error
- Network failures are logged but don't block processing

## Performance Considerations

- Status messages are published asynchronously to avoid blocking
- Connection lookups are cached in DynamoDB
- AppSync automatically handles WebSocket connection management
- Status publisher has 30-second timeout (sufficient for GraphQL mutation)

## Security

- AppSync API uses IAM authentication for Lambda invocations
- API Key authentication available for client connections
- User sessions table partitioned by tenant_id
- Status messages filtered by userId in subscription

## Monitoring

- CloudWatch Logs for status publisher Lambda
- AppSync field-level logging enabled
- X-Ray tracing for end-to-end request tracking
- Metrics: connection count, message publish rate, error rate

## Demo Integration

The real-time status system is critical for the hackathon demo:

1. **Visual Feedback** - Users see agents executing in real-time
2. **Transparency** - Clear visibility into system operations
3. **Debugging** - Easy to identify where processing fails
4. **Engagement** - Keeps users informed during processing

## Future Enhancements

- Message batching for high-volume scenarios
- Status message replay for reconnecting clients
- Progress percentage calculations
- Estimated time remaining
- Rich metadata (agent dependencies, tool parameters)
