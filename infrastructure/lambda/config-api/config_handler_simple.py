"""
Simplified Configuration API Handler - DynamoDB Only
Handles basic CRUD operations for agent and domain configurations
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import traceback

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables with fallbacks
CONFIGURATIONS_TABLE = os.environ.get(
    "CONFIGURATIONS_TABLE", "MultiAgentOrchestration-dev-Data-Configurations"
)

# Initialize DynamoDB table
try:
    config_table = dynamodb.Table(CONFIGURATIONS_TABLE)
except Exception as e:
    print(f"Warning: Could not initialize DynamoDB table: {e}")
    config_table = None


def handler(event, context):
    """
    Main Lambda handler - simplified for quick deployment
    """
    print(f"Event: {json.dumps(event)}")

    try:
        # Extract request details
        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        query_params = event.get("queryStringParameters") or {}
        path_params = event.get("pathParameters") or {}

        # Parse body
        body = {}
        if event.get("body"):
            try:
                body = json.loads(event.get("body"))
            except:
                return error_response(400, "Invalid JSON in request body")

        # Extract tenant_id (use default for demo)
        tenant_id = extract_tenant_id(event)
        user_id = extract_user_id(event)

        print(f"Method: {http_method}, Path: {path}, Tenant: {tenant_id}")

        # Route requests
        if http_method == "GET" and query_params.get("type"):
            # List configurations by type
            return list_configurations(tenant_id, query_params.get("type"), user_id)

        elif http_method == "GET" and path_params:
            # Get specific configuration
            config_type = path_params.get("type")
            config_id = path_params.get("id")
            return get_configuration(tenant_id, config_type, config_id)

        elif http_method == "POST":
            # Create new configuration
            return create_configuration(tenant_id, user_id, body)

        elif http_method == "PUT" and path_params:
            # Update configuration
            config_type = path_params.get("type")
            config_id = path_params.get("id")
            return update_configuration(
                tenant_id, user_id, config_type, config_id, body
            )

        elif http_method == "DELETE" and path_params:
            # Delete configuration
            config_type = path_params.get("type")
            config_id = path_params.get("id")
            return delete_configuration(tenant_id, config_type, config_id)

        else:
            return error_response(400, "Invalid request format")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def list_configurations(tenant_id, config_type, user_id=None):
    """List all configurations of a given type"""
    try:
        print(f"Listing configs: type={config_type}, tenant={tenant_id}")

        if not config_table:
            return error_response(500, "Database not available")

        # Scan table with filter (use boto3 condition expressions)
        from boto3.dynamodb.conditions import Attr

        filter_expr = Attr("config_type").eq(config_type)
        if tenant_id != "default-tenant":
            filter_expr = filter_expr & Attr("tenant_id").eq(tenant_id)

        response = config_table.scan(
            FilterExpression=filter_expr,
        )

        items = response.get("Items", [])

        # Add metadata flags
        for item in items:
            item["created_by_me"] = item.get("created_by") == user_id

        print(f"Found {len(items)} configurations")

        return success_response({"configs": items, "count": len(items)})

    except Exception as e:
        print(f"Error listing configs: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to list configurations: {str(e)}")


def get_configuration(tenant_id, config_type, config_id):
    """Get a specific configuration"""
    try:
        print(f"Getting config: type={config_type}, id={config_id}, tenant={tenant_id}")

        if not config_table:
            return error_response(500, "Database not available")

        # Query by primary key
        response = config_table.get_item(
            Key={"tenant_id": tenant_id, "config_key": config_id}
        )

        item = response.get("Item")

        if not item:
            return error_response(404, f"{config_type} not found: {config_id}")

        return success_response(item)

    except Exception as e:
        print(f"Error getting config: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to get configuration: {str(e)}")


def create_configuration(tenant_id, user_id, body):
    """Create a new configuration"""
    try:
        config_type = body.get("type")
        config_data = body.get("config", {})

        if not config_type:
            return error_response(400, "Missing required field: type")

        if not config_data:
            return error_response(400, "Missing required field: config")

        print(f"Creating config: type={config_type}, tenant={tenant_id}")

        if not config_table:
            return error_response(500, "Database not available")

        # Generate config ID based on type
        if config_type == "agent":
            agent_name = config_data.get("agent_name", "unnamed")
            config_id = (
                f"agent_{agent_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
            )
        elif config_type == "domain_template":
            domain_id = config_data.get("domain_id", "custom")
            config_id = f"domain_{domain_id}_{uuid.uuid4().hex[:8]}"
        elif config_type == "playbook":
            config_id = f"playbook_{uuid.uuid4().hex[:8]}"
        elif config_type == "dependency_graph":
            config_id = f"depgraph_{uuid.uuid4().hex[:8]}"
        else:
            config_id = f"{config_type}_{uuid.uuid4().hex[:8]}"

        # Build item
        item = {
            "tenant_id": tenant_id,
            "config_key": config_id,
            "config_type": config_type,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": user_id or "system",
            "is_builtin": False,
            "version": 1,
            **config_data,
        }

        # Add type-specific ID field
        if config_type == "agent":
            item["agent_id"] = config_id
        elif config_type == "domain_template":
            item["template_id"] = config_id
        elif config_type == "playbook":
            item["playbook_id"] = config_id
        elif config_type == "dependency_graph":
            item["graph_id"] = config_id

        # Save to DynamoDB
        config_table.put_item(Item=item)

        print(f"Created config: {config_id}")

        return success_response(item, status_code=201)

    except Exception as e:
        print(f"Error creating config: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to create configuration: {str(e)}")


def update_configuration(tenant_id, user_id, config_type, config_id, body):
    """Update an existing configuration"""
    try:
        config_data = body.get("config", {})

        if not config_data:
            return error_response(400, "Missing required field: config")

        print(
            f"Updating config: type={config_type}, id={config_id}, tenant={tenant_id}"
        )

        if not config_table:
            return error_response(500, "Database not available")

        # Check if exists
        response = config_table.get_item(
            Key={"tenant_id": tenant_id, "config_key": config_id}
        )

        existing_item = response.get("Item")
        if not existing_item:
            return error_response(404, f"{config_type} not found: {config_id}")

        # Update item
        updated_item = {
            **existing_item,
            **config_data,
            "updated_at": datetime.utcnow().isoformat(),
            "version": existing_item.get("version", 1) + 1,
        }

        # Save updated item
        config_table.put_item(Item=updated_item)

        print(f"Updated config: {config_id}")

        return success_response(updated_item)

    except Exception as e:
        print(f"Error updating config: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to update configuration: {str(e)}")


def delete_configuration(tenant_id, config_type, config_id):
    """Delete a configuration"""
    try:
        print(
            f"Deleting config: type={config_type}, id={config_id}, tenant={tenant_id}"
        )

        if not config_table:
            return error_response(500, "Database not available")

        # Check if exists
        response = config_table.get_item(
            Key={"tenant_id": tenant_id, "config_key": config_id}
        )

        existing_item = response.get("Item")
        if not existing_item:
            return error_response(404, f"{config_type} not found: {config_id}")

        # Don't allow deleting built-in configs
        if existing_item.get("is_builtin", False):
            return error_response(403, "Cannot delete built-in configurations")

        # Delete item
        config_table.delete_item(Key={"tenant_id": tenant_id, "config_key": config_id})

        print(f"Deleted config: {config_id}")

        return success_response({"message": f"{config_type} deleted successfully"})

    except Exception as e:
        print(f"Error deleting config: {e}")
        print(traceback.format_exc())
        return error_response(500, f"Failed to delete configuration: {str(e)}")


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
