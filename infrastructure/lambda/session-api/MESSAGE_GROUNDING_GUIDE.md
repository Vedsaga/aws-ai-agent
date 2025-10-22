# Message Grounding Implementation Guide

## Overview

Message grounding links assistant responses to source data (Reports) for transparency and traceability. This implementation provides functions to create grounded messages in chat sessions.

## Implementation Status

✅ **COMPLETED** - Task 19: Implement message grounding

### What Was Implemented

1. **`create_assistant_message()`** - Creates assistant messages with references metadata
2. **`create_user_message()`** - Creates user messages in sessions
3. **`format_references_from_query_result()`** - Formats references from query results
4. **Integration with Query Handler** - Functions to update queries and create messages
5. **Session Activity Tracking** - Updates `last_activity` and `message_count` on message creation

## Core Functions

### 1. create_assistant_message()

Creates an assistant message with grounding references linking to source Reports.

**Location**: `infrastructure/lambda/session-api/message_utils.py`

**Signature**:
```python
def create_assistant_message(
    session_id: str,
    content: str,
    query_id: str,
    references: List[Dict[str, Any]],
    messages_table_name: str,
    sessions_table_name: str,
) -> Dict[str, Any]
```

**Parameters**:
- `session_id`: The session ID where the message belongs
- `content`: The assistant's response text (summary/answer)
- `query_id`: The query ID that generated this response
- `references`: Array of source Reports used to generate the answer
- `messages_table_name`: DynamoDB table name for messages
- `sessions_table_name`: DynamoDB table name for sessions

**Returns**: The created message document with metadata

**Example Usage**:
```python
from message_utils import create_assistant_message

# After query completes with results
message = create_assistant_message(
    session_id="sess_abc123",
    content="I found 5 pothole reports in your area.",
    query_id="qry_xyz789",
    references=[
        {
            "type": "report",
            "reference_id": "inc_report1",
            "summary": "Pothole on Main Street",
            "status": "pending",
            "location": {
                "type": "Point",
                "coordinates": [36.9, 37.1]
            }
        }
    ],
    messages_table_name="MultiAgentOrchestration-dev-Messages",
    sessions_table_name="MultiAgentOrchestration-dev-Sessions",
)

print(f"Created message: {message['message_id']}")
```

**Message Structure**:
```json
{
  "message_id": "msg_12345678",
  "session_id": "sess_abc123",
  "role": "assistant",
  "content": "I found 5 pothole reports in your area.",
  "timestamp": "2025-10-21T16:05:00Z",
  "metadata": {
    "query_id": "qry_xyz789",
    "references": [
      {
        "type": "report",
        "reference_id": "inc_report1",
        "summary": "Pothole on Main Street",
        "status": "pending",
        "location": {
          "type": "Point",
          "coordinates": [36.9, 37.1]
        }
      }
    ]
  }
}
```

### 2. create_user_message()

Creates a user message in a session.

**Signature**:
```python
def create_user_message(
    session_id: str,
    content: str,
    messages_table_name: str,
    sessions_table_name: str,
) -> Dict[str, Any]
```

**Example Usage**:
```python
from message_utils import create_user_message

message = create_user_message(
    session_id="sess_abc123",
    content="Show me all potholes in my area",
    messages_table_name="MultiAgentOrchestration-dev-Messages",
    sessions_table_name="MultiAgentOrchestration-dev-Sessions",
)
```

### 3. format_references_from_query_result()

Extracts and formats references from a query result.

**Signature**:
```python
def format_references_from_query_result(
    query_result: Dict[str, Any]
) -> List[Dict[str, Any]]
```

**Example Usage**:
```python
from message_utils import format_references_from_query_result

query_result = {
    "query_id": "qry_123",
    "references_used": [
        {
            "type": "report",
            "reference_id": "inc_1",
            "summary": "Test report",
            "status": "pending"
        }
    ]
}

references = format_references_from_query_result(query_result)
```

## Integration with Query Handler

The query handler now includes helper functions for creating messages when queries complete.

**Location**: `infrastructure/lambda/orchestration/query_handler_simple.py`

### create_query_completion_message()

Creates an assistant message when a query completes.

**Signature**:
```python
def create_query_completion_message(query_result: dict) -> dict
```

**Example Usage**:
```python
# After orchestrator completes query processing
query_result = {
    "query_id": "qry_123",
    "session_id": "sess_abc",
    "summary": "Found 5 potholes",
    "references_used": [...]
}

result = create_query_completion_message(query_result)
if result.get("success"):
    print(f"Created message: {result['message_id']}")
```

### update_query_and_create_message()

Updates a query with results and creates an assistant message.

**Signature**:
```python
def update_query_and_create_message(
    query_id: str,
    status: str,
    summary: str = "",
    map_data: dict = None,
    references_used: list = None,
    execution_log: list = None,
) -> dict
```

**Example Usage (for Orchestrator)**:
```python
# When orchestrator completes query processing
result = update_query_and_create_message(
    query_id="qry_123",
    status="completed",
    summary="I found 5 pothole reports in your area.",
    map_data={
        "map_action": "FIT_BOUNDS",
        "data": {"type": "FeatureCollection", "features": [...]}
    },
    references_used=[
        {
            "type": "report",
            "reference_id": "inc_1",
            "summary": "Pothole on Main St",
            "status": "pending"
        }
    ],
    execution_log=[...]
)

if result.get("success"):
    print(f"Query updated and message created: {result['message_id']}")
```

## Session Activity Tracking

Both `create_assistant_message()` and `create_user_message()` automatically update the session:

1. **last_activity**: Set to current timestamp
2. **message_count**: Incremented by 1
3. **updated_at**: Set to current timestamp

This ensures sessions reflect the latest activity for sorting and display.

## Reference Structure

References link assistant responses to source Reports:

```json
{
  "type": "report",
  "reference_id": "inc_abc123",
  "summary": "Brief description of the report",
  "status": "pending",
  "location": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  }
}
```

**Required Fields**:
- `type`: Always "report"
- `reference_id`: The incident_id from Reports table
- `summary`: Brief description

**Optional Fields**:
- `status`: Report status
- `location`: GeoJSON Point for map display

## Requirements Satisfied

### Requirement 5.2
✅ **WHEN a user sends a GET request to `/api/v1/sessions/{session_id}`, THE API Gateway SHALL return the session with all messages including metadata references with HTTP 200**

The session handler returns messages with metadata including references.

### Requirement 5.3
✅ **WHEN a user sends a GET request to `/api/v1/sessions`, THE API Gateway SHALL return a paginated list of sessions with message_count and last_activity with HTTP 200**

Sessions include `message_count` and `last_activity` which are updated on message creation.

## Testing

Run the test suite:

```bash
cd infrastructure/lambda/session-api
python3 test_message_grounding.py
```

**Test Coverage**:
- ✅ Create assistant message with references
- ✅ Create user message
- ✅ Format references from query result
- ✅ Handle empty references
- ✅ Session activity tracking

## Usage Flow

### Complete Query Processing Flow

1. **User submits query** → POST /api/v1/queries
2. **Query handler creates query record** → QueryJobs table
3. **Orchestrator processes query** → Executes agents
4. **Orchestrator completes** → Calls `update_query_and_create_message()`
5. **Query updated** → QueryJobs table with results
6. **Assistant message created** → Messages table with references
7. **Session updated** → last_activity and message_count updated
8. **User retrieves session** → GET /api/v1/sessions/{session_id}
9. **Frontend displays** → Shows grounded conversation with references

### Example: Complete Integration

```python
# In orchestrator after query completes
from query_handler_simple import update_query_and_create_message

# Update query and create grounded message
result = update_query_and_create_message(
    query_id=job_data["query_id"],
    status="completed",
    summary=synthesized_answer,
    map_data=map_visualization,
    references_used=source_reports,
    execution_log=agent_steps,
)

if result.get("success"):
    print(f"✅ Query completed and message created")
    print(f"   Query ID: {result['query_id']}")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Session updated with activity")
else:
    print(f"❌ Error: {result.get('error')}")
```

## Next Steps

The orchestrator should be updated to call `update_query_and_create_message()` when query processing completes. This will automatically:

1. Update the query record with results
2. Create a grounded assistant message
3. Update session activity
4. Enable full conversation history with references

## Benefits

1. **Transparency**: Users can see which reports were used to generate answers
2. **Traceability**: Every response links back to source data
3. **Debugging**: Developers can trace reasoning chains
4. **Trust**: Users trust answers backed by real data
5. **Navigation**: Users can click references to view full reports

## Files Modified

- ✅ `infrastructure/lambda/session-api/message_utils.py` - Core implementation
- ✅ `infrastructure/lambda/orchestration/query_handler_simple.py` - Integration functions
- ✅ `infrastructure/lambda/session-api/test_message_grounding.py` - Test suite
- ✅ `infrastructure/lambda/session-api/MESSAGE_GROUNDING_GUIDE.md` - This guide

## Status

**Task 19: Implement message grounding** - ✅ COMPLETED

All sub-tasks completed:
- ✅ Write create_assistant_message() with references metadata
- ✅ Add references array linking to source Reports
- ✅ Update session last_activity on message creation
- ✅ Integration with query handler
- ✅ Test coverage
