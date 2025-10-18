"""
Playbook Configuration Manager
Handles CRUD operations for playbook configurations with validation
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger()


class PlaybookConfigManager:
    """Manages playbook configuration CRUD operations"""
    
    def __init__(self, dynamodb, s3, table_name: str, backup_bucket: str):
        self.dynamodb = dynamodb
        self.s3 = s3
        self.table = dynamodb.Table(table_name)
        self.backup_bucket = backup_bucket
    
    def create(self, tenant_id: str, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new playbook configuration"""
        # Validate required fields
        self._validate_playbook_config(config, tenant_id)
        
        # Generate playbook_id if not provided
        playbook_id = config.get('playbook_id') or str(uuid.uuid4())
        
        # Build configuration item
        timestamp = int(datetime.utcnow().timestamp())
        config_item = {
            'tenant_id': tenant_id,
            'config_key': f'playbook#{playbook_id}',
            'config_type': 'playbook',
            'playbook_id': playbook_id,
            'domain_id': config['domain_id'],
            'playbook_type': config['playbook_type'],
            'agent_ids': config['agent_ids'],
            'description': config.get('description', ''),
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id,
            'version': 1
        }
        
        # Save to DynamoDB
        self.table.put_item(Item=config_item)
        
        logger.info(f"Created playbook config: {playbook_id} for tenant {tenant_id}")
        
        return config_item
    
    def get(self, tenant_id: str, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get a playbook configuration"""
        response = self.table.get_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'playbook#{playbook_id}'
            }
        )
        
        return response.get('Item')
    
    def list(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all playbook configurations for a tenant"""
        response = self.table.query(
            KeyConditionExpression='tenant_id = :tenant_id AND begins_with(config_key, :prefix)',
            ExpressionAttributeValues={
                ':tenant_id': tenant_id,
                ':prefix': 'playbook#'
            }
        )
        
        return response.get('Items', [])
    
    def update(self, tenant_id: str, user_id: str, playbook_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing playbook configuration"""
        # Get existing config
        existing = self.get(tenant_id, playbook_id)
        if not existing:
            return None
        
        # Validate new config
        self._validate_playbook_config(config, tenant_id)
        
        # Backup old version to S3
        self._backup_to_s3(tenant_id, playbook_id, existing)
        
        # Update configuration
        timestamp = int(datetime.utcnow().timestamp())
        new_version = existing.get('version', 1) + 1
        
        updated_item = {
            'tenant_id': tenant_id,
            'config_key': f'playbook#{playbook_id}',
            'config_type': 'playbook',
            'playbook_id': playbook_id,
            'domain_id': config['domain_id'],
            'playbook_type': config['playbook_type'],
            'agent_ids': config['agent_ids'],
            'description': config.get('description', ''),
            'created_at': existing['created_at'],
            'updated_at': timestamp,
            'created_by': existing['created_by'],
            'updated_by': user_id,
            'version': new_version
        }
        
        self.table.put_item(Item=updated_item)
        
        logger.info(f"Updated playbook config: {playbook_id} to version {new_version}")
        
        return updated_item
    
    def delete(self, tenant_id: str, playbook_id: str) -> bool:
        """Delete a playbook configuration"""
        # Get existing config for backup
        existing = self.get(tenant_id, playbook_id)
        if not existing:
            return False
        
        # Backup before deletion
        self._backup_to_s3(tenant_id, playbook_id, existing, deleted=True)
        
        # Delete from DynamoDB
        self.table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'playbook#{playbook_id}'
            }
        )
        
        logger.info(f"Deleted playbook config: {playbook_id}")
        
        return True
    
    def _validate_playbook_config(self, config: Dict[str, Any], tenant_id: str) -> None:
        """Validate playbook configuration"""
        # Required fields
        required_fields = ['domain_id', 'playbook_type', 'agent_ids']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate playbook_type
        valid_types = ['ingestion', 'query']
        if config['playbook_type'] not in valid_types:
            raise ValueError(f"Invalid playbook_type: {config['playbook_type']}. Must be one of {valid_types}")
        
        # Validate agent_ids
        agent_ids = config['agent_ids']
        if not isinstance(agent_ids, list):
            raise ValueError("agent_ids must be a list")
        
        if len(agent_ids) == 0:
            raise ValueError("agent_ids cannot be empty")
        
        # Verify all agents exist
        for agent_id in agent_ids:
            if not self._agent_exists(tenant_id, agent_id):
                raise ValueError(f"Agent not found: {agent_id}")
        
        # Validate domain_id
        if not isinstance(config['domain_id'], str) or len(config['domain_id']) == 0:
            raise ValueError("domain_id must be a non-empty string")
    
    def _agent_exists(self, tenant_id: str, agent_id: str) -> bool:
        """Check if an agent exists"""
        try:
            response = self.table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'config_key': f'agent#{agent_id}'
                }
            )
            return 'Item' in response
        except Exception as e:
            logger.error(f"Error checking agent existence: {str(e)}")
            return False
    
    def _backup_to_s3(self, tenant_id: str, playbook_id: str, config: Dict[str, Any], deleted: bool = False) -> None:
        """Backup configuration to S3"""
        try:
            version = config.get('version', 1)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Build S3 key
            status = 'deleted' if deleted else 'backup'
            s3_key = f"{tenant_id}/playbooks/{playbook_id}_v{version}_{timestamp}_{status}.json"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.backup_bucket,
                Key=s3_key,
                Body=json.dumps(config, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Backed up playbook config to S3: {s3_key}")
        
        except Exception as e:
            logger.error(f"Failed to backup to S3: {str(e)}")
            # Don't fail the operation if backup fails
