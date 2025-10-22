"""
Session Handler Lambda
Handles CRUD operations for session management with message grounding.
Manages chat sessions and messages with references to source data.
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback
from typing import Dict, Any, Optional, List

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables
SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE", "MultiAgentOrchestration-dev-Sessions")
MESSAGES_TABLE = os.environ.get("MESSAGES_TABLE", "MultiAgentOrchestration-dev-Messages")

# Initialize DynamoDB tables
try:
    sessions_table = dynamodb.Table(SESSIONS_TABLE)
    sessions_table.table_status
    print(f"Initialized Sessions table: {SESSIONS_TABLE}")
except Exception as e:
    print(f"Warning: Could not initialize Sessions table: {e}")
    sessions_table = None

try:
    messages_table = dynamodb.Table(MESSAGES_TABLE)
    messages_table.table_status
    print(f"Initialized Messages table: {MESSAGES_TABLE}")
except Exception as e:
    print(f"Warning: Could not initialize Messages table: {e}")
    messages_table = None


def handler(event, context):
    """
    Main Lambda handler for Session API
    Routes requests to appropriate CRUD operations
    """
    print(f"Event: {json.dumps(event, default=str)}")

    try:
        # Extract request details
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}

        # Extract tenant_id and user_id from authorizer
        tenant_id = extract_tenant_id(event)
        user_id = extract_user_id(event)

        print(f"Method: {http_method}, Path: {path}, Tenant: {tenant_id}, User: {user_id}")

        # Route based on HTTP method and path
        if http_method == "POST" and "/sessions" in path:
            return create_session(event, tenant_id, user_id)
        
        elif http_method == "GET" and path_parameters.get("session_id"):
            session_id = path_parameters["session_id"]
            return get_session(session_id, tenant_id, user_id)
        
        elif http_method == "GET" and "/sessions" in path:
            return list_sessions(event, tenant_id, user_id)
        
        elif http_method == "PUT" and path_parameters.get("session_id"):
            session_id = path_parameters["session_id"]
            return update_session(event, session_id, tenant_id, user_id)
        
        elif http_method == "DELETE" and path_parameters.get("session_id"):
            session_id = path_parameters["session_id"]
            return delete_session(session_id, tenant_id, user_id)
        
        else:
            return error_response(404, "Endpoint not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def create_session(event: dict, tenant_id: str, user_id: str) -> dict:
    """
    Create a new session
    POST /api/v1/sessions
    
    Request body:
    {
        "domain_id": "string (required)",
        "title": "string (optional, default: 'New Session')"
    }
    """
    # Parse request body
    body = parse_body(event)
    if isinstance(body, dict) and "error" in body:
        return error_response(400, body["error"])

    # Validate required fields
    domain_id = body.get("domain_id")
    if not domain_id:
        return error_response(400, "Missing required field: domain_id")

    # Get optional fields
    title = body.get("title", "New Session")

    # Generate IDs
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    session_uuid = str(uuid.uuid4())

    print(f"Creating session: session_id={session_id}, domain={domain_id}")

    # Create session document
    timestamp = datetime.utcnow().isoformat()
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "domain_id": domain_id,
        "title": title,
        "message_count": 0,
        "id": session_uuid,
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_activity": timestamp,
    }

    # Store to DynamoDB
    if not sessions_table:
        return error_response(500, "Sessions table not available")

    try:
        sessions_table.put_item(Item=session)
        print(f"Stored session: {session_id}")
    except Exception as e:
        print(f"Error storing to DynamoDB: {e}")
        return error_response(500, f"Failed to store session: {str(e)}")

    # Return 201 Created response
    return success_response(
        {
            "session_id": session_id,
            "domain_id": domain_id,
            "title": title,
            "id": session_uuid,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
        status_code=201,
    )


def get_session(session_id: str, tenant_id: str, user_id: str) -> dict:
    """
    Get a session with all messages
    GET /api/v1/sessions/{session_id}
    
    Response includes:
    - Session metadata
    - All messages with metadata (including references)
    """
    if not sessions_table or not messages_table:
        return error_response(500, "Sessions or Messages table not available")

    try:
        # Get session
        response = sessions_table.get_item(Key={"session_id": session_id})
        
        if "Item" not in response:
            return error_response(404, f"Session not found: {session_id}")
        
        session = response["Item"]
        
        # Verify tenant and user access
        if session.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this session")
        
        if session.get("user_id") != user_id:
            return error_response(403, "Access denied to this session")
        
        # Get all messages for this session
        messages_response = messages_table.query(
            IndexName="session-timestamp-index",
            KeyConditionExpression="session_id = :session_id",
            ExpressionAttributeValues={":session_id": session_id},
            ScanIndexForward=True,  # Sort by timestamp ascending
        )
        
        messages = messages_response.get("Items", [])
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "message_id": msg["message_id"],
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
            }
            
            # Include metadata if present
            if "metadata" in msg:
                formatted_msg["metadata"] = msg["metadata"]
            
            formatted_messages.append(formatted_msg)
        
        # Return full session with messages
        return success_response({
            "session_id": session["session_id"],
            "title": session["title"],
            "domain_id": session["domain_id"],
            "messages": formatted_messages,
            "id": session["id"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
        })

    except Exception as e:
        print(f"Error retrieving session: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to retrieve session: {str(e)}")


def list_sessions(event: dict, tenant_id: str, user_id: str) -> dict:
    """
    List sessions for the current user with pagination
    GET /api/v1/sessions?page=1&limit=20
    
    Uses user-activity GSI to get sessions sorted by last_activity
    """
    if not sessions_table:
        return error_response(500, "Sessions table not available")

    # Parse query parameters
    query_params = event.get("queryStringParameters") or {}
    page = int(query_params.get("page", 1))
    limit = int(query_params.get("limit", 20))

    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    try:
        # Query using user-activity GSI
        response = sessions_table.query(
            IndexName="user-activity-index",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
            ScanIndexForward=False,  # Sort by last_activity descending (most recent first)
        )
        
        items = response.get("Items", [])
        
        # Filter by tenant (additional security check)
        items = [item for item in items if item.get("tenant_id") == tenant_id]
        
        # Calculate pagination
        total = len(items)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = items[start_idx:end_idx]
        
        # Return simplified list view
        sessions = [
            {
                "session_id": item["session_id"],
                "title": item["title"],
                "domain_id": item["domain_id"],
                "message_count": item.get("message_count", 0),
                "last_activity": item.get("last_activity", item.get("created_at", "")),
                "created_at": item.get("created_at", ""),
            }
            for item in paginated_items
        ]
        
        return success_response({
            "sessions": sessions,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
            },
        })

    except Exception as e:
        print(f"Error listing sessions: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to list sessions: {str(e)}")


def update_session(event: dict, session_id: str, tenant_id: str, user_id: str) -> dict:
    """
    Update session metadata (title)
    PUT /api/v1/sessions/{session_id}
    
    Request body:
    {
        "title": "string (optional)"
    }
    """
    if not sessions_table:
        return error_response(500, "Sessions table not available")

    # Parse request body
    body = parse_body(event)
    if isinstance(body, dict) and "error" in body:
        return error_response(400, body["error"])

    # Get the existing session first
    try:
        response = sessions_table.get_item(Key={"session_id": session_id})
        
        if "Item" not in response:
            return error_response(404, f"Session not found: {session_id}")
        
        session = response["Item"]
        
        # Verify tenant and user access
        if session.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this session")
        
        if session.get("user_id") != user_id:
            return error_response(403, "Access denied to this session")

    except Exception as e:
        print(f"Error retrieving session: {e}")
        return error_response(500, f"Failed to retrieve session: {str(e)}")

    # Build update expression
    update_parts = []
    expression_values = {}

    # Update title if provided
    if "title" in body:
        update_parts.append("title = :title")
        expression_values[":title"] = body["title"]

    # Always update updated_at
    update_parts.append("updated_at = :updated_at")
    expression_values[":updated_at"] = datetime.utcnow().isoformat()

    if len(update_parts) == 1:  # Only updated_at
        return error_response(400, "No valid fields to update")

    # Perform update
    try:
        update_expression = "SET " + ", ".join(update_parts)
        
        response = sessions_table.update_item(
            Key={"session_id": session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW",
        )
        
        updated_session = response["Attributes"]
        
        return success_response({
            "session_id": updated_session["session_id"],
            "title": updated_session["title"],
            "domain_id": updated_session["domain_id"],
            "id": updated_session["id"],
            "created_at": updated_session["created_at"],
            "updated_at": updated_session["updated_at"],
        })

    except Exception as e:
        print(f"Error updating session: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to update session: {str(e)}")


def delete_session(session_id: str, tenant_id: str, user_id: str) -> dict:
    """
    Delete a session and cascade delete all messages
    DELETE /api/v1/sessions/{session_id}
    """
    if not sessions_table or not messages_table:
        return error_response(500, "Sessions or Messages table not available")

    # Get the session first to verify access
    try:
        response = sessions_table.get_item(Key={"session_id": session_id})
        
        if "Item" not in response:
            return error_response(404, f"Session not found: {session_id}")
        
        session = response["Item"]
        
        # Verify tenant and user access
        if session.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this session")
        
        if session.get("user_id") != user_id:
            return error_response(403, "Access denied to this session")

    except Exception as e:
        print(f"Error retrieving session: {e}")
        return error_response(500, f"Failed to retrieve session: {str(e)}")

    # Delete all messages for this session (cascade delete)
    try:
        # Query all messages for this session
        messages_response = messages_table.query(
            IndexName="session-timestamp-index",
            KeyConditionExpression="session_id = :session_id",
            ExpressionAttributeValues={":session_id": session_id},
        )
        
        messages = messages_response.get("Items", [])
        
        # Delete each message
        for msg in messages:
            messages_table.delete_item(Key={"message_id": msg["message_id"]})
        
        print(f"Deleted {len(messages)} messages for session {session_id}")

    except Exception as e:
        print(f"Warning: Error deleting messages: {e}")
        # Continue with session deletion even if message deletion fails

    # Delete the session
    try:
        sessions_table.delete_item(Key={"session_id": session_id})
        
        return success_response({
            "message": "Session deleted successfully",
            "session_id": session_id,
        })

    except Exception as e:
        print(f"Error deleting session: {e}")
        return error_response(500, f"Failed to delete session: {str(e)}")


def parse_body(event: dict) -> dict:
    """Parse request body from event"""
    body = event.get("body")
    if not body:
        return {"error": "Request body is required"}
    
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in request body"}


def extract_tenant_id(event: dict) -> str:
    """Extract tenant_id from authorizer context"""
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    
    tenant_id = authorizer.get("tenantId") or authorizer.get("tenant_id")
    if tenant_id:
        return tenant_id
    
    headers = event.get("headers", {})
    tenant_id = headers.get("X-Tenant-ID") or headers.get("x-tenant-id")
    if tenant_id:
        return tenant_id
    
    return "default-tenant"


def extract_user_id(event: dict) -> str:
    """Extract user_id from authorizer context"""
    authorizer = event.get("requestContext", {}).get("authorizer", {})
    
    user_id = (
        authorizer.get("userId")
        or authorizer.get("user_id")
        or authorizer.get("sub")
    )
    if user_id:
        return user_id
    
    return "demo-user"


def success_response(data: dict, status_code: int = 200) -> dict:
    """Return successful response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(data, default=str),
    }


def error_response(status_code: int, message: str) -> dict:
    """Return error response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps({
            "error": message,
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": f"ERR_{status_code}",
        }),
    }


def cors_headers() -> dict:
    """Return CORS headers"""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Tenant-ID",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }
