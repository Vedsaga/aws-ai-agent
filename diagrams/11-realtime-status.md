# Diagram 11: Real-Time Status Streaming Architecture

## Purpose
AWS AppSync WebSocket broadcasting for real-time agent execution updates.

## Diagram

```mermaid
flowchart TB
    User["User Web App<br/>WebSocket client"]
    
    AppSync["AWS AppSync<br/>GraphQL API<br/>WebSocket endpoint"]
    
    StatusPublisher["Status Publisher Lambda<br/>Called by orchestrator"]
    
    Orchestrator["Step Functions<br/>Publishes at checkpoints"]
    
    Agents["Agent Lambdas<br/>Publish tool calls"]
    
    ConnectionTable[("DynamoDB<br/>appsync_connections<br/>PK user_id")]
    
    User -->|Step 1 Connect| AppSync
    AppSync -->|Step 2 Store connection_id| ConnectionTable
    
    User -->|Step 3 Subscribe| AppSync
    
    Orchestrator -->|Step 4 Publish status| StatusPublisher
    Agents -->|Step 5 Publish status| StatusPublisher
    
    StatusPublisher -->|Step 6 Get connection_id| ConnectionTable
    StatusPublisher -->|Step 7 Send message| AppSync
    AppSync -->|Step 8 Push via WebSocket| User

    classDef userBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef appsyncBox fill:#e0f7fa,stroke:#00838f,stroke-width:3px
    classDef publisherBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class User userBox
    class AppSync appsyncBox
    class StatusPublisher,Orchestrator,Agents,ConnectionTable publisherBox
```

## GraphQL Schema

```graphql
type Mutation {
  publishStatus(input: StatusInput!): Status
}

type Subscription {
  onStatusUpdate(userId: ID!): Status
    @aws_subscribe(mutations: ["publishStatus"])
}

type Status {
  jobId: ID!
  userId: ID!
  agentName: String
  status: String!
  message: String
  timestamp: AWSDateTime!
}

input StatusInput {
  jobId: ID!
  userId: ID!
  agentName: String
  status: String!
  message: String
}
```

## Status Types

- `loading_agents`: Orchestrator loading playbook
- `invoking_geo_agent`: Starting Geo Agent
- `calling_amazon_location`: Geo Agent using tool
- `agent_complete_geo_agent`: Geo Agent finished
- `validating`: Validation in progress
- `synthesizing`: Synthesis in progress
- `complete`: Job finished
- `error`: Job failed
