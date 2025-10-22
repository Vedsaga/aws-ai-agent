"""
Query Handler - CRUD operations for Queries
Handles query submission, retrieval, and deletion
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback
from typing import Dict, Any, Optional

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables
QUERY_JOBS_TABLE = os.environ.get("QUERY_JOBS_TABLE", "MultiAgentOrchestration-dev-QueryJobs")
ORCHESTRATOR_FUNCTION = os.environ.get("ORCHESTRATOR_FUNCTION", "")

# Initialize DynamoDB table
try:
    query_jobs_table = dynamodb.Table(QUERY_JOBS_TABLE)
    query_jobs_table.table_status
    print(f"Initialized QueryJobs table: {QUERY_JOBS_TABLE}")
except Exception as e:
    print(f"Warning: Could not initialize QueryJobs table: {e}")
    query_jobs_table = None


def handler(event, context):
    """
    Main Lambda handler for Query API
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
        if http_method == "POST" and "/queries" in path:
            return create_query(event, tenant_id, user_id)
        
        elif http_method == "GET" and path_parameters.get("query_id"):
            query_id = path_parameters["query_id"]
            return get_query(query_id, tenant_id)
        
        elif http_method == "GET" and "/queries" in path:
            return list_queries(event, tenant_id)
        
        elif http_method == "DELETE" and path_parameters.get("query_id"):
            query_id = path_parameters["query_id"]
            return delete_query(query_id, tenant_id)
        
        else:
            return error_response(404, "Endpoint not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def create_query(event: dict, tenant_id: str, user_id: str) -> dict:
    """
    Create a new query and trigger query playbook
    POST /api/v1/queries
    """
    # Parse request body
    body = parse_body(event)
    if isinstance(body, dict) and "error" in body:
        return error_response(400, body["error"])

    # Validate required fields
    session_id = body.get("session_id")
    domain_id = body.get("domain_id")
    question = body.get("question")

    if not session_id:
        return error_response(400, "Missing required field: session_id")
    
    if not domain_id:
        return error_response(400, "Missing required field: domain_id")
    
    if not question:
        return error_response(400, "Missing required field: question")

    # Validate question length
    if len(question) > 5000:
        return error_response(400, "Question exceeds maximum length of 5000 characters")

    # Generate IDs
    job_id = f"job_{uuid.uuid4().hex}"
    query_id = f"qry_{uuid.uuid4().hex[:8]}"

    print(f"Creating query: query_id={query_id}, session={session_id}, domain={domain_id}")

    # Create query document
    timestamp = datetime.utcnow().isoformat()
    query = {
        "query_id": query_id,
        "job_id": job_id,
        "tenant_id": tenant_id,
        "session_id": session_id,
        "domain_id": domain_id,
        "question": question,
        "status": "processing",
        "summary": "",  # Will be populated by query agents
        "map_data": None,  # Optional map visualization data
        "references_used": [],  # References from RAG
        "execution_log": [],  # Agent execution details
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_by": user_id,
    }

    # Store to DynamoDB
    if not query_jobs_table:
        return error_response(500, "Query jobs table not available")

    try:
        query_jobs_table.put_item(Item=query)
        print(f"Stored query: {query_id}")
    except Exception as e:
        print(f"Error storing to DynamoDB: {e}")
        return error_response(500, f"Failed to store query: {str(e)}")

    # Trigger orchestrator Lambda asynchronously with query playbook
    if ORCHESTRATOR_FUNCTION:
        try:
            orchestrator_payload = {
                "job_id": job_id,
                "job_type": "query",
                "query_id": query_id,
                "session_id": session_id,
                "domain_id": domain_id,
                "question": question,
                "tenant_id": tenant_id,
                "user_id": user_id,
            }

            lambda_client.invoke(
                FunctionName=ORCHESTRATOR_FUNCTION,
                InvocationType="Event",  # Async invocation
                Payload=json.dumps(orchestrator_payload),
            )
            print(f"Triggered orchestrator for job {job_id}")
        except Exception as e:
            print(f"Warning: Could not trigger orchestrator: {e}")

    # Return 202 Accepted response
    return success_response(
        {
            "job_id": job_id,
            "query_id": query_id,
            "session_id": session_id,
            "status": "accepted",
            "message": "Query submitted for processing",
            "timestamp": timestamp,
        },
        status_code=202,
    )


def get_query(query_id: str, tenant_id: str) -> dict:
    """
    Get a query by query_id
    GET /api/v1/queries/{query_id}
    """
    if not query_jobs_table:
        return error_response(500, "Query jobs table not available")

    try:
        response = query_jobs_table.get_item(Key={"query_id": query_id})
        
        if "Item" not in response:
            return error_response(404, f"Query not found: {query_id}")
        
        query = response["Item"]
        
        # Verify tenant access
        if query.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this query")
        
        # Return full document structure with execution_log
        return success_response(query)

    except Exception as e:
        print(f"Error retrieving query: {e}")
        return error_response(500, f"Failed to retrieve query: {str(e)}")


def list_queries(event: dict, tenant_id: str) -> dict:
    """
    List queries with filtering and pagination
    GET /api/v1/queries?page=1&limit=20&session_id=sess_123&status=completed
    """
    if not query_jobs_table:
        return error_response(500, "Query jobs table not available")

    # Parse query parameters
    query_params = event.get("queryStringParameters") or {}
    page = int(query_params.get("page", 1))
    limit = int(query_params.get("limit", 20))
    session_id = query_params.get("session_id")
    status = query_params.get("status")

    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    try:
        # Build query based on filters
        if session_id:
            # Use GSI: session-created-index
            query_kwargs = {
                "IndexName": "session-created-index",
                "KeyConditionExpression": "session_id = :session_id",
                "ExpressionAttributeValues": {":session_id": session_id},
                "ScanIndexForward": False,  # Sort by created_at descending
            }
            
            # Add status filter if provided
            if status:
                query_kwargs["FilterExpression"] = "#status = :status"
                query_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
                query_kwargs["ExpressionAttributeValues"][":status"] = status
            
            response = query_jobs_table.query(**query_kwargs)
        else:
            # Scan with tenant filter (less efficient, but works)
            scan_kwargs = {
                "FilterExpression": "tenant_id = :tenant_id",
                "ExpressionAttributeValues": {":tenant_id": tenant_id},
            }
            
            if status:
                scan_kwargs["FilterExpression"] += " AND #status = :status"
                scan_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
                scan_kwargs["ExpressionAttributeValues"][":status"] = status
            
            response = query_jobs_table.scan(**scan_kwargs)

        items = response.get("Items", [])
        
        # Filter by tenant (additional security check)
        items = [item for item in items if item.get("tenant_id") == tenant_id]
        
        # Sort by created_at descending
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Calculate pagination
        total = len(items)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = items[start_idx:end_idx]
        
        # Return simplified list view
        queries = [
            {
                "query_id": item["query_id"],
                "session_id": item["session_id"],
                "domain_id": item["domain_id"],
                "question": item.get("question", "")[:200],  # Truncate for list view
                "status": item.get("status", "unknown"),
                "created_at": item.get("created_at", ""),
            }
            for item in paginated_items
        ]
        
        return success_response({
            "queries": queries,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
            },
        })

    except Exception as e:
        print(f"Error listing queries: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to list queries: {str(e)}")


def delete_query(query_id: str, tenant_id: str) -> dict:
    """
    Delete a query
    DELETE /api/v1/queries/{query_id}
    """
    if not query_jobs_table:
        return error_response(500, "Query jobs table not available")

    # Get the query first to verify tenant access
    try:
        response = query_jobs_table.get_item(Key={"query_id": query_id})
        
        if "Item" not in response:
            return error_response(404, f"Query not found: {query_id}")
        
        query = response["Item"]
        
        # Verify tenant access
        if query.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this query")

    except Exception as e:
        print(f"Error retrieving query: {e}")
        return error_response(500, f"Failed to retrieve query: {str(e)}")

    # Delete the query
    try:
        query_jobs_table.delete_item(Key={"query_id": query_id})
        
        return success_response({
            "message": "Query deleted successfully",
            "query_id": query_id,
        })

    except Exception as e:
        print(f"Error deleting query: {e}")
        return error_response(500, f"Failed to delete query: {str(e)}")


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
        "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    }
