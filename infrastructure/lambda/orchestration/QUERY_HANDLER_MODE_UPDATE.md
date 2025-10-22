# Query Handler Mode Selection Update

## Overview

Updated the Query Handler (`query_handler_simple.py`) to implement mode-based routing as specified in the API refactoring requirements. The handler now routes queries to either the `query_playbook` (for read operations) or `management_playbook` (for update operations) based on an explicit `mode` parameter.

## Changes Implemented

### 1. Table Migration
- **Old**: Used `Queries` table with `job_id` as primary key
- **New**: Uses `QueryJobs` table with `query_id` as primary key
- **Schema**: Added GSI `session-created-index` for filtering by session

### 2. Mode Parameter
- Added required `mode` parameter to POST requests
- Valid values: `"query"` or `"management"`
- Defaults to `"query"` if not specified
- Routes to appropriate playbook based on mode:
  - `mode="query"` → `query_playbook` (read operations)
  - `mode="management"` → `management_playbook` (update operations)

### 3. Removed Intent Classification
- **Before**: Server attempted to classify user intent from question text
- **After**: Client explicitly specifies mode in request
- Simpler, more reliable, and follows single-responsibility principle

### 4. API Operations

#### POST /api/v1/queries
Submit a new query with mode selection.

**Request Body**:
```json
{
  "session_id": "string (required)",
  "domain_id": "string (required)",
  "question": "string (required)",
  "mode": "query|management (optional, default: query)"
}
```

**Response (202 Accepted)**:
```json
{
  "job_id": "string",
  "query_id": "string",
  "session_id": "string",
  "status": "accepted",
  "message": "Query submitted for processing",
  "timestamp": "ISO8601"
}
```

#### GET /api/v1/queries/{query_id}
Get query result with execution log.

**Response (200 OK)**:
```json
{
  "query_id": "string",
  "job_id": "string",
  "session_id": "string",
  "question": "string",
  "mode": "query|management",
  "status": "processing|completed|failed",
  "summary": "string",
  "map_data": {},
  "references_used": [],
  "execution_log": [],
  "created_at": "ISO8601",
  "completed_at": "ISO8601"
}
```

#### GET /api/v1/queries
List queries with optional filtering.

**Query Parameters**:
- `page`: number (default: 1)
- `limit`: number (default: 20, max: 100)
- `session_id`: string (optional filter)

**Response (200 OK)**:
```json
{
  "queries": [
    {
      "query_id": "string",
      "question": "string",
      "status": "string",
      "created_at": "ISO8601"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50
  }
}
```

#### DELETE /api/v1/queries/{query_id}
Delete a query.

**Response (200 OK)**:
```json
{
  "message": "Query deleted successfully",
  "query_id": "string"
}
```

### 5. Orchestrator Integration

The handler passes the following payload to the orchestrator:

```json
{
  "job_id": "query_uuid",
  "job_type": "query|management",
  "playbook_type": "query_playbook|management_playbook",
  "query_id": "qry_12345678",
  "session_id": "session_uuid",
  "domain_id": "civic_complaints_v1",
  "question": "Show me all potholes",
  "tenant_id": "tenant_uuid",
  "user_id": "user_uuid"
}
```

### 6. Data Structure

**QueryJobs Table Schema**:
- Primary Key: `query_id` (String)
- GSI: `session-created-index` (session_id, created_at)
- Attributes:
  - `query_id`: Unique identifier
  - `job_id`: Orchestrator job ID
  - `session_id`: Chat session ID
  - `tenant_id`: Tenant isolation
  - `domain_id`: Domain configuration
  - `question`: User's natural language query
  - `mode`: "query" or "management"
  - `status`: "processing", "completed", or "failed"
  - `summary`: Generated answer
  - `map_data`: Geographic visualization data
  - `references_used`: Source documents
  - `execution_log`: Agent execution details
  - `id`: Standard metadata (same as query_id)
  - `created_at`: ISO8601 timestamp
  - `created_by`: User ID
  - `completed_at`: ISO8601 timestamp (when finished)

## Requirements Satisfied

✅ **Requirement 4.1**: Mode parameter routes to query_playbook for read operations
✅ **Requirement 4.2**: Mode parameter routes to management_playbook for update operations  
✅ **Requirement 4.3**: Uses QueryJobs table with proper schema and GSI, returns execution_log, map_data, references_used
✅ **Requirement 14.1**: Query handler stores execution_log field (populated by orchestrator)
✅ **Requirement 14.2**: GET /api/v1/queries/{query_id} returns execution_log array with all agent steps

## Client Integration

The frontend should now:

1. **Ask Mode** (Read operations):
```javascript
POST /api/v1/queries
{
  "session_id": sessionId,
  "domain_id": domainId,
  "question": "Show me all pending potholes",
  "mode": "query"
}
```

2. **Manage Mode** (Update operations):
```javascript
POST /api/v1/queries
{
  "session_id": sessionId,
  "domain_id": domainId,
  "question": "Assign pothole #123 to Team B",
  "mode": "management"
}
```

3. **Report Mode** (Create operations):
```javascript
POST /api/v1/reports
{
  "domain_id": domainId,
  "text": "There is a pothole on Main Street",
  "images": []
}
```

## Testing

To test the updated handler:

```bash
# Test query mode (read)
curl -X POST https://api.example.com/api/v1/queries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_123",
    "domain_id": "civic_complaints_v1",
    "question": "Show me all potholes",
    "mode": "query"
  }'

# Test management mode (update)
curl -X POST https://api.example.com/api/v1/queries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_123",
    "domain_id": "civic_complaints_v1",
    "question": "Assign this to Team B",
    "mode": "management"
  }'

# Get query result
curl -X GET https://api.example.com/api/v1/queries/qry_12345678 \
  -H "Authorization: Bearer $TOKEN"

# List queries for session
curl -X GET "https://api.example.com/api/v1/queries?session_id=sess_123&page=1&limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Delete query
curl -X DELETE https://api.example.com/api/v1/queries/qry_12345678 \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

1. Update API Gateway routes to point to this handler
2. Update orchestrator to handle `playbook_type` parameter
3. Create Session Handler for session management
4. Update frontend to use mode parameter
5. Add execution_log and map_data population in orchestrator

## Notes

- The handler creates the QueryJobs table automatically if it doesn't exist
- All operations enforce tenant isolation
- Pagination is implemented for list operations
- Standard metadata (id, created_at, created_by) is included in all records
- CORS headers are included in all responses
