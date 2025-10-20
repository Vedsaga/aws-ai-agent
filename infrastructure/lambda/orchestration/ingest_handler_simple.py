"""
Simplified Ingest API Handler - DynamoDB Only
Handles report submission without complex agent orchestration
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
INCIDENTS_TABLE = os.environ.get(
    "INCIDENTS_TABLE", "MultiAgentOrchestration-dev-Data-Incidents"
)
ORCHESTRATOR_FUNCTION = os.environ.get(
    "ORCHESTRATOR_FUNCTION", "MultiAgentOrchestration-dev-Orchestrator"
)

# Initialize DynamoDB table (create if doesn't exist)
try:
    incidents_table = dynamodb.Table(INCIDENTS_TABLE)
    # Test if table exists
    incidents_table.table_status
except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    print(f"Creating incidents table: {INCIDENTS_TABLE}")
    try:
        incidents_table = dynamodb.create_table(
            TableName=INCIDENTS_TABLE,
            KeySchema=[{"AttributeName": "incident_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "incident_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Created incidents table: {INCIDENTS_TABLE}")
    except Exception as e:
        print(f"Error creating table: {e}")
        incidents_table = None
except Exception as e:
    print(f"Warning: Could not initialize incidents table: {e}")
    incidents_table = None


def handler(event, context):
    """
    Main Lambda handler for ingest API
    Simplified version that stores to DynamoDB only
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
        text = body.get("text")

        if not domain_id:
            return error_response(400, "Missing required field: domain_id")

        if not text:
            return error_response(400, "Missing required field: text")

        # Validate text length
        if len(text) > 10000:
            return error_response(
                400, "Text exceeds maximum length of 10000 characters"
            )

        # Generate job and incident IDs
        job_id = f"job_{uuid.uuid4().hex}"
        incident_id = f"inc_{uuid.uuid4().hex[:8]}"

        # Get optional fields
        images = body.get("images", [])
        source = body.get("source", "web")
        priority = body.get("priority", "normal")
        reporter_contact = body.get("reporter_contact")

        print(
            f"Processing ingest: job_id={job_id}, domain={domain_id}, text_length={len(text)}"
        )

        # Create incident record
        incident = {
            "incident_id": incident_id,
            "job_id": job_id,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "raw_text": text,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "source": source,
            "priority": priority,
        }

        # Add optional fields
        if images:
            incident["images"] = images[:5]  # Limit to 5 images

        if reporter_contact:
            incident["reporter_contact"] = reporter_contact

        # Add placeholder structured data (will be populated by agents)
        incident["structured_data"] = {
            "processing_status": "pending",
            "agents_executed": [],
        }

        # Store to DynamoDB
        if incidents_table:
            try:
                incidents_table.put_item(Item=incident)
                print(f"Stored incident: {incident_id}")
            except Exception as e:
                print(f"Error storing to DynamoDB: {e}")
                return error_response(500, f"Failed to store incident: {str(e)}")
        else:
            # If table doesn't exist, still return success but log warning
            print("WARNING: Incidents table not available, incident not stored")

        # Trigger orchestrator Lambda asynchronously
        try:
            orchestrator_payload = {
                "job_id": job_id,
                "incident_id": incident_id,
                "domain_id": domain_id,
                "text": text,
                "tenant_id": tenant_id,
            }

            lambda_client.invoke(
                FunctionName=ORCHESTRATOR_FUNCTION,
                InvocationType="Event",  # Async invocation
                Payload=json.dumps(orchestrator_payload),
            )
            print(f"Triggered orchestrator Lambda async for job {job_id}")
        except Exception as e:
            print(f"Warning: Could not trigger orchestrator: {e}")
            # Don't fail the request, orchestrator can be triggered later

        # Return success response
        return success_response(
            {
                "job_id": job_id,
                "status": "accepted",
                "message": "Report submitted for processing",
                "timestamp": datetime.utcnow().isoformat(),
                "estimated_completion_seconds": 30,
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
