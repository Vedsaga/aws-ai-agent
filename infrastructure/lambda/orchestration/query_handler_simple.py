"""
Query API Handler - Handles data read/update via query/management agents
Routes to appropriate playbook based on mode parameter
"""

import json
import os
import boto3
import sys
from datetime import datetime
import uuid
import traceback

# Add session-api module to path for message utilities
session_api_path = os.path.join(os.path.dirname(__file__), "../session-api")
if os.path.exists(session_api_path):
    sys.path.insert(0, os.path.dirname(session_api_path))

try:
    from session_api.message_utils import create_assistant_message, format_references_from_query_result
    print("Message utils loaded successfully")
except ImportError as e:
    print(f"Warning: message_utils not available: {e}")
    create_assistant_message = None
    format_references_from_query_result = None

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables with fallbacks
QUERY_JOBS_TABLE = os.environ.get(
    "QUERY_JOBS_TABLE", "MultiAgentOrchestration-dev-QueryJobs"
)
ORCHESTRATOR_FUNCTION = os.environ.get(
    "ORCHESTRATOR_FUNCTION", "MultiAgentOrchestration-dev-Orchestrator"
)
SESSIONS_TABLE = os.environ.get(
    "SESSIONS_TABLE", "MultiAgentOrchestration-dev-Sessions"
)
MESSAGES_TABLE = os.environ.get(
    "MESSAGES_TABLE", "MultiAgentOrchestration-dev-Messages"
)

# Initialize DynamoDB table (create if doesn't exist)
try:
    query_jobs_table = dynamodb.Table(QUERY_JOBS_TABLE)
    # Test if table exists
    query_jobs_table.table_status
except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    print(f"Creating QueryJobs table: {QUERY_JOBS_TABLE}")
    try:
        query_jobs_table = dynamodb.create_table(
            TableName=QUERY_JOBS_TABLE,
            KeySchema=[{"AttributeName": "query_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "query_id", "AttributeType": "S"},
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "session-created-index",
                    "KeySchema": [
                        {"AttributeName": "session_id", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created QueryJobs table: {QUERY_JOBS_TABLE}")
    except Exception as e:
        print(f"Error creating table: {e}")
        query_jobs_table = None
except Exception as e:
    print(f"Warning: Could not initialize QueryJobs table: {e}")
    query_jobs_table = None


def handler(event, context):
    """
    Main Lambda handler for query API
    Routes to query_playbook or management_playbook based on mode parameter
    """
    print(f"Event: {json.dumps(event)}")

    try:
        # Extract request details
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")

        # Parse body
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event.get("body"))
            except:
                return error_response(400, "Invalid JSON in request body")

        # Extract tenant_id and user_id
        tenant_id = extract_tenant_id(event)
        user_id = extract_user_id(event)

        print(f"Method: {http_method}, Path: {path}, Tenant: {tenant_id}")

        # Route based on HTTP method
        if http_method == "POST":
            return handle_submit_query(body, tenant_id, user_id)
        elif http_method == "GET":
            # Check if it's a list or get operation
            path_params = event.get("pathParameters", {})
            query_id = path_params.get("query_id") if path_params else None
            query_params = event.get("queryStringParameters", {}) or {}
            
            if query_id:
                return handle_get_query(query_id, tenant_id)
            else:
                return handle_list_queries(query_params, tenant_id)
        elif http_method == "DELETE":
            path_params = event.get("pathParameters", {})
            query_id = path_params.get("query_id") if path_params else None
            
            if not query_id:
                return error_response(400, "Missing query_id in path")
            
            return handle_delete_query(query_id, tenant_id)
        else:
            return error_response(405, "Method not allowed")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def handle_submit_query(body, tenant_id, user_id):
    """
    Handle POST /api/v1/queries - Submit a new query
    """
    try:

        # Validate required fields
        session_id = body.get("session_id")
        domain_id = body.get("domain_id")
        question = body.get("question")
        mode = body.get("mode", "query")  # Default to 'query' mode

        if not session_id:
            return error_response(400, "Missing required field: session_id")

        if not domain_id:
            return error_response(400, "Missing required field: domain_id")

        if not question:
            return error_response(400, "Missing required field: question")

        # Validate mode parameter
        if mode not in ["query", "management"]:
            return error_response(
                400, "Invalid mode parameter. Must be 'query' or 'management'"
            )

        # Validate question length
        if len(question) > 1000:
            return error_response(
                400, "Question exceeds maximum length of 1000 characters"
            )

        # Generate job and query IDs
        job_id = f"query_{uuid.uuid4().hex}"
        query_id = f"qry_{uuid.uuid4().hex[:8]}"

        print(
            f"Processing query: job_id={job_id}, query_id={query_id}, domain={domain_id}, mode={mode}, question_length={len(question)}"
        )

        # Create query record
        query_record = {
            "query_id": query_id,
            "job_id": job_id,
            "session_id": session_id,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "question": question,
            "mode": mode,
            "status": "processing",
            "id": query_id,  # Standard metadata
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
        }

        # Add placeholder for results (will be populated by orchestrator)
        query_record["summary"] = ""
        query_record["map_data"] = {}
        query_record["references_used"] = []
        query_record["execution_log"] = []
        # completed_at will be set by orchestrator when job finishes

        # Store to DynamoDB
        if query_jobs_table:
            try:
                query_jobs_table.put_item(Item=query_record)
                print(f"Stored query: {query_id}")
            except Exception as e:
                print(f"Error storing to DynamoDB: {e}")
                return error_response(500, f"Failed to store query: {str(e)}")
        else:
            # If table doesn't exist, still return success but log warning
            print("WARNING: QueryJobs table not available, query not stored")

        # Trigger orchestrator Lambda asynchronously
        try:
            # Determine playbook type based on mode
            playbook_type = "query_playbook" if mode == "query" else "management_playbook"
            
            orchestrator_payload = {
                "job_id": job_id,
                "job_type": mode,  # 'query' or 'management'
                "playbook_type": playbook_type,
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
            print(f"Triggered orchestrator Lambda async for query {job_id} with {playbook_type}")
        except Exception as e:
            print(f"Warning: Could not trigger orchestrator: {e}")
            # Don't fail the request, orchestrator can be triggered later

        # Return success response with job_id and query_id
        return success_response(
            {
                "job_id": job_id,
                "query_id": query_id,
                "session_id": session_id,
                "status": "accepted",
                "message": "Query submitted for processing",
                "timestamp": datetime.utcnow().isoformat(),
            },
            status_code=202,
        )

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def handle_get_query(query_id, tenant_id):
    """
    Handle GET /api/v1/queries/{query_id} - Get query result
    """
    try:
        if not query_jobs_table:
            return error_response(500, "QueryJobs table not available")

        # Get query from DynamoDB
        response = query_jobs_table.get_item(Key={"query_id": query_id})
        
        if "Item" not in response:
            return error_response(404, f"Query not found: {query_id}")
        
        query = response["Item"]
        
        # Verify tenant access
        if query.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this query")
        
        # Return query with all fields
        return success_response(query)

    except Exception as e:
        print(f"ERROR getting query: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to get query: {str(e)}")


def handle_list_queries(query_params, tenant_id):
    """
    Handle GET /api/v1/queries - List queries with optional filtering
    """
    try:
        if not query_jobs_table:
            return error_response(500, "QueryJobs table not available")

        # Parse pagination parameters
        page = int(query_params.get("page", 1))
        limit = int(query_params.get("limit", 20))
        session_id = query_params.get("session_id")
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        # Query based on session_id filter
        if session_id:
            # Use GSI to filter by session_id
            response = query_jobs_table.query(
                IndexName="session-created-index",
                KeyConditionExpression="session_id = :session_id",
                ExpressionAttributeValues={":session_id": session_id},
                ScanIndexForward=False,  # Sort by created_at descending
            )
        else:
            # Scan all queries for tenant (not ideal, but works for demo)
            response = query_jobs_table.scan(
                FilterExpression="tenant_id = :tenant_id",
                ExpressionAttributeValues={":tenant_id": tenant_id},
            )
        
        queries = response.get("Items", [])
        
        # Sort by created_at descending
        queries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Calculate pagination
        total = len(queries)
        start = (page - 1) * limit
        end = start + limit
        paginated_queries = queries[start:end]
        
        # Return simplified query list
        query_list = [
            {
                "query_id": q.get("query_id"),
                "question": q.get("question"),
                "status": q.get("status"),
                "created_at": q.get("created_at"),
            }
            for q in paginated_queries
        ]
        
        return success_response({
            "queries": query_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
            }
        })

    except Exception as e:
        print(f"ERROR listing queries: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to list queries: {str(e)}")


def handle_delete_query(query_id, tenant_id):
    """
    Handle DELETE /api/v1/queries/{query_id} - Delete a query
    """
    try:
        if not query_jobs_table:
            return error_response(500, "QueryJobs table not available")

        # Get query first to verify ownership
        response = query_jobs_table.get_item(Key={"query_id": query_id})
        
        if "Item" not in response:
            return error_response(404, f"Query not found: {query_id}")
        
        query = response["Item"]
        
        # Verify tenant access
        if query.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this query")
        
        # Delete query
        query_jobs_table.delete_item(Key={"query_id": query_id})
        
        print(f"Deleted query: {query_id}")
        
        return success_response({
            "message": "Query deleted successfully",
            "query_id": query_id,
        })

    except Exception as e:
        print(f"ERROR deleting query: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to delete query: {str(e)}")


def create_query_completion_message(query_result: dict) -> dict:
    """
    Create an assistant message in the session when a query completes.
    This implements message grounding by linking the assistant's response
    to the source reports used to generate the answer.
    
    Args:
        query_result: The completed query result from QueryJobs table
    
    Returns:
        The created message document or error dict
    
    This function should be called by the orchestrator after query completion.
    """
    try:
        # Validate required fields
        session_id = query_result.get("session_id")
        query_id = query_result.get("query_id")
        summary = query_result.get("summary", "")
        references_used = query_result.get("references_used", [])
        
        if not session_id:
            print("ERROR: Missing session_id in query result")
            return {"error": "Missing session_id"}
        
        if not query_id:
            print("ERROR: Missing query_id in query result")
            return {"error": "Missing query_id"}
        
        # Check if message utils are available
        if not create_assistant_message:
            print("WARNING: create_assistant_message not available, skipping message creation")
            return {"error": "Message utils not available"}
        
        # Format references if needed
        if format_references_from_query_result:
            references = format_references_from_query_result(query_result)
        else:
            references = references_used
        
        # Create assistant message with grounding references
        message = create_assistant_message(
            session_id=session_id,
            content=summary,
            query_id=query_id,
            references=references,
            messages_table_name=MESSAGES_TABLE,
            sessions_table_name=SESSIONS_TABLE,
        )
        
        print(f"Created assistant message {message['message_id']} for query {query_id} in session {session_id}")
        
        return {
            "success": True,
            "message_id": message["message_id"],
            "session_id": session_id,
        }
        
    except Exception as e:
        print(f"ERROR creating query completion message: {str(e)}")
        print(traceback.format_exc())
        return {"error": str(e)}


def update_query_and_create_message(
    query_id: str,
    status: str,
    summary: str = "",
    map_data: dict = None,
    references_used: list = None,
    execution_log: list = None,
) -> dict:
    """
    Update a query with results and create an assistant message in the session.
    This is a helper function for the orchestrator to call when query processing completes.
    
    Args:
        query_id: The query ID to update
        status: Query status ('completed' or 'failed')
        summary: The generated summary/answer
        map_data: Geographic visualization data
        references_used: Array of source reports
        execution_log: Array of agent execution steps
    
    Returns:
        Update result with message_id if successful
    """
    try:
        if not query_jobs_table:
            return {"error": "QueryJobs table not available"}
        
        # Get existing query
        response = query_jobs_table.get_item(Key={"query_id": query_id})
        
        if "Item" not in response:
            return {"error": f"Query not found: {query_id}"}
        
        query = response["Item"]
        
        # Build update expression
        update_parts = ["#status = :status", "completed_at = :completed_at"]
        expression_values = {
            ":status": status,
            ":completed_at": datetime.utcnow().isoformat(),
        }
        expression_names = {"#status": "status"}
        
        if summary:
            update_parts.append("summary = :summary")
            expression_values[":summary"] = summary
        
        if map_data is not None:
            update_parts.append("map_data = :map_data")
            expression_values[":map_data"] = map_data
        
        if references_used is not None:
            update_parts.append("references_used = :references_used")
            expression_values[":references_used"] = references_used
        
        if execution_log is not None:
            update_parts.append("execution_log = :execution_log")
            expression_values[":execution_log"] = execution_log
        
        # Update query in DynamoDB
        update_expression = "SET " + ", ".join(update_parts)
        
        query_jobs_table.update_item(
            Key={"query_id": query_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
        )
        
        print(f"Updated query {query_id} with status {status}")
        
        # If query completed successfully, create assistant message
        if status == "completed" and summary:
            # Get updated query
            response = query_jobs_table.get_item(Key={"query_id": query_id})
            updated_query = response["Item"]
            
            # Create assistant message with grounding
            message_result = create_query_completion_message(updated_query)
            
            return {
                "success": True,
                "query_id": query_id,
                "status": status,
                "message_created": message_result.get("success", False),
                "message_id": message_result.get("message_id"),
            }
        
        return {
            "success": True,
            "query_id": query_id,
            "status": status,
            "message_created": False,
        }
        
    except Exception as e:
        print(f"ERROR updating query and creating message: {str(e)}")
        print(traceback.format_exc())
        return {"error": str(e)}


def extract_tenant_id(event):
    """Extract tenant_id from event - handles both snake_case and camelCase"""
    # Try authorizer context first (supports both formats)
    authorizer = event.get("requestContext", {}).get("authorizer", {})

    # Try camelCase (from Lambda authorizer context)
    tenant_id = authorizer.get("tenantId")
    if tenant_id:
        return tenant_id

    # Try snake_case
    tenant_id = authorizer.get("tenant_id")
    if tenant_id:
        return tenant_id

    # Try custom header
    headers = event.get("headers", {})
    tenant_id = headers.get("X-Tenant-ID") or headers.get("x-tenant-id")
    if tenant_id:
        return tenant_id

    # Default for demo
    return "default-tenant"


def extract_user_id(event):
    """Extract user_id from event - handles both snake_case and camelCase"""
    # Try authorizer context (supports both formats)
    authorizer = event.get("requestContext", {}).get("authorizer", {})

    # Try camelCase
    user_id = authorizer.get("userId")
    if user_id:
        return user_id

    # Try snake_case
    user_id = authorizer.get("user_id")
    if user_id:
        return user_id

    # Try sub claim
    user_id = authorizer.get("sub")
    if user_id:
        return user_id

    # Default
    return "demo-user"


def success_response(data, status_code=200):
    """Return successful response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(data, default=str),
    }


def error_response(status_code, message):
    """Return error response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(
            {
                "error": message,
                "timestamp": datetime.utcnow().isoformat(),
                "error_code": f"ERR_{status_code}",
            }
        ),
    }


def cors_headers():
    """Return CORS headers"""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Tenant-ID",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }
