"""
Configuration API Handler
Handles CRUD operations for all configuration types:
- Agent configurations
- Playbook configurations
- Dependency graph configurations
- Domain templates
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from agent_config_manager import AgentConfigManager
from playbook_config_manager import PlaybookConfigManager
from dependency_graph_manager import DependencyGraphManager
from domain_template_manager import DomainTemplateManager

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
CONFIGURATIONS_TABLE = os.environ['CONFIGURATIONS_TABLE']
CONFIG_BACKUP_BUCKET = os.environ['CONFIG_BACKUP_BUCKET']

# Initialize managers
agent_manager = AgentConfigManager(dynamodb, s3, CONFIGURATIONS_TABLE, CONFIG_BACKUP_BUCKET)
playbook_manager = PlaybookConfigManager(dynamodb, s3, CONFIGURATIONS_TABLE, CONFIG_BACKUP_BUCKET)
dependency_manager = DependencyGraphManager(dynamodb, s3, CONFIGURATIONS_TABLE, CONFIG_BACKUP_BUCKET)
template_manager = DomainTemplateManager(dynamodb, s3, CONFIGURATIONS_TABLE, CONFIG_BACKUP_BUCKET)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for configuration API
    
    Routes:
    - POST /api/v1/config - Create configuration
    - GET /api/v1/config/{type}/{id} - Get configuration
    - PUT /api/v1/config/{type}/{id} - Update configuration
    - DELETE /api/v1/config/{type}/{id} - Delete configuration
    - GET /api/v1/config?type={type} - List configurations by type
    """
    try:
        # Extract request details
        http_method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Extract tenant_id from authorizer context
        authorizer_context = event.get('requestContext', {}).get('authorizer', {})
        tenant_id = authorizer_context.get('tenant_id')
        user_id = authorizer_context.get('user_id')
        
        if not tenant_id:
            return error_response(401, 'Unauthorized: Missing tenant_id')
        
        logger.info(f"Request: {http_method} tenant={tenant_id} path={path_parameters} query={query_parameters}")
        
        # Route based on HTTP method and path
        if http_method == 'POST' and not path_parameters:
            # Create configuration
            return create_config(tenant_id, user_id, body)
        
        elif http_method == 'GET' and path_parameters:
            # Get specific configuration
            config_type = path_parameters.get('type')
            config_id = path_parameters.get('id')
            return get_config(tenant_id, config_type, config_id)
        
        elif http_method == 'GET' and query_parameters.get('type'):
            # List configurations by type
            config_type = query_parameters.get('type')
            return list_configs(tenant_id, user_id, config_type)
        
        elif http_method == 'PUT' and path_parameters:
            # Update configuration
            config_type = path_parameters.get('type')
            config_id = path_parameters.get('id')
            return update_config(tenant_id, user_id, config_type, config_id, body)
        
        elif http_method == 'DELETE' and path_parameters:
            # Delete configuration
            config_type = path_parameters.get('type')
            config_id = path_parameters.get('id')
            return delete_config(tenant_id, config_type, config_id)
        
        else:
            return error_response(400, 'Invalid request')
    
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}", exc_info=True)
        return error_response(500, f"Internal server error: {str(e)}")


def create_config(tenant_id: str, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new configuration"""
    config_type = body.get('type')
    config_data = body.get('config')
    
    if not config_type or not config_data:
        return error_response(400, 'Missing required fields: type, config')
    
    try:
        if config_type == 'agent':
            result = agent_manager.create(tenant_id, user_id, config_data)
        elif config_type == 'playbook':
            result = playbook_manager.create(tenant_id, user_id, config_data)
        elif config_type == 'dependency_graph':
            result = dependency_manager.create(tenant_id, user_id, config_data)
        elif config_type == 'domain_template':
            # Check if simplified format (agent_ids) or full format
            if 'ingest_agent_ids' in config_data and 'query_agent_ids' in config_data:
                # Simplified format - create from agent IDs
                result = template_manager.create_from_agent_ids(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    template_name=config_data.get('template_name', ''),
                    domain_id=config_data.get('domain_id', ''),
                    ingest_agent_ids=config_data['ingest_agent_ids'],
                    query_agent_ids=config_data['query_agent_ids'],
                    description=config_data.get('description', '')
                )
            else:
                # Full format - use existing create method
                result = template_manager.create(tenant_id, user_id, config_data)
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        return success_response(201, result)
    
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        logger.error(f"Error creating config: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to create configuration: {str(e)}")


def get_config(tenant_id: str, config_type: str, config_id: str) -> Dict[str, Any]:
    """Get a specific configuration"""
    try:
        if config_type == 'agent':
            result = agent_manager.get(tenant_id, config_id)
        elif config_type == 'playbook':
            result = playbook_manager.get(tenant_id, config_id)
        elif config_type == 'dependency_graph':
            result = dependency_manager.get(tenant_id, config_id)
        elif config_type == 'domain_template':
            result = template_manager.get(tenant_id, config_id)
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        if not result:
            return error_response(404, f'Configuration not found: {config_type}/{config_id}')
        
        return success_response(200, result)
    
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to get configuration: {str(e)}")


def list_configs(tenant_id: str, user_id: str, config_type: str) -> Dict[str, Any]:
    """List all configurations of a specific type"""
    try:
        if config_type == 'agent':
            results = agent_manager.list(tenant_id)
            # Add metadata flags
            for agent in results:
                agent['is_builtin'] = agent.get('is_builtin', False)
                agent['created_by_me'] = agent.get('created_by') == user_id
                
        elif config_type == 'playbook':
            results = playbook_manager.list(tenant_id)
            
        elif config_type == 'dependency_graph':
            results = dependency_manager.list(tenant_id)
            
        elif config_type == 'domain_template':
            results = template_manager.list(tenant_id)
            # Add metadata for domain templates
            for domain in results:
                domain['is_builtin'] = domain.get('is_builtin', False)
                domain['created_by_me'] = domain.get('created_by') == user_id
                # Count agents in this domain
                domain['agent_count'] = len(domain.get('agent_configs', []))
                # Get incident count from data layer (placeholder - would need actual query)
                domain['incident_count'] = 0  # TODO: Query actual incident count from data API
                
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        return success_response(200, {'configs': results, 'count': len(results)})
    
    except Exception as e:
        logger.error(f"Error listing configs: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to list configurations: {str(e)}")


def update_config(tenant_id: str, user_id: str, config_type: str, config_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing configuration"""
    config_data = body.get('config')
    
    if not config_data:
        return error_response(400, 'Missing required field: config')
    
    try:
        if config_type == 'agent':
            result = agent_manager.update(tenant_id, user_id, config_id, config_data)
        elif config_type == 'playbook':
            result = playbook_manager.update(tenant_id, user_id, config_id, config_data)
        elif config_type == 'dependency_graph':
            result = dependency_manager.update(tenant_id, user_id, config_id, config_data)
        elif config_type == 'domain_template':
            result = template_manager.update(tenant_id, user_id, config_id, config_data)
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        if not result:
            return error_response(404, f'Configuration not found: {config_type}/{config_id}')
        
        return success_response(200, result)
    
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to update configuration: {str(e)}")


def delete_config(tenant_id: str, config_type: str, config_id: str) -> Dict[str, Any]:
    """Delete a configuration"""
    try:
        if config_type == 'agent':
            success = agent_manager.delete(tenant_id, config_id)
        elif config_type == 'playbook':
            success = playbook_manager.delete(tenant_id, config_id)
        elif config_type == 'dependency_graph':
            success = dependency_manager.delete(tenant_id, config_id)
        elif config_type == 'domain_template':
            success = template_manager.delete(tenant_id, config_id)
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        if not success:
            return error_response(404, f'Configuration not found: {config_type}/{config_id}')
        
        return success_response(200, {'message': 'Configuration deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting config: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to delete configuration: {str(e)}")


def success_response(status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate success response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(data, default=str)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Generate error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
