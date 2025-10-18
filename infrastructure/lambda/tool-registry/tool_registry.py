"""
Tool Registry Management Lambda

Handles CRUD operations for tool catalog in DynamoDB.
Supports built-in and custom tools.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TOOL_CATALOG_TABLE', 'tool_catalog')
tool_catalog_table = dynamodb.Table(table_name)


class DecimalEncoder(json.JSONEncoder):
    """Helper to convert Decimal to int/float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def validate_tool_metadata(tool_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate tool metadata structure.
    
    Args:
        tool_data: Tool metadata dict
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['tool_name', 'tool_type', 'endpoint', 'auth_method']
    
    for field in required_fields:
        if field not in tool_data:
            return False, f"Missing required field: {field}"
    
    # Validate tool_type
    valid_types = ['aws_service', 'external_api', 'custom', 'data_api']
    if tool_data['tool_type'] not in valid_types:
        return False, f"Invalid tool_type. Must be one of: {', '.join(valid_types)}"
    
    # Validate auth_method
    valid_auth = ['iam', 'api_key', 'oauth', 'custom', 'none']
    if tool_data['auth_method'] not in valid_auth:
        return False, f"Invalid auth_method. Must be one of: {', '.join(valid_auth)}"
    
    return True, None


def create_tool(tool_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a new tool in the catalog.
    
    Args:
        tool_data: Tool metadata
    
    Returns:
        Created tool data
    """
    # Validate metadata
    is_valid, error_msg = validate_tool_metadata(tool_data)
    if not is_valid:
        raise ValueError(error_msg)
    
    tool_name = tool_data['tool_name']
    
    # Check if tool already exists
    try:
        response = tool_catalog_table.get_item(Key={'tool_name': tool_name})
        if 'Item' in response:
            raise ValueError(f"Tool '{tool_name}' already exists")
    except Exception as e:
        if "already exists" not in str(e):
            logger.error(f"Error checking tool existence: {str(e)}")
    
    # Add metadata
    tool_data['created_at'] = int(datetime.utcnow().timestamp())
    tool_data['updated_at'] = int(datetime.utcnow().timestamp())
    tool_data['is_builtin'] = tool_data.get('is_builtin', False)
    
    # Store in DynamoDB
    tool_catalog_table.put_item(Item=tool_data)
    
    logger.info(f"Created tool: {tool_name}")
    return tool_data


def get_tool(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve tool metadata by name.
    
    Args:
        tool_name: Tool identifier
    
    Returns:
        Tool metadata or None if not found
    """
    try:
        response = tool_catalog_table.get_item(Key={'tool_name': tool_name})
        
        if 'Item' in response:
            return response['Item']
        
        return None
    except Exception as e:
        logger.error(f"Error retrieving tool '{tool_name}': {str(e)}")
        raise


def update_tool(tool_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update tool metadata.
    
    Args:
        tool_name: Tool identifier
        updates: Fields to update
    
    Returns:
        Updated tool data
    """
    # Get existing tool
    existing_tool = get_tool(tool_name)
    if not existing_tool:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # Prevent updating tool_name
    if 'tool_name' in updates and updates['tool_name'] != tool_name:
        raise ValueError("Cannot change tool_name")
    
    # Prevent updating is_builtin for built-in tools
    if existing_tool.get('is_builtin') and 'is_builtin' in updates:
        raise ValueError("Cannot modify is_builtin flag for built-in tools")
    
    # Merge updates
    updated_tool = {**existing_tool, **updates}
    updated_tool['updated_at'] = int(datetime.utcnow().timestamp())
    
    # Validate updated metadata
    is_valid, error_msg = validate_tool_metadata(updated_tool)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Store updated tool
    tool_catalog_table.put_item(Item=updated_tool)
    
    logger.info(f"Updated tool: {tool_name}")
    return updated_tool


def delete_tool(tool_name: str) -> Dict[str, Any]:
    """
    Delete tool from catalog.
    
    Args:
        tool_name: Tool identifier
    
    Returns:
        Deletion confirmation
    """
    # Get existing tool
    existing_tool = get_tool(tool_name)
    if not existing_tool:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # Prevent deleting built-in tools
    if existing_tool.get('is_builtin'):
        raise ValueError("Cannot delete built-in tools")
    
    # Delete from DynamoDB
    tool_catalog_table.delete_item(Key={'tool_name': tool_name})
    
    logger.info(f"Deleted tool: {tool_name}")
    return {'tool_name': tool_name, 'status': 'deleted'}


def list_tools(tool_type: Optional[str] = None) -> list[Dict[str, Any]]:
    """
    List all tools, optionally filtered by type.
    
    Args:
        tool_type: Optional filter by tool type
    
    Returns:
        List of tool metadata
    """
    try:
        if tool_type:
            # Scan with filter
            response = tool_catalog_table.scan(
                FilterExpression='tool_type = :type',
                ExpressionAttributeValues={':type': tool_type}
            )
        else:
            # Scan all
            response = tool_catalog_table.scan()
        
        tools = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            if tool_type:
                response = tool_catalog_table.scan(
                    FilterExpression='tool_type = :type',
                    ExpressionAttributeValues={':type': tool_type},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            else:
                response = tool_catalog_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
            tools.extend(response.get('Items', []))
        
        return tools
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for tool registry operations.
    
    Supports:
    - POST /tools - Create tool
    - GET /tools/{tool_name} - Get tool
    - PUT /tools/{tool_name} - Update tool
    - DELETE /tools/{tool_name} - Delete tool
    - GET /tools - List tools
    """
    try:
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method'))
        path = event.get('path', event.get('rawPath', ''))
        path_params = event.get('pathParameters') or {}
        query_params = event.get('queryStringParameters') or {}
        
        # Parse body if present
        body = {}
        if event.get('body'):
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        # Route to appropriate handler
        if http_method == 'POST' and path.endswith('/tools'):
            # Create tool
            result = create_tool(body)
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        
        elif http_method == 'GET' and path_params.get('tool_name'):
            # Get specific tool
            tool_name = path_params['tool_name']
            result = get_tool(tool_name)
            
            if result:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(result, cls=DecimalEncoder)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'not_found', 'message': f"Tool '{tool_name}' not found"})
                }
        
        elif http_method == 'GET' and path.endswith('/tools'):
            # List tools
            tool_type = query_params.get('type')
            result = list_tools(tool_type)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'tools': result, 'count': len(result)}, cls=DecimalEncoder)
            }
        
        elif http_method == 'PUT' and path_params.get('tool_name'):
            # Update tool
            tool_name = path_params['tool_name']
            result = update_tool(tool_name, body)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        
        elif http_method == 'DELETE' and path_params.get('tool_name'):
            # Delete tool
            tool_name = path_params['tool_name']
            result = delete_tool(tool_name)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Invalid request'})
            }
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'validation_error', 'message': str(e)})
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal_error', 'message': 'Internal server error'})
        }
