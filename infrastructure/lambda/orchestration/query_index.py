"""
Query Handler with Orchestrator Integration
Accepts queries and triggers agent orchestration for data retrieval
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback
import sys

# Add realtime module to path (in Lambda, realtime/ is at same level)
realtime_path = os.path.join(os.path.dirname(__file__), "realtime")
if os.path.exists(realtime_path):
    sys.path.insert(0, os.path.dirname(__file__))

try:
    from realtime.status_utils import publish_orchestrator_status
    print("Status utils loaded successfully")
except ImportError as e:
    print(f"Warning: status_utils not available: {e}")

    def publish_orchestrator_status(*args, **kwargs):
        return False


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")
sqs = boto3.client("sqs")

# Environment variables
DATA_QUERIES_TABLE = os.environ.get(
    "DATA_QUERIES_TABLE", "MultiAgentOrchestration-dev-DataQueries"
)
ORCHESTRATOR_FUNCTION = os.environ.get(
    "ORCHESTRATOR_FUNCTION", "MultiAgentOrchestration-dev-Orchestrator"
)
ORCHESTRATOR_QUEUE = os.environ.get("ORCHESTRATOR_QUEUE", "")

# Initialize DynamoDB table
try:
    queries_table = dynamodb.Table(DATA_QUERIES_TABLE)
    queries_table.table_status
except Exception as e:
    print(f"Warning: Could not initialize queries table: {e}")
    queries_table = None


def handler(event, context):
    """
    Main Lambda handler for query API
    Accepts question and triggers orchestrator
    """
    print(f"Event: {json.dumps(event, default=str)}")

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
        if len(question) > 5000:
            return error_response(
                400, "Question exceeds maximum length of 5000 characters"
            )

        # Generate job and query IDs
        job_id = f"query_{uuid.uuid4().hex}"
        query_id = f"qry_{uuid.uuid4().hex[:8]}"

        # Get optional fields
        filters = body.get("filters", {})
        time_range = body.get("time_range")
        spatial_bounds = body.get("spatial_bounds")

        print(
            f"Processing query: job_id={job_id}, domain={domain_id}, question_length={len(question)}"
        )

        # Create query record
        query_record = {
            "query_id": query_id,
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

        if time_range:
            query_record["time_range"] = time_range

        if spatial_bounds:
            query_record["spatial_bounds"] = spatial_bounds

        # Add placeholder for results
        query_record["results"] = {
            "processing_status": "pending",
            "agents_executed": [],
        }

        # Store to DynamoDB
        if queries_table:
            try:
                queries_table.put_item(Item=query_record)
                print(f"Stored query: {query_id}")
            except Exception as e:
                print(f"Error storing to DynamoDB: {e}")

        # Publish initial status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="accepted",
            message="Query received and queued for processing",
        )

        # Trigger orchestrator
        orchestration_payload = {
            "job_id": job_id,
            "job_type": "query",
            "domain_id": domain_id,
            "question": question,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "query_id": query_id,
            "filters": filters,
            "time_range": time_range,
            "spatial_bounds": spatial_bounds,
        }

        trigger_orchestrator(orchestration_payload)

        # Publish orchestration started status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="processing",
            message="Query agent orchestration started",
        )

        # Return success response
        return success_response(
            {
                "job_id": job_id,
                "query_id": query_id,
                "status": "accepted",
                "message": "Query submitted for processing",
                "timestamp": datetime.utcnow().isoformat(),
                "estimated_completion_seconds": 30,
            },
            status_code=202,
        )

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def trigger_orchestrator(payload: dict):
    """
    Trigger orchestrator to process the query job
    Try multiple methods: SQS, Lambda async, or direct invoke
    """

    # Method 1: Try SQS queue (best for async processing)
    if ORCHESTRATOR_QUEUE:
        try:
            sqs.send_message(
                QueueUrl=ORCHESTRATOR_QUEUE,
                MessageBody=json.dumps(payload),
            )
            print(f"Sent query job {payload['job_id']} to SQS queue")
            return
        except Exception as e:
            print(f"SQS send failed: {e}, trying Lambda invoke...")

    # Method 2: Try async Lambda invocation
    try:
        lambda_client.invoke(
            FunctionName=ORCHESTRATOR_FUNCTION,
            InvocationType="Event",  # Async
            Payload=json.dumps(payload),
        )
        print(f"Triggered orchestrator Lambda async for query job {payload['job_id']}")
        return
    except Exception as e:
        print(f"Lambda async invoke failed: {e}, trying sync invoke...")

    # Method 3: Fallback to sync invoke (not ideal but works)
    try:
        response = lambda_client.invoke(
            FunctionName=ORCHESTRATOR_FUNCTION,
            InvocationType="RequestResponse",  # Sync
            Payload=json.dumps(payload),
        )
        print(f"Triggered orchestrator Lambda sync for query job {payload['job_id']}")
        result = json.loads(response["Payload"].read())
        print(f"Orchestrator response: {result}")
    except Exception as e:
        print(f"Failed to trigger orchestrator: {e}")
        print("Query job will remain in 'processing' status")


def extract_tenant_id(event):
    """Extract tenant_id from event"""
    authorizer = event.get("requestContext", {}).get("authorizer", {})

    tenant_id = authorizer.get("tenantId") or authorizer.get("tenant_id")
    if tenant_id:
        return tenant_id

    headers = event.get("headers", {})
    tenant_id = headers.get("X-Tenant-ID") or headers.get("x-tenant-id")
    if tenant_id:
        return tenant_id

    return "default-tenant"


def extract_user_id(event):
    """Extract user_id from event"""
    authorizer = event.get("requestContext", {}).get("authorizer", {})

    user_id = (
        authorizer.get("userId") or authorizer.get("user_id") or authorizer.get("sub")
    )
    if user_id:
        return user_id

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
