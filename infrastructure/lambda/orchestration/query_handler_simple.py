"""
Simplified Query API Handler - DynamoDB Only
Handles natural language queries without complex agent orchestration
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables with fallbacks
QUERIES_TABLE = os.environ.get(
    "QUERIES_TABLE", "MultiAgentOrchestration-dev-Data-Queries"
)
ORCHESTRATOR_FUNCTION = os.environ.get(
    "ORCHESTRATOR_FUNCTION", "MultiAgentOrchestration-dev-Orchestrator"
)

# Initialize DynamoDB table (create if doesn't exist)
try:
    queries_table = dynamodb.Table(QUERIES_TABLE)
    # Test if table exists
    queries_table.table_status
except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    print(f"Creating queries table: {QUERIES_TABLE}")
    try:
        queries_table = dynamodb.create_table(
            TableName=QUERIES_TABLE,
            KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "job_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created queries table: {QUERIES_TABLE}")
    except Exception as e:
        print(f"Error creating table: {e}")
        queries_table = None
except Exception as e:
    print(f"Warning: Could not initialize queries table: {e}")
    queries_table = None


def handler(event, context):
    """
    Main Lambda handler for query API
    Simplified version that stores to DynamoDB and returns mock results
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

        # Only handle POST requests
        if http_method != "POST":
            return error_response(405, "Method not allowed")

        # Validate required fields
        domain_id = body.get("domain_id")
        question = body.get("question")

        if not domain_id:
            return error_response(400, "Missing required field: domain_id")

        if not question:
            return error_response(400, "Missing required field: question")

        # Validate question length
        if len(question) > 1000:
            return error_response(
                400, "Question exceeds maximum length of 1000 characters"
            )

        # Get optional fields
        filters = body.get("filters", {})
        include_visualizations = body.get("include_visualizations", False)

        # Generate job ID
        job_id = f"query_{uuid.uuid4().hex}"

        print(
            f"Processing query: job_id={job_id}, domain={domain_id}, question_length={len(question)}"
        )

        # Create query record
        query_record = {
            "job_id": job_id,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "question": question,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
        }

        # Add optional fields
        if filters:
            query_record["filters"] = filters

        if include_visualizations:
            query_record["include_visualizations"] = include_visualizations

        # Add placeholder results (will be populated by agents)
        query_record["agent_results"] = {}
        query_record["summary"] = "Processing your question..."

        # Store to DynamoDB
        if queries_table:
            try:
                queries_table.put_item(Item=query_record)
                print(f"Stored query: {job_id}")
            except Exception as e:
                print(f"Error storing to DynamoDB: {e}")
                return error_response(500, f"Failed to store query: {str(e)}")
        else:
            # If table doesn't exist, still return success but log warning
            print("WARNING: Queries table not available, query not stored")

        # Trigger orchestrator Lambda asynchronously
        try:
            orchestrator_payload = {
                "job_id": job_id,
                "job_type": "query",
                "domain_id": domain_id,
                "question": question,
                "tenant_id": tenant_id,
                "filters": filters or {},
            }

            lambda_client.invoke(
                FunctionName=ORCHESTRATOR_FUNCTION,
                InvocationType="Event",  # Async invocation
                Payload=json.dumps(orchestrator_payload),
            )
            print(f"Triggered orchestrator Lambda async for query {job_id}")
        except Exception as e:
            print(f"Warning: Could not trigger orchestrator: {e}")
            # Don't fail the request, orchestrator can be triggered later

        # Return success response with job_id
        return success_response(
            {
                "job_id": job_id,
                "status": "accepted",
                "message": "Question submitted for processing",
                "timestamp": datetime.utcnow().isoformat(),
                "estimated_completion_seconds": 10,
            },
            status_code=202,
        )

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


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
