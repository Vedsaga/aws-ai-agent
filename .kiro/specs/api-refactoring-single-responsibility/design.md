# Design Document: DomainFlow Agentic Orchestration Platform

## Overview

This document outlines the technical design for refactoring the Multi-Agent Orchestration System API from a monolithic architecture to a microservices-based architecture following the single-responsibility principle. The new design implements a unified agent class system with three agent types (ingestion, query, management) and hybrid data storage (RDS + DynamoDB).

### Design Goals

1. **Single Responsibility**: Each API endpoint handles one specific domain concern
2. **Unified Agent Management**: Single API for all three agent classes
3. **Hybrid Storage**: RDS for structured data, DynamoDB for flexible documents
4. **DAG Validation**: Prevent circular dependencies in agent graphs
5. **Execution Observability**: Complete logging of agent reasoning and outputs
6. **Robust Error Handling**: Fail-fast with clear error propagation
7. **Real-Time Updates**: WebSocket subscriptions for live progress
8. **Grounded Conversations**: Message references link to source data

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │ Agents   │ Domains  │ Reports  │ Queries  │ Sessions     │  │
│  │ API      │ API      │ API      │ API      │ API          │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Lambda Functions                            │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │ Agent    │ Domain   │ Report   │ Query    │ Session      │  │
│  │ Handler  │ Handler  │ Handler  │ Handler  │ Handler      │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘  │
│                              │                                   │
│                              ▼                                   │
│                    ┌──────────────────┐                         │
│                    │  Orchestrator    │                         │
│                    │  Lambda          │                         │
│                    └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   RDS (PostgreSQL)        │   │   DynamoDB                │
│                           │   │                           │
│  - Users                  │   │  - Reports                │
│  - Teams                  │   │  - Sessions               │
│  - AgentDefinitions       │   │  - Messages               │
│  - DomainConfigurations   │   │  - QueryJobs              │
└───────────────────────────┘   └───────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  AppSync         │
                    │  (WebSocket)     │
                    └──────────────────┘
```

### Component Breakdown

**API Layer (API Gateway)**
- Routes HTTP requests to appropriate Lambda handlers
- Handles authentication via Cognito JWT
- Enforces rate limiting and request validation
- Returns standardized response envelopes

**Lambda Handlers**
- Agent Handler: CRUD operations for all agent classes
- Domain Handler: CRUD operations for domain configurations
- Report Handler: Submit and manage reports (CREATE data)
- Query Handler: Submit and manage queries (READ/UPDATE data)
- Session Handler: Manage chat sessions and messages
- Data Handler: Bulk data retrieval for dashboards

**Orchestrator Lambda**
- Executes agent playbooks based on dependency graphs
- Implements DAG validation and topological sorting
- Manages agent output caching (memoization)
- Logs execution steps with reasoning and outputs
- Handles error propagation and failure modes
- Publishes real-time status updates via AppSync

**Data Layer**
- RDS PostgreSQL: Structured, relational data
- DynamoDB: Flexible, high-volume documents
- AppSync: Real-time WebSocket subscriptions

## Components and Interfaces

### 1. Agent Management Service

**Responsibility**: Manage all three classes of agents (ingestion, query, management)

**Lambda Function**: `agent-handler.py`

**Key Operations**:
- Create agent with DAG validation
- List agents with filtering by class
- Get agent with dependency graph
- Update agent with circular dependency check
- Delete agent (only non-builtin)

**DAG Validation Algorithm**:
```python
def validate_dag(agent_id, dependencies, all_agents):
    """
    Validates that adding dependencies doesn't create cycles.
    Uses DFS to detect cycles in the dependency graph.
    """
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        # Get dependencies of current node
        node_deps = get_agent_dependencies(node, all_agents)
        
        for dep in node_deps:
            if dep not in visited:
                if has_cycle(dep):
                    return True
            elif dep in rec_stack:
                return True  # Cycle detected
        
        rec_stack.remove(node)
        return False
    
    # Check if adding new dependencies creates cycle
    for dep in dependencies:
        if has_cycle(dep):
            return False, f"Circular dependency detected: {agent_id} -> {dep}"
    
    return True, None
```

**Dependency Graph Generation**:
```python
def build_dependency_graph(agent_id, all_agents):
    """
    Builds a visual dependency graph for an agent.
    Returns nodes and edges for frontend visualization.
    """
    nodes = []
    edges = []
    visited = set()
    
    def traverse(node_id):
        if node_id in visited:
            return
        visited.add(node_id)
        
        agent = get_agent(node_id, all_agents)
        nodes.append({
            "id": node_id,
            "label": agent["agent_name"],
            "class": agent["agent_class"]
        })
        
        for dep_id in agent.get("agent_dependencies", []):
            edges.append({"from": dep_id, "to": node_id})
            traverse(dep_id)
    
    traverse(agent_id)
    return {"nodes": nodes, "edges": edges}
```

**Database Schema (RDS)**:
```sql
CREATE TABLE agent_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL,
    agent_name VARCHAR(200) NOT NULL,
    agent_class VARCHAR(20) NOT NULL CHECK (agent_class IN ('ingestion', 'query', 'management')),
    system_prompt TEXT NOT NULL,
    tools JSONB DEFAULT '[]',
    agent_dependencies JSONB DEFAULT '[]',
    max_output_keys INTEGER DEFAULT 5,
    output_schema JSONB NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    is_inbuilt BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_agents_tenant ON agent_definitions(tenant_id, agent_class);
CREATE INDEX idx_agents_enabled ON agent_definitions(enabled);
```

### 2. Domain Management Service

**Responsibility**: Configure domains with three playbooks (ingestion, query, management)

**Lambda Function**: `domain-handler.py`

**Key Operations**:
- Create domain with playbook validation
- List domains with pagination
- Get domain with full playbook details
- Update domain playbooks
- Delete domain

**Playbook Validation**:
```python
def validate_playbook(playbook, agent_class, all_agents):
    """
    Validates that a playbook's agent_execution_graph is a valid DAG
    and all agents belong to the correct class.
    """
    graph = playbook["agent_execution_graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    # Validate all agents exist and have correct class
    for agent_id in nodes:
        agent = get_agent(agent_id, all_agents)
        if not agent:
            return False, f"Agent not found: {agent_id}"
        if agent["agent_class"] != agent_class:
            return False, f"Agent {agent_id} is not a {agent_class} agent"
    
    # Validate DAG (no cycles)
    if has_cycle_in_graph(nodes, edges):
        return False, "Playbook contains circular dependencies"
    
    return True, None
```

**Database Schema (RDS)**:
```sql
CREATE TABLE domain_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id VARCHAR(100) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL,
    domain_name VARCHAR(200) NOT NULL,
    description TEXT,
    ingestion_playbook JSONB NOT NULL,
    query_playbook JSONB NOT NULL,
    management_playbook JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_domains_tenant ON domain_configurations(tenant_id);
```

### 3. Report Submission Service

**Responsibility**: Handle data creation via ingestion agents

**Lambda Function**: `report-handler.py`

**Key Operations**:
- Submit report (triggers ingestion playbook)
- Get report with ingestion_data and management_data
- List reports with filtering
- Update report (merge management_data)
- Delete report

**Report Submission Flow**:
```
1. User submits report → POST /api/v1/reports
2. Report Handler validates domain_id and text
3. Creates incident_id and job_id
4. Stores initial report in DynamoDB
5. Invokes Orchestrator Lambda async with ingestion_playbook
6. Returns 202 Accepted with job_id and incident_id
7. Orchestrator executes ingestion agents
8. Updates report with ingestion_data
9. Publishes status updates via AppSync
```

**DynamoDB Schema**:
```json
{
  "TableName": "Reports",
  "KeySchema": [
    {"AttributeName": "incident_id", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "incident_id", "AttributeType": "S"},
    {"AttributeName": "tenant_id", "AttributeType": "S"},
    {"AttributeName": "domain_id", "AttributeType": "S"},
    {"AttributeName": "created_at", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "tenant-domain-index",
      "KeySchema": [
        {"AttributeName": "tenant_id", "KeyType": "HASH"},
        {"AttributeName": "domain_id", "KeyType": "RANGE"}
      ]
    },
    {
      "IndexName": "domain-created-index",
      "KeySchema": [
        {"AttributeName": "domain_id", "KeyType": "HASH"},
        {"AttributeName": "created_at", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

**Report Document Structure**:
```json
{
  "incident_id": "report-uuid-90123",
  "tenant_id": "tenant-uuid-456",
  "domain_id": "civic_complaints_v1",
  "raw_text": "There is a huge pothole...",
  "images": ["https://example.com/img.png"],
  "source": "mobile-app",
  "status": "completed",
  "ingestion_data": {
    "complaint_type": "pothole",
    "location_text": "Ataturk Boulevard",
    "urgency": "high",
    "geo_location": {
      "type": "Point",
      "coordinates": [36.9081, 37.1702]
    }
  },
  "management_data": {
    "task_details": {
      "assignee_id": "team-roads-b",
      "priority": "high",
      "due_at": "2025-10-23T16:10:00Z"
    },
    "history": [
      {"status": "pending", "timestamp": "2025-10-21T16:05:30Z", "by": "agent"},
      {"status": "assigned", "timestamp": "2025-10-21T16:10:15Z", "by": "user-uuid-admin"}
    ]
  },
  "id": "r-uuid-55555",
  "created_at": "2025-10-21T16:05:00Z",
  "updated_at": "2025-10-21T16:10:15Z",
  "created_by": "user-uuid-789"
}
```

### 4. Query & Management Service

**Responsibility**: Handle data read/update via query/management agents

**Lambda Function**: `query-handler.py`

**Key Operations**:
- Submit query (routes to query or management playbook)
- Get query result with execution_log
- List queries with filtering
- Delete query

**Mode Selection (Client-Side)**:
The user selects the mode in the UI:
- **Report Mode** → Routes to `/api/v1/reports` (ingestion playbook)
- **Ask Mode** → Routes to `/api/v1/queries` with mode='query' (query playbook)
- **Manage Mode** → Routes to `/api/v1/queries` with mode='management' (management playbook)

No server-side intent classification needed - the client explicitly specifies the mode.

**Query Submission Flow**:
```
1. User submits query → POST /api/v1/queries
2. Query Handler classifies intent (read vs update)
3. Creates query_id and job_id
4. Stores initial query in DynamoDB
5. Invokes Orchestrator with appropriate playbook
6. Returns 202 Accepted with job_id and query_id
7. Orchestrator executes agents with caching
8. Updates query with results and execution_log
9. Publishes status updates via AppSync
```

**DynamoDB Schema**:
```json
{
  "TableName": "QueryJobs",
  "KeySchema": [
    {"AttributeName": "query_id", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "query_id", "AttributeType": "S"},
    {"AttributeName": "session_id", "AttributeType": "S"},
    {"AttributeName": "created_at", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "session-created-index",
      "KeySchema": [
        {"AttributeName": "session_id", "KeyType": "HASH"},
        {"AttributeName": "created_at", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

### 5. Orchestrator Service

**Responsibility**: Execute agent playbooks with DAG traversal, caching, and logging

**Lambda Function**: `orchestrator.py`

**Core Algorithm**:
```python
class Orchestrator:
    def __init__(self, job_id, playbook, domain_id, tenant_id):
        self.job_id = job_id
        self.playbook = playbook
        self.domain_id = domain_id
        self.tenant_id = tenant_id
        self.cache = {}  # Agent output cache
        self.execution_log = []
        
    def execute(self, input_data):
        """
        Executes playbook agents in topological order with caching.
        """
        graph = self.playbook["agent_execution_graph"]
        nodes = graph["nodes"]
        edges = graph["edges"]
        
        # Build adjacency list and in-degree map
        adj_list = {node: [] for node in nodes}
        in_degree = {node: 0 for node in nodes}
        
        for edge in edges:
            adj_list[edge["from"]].append(edge["to"])
            in_degree[edge["to"]] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [node for node in nodes if in_degree[node] == 0]
        execution_order = []
        
        while queue:
            node = queue.pop(0)
            execution_order.append(node)
            
            for neighbor in adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Execute agents in order
        for agent_id in execution_order:
            try:
                result = self.execute_agent(agent_id, input_data)
                if result["status"] == "error":
                    # Fail fast: mark remaining agents as skipped
                    self.mark_remaining_as_skipped(execution_order, agent_id)
                    break
            except Exception as e:
                self.log_agent_error(agent_id, str(e))
                self.mark_remaining_as_skipped(execution_order, agent_id)
                break
        
        return {
            "status": "completed" if all(log["status"] in ["success", "cached"] for log in self.execution_log) else "failed",
            "execution_log": self.execution_log
        }
    
    def execute_agent(self, agent_id, input_data):
        """
        Executes a single agent with caching.
        """
        # Check cache first
        if agent_id in self.cache:
            self.log_agent_cached(agent_id)
            return self.cache[agent_id]
        
        # Get agent definition
        agent = get_agent_from_rds(agent_id)
        
        # Gather inputs from dependencies
        agent_input = self.gather_dependency_outputs(agent)
        agent_input.update(input_data)
        
        # Publish status update
        publish_status(self.job_id, "agent_invoking", f"Executing {agent['agent_name']}")
        
        # Invoke agent (call LLM with system_prompt and tools)
        result = invoke_agent_llm(agent, agent_input)
        
        # Cache output
        self.cache[agent_id] = result
        
        # Log execution
        self.log_agent_success(agent_id, agent["agent_name"], result)
        
        return result
    
    def gather_dependency_outputs(self, agent):
        """
        Collects outputs from all dependency agents.
        """
        inputs = {}
        for dep_id in agent.get("agent_dependencies", []):
            if dep_id in self.cache:
                inputs[f"{dep_id}_output"] = self.cache[dep_id]["output"]
        return inputs
    
    def log_agent_success(self, agent_id, agent_name, result):
        """
        Logs successful agent execution.
        """
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": result.get("reasoning", ""),
            "output": result.get("output", {})
        })
    
    def log_agent_cached(self, agent_id):
        """
        Logs cached agent output reuse.
        """
        agent = get_agent_from_rds(agent_id)
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent["agent_name"],
            "status": "cached",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": "Output retrieved from cache",
            "output": self.cache[agent_id]["output"]
        })
    
    def log_agent_error(self, agent_id, error_message):
        """
        Logs agent execution error.
        """
        agent = get_agent_from_rds(agent_id)
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent["agent_name"],
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": "",
            "output": None,
            "error_message": error_message
        })
    
    def mark_remaining_as_skipped(self, execution_order, failed_agent_id):
        """
        Marks all agents after failed agent as skipped.
        """
        skip_remaining = False
        for agent_id in execution_order:
            if agent_id == failed_agent_id:
                skip_remaining = True
                continue
            if skip_remaining:
                agent = get_agent_from_rds(agent_id)
                self.execution_log.append({
                    "agent_id": agent_id,
                    "agent_name": agent["agent_name"],
                    "status": "skipped",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reasoning": f"Skipped due to failure of {failed_agent_id}",
                    "output": None
                })
```

### 6. Session Management Service

**Responsibility**: Manage chat sessions with grounded message references

**Lambda Function**: `session-handler.py`

**Key Operations**:
- Create session
- Get session with messages
- List sessions
- Update session metadata
- Delete session and messages

**DynamoDB Schema**:
```json
{
  "TableName": "Sessions",
  "KeySchema": [
    {"AttributeName": "session_id", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "session_id", "AttributeType": "S"},
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "last_activity", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-activity-index",
      "KeySchema": [
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "last_activity", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

```json
{
  "TableName": "Messages",
  "KeySchema": [
    {"AttributeName": "message_id", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "message_id", "AttributeType": "S"},
    {"AttributeName": "session_id", "AttributeType": "S"},
    {"AttributeName": "timestamp", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "session-timestamp-index",
      "KeySchema": [
        {"AttributeName": "session_id", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
      ]
    }
  ]
}
```

**Message Grounding**:
```python
def create_assistant_message(session_id, query_result):
    """
    Creates an assistant message with references to source data.
    """
    message = {
        "message_id": f"msg-{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "role": "assistant",
        "content": query_result["summary"],
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "query_id": query_result["query_id"],
            "references": query_result["references_used"]
        }
    }
    
    # Store in DynamoDB
    messages_table.put_item(Item=message)
    
    # Update session last_activity
    sessions_table.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET last_activity = :timestamp",
        ExpressionAttributeValues={":timestamp": message["timestamp"]}
    )
    
    return message
```

### 7. Data Retrieval Service

**Responsibility**: Bulk data retrieval for dashboards

**Lambda Function**: `data-handler.py`

**Key Operations**:
- Get geographic data (GeoJSON)
- Get aggregated statistics

**Geographic Data Query**:
```python
def get_geo_data(domain_id, bounds=None):
    """
    Retrieves reports as GeoJSON for map display.
    """
    # Query DynamoDB
    if bounds:
        # Parse bounds: "west,south,east,north"
        west, south, east, north = map(float, bounds.split(','))
        
        # Query with geo filter
        response = reports_table.query(
            IndexName='domain-created-index',
            KeyConditionExpression='domain_id = :domain_id',
            FilterExpression='ingestion_data.geo_location.coordinates[0] BETWEEN :west AND :east AND ingestion_data.geo_location.coordinates[1] BETWEEN :south AND :north',
            ExpressionAttributeValues={
                ':domain_id': domain_id,
                ':west': west,
                ':east': east,
                ':south': south,
                ':north': north
            }
        )
    else:
        # Query all reports for domain
        response = reports_table.query(
            IndexName='domain-created-index',
            KeyConditionExpression='domain_id = :domain_id',
            ExpressionAttributeValues={':domain_id': domain_id}
        )
    
    # Convert to GeoJSON
    features = []
    for report in response['Items']:
        if 'geo_location' in report.get('ingestion_data', {}):
            features.append({
                "type": "Feature",
                "geometry": report['ingestion_data']['geo_location'],
                "properties": {
                    "incident_id": report['incident_id'],
                    "status": report['status']
                }
            })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }
```

**Aggregated Data Query**:
```python
def get_aggregated_data(domain_id, group_by):
    """
    Aggregates reports by a field (e.g., status, complaint_type).
    """
    # Query all reports for domain
    response = reports_table.query(
        IndexName='domain-created-index',
        KeyConditionExpression='domain_id = :domain_id',
        ExpressionAttributeValues={':domain_id': domain_id}
    )
    
    # Aggregate by field
    aggregations = {}
    total = 0
    
    for report in response['Items']:
        # Extract field value (supports nested paths)
        value = extract_field(report, group_by)
        
        if value:
            aggregations[value] = aggregations.get(value, 0) + 1
            total += 1
    
    # Convert to array
    result = [
        {"key": key, "count": count}
        for key, count in aggregations.items()
    ]
    
    return {
        "aggregations": result,
        "total": total
    }
```

## Data Models

### RDS PostgreSQL Tables

**Users Table**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    cognito_sub VARCHAR(255) UNIQUE NOT NULL,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

**Teams Table**:
```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(200) NOT NULL,
    tenant_id UUID NOT NULL,
    members JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

**Tenants Table**:
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### DynamoDB Tables

**Reports Table**:
- Partition Key: `incident_id` (String)
- GSI: `tenant-domain-index` (tenant_id, domain_id)
- GSI: `domain-created-index` (domain_id, created_at)
- Attributes: incident_id, tenant_id, domain_id, raw_text, images, source, status, ingestion_data, management_data, id, created_at, updated_at, created_by

**Sessions Table**:
- Partition Key: `session_id` (String)
- GSI: `user-activity-index` (user_id, last_activity)
- Attributes: session_id, user_id, tenant_id, domain_id, title, message_count, id, created_at, updated_at, last_activity

**Messages Table**:
- Partition Key: `message_id` (String)
- GSI: `session-timestamp-index` (session_id, timestamp)
- Attributes: message_id, session_id, role, content, timestamp, metadata

**QueryJobs Table**:
- Partition Key: `query_id` (String)
- GSI: `session-created-index` (session_id, created_at)
- Attributes: query_id, job_id, session_id, tenant_id, domain_id, question, status, summary, map_data, references_used, execution_log, id, created_at, completed_at

## Error Handling

### Error Response Format

All API errors follow a standardized format:

```json
{
  "error": "Error message",
  "error_code": "ERR_400",
  "timestamp": "2025-10-21T16:00:00Z",
  "details": {
    "field": "agent_dependencies",
    "reason": "Circular dependency detected: agent-A -> agent-B -> agent-A"
  }
}
```

### HTTP Status Codes

- **200 OK**: Successful GET, PUT, DELETE
- **201 Created**: Successful POST
- **202 Accepted**: Async job submitted
- **400 Bad Request**: Invalid input, validation error
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: User doesn't own resource
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Circular dependency detected
- **410 Gone**: Deprecated endpoint
- **500 Internal Server Error**: Unexpected error

### Orchestrator Error Handling

**Fail-Fast Strategy**:
1. Agent fails → Log error with details
2. Mark all dependent agents as "skipped"
3. Set job status to "failed"
4. Publish error status via AppSync
5. Return execution_log showing failure point

**Example Execution Log with Error**:
```json
{
  "execution_log": [
    {
      "agent_id": "agent-uuid-geo",
      "agent_name": "Geo Locator",
      "status": "success",
      "timestamp": "2025-10-21T16:08:01Z",
      "reasoning": "Extracted location from text",
      "output": {"geo_location": {"type": "Point", "coordinates": [36.9, 37.1]}}
    },
    {
      "agent_id": "agent-uuid-classifier",
      "agent_name": "Complaint Classifier",
      "status": "error",
      "timestamp": "2025-10-21T16:08:03Z",
      "reasoning": "",
      "output": null,
      "error_message": "LLM API timeout after 30 seconds"
    },
    {
      "agent_id": "agent-uuid-priority",
      "agent_name": "Priority Assessor",
      "status": "skipped",
      "timestamp": "2025-10-21T16:08:03Z",
      "reasoning": "Skipped due to failure of agent-uuid-classifier",
      "output": null
    }
  ]
}
```

## Testing Strategy

### Unit Tests

**Agent Handler Tests**:
- Test DAG validation with circular dependencies
- Test agent creation with valid/invalid schemas
- Test dependency graph generation
- Test agent filtering by class

**Orchestrator Tests**:
- Test topological sort with various graphs
- Test agent output caching
- Test error propagation
- Test execution log generation

**Domain Handler Tests**:
- Test playbook validation
- Test agent class verification
- Test DAG validation in playbooks

### Integration Tests

**End-to-End Report Flow**:
1. Submit report via POST /api/v1/reports
2. Verify 202 response with job_id
3. Poll GET /api/v1/reports/{incident_id} until status = "completed"
4. Verify ingestion_data is populated
5. Verify execution_log shows all agents

**End-to-End Query Flow**:
1. Create session via POST /api/v1/sessions
2. Submit query via POST /api/v1/queries
3. Verify 202 response with query_id
4. Poll GET /api/v1/queries/{query_id} until status = "completed"
5. Verify summary, map_data, references_used
6. Verify execution_log shows agent reasoning

**AppSync WebSocket Test**:
```python
def test_appsync_realtime():
    # Establish WebSocket connection
    subscription = appsync_client.subscribe(
        query="""
        subscription OnJobUpdate($sessionId: ID!) {
          onJobUpdate(sessionId: $sessionId) {
            jobId
            status
            message
          }
        }
        """,
        variables={"sessionId": session_id}
    )
    
    # Submit query
    response = requests.post(
        f"{API_BASE_URL}/api/v1/queries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": session_id,
            "domain_id": "civic_complaints_v1",
            "question": "Show me all potholes"
        }
    )
    
    # Collect status updates
    updates = []
    for update in subscription:
        updates.append(update)
        if update["status"] in ["complete", "error"]:
            break
    
    # Verify status progression
    assert "agent_invoking" in [u["status"] for u in updates]
    assert "complete" in [u["status"] for u in updates]
```

### TEST.py Updates

Add new test cases:
- Test agent CRUD operations
- Test domain CRUD operations
- Test report submission and retrieval
- Test query submission with execution_log
- Test session and message management
- Test AppSync WebSocket subscriptions
- Test DAG validation errors
- Test error propagation in orchestrator

## Deployment Architecture

### CDK Stack Structure

```
infrastructure/lib/stacks/
├── api-gateway-stack.ts       # API Gateway with routes
├── agent-api-stack.ts          # Agent management Lambda
├── domain-api-stack.ts         # Domain management Lambda
├── report-api-stack.ts         # Report submission Lambda
├── query-api-stack.ts          # Query submission Lambda
├── session-api-stack.ts        # Session management Lambda
├── data-api-stack.ts           # Data retrieval Lambda
├── orchestrator-stack.ts       # Orchestrator Lambda
├── realtime-stack.ts           # AppSync (existing)
├── storage-stack.ts            # RDS + DynamoDB
└── auth-stack.ts               # Cognito (existing)
```

### Lambda Function Configuration

**Agent Handler**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 30 seconds
- Environment: RDS_CLUSTER_ARN, DB_SECRET_ARN
- Permissions: RDS Data API, Secrets Manager

**Domain Handler**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 30 seconds
- Environment: RDS_CLUSTER_ARN, DB_SECRET_ARN
- Permissions: RDS Data API, Secrets Manager

**Report Handler**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 30 seconds
- Environment: REPORTS_TABLE, ORCHESTRATOR_FUNCTION
- Permissions: DynamoDB, Lambda Invoke

**Query Handler**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 30 seconds
- Environment: QUERIES_TABLE, ORCHESTRATOR_FUNCTION
- Permissions: DynamoDB, Lambda Invoke

**Session Handler**:
- Runtime: Python 3.11
- Memory: 256 MB
- Timeout: 15 seconds
- Environment: SESSIONS_TABLE, MESSAGES_TABLE
- Permissions: DynamoDB

**Data Handler**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 30 seconds
- Environment: REPORTS_TABLE
- Permissions: DynamoDB

**Orchestrator**:
- Runtime: Python 3.11
- Memory: 1024 MB
- Timeout: 300 seconds (5 minutes)
- Environment: RDS_CLUSTER_ARN, DB_SECRET_ARN, REPORTS_TABLE, QUERIES_TABLE, STATUS_PUBLISHER_FUNCTION
- Permissions: RDS Data API, DynamoDB, Lambda Invoke, Bedrock, Comprehend

### API Gateway Routes

```typescript
// Agent API
api.root.addResource('agents')
  .addMethod('POST', agentHandler)  // Create agent
  .addMethod('GET', agentHandler);  // List agents

api.root.resourceForPath('/agents/{agent_id}')
  .addMethod('GET', agentHandler)    // Get agent
  .addMethod('PUT', agentHandler)    // Update agent
  .addMethod('DELETE', agentHandler); // Delete agent

// Domain API
api.root.addResource('domains')
  .addMethod('POST', domainHandler)
  .addMethod('GET', domainHandler);

api.root.resourceForPath('/domains/{domain_id}')
  .addMethod('GET', domainHandler)
  .addMethod('PUT', domainHandler)
  .addMethod('DELETE', domainHandler);

// Report API
api.root.addResource('reports')
  .addMethod('POST', reportHandler)
  .addMethod('GET', reportHandler);

api.root.resourceForPath('/reports/{incident_id}')
  .addMethod('GET', reportHandler)
  .addMethod('PUT', reportHandler)
  .addMethod('DELETE', reportHandler);

// Query API
api.root.addResource('queries')
  .addMethod('POST', queryHandler)
  .addMethod('GET', queryHandler);

api.root.resourceForPath('/queries/{query_id}')
  .addMethod('GET', queryHandler)
  .addMethod('DELETE', queryHandler);

// Session API
api.root.addResource('sessions')
  .addMethod('POST', sessionHandler)
  .addMethod('GET', sessionHandler);

api.root.resourceForPath('/sessions/{session_id}')
  .addMethod('GET', sessionHandler)
  .addMethod('PUT', sessionHandler)
  .addMethod('DELETE', sessionHandler);

// Data API
api.root.addResource('data')
  .addResource('geo')
  .addMethod('GET', dataHandler);

api.root.resourceForPath('/data/aggregated')
  .addMethod('GET', dataHandler);
```

### Migration Strategy

**Phase 1: Deploy New APIs (Parallel)**
1. Deploy new Lambda functions
2. Deploy new API Gateway routes
3. Keep old config API running
4. Test new APIs thoroughly

**Phase 2: Migrate Data**
1. Create RDS tables (agent_definitions, domain_configurations)
2. Migrate existing agents from DynamoDB to RDS
3. Migrate existing domains from DynamoDB to RDS
4. Verify data integrity

**Phase 3: Update Frontend**
1. Update API client to use new endpoints
2. Test all frontend flows
3. Deploy frontend changes

**Phase 4: Deprecate Old APIs**
1. Mark old /api/v1/config endpoint as deprecated
2. Return HTTP 410 Gone with migration message
3. Remove old Lambda functions after 30 days
4. Clean up unused DynamoDB tables

## Security Considerations

### Authentication & Authorization

**JWT Token Validation**:
- All requests require valid Cognito JWT token
- Token must contain `sub` (user_id) and `custom:tenant_id` claims
- API Gateway Lambda authorizer validates token

**Tenant Isolation**:
- All queries filtered by tenant_id
- Users can only access resources in their tenant
- Cross-tenant access returns 403 Forbidden

**Resource Ownership**:
- Users can only modify resources they created
- Builtin agents cannot be deleted
- Admin role can modify all resources

### Input Validation

**Agent Creation**:
- Validate agent_class is one of: ingestion, query, management
- Validate output_schema has max 5 properties
- Validate agent_dependencies exist
- Validate no circular dependencies

**Report Submission**:
- Validate text length ≤ 10,000 characters
- Validate images array ≤ 5 URLs
- Validate domain_id exists

**Query Submission**:
- Validate question length ≤ 1,000 characters
- Validate session_id exists
- Validate domain_id exists

### Rate Limiting

**API Gateway Throttling**:
- Rate limit: 100 requests/second per user
- Burst limit: 200 requests
- Quota: 10,000 requests/day per user

**Lambda Concurrency**:
- Reserved concurrency: 50 per handler
- Orchestrator: 100 concurrent executions

## Monitoring & Observability

### CloudWatch Metrics

**API Gateway**:
- Request count by endpoint
- Error rate (4xx, 5xx)
- Latency (p50, p95, p99)

**Lambda Functions**:
- Invocation count
- Error count
- Duration
- Throttles

**DynamoDB**:
- Read/write capacity units
- Throttled requests
- Item count

**RDS**:
- CPU utilization
- Database connections
- Query latency

### CloudWatch Logs

**Structured Logging**:
```python
logger.info("Agent execution started", extra={
    "job_id": job_id,
    "agent_id": agent_id,
    "agent_name": agent_name,
    "tenant_id": tenant_id
})
```

**Log Groups**:
- `/aws/lambda/agent-handler`
- `/aws/lambda/domain-handler`
- `/aws/lambda/report-handler`
- `/aws/lambda/query-handler`
- `/aws/lambda/session-handler`
- `/aws/lambda/orchestrator`

### X-Ray Tracing

Enable X-Ray for:
- All Lambda functions
- API Gateway
- DynamoDB operations
- RDS Data API calls

### Alarms

**Critical Alarms**:
- Lambda error rate > 5%
- API Gateway 5xx rate > 1%
- Orchestrator timeout rate > 10%
- DynamoDB throttling > 0

**Warning Alarms**:
- Lambda duration > 25 seconds
- API Gateway latency > 2 seconds
- RDS CPU > 80%
- DynamoDB read/write capacity > 80%

## Performance Optimization

### Caching Strategy

**Agent Output Caching**:
- In-memory cache during job execution
- Cleared after job completion
- Reduces redundant LLM calls

**API Response Caching**:
- API Gateway caching for GET endpoints
- TTL: 5 minutes for list endpoints
- TTL: 1 minute for detail endpoints

**Database Query Optimization**:
- Use GSIs for common query patterns
- Batch get operations where possible
- Connection pooling for RDS

### Async Processing

**Report Submission**:
- Return 202 immediately
- Process in background via Orchestrator
- Publish status updates via AppSync

**Query Submission**:
- Return 202 immediately
- Execute agents asynchronously
- Stream results via WebSocket

### Pagination

**List Endpoints**:
- Default page size: 20
- Max page size: 100
- Return pagination metadata with next/prev links

## Leveraging Existing Infrastructure

### What's Already Deployed

**API Gateway & Lambda**:
- ✅ API Gateway with `/api/v1` base path
- ✅ Lambda authorizer with Cognito JWT validation
- ✅ Config Handler Lambda (monolithic - to be refactored)
- ✅ Ingest Handler Lambda (basic version)
- ✅ Query Handler Lambda (basic version)
- ✅ Data Handler Lambda (broken - needs fixing)
- ✅ Tools Handler Lambda

**Orchestration**:
- ✅ Step Functions state machine with 8 Lambda functions
- ✅ Load Playbook, Load Dependency Graph, Build Execution Plan
- ✅ Agent Invoker, Result Aggregator, Validator, Synthesizer, Save Results
- ⚠️ **Needs Update**: Add caching, execution logging, error propagation

**Data Layer**:
- ✅ RDS Aurora Serverless v2 (PostgreSQL 15.4)
- ✅ DynamoDB: Configurations, UserSessions, ToolCatalog, ToolPermissions
- ❌ **Missing**: Reports, Sessions, Messages, QueryJobs tables
- ❌ **Missing**: RDS tables for AgentDefinitions, DomainConfigurations

**Real-Time**:
- ✅ AppSync GraphQL API with WebSocket subscriptions
- ✅ Status Publisher Lambda

**Storage**:
- ✅ S3 Evidence Bucket for images
- ✅ S3 Config Backup Bucket

### What Needs to Be Built

**New Lambda Functions**:
1. **Agent Handler** - Unified agent management with DAG validation
2. **Domain Handler** - Domain configuration with playbook validation
3. **Session Handler** - Chat session and message management

**Database Changes**:
1. **RDS Tables**: Create agent_definitions, domain_configurations, users, teams, tenants
2. **DynamoDB Tables**: Create Reports, Sessions, Messages, QueryJobs
3. **Data Migration**: Move existing agents/domains from DynamoDB Configurations to RDS

**Orchestrator Updates**:
1. Add agent output caching (memoization)
2. Add execution logging with reasoning
3. Add error propagation and fail-fast logic
4. Update to use RDS for agent/domain lookups

**API Gateway Updates**:
1. Add `/api/v1/agents` routes
2. Add `/api/v1/domains` routes
3. Add `/api/v1/sessions` routes
4. Update `/api/v1/reports` to use new schema
5. Update `/api/v1/queries` to accept mode parameter
6. Deprecate old `/api/v1/config` endpoint

### AWS Services for Hackathon Requirements

**LLM (Required)**:
- ✅ **Amazon Bedrock** - Already integrated
  - Claude 3 Sonnet for orchestration
  - Nova Micro for agents
  - Nova Pro for synthesis

**AWS Services (Required - At least 1)**:
- ✅ **Amazon Bedrock AgentCore** - Using primitives for agent execution
- ✅ **Amazon Bedrock/Nova** - Using Nova models for agents
- ✅ **AWS Lambda** - All agent logic runs in Lambda
- ✅ **Amazon API Gateway** - REST API endpoints
- ✅ **Amazon S3** - Evidence storage

**AI Agent Qualification (Required)**:
- ✅ **Reasoning LLMs** - Bedrock models for decision-making
- ✅ **Autonomous Capabilities** - Agents execute without human input
- ✅ **Integrates APIs/Tools** - Bedrock, Comprehend, Location Service, Web Search
- ✅ **Multi-Agent** - Orchestrator coordinates multiple agents

**Helper Services (Optional)**:
- ✅ **AWS Lambda** - Core compute
- ✅ **Amazon S3** - Storage
- ✅ **Amazon API Gateway** - API layer
- ✅ **Amazon DynamoDB** - NoSQL storage
- ✅ **Amazon RDS** - Relational storage
- ✅ **AWS Step Functions** - Orchestration workflow
- ✅ **Amazon AppSync** - Real-time updates
- ✅ **Amazon Cognito** - Authentication

### Reusable Components

**Keep As-Is**:
- API Gateway configuration
- Lambda authorizer
- Cognito user pool
- AppSync API
- Status Publisher Lambda
- Step Functions state machine structure
- S3 buckets
- VPC and networking

**Refactor**:
- Config Handler → Split into Agent Handler + Domain Handler
- Ingest Handler → Update to use new Reports table
- Query Handler → Update to accept mode parameter
- Data Handler → Fix and update to use new schema
- Orchestrator Lambdas → Add caching, logging, error handling

**Add New**:
- Session Handler Lambda
- RDS tables for agents/domains
- DynamoDB tables for reports/sessions/messages/queries
- DAG validation logic
- Agent output caching
- Execution logging

## Summary

This design implements a robust, scalable API architecture with:

✅ **Unified Agent Management** - Single API for all agent classes
✅ **Hybrid Storage** - RDS for structured data, DynamoDB for flexible documents
✅ **DAG Validation** - Prevent circular dependencies
✅ **Agent Caching** - Memoization for efficiency
✅ **Execution Logging** - Complete observability with reasoning chains
✅ **Error Handling** - Fail-fast with clear propagation
✅ **Real-Time Updates** - AppSync WebSocket subscriptions
✅ **Grounded Conversations** - Message references to source data
✅ **Security** - JWT authentication, tenant isolation, input validation
✅ **Testing** - Comprehensive unit and integration tests
✅ **Monitoring** - CloudWatch metrics, logs, X-Ray tracing
✅ **Performance** - Caching, async processing, pagination

The design is ready for implementation.
