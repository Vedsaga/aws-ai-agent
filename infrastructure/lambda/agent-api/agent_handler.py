"""
Agent Handler Lambda
Handles CRUD operations for agent management with DAG validation.
Supports all three agent classes: ingestion, query, management
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

# Import DAG validator
from dag_validator import validate_dag, build_dependency_graph

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
    Main Lambda handler for agent management API.
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
        if http_method == "POST" and "/agents" in path and not path_params:
            # Create agent
            return create_agent(tenant_id, user_id, body, event)
        
        elif http_method == "GET" and "/agents" in path and not path_params:
            # List agents
            return list_agents(tenant_id, user_id, query_params)
        
        elif http_method == "GET" and path_params.get("agent_id"):
            # Get specific agent
            agent_id = path_params.get("agent_id")
            return get_agent(tenant_id, user_id, agent_id)
        
        elif http_method == "PUT" and path_params.get("agent_id"):
            # Update agent
            agent_id = path_params.get("agent_id")
            return update_agent(tenant_id, user_id, agent_id, body)
        
        elif http_method == "DELETE" and path_params.get("agent_id"):
            # Delete agent
            agent_id = path_params.get("agent_id")
            return delete_agent(tenant_id, user_id, agent_id)
        
        else:
            return error_response(404, "Endpoint not found")
    
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return error_response(500, f"Internal server error: {str(e)}")


def ensure_user_exists(cursor, user_id: str, tenant_id: str, event: Dict[str, Any]) -> None:
    """
    Ensure user exists in database. Auto-create if from Cognito but not in DB.
    This is needed for hackathon - users authenticated via Cognito may not exist in DB yet.
    """
    try:
        # Check if user exists by UUID
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if cursor.fetchone():
            return  # User exists
        
        # User doesn't exist - get info from authorizer context
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        cognito_sub = authorizer.get("userId", user_id)
        username = authorizer.get("username", f"user-{user_id[:8]}")
        
        # Auto-create user
        logger.info(f"Auto-creating user {username} ({cognito_sub}) for tenant {tenant_id}")
        cursor.execute("""
            INSERT INTO users (id, username, email, cognito_sub, tenant_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """, (user_id, username, f"{username}@auto-created.local", cognito_sub, tenant_id))
        
        logger.info(f"User {username} auto-created successfully")
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}", exc_info=True)
        # Don't fail the request if user creation fails - let the FK constraint handle it


def create_agent(tenant_id: str, user_id: str, body: Dict[str, Any], event: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a new agent with DAG validation.
    
    Request body:
    {
        "agent_name": "string",
        "agent_class": "ingestion|query|management",
        "system_prompt": "string",
        "tools": ["string"],
        "agent_dependencies": ["agent_id"],
        "output_schema": {object},
        "description": "string",
        "enabled": boolean
    }
    """
    logger.info(f"Creating agent for tenant {tenant_id}")
    
    try:
        # Validate required fields
        required_fields = ["agent_name", "agent_class", "system_prompt", "output_schema"]
        for field in required_fields:
            if field not in body:
                return error_response(400, f"Missing required field: {field}")
        
        # Validate agent_class
        agent_class = body.get("agent_class")
        if agent_class not in ["ingestion", "query", "management"]:
            return error_response(400, f"Invalid agent_class: {agent_class}. Must be one of: ingestion, query, management")
        
        # Validate output_schema has max 5 properties
        output_schema = body.get("output_schema", {})
        if not isinstance(output_schema, dict):
            return error_response(400, "output_schema must be a JSON object")
        
        # Check if schema has "properties" key (JSON Schema format) or direct keys
        if "properties" in output_schema:
            if len(output_schema["properties"]) > 5:
                return error_response(400, "output_schema can have maximum 5 properties")
        else:
            # Direct keys format
            if len(output_schema) > 5:
                return error_response(400, "output_schema can have maximum 5 properties")
        
        # Get agent dependencies
        agent_dependencies = body.get("agent_dependencies", [])
        
        # Validate dependencies exist and perform DAG validation
        if agent_dependencies:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all agents for DAG validation
            all_agents = get_all_agents_dict(cursor, tenant_id)
            
            # Validate DAG
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
            is_valid, error_msg = validate_dag(agent_id, agent_dependencies, all_agents)
            
            if not is_valid:
                return error_response(400, f"Circular dependency detected: {error_msg}")
        else:
            agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        
        # Insert agent into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure user exists (auto-create if needed for hackathon)
        if event:
            ensure_user_exists(cursor, user_id, tenant_id, event)
            conn.commit()
        
        insert_query = """
            INSERT INTO agent_definitions (
                agent_id, tenant_id, agent_name, agent_class, system_prompt,
                tools, agent_dependencies, max_output_keys, output_schema,
                description, enabled, is_inbuilt, version, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, agent_id, agent_name, agent_class, version, is_inbuilt,
                      created_at, updated_at, created_by;
        """
        
        cursor.execute(insert_query, (
            agent_id,
            tenant_id,
            body.get("agent_name"),
            agent_class,
            body.get("system_prompt"),
            json.dumps(body.get("tools", [])),
            json.dumps(agent_dependencies),
            5,  # max_output_keys locked at 5
            json.dumps(output_schema),
            body.get("description"),
            body.get("enabled", True),
            False,  # is_inbuilt always False for user-created agents
            1,  # initial version
            user_id
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        logger.info(f"Agent created successfully: {agent_id}")
        
        # Format response
        response_data = {
            "agent_id": result["agent_id"],
            "agent_name": result["agent_name"],
            "agent_class": result["agent_class"],
            "version": result["version"],
            "is_inbuilt": result["is_inbuilt"],
            "id": str(result["id"]),
            "created_at": result["created_at"].isoformat(),
            "updated_at": result["updated_at"].isoformat(),
            "created_by": str(result["created_by"])
        }
        
        return success_response(201, response_data)
    
    except psycopg.errors.UniqueViolation as e:
        logger.error(f"Database integrity error: {str(e)}")
        conn.rollback()
        return error_response(409, "Agent with this ID already exists")
    
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to create agent: {str(e)}")


def list_agents(tenant_id: str, user_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    List agents with optional filtering by agent_class.
    
    Query parameters:
    - page: int (default: 1)
    - limit: int (default: 20, max: 100)
    - agent_class: string (optional filter)
    """
    logger.info(f"Listing agents for tenant {tenant_id}")
    
    try:
        # Parse pagination parameters
        page = int(query_params.get("page", 1))
        limit = min(int(query_params.get("limit", 20)), 100)
        offset = (page - 1) * limit
        
        agent_class_filter = query_params.get("agent_class")
        
        # Validate agent_class filter
        if agent_class_filter and agent_class_filter not in ["ingestion", "query", "management"]:
            return error_response(400, f"Invalid agent_class filter: {agent_class_filter}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with optional filter
        if agent_class_filter:
            count_query = """
                SELECT COUNT(*) as total
                FROM agent_definitions
                WHERE tenant_id = %s AND agent_class = %s;
            """
            cursor.execute(count_query, (tenant_id, agent_class_filter))
        else:
            count_query = """
                SELECT COUNT(*) as total
                FROM agent_definitions
                WHERE tenant_id = %s;
            """
            cursor.execute(count_query, (tenant_id,))
        
        total = cursor.fetchone()["total"]
        
        # Get agents
        if agent_class_filter:
            select_query = """
                SELECT agent_id, agent_name, agent_class, enabled, is_inbuilt,
                       created_at, created_by
                FROM agent_definitions
                WHERE tenant_id = %s AND agent_class = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
            """
            cursor.execute(select_query, (tenant_id, agent_class_filter, limit, offset))
        else:
            select_query = """
                SELECT agent_id, agent_name, agent_class, enabled, is_inbuilt,
                       created_at, created_by
                FROM agent_definitions
                WHERE tenant_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
            """
            cursor.execute(select_query, (tenant_id, limit, offset))
        
        agents = cursor.fetchall()
        
        # Format response
        agents_list = []
        for agent in agents:
            agents_list.append({
                "agent_id": agent["agent_id"],
                "agent_name": agent["agent_name"],
                "agent_class": agent["agent_class"],
                "enabled": agent["enabled"],
                "is_inbuilt": agent["is_inbuilt"],
                "created_at": agent["created_at"].isoformat(),
                "created_by_me": str(agent["created_by"]) == user_id
            })
        
        response_data = {
            "agents": agents_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to list agents: {str(e)}")


def get_agent(tenant_id: str, user_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Get a specific agent with dependency graph.
    """
    logger.info(f"Getting agent {agent_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get agent
        select_query = """
            SELECT id, agent_id, agent_name, agent_class, system_prompt, tools,
                   agent_dependencies, max_output_keys, output_schema, description,
                   enabled, is_inbuilt, version, created_at, updated_at
            FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = %s;
        """
        cursor.execute(select_query, (tenant_id, agent_id))
        agent = cursor.fetchone()
        
        if not agent:
            return error_response(404, f"Agent not found: {agent_id}")
        
        # Get all agents for dependency graph
        all_agents = get_all_agents_dict(cursor, tenant_id)
        
        # Build dependency graph
        dependency_graph = build_dependency_graph(agent_id, all_agents)
        
        # Format response
        response_data = {
            "agent_id": agent["agent_id"],
            "agent_name": agent["agent_name"],
            "agent_class": agent["agent_class"],
            "system_prompt": agent["system_prompt"],
            "tools": agent["tools"],
            "agent_dependencies": agent["agent_dependencies"],
            "dependency_graph": dependency_graph,
            "max_output_keys": agent["max_output_keys"],
            "output_schema": agent["output_schema"],
            "description": agent["description"],
            "enabled": agent["enabled"],
            "is_inbuilt": agent["is_inbuilt"],
            "id": str(agent["id"]),
            "created_at": agent["created_at"].isoformat(),
            "updated_at": agent["updated_at"].isoformat(),
            "version": agent["version"]
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error getting agent: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to get agent: {str(e)}")


def update_agent(tenant_id: str, user_id: str, agent_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an agent with circular dependency check.
    
    Request body (all fields optional):
    {
        "agent_name": "string",
        "system_prompt": "string",
        "tools": ["string"],
        "agent_dependencies": ["agent_id"],
        "output_schema": {object},
        "description": "string",
        "enabled": boolean
    }
    """
    logger.info(f"Updating agent {agent_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if agent exists and is not builtin
        check_query = """
            SELECT is_inbuilt, version
            FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = %s;
        """
        cursor.execute(check_query, (tenant_id, agent_id))
        existing = cursor.fetchone()
        
        if not existing:
            return error_response(404, f"Agent not found: {agent_id}")
        
        if existing["is_inbuilt"]:
            return error_response(403, "Cannot modify builtin agents")
        
        # Validate agent_dependencies if provided
        if "agent_dependencies" in body:
            agent_dependencies = body.get("agent_dependencies", [])
            
            # Get all agents for DAG validation
            all_agents = get_all_agents_dict(cursor, tenant_id)
            
            # Validate DAG
            is_valid, error_msg = validate_dag(agent_id, agent_dependencies, all_agents)
            
            if not is_valid:
                return error_response(400, f"Circular dependency detected: {error_msg}")
        
        # Validate output_schema if provided
        if "output_schema" in body:
            output_schema = body.get("output_schema")
            if not isinstance(output_schema, dict):
                return error_response(400, "output_schema must be a JSON object")
            
            # Check if schema has "properties" key (JSON Schema format) or direct keys
            if "properties" in output_schema:
                if len(output_schema["properties"]) > 5:
                    return error_response(400, "output_schema can have maximum 5 properties")
            else:
                # Direct keys format
                if len(output_schema) > 5:
                    return error_response(400, "output_schema can have maximum 5 properties")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if "agent_name" in body:
            update_fields.append("agent_name = %s")
            update_values.append(body["agent_name"])
        
        if "system_prompt" in body:
            update_fields.append("system_prompt = %s")
            update_values.append(body["system_prompt"])
        
        if "tools" in body:
            update_fields.append("tools = %s")
            update_values.append(json.dumps(body["tools"]))
        
        if "agent_dependencies" in body:
            update_fields.append("agent_dependencies = %s")
            update_values.append(json.dumps(body["agent_dependencies"]))
        
        if "output_schema" in body:
            update_fields.append("output_schema = %s")
            update_values.append(json.dumps(body["output_schema"]))
        
        if "description" in body:
            update_fields.append("description = %s")
            update_values.append(body["description"])
        
        if "enabled" in body:
            update_fields.append("enabled = %s")
            update_values.append(body["enabled"])
        
        # Increment version
        update_fields.append("version = version + 1")
        
        if not update_fields:
            return error_response(400, "No fields to update")
        
        # Execute update
        update_query = f"""
            UPDATE agent_definitions
            SET {', '.join(update_fields)}
            WHERE tenant_id = %s AND agent_id = %s
            RETURNING id, agent_id, agent_name, agent_class, system_prompt, tools,
                      agent_dependencies, max_output_keys, output_schema, description,
                      enabled, is_inbuilt, version, created_at, updated_at;
        """
        
        update_values.extend([tenant_id, agent_id])
        cursor.execute(update_query, update_values)
        
        result = cursor.fetchone()
        conn.commit()
        
        # Get all agents for dependency graph
        all_agents = get_all_agents_dict(cursor, tenant_id)
        
        # Build dependency graph
        dependency_graph = build_dependency_graph(agent_id, all_agents)
        
        logger.info(f"Agent updated successfully: {agent_id}")
        
        # Format response
        response_data = {
            "agent_id": result["agent_id"],
            "agent_name": result["agent_name"],
            "agent_class": result["agent_class"],
            "system_prompt": result["system_prompt"],
            "tools": result["tools"],
            "agent_dependencies": result["agent_dependencies"],
            "dependency_graph": dependency_graph,
            "max_output_keys": result["max_output_keys"],
            "output_schema": result["output_schema"],
            "description": result["description"],
            "enabled": result["enabled"],
            "is_inbuilt": result["is_inbuilt"],
            "id": str(result["id"]),
            "created_at": result["created_at"].isoformat(),
            "updated_at": result["updated_at"].isoformat(),
            "version": result["version"]
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to update agent: {str(e)}")


def delete_agent(tenant_id: str, user_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Delete an agent (only non-builtin agents).
    """
    logger.info(f"Deleting agent {agent_id} for tenant {tenant_id}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if agent exists and is not builtin
        check_query = """
            SELECT is_inbuilt
            FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = %s;
        """
        cursor.execute(check_query, (tenant_id, agent_id))
        existing = cursor.fetchone()
        
        if not existing:
            return error_response(404, f"Agent not found: {agent_id}")
        
        if existing["is_inbuilt"]:
            return error_response(403, "Cannot delete builtin agents")
        
        # Delete agent
        delete_query = """
            DELETE FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = %s;
        """
        cursor.execute(delete_query, (tenant_id, agent_id))
        conn.commit()
        
        logger.info(f"Agent deleted successfully: {agent_id}")
        
        response_data = {
            "message": "Agent deleted successfully",
            "agent_id": agent_id
        }
        
        return success_response(200, response_data)
    
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return error_response(500, f"Failed to delete agent: {str(e)}")


# Helper functions

def get_all_agents_dict(cursor, tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all agents as a dictionary for DAG validation.
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
