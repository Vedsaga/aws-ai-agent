# Requirements Document: DomainFlow Agentic Orchestration Platform

## Introduction

This document outlines the API requirements for "DomainFlow", a multi-agent orchestration platform designed to build and deploy complex, data-driven workflows. The system uses a unified architecture of three agent classes where administrators configure agents rather than building new APIs for each business problem.

### Core Agent Classes

1. **Data-Ingestion Agents**: CREATE new data by receiving unstructured input (text, speech) and outputting structured JSON saved as Report documents
2. **Data-Query Agents**: READ data by receiving natural language questions, searching Report documents, and returning synthesized answers
3. **Data-Management Agents**: UPDATE existing data by receiving natural language commands and merging JSON into existing Report documents

## Glossary

- **API Gateway**: AWS API Gateway service that routes HTTP requests to Lambda functions
- **Lambda Function**: AWS serverless compute function that handles API requests
- **CRUD**: Create, Read, Update, Delete operations
- **Ingestion Agent**: Agent configured with 'ingestion' class to CREATE data
- **Query Agent**: Agent configured with 'query' class to READ data
- **Management Agent**: Agent configured with 'management' class to UPDATE data
- **Domain**: Business configuration (e.g., civic_complaints) that groups agents into playbooks
- **Report**: Core JSON document in DynamoDB representing an incident, case, or data record
- **Query**: User-submitted natural language string for reading or updating data
- **Session**: Chat conversation context
- **JWT Token**: JSON Web Token for authentication
- **AppSync**: AWS real-time GraphQL API service
- **RDS (PostgreSQL)**: Structured, relational data storage for Agents, Domains, Users, Teams
- **DynamoDB (NoSQL)**: Flexible, high-volume data storage for Reports, Sessions, Messages
- **Playbook**: Agent execution graph defining how agents process data
- **Dependency Graph**: Visual representation of agent execution order and dependencies

## Architecture & Data Storage

### Hybrid Storage Strategy

**Amazon RDS (PostgreSQL)** - Structured, relational data requiring joins and transactional integrity:
- Tables: Users, Teams, AgentDefinitions (all 3 classes), DomainConfigurations

**Amazon DynamoDB (NoSQL)** - High-volume, dynamic data with flexible schema:
- Tables: Reports (core data documents), Sessions, Messages, QueryJobs

### Standard Metadata

All primary objects MUST include:
- `id`: string (uuid, primary key)
- `created_at`: ISO8601 timestamp
- `updated_at`: ISO8601 timestamp
- `created_by`: string (user_id)

## API Request/Response Specifications

### Agent Management API (Unified)

**Base Path:** `/api/v1/agents`

Provides a single set of endpoints to manage all three classes of agents.

**Create Agent (POST /api/v1/agents)**

Request Body:
```json
{
  "agent_name": "string (required)",
  "agent_class": "string (required, 'ingestion' | 'query' | 'management')",
  "system_prompt": "string (required)",
  "tools": ["string"] (optional, default: [], LLM is default),
  "agent_dependencies": ["string"] (optional, array of agent_ids),
  "max_output_keys": 5 (locked at 5),
  "output_schema": {object} (required, JSON schema, max 5 properties),
  "description": "string (optional)",
  "enabled": boolean (optional, default: true)
}
```

Response (201 Created):
```json
{
  "agent_id": "string",
  "agent_name": "string",
  "agent_class": "string",
  "version": number,
  "is_inbuilt": boolean,
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp",
  "created_by": "string"
}
```

**List Agents (GET /api/v1/agents)**

Query Parameters:
- `page`: number (optional, default: 1)
- `limit`: number (optional, default: 20)
- `agent_class`: string (optional, filter by 'ingestion'|'query'|'management')

Response (200 OK):
```json
{
  "agents": [
    {
      "agent_id": "string",
      "agent_name": "string",
      "agent_class": "string",
      "enabled": boolean,
      "is_inbuilt": boolean,
      "created_at": "ISO8601 timestamp",
      "created_by_me": boolean
    }
  ],
  "pagination": {
    "page": number,
    "limit": number,
    "total": number
  }
}
```

**Get Agent (GET /api/v1/agents/{agent_id})**

Response (200 OK):
```json
{
  "agent_id": "string",
  "agent_name": "string",
  "agent_class": "string",
  "system_prompt": "string",
  "tools": ["string"],
  "agent_dependencies": ["string"],
  "dependency_graph": {
    "nodes": [{"id": "string", "label": "string"}],
    "edges": [{"from": "string", "to": "string"}]
  },
  "max_output_keys": 5,
  "output_schema": {object},
  "description": "string",
  "enabled": boolean,
  "is_inbuilt": boolean,
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp",
  "version": number
}
```

**Update Agent (PUT /api/v1/agents/{agent_id})**

Request Body (all fields optional):
```json
{
  "agent_name": "string (optional)",
  "system_prompt": "string (optional)",
  "tools": ["string"] (optional),
  "agent_dependencies": ["string"] (optional),
  "output_schema": {object} (optional),
  "description": "string (optional)",
  "enabled": boolean (optional)
}
```

Response (200 OK): Same as Get Agent

**Delete Agent (DELETE /api/v1/agents/{agent_id})**

Response (200 OK):
```json
{
  "message": "Agent deleted successfully",
  "agent_id": "string"
}
```

---

### Domain Management API

**Base Path:** `/api/v1/domains`

Configures a Domain by assigning agents to each of the three playbooks.

**Create Domain (POST /api/v1/domains)**

Request Body:
```json
{
  "domain_id": "string (required, e.g., 'civic_complaints')",
  "domain_name": "string (required)",
  "description": "string (optional)",
  "ingestion_playbook": {
    "agent_execution_graph": {
      "nodes": ["string (agent_id)"],
      "edges": [{"from": "string", "to": "string"}]
    }
  } (required),
  "query_playbook": {
    "agent_execution_graph": {
      "nodes": ["string"],
      "edges": [{"from": "string", "to": "string"}]
    }
  } (required),
  "management_playbook": {
    "agent_execution_graph": {
      "nodes": ["string"],
      "edges": [{"from": "string", "to": "string"}]
    }
  } (required)
}
```

Response (201 Created):
```json
{
  "domain_id": "string",
  "domain_name": "string",
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp",
  "created_by": "string"
}
```

**List Domains (GET /api/v1/domains)**

Query Parameters: page, limit

Response (200 OK):
```json
{
  "domains": [
    {
      "domain_id": "string",
      "domain_name": "string",
      "description": "string",
      "id": "string",
      "created_at": "ISO8601 timestamp"
    }
  ],
  "pagination": {object}
}
```

**Get Domain (GET /api/v1/domains/{domain_id})**

Response (200 OK): Full domain configuration including all three playbooks

**Update Domain (PUT /api/v1/domains/{domain_id})**

Request Body: Same as Create (all fields optional)

**Delete Domain (DELETE /api/v1/domains/{domain_id})**

Response (200 OK): Confirmation message

---

### Report Submission API (The "Write" Endpoint)

**Base Path:** `/api/v1/reports`

Handles all data creation, routing unstructured input to the correct ingestion_playbook.

**Submit Report (POST /api/v1/reports)**

Request Body:
```json
{
  "domain_id": "string (required)",
  "text": "string (required)",
  "images": ["string"] (optional, array of image URLs),
  "source": "string (optional, default: 'web')"
}
```

Response (202 Accepted):
```json
{
  "job_id": "string",
  "incident_id": "string",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "ISO8601 timestamp"
}
```

**Get Report (GET /api/v1/reports/{incident_id})**

Response (200 OK):
```json
{
  "incident_id": "string",
  "domain_id": "string",
  "raw_text": "string",
  "status": "string",
  "ingestion_data": {
    "complaint_type": "string",
    "location_text": "string",
    "urgency": "string",
    "geo_location": {
      "type": "Point",
      "coordinates": [longitude, latitude]
    }
  },
  "management_data": {
    "task_details": {
      "assignee_id": "string",
      "priority": "string",
      "due_at": "ISO8601 timestamp"
    },
    "history": [
      {
        "status": "string",
        "timestamp": "ISO8601 timestamp",
        "by": "string"
      }
    ]
  },
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**List Reports (GET /api/v1/reports)**

Query Parameters:
- `page`: number (optional)
- `limit`: number (optional)
- `domain_id`: string (optional, filter by domain)
- `status`: string (optional, filter by status)

Response (200 OK):
```json
{
  "reports": [
    {
      "incident_id": "string",
      "domain_id": "string",
      "raw_text": "string",
      "status": "string",
      "created_at": "ISO8601 timestamp"
    }
  ],
  "pagination": {object}
}
```

**Update Report (PUT /api/v1/reports/{incident_id})**

Request Body (all optional):
```json
{
  "status": "string (optional)",
  "management_data": {object} (optional, merged into existing data)
}
```

**Delete Report (DELETE /api/v1/reports/{incident_id})**

Response (200 OK): Confirmation message

---

### Query & Management API (The "Read" & "Update" Endpoint)

**Base Path:** `/api/v1/queries`

Single endpoint handling all data interaction. Orchestrator routes questions to either query_playbook (read) or management_playbook (update).

**Submit Query (POST /api/v1/queries)**

Request Body:
```json
{
  "session_id": "string (required)",
  "domain_id": "string (required)",
  "question": "string (required, e.g., 'Show me pending potholes' OR 'Assign this to Team B')"
}
```

Response (202 Accepted):
```json
{
  "job_id": "string",
  "query_id": "string",
  "session_id": "string",
  "status": "accepted",
  "message": "Query submitted for processing",
  "timestamp": "ISO8601 timestamp"
}
```

**Get Query Result (GET /api/v1/queries/{query_id})**

Response (200 OK):
```json
{
  "job_id": "string",
  "query_id": "string",
  "question": "string",
  "status": "string ('processing'|'completed'|'failed')",
  "summary": "string",
  "map_data": {
    "map_action": "string (e.g., 'FIT_BOUNDS', 'ADD_MARKERS')",
    "data": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude]
          },
          "properties": {
            "incident_id": "string",
            "status": "string"
          }
        }
      ]
    }
  },
  "references_used": [
    {
      "type": "report",
      "reference_id": "string",
      "summary": "string",
      "status": "string",
      "location": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      }
    }
  ],
  "execution_log": [
    {
      "agent_id": "string",
      "agent_name": "string",
      "status": "string ('success'|'error'|'skipped'|'cached')",
      "timestamp": "ISO8601 timestamp",
      "reasoning": "string (agent's thought process)",
      "output": {object} (intermediate output passed to next agents),
      "error_message": "string (only if status is 'error')"
    }
  ],
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "completed_at": "ISO8601 timestamp"
}
```

**List Queries (GET /api/v1/queries)**

Query Parameters: page, limit, session_id (optional)

Response (200 OK):
```json
{
  "queries": [
    {
      "query_id": "string",
      "question": "string",
      "status": "string",
      "created_at": "ISO8601 timestamp"
    }
  ],
  "pagination": {object}
}
```

**Delete Query (DELETE /api/v1/queries/{query_id})**

Response (200 OK): Confirmation message

---

### Session Management API

**Base Path:** `/api/v1/sessions`

Manages chat history with embedded references for groundedness.

**Create Session (POST /api/v1/sessions)**

Request Body:
```json
{
  "domain_id": "string (required)",
  "title": "string (optional, default: 'New Session')"
}
```

Response (201 Created):
```json
{
  "session_id": "string",
  "domain_id": "string",
  "title": "string",
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Get Session (GET /api/v1/sessions/{session_id})**

Response (200 OK):
```json
{
  "session_id": "string",
  "title": "string",
  "domain_id": "string",
  "messages": [
    {
      "message_id": "string",
      "role": "string ('user'|'assistant')",
      "content": "string",
      "timestamp": "ISO8601 timestamp",
      "metadata": {
        "query_id": "string",
        "references": [
          {
            "type": "report",
            "reference_id": "string",
            "summary": "string",
            "status": "string",
            "location": {
              "type": "Point",
              "coordinates": [longitude, latitude]
            }
          }
        ]
      }
    }
  ],
  "id": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**List Sessions (GET /api/v1/sessions)**

Query Parameters: page, limit

Response (200 OK):
```json
{
  "sessions": [
    {
      "session_id": "string",
      "title": "string",
      "domain_id": "string",
      "message_count": number,
      "last_activity": "ISO8601 timestamp",
      "created_at": "ISO8601 timestamp"
    }
  ],
  "pagination": {object}
}
```

**Update Session (PUT /api/v1/sessions/{session_id})**

Request Body:
```json
{
  "title": "string (optional)"
}
```

**Delete Session (DELETE /api/v1/sessions/{session_id})**

Response (200 OK): Confirmation message

---

### Data Retrieval API (For Bulk Display)

**Base Path:** `/api/v1/data`

Read-only endpoints for populating UIs like map dashboards.

**Get Geographic Data (GET /api/v1/data/geo)**

Query Parameters:
- `domain_id`: string (required)
- `bounds`: string (optional, "west,south,east,north")

Response (200 OK):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "incident_id": "string",
        "status": "string"
      }
    }
  ]
}
```

**Get Aggregated Data (GET /api/v1/data/aggregated)**

Query Parameters:
- `domain_id`: string (required)
- `group_by`: string (required, e.g., 'status', 'ingestion_data.complaint_type')

Response (200 OK):
```json
{
  "aggregations": [
    {
      "key": "string",
      "count": number
    }
  ],
  "total": number
}
```

---

### Real-Time Communication API (AppSync)

**GraphQL Endpoint:** AppSync WebSocket URL

**Subscription:**
```graphql
subscription OnJobUpdate($sessionId: ID!) {
  onJobUpdate(sessionId: $sessionId) {
    jobId
    queryId
    sessionId
    status
    message
    timestamp
  }
}
```

**Status Types:**
- `loading_agents` - Loading playbook configuration
- `agent_invoking` - Agent starting execution
- `calling_tool` - Agent invoking a tool
- `agent_complete` - Agent finished successfully
- `agent_error` - Agent execution failed
- `validating` - Validating agent outputs
- `synthesizing` - Merging agent outputs
- `complete` - Processing complete
- `error` - Processing failed

## Requirements

### Requirement 1: Unified Agent Management API

**User Story:** As a system administrator, I want to manage all three classes of agents (ingestion, query, management) through a single API, so that I have a consistent interface for agent configuration.

#### Acceptance Criteria

1. WHEN an administrator sends a POST request to `/api/v1/agents` with agent_class 'ingestion', THE API Gateway SHALL create a new ingestion agent and return HTTP 201
2. WHEN an administrator sends a GET request to `/api/v1/agents?agent_class=query`, THE API Gateway SHALL return a filtered list of query agents with HTTP 200
3. WHEN an administrator sends a GET request to `/api/v1/agents/{agent_id}`, THE API Gateway SHALL return the agent details including dependency_graph with HTTP 200
4. WHEN an administrator sends a PUT request to `/api/v1/agents/{agent_id}`, THE API Gateway SHALL update the agent configuration and increment version number with HTTP 200
5. WHEN an administrator sends a DELETE request to `/api/v1/agents/{agent_id}` for a non-builtin agent, THE API Gateway SHALL remove the agent and return HTTP 200

### Requirement 2: Domain Configuration API

**User Story:** As a system administrator, I want to configure domains with three playbooks (ingestion, query, management), so that I can define how agents process data for each business context.

#### Acceptance Criteria

1. WHEN an administrator sends a POST request to `/api/v1/domains` with all three playbooks, THE API Gateway SHALL create a new domain configuration and return HTTP 201
2. WHEN an administrator sends a GET request to `/api/v1/domains`, THE API Gateway SHALL return a paginated list of all domains with HTTP 200
3. WHEN an administrator sends a GET request to `/api/v1/domains/{domain_id}`, THE API Gateway SHALL return the full domain configuration including all playbooks with HTTP 200
4. WHEN an administrator sends a PUT request to `/api/v1/domains/{domain_id}`, THE API Gateway SHALL update the domain playbooks and return HTTP 200
5. WHEN an administrator sends a DELETE request to `/api/v1/domains/{domain_id}`, THE API Gateway SHALL remove the domain and return HTTP 200

### Requirement 3: Report Submission API (Data Creation)

**User Story:** As an end user, I want to submit unstructured reports, so that the system can process and structure my data using ingestion agents.

#### Acceptance Criteria

1. WHEN a user sends a POST request to `/api/v1/reports` with domain_id and text, THE API Gateway SHALL accept the report and return HTTP 202 with job_id and incident_id
2. WHEN a user sends a GET request to `/api/v1/reports/{incident_id}`, THE API Gateway SHALL return the report with ingestion_data and management_data with HTTP 200
3. WHEN a user sends a GET request to `/api/v1/reports` with domain_id filter, THE API Gateway SHALL return a paginated list of reports for that domain with HTTP 200
4. WHEN a user sends a PUT request to `/api/v1/reports/{incident_id}` with management_data, THE API Gateway SHALL merge the data into the existing report and return HTTP 200
5. WHEN a user sends a DELETE request to `/api/v1/reports/{incident_id}`, THE API Gateway SHALL remove the report from DynamoDB and return HTTP 200

### Requirement 4: Query & Management API (Data Read/Update)

**User Story:** As an end user, I want to ask questions and issue commands in natural language, so that the system can read or update data using the appropriate agents.

#### Acceptance Criteria

1. WHEN a user sends a POST request to `/api/v1/queries` with a read intent question, THE Orchestrator SHALL route to query_playbook and return HTTP 202 with job_id and query_id
2. WHEN a user sends a POST request to `/api/v1/queries` with an update intent command, THE Orchestrator SHALL route to management_playbook and return HTTP 202
3. WHEN a user sends a GET request to `/api/v1/queries/{query_id}` for a completed query, THE API Gateway SHALL return summary, map_data, and references_used with HTTP 200
4. WHEN a user sends a GET request to `/api/v1/queries` with session_id filter, THE API Gateway SHALL return a paginated list of queries for that session with HTTP 200
5. WHEN a user sends a DELETE request to `/api/v1/queries/{query_id}`, THE API Gateway SHALL remove the query from DynamoDB and return HTTP 200

### Requirement 5: Session Management API

**User Story:** As an end user, I want to manage chat sessions with embedded references, so that I can track conversation history with groundedness to source data.

#### Acceptance Criteria

1. WHEN a user sends a POST request to `/api/v1/sessions` with domain_id, THE API Gateway SHALL create a new session and return HTTP 201 with session_id
2. WHEN a user sends a GET request to `/api/v1/sessions/{session_id}`, THE API Gateway SHALL return the session with all messages including metadata references with HTTP 200
3. WHEN a user sends a GET request to `/api/v1/sessions`, THE API Gateway SHALL return a paginated list of sessions with message_count and last_activity with HTTP 200
4. WHEN a user sends a PUT request to `/api/v1/sessions/{session_id}` with title, THE API Gateway SHALL update the session metadata and return HTTP 200
5. WHEN a user sends a DELETE request to `/api/v1/sessions/{session_id}`, THE API Gateway SHALL remove the session and all messages from DynamoDB and return HTTP 200

### Requirement 6: Data Retrieval API

**User Story:** As an end user, I want to retrieve geographic and aggregated data, so that I can populate map dashboards and visualizations.

#### Acceptance Criteria

1. WHEN a user sends a GET request to `/api/v1/data/geo` with domain_id and bounds, THE API Gateway SHALL return GeoJSON FeatureCollection with HTTP 200
2. WHEN a user sends a GET request to `/api/v1/data/aggregated` with domain_id and group_by, THE API Gateway SHALL return aggregated statistics with HTTP 200
3. WHEN the geo endpoint receives a request without bounds, THE API Gateway SHALL return all geographic data for the domain with HTTP 200
4. WHEN the aggregated endpoint receives an invalid group_by field, THE API Gateway SHALL return HTTP 400 with validation error
5. WHEN either endpoint receives a non-existent domain_id, THE API Gateway SHALL return HTTP 404 with error message

### Requirement 7: Real-Time Communication API

**User Story:** As an end user, I want to receive real-time updates during processing, so that I can see agent progress and results as they happen.

#### Acceptance Criteria

1. WHEN a user establishes a WebSocket connection to AppSync with session_id, THE AppSync API SHALL accept the subscription and maintain the connection
2. WHEN an agent starts processing in any playbook, THE Status Publisher Lambda SHALL publish a status update via AppSync GraphQL mutation
3. WHEN an agent completes processing, THE Status Publisher Lambda SHALL publish a completion status with results via AppSync
4. WHEN an error occurs during processing, THE Status Publisher Lambda SHALL publish an error status with details via AppSync
5. WHEN a user disconnects from AppSync, THE AppSync API SHALL close the WebSocket connection and clean up resources

### Requirement 8: Hybrid Data Storage

**User Story:** As a system architect, I want to use RDS for structured data and DynamoDB for flexible data, so that the system can handle both relational and dynamic data efficiently.

#### Acceptance Criteria

1. WHEN an agent or domain is created, THE system SHALL store the configuration in RDS PostgreSQL with relational integrity
2. WHEN a report is created, THE system SHALL store the document in DynamoDB with flexible schema for ingestion_data and management_data
3. WHEN a session is created, THE system SHALL store the session and messages in DynamoDB for high-volume chat data
4. WHEN a query needs to join agent and report data, THE system SHALL query RDS for agent definitions and DynamoDB for report documents
5. WHEN management agents update reports, THE system SHALL merge JSON data into DynamoDB without schema constraints

### Requirement 9: Agent Dependency Management with DAG Validation

**User Story:** As a system administrator, I want to define agent dependencies with circular dependency prevention, so that agents can execute in the correct order without infinite loops.

#### Acceptance Criteria

1. WHEN an administrator creates or updates an agent with agent_dependencies, THE system SHALL traverse the entire dependency tree and validate it forms a Directed Acyclic Graph (DAG)
2. WHEN a circular dependency is detected during agent creation, THE API SHALL return HTTP 400 Bad Request with error message identifying the circular path
3. WHEN an administrator retrieves an agent, THE API SHALL return a dependency_graph with nodes and edges showing execution flow
4. WHEN a domain playbook is created, THE system SHALL validate the agent_execution_graph is a valid DAG before saving
5. WHEN a playbook executes, THE Orchestrator SHALL respect the dependency graph and execute agents in topological order

### Requirement 10: Testing Infrastructure

**User Story:** As a developer, I want comprehensive API tests including AppSync WebSocket testing, so that I can verify all endpoints work correctly after changes.

#### Acceptance Criteria

1. WHEN a new API endpoint is created, THE developer SHALL add corresponding test cases to TEST.py
2. WHEN TEST.py is executed, THE test suite SHALL authenticate with Cognito and obtain a valid JWT token
3. WHEN TEST.py runs all tests, THE test suite SHALL report pass/fail status for each endpoint with colored output
4. WHEN TEST.py completes, THE test suite SHALL display a summary with total tests, passed, failed, and success rate
5. WHEN AppSync real-time functionality is tested, THE test suite SHALL establish a WebSocket connection, submit a query, and verify status updates are received

### Requirement 11: API Security

**User Story:** As a system administrator, I want API security controls, so that the system is protected from unauthorized access.

#### Acceptance Criteria

1. WHEN a request is made without a valid JWT token, THE API Gateway SHALL return HTTP 401 Unauthorized
2. WHEN a request contains invalid data, THE API Gateway SHALL return HTTP 400 Bad Request with validation errors
3. WHEN a user requests a resource they don't own, THE API Gateway SHALL return HTTP 403 Forbidden
4. WHEN a requested resource does not exist, THE API Gateway SHALL return HTTP 404 Not Found
5. WHEN a user's JWT token is valid, THE API Gateway SHALL extract tenant_id and user_id from the token claims

### Requirement 12: Standard Metadata Enforcement

**User Story:** As a system architect, I want all primary objects to include standard metadata, so that the system has consistent audit trails and versioning.

#### Acceptance Criteria

1. WHEN any primary object is created, THE system SHALL automatically add id, created_at, updated_at, and created_by fields
2. WHEN any primary object is updated, THE system SHALL automatically update the updated_at timestamp
3. WHEN an agent is updated, THE system SHALL increment the version number
4. WHEN a user queries their own resources, THE system SHALL include a created_by_me boolean flag
5. WHEN metadata fields are missing in a request, THE system SHALL reject the request with HTTP 400

### Requirement 13: Agent Output Caching (Memoization)

**User Story:** As a system architect, I want agent outputs to be cached during job execution, so that shared dependencies are computed only once for efficiency and consistency.

#### Acceptance Criteria

1. WHEN a playbook executes and an agent is reached in the dependency graph, THE Orchestrator SHALL cache the agent's output for the duration of that job
2. WHEN multiple agents depend on the same upstream agent, THE Orchestrator SHALL pass the cached output to all dependent agents without re-execution
3. WHEN an agent is executed, THE Orchestrator SHALL check the cache first and skip execution if output already exists
4. WHEN a job completes or fails, THE Orchestrator SHALL clear the cache for that job_id
5. WHEN an agent's output is cached, THE execution_log SHALL indicate whether the output was computed or retrieved from cache

### Requirement 14: Execution Logging and Reasoning Chain

**User Story:** As a developer and end user, I want to see the complete execution log with agent reasoning and intermediate outputs, so that I can debug issues and understand how answers were derived.

#### Acceptance Criteria

1. WHEN a query is executed, THE Orchestrator SHALL log each agent execution with agent_id, agent_name, status, timestamp, reasoning, and output
2. WHEN a query completes, THE GET /api/v1/queries/{query_id} endpoint SHALL return an execution_log array with all agent steps
3. WHEN an agent executes, THE Orchestrator SHALL capture the agent's reasoning text explaining its decision-making process
4. WHEN an agent produces output, THE Orchestrator SHALL store the intermediate output in the execution_log for debugging
5. WHEN the execution_log is returned, THE entries SHALL be ordered chronologically showing the execution flow

### Requirement 15: Graph Error Handling and Failure Propagation

**User Story:** As a system architect, I want robust error handling in agent execution graphs, so that failures are clearly reported and dependent agents are handled appropriately.

#### Acceptance Criteria

1. WHEN an agent fails during execution, THE Orchestrator SHALL mark the agent status as 'error' in the execution_log with error details
2. WHEN an agent fails, THE Orchestrator SHALL automatically mark all dependent agents as 'skipped' without executing them
3. WHEN any agent in a playbook fails, THE Orchestrator SHALL set the final job status to 'failed' and stop execution
4. WHEN an error occurs, THE execution_log SHALL clearly show which agent failed, the error message, and which agents were skipped
5. WHEN a query fails, THE GET /api/v1/queries/{query_id} endpoint SHALL return status 'failed' with the execution_log showing the failure point

### Requirement 16: Legacy API Cleanup

**User Story:** As a system administrator, I want to remove duplicate and legacy API implementations, so that the codebase is maintainable and consistent.

#### Acceptance Criteria

1. WHEN the new unified APIs are deployed and tested, THE old monolithic config API SHALL be deprecated
2. WHEN duplicate API handlers exist for the same functionality, THE system SHALL retain only the new implementation
3. WHEN legacy endpoints are removed, THE API Gateway SHALL return HTTP 410 Gone for deprecated endpoints
4. WHEN API cleanup is complete, THE codebase SHALL have no unused Lambda functions or API routes
5. WHEN documentation is updated, THE API documentation SHALL reflect only the new unified endpoints
