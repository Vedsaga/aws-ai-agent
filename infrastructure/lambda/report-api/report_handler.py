"""
Report Handler - CRUD operations for Reports
Handles report submission, retrieval, updates, and deletion
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
REPORTS_TABLE = os.environ.get("REPORTS_TABLE", "MultiAgentOrchestration-dev-Reports")
ORCHESTRATOR_FUNCTION = os.environ.get("ORCHESTRATOR_FUNCTION", "")

# Initialize DynamoDB table
try:
    reports_table = dynamodb.Table(REPORTS_TABLE)
    reports_table.table_status
    print(f"Initialized Reports table: {REPORTS_TABLE}")
except Exception as e:
    print(f"Warning: Could not initialize Reports table: {e}")
    reports_table = None


def handler(event, context):
    """
    Main Lambda handler for Report API
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
        if http_method == "POST" and "/reports" in path:
            return create_report(event, tenant_id, user_id)
        
        elif http_method == "GET" and path_parameters.get("incident_id"):
            incident_id = path_parameters["incident_id"]
            return get_report(incident_id, tenant_id)
        
        elif http_method == "GET" and "/reports" in path:
            return list_reports(event, tenant_id)
        
        elif http_method == "PUT" and path_parameters.get("incident_id"):
            incident_id = path_parameters["incident_id"]
            return update_report(event, incident_id, tenant_id, user_id)
        
        elif http_method == "DELETE" and path_parameters.get("incident_id"):
            incident_id = path_parameters["incident_id"]
            return delete_report(incident_id, tenant_id)
        
        else:
            return error_response(404, "Endpoint not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def create_report(event: dict, tenant_id: str, user_id: str) -> dict:
    """
    Create a new report and trigger ingestion playbook
    POST /api/v1/reports
    """
    # Parse request body
    body = parse_body(event)
    if isinstance(body, dict) and "error" in body:
        return error_response(400, body["error"])

    # Validate required fields
    domain_id = body.get("domain_id")
    text = body.get("text")

    if not domain_id:
        return error_response(400, "Missing required field: domain_id")
    
    if not text:
        return error_response(400, "Missing required field: text")

    # Validate text length
    if len(text) > 10000:
        return error_response(400, "Text exceeds maximum length of 10000 characters")

    # Generate IDs
    job_id = f"job_{uuid.uuid4().hex}"
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"
    report_id = str(uuid.uuid4())

    # Get optional fields
    images = body.get("images", [])
    source = body.get("source", "web")

    print(f"Creating report: incident_id={incident_id}, domain={domain_id}")

    # Create report document
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

    # Store to DynamoDB
    if not reports_table:
        return error_response(500, "Reports table not available")

    try:
        reports_table.put_item(Item=report)
        print(f"Stored report: {incident_id}")
    except Exception as e:
        print(f"Error storing to DynamoDB: {e}")
        return error_response(500, f"Failed to store report: {str(e)}")

    # Trigger orchestrator Lambda asynchronously with ingestion playbook
    if ORCHESTRATOR_FUNCTION:
        try:
            orchestrator_payload = {
                "job_id": job_id,
                "job_type": "ingest",
                "incident_id": incident_id,
                "domain_id": domain_id,
                "text": text,
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
            "incident_id": incident_id,
            "status": "accepted",
            "message": "Report submitted for processing",
            "timestamp": timestamp,
        },
        status_code=202,
    )


def get_report(incident_id: str, tenant_id: str) -> dict:
    """
    Get a report by incident_id
    GET /api/v1/reports/{incident_id}
    """
    if not reports_table:
        return error_response(500, "Reports table not available")

    try:
        response = reports_table.get_item(Key={"incident_id": incident_id})
        
        if "Item" not in response:
            return error_response(404, f"Report not found: {incident_id}")
        
        report = response["Item"]
        
        # Verify tenant access
        if report.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this report")
        
        # Return full document structure with ingestion_data and management_data
        return success_response(report)

    except Exception as e:
        print(f"Error retrieving report: {e}")
        return error_response(500, f"Failed to retrieve report: {str(e)}")


def list_reports(event: dict, tenant_id: str) -> dict:
    """
    List reports with filtering and pagination
    GET /api/v1/reports?page=1&limit=20&domain_id=civic_complaints&status=completed
    """
    if not reports_table:
        return error_response(500, "Reports table not available")

    # Parse query parameters
    query_params = event.get("queryStringParameters") or {}
    page = int(query_params.get("page", 1))
    limit = int(query_params.get("limit", 20))
    domain_id = query_params.get("domain_id")
    status = query_params.get("status")

    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    try:
        # Build query based on filters
        if domain_id:
            # Use GSI: domain-created-index
            query_kwargs = {
                "IndexName": "domain-created-index",
                "KeyConditionExpression": "domain_id = :domain_id",
                "ExpressionAttributeValues": {":domain_id": domain_id},
                "ScanIndexForward": False,  # Sort by created_at descending
            }
            
            # Add status filter if provided
            if status:
                query_kwargs["FilterExpression"] = "#status = :status"
                query_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
                query_kwargs["ExpressionAttributeValues"][":status"] = status
            
            response = reports_table.query(**query_kwargs)
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
            
            response = reports_table.scan(**scan_kwargs)

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
        reports = [
            {
                "incident_id": item["incident_id"],
                "domain_id": item["domain_id"],
                "raw_text": item.get("raw_text", "")[:200],  # Truncate for list view
                "status": item.get("status", "unknown"),
                "created_at": item.get("created_at", ""),
            }
            for item in paginated_items
        ]
        
        return success_response({
            "reports": reports,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
            },
        })

    except Exception as e:
        print(f"Error listing reports: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to list reports: {str(e)}")


def update_report(event: dict, incident_id: str, tenant_id: str, user_id: str) -> dict:
    """
    Update a report (merge management_data)
    PUT /api/v1/reports/{incident_id}
    """
    if not reports_table:
        return error_response(500, "Reports table not available")

    # Parse request body
    body = parse_body(event)
    if isinstance(body, dict) and "error" in body:
        return error_response(400, body["error"])

    # Get the existing report first
    try:
        response = reports_table.get_item(Key={"incident_id": incident_id})
        
        if "Item" not in response:
            return error_response(404, f"Report not found: {incident_id}")
        
        report = response["Item"]
        
        # Verify tenant access
        if report.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this report")

    except Exception as e:
        print(f"Error retrieving report: {e}")
        return error_response(500, f"Failed to retrieve report: {str(e)}")

    # Build update expression
    update_parts = []
    expression_values = {}
    expression_names = {}

    # Update status if provided
    if "status" in body:
        update_parts.append("#status = :status")
        expression_names["#status"] = "status"
        expression_values[":status"] = body["status"]

    # Merge management_data if provided
    if "management_data" in body:
        new_management_data = body["management_data"]
        existing_management_data = report.get("management_data", {})
        
        # Deep merge management_data
        merged_management_data = deep_merge(existing_management_data, new_management_data)
        
        update_parts.append("management_data = :management_data")
        expression_values[":management_data"] = merged_management_data

    # Always update updated_at
    update_parts.append("updated_at = :updated_at")
    expression_values[":updated_at"] = datetime.utcnow().isoformat()

    if not update_parts:
        return error_response(400, "No valid fields to update")

    # Perform update
    try:
        update_expression = "SET " + ", ".join(update_parts)
        
        update_kwargs = {
            "Key": {"incident_id": incident_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW",
        }
        
        if expression_names:
            update_kwargs["ExpressionAttributeNames"] = expression_names
        
        response = reports_table.update_item(**update_kwargs)
        
        updated_report = response["Attributes"]
        
        return success_response(updated_report)

    except Exception as e:
        print(f"Error updating report: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to update report: {str(e)}")


def delete_report(incident_id: str, tenant_id: str) -> dict:
    """
    Delete a report
    DELETE /api/v1/reports/{incident_id}
    """
    if not reports_table:
        return error_response(500, "Reports table not available")

    # Get the report first to verify tenant access
    try:
        response = reports_table.get_item(Key={"incident_id": incident_id})
        
        if "Item" not in response:
            return error_response(404, f"Report not found: {incident_id}")
        
        report = response["Item"]
        
        # Verify tenant access
        if report.get("tenant_id") != tenant_id:
            return error_response(403, "Access denied to this report")

    except Exception as e:
        print(f"Error retrieving report: {e}")
        return error_response(500, f"Failed to retrieve report: {str(e)}")

    # Delete the report
    try:
        reports_table.delete_item(Key={"incident_id": incident_id})
        
        return success_response({
            "message": "Report deleted successfully",
            "incident_id": incident_id,
        })

    except Exception as e:
        print(f"Error deleting report: {e}")
        return error_response(500, f"Failed to delete report: {str(e)}")


def deep_merge(base: dict, update: dict) -> dict:
    """
    Deep merge two dictionaries
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


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
