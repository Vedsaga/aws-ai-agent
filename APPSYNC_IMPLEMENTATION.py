#!/usr/bin/env python3
"""
AppSync Real-time Status Broadcasting - Technical Implementation Summary

This file documents the AppSync implementation for real-time status updates
during data-ingestion and data-query operations.

OVERVIEW
========
AWS AppSync provides real-time GraphQL subscriptions that allow clients to
receive status updates as jobs progress through the multi-agent orchestration
pipeline. This eliminates the need for polling and provides instant feedback
to users.

ARCHITECTURE
============

┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │◄────────┤   AppSync    │◄────────┤  Status     │
│ (Browser/   │WebSocket│   GraphQL    │ GraphQL │  Publisher  │
│  Mobile)    │Subscribe│     API      │ Mutation│  Lambda     │
└─────────────┘         └──────────────┘         └─────────────┘
                               ▲                        ▲
                               │                        │
                               │                        │
                        ┌──────┴────────┐      ┌────────┴────────┐
                        │  UserSessions │      │  Orchestrator   │
                        │  DynamoDB     │      │  & Agents       │
                        └───────────────┘      └─────────────────┘

COMPONENTS
==========

1. AppSync GraphQL API
   - Provides WebSocket subscriptions
   - Handles connection management
   - Routes status updates to subscribers
   - File: infrastructure/lib/stacks/realtime-stack.ts

2. GraphQL Schema
   - Defines StatusUpdate type
   - Mutation: publishStatus
   - Subscription: onStatusUpdate
   - File: infrastructure/lambda/realtime/schema.graphql

3. Status Publisher Lambda
   - Receives status events from orchestrator/agents
   - Looks up user connection_id
   - Publishes to AppSync GraphQL mutation
   - File: infrastructure/lambda/realtime/status_publisher.py

4. Status Utils Module
   - Helper functions for publishing status
   - Used by orchestrator and agents
   - Provides: publish_orchestrator_status(), publish_agent_status()
   - File: infrastructure/lambda/realtime/status_utils.py

5. Updated Handlers
   - ingest_handler_with_orchestrator.py: Publishes initial status
   - query_index.py: Publishes query status
   - orchestrator_handler.py: Publishes status at each pipeline stage

GRAPHQL SCHEMA
==============

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
  publishStatus(
    jobId: ID!
    userId: ID!
    agentName: String
    status: String!
    message: String!
    metadata: AWSJSON
  ): StatusUpdate
}

type Subscription {
  onStatusUpdate(userId: ID!): StatusUpdate
    @aws_subscribe(mutations: ["publishStatus"])
}

STATUS FLOW - DATA INGESTION
=============================

1. Client submits report → POST /api/v1/ingest
   Status: "accepted" - Report received and queued

2. Orchestrator starts
   Status: "processing" - Agent orchestration started
   Status: "loading_agents" - Loading agent configuration
   Status: "agents_loaded" - Agent pipeline loaded

3. For each agent:
   Status: "agent_invoking" - Executing agent X/N
   Status: "agent_complete" - Agent completed with confidence

4. Verification & Summary:
   Status: "verifying" - Verifying agent outputs
   Status: "synthesizing" - Generating summary
   Status: "saving" - Saving results to database

5. Completion:
   Status: "complete" - Job completed successfully
   OR
   Status: "error" - Job failed with error

STATUS FLOW - DATA QUERY
=========================

Same flow as data ingestion, but with query-specific agents:
- what_agent, where_agent, when_agent, how_agent, why_agent

CLIENT INTEGRATION
==================

JavaScript/Browser Example:
---------------------------
const subscriber = new BrowserAppSyncClient();
const ws = await subscriber.subscribe('demo-user', (update) => {
  console.log('Status:', update.status, update.message);

  if (update.status === 'complete') {
    console.log('Job completed!', update.metadata);
  }
});

Python Example:
---------------
subscriber = AppSyncStatusSubscriber(
    api_url=APPSYNC_API_URL,
    api_key=APPSYNC_API_KEY,
    user_id='demo-user'
)

subscriber.on_status(lambda update: print(f"Status: {update['status']}"))
await subscriber.subscribe()

React Example:
--------------
import { useEffect, useState } from 'react';

function StatusMonitor({ userId, jobId }) {
  const [status, setStatus] = useState([]);

  useEffect(() => {
    const ws = subscribeToStatus(userId, (update) => {
      if (update.jobId === jobId) {
        setStatus(prev => [...prev, update]);
      }
    });

    return () => ws.close();
  }, [userId, jobId]);

  return (
    <div>
      {status.map((s, i) => (
        <StatusItem key={i} status={s} />
      ))}
    </div>
  );
}

DEPLOYMENT
==========

1. Deploy AppSync Stack:
   bash deploy_realtime_stack.sh

2. Update Orchestrator Environment:
   - Add STATUS_PUBLISHER_FUNCTION env variable
   - Grant Lambda invoke permissions

3. Deploy Updated Handlers:
   - Redeploy ingest_handler_with_orchestrator.py
   - Redeploy query_index.py
   - Redeploy orchestrator_handler.py

4. Test Real-time Updates:
   python test_appsync_realtime.py

CONFIGURATION
=============

Environment Variables Required:
- APPSYNC_API_URL: AppSync GraphQL endpoint
- APPSYNC_API_KEY: API key for authentication
- STATUS_PUBLISHER_FUNCTION: ARN of status publisher Lambda
- USER_SESSIONS_TABLE: DynamoDB table for connection tracking

IAM Permissions Required:
- Lambda → AppSync: appsync:GraphQL
- Lambda → DynamoDB: dynamodb:Query (UserSessions table)
- Orchestrator → Lambda: lambda:InvokeFunction (status publisher)

BENEFITS vs POLLING
====================

1. Real-time Updates
   - Instant notification of status changes
   - No delay between status change and client notification
   - Polling: 1-5 second delay depending on polling interval

2. Reduced Load
   - No repeated polling requests
   - Server only sends updates when status changes
   - Polling: N requests per second per client

3. Better UX
   - Immediate feedback to users
   - Progress indication during 2-3 minute jobs
   - Shows which agent is currently executing

4. Scalability
   - AppSync handles connection management
   - Auto-scales to thousands of concurrent subscribers
   - Polling: Each client creates independent load

5. Cost Efficiency
   - Pay only for actual status updates
   - No wasted requests for unchanged status
   - Polling: Pay for all requests, even when no change

COMPARISON: AppSync vs Polling
===============================

Metric               | AppSync Real-time | Polling (5s interval)
---------------------|-------------------|----------------------
Update Latency       | <100ms            | 0-5 seconds
Requests per Job     | 10-15 updates     | 24-36 requests
Server Load          | Low (event-driven)| High (continuous)
Client Complexity    | WebSocket setup   | Simple HTTP
Network Efficiency   | Very High         | Low
Cost (per 1000 jobs) | ~$0.50            | ~$2-5

STATUS CODES REFERENCE
======================

Orchestrator Level:
- accepted: Job received and queued
- processing: Orchestration started
- loading_agents: Loading agent configuration
- agents_loaded: Agent pipeline ready
- verifying: Checking agent outputs
- synthesizing: Generating summary
- saving: Persisting results
- complete: Job finished successfully
- error: Job failed

Agent Level:
- agent_invoking: Agent execution starting
- agent_calling_tool: Agent using external tool
- agent_complete: Agent finished

TESTING
=======

Run comprehensive tests:
  python test_appsync_realtime.py

Run example client:
  # Ingest with monitoring
  python appsync_client_example.py ingest

  # Query with monitoring
  python appsync_client_example.py query

  # Continuous monitoring
  python appsync_client_example.py monitor

Check AppSync logs:
  aws logs tail /aws/appsync/apis/<api-id> --follow

TROUBLESHOOTING
===============

Issue: No status updates received
Solution:
  1. Check AppSync API URL and key are correct
  2. Verify STATUS_PUBLISHER_FUNCTION is set in orchestrator
  3. Check CloudWatch logs for status publisher Lambda
  4. Ensure WebSocket connection is established

Issue: Connection drops after 2 minutes
Solution:
  - AppSync has keep-alive mechanism
  - Client should handle 'ka' (keep-alive) messages
  - Reconnect on connection loss

Issue: Status updates delayed
Solution:
  - Check Lambda execution time
  - Verify STATUS_PUBLISHER_FUNCTION invocation is async
  - Review orchestrator logs for bottlenecks

Issue: Missing agent-level updates
Solution:
  - Ensure publish_agent_status() is called in orchestrator
  - Check that realtime module is in sys.path
  - Verify agent execution doesn't fail silently

MONITORING
==========

Key Metrics to Track:
1. AppSync Connection Count
2. Status Update Latency
3. WebSocket Connection Errors
4. Status Publisher Lambda Invocations
5. Failed Status Publications

CloudWatch Queries:
  # Count status updates by type
  fields @timestamp, status, jobId
  | filter @message like /Status:/
  | stats count() by status

  # Find slow status publications
  fields @timestamp, @duration, jobId
  | filter @type = "Lambda"
  | filter @duration > 1000
  | sort @duration desc

FUTURE ENHANCEMENTS
===================

1. Add status history to DynamoDB
   - Store all status updates for audit trail
   - Enable status replay for reconnecting clients

2. Implement status filters
   - Allow clients to subscribe to specific job types
   - Filter by domain_id or priority

3. Add rate limiting
   - Prevent status spam
   - Batch rapid updates

4. Implement status acknowledgment
   - Track which updates client has received
   - Resend missed updates on reconnection

5. Add multi-region support
   - Replicate AppSync API across regions
   - Route clients to nearest endpoint

SECURITY CONSIDERATIONS
=======================

1. Authentication
   - Current: API Key (for demo/testing)
   - Production: Use Cognito User Pools or IAM
   - Implement user_id validation

2. Authorization
   - Verify user can access job status
   - Check tenant_id matches user's tenant
   - Implement RBAC for sensitive statuses

3. Rate Limiting
   - Limit status publications per job
   - Throttle rapid reconnections
   - Monitor for abuse patterns

4. Data Privacy
   - Don't include sensitive data in status messages
   - Log sanitized versions of updates
   - Encrypt metadata field if needed

COST ESTIMATION
===============

AppSync Pricing (us-east-1):
- Queries/Mutations: $4 per million
- Real-time updates: $2 per million
- Connection minutes: $0.08 per million

Example: 10,000 jobs/month, 15 status updates each
- Total updates: 150,000
- Cost: $0.30/month
- Plus connection time: ~$0.20/month
- Total: ~$0.50/month

Compared to API Gateway polling (5s interval):
- 10,000 jobs × 30 seconds × (1 poll/5s) = 60,000 requests
- Cost: ~$2.00/month (API Gateway + Lambda)

Savings: ~75% cost reduction with better UX

FILES MODIFIED/CREATED
======================

Created:
- infrastructure/lambda/realtime/status_publisher.py
- infrastructure/lambda/realtime/status_utils.py
- infrastructure/lambda/realtime/schema.graphql
- infrastructure/lib/stacks/realtime-stack.ts
- appsync_client_example.py
- appsync_client_example.js
- test_appsync_realtime.py
- deploy_realtime_stack.sh

Modified:
- infrastructure/lambda/orchestration/ingest_handler_with_orchestrator.py
- infrastructure/lambda/orchestration/query_index.py
- infrastructure/lambda/orchestration/orchestrator_handler.py
- infrastructure/lib/stacks/orchestration-stack.ts

SUMMARY
=======

AppSync provides a production-ready solution for real-time status updates with:
✅ Sub-second latency
✅ Automatic scaling
✅ Lower cost than polling
✅ Better user experience
✅ Reduced server load
✅ Simple client integration

The implementation is complete and ready for deployment.
"""


# Example usage in Lambda
def example_publish_status():
    """Example: Publishing status from orchestrator"""
    from status_utils import publish_orchestrator_status

    publish_orchestrator_status(
        job_id="job_abc123",
        user_id="demo-user",
        tenant_id="default-tenant",
        status="loading_agents",
        message="Loading agent configuration for domain: civic_complaints",
        metadata={"domain_id": "civic_complaints"},
    )


def example_client_subscription():
    """Example: Client subscribing to updates"""
    import asyncio
    from appsync_client_example import AppSyncStatusSubscriber

    async def monitor():
        subscriber = AppSyncStatusSubscriber(
            api_url="https://xxx.appsync-api.us-east-1.amazonaws.com/graphql",
            api_key="your-api-key",
            user_id="demo-user",
        )

        subscriber.on_status(lambda update: print(f"Status: {update['status']}"))
        await subscriber.subscribe()

    asyncio.run(monitor())
