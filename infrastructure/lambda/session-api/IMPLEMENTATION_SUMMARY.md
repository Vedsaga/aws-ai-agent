# Session Handler Implementation Summary

## Overview

Implemented the Session Handler Lambda for managing chat sessions and messages with grounding references. This handler provides CRUD operations for sessions and supports message grounding to link assistant responses to source data.

## Files Created

1. **session_handler.py** - Main Lambda handler with all CRUD operations
2. **message_utils.py** - Helper utilities for message creation and management
3. **requirements.txt** - Python dependencies
4. **README.md** - Comprehensive documentation

## Implemented Functions

### Session Handler (session_handler.py)

#### 1. create_session()
- **Endpoint**: POST /api/v1/sessions
- **Purpose**: Create a new chat session for a domain
- **Input**: domain_id (required), title (optional)
- **Output**: Session object with session_id, domain_id, title, timestamps
- **Status Code**: 201 Created

#### 2. get_session()
- **Endpoint**: GET /api/v1/sessions/{session_id}
- **Purpose**: Retrieve session with all messages
- **Input**: session_id (path parameter)
- **Output**: Full session object with messages array including metadata
- **Status Code**: 200 OK
- **Features**:
  - Queries Messages table using session-timestamp-index GSI
  - Returns messages in chronological order
  - Includes message metadata with references

#### 3. list_sessions()
- **Endpoint**: GET /api/v1/sessions?page=1&limit=20
- **Purpose**: List user's sessions with pagination
- **Input**: page (optional), limit (optional)
- **Output**: Paginated list of sessions sorted by last_activity
- **Status Code**: 200 OK
- **Features**:
  - Uses user-activity-index GSI for efficient querying
  - Sorts by last_activity descending (most recent first)
  - Includes message_count and last_activity for each session

#### 4. update_session()
- **Endpoint**: PUT /api/v1/sessions/{session_id}
- **Purpose**: Update session metadata (title)
- **Input**: session_id (path parameter), title (optional)
- **Output**: Updated session object
- **Status Code**: 200 OK
- **Features**:
  - Validates user and tenant access
  - Updates updated_at timestamp automatically

#### 5. delete_session()
- **Endpoint**: DELETE /api/v1/sessions/{session_id}
- **Purpose**: Delete session and cascade delete all messages
- **Input**: session_id (path parameter)
- **Output**: Confirmation message
- **Status Code**: 200 OK
- **Features**:
  - Cascade delete: Removes all messages first
  - Validates user and tenant access
  - Logs number of messages deleted

### Message Utilities (message_utils.py)

#### 1. create_user_message()
- Creates a user message in a session
- Updates session last_activity and message_count
- Returns created message document

#### 2. create_assistant_message()
- Creates an assistant message with grounding references
- Includes metadata with query_id and references array
- Updates session last_activity and message_count
- Provides groundedness by linking to source Reports

#### 3. get_session_messages()
- Retrieves all messages for a session
- Uses session-timestamp-index GSI
- Returns messages in chronological order
- Supports optional limit parameter

#### 4. delete_session_messages()
- Deletes all messages for a session (cascade delete)
- Returns count of deleted messages
- Used by delete_session() handler

#### 5. format_references_from_query_result()
- Extracts and formats references from query results
- Ensures references have required fields
- Used when creating assistant messages from query responses

## Security Features

1. **Tenant Isolation**: All operations filtered by tenant_id
2. **User Isolation**: Users can only access their own sessions
3. **Access Verification**: Checked on every operation (get, update, delete)
4. **CORS Support**: Configured for cross-origin requests

## DynamoDB Integration

### Sessions Table
- **Partition Key**: session_id
- **GSI**: user-activity-index (user_id, last_activity)
- **Attributes**: session_id, user_id, tenant_id, domain_id, title, message_count, id, created_at, updated_at, last_activity

### Messages Table
- **Partition Key**: message_id
- **GSI**: session-timestamp-index (session_id, timestamp)
- **Attributes**: message_id, session_id, role, content, timestamp, metadata

## Message Grounding

Assistant messages include a `metadata` field with:
- **query_id**: Links to the query that generated the response
- **references**: Array of source Reports used to generate the answer

Example reference structure:
```json
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
```

This provides groundedness by allowing users to trace assistant responses back to source data.

## Error Handling

Standard error responses with:
- HTTP status code (400, 403, 404, 500)
- Error message
- Error code (ERR_XXX)
- Timestamp

Common errors:
- **400**: Invalid request body or parameters
- **403**: Access denied (wrong tenant/user)
- **404**: Session not found
- **500**: Internal server error

## Environment Variables

- `SESSIONS_TABLE`: DynamoDB table name for sessions (default: MultiAgentOrchestration-dev-Sessions)
- `MESSAGES_TABLE`: DynamoDB table name for messages (default: MultiAgentOrchestration-dev-Messages)

## Requirements Met

✅ **Requirement 5.1**: Create session with domain_id and title
✅ **Requirement 5.2**: Get session with all messages including metadata references
✅ **Requirement 5.3**: List sessions with pagination, message_count, and last_activity
✅ **Requirement 5.4**: Update session metadata (title)
✅ **Requirement 5.5**: Delete session with cascade to messages

## Integration Points

### Query Handler Integration
The Query Handler should use `create_assistant_message()` from message_utils.py to create assistant messages with references after query completion:

```python
from message_utils import create_assistant_message, format_references_from_query_result

# After query completes
references = format_references_from_query_result(query_result)
message = create_assistant_message(
    session_id=session_id,
    content=query_result["summary"],
    query_id=query_result["query_id"],
    references=references,
    messages_table_name=MESSAGES_TABLE,
    sessions_table_name=SESSIONS_TABLE,
)
```

### Frontend Integration
The frontend can:
1. Create sessions when starting a new conversation
2. Display messages with references as clickable links
3. Show reference details (location on map, status, etc.)
4. Update session titles for better organization
5. Delete old sessions to clean up

## Testing Recommendations

1. **Unit Tests**:
   - Test session CRUD operations
   - Test message grounding with references
   - Test cascade delete
   - Test pagination
   - Test access control (tenant/user isolation)

2. **Integration Tests**:
   - Create session → Submit query → Verify assistant message with references
   - List sessions → Verify sorting by last_activity
   - Delete session → Verify messages are deleted

3. **Manual Testing**:
   - Use curl commands from README.md
   - Test with multiple users/tenants
   - Verify GSI queries are efficient

## Next Steps

1. **Deploy Lambda**: Add to CDK stack with proper IAM permissions
2. **Create DynamoDB Tables**: Ensure Sessions and Messages tables exist with GSIs
3. **Add API Gateway Routes**: Configure routes for /api/v1/sessions endpoints
4. **Update Query Handler**: Integrate message_utils.py for assistant message creation
5. **Frontend Integration**: Update UI to use session endpoints
6. **Write Tests**: Add unit and integration tests

## Notes

- The handler follows the same pattern as report_handler.py and agent_handler.py for consistency
- Message grounding provides traceability from answers to source data
- Cascade delete ensures no orphaned messages
- GSI usage enables efficient querying by user and session
- The implementation is ready for deployment and testing
