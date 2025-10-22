"""
Domain Handler Lambda
Handles CRUD operations for domain management with playbook validation.
Manages domain configurations with three playbooks: ingestion, query, management
"""

import json
import os
import boto3
import psycopg
from psycopg.rows import dict_row
import logging
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional, Tuple

# Import playbook validator
from playbook_validator import validate_domain_playbooks, validate_playbook

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'domainflow')

secrets_client = boto3.client('secretsmanager')

# Database connection pool (reuse across invocations)
_db_connection = None


def get_db_connection():
    """
    Get or create database connection with connection pooling.
    """
    global _db_connection
    
    if _db_connection is None or _db_connection.closed:
        # Get database credentials from Secrets Manager
        secret_response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
        secret = json.loads(secret_response['SecretString'])
        
        db_username = secret['username']
        db_password = secret['password']
        
        # Connect to database using psycopg3
        _db_connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=db_username,
            password=db_password,
            row_factory=dict_row,
            autocommit=False
        )
        logger.info("Database connection established")
    
    return _db_connection


def handler(event, context):
    """
    Main Lambda handler for domain management API.
    Routes requests to appropriate CRUD operations.
    """
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
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
            except json.JSONDecodeError:
                return error_response(400, "Invalid JSON in request body")
        
        # Extract tenant_id and user_id from authorizer context
        tenant_id = extract_tenant_id(event)
        user_id = extract_user_id(event)
        
        logger.info(f"Method: {http_method}, Path: {path}, Tenant: {tenant_id}, User: {user_id}")
        
        # Route requests
        if http_method == "POST" and "/domains" in path and not path_params:
            # Create domain
            return create_domain(tenant_id, user_id, body)
        
        elif http_method == "GET" and "/domains" in path and not path_params:
            # List domains
            return list_domains(tenant_id, user_id, query_params)
        
        elif http_method == "GET" and path_params.get("domain_id"):
            # Get specific domain
            domain_id = path_params.get("domain_id")
            return get_domain(tenant_id, user_id, domain_id)
        
        elif http_method == "PUT" and path_params.get("domain_id"):
            # Update domain
            domain_id = path_params.get("domain_id")
            return update_domain(tenant_id, user_id, domain_id, body)
        
        elif http_method == "DELETE" and path_params.get("domain_id"):
            # Delete domain
            domain_id = path_params.get("domain_id")
            return delete_domain(tenant_id, user_id, domain_id)
        
        else:
            return error_response(404, "Endpoint not found")
    
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return error_response(500, f"Internal server error: {str(e)}")


def create_domain(tenant_id: str, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new domain with playbook validation.
    
    Request body:
    {
        "domain_id": "string",
        "domain_name": "string",
        "description": "string",
        "ingestion_playbook": {
            "agent_execution_graph": {
                "nodes": ["agent_id"],
                "edges": [{"from": "agent_id", "to": "agent_id"}]
            }
        },
        "query_playbook": {...},
        "management_playbook": {...}
    }
    """
    logger.info(f"Creating domain for tenant {tenant_id}")
    
    try:
        # Validate required fields
        required_fields = ["domain_id", "domain_name", "ingestion_playbook", "query_playbook", "management_playbook"]
        for field in required_fields:
            if field not in body:
                return error_response(400, f"Missing required field: {field}")
        
        domain_id = body.get("domain_id")
        domain_name = body.get("domain_name")
        description = body.get("description", "")
        ingestion_playbook = body.get("ingestion_playbook")
        query_playbook = body.get("query_playbook")
        management_playbook = body.get("management_playbook")
        
        # Get all agents for validation
        conn = get_db_connection()
        cursor = conn.cursor()
        all_agents = get_all_agents_dict(cursor, tenant_id)
        
        # Validate all three playbooks
        is_valid, error_msg = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            all_agents
        )
        
        if not is_valid:
            return error_response(400, f"Playbook validation failed: {error_msg}")
        
        # Insert domain into database
        insert_query = """
            INSERT INTO domain_configurations (
                domain_id, tenant_id, domain_name, description,
                ingestion_playbook, query_playbook, management_playbook,
                created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, domain_id, domain_name, created_at, updated_at, created_by;
        """
        
        cursor.execute(insert_query, (
            domain_id,
            tenant_id,
            domain_name,
            description,
            json.dumps(ingestion_playbook),
            json.dumps(query_playbook),
            json.dumps(management_playbook),
            user_id
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Domain created successfully: {domain_id}")
        
        # Format response
        response_data = {
            "domain_id": result["domain_id"],
            "domain_name": result["domain_name"],
            "id": str(result["id"]),
            "created_at": result["created_at"].isoformat(),
            "updated_at": result["updated_at"].isoformat(),
            "created_by": str(result["created_by"])
        }
        
        return success_response(201, response_data)
    
    except psycopg.errors.UniqueViolation as e:
        logger.error(f"Database integrity error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return error_response(409, f"Domain with ID '{domain_id}' already exists")
    
    except Exception as e:
        logger.error(f"Error creating domain: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to create domain: {str(e)}")


def list_domains(tenant_id: str, user_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    List domains with pagination.
    
    Query parameters:
    - page: int (default: 1)
    - limit: int (default: 20, max: 100)
    """
    logger.info(f"Listing domains for tenant {tenant_id}")
    
    try:
        # Parse pagination parameters
        page = int(query_params.get("page", 1))
        limit = min(int(query_params.get("limit", 20)), 100)
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM domain_configurations
            WHERE tenant_id = %s;
        """
        cursor.execute(count_query, (tenant_id,))
        total = cursor.fetchone()["total"]
        
        # Get domains
        select_query = """
            SELECT domain_id, domain_name, description, id, created_at
            FROM domain_configurations
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
        """
        cursor.execute(select_query, (tenant_id, limit, offset))
        domains = cursor.fetchall()
        
        # Format response
        domains_list = []
        for domain in domains:
            domains_list.append({
                "domain_id": domain["domain_id"],
                "domain_name": domain["domain_name"],
                "description": domain["description"],
                "id": str(domain["id"]),
                "created_at": domain["created_at"].isoformat()
            })
        
        response_data = {
            "domains": domains_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error listing domains: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to list domains: {str(e)}")


def get_domain(tenant_id: str, user_id: str, domain_id: str) -> Dict[str, Any]:
    """
    Get a specific domain with full playbook details.
    """
    logger.info(f"Getting domain {domain_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get domain
        select_query = """
            SELECT id, domain_id, domain_name, description,
                   ingestion_playbook, query_playbook, management_playbook,
                   created_at, updated_at, created_by
            FROM domain_configurations
            WHERE tenant_id = %s AND domain_id = %s;
        """
        cursor.execute(select_query, (tenant_id, domain_id))
        domain = cursor.fetchone()
        
        if not domain:
            return error_response(404, f"Domain not found: {domain_id}")
        
        # Format response
        response_data = {
            "domain_id": domain["domain_id"],
            "domain_name": domain["domain_name"],
            "description": domain["description"],
            "ingestion_playbook": domain["ingestion_playbook"],
            "query_playbook": domain["query_playbook"],
            "management_playbook": domain["management_playbook"],
            "id": str(domain["id"]),
            "created_at": domain["created_at"].isoformat(),
            "updated_at": domain["updated_at"].isoformat(),
            "created_by": str(domain["created_by"])
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error getting domain: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to get domain: {str(e)}")


def update_domain(tenant_id: str, user_id: str, domain_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a domain with playbook validation.
    
    Request body (all fields optional):
    {
        "domain_name": "string",
        "description": "string",
        "ingestion_playbook": {...},
        "query_playbook": {...},
        "management_playbook": {...}
    }
    """
    logger.info(f"Updating domain {domain_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if domain exists
        check_query = """
            SELECT id, ingestion_playbook, query_playbook, management_playbook
            FROM domain_configurations
            WHERE tenant_id = %s AND domain_id = %s;
        """
        cursor.execute(check_query, (tenant_id, domain_id))
        existing = cursor.fetchone()
        
        if not existing:
            return error_response(404, f"Domain not found: {domain_id}")
        
        # Get current playbooks (for partial updates)
        current_ingestion = existing["ingestion_playbook"]
        current_query = existing["query_playbook"]
        current_management = existing["management_playbook"]
        
        # Use updated playbooks or keep current ones
        ingestion_playbook = body.get("ingestion_playbook", current_ingestion)
        query_playbook = body.get("query_playbook", current_query)
        management_playbook = body.get("management_playbook", current_management)
        
        # Get all agents for validation
        all_agents = get_all_agents_dict(cursor, tenant_id)
        
        # Validate all three playbooks
        is_valid, error_msg = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            all_agents
        )
        
        if not is_valid:
            return error_response(400, f"Playbook validation failed: {error_msg}")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if "domain_name" in body:
            update_fields.append("domain_name = %s")
            update_values.append(body["domain_name"])
        
        if "description" in body:
            update_fields.append("description = %s")
            update_values.append(body["description"])
        
        if "ingestion_playbook" in body:
            update_fields.append("ingestion_playbook = %s")
            update_values.append(json.dumps(ingestion_playbook))
        
        if "query_playbook" in body:
            update_fields.append("query_playbook = %s")
            update_values.append(json.dumps(query_playbook))
        
        if "management_playbook" in body:
            update_fields.append("management_playbook = %s")
            update_values.append(json.dumps(management_playbook))
        
        # Update timestamp
        update_fields.append("updated_at = NOW()")
        
        if len(update_fields) == 1:  # Only timestamp update
            return error_response(400, "No fields to update")
        
        # Execute update
        update_query = f"""
            UPDATE domain_configurations
            SET {', '.join(update_fields)}
            WHERE tenant_id = %s AND domain_id = %s
            RETURNING id, domain_id, domain_name, description,
                      ingestion_playbook, query_playbook, management_playbook,
                      created_at, updated_at, created_by;
        """
        
        update_values.extend([tenant_id, domain_id])
        cursor.execute(update_query, update_values)
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Domain updated successfully: {domain_id}")
        
        # Format response
        response_data = {
            "domain_id": result["domain_id"],
            "domain_name": result["domain_name"],
            "description": result["description"],
            "ingestion_playbook": result["ingestion_playbook"],
            "query_playbook": result["query_playbook"],
            "management_playbook": result["management_playbook"],
            "id": str(result["id"]),
            "created_at": result["created_at"].isoformat(),
            "updated_at": result["updated_at"].isoformat(),
            "created_by": str(result["created_by"])
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error updating domain: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to update domain: {str(e)}")


def delete_domain(tenant_id: str, user_id: str, domain_id: str) -> Dict[str, Any]:
    """
    Delete a domain.
    """
    logger.info(f"Deleting domain {domain_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if domain exists
        check_query = """
            SELECT id
            FROM domain_configurations
            WHERE tenant_id = %s AND domain_id = %s;
        """
        cursor.execute(check_query, (tenant_id, domain_id))
        existing = cursor.fetchone()
        
        if not existing:
            return error_response(404, f"Domain not found: {domain_id}")
        
        # Delete domain
        delete_query = """
            DELETE FROM domain_configurations
            WHERE tenant_id = %s AND domain_id = %s;
        """
        cursor.execute(delete_query, (tenant_id, domain_id))
        conn.commit()
        
        logger.info(f"Domain deleted successfully: {domain_id}")
        
        response_data = {
            "message": "Domain deleted successfully",
            "domain_id": domain_id
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error deleting domain: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to delete domain: {str(e)}")


# Helper functions

def get_all_agents_dict(cursor, tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all agents as a dictionary for playbook validation.
    """
    select_query = """
        SELECT agent_id, agent_name, agent_class, agent_dependencies
        FROM agent_definitions
        WHERE tenant_id = %s;
    """
    cursor.execute(select_query, (tenant_id,))
    agents = cursor.fetchall()
    
    agents_dict = {}
    for agent in agents:
        agents_dict[agent["agent_id"]] = {
            "agent_name": agent["agent_name"],
            "agent_class": agent["agent_class"],
            "agent_dependencies": agent["agent_dependencies"]
        }
    
    return agents_dict


def extract_tenant_id(event: Dict[str, Any]) -> str:
    """
    Extract tenant_id from authorizer context or query system tenant from database.
    Returns UUID string.
    """
    try:
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        tenant_id = authorizer.get("tenantId") or authorizer.get("tenant_id") or authorizer.get("claims", {}).get("custom:tenant_id")
        
        if tenant_id and tenant_id != "default-tenant":
            # If it's already a UUID, return it
            try:
                uuid.UUID(tenant_id)
                return tenant_id
            except ValueError:
                pass
        
        # Fallback: Query system tenant UUID from database
        logger.warning("No valid tenant_id found in authorizer, querying system tenant")
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tenants WHERE tenant_name = 'system' LIMIT 1")
            result = cursor.fetchone()
            if result:
                return str(result['id'])
            else:
                # If no system tenant, create one
                cursor.execute("""
                    INSERT INTO tenants (tenant_name, created_at, updated_at)
                    VALUES ('system', NOW(), NOW())
                    RETURNING id
                """)
                conn.commit()
                result = cursor.fetchone()
                return str(result['id'])
    
    except Exception as e:
        logger.error(f"Error extracting tenant_id: {e}")
        # Last resort: generate a deterministic UUID for 'system'
        import hashlib
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, 'system'))


def extract_user_id(event: Dict[str, Any]) -> str:
    """
    Extract user_id from authorizer context or query system user from database.
    Returns UUID string.
    """
    try:
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        user_id = authorizer.get("userId") or authorizer.get("user_id") or authorizer.get("claims", {}).get("sub")
        
        if user_id and user_id != "demo-user":
            # If it's already a UUID, return it
            try:
                uuid.UUID(user_id)
                return user_id
            except ValueError:
                pass
        
        # Fallback: Query system user UUID from database
        logger.warning("No valid user_id found in authorizer, querying system user")
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = 'system' LIMIT 1")
            result = cursor.fetchone()
            if result:
                return str(result['id'])
            else:
                # If no system user, create one (need tenant_id first)
                cursor.execute("SELECT id FROM tenants WHERE tenant_name = 'system' LIMIT 1")
                tenant_result = cursor.fetchone()
                if tenant_result:
                    tenant_id = str(tenant_result['id'])
                    cursor.execute("""
                        INSERT INTO users (username, email, cognito_sub, tenant_id, created_at, updated_at)
                        VALUES ('system', 'system@domainflow.ai', 'system-builtin', %s, NOW(), NOW())
                        RETURNING id
                    """, (tenant_id,))
                    conn.commit()
                    result = cursor.fetchone()
                    return str(result['id'])
        
    except Exception as e:
        logger.error(f"Error extracting user_id: {e}")
        # Last resort: generate a deterministic UUID for 'system'
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, 'system-user'))


def success_response(status_code: int, data: Any) -> Dict[str, Any]:
    """
    Format successful API response.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(data, default=str)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Format error API response.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps({
            "error": message,
            "error_code": f"ERR_{status_code}",
            "timestamp": datetime.utcnow().isoformat()
        })
    }
