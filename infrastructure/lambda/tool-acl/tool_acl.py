"""
Tool Access Control Layer Lambda

Verifies agent permissions to access tools and returns tool metadata with credentials.
Implements in-memory caching with 5-minute TTL.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')

# Environment variables
TOOL_CATALOG_TABLE = os.environ.get('TOOL_CATALOG_TABLE', 'tool_catalog')
TOOL_PERMISSIONS_TABLE = os.environ.get('TOOL_PERMISSIONS_TABLE', 'tool_permissions')

tool_catalog_table = dynamodb.Table(TOOL_CATALOG_TABLE)
tool_permissions_table = dynamodb.Table(TOOL_PERMISSIONS_TABLE)

# In-memory cache with 5-minute TTL
cache = {}
CACHE_TTL_SECONDS = 300


class DecimalEncoder(json.JSONEncoder):
    """Helper to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_from_cache(key: str) -> Optional[Dict[str, Any]]:
    """
    Get value from cache if not expired.
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if expired/not found
    """
    if key in cache:
        entry = cache[key]
        if datetime.utcnow() < entry['expires_at']:
            logger.info(f"Cache hit for key: {key}")
            return entry['value']
        else:
            # Expired, remove from cache
            del cache[key]
            logger.info(f"Cache expired for key: {key}")
    
    return None


def set_in_cache(key: str, value: Dict[str, Any]) -> None:
    """
    Store value in cache with TTL.
    
    Args:
        key: Cache key
        value: Value to cache
    """
    cache[key] = {
        'value': value,
        'expires_at': datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS)
    }
    logger.info(f"Cached value for key: {key}")


def check_permission(tenant_id: str, agent_id: str, tool_name: str) -> bool:
    """
    Check if agent has permission to access tool.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
        tool_name: Tool name
    
    Returns:
        True if permission granted, False otherwise
    """
    # Check cache first
    cache_key = f"perm:{tenant_id}:{agent_id}:{tool_name}"
    cached_result = get_from_cache(cache_key)
    
    if cached_result is not None:
        return cached_result.get('allowed', False)
    
    try:
        # Query DynamoDB for permission
        pk = f"{tenant_id}#{agent_id}"
        response = tool_permissions_table.get_item(
            Key={
                'tenant_agent_id': pk,
                'tool_name': tool_name
            }
        )
        
        if 'Item' in response:
            allowed = response['Item'].get('allowed', False)
            # Cache the result
            set_in_cache(cache_key, {'allowed': allowed})
            return allowed
        
        # No explicit permission = denied
        set_in_cache(cache_key, {'allowed': False})
        return False
    
    except Exception as e:
        logger.error(f"Error checking permission: {str(e)}")
        # Fail closed - deny access on error
        return False


def get_tool_metadata(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve tool metadata from catalog.
    
    Args:
        tool_name: Tool identifier
    
    Returns:
        Tool metadata or None if not found
    """
    # Check cache first
    cache_key = f"tool:{tool_name}"
    cached_result = get_from_cache(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    try:
        response = tool_catalog_table.get_item(Key={'tool_name': tool_name})
        
        if 'Item' in response:
            tool_data = response['Item']
            # Cache the result
            set_in_cache(cache_key, tool_data)
            return tool_data
        
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving tool metadata: {str(e)}")
        return None


def get_tool_credentials(tool_name: str, auth_method: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve tool credentials from Secrets Manager.
    
    Args:
        tool_name: Tool identifier
        auth_method: Authentication method
    
    Returns:
        Credentials dict or None
    """
    # IAM auth doesn't need credentials
    if auth_method == 'iam':
        return {'auth_type': 'iam', 'message': 'Use IAM role'}
    
    # No auth needed
    if auth_method == 'none':
        return {'auth_type': 'none'}
    
    # Retrieve from Secrets Manager
    try:
        secret_name = f"tool-credentials/{tool_name}"
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            credentials = json.loads(response['SecretString'])
            return credentials
        
        return None
    
    except secrets_client.exceptions.ResourceNotFoundException:
        logger.warning(f"Credentials not found for tool: {tool_name}")
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving credentials: {str(e)}")
        return None


def verify_tool_access(
    tenant_id: str,
    agent_id: str,
    tool_name: str,
    include_credentials: bool = True
) -> Dict[str, Any]:
    """
    Verify tool access and return tool metadata with credentials.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
        tool_name: Tool name
        include_credentials: Whether to include credentials in response
    
    Returns:
        Dict with access status, tool metadata, and credentials
    """
    # Check permission
    has_permission = check_permission(tenant_id, agent_id, tool_name)
    
    if not has_permission:
        return {
            'allowed': False,
            'tool_name': tool_name,
            'error': 'permission_denied',
            'message': f"Agent '{agent_id}' does not have permission to access tool '{tool_name}'"
        }
    
    # Get tool metadata
    tool_metadata = get_tool_metadata(tool_name)
    
    if not tool_metadata:
        return {
            'allowed': False,
            'tool_name': tool_name,
            'error': 'tool_not_found',
            'message': f"Tool '{tool_name}' not found in catalog"
        }
    
    # Prepare response
    response = {
        'allowed': True,
        'tool_name': tool_name,
        'tool_metadata': {
            'tool_type': tool_metadata.get('tool_type'),
            'endpoint': tool_metadata.get('endpoint'),
            'auth_method': tool_metadata.get('auth_method'),
            'description': tool_metadata.get('description'),
            'parameters_schema': tool_metadata.get('parameters_schema')
        }
    }
    
    # Include credentials if requested
    if include_credentials:
        auth_method = tool_metadata.get('auth_method')
        credentials = get_tool_credentials(tool_name, auth_method)
        
        if credentials:
            response['credentials'] = credentials
        else:
            logger.warning(f"Credentials not available for tool: {tool_name}")
    
    return response


def grant_permission(tenant_id: str, agent_id: str, tool_name: str) -> Dict[str, Any]:
    """
    Grant tool access permission to agent.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
        tool_name: Tool name
    
    Returns:
        Permission record
    """
    pk = f"{tenant_id}#{agent_id}"
    
    permission_record = {
        'tenant_agent_id': pk,
        'tool_name': tool_name,
        'tenant_id': tenant_id,
        'agent_id': agent_id,
        'allowed': True,
        'granted_at': int(datetime.utcnow().timestamp())
    }
    
    tool_permissions_table.put_item(Item=permission_record)
    
    # Invalidate cache
    cache_key = f"perm:{tenant_id}:{agent_id}:{tool_name}"
    if cache_key in cache:
        del cache[cache_key]
    
    logger.info(f"Granted permission: {tenant_id}/{agent_id} -> {tool_name}")
    return permission_record


def revoke_permission(tenant_id: str, agent_id: str, tool_name: str) -> Dict[str, Any]:
    """
    Revoke tool access permission from agent.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
        tool_name: Tool name
    
    Returns:
        Revocation confirmation
    """
    pk = f"{tenant_id}#{agent_id}"
    
    tool_permissions_table.delete_item(
        Key={
            'tenant_agent_id': pk,
            'tool_name': tool_name
        }
    )
    
    # Invalidate cache
    cache_key = f"perm:{tenant_id}:{agent_id}:{tool_name}"
    if cache_key in cache:
        del cache[cache_key]
    
    logger.info(f"Revoked permission: {tenant_id}/{agent_id} -> {tool_name}")
    return {
        'tenant_id': tenant_id,
        'agent_id': agent_id,
        'tool_name': tool_name,
        'status': 'revoked'
    }


def list_agent_permissions(tenant_id: str, agent_id: str) -> list[Dict[str, Any]]:
    """
    List all tool permissions for an agent.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
    
    Returns:
        List of permission records
    """
    pk = f"{tenant_id}#{agent_id}"
    
    try:
        response = tool_permissions_table.query(
            KeyConditionExpression='tenant_agent_id = :pk',
            ExpressionAttributeValues={':pk': pk}
        )
        
        permissions = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = tool_permissions_table.query(
                KeyConditionExpression='tenant_agent_id = :pk',
                ExpressionAttributeValues={':pk': pk},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            permissions.extend(response.get('Items', []))
        
        return permissions
    
    except Exception as e:
        logger.error(f"Error listing permissions: {str(e)}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for tool access control operations.
    
    Supports:
    - POST /tool-access/verify - Verify tool access
    - POST /tool-access/grant - Grant permission
    - DELETE /tool-access/revoke - Revoke permission
    - GET /tool-access/list - List agent permissions
    """
    try:
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method'))
        path = event.get('path', event.get('rawPath', ''))
        query_params = event.get('queryStringParameters') or {}
        
        # Parse body if present
        body = {}
        if event.get('body'):
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        # Extract tenant_id from JWT (would come from authorizer in real implementation)
        tenant_id = event.get('requestContext', {}).get('authorizer', {}).get('tenant_id', body.get('tenant_id'))
        
        if not tenant_id:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'unauthorized', 'message': 'Missing tenant_id'})
            }
        
        # Route to appropriate handler
        if 'verify' in path and http_method == 'POST':
            # Verify tool access
            agent_id = body.get('agent_id')
            tool_name = body.get('tool_name')
            include_credentials = body.get('include_credentials', True)
            
            if not agent_id or not tool_name:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing agent_id or tool_name'})
                }
            
            result = verify_tool_access(tenant_id, agent_id, tool_name, include_credentials)
            status_code = 200 if result.get('allowed') else 403
            
            return {
                'statusCode': status_code,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        
        elif 'grant' in path and http_method == 'POST':
            # Grant permission
            agent_id = body.get('agent_id')
            tool_name = body.get('tool_name')
            
            if not agent_id or not tool_name:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing agent_id or tool_name'})
                }
            
            result = grant_permission(tenant_id, agent_id, tool_name)
            
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        
        elif 'revoke' in path and http_method in ['POST', 'DELETE']:
            # Revoke permission
            agent_id = body.get('agent_id')
            tool_name = body.get('tool_name')
            
            if not agent_id or not tool_name:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing agent_id or tool_name'})
                }
            
            result = revoke_permission(tenant_id, agent_id, tool_name)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif 'list' in path and http_method == 'GET':
            # List permissions
            agent_id = query_params.get('agent_id')
            
            if not agent_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing agent_id'})
                }
            
            result = list_agent_permissions(tenant_id, agent_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'permissions': result, 'count': len(result)}, cls=DecimalEncoder)
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Invalid request'})
            }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal_error', 'message': 'Internal server error'})
        }
