"""
Simplified Ingest API Handler - Reports Table
Handles report submission using new Reports table structure
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Environment variables with fallbacks
REPORTS_TABLE = os.environ.get(
    "REPORTS_TABLE", "MultiAgentOrchestration-dev-Reports"
)
ORCHESTRATOR_FUNCTION = os.environ.get(
    "ORCHESTRATOR_FUNCTION", "MultiAgentOrchestration-dev-Orchestrator"
)

# RDS connection parameters
DB_HOST = os.environ.get("DB_HOST", "")
DB_NAME = os.environ.get("DB_NAME", "orchestration_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))

# Initialize DynamoDB table
try:
    reports_table = dynamodb.Table(REPORTS_TABLE)
    # Test if table exists
    reports_table.table_status
    print(f"Initialized Reports table: {REPORTS_TABLE}")
except Exception as e:
    print(f"Warning: Could not initialize Reports table: {e}")
    reports_table = None


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
        report_id = str(uuid.uuid4())

        # Get optional fields
        images = body.get("images", [])
        source = body.get("source", "web")

        print(
            f"Processing ingest: job_id={job_id}, incident_id={incident_id}, domain={domain_id}, text_length={len(text)}"
        )

        # Load domain configuration to get ingestion_playbook
        ingestion_playbook = load_ingestion_playbook(domain_id, tenant_id)
        if not ingestion_playbook:
            return error_response(404, f"Domain not found or has no ingestion playbook: {domain_id}")

        # Create report document with standard metadata
        timestamp = datetime.utcnow().isoformat()
        report = {
            "incident_id": incident_id,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "raw_text": text,
            "status": "processing",
            "ingestion_data": {},  # Will be populated by ingestion agents
            "management_data": {},  # Will be populated by management agents
            "id": report_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "created_by": user_id,
            "source": source,
        }

        # Add optional fields
        if images:
            report["images"] = images[:5]  # Limit to 5 images

        # Store to DynamoDB Reports table
        if not reports_table:
            return error_response(500, "Reports table not available")

        try:
            reports_table.put_item(Item=report)
            print(f"Stored report: {incident_id}")
        except Exception as e:
            print(f"Error storing to DynamoDB: {e}")
            return error_response(500, f"Failed to store report: {str(e)}")

        # Trigger orchestrator Lambda asynchronously with ingestion_playbook
        try:
            orchestrator_payload = {
                "job_id": job_id,
                "job_type": "ingest",
                "incident_id": incident_id,
                "domain_id": domain_id,
                "text": text,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "playbook": ingestion_playbook,  # Pass ingestion_playbook
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
                "incident_id": incident_id,
                "status": "accepted",
                "message": "Report submitted for processing",
                "timestamp": timestamp,
            },
            status_code=202,
        )

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def load_ingestion_playbook(domain_id: str, tenant_id: str):
    """
    Load ingestion_playbook from RDS domain_configurations table
    Returns the playbook dict or None if not found
    """
    if not DB_HOST or not DB_PASSWORD:
        print("Warning: RDS credentials not configured, using fallback")
        return get_fallback_playbook()

    conn = None
    try:
        # Connect to RDS
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=5,
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query domain configuration
        cursor.execute(
            """
            SELECT ingestion_playbook
            FROM domain_configurations
            WHERE domain_id = %s AND tenant_id = %s
            """,
            (domain_id, tenant_id),
        )

        result = cursor.fetchone()

        if result:
            print(f"Loaded ingestion_playbook for domain: {domain_id}")
            return result["ingestion_playbook"]
        else:
            print(f"Domain not found: {domain_id}, using fallback")
            return get_fallback_playbook()

    except Exception as e:
        print(f"Error loading ingestion_playbook from RDS: {e}")
        print(traceback.format_exc())
        return get_fallback_playbook()

    finally:
        if conn:
            conn.close()


def get_fallback_playbook():
    """
    Return a fallback ingestion playbook with basic agents
    """
    return {
        "agent_execution_graph": {
            "nodes": ["geo_agent", "temporal_agent", "category_agent"],
            "edges": [],
        }
    }


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
