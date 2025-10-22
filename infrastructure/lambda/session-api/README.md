# Session Handler Lambda

Handles CRUD operations for session management with message grounding.

## Overview

The Session Handler manages chat sessions and messages with references to source data. It provides endpoints for creating, retrieving, updating, and deleting sessions, as well as managing the messages within those sessions.

## Features

- **Create Session**: Initialize a new chat session for a domain
- **Get Session**: Retrieve session details with all messages and metadata
- **List Sessions**: Get paginated list of user's sessions sorted by activity
- **Update Session**: Modify session metadata (title)
- **Delete Session**: Remove session and cascade delete all messages
- **Message Grounding**: Messages include references to source Reports for groundedness

## API Endpoints

### POST /api/v1/sessions
Create a new session.

**Request Body:**
```json
{
  "domain_id": "civic_complaints_v1",
  "title": "Pothole Issues Discussion"
}
```

**Response (201 Created):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "domain_id": "civic_complaints_v1",
  "title": "Pothole Issues Discussion",
  "id": "uuid-string",
  "created_at": "2025-10-21T16:00:00Z",
  "updated_at": "2025-10-21T16:00:00Z"
}
```

### GET /api/v1/sessions/{session_id}
Get session with all messages.

**Response (200 OK):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "title": "Pothole Issues Discussion",
  "domain_id": "civic_complaints_v1",
  "messages": [
    {
      "message_id": "msg_12345678",
      "role": "user",
      "content": "Show me all potholes",
      "timestamp": "2025-10-21T16:01:00Z"
    },
    {
      "message_id": "msg_87654321",
      "role": "assistant",
      "content": "I found 5 pothole reports...",
      "timestamp": "2025-10-21T16:01:05Z",
      "metadata": {
        "query_id": "query_xyz",
        "references": [
          {
            "type": "report",
            "reference_id": "inc_abc123",
            "summary": "Pothole on Main St",
            "status": "pending",
            "location": {
              "type": "Point",
              "coordinates": [36.9, 37.1]
            }
          }
        ]
      }
    }
  ],
  "id": "uuid-string",
  "created_at": "2025-10-21T16:00:00Z",
  "updated_at": "2025-10-21T16:01:05Z"
}
```

### GET /api/v1/sessions?page=1&limit=20
List user's sessions.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "sess_a1b2c3d4",
      "title": "Pothole Issues Discussion",
      "domain_id": "civic_complaints_v1",
      "message_count": 10,
      "last_activity": "2025-10-21T16:05:00Z",
      "created_at": "2025-10-21T16:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1
  }
}
```

### PUT /api/v1/sessions/{session_id}
Update session metadata.

**Request Body:**
```json
{
  "title": "Updated Title"
}
```

**Response (200 OK):**
```json
{
  "session_id": "sess_a1b2c3d4",
  "title": "Updated Title",
  "domain_id": "civic_complaints_v1",
  "id": "uuid-string",
  "created_at": "2025-10-21T16:00:00Z",
  "updated_at": "2025-10-21T16:10:00Z"
}
```

### DELETE /api/v1/sessions/{session_id}
Delete session and all messages.

**Response (200 OK):**
```json
{
  "message": "Session deleted successfully",
  "session_id": "sess_a1b2c3d4"
}
```

## DynamoDB Tables

### Sessions Table
- **Partition Key**: `session_id` (String)
- **GSI**: `user-activity-index` (user_id, last_activity)
- **Attributes**:
  - session_id: Unique session identifier
  - user_id: Owner of the session
  - tenant_id: Tenant isolation
  - domain_id: Associated domain
  - title: Session title
  - message_count: Number of messages
  - id: UUID for standard metadata
  - created_at: Creation timestamp
  - updated_at: Last update timestamp
  - last_activity: Last message timestamp

### Messages Table
- **Partition Key**: `message_id` (String)
- **GSI**: `session-timestamp-index` (session_id, timestamp)
- **Attributes**:
  - message_id: Unique message identifier
  - session_id: Parent session
  - role: "user" or "assistant"
  - content: Message text
  - timestamp: Message timestamp
  - metadata: Optional metadata including references

## Message Grounding

Assistant messages include a `metadata` field with:
- `query_id`: The query that generated this response
- `references`: Array of source Reports used to generate the answer

This provides groundedness by linking responses to source data.

## Security

- **Tenant Isolation**: All queries filtered by tenant_id
- **User Isolation**: Users can only access their own sessions
- **Access Control**: Verified on every operation
- **CORS**: Configured for cross-origin requests

## Environment Variables

- `SESSIONS_TABLE`: DynamoDB table name for sessions
- `MESSAGES_TABLE`: DynamoDB table name for messages

## Error Handling

Standard error responses with:
- HTTP status code
- Error message
- Error code (ERR_XXX)
- Timestamp

Common errors:
- 400: Invalid request body or parameters
- 403: Access denied (wrong tenant/user)
- 404: Session not found
- 500: Internal server error

## Testing

Test the handler locally:

```bash
# Create session
curl -X POST https://api.example.com/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id": "civic_complaints_v1", "title": "Test Session"}'

# Get session
curl https://api.example.com/api/v1/sessions/sess_a1b2c3d4 \
  -H "Authorization: Bearer $TOKEN"

# List sessions
curl https://api.example.com/api/v1/sessions?page=1&limit=20 \
  -H "Authorization: Bearer $TOKEN"

# Update session
curl -X PUT https://api.example.com/api/v1/sessions/sess_a1b2c3d4 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Delete session
curl -X DELETE https://api.example.com/api/v1/sessions/sess_a1b2c3d4 \
  -H "Authorization: Bearer $TOKEN"
```

## Implementation Notes

1. **Cascade Delete**: When deleting a session, all associated messages are deleted first
2. **GSI Usage**: Uses user-activity-index for efficient session listing sorted by activity
3. **Pagination**: Supports pagination for session lists
4. **Message Ordering**: Messages returned in chronological order (oldest first)
5. **Activity Tracking**: last_activity updated when messages are added (handled by query handler)

## Related Components

- **Query Handler**: Creates assistant messages with references
- **Report Handler**: Provides source data for message references
- **AppSync**: Real-time updates for new messages (future enhancement)
