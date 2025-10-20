# Multi-Agent Orchestration System - API Reference

**Version:** 1.0  
**Last Updated:** October 20, 2025

## Table of Contents

- [Authentication](#authentication)
  - [JWT Token Requirements](#jwt-token-requirements)
  - [Authorization Header](#authorization-header)
- [Error Codes Reference](#error-codes-reference)
  - [HTTP Status Codes](#http-status-codes)
  - [Error Response Format](#error-response-format)
  - [Common Error Messages](#common-error-messages)
- [Rate Limits and Pagination](#rate-limits-and-pagination)
- [Config API](#config-api)
  - [Create Configuration](#create-configuration)
  - [Get Configuration](#get-configuration)
  - [List Configurations](#list-configurations)
  - [Update Configuration](#update-configuration)
  - [Delete Configuration](#delete-configuration)
- [Data API](#data-api)
  - [Retrieve Incidents](#retrieve-incidents)
  - [Spatial Queries](#spatial-queries)
  - [Analytics Queries](#analytics-queries)
  - [Aggregation Queries](#aggregation-queries)
  - [Vector Search](#vector-search)
- [Ingest API](#ingest-api)
  - [Submit Report](#submit-report)
- [Query API](#query-api)
  - [Ask Question](#ask-question)
- [Tool Registry API](#tool-registry-api)
  - [List Tools](#list-tools)
  - [Get Tool Details](#get-tool-details)
- [Real-time API](#real-time-api)
  - [Status Update Subscription](#status-update-subscription)
  - [WebSocket Connection](#websocket-connection)
- [Validation Rules](#validation-rules)
  - [Client-Side Validation](#client-side-validation)
  - [Server-Side Validation](#server-side-validation)

---

## Authentication

All API endpoints require authentication using JWT (JSON Web Token) tokens issued by AWS Cognito.

### JWT Token Requirements

Your JWT token must include the following claims:

- `tenant_id` (string): Unique identifier for your organization/tenant
- `user_id` (string): Unique identifier for the authenticated user
- `exp` (number): Token expiration timestamp

### Authorization Header

Include the JWT token in the `Authorization` header of every request:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example:**

```bash
curl -X GET https://api.example.com/api/v1/config?type=agent \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Error Codes Reference

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful GET, PUT, or DELETE request |
| 201 | Created | Successful POST request (resource created) |
| 202 | Accepted | Asynchronous operation started (Ingest, Query) |
| 400 | Bad Request | Invalid input, validation errors, or malformed request |
| 401 | Unauthorized | Missing, invalid, or expired JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Requested resource doesn't exist |
| 409 | Conflict | Resource already exists or version conflict |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Temporary service outage |

### Error Response Format

All error responses follow this consistent structure:

```json
{
  "error": "Human-readable error message",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "field_name",
    "constraint": "constraint_violated"
  }
}
```

**Example Error Response (400 Bad Request):**

```json
{
  "error": "Missing required field: agent_name",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "MISSING_FIELD",
  "details": {
    "field": "agent_name"
  }
}
```

### Common Error Messages

#### Validation Errors (400)

- `Missing required field: {field_name}`
- `Invalid agent_type: {type}. Must be one of ['ingestion', 'query', 'custom']`
- `output_schema cannot have more than 5 keys. Found {count} keys`
- `Field {field_name} exceeds maximum length of {max_length} characters`
- `Invalid data type for field {field_name}. Expected {expected_type}, got {actual_type}`
- `Circular dependency detected in agent configuration`
- `Multi-level dependencies detected. Each agent can only depend on one parent agent`
- `Tool not found: {tool_id}`

#### Authentication Errors (401)

- `Unauthorized: Missing tenant_id in JWT token`
- `Unauthorized: Invalid JWT token`
- `Unauthorized: JWT token has expired`

#### Not Found Errors (404)

- `Configuration not found: {type}/{id}`
- `Domain not found: {domain_id}`
- `Agent not found: {agent_id}`

#### Server Errors (500)

- `Internal server error: {error_details}`
- `Database connection failed`
- `Failed to process request`

---

## Rate Limits and Pagination

### Rate Limits

- **Config API**: 100 requests per minute per tenant
- **Data API**: 200 requests per minute per tenant
- **Ingest API**: 50 requests per minute per tenant
- **Query API**: 50 requests per minute per tenant

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response with a `Retry-After` header.

### Pagination

List endpoints support pagination using `limit` and `offset` parameters:

- `limit`: Number of results per page (default: 100, max: 1000)
- `offset`: Number of results to skip (default: 0)

**Pagination Response:**

```json
{
  "data": [...],
  "count": 25,
  "limit": 100,
  "offset": 0,
  "total_count": 250
}
```

---

## Config API

Base URL: `/api/v1/config`

The Config API manages all system configurations including agents, playbooks, dependency graphs, and domain templates.

### Create Configuration

Create a new configuration (agent, playbook, dependency graph, or domain template).

**Endpoint:** `POST /api/v1/config`

**Authentication:** Required

**Request Body:**

```json
{
  "type": "agent|playbook|dependency_graph|domain_template",
  "config": {
    // Configuration-specific fields
  }
}
```

#### Create Agent

**Request:**

```json
{
  "type": "agent",
  "config": {
    "agent_name": "string (required, 1-100 chars)",
    "agent_type": "ingestion|query|custom (required)",
    "system_prompt": "string (required, 1-2000 chars)",
    "tools": ["tool_id1", "tool_id2"] (required, min 1 tool),
    "output_schema": {
      "field1": "type",
      "field2": "type"
    } (required, max 5 keys),
    "dependency_parent": "agent_id (optional)",
    "api_endpoint": "https://... (optional)",
    "example_output": {} (optional)
  }
}
```

**Response (201 Created):**

```json
{
  "tenant_id": "tenant-123",
  "config_key": "agent#agent-456",
  "config_type": "agent",
  "agent_id": "agent-456",
  "agent_name": "Severity Classifier",
  "agent_type": "custom",
  "system_prompt": "Classify the severity...",
  "tools": ["bedrock"],
  "output_schema": {
    "severity": "number",
    "reasoning": "string"
  },
  "version": 1,
  "created_at": 1729425296,
  "updated_at": 1729425296,
  "created_by": "user-789",
  "is_builtin": false
}
```

**curl Example:**

```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Severity Classifier",
      "agent_type": "custom",
      "system_prompt": "Classify the severity of incidents on a scale of 1-10.",
      "tools": ["bedrock"],
      "output_schema": {
        "severity": "number",
        "reasoning": "string",
        "urgency": "string"
      }
    }
  }'
```

#### Create Domain Template

**Request (Simplified Format):**

```json
{
  "type": "domain_template",
  "config": {
    "template_name": "string (required, 1-100 chars)",
    "domain_id": "string (required, 1-50 chars, lowercase alphanumeric + underscores)",
    "description": "string (optional, max 500 chars)",
    "ingest_agent_ids": ["agent_id1", "agent_id2"] (required, min 1),
    "query_agent_ids": ["agent_id1", "agent_id2"] (required, min 1)
  }
}
```

**Response (201 Created):**

```json
{
  "tenant_id": "tenant-123",
  "config_key": "domain_template#template-456",
  "config_type": "domain_template",
  "template_id": "template-456",
  "template_name": "Custom Domain",
  "domain_id": "custom_domain",
  "description": "Custom domain for...",
  "agent_configs": [...],
  "playbook_configs": [...],
  "dependency_graph_configs": [],
  "version": 1,
  "created_at": 1729425296,
  "updated_at": 1729425296,
  "created_by": "user-789",
  "is_builtin": false
}
```

**curl Example:**

```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "domain_template",
    "config": {
      "template_name": "Custom Incident Domain",
      "domain_id": "custom_incidents",
      "description": "Custom domain for incident tracking",
      "ingest_agent_ids": ["geo_agent", "temporal_agent", "entity_agent"],
      "query_agent_ids": ["when_agent", "where_agent", "what_agent"]
    }
  }'
```

#### Create Playbook

**Request:**

```json
{
  "type": "playbook",
  "config": {
    "domain_id": "string (required)",
    "playbook_type": "ingestion|query (required)",
    "agent_ids": ["agent_id1", "agent_id2"] (required, min 1),
    "description": "string (optional, max 500 chars)"
  }
}
```

**curl Example:**

```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "playbook",
    "config": {
      "domain_id": "civic_complaints",
      "playbook_type": "ingestion",
      "agent_ids": ["geo_agent", "temporal_agent", "entity_agent"],
      "description": "Ingestion pipeline for civic complaints"
    }
  }'
```

#### Create Dependency Graph

**Request:**

```json
{
  "type": "dependency_graph",
  "config": {
    "playbook_id": "string (required)",
    "edges": [
      {
        "from": "parent_agent_id",
        "to": "child_agent_id"
      }
    ] (required)
  }
}
```

**Note:** Each agent can have at most one parent (single-level dependency only).

**curl Example:**

```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "dependency_graph",
    "config": {
      "playbook_id": "playbook-123",
      "edges": [
        {
          "from": "entity_agent",
          "to": "severity_classifier"
        }
      ]
    }
  }'
```

---

### Get Configuration

Retrieve a specific configuration by type and ID.

**Endpoint:** `GET /api/v1/config/{type}/{id}`

**Authentication:** Required

**Path Parameters:**

- `type`: Configuration type (`agent`, `playbook`, `dependency_graph`, `domain_template`)
- `id`: Configuration ID

**Response (200 OK):**

Returns the configuration object with all fields.

**curl Example:**

```bash
# Get agent
curl -X GET https://api.example.com/api/v1/config/agent/agent-456 \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get domain template
curl -X GET https://api.example.com/api/v1/config/domain_template/template-456 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Error Responses:**

- `404 Not Found`: Configuration doesn't exist
- `401 Unauthorized`: Invalid or missing JWT token

---

### List Configurations

List all configurations of a specific type for your tenant.

**Endpoint:** `GET /api/v1/config?type={type}`

**Authentication:** Required

**Query Parameters:**

- `type`: Configuration type (`agent`, `playbook`, `dependency_graph`, `domain_template`)

**Response (200 OK):**

```json
{
  "configs": [
    {
      "tenant_id": "tenant-123",
      "config_key": "agent#agent-456",
      "agent_id": "agent-456",
      "agent_name": "Severity Classifier",
      "is_builtin": false,
      "created_by_me": true,
      ...
    },
    {
      "tenant_id": "tenant-123",
      "config_key": "agent#geo_agent",
      "agent_id": "geo_agent",
      "agent_name": "Geo Agent",
      "is_builtin": true,
      "created_by_me": false,
      ...
    }
  ],
  "count": 2
}
```

**Metadata Fields:**

- `is_builtin`: `true` if this is a system-provided configuration
- `created_by_me`: `true` if the authenticated user created this configuration
- `agent_count`: (domain templates only) Number of agents in the domain
- `incident_count`: (domain templates only) Number of incidents in the domain

**curl Example:**

```bash
# List all agents
curl -X GET "https://api.example.com/api/v1/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN"

# List all domain templates
curl -X GET "https://api.example.com/api/v1/config?type=domain_template" \
  -H "Authorization: Bearer $JWT_TOKEN"

# List all playbooks
curl -X GET "https://api.example.com/api/v1/config?type=playbook" \
  -H "Authorization: Bearer $JWT_TOKEN"

# List all dependency graphs
curl -X GET "https://api.example.com/api/v1/config?type=dependency_graph" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Update Configuration

Update an existing configuration.

**Endpoint:** `PUT /api/v1/config/{type}/{id}`

**Authentication:** Required

**Path Parameters:**

- `type`: Configuration type
- `id`: Configuration ID

**Request Body:**

```json
{
  "config": {
    // Updated configuration fields
  }
}
```

**Response (200 OK):**

Returns the updated configuration object with incremented version number.

**curl Example:**

```bash
curl -X PUT https://api.example.com/api/v1/config/agent/agent-456 \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agent_name": "Severity Classifier v2",
      "agent_type": "custom",
      "system_prompt": "Updated prompt with better instructions...",
      "tools": ["bedrock", "comprehend"],
      "output_schema": {
        "severity": "number",
        "reasoning": "string",
        "confidence": "number"
      }
    }
  }'
```

**Notes:**

- Previous version is automatically backed up to S3
- Version number is incremented
- `updated_at` timestamp is updated
- Built-in configurations cannot be modified

**Error Responses:**

- `404 Not Found`: Configuration doesn't exist
- `400 Bad Request`: Validation errors
- `403 Forbidden`: Cannot modify built-in configurations

---

### Delete Configuration

Delete a configuration.

**Endpoint:** `DELETE /api/v1/config/{type}/{id}`

**Authentication:** Required

**Path Parameters:**

- `type`: Configuration type
- `id`: Configuration ID

**Response (200 OK):**

```json
{
  "message": "Configuration deleted successfully"
}
```

**curl Example:**

```bash
curl -X DELETE https://api.example.com/api/v1/config/agent/agent-456 \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Notes:**

- Configuration is backed up to S3 before deletion
- Built-in configurations cannot be deleted
- Deleting a domain template does not delete associated incidents

**Error Responses:**

- `404 Not Found`: Configuration doesn't exist
- `403 Forbidden`: Cannot delete built-in configurations

---

## Data API

Base URL: `/api/v1/data`

The Data API provides access to stored incident data with powerful filtering, querying, and analysis capabilities.

### Retrieve Incidents

Retrieve incidents with optional filtering and pagination.

**Endpoint:** `GET /api/v1/data?type=retrieval`

**Authentication:** Required

**Query Parameters:**

- `type`: Must be `retrieval` (required)
- `filters`: JSON-encoded filter object (optional)

**Filter Object Structure:**

```json
{
  "domain_id": "string (optional)",
  "date_from": "ISO 8601 date string (optional)",
  "date_to": "ISO 8601 date string (optional)",
  "location": "string (optional, searches in location fields)",
  "category": "string (optional)",
  "custom_filters": {
    "field_name": "value"
  } (optional),
  "limit": 100 (optional, default: 100, max: 1000),
  "offset": 0 (optional, default: 0)
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "incident-123",
      "tenant_id": "tenant-456",
      "domain_id": "civic_complaints",
      "raw_text": "There is a pothole on Main Street near the library",
      "structured_data": {
        "location": {
          "address": "Main Street",
          "coordinates": {
            "lat": 40.7128,
            "lon": -74.0060
          },
          "confidence": 0.95
        },
        "timestamp": {
          "extracted_time": "2025-10-20T10:30:00Z",
          "confidence": 0.87
        },
        "category": {
          "type": "infrastructure",
          "subcategory": "road_damage",
          "confidence": 0.92
        },
        "entities": {
          "locations": ["Main Street", "library"],
          "organizations": [],
          "sentiment": "negative"
        }
      },
      "created_at": "2025-10-20T10:35:22.123Z",
      "updated_at": "2025-10-20T10:35:22.123Z",
      "created_by": "user-789",
      "images": [
        {
          "id": "image-001",
          "s3_key": "incidents/incident-123/image1.jpg",
          "s3_bucket": "incident-images-bucket",
          "content_type": "image/jpeg",
          "file_size_bytes": 245678,
          "url": "https://s3.amazonaws.com/presigned-url..."
        }
      ]
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**curl Example (Basic Retrieval):**

```bash
curl -X GET "https://api.example.com/api/v1/data?type=retrieval" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**curl Example (With Filters):**

```bash
# Filter by domain and date range
FILTERS='{"domain_id":"civic_complaints","date_from":"2025-10-01T00:00:00Z","date_to":"2025-10-31T23:59:59Z","limit":50}'
curl -X GET "https://api.example.com/api/v1/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Filter by location
FILTERS='{"location":"Main Street","limit":20}'
curl -X GET "https://api.example.com/api/v1/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Filter by category
FILTERS='{"category":"infrastructure","limit":100}'
curl -X GET "https://api.example.com/api/v1/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Pagination Example:**

```bash
# Get first page (results 0-99)
FILTERS='{"limit":100,"offset":0}'
curl -X GET "https://api.example.com/api/v1/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get second page (results 100-199)
FILTERS='{"limit":100,"offset":100}'
curl -X GET "https://api.example.com/api/v1/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Spatial Queries

Perform spatial queries on incident data using bounding boxes or proximity searches.

**Endpoint:** `GET /api/v1/data?type=spatial`

**Authentication:** Required

**Query Parameters:**

- `type`: Must be `spatial` (required)
- `filters`: JSON-encoded filter object (optional)

**Spatial Filter Object:**

```json
{
  "domain_id": "string (optional)",
  "bbox": [lon_min, lat_min, lon_max, lat_max] (optional),
  "center": {
    "lat": 40.7128,
    "lon": -74.0060
  } (optional),
  "radius_km": 5.0 (optional, requires center),
  "limit": 100 (optional),
  "offset": 0 (optional)
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "incident-123",
      "domain_id": "civic_complaints",
      "location": {
        "lat": 40.7128,
        "lon": -74.0060,
        "address": "Main Street"
      },
      "distance_km": 2.3,
      "raw_text": "...",
      "structured_data": {...},
      "created_at": "2025-10-20T10:35:22.123Z"
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

**curl Example (Bounding Box):**

```bash
# Query incidents within a bounding box (NYC area)
FILTERS='{"bbox":[-74.05,40.70,-73.95,40.75],"limit":50}'
curl -X GET "https://api.example.com/api/v1/data?type=spatial&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**curl Example (Proximity Search):**

```bash
# Query incidents within 5km of a point
FILTERS='{"center":{"lat":40.7128,"lon":-74.0060},"radius_km":5.0,"limit":50}'
curl -X GET "https://api.example.com/api/v1/data?type=spatial&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Analytics Queries

Perform analytics queries to get aggregated insights from incident data.

**Endpoint:** `GET /api/v1/data?type=analytics`

**Authentication:** Required

**Query Parameters:**

- `type`: Must be `analytics` (required)
- `filters`: JSON-encoded filter object (optional)

**Analytics Filter Object:**

```json
{
  "domain_id": "string (optional)",
  "date_from": "ISO 8601 date (optional)",
  "date_to": "ISO 8601 date (optional)",
  "group_by": "category|location|time_period (optional)",
  "time_period": "hour|day|week|month (optional, requires group_by=time_period)",
  "metrics": ["count", "avg_confidence", "sentiment_distribution"] (optional)
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "total_incidents": 1250,
    "date_range": {
      "from": "2025-10-01T00:00:00Z",
      "to": "2025-10-31T23:59:59Z"
    },
    "by_category": {
      "infrastructure": 450,
      "public_safety": 320,
      "environmental": 280,
      "other": 200
    },
    "by_time_period": [
      {
        "period": "2025-10-01",
        "count": 42,
        "avg_confidence": 0.87
      },
      {
        "period": "2025-10-02",
        "count": 38,
        "avg_confidence": 0.89
      }
    ],
    "sentiment_distribution": {
      "positive": 120,
      "neutral": 530,
      "negative": 600
    }
  }
}
```

**curl Example:**

```bash
# Get analytics grouped by category
FILTERS='{"domain_id":"civic_complaints","date_from":"2025-10-01T00:00:00Z","date_to":"2025-10-31T23:59:59Z","group_by":"category"}'
curl -X GET "https://api.example.com/api/v1/data?type=analytics&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get time series analytics
FILTERS='{"domain_id":"civic_complaints","group_by":"time_period","time_period":"day"}'
curl -X GET "https://api.example.com/api/v1/data?type=analytics&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Aggregation Queries

Perform custom aggregation queries on incident data.

**Endpoint:** `GET /api/v1/data?type=aggregation`

**Authentication:** Required

**Query Parameters:**

- `type`: Must be `aggregation` (required)
- `filters`: JSON-encoded filter object (optional)

**Aggregation Filter Object:**

```json
{
  "domain_id": "string (optional)",
  "aggregations": [
    {
      "field": "structured_data.category.type",
      "operation": "count|sum|avg|min|max",
      "alias": "category_count"
    }
  ] (required),
  "filters": {
    "date_from": "ISO 8601 date (optional)",
    "date_to": "ISO 8601 date (optional)"
  } (optional)
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "aggregations": {
      "category_count": {
        "infrastructure": 450,
        "public_safety": 320,
        "environmental": 280
      },
      "avg_confidence": 0.87
    }
  }
}
```

**curl Example:**

```bash
FILTERS='{"domain_id":"civic_complaints","aggregations":[{"field":"structured_data.category.type","operation":"count","alias":"category_count"}]}'
curl -X GET "https://api.example.com/api/v1/data?type=aggregation&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Vector Search

Perform semantic search on incident data using vector embeddings.

**Endpoint:** `GET /api/v1/data?type=vector_search`

**Authentication:** Required

**Query Parameters:**

- `type`: Must be `vector_search` (required)
- `filters`: JSON-encoded filter object (optional)

**Vector Search Filter Object:**

```json
{
  "domain_id": "string (optional)",
  "query_text": "string (required)",
  "limit": 10 (optional, default: 10, max: 100),
  "min_similarity": 0.7 (optional, default: 0.0, range: 0.0-1.0),
  "filters": {
    "date_from": "ISO 8601 date (optional)",
    "date_to": "ISO 8601 date (optional)",
    "category": "string (optional)"
  } (optional)
}
```

**Response (200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "incident-123",
      "domain_id": "civic_complaints",
      "raw_text": "There is a pothole on Main Street",
      "structured_data": {...},
      "similarity_score": 0.92,
      "created_at": "2025-10-20T10:35:22.123Z"
    },
    {
      "id": "incident-456",
      "domain_id": "civic_complaints",
      "raw_text": "Road damage reported on Elm Avenue",
      "structured_data": {...},
      "similarity_score": 0.87,
      "created_at": "2025-10-19T14:22:11.456Z"
    }
  ],
  "count": 2,
  "query_text": "road damage and potholes"
}
```

**curl Example:**

```bash
FILTERS='{"query_text":"road damage and potholes","limit":10,"min_similarity":0.7}'
curl -X GET "https://api.example.com/api/v1/data?type=vector_search&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Ingest API

Base URL: `/api/v1/ingest`

The Ingest API accepts incident reports (text and images) and processes them asynchronously through the configured agent pipeline.

### Submit Report

Submit a new incident report for processing.

**Endpoint:** `POST /api/v1/ingest`

**Authentication:** Required

**Request Body:**

```json
{
  "domain_id": "string (required)",
  "text": "string (required, 1-10000 chars)",
  "images": [
    "base64_encoded_image_string"
  ] (optional, max 5 images, 5MB each),
  "metadata": {
    "source": "string (optional)",
    "priority": "low|medium|high|critical (optional)",
    "reporter_contact": "string (optional)"
  } (optional)
}
```

**Field Constraints:**

- `domain_id`: Must be a valid domain ID that exists in your tenant
- `text`: Minimum 1 character, maximum 10,000 characters
- `images`: Maximum 5 images per report
- Each image: Maximum 5MB, base64-encoded, supported formats: JPEG, PNG, GIF, WebP

**Response (202 Accepted):**

```json
{
  "job_id": "job-abc-123",
  "status": "processing",
  "message": "Report submitted successfully",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "estimated_completion_seconds": 30
}
```

**Async Processing Flow:**

1. API returns `202 Accepted` with `job_id` immediately
2. Report is queued for processing
3. Agent pipeline executes (geo, temporal, entity extraction, etc.)
4. Real-time status updates are published via AppSync (see [Real-time API](#real-time-api))
5. Structured data is saved to database
6. Images are uploaded to S3
7. Final status update indicates completion

**curl Example (Text Only):**

```bash
curl -X POST https://api.example.com/api/v1/ingest \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "There is a large pothole on Main Street near the public library. It has been there for over a week and is causing damage to vehicles.",
    "metadata": {
      "source": "mobile_app",
      "priority": "medium"
    }
  }'
```

**curl Example (With Images):**

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -w 0 pothole.jpg)

curl -X POST https://api.example.com/api/v1/ingest \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"civic_complaints\",
    \"text\": \"Pothole on Main Street near library\",
    \"images\": [\"$IMAGE_BASE64\"],
    \"metadata\": {
      \"source\": \"mobile_app\"
    }
  }"
```

**Python Example:**

```python
import requests
import base64
import json

# Read and encode image
with open('pothole.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# Submit report
response = requests.post(
    'https://api.example.com/api/v1/ingest',
    headers={
        'Authorization': f'Bearer {JWT_TOKEN}',
        'Content-Type': 'application/json'
    },
    json={
        'domain_id': 'civic_complaints',
        'text': 'Pothole on Main Street near library',
        'images': [image_base64],
        'metadata': {
            'source': 'python_script',
            'priority': 'medium'
        }
    }
)

job_id = response.json()['job_id']
print(f'Report submitted with job_id: {job_id}')
```

**Error Responses:**

- `400 Bad Request`: Missing required fields, invalid data, text too long, too many images
- `404 Not Found`: Domain ID doesn't exist
- `413 Payload Too Large`: Image exceeds 5MB limit
- `429 Too Many Requests`: Rate limit exceeded (50 requests/minute)

**Example Error Response:**

```json
{
  "error": "Text exceeds maximum length of 10000 characters",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_LONG",
  "details": {
    "field": "text",
    "max_length": 10000,
    "actual_length": 12500
  }
}
```

---

## Query API

Base URL: `/api/v1/query`

The Query API accepts natural language questions and processes them asynchronously through the configured interrogative agent pipeline.

### Ask Question

Submit a natural language question about incident data.

**Endpoint:** `POST /api/v1/query`

**Authentication:** Required

**Request Body:**

```json
{
  "domain_id": "string (required)",
  "question": "string (required, 1-1000 chars)",
  "filters": {
    "date_range": {
      "start": "ISO 8601 date (optional)",
      "end": "ISO 8601 date (optional)"
    },
    "location": {
      "bbox": [lon_min, lat_min, lon_max, lat_max] (optional)
    },
    "category": "string (optional)"
  } (optional),
  "options": {
    "include_visualizations": true (optional, default: false),
    "max_results": 100 (optional, default: 50)
  } (optional)
}
```

**Field Constraints:**

- `domain_id`: Must be a valid domain ID that exists in your tenant
- `question`: Minimum 1 character, maximum 1,000 characters
- Filters are optional and narrow the data scope for the query

**Response (202 Accepted):**

```json
{
  "job_id": "job-xyz-789",
  "status": "processing",
  "message": "Query submitted successfully",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "estimated_completion_seconds": 45
}
```

**Async Processing Flow:**

1. API returns `202 Accepted` with `job_id` immediately
2. Question is analyzed and routed to appropriate interrogative agents
3. Agents execute in parallel (when, where, what, who, why, how agents)
4. Real-time status updates are published via AppSync (see [Real-time API](#real-time-api))
5. Results are aggregated and synthesized
6. AI-generated summary is created
7. Final results are saved to database
8. Completion status update is published

**Query Result Structure:**

Once processing is complete, retrieve results via the Data API or through real-time updates:

```json
{
  "job_id": "job-xyz-789",
  "status": "complete",
  "question": "What are the most common complaints this month?",
  "domain_id": "civic_complaints",
  "agent_results": {
    "what_agent": {
      "answer": "The most common complaints are infrastructure-related...",
      "confidence": 0.92,
      "data": {
        "top_categories": [
          {"category": "infrastructure", "count": 450},
          {"category": "public_safety", "count": 320}
        ]
      }
    },
    "when_agent": {
      "answer": "Peak complaint times are weekday mornings...",
      "confidence": 0.87,
      "data": {...}
    },
    "where_agent": {
      "answer": "Most complaints come from downtown area...",
      "confidence": 0.89,
      "data": {...}
    }
  },
  "summary": "This month, infrastructure complaints (particularly potholes and street damage) are the most common, with 450 reports. These complaints peak during weekday mornings and are concentrated in the downtown area.",
  "confidence_score": 0.89,
  "visualizations": [
    {
      "type": "bar_chart",
      "title": "Complaints by Category",
      "data": {...}
    }
  ],
  "created_at": "2025-10-20T12:35:42.123Z",
  "processing_time_seconds": 12.5
}
```

**curl Example (Simple Question):**

```bash
curl -X POST https://api.example.com/api/v1/query \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints this month?"
  }'
```

**curl Example (Question with Filters):**

```bash
curl -X POST https://api.example.com/api/v1/query \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "Where are the infrastructure problems concentrated?",
    "filters": {
      "date_range": {
        "start": "2025-10-01T00:00:00Z",
        "end": "2025-10-31T23:59:59Z"
      },
      "category": "infrastructure"
    },
    "options": {
      "include_visualizations": true
    }
  }'
```

**Python Example:**

```python
import requests
import json

response = requests.post(
    'https://api.example.com/api/v1/query',
    headers={
        'Authorization': f'Bearer {JWT_TOKEN}',
        'Content-Type': 'application/json'
    },
    json={
        'domain_id': 'civic_complaints',
        'question': 'What are the trends in public safety complaints over the last 3 months?',
        'filters': {
            'date_range': {
                'start': '2025-07-01T00:00:00Z',
                'end': '2025-10-20T23:59:59Z'
            },
            'category': 'public_safety'
        },
        'options': {
            'include_visualizations': True,
            'max_results': 100
        }
    }
)

job_id = response.json()['job_id']
print(f'Query submitted with job_id: {job_id}')
```

**Error Responses:**

- `400 Bad Request`: Missing required fields, invalid data, question too long
- `404 Not Found`: Domain ID doesn't exist
- `429 Too Many Requests`: Rate limit exceeded (50 requests/minute)

**Example Error Response:**

```json
{
  "error": "Question exceeds maximum length of 1000 characters",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_LONG",
  "details": {
    "field": "question",
    "max_length": 1000,
    "actual_length": 1250
  }
}
```

---

## Tool Registry API

Base URL: `/api/v1/tools`

The Tool Registry API provides access to the catalog of available tools that agents can use during processing.

### List Tools

List all available tools, optionally filtered by type.

**Endpoint:** `GET /api/v1/tools`

**Authentication:** Required

**Query Parameters:**

- `type`: Filter by tool type (optional): `aws_service`, `external_api`, `custom`, `data_api`

**Response (200 OK):**

```json
{
  "tools": [
    {
      "tool_name": "bedrock",
      "tool_type": "aws_service",
      "description": "AWS Bedrock for LLM inference",
      "endpoint": "bedrock.us-east-1.amazonaws.com",
      "auth_method": "iam",
      "capabilities": [
        "text_generation",
        "text_analysis",
        "entity_extraction"
      ],
      "parameters": {
        "model_id": "string (required)",
        "max_tokens": "number (optional, default: 1000)",
        "temperature": "number (optional, default: 0.7)"
      },
      "is_builtin": true,
      "created_at": 1729425296,
      "updated_at": 1729425296
    },
    {
      "tool_name": "comprehend",
      "tool_type": "aws_service",
      "description": "AWS Comprehend for NLP",
      "endpoint": "comprehend.us-east-1.amazonaws.com",
      "auth_method": "iam",
      "capabilities": [
        "entity_recognition",
        "sentiment_analysis",
        "key_phrase_extraction"
      ],
      "parameters": {
        "language_code": "string (optional, default: 'en')"
      },
      "is_builtin": true,
      "created_at": 1729425296,
      "updated_at": 1729425296
    },
    {
      "tool_name": "location",
      "tool_type": "aws_service",
      "description": "AWS Location Service for geocoding",
      "endpoint": "geo.us-east-1.amazonaws.com",
      "auth_method": "iam",
      "capabilities": [
        "geocoding",
        "reverse_geocoding",
        "place_search"
      ],
      "parameters": {
        "index_name": "string (required)"
      },
      "is_builtin": true,
      "created_at": 1729425296,
      "updated_at": 1729425296
    }
  ],
  "count": 3
}
```

**curl Example:**

```bash
# List all tools
curl -X GET https://api.example.com/api/v1/tools \
  -H "Authorization: Bearer $JWT_TOKEN"

# List only AWS service tools
curl -X GET "https://api.example.com/api/v1/tools?type=aws_service" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

### Get Tool Details

Retrieve detailed information about a specific tool.

**Endpoint:** `GET /api/v1/tools/{tool_id}`

**Authentication:** Required

**Path Parameters:**

- `tool_id`: Tool identifier (e.g., `bedrock`, `comprehend`, `location`)

**Response (200 OK):**

```json
{
  "tool_name": "bedrock",
  "tool_type": "aws_service",
  "description": "AWS Bedrock for LLM inference and text generation",
  "endpoint": "bedrock.us-east-1.amazonaws.com",
  "auth_method": "iam",
  "capabilities": [
    "text_generation",
    "text_analysis",
    "entity_extraction",
    "summarization"
  ],
  "parameters": {
    "model_id": {
      "type": "string",
      "required": true,
      "description": "Bedrock model identifier",
      "allowed_values": [
        "anthropic.claude-v2",
        "anthropic.claude-instant-v1",
        "amazon.titan-text-express-v1"
      ]
    },
    "max_tokens": {
      "type": "number",
      "required": false,
      "default": 1000,
      "min": 1,
      "max": 4096,
      "description": "Maximum tokens to generate"
    },
    "temperature": {
      "type": "number",
      "required": false,
      "default": 0.7,
      "min": 0.0,
      "max": 1.0,
      "description": "Sampling temperature"
    }
  },
  "rate_limits": {
    "requests_per_second": 10,
    "tokens_per_minute": 100000
  },
  "is_builtin": true,
  "created_at": 1729425296,
  "updated_at": 1729425296
}
```

**curl Example:**

```bash
curl -X GET https://api.example.com/api/v1/tools/bedrock \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**Error Responses:**

- `404 Not Found`: Tool doesn't exist

---

## Real-time API

Base URL: AppSync GraphQL endpoint (provided in deployment outputs)

The Real-time API provides WebSocket-based subscriptions for receiving live status updates during asynchronous operations (ingest and query).

### Status Update Subscription

Subscribe to real-time status updates for a specific job.

**GraphQL Schema:**

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

type Subscription {
  onStatusUpdate(userId: ID!): StatusUpdate
    @aws_subscribe(mutations: ["publishStatus"])
}
```

**Status Types:**

| Status | Description | Example Message |
|--------|-------------|-----------------|
| `loading_agents` | Loading playbook configuration | "Loading agent configuration for domain: civic_complaints" |
| `invoking_{agent_name}` | Agent starting execution | "Invoking geo_agent" |
| `calling_{tool_name}` | Tool invocation in progress | "Calling bedrock for entity extraction" |
| `agent_complete_{agent_name}` | Agent finished execution | "geo_agent completed with confidence: 0.95" |
| `validating` | Validation in progress | "Validating agent outputs" |
| `synthesizing` | Synthesis in progress | "Synthesizing query results" |
| `complete` | Job complete | "Processing complete" |
| `error` | Error occurred | "Error: Agent execution failed" |

**Metadata Fields:**

```json
{
  "confidence": 0.95,
  "agent_output": {...},
  "error_details": "...",
  "processing_time_ms": 1250
}
```

---

### WebSocket Connection

**JavaScript Example (AWS Amplify):**

```javascript
import { API, graphqlOperation } from 'aws-amplify';

const subscription = `
  subscription OnStatusUpdate($userId: ID!) {
    onStatusUpdate(userId: $userId) {
      jobId
      userId
      agentName
      status
      message
      timestamp
      metadata
    }
  }
`;

// Subscribe to updates
const subscriptionClient = API.graphql(
  graphqlOperation(subscription, { userId: 'user-123' })
).subscribe({
  next: ({ value }) => {
    const update = value.data.onStatusUpdate;
    console.log('Status update:', update);
    
    // Handle different status types
    if (update.status === 'complete') {
      console.log('Job completed!');
    } else if (update.status === 'error') {
      console.error('Job failed:', update.message);
    } else if (update.status.startsWith('agent_complete_')) {
      const agentName = update.agentName;
      const confidence = JSON.parse(update.metadata).confidence;
      console.log(`${agentName} completed with confidence: ${confidence}`);
    }
  },
  error: (error) => {
    console.error('Subscription error:', error);
  }
});

// Unsubscribe when done
// subscriptionClient.unsubscribe();
```

**Python Example (using websockets):**

```python
import asyncio
import websockets
import json
from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport

# AppSync WebSocket endpoint
APPSYNC_ENDPOINT = "wss://your-appsync-endpoint.appsync-realtime-api.us-east-1.amazonaws.com/graphql"

subscription_query = gql("""
    subscription OnStatusUpdate($userId: ID!) {
        onStatusUpdate(userId: $userId) {
            jobId
            userId
            agentName
            status
            message
            timestamp
            metadata
        }
    }
""")

async def subscribe_to_updates(user_id: str):
    transport = WebsocketsTransport(
        url=APPSYNC_ENDPOINT,
        headers={
            'Authorization': f'Bearer {JWT_TOKEN}'
        }
    )
    
    async with Client(transport=transport) as session:
        async for result in session.subscribe(
            subscription_query,
            variable_values={'userId': user_id}
        ):
            update = result['onStatusUpdate']
            print(f"Status: {update['status']}")
            print(f"Message: {update['message']}")
            
            if update['status'] == 'complete':
                print("Job completed!")
                break
            elif update['status'] == 'error':
                print(f"Job failed: {update['message']}")
                break

# Run subscription
asyncio.run(subscribe_to_updates('user-123'))
```

**curl Example (HTTP POST for testing):**

Note: Real-time subscriptions require WebSocket connections. For testing, you can use the mutation endpoint:

```bash
curl -X POST https://your-appsync-endpoint.appsync-api.us-east-1.amazonaws.com/graphql \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation PublishStatus($jobId: ID!, $userId: ID!, $status: String!, $message: String!) { publishStatus(jobId: $jobId, userId: $userId, status: $status, message: $message) { jobId status message timestamp } }",
    "variables": {
      "jobId": "job-123",
      "userId": "user-456",
      "status": "complete",
      "message": "Processing complete"
    }
  }'
```

**Status Update Flow Example:**

When you submit a report via the Ingest API, you'll receive status updates in this sequence:

```
1. loading_agents
   "Loading agent configuration for domain: civic_complaints"

2. invoking_geo_agent
   "Invoking geo_agent"

3. calling_location
   "Calling location service for geocoding"

4. agent_complete_geo_agent
   "geo_agent completed with confidence: 0.95"
   metadata: {"confidence": 0.95, "processing_time_ms": 850}

5. invoking_temporal_agent
   "Invoking temporal_agent"

6. agent_complete_temporal_agent
   "temporal_agent completed with confidence: 0.87"
   metadata: {"confidence": 0.87, "processing_time_ms": 620}

7. invoking_entity_agent
   "Invoking entity_agent"

8. calling_comprehend
   "Calling comprehend for entity extraction"

9. agent_complete_entity_agent
   "entity_agent completed with confidence: 0.92"
   metadata: {"confidence": 0.92, "processing_time_ms": 1200}

10. validating
    "Validating agent outputs"

11. complete
    "Processing complete"
    metadata: {"total_processing_time_ms": 3500}
```

---

## Validation Rules

### Client-Side Validation

Perform these validations in your frontend application before making API calls to provide immediate feedback to users.

#### Agent Configuration

| Field | Validation Rules |
|-------|-----------------|
| `agent_name` | Required, 1-100 characters, alphanumeric + spaces + hyphens + underscores |
| `agent_type` | Required, must be one of: `ingestion`, `query`, `custom` |
| `system_prompt` | Required, 1-2000 characters |
| `tools` | Required, array with at least 1 tool ID, each tool must exist in registry |
| `output_schema` | Required, object with 1-5 keys, each key must be a valid field name |
| `dependency_parent` | Optional, must be a valid agent ID if provided |
| `api_endpoint` | Optional, must be a valid URL if provided |

**Validation Examples:**

```javascript
// Agent name validation
function validateAgentName(name) {
  if (!name || name.length < 1 || name.length > 100) {
    return 'Agent name must be 1-100 characters';
  }
  if (!/^[a-zA-Z0-9\s\-_]+$/.test(name)) {
    return 'Agent name can only contain letters, numbers, spaces, hyphens, and underscores';
  }
  return null; // Valid
}

// Agent type validation
function validateAgentType(type) {
  const validTypes = ['ingestion', 'query', 'custom'];
  if (!validTypes.includes(type)) {
    return `Agent type must be one of: ${validTypes.join(', ')}`;
  }
  return null; // Valid
}

// System prompt validation
function validateSystemPrompt(prompt) {
  if (!prompt || prompt.length < 1 || prompt.length > 2000) {
    return 'System prompt must be 1-2000 characters';
  }
  return null; // Valid
}

// Tools validation
function validateTools(tools) {
  if (!Array.isArray(tools) || tools.length < 1) {
    return 'At least one tool must be selected';
  }
  return null; // Valid
}

// Output schema validation
function validateOutputSchema(schema) {
  if (!schema || typeof schema !== 'object') {
    return 'Output schema must be an object';
  }
  const keys = Object.keys(schema);
  if (keys.length < 1 || keys.length > 5) {
    return 'Output schema must have 1-5 fields';
  }
  return null; // Valid
}
```

#### Domain Template Configuration

| Field | Validation Rules |
|-------|-----------------|
| `template_name` | Required, 1-100 characters |
| `domain_id` | Required, 1-50 characters, lowercase alphanumeric + underscores only |
| `description` | Optional, max 500 characters |
| `ingest_agent_ids` | Required, array with at least 1 agent ID |
| `query_agent_ids` | Required, array with at least 1 agent ID |

**Validation Examples:**

```javascript
// Domain ID validation
function validateDomainId(domainId) {
  if (!domainId || domainId.length < 1 || domainId.length > 50) {
    return 'Domain ID must be 1-50 characters';
  }
  if (!/^[a-z0-9_]+$/.test(domainId)) {
    return 'Domain ID can only contain lowercase letters, numbers, and underscores';
  }
  return null; // Valid
}

// Agent IDs validation
function validateAgentIds(agentIds, fieldName) {
  if (!Array.isArray(agentIds) || agentIds.length < 1) {
    return `${fieldName} must contain at least one agent ID`;
  }
  return null; // Valid
}
```

#### Report Submission

| Field | Validation Rules |
|-------|-----------------|
| `domain_id` | Required, must exist in your tenant |
| `text` | Required, 1-10,000 characters |
| `images` | Optional, max 5 images, each max 5MB, base64-encoded |
| `metadata.priority` | Optional, must be one of: `low`, `medium`, `high`, `critical` |

**Validation Examples:**

```javascript
// Text validation
function validateReportText(text) {
  if (!text || text.length < 1) {
    return 'Report text is required';
  }
  if (text.length > 10000) {
    return 'Report text cannot exceed 10,000 characters';
  }
  return null; // Valid
}

// Images validation
function validateImages(images) {
  if (!images) return null; // Optional field
  
  if (!Array.isArray(images)) {
    return 'Images must be an array';
  }
  if (images.length > 5) {
    return 'Maximum 5 images allowed per report';
  }
  
  // Check each image size (base64 string length / 1.37 ≈ original size)
  for (let i = 0; i < images.length; i++) {
    const estimatedSize = (images[i].length * 0.75) / (1024 * 1024); // MB
    if (estimatedSize > 5) {
      return `Image ${i + 1} exceeds 5MB limit`;
    }
  }
  
  return null; // Valid
}

// Priority validation
function validatePriority(priority) {
  if (!priority) return null; // Optional field
  
  const validPriorities = ['low', 'medium', 'high', 'critical'];
  if (!validPriorities.includes(priority)) {
    return `Priority must be one of: ${validPriorities.join(', ')}`;
  }
  return null; // Valid
}
```

#### Query Submission

| Field | Validation Rules |
|-------|-----------------|
| `domain_id` | Required, must exist in your tenant |
| `question` | Required, 1-1,000 characters |
| `filters.date_range` | Optional, start must be before end |
| `filters.location.bbox` | Optional, must be array of 4 numbers [lon_min, lat_min, lon_max, lat_max] |

**Validation Examples:**

```javascript
// Question validation
function validateQuestion(question) {
  if (!question || question.length < 1) {
    return 'Question is required';
  }
  if (question.length > 1000) {
    return 'Question cannot exceed 1,000 characters';
  }
  return null; // Valid
}

// Date range validation
function validateDateRange(dateRange) {
  if (!dateRange) return null; // Optional field
  
  if (dateRange.start && dateRange.end) {
    const start = new Date(dateRange.start);
    const end = new Date(dateRange.end);
    
    if (start >= end) {
      return 'Start date must be before end date';
    }
  }
  return null; // Valid
}

// Bounding box validation
function validateBbox(bbox) {
  if (!bbox) return null; // Optional field
  
  if (!Array.isArray(bbox) || bbox.length !== 4) {
    return 'Bounding box must be an array of 4 numbers [lon_min, lat_min, lon_max, lat_max]';
  }
  
  const [lonMin, latMin, lonMax, latMax] = bbox;
  
  if (lonMin >= lonMax) {
    return 'lon_min must be less than lon_max';
  }
  if (latMin >= latMax) {
    return 'lat_min must be less than lat_max';
  }
  if (lonMin < -180 || lonMax > 180) {
    return 'Longitude must be between -180 and 180';
  }
  if (latMin < -90 || latMax > 90) {
    return 'Latitude must be between -90 and 90';
  }
  
  return null; // Valid
}
```

---

### Server-Side Validation

The backend performs these validations and returns appropriate error responses.

#### Agent Configuration Validation

- **Agent Type**: Must be one of `ingestion`, `query`, or `custom`
- **Tools**: All tool IDs must exist in the tool registry
- **Output Schema**: Maximum 5 keys allowed
- **Dependency Parent**: 
  - Must exist if provided
  - Cannot create circular dependencies
  - Cannot create multi-level dependencies (max depth: 1)
- **Uniqueness**: Agent names must be unique within a tenant

**Error Examples:**

```json
// Invalid agent type
{
  "error": "Invalid agent_type: 'analytics'. Must be one of ['ingestion', 'query', 'custom']",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "INVALID_VALUE"
}

// Tool not found
{
  "error": "Tool not found: custom_tool_123",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "NOT_FOUND",
  "details": {
    "field": "tools",
    "invalid_value": "custom_tool_123"
  }
}

// Too many output schema keys
{
  "error": "output_schema cannot have more than 5 keys. Found 7 keys",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_MANY",
  "details": {
    "field": "output_schema",
    "max_keys": 5,
    "actual_keys": 7
  }
}

// Circular dependency
{
  "error": "Circular dependency detected: agent_a -> agent_b -> agent_a",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "CIRCULAR_DEPENDENCY"
}

// Multi-level dependency
{
  "error": "Multi-level dependencies detected. Each agent can only depend on one parent agent",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "MULTI_LEVEL_DEPENDENCY"
}
```

#### Domain Template Validation

- **Domain ID**: Must be unique within tenant, lowercase alphanumeric + underscores only
- **Agent IDs**: All agent IDs must exist
- **Minimum Agents**: At least one ingestion agent and one query agent required

**Error Examples:**

```json
// Domain ID already exists
{
  "error": "Domain ID 'civic_complaints' already exists",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "ALREADY_EXISTS",
  "details": {
    "field": "domain_id",
    "value": "civic_complaints"
  }
}

// Invalid domain ID format
{
  "error": "Domain ID can only contain lowercase letters, numbers, and underscores",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "INVALID_FORMAT",
  "details": {
    "field": "domain_id",
    "value": "Civic-Complaints"
  }
}

// Agent not found
{
  "error": "Agent not found: custom_agent_123",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "NOT_FOUND",
  "details": {
    "field": "ingest_agent_ids",
    "invalid_value": "custom_agent_123"
  }
}
```

#### Report Submission Validation

- **Domain ID**: Must exist in tenant
- **Text Length**: 1-10,000 characters
- **Image Count**: Maximum 5 images
- **Image Size**: Maximum 5MB per image
- **Image Format**: Must be valid base64-encoded image

**Error Examples:**

```json
// Domain not found
{
  "error": "Domain not found: invalid_domain",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "NOT_FOUND",
  "details": {
    "field": "domain_id",
    "value": "invalid_domain"
  }
}

// Text too long
{
  "error": "Text exceeds maximum length of 10000 characters",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_LONG",
  "details": {
    "field": "text",
    "max_length": 10000,
    "actual_length": 12500
  }
}

// Too many images
{
  "error": "Maximum 5 images allowed per report",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_MANY",
  "details": {
    "field": "images",
    "max_count": 5,
    "actual_count": 7
  }
}

// Image too large
{
  "error": "Image exceeds maximum size of 5MB",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_LARGE",
  "details": {
    "field": "images[2]",
    "max_size_mb": 5,
    "actual_size_mb": 7.2
  }
}
```

#### Query Submission Validation

- **Domain ID**: Must exist in tenant
- **Question Length**: 1-1,000 characters
- **Date Range**: Start date must be before end date
- **Bounding Box**: Must be valid coordinates

**Error Examples:**

```json
// Question too long
{
  "error": "Question exceeds maximum length of 1000 characters",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_LONG",
  "details": {
    "field": "question",
    "max_length": 1000,
    "actual_length": 1250
  }
}

// Invalid date range
{
  "error": "Start date must be before end date",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "INVALID_RANGE",
  "details": {
    "field": "filters.date_range",
    "start": "2025-10-31T00:00:00Z",
    "end": "2025-10-01T00:00:00Z"
  }
}

// Invalid bounding box
{
  "error": "Invalid bounding box coordinates",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "INVALID_VALUE",
  "details": {
    "field": "filters.location.bbox",
    "message": "lon_min must be less than lon_max"
  }
}
```

---

## Appendix

### Built-in Domain Templates

The system includes three pre-configured domain templates:

#### 1. Civic Complaints

**Domain ID:** `civic_complaints`

**Description:** Track and analyze civic infrastructure complaints and public service issues

**Ingestion Agents:**
- Geo Agent (location extraction)
- Temporal Agent (time extraction)
- Entity Agent (entity and sentiment extraction)

**Query Agents:**
- When Agent (temporal analysis)
- Where Agent (spatial analysis)
- What Agent (categorical analysis)
- Who Agent (entity analysis)
- Why Agent (causal analysis)
- How Agent (process analysis)

#### 2. Disaster Response

**Domain ID:** `disaster_response`

**Description:** Emergency incident tracking and disaster response coordination

**Ingestion Agents:**
- Geo Agent (location extraction)
- Temporal Agent (time extraction)
- Severity Agent (severity assessment)

**Query Agents:**
- When Agent (temporal analysis)
- Where Agent (spatial analysis)
- What Agent (incident type analysis)

#### 3. Agriculture

**Domain ID:** `agriculture`

**Description:** Agricultural monitoring and crop management

**Ingestion Agents:**
- Crop Agent (crop information extraction)
- Geo Agent (farm location extraction)
- Temporal Agent (time extraction)

**Query Agents:**
- When Agent (temporal analysis)
- Where Agent (spatial analysis)
- What Agent (crop analysis)

---

### Code Examples

#### Complete Workflow Example (Python)

```python
import requests
import base64
import time
import json

BASE_URL = "https://api.example.com/api/v1"
JWT_TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Create a custom agent
print("Creating custom agent...")
agent_response = requests.post(
    f"{BASE_URL}/config",
    headers=headers,
    json={
        "type": "agent",
        "config": {
            "agent_name": "Priority Scorer",
            "agent_type": "custom",
            "system_prompt": "Score the priority of incidents on a scale of 1-10",
            "tools": ["bedrock"],
            "output_schema": {
                "priority_score": "number",
                "reasoning": "string"
            }
        }
    }
)
agent_id = agent_response.json()["agent_id"]
print(f"Created agent: {agent_id}")

# Step 2: Create a custom domain
print("\nCreating custom domain...")
domain_response = requests.post(
    f"{BASE_URL}/config",
    headers=headers,
    json={
        "type": "domain_template",
        "config": {
            "template_name": "Custom Incidents",
            "domain_id": "custom_incidents",
            "description": "Custom incident tracking with priority scoring",
            "ingest_agent_ids": ["geo_agent", "temporal_agent", agent_id],
            "query_agent_ids": ["when_agent", "where_agent", "what_agent"]
        }
    }
)
domain_id = domain_response.json()["domain_id"]
print(f"Created domain: {domain_id}")

# Step 3: Submit a report
print("\nSubmitting report...")
ingest_response = requests.post(
    f"{BASE_URL}/ingest",
    headers=headers,
    json={
        "domain_id": domain_id,
        "text": "Large pothole on Main Street causing vehicle damage",
        "metadata": {
            "source": "python_script",
            "priority": "high"
        }
    }
)
job_id = ingest_response.json()["job_id"]
print(f"Report submitted with job_id: {job_id}")

# Step 4: Wait for processing (in production, use WebSocket subscription)
print("\nWaiting for processing...")
time.sleep(10)

# Step 5: Query the data
print("\nQuerying data...")
query_response = requests.post(
    f"{BASE_URL}/query",
    headers=headers,
    json={
        "domain_id": domain_id,
        "question": "What are the highest priority incidents?"
    }
)
query_job_id = query_response.json()["job_id"]
print(f"Query submitted with job_id: {query_job_id}")

# Step 6: Retrieve incidents
print("\nRetrieving incidents...")
filters = json.dumps({"domain_id": domain_id, "limit": 10})
data_response = requests.get(
    f"{BASE_URL}/data?type=retrieval&filters={filters}",
    headers=headers
)
incidents = data_response.json()["data"]
print(f"Retrieved {len(incidents)} incidents")

for incident in incidents:
    print(f"\nIncident: {incident['id']}")
    print(f"Text: {incident['raw_text']}")
    print(f"Priority: {incident['structured_data'].get('priority_score', 'N/A')}")
```

---

### Support and Resources

- **API Status**: https://status.example.com
- **Developer Portal**: https://developers.example.com
- **Support Email**: api-support@example.com
- **Rate Limit Increases**: Contact support with your use case

---

**End of API Reference**

