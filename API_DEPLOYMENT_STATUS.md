---
# Requirements Document: Agentic Orchestration Platform

### 1. Introduction & Core Concept

This document outlines the API requirements for a "DomainFlow" platform, a multi-agent system designed to build and deploy complex, data-driven workflows.

The system is built on a unified architecture of three agent classes. An administrator does not build new APIs for new business problems (e.g., "tasks"); instead, they configure a new agent of the appropriate class.

* **1. Data-Ingestion Agents:** Their purpose is to **CREATE** new data. They receive unstructured input (text, speech) and output a structured JSON object, which is then saved as a new `Report` document.
* **2. Data-Query Agents:** Their purpose is to **READ** data. They receive a natural language question, search the database for existing `Report` documents, and return a synthesized answer and the data they used.
* **3. Data-Management Agents:** Their purpose is to **UPDATE** existing data. They receive a natural language command (e.g., "assign this task"), and their output is a JSON object that is *merged* into an existing `Report` document.

### 2. Glossary

- **API Gateway**: AWS API Gateway service.
- **Lambda Function**: AWS serverless compute function.
- **CRUD**: Create, Read, Update, Delete operations.
- **Ingestion Agent**: An agent configured with the `ingestion` class to **CREATE** data.
- **Query Agent**: An agent configured with the `query` class to **READ** data.
- **Management Agent**: An agent configured with the `management` class to **UPDATE** data.
- **Domain**: A business configuration (e.g., `civic_complaints`) that groups agents into playbooks.
- **Report**: The core JSON document in DynamoDB representing an incident, case, or data record.
- **Query**: A user-submitted natural language string.
- **Session**: A chat conversation context.
- **JWT Token**: JSON Web Token for authentication.
- **AppSync**: AWS real-time GraphQL API service.
- **RDS (PostgreSQL)**: Used for structured, relational data (Agents, Domains, Users, Teams).
- **DynamoDB (NoSQL)**: Used for flexible, high-volume data (Reports, Sessions, Messages).

### 3. Architecture & Data Storage

The system will use a **hybrid data storage** strategy:

* **Amazon RDS (PostgreSQL):** Will be used for structured, relational data that requires joins and transactional integrity.
    * **Tables:** `Users`, `Teams`, `AgentDefinitions` (for all 3 classes), `DomainConfigurations`.
* **Amazon DynamoDB (NoSQL):** Will be used for high-volume, dynamic data. This flexible, schemaless model is critical for allowing `Management-Agents` to add any JSON data (e.g., `task_details`, `prescription_details`) to a report.
    * **Tables:** `Reports` (the core data documents), `Sessions`, `Messages`, `QueryJobs`.

### 4. Standard Metadata

All primary objects created in the system (Agents, Domains, Reports, etc.) **must** include the following metadata:
* `id`: "string" (uuid, primary key)
* `created_at`: "ISO8601 timestamp"
* `updated_at`: "ISO8601 timestamp"
* `created_by`: "string" (user_id)

---

### 5. API Request/Response Specifications

### 5.1. Agent Management API (Unified)

Provides a single set of endpoints to manage all three classes of agents.

**Base Path:** `/api/v1/agents`

**Create Agent (POST /api/v1/agents)**
* Request Body:
    ```jsonc
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
* Example Request:
    ```jsonc
    // Example of creating an "Ingestion" agent
    {
      "agent_name": "Pothole Report Extractor",
      "agent_class": "ingestion",
      "system_prompt": "You are an expert at extracting details about civic complaints. You must identify the 'type' and 'location' of the complaint.",
      "agent_dependencies": ["agent-uuid-geo-inbuilt"],
      "max_output_keys": 5,
      "output_schema": {
        "type": "object",
        "properties": {
          "complaint_type": {"type": "string"},
          "location_text": {"type": "string"},
          "urgency": {"type": "string", "enum": ["low", "medium", "high"]}
        },
        "required": ["complaint_type", "location_text"]
      },
      "description": "Extracts basic details for pothole reports."
    }
    ```
* Response (201 Created):
    ```json
    {
      "agent_id": "agent-uuid-12345",
      "agent_name": "Pothole Report Extractor",
      "agent_class": "ingestion",
      "version": 1,
      "is_inbuilt": false,
      "id": "a-uuid-98765",
      "created_at": "2025-10-21T15:30:00Z",
      "updated_at": "2025-10-21T15:30:00Z",
      "created_by": "user-uuid-admin"
    }
    ```

**List Agents (GET /api/v1/agents)**
* Query Parameters: `page` (number), `limit` (number), `agent_class` (string, e.g., 'query')
* Response (200 OK):
    ```json
    {
      "agents": [
        {
          "agent_id": "agent-uuid-12345",
          "agent_name": "Pothole Report Extractor",
          "agent_class": "ingestion",
          "enabled": true,
          "is_inbuilt": false,
          "created_at": "2025-10-21T15:30:00Z",
          "created_by_me": true
        },
        {
          "agent_id": "agent-uuid-geo-inbuilt",
          "agent_name": "Inbuilt Geo-Locator",
          "agent_class": "ingestion",
          "enabled": true,
          "is_inbuilt": true,
          "created_at": "2025-10-20T10:00:00Z",
          "created_by_me": false
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 2
      }
    }
    ```

**Get Agent (GET /api/v1/agents/{agent_id})**
* Response (200 OK):
    ```jsonc
    {
      "agent_id": "agent-uuid-12345",
      "agent_name": "Pothole Report Extractor",
      "agent_class": "ingestion",
      "system_prompt": "You are an expert at extracting details...",
      "tools": [],
      "agent_dependencies": ["agent-uuid-geo-inbuilt"],
      // The graph shows how agents are connected.
      "dependency_graph": {
        "nodes": [
          {"id": "agent-uuid-12345", "label": "Pothole Report Extractor"},
          {"id": "agent-uuid-geo-inbuilt", "label": "Inbuilt Geo-Locator"}
        ],
        "edges": [
          {"from": "agent-uuid-geo-inbuilt", "to": "agent-uuid-12345"}
        ]
      },
      "max_output_keys": 5,
      "output_schema": {
        "type": "object",
        "properties": { "complaint_type": {"type": "string"}, ... }
      },
      "description": "Extracts basic details for pothole reports.",
      "enabled": true,
      "is_inbuilt": false,
      "id": "a-uuid-98765",
      "created_at": "2025-10-21T15:30:00Z",
      "updated_at": "2025-10-21T15:35:00Z",
      "version": 2
    }
    ```
**Update Agent (PUT /api/v1/agents/{agent_id})**: Standard PUT, returns 200 OK with the updated Agent object.
**Delete Agent (DELETE /api/v1/agents/{agent_id})**: Standard DELETE, returns 200 OK with a confirmation.

---

### 5.2. Domain Management API

Configures a "Domain" by assigning agents to each of the three playbooks.

**Base Path:** `/api/v1/domains`

**Create Domain (POST /api/v1/domains)**
* Request Body:
    ```json
    {
      "domain_id": "string (required, e.g., 'civic_complaints')",
      "domain_name": "string (required)",
      "description": "string (optional)",
      "ingestion_playbook": {
    "agent_execution_graph": {
      "nodes": ["string" (agent_id, e.g., 'A', 'B', 'C', 'Geo', 'Entity')],
      "edges": [
        {"from": "Geo", "to": "A"},
        {"from": "Entity", "to": "A"},
        {"from": "Entity", "to": "B"},
        {"from": "A", "to": "C"},
        {"from": "B", "to": "C"}
      ]
    }
  } (required),
      "query_playbook": {
        "agent_execution_graph": { ... }
      } (required),
      "management_playbook": {
        "agent_execution_graph": { ... }
      } (required)
    }
    ```
* Example Request:
    ```jsonc
    // Creates a new domain for "Civic Complaints"
    {
      "domain_id": "civic_complaints_v1",
      "domain_name": "Civic Complaints (Nurdağı)",
      "description": "Manages potholes, streetlights, and garbage reports.",
      "ingestion_playbook": {
        "agent_execution_graph": {
          "nodes": ["agent-uuid-12345", "agent-uuid-geo-inbuilt"],
          "edges": [{"from": "agent-uuid-geo-inbuilt", "to": "agent-uuid-12345"}]
        }
      },
      "query_playbook": {
        "agent_execution_graph": {
          "nodes": ["agent-uuid-query-where", "agent-uuid-query-howmany"],
          "edges": [] // Parallel execution
        }
      },
      "management_playbook": {
        "agent_execution_graph": {
          "nodes": ["agent-uuid-mgmt-assign"],
          "edges": []
        }
      }
    }
    ```
* Response (201 Created):
    ```json
    {
      "domain_id": "civic_complaints_v1",
      "domain_name": "Civic Complaints (Nurdağı)",
      "id": "d-uuid-11111",
      "created_at": "2025-10-21T16:00:00Z",
      "updated_at": "2025-10-21T16:00:00Z",
      "created_by": "user-uuid-admin"
    }
    ```
**List/Get/Update/Delete:** Standard CRUD operations.

---

### 5.3. Report Submission API (The "Write" Endpoint)

Handles all **data creation**, routing unstructured input to the correct `ingestion_playbook`.

**Base Path:** `/api/v1/reports`

**Submit Report (POST /api/v1/reports)**
* Request Body:
    ```json
    {
      "domain_id": "string (required)",
      "text": "string (required)",
      "images": ["string"] (optional, array of image URLs),
      "source": "string (optional, default: 'web')"
    }
    ```
* Example Request:
    ```json
    {
      "domain_id": "civic_complaints_v1",
      "text": "There is a huge pothole on Ataturk Boulevard, right in front of the main post office.",
      "images": ["[https://example.com/img_3afa44.png](https://example.com/img_3afa44.png)"],
      "source": "mobile-app"
    }
    ```
* Response (202 Accepted):
    ```json
    {
      "job_id": "job-uuid-abcde",
      "incident_id": "report-uuid-90123",
      "status": "accepted",
      "message": "Report submitted for processing",
      "timestamp": "2025-10-21T16:05:00Z"
    }
    ```

**Get Report (GET /api/v1/reports/{incident_id})**
* Response (200 OK):
    ```jsonc
    // Example of a report that has been ingested and later had a task assigned
    {
      "incident_id": "report-uuid-90123",
      "domain_id": "civic_complaints_v1",
      "raw_text": "There is a huge pothole on Ataturk Boulevard...",
      "status": "assigned",
      // Data created by the "Ingestion-Agent"
      "ingestion_data": {
        "complaint_type": "pothole",
        "location_text": "Ataturk Boulevard, main post office",
        "urgency": "high",
        "geo_location": {
          "type": "Point",
          "coordinates": [36.9081, 37.1702]
        }
      },
      // Data added later by a "Management-Agent"
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
      "updated_at": "2025-10-21T16:10:15Z"
    }
    ```
**List/Update/Delete:** Standard CRUD operations.

---

### 5.4. Query & Management API (The "Read" & "Update" Endpoint)

This single endpoint handles all **data interaction**. The orchestrator routes the user's "question" to either the `query_playbook` (for read intents) or the `management_playbook` (for update intents).

**Base Path:** `/api/v1/queries`

**Submit Query (POST /api/v1/queries)**
* Request Body:
    ```json
    {
      "session_id": "string (required)",
      "domain_id": "string (required)",
      "question": "string (required, e.g., 'Show me pending potholes' OR 'Assign this to Team B')"
    }
    ```
* Example Request (A "Read" Query):
    ```json
    {
      "session_id": "session-uuid-777",
      "domain_id": "civic_complaints_v1",
      "question": "Show me all high-priority potholes in Nurdağı."
    }
    ```
* Example Request (An "Update" Command):
    ```json
    {
      "session_id": "session-uuid-777",
      "domain_id": "civic_complaints_v1",
      "question": "Assign report-uuid-90123 to 'Team B' with high priority. Set it due in 48 hours."
    }
    ```
* Response (202 Accepted):
    ```json
    {
      "job_id": "job-uuid-fghij",
      "query_id": "query-uuid-456",
      "session_id": "session-uuid-777",
      "status": "accepted",
      "message": "Query submitted for processing",
      "timestamp": "2025-10-21T16:08:00Z"
    }
    ```

**Get Query Result (GET /api/v1/queries/{query_id})**
* Response (200 OK):
    ```jsonc
    // Example response for the "Read" query: "Show me all high-priority potholes..."
    {
      "job_id": "job-uuid-fghij",
      "query_id": "query-uuid-456",
      "question": "Show me all high-priority potholes in Nurdağı.",
      "status": "completed",
      "summary": "I found 2 high-priority potholes matching your criteria.",
      // map_data tells the frontend how to update the map
      "map_data": {
        "map_action": "FIT_BOUNDS",
        "data": {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "geometry": { "type": "Point", "coordinates": [36.9081, 37.1702] },
              "properties": { "incident_id": "report-uuid-90123", "status": "assigned" }
            },
            {
              "type": "Feature",
              "geometry": { "type": "Point", "coordinates": [36.9120, 37.1750] },
              "properties": { "incident_id": "report-uuid-90124", "status": "pending" }
            }
          ]
        }
      },
      // references_used provides the "groundedness" for the summary
      "references_used": [
        {
          "type": "report",
          "reference_id": "report-uuid-90123",
          "summary": "Pothole on Ataturk Boulevard...",
          "status": "assigned",
          "location": { "type": "Point", "coordinates": [36.9081, 37.1702] }
        },
        {
          "type": "report",
          "reference_id": "report-uuid-90124",
          "summary": "Another pothole near the park",
          "status": "pending",
          "location": { "type": "Point", "coordinates": [36.9120, 37.1750] }
        }
      ],
      "id": "q-uuid-33333",
      "created_at": "2025-10-21T16:08:00Z",
      "completed_at": "2025-10-21T16:08:05Z"
    }
    ```

---

### 5.5. Session Management API

Manages the chat history, embedding `references` in messages to ensure "groundedness."

**Base Path:** `/api/v1/sessions`

**Create Session (POST /api/v1/sessions)**
* Request Body:
    ```json
    {
      "domain_id": "civic_complaints_v1",
      "title": "Pothole Reports"
    }
    ```
* Response (201 Created): Full session object (see `Get Session`).

**Get Session (GET /api/v1/sessions/{session_id})**
* Response (200 OK):
    ```jsonc
    // Shows a conversation with grounded assistant messages
    {
      "session_id": "session-uuid-777",
      "title": "Pothole Reports",
      "domain_id": "civic_complaints_v1",
      "messages": [
        {
          "message_id": "msg-uuid-001",
          "role": "user",
          "content": "Show me all high-priority potholes in Nurdağı.",
          "timestamp": "2025-10-21T16:08:00Z",
          "metadata": null
        },
        {
          "message_id": "msg-uuid-002",
          "role": "assistant",
          "content": "I found 2 high-priority potholes matching your criteria.",
          "timestamp": "2025-10-21T16:08:05Z",
          // The metadata links the message to the query and the data used
          "metadata": {
            "query_id": "query-uuid-456",
            "references": [
              {
                "type": "report",
                "reference_id": "report-uuid-90123",
                "summary": "Pothole on Ataturk Boulevard...",
                "status": "assigned",
                "location": { "type": "Point", "coordinates": [36.9081, 37.1702] }
              },
              {
                "type": "report",
                "reference_id": "report-uuid-90124",
                "summary": "Another pothole near the park",
                "status": "pending",
                "location": { "type": "Point", "coordinates": [36.9120, 37.1750] }
              }
            ]
          }
        },
        {
          "message_id": "msg-uuid-003",
          "role": "user",
          "content": "Great. Assign the first one to 'Team B', due in 48 hours.",
          "timestamp": "2025-10-21T16:10:10Z",
          "metadata": null
        },
        {
          "message_id": "msg-uuid-004",
          "role": "assistant",
          "content": "Done. I've assigned task 'report-uuid-90123' to Team B, due 2025-10-23.",
          "timestamp": "2025-10-21T16:10:15Z",
          "metadata": {
            "query_id": "query-uuid-457",
            "references": [ // This "update" action also has a reference
              {
                "type": "report",
                "reference_id": "report-uuid-90123",
                "summary": "Pothole on Ataturk Boulevard...",
                "status": "assigned", // The new status
                "location": { "type": "Point", "coordinates": [36.9081, 37.1702] }
              }
            ]
          }
        }
      ],
      "id": "s-uuid-44444",
      "created_at": "2025-10-21T16:07:00Z",
      "updated_at": "2025-10-21T16:10:15Z"
    }
    ```
**List/Update/Delete:** Standard CRUD operations.

---

### 5.6. Data Retrieval API (For Bulk Display)

Read-only endpoints designed to populate UIs like the main map dashboard.

**Base Path:** `/api/v1/data`

**Get Geographic Data (GET /api/v1/data/geo)**
* Query Parameters: `domain_id`, `bounds` (string, "west,south,east,north")
* Example Request: `GET /api/v1/data/geo?domain_id=civic_complaints_v1&bounds=36.9,37.1,37.0,37.2`
* Response (200 OK):
    ```json
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { "type": "Point", "coordinates": [36.9081, 37.1702] },
          "properties": { "incident_id": "report-uuid-90123", "status": "assigned" }
        },
        {
          "type": "Feature",
          "geometry": { "type": "Point", "coordinates": [36.9120, 37.1750] },
          "properties": { "incident_id": "report-uuid-90124", "status": "pending" }
        }
      ]
    }
    ```

**Get Aggregated Data (GET /api/v1/data/aggregated)**
* Query Parameters: `domain_id`, `group_by` (string, e.g., 'status', 'ingestion_data.complaint_type')
* Example Request: `GET /api/v1/data/aggregated?domain_id=civic_complaints_v1&group_by=status`
* Response (200 OK):
    ```json
    {
      "aggregations": [
        { "key": "assigned", "count": 1 },
        { "key": "pending", "count": 1 }
      ],
      "total": 2
    }
    ```

---

### 5.7. Real-Time Communication API (AppSync)

Provides WebSocket subscriptions for real-time UI updates.

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