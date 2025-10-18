"""
Agent Configuration Manager
Handles CRUD operations for agent configurations with validation
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger()


class AgentConfigManager:
    """Manages agent configuration CRUD operations"""
    
    def __init__(self, dynamodb, s3, table_name: str, backup_bucket: str):
        self.dynamodb = dynamodb
        self.s3 = s3
        self.table = dynamodb.Table(table_name)
        self.backup_bucket = backup_bucket
    
    def create(self, tenant_id: str, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent configuration"""
        # Validate required fields
        self._validate_agent_config(config)
        
        # Generate agent_id if not provided
        agent_id = config.get('agent_id') or str(uuid.uuid4())
        
        # Build configuration item
        timestamp = int(datetime.utcnow().timestamp())
        config_item = {
            'tenant_id': tenant_id,
            'config_key': f'agent#{agent_id}',
            'config_type': 'agent',
            'agent_id': agent_id,
            'agent_name': config['agent_name'],
            'agent_type': config['agent_type'],
            'system_prompt': config['system_prompt'],
            'tools': config.get('tools', []),
            'output_schema': config['output_schema'],
            'dependency_parent': config.get('dependency_parent'),
            'interrogative': config.get('interrogative'),
            'is_builtin': config.get('is_builtin', False),
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id,
            'version': 1
        }
        
        # Save to DynamoDB
        self.table.put_item(Item=config_item)
        
        logger.info(f"Created agent config: {agent_id} for tenant {tenant_id}")
        
        return config_item
    
    def get(self, tenant_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent configuration"""
        response = self.table.get_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'agent#{agent_id}'
            }
        )
        
        return response.get('Item')
    
    def list(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all agent configurations for a tenant"""
        response = self.table.query(
            KeyConditionExpression='tenant_id = :tenant_id AND begins_with(config_key, :prefix)',
            ExpressionAttributeValues={
                ':tenant_id': tenant_id,
                ':prefix': 'agent#'
            }
        )
        
        return response.get('Items', [])
    
    def update(self, tenant_id: str, user_id: str, agent_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing agent configuration"""
        # Get existing config
        existing = self.get(tenant_id, agent_id)
        if not existing:
            return None
        
        # Validate new config
        self._validate_agent_config(config)
        
        # Backup old version to S3
        self._backup_to_s3(tenant_id, agent_id, existing)
        
        # Update configuration
        timestamp = int(datetime.utcnow().timestamp())
        new_version = existing.get('version', 1) + 1
        
        updated_item = {
            'tenant_id': tenant_id,
            'config_key': f'agent#{agent_id}',
            'config_type': 'agent',
            'agent_id': agent_id,
            'agent_name': config['agent_name'],
            'agent_type': config['agent_type'],
            'system_prompt': config['system_prompt'],
            'tools': config.get('tools', []),
            'output_schema': config['output_schema'],
            'dependency_parent': config.get('dependency_parent'),
            'interrogative': config.get('interrogative'),
            'is_builtin': existing.get('is_builtin', False),
            'created_at': existing['created_at'],
            'updated_at': timestamp,
            'created_by': existing['created_by'],
            'updated_by': user_id,
            'version': new_version
        }
        
        self.table.put_item(Item=updated_item)
        
        logger.info(f"Updated agent config: {agent_id} to version {new_version}")
        
        return updated_item
    
    def delete(self, tenant_id: str, agent_id: str) -> bool:
        """Delete an agent configuration"""
        # Get existing config for backup
        existing = self.get(tenant_id, agent_id)
        if not existing:
            return False
        
        # Backup before deletion
        self._backup_to_s3(tenant_id, agent_id, existing, deleted=True)
        
        # Delete from DynamoDB
        self.table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'agent#{agent_id}'
            }
        )
        
        logger.info(f"Deleted agent config: {agent_id}")
        
        return True
    
    def _validate_agent_config(self, config: Dict[str, Any]) -> None:
        """Validate agent configuration"""
        # Required fields
        required_fields = ['agent_name', 'agent_type', 'system_prompt', 'output_schema']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate agent_type
        valid_types = ['ingestion', 'query', 'custom']
        if config['agent_type'] not in valid_types:
            raise ValueError(f"Invalid agent_type: {config['agent_type']}. Must be one of {valid_types}")
        
        # Validate output_schema (max 5 keys)
        output_schema = config['output_schema']
        if not isinstance(output_schema, dict):
            raise ValueError("output_schema must be a dictionary")
        
        if len(output_schema) > 5:
            raise ValueError(f"output_schema cannot have more than 5 keys. Found {len(output_schema)} keys")
        
        # Validate system_prompt
        if not isinstance(config['system_prompt'], str) or len(config['system_prompt']) < 10:
            raise ValueError("system_prompt must be a string with at least 10 characters")
        
        # Validate tools (if provided)
        if 'tools' in config:
            if not isinstance(config['tools'], list):
                raise ValueError("tools must be a list")
        
        # Validate single-level dependency
        if 'dependency_parent' in config and config['dependency_parent']:
            if not isinstance(config['dependency_parent'], str):
                raise ValueError("dependency_parent must be a string (agent_id)")
        
        # Validate interrogative for query agents
        if config['agent_type'] == 'query':
            valid_interrogatives = [
                'when', 'where', 'why', 'how', 'what', 'who', 'which',
                'how_many', 'how_much', 'from_where', 'what_kind'
            ]
            interrogative = config.get('interrogative')
            if interrogative and interrogative not in valid_interrogatives:
                raise ValueError(f"Invalid interrogative: {interrogative}. Must be one of {valid_interrogatives}")
    
    def _backup_to_s3(self, tenant_id: str, agent_id: str, config: Dict[str, Any], deleted: bool = False) -> None:
        """Backup configuration to S3"""
        try:
            version = config.get('version', 1)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Build S3 key
            status = 'deleted' if deleted else 'backup'
            s3_key = f"{tenant_id}/agents/{agent_id}_v{version}_{timestamp}_{status}.json"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.backup_bucket,
                Key=s3_key,
                Body=json.dumps(config, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Backed up agent config to S3: {s3_key}")
        
        except Exception as e:
            logger.error(f"Failed to backup to S3: {str(e)}")
            # Don't fail the operation if backup fails
