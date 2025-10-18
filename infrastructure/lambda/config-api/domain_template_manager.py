"""
Domain Template Manager
Handles CRUD operations for domain templates with pre-built configurations
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger()


class DomainTemplateManager:
    """Manages domain template CRUD operations"""
    
    def __init__(self, dynamodb, s3, table_name: str, backup_bucket: str):
        self.dynamodb = dynamodb
        self.s3 = s3
        self.table = dynamodb.Table(table_name)
        self.backup_bucket = backup_bucket
    
    def create(self, tenant_id: str, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new domain template"""
        # Validate required fields
        self._validate_template_config(config)
        
        # Generate template_id if not provided
        template_id = config.get('template_id') or str(uuid.uuid4())
        
        # Build configuration item
        timestamp = int(datetime.utcnow().timestamp())
        config_item = {
            'tenant_id': tenant_id,
            'config_key': f'domain_template#{template_id}',
            'config_type': 'domain_template',
            'template_id': template_id,
            'template_name': config['template_name'],
            'domain_id': config['domain_id'],
            'description': config.get('description', ''),
            'agent_configs': config['agent_configs'],
            'playbook_configs': config['playbook_configs'],
            'dependency_graph_configs': config.get('dependency_graph_configs', []),
            'ui_template': config.get('ui_template', {}),
            'is_builtin': config.get('is_builtin', False),
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id,
            'version': 1
        }
        
        # Save to DynamoDB
        self.table.put_item(Item=config_item)
        
        logger.info(f"Created domain template: {template_id} for tenant {tenant_id}")
        
        return config_item
    
    def get(self, tenant_id: str, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a domain template"""
        response = self.table.get_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'domain_template#{template_id}'
            }
        )
        
        return response.get('Item')
    
    def list(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all domain templates for a tenant"""
        response = self.table.query(
            KeyConditionExpression='tenant_id = :tenant_id AND begins_with(config_key, :prefix)',
            ExpressionAttributeValues={
                ':tenant_id': tenant_id,
                ':prefix': 'domain_template#'
            }
        )
        
        return response.get('Items', [])
    
    def update(self, tenant_id: str, user_id: str, template_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing domain template"""
        # Get existing config
        existing = self.get(tenant_id, template_id)
        if not existing:
            return None
        
        # Validate new config
        self._validate_template_config(config)
        
        # Backup old version to S3
        self._backup_to_s3(tenant_id, template_id, existing)
        
        # Update configuration
        timestamp = int(datetime.utcnow().timestamp())
        new_version = existing.get('version', 1) + 1
        
        updated_item = {
            'tenant_id': tenant_id,
            'config_key': f'domain_template#{template_id}',
            'config_type': 'domain_template',
            'template_id': template_id,
            'template_name': config['template_name'],
            'domain_id': config['domain_id'],
            'description': config.get('description', ''),
            'agent_configs': config['agent_configs'],
            'playbook_configs': config['playbook_configs'],
            'dependency_graph_configs': config.get('dependency_graph_configs', []),
            'ui_template': config.get('ui_template', {}),
            'is_builtin': existing.get('is_builtin', False),
            'created_at': existing['created_at'],
            'updated_at': timestamp,
            'created_by': existing['created_by'],
            'updated_by': user_id,
            'version': new_version
        }
        
        self.table.put_item(Item=updated_item)
        
        logger.info(f"Updated domain template: {template_id} to version {new_version}")
        
        return updated_item
    
    def delete(self, tenant_id: str, template_id: str) -> bool:
        """Delete a domain template"""
        # Get existing config for backup
        existing = self.get(tenant_id, template_id)
        if not existing:
            return False
        
        # Backup before deletion
        self._backup_to_s3(tenant_id, template_id, existing, deleted=True)
        
        # Delete from DynamoDB
        self.table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'domain_template#{template_id}'
            }
        )
        
        logger.info(f"Deleted domain template: {template_id}")
        
        return True
    
    def instantiate_template(self, tenant_id: str, user_id: str, template_id: str) -> Dict[str, Any]:
        """Instantiate a domain template for a tenant"""
        # Get template
        template = self.get(tenant_id, template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Create agents from template
        created_agents = []
        agent_id_mapping = {}  # Map template agent IDs to new agent IDs
        
        for agent_config in template['agent_configs']:
            # Generate new agent_id
            new_agent_id = str(uuid.uuid4())
            old_agent_id = agent_config.get('agent_id', '')
            agent_id_mapping[old_agent_id] = new_agent_id
            
            # Create agent
            agent_item = {
                'tenant_id': tenant_id,
                'config_key': f'agent#{new_agent_id}',
                'config_type': 'agent',
                'agent_id': new_agent_id,
                'agent_name': agent_config['agent_name'],
                'agent_type': agent_config['agent_type'],
                'system_prompt': agent_config['system_prompt'],
                'tools': agent_config.get('tools', []),
                'output_schema': agent_config['output_schema'],
                'dependency_parent': agent_config.get('dependency_parent'),
                'interrogative': agent_config.get('interrogative'),
                'is_builtin': False,
                'created_at': int(datetime.utcnow().timestamp()),
                'updated_at': int(datetime.utcnow().timestamp()),
                'created_by': user_id,
                'version': 1
            }
            
            self.table.put_item(Item=agent_item)
            created_agents.append(new_agent_id)
        
        # Create playbooks from template
        created_playbooks = []
        
        for playbook_config in template['playbook_configs']:
            # Generate new playbook_id
            new_playbook_id = str(uuid.uuid4())
            
            # Map old agent IDs to new agent IDs
            new_agent_ids = [agent_id_mapping.get(old_id, old_id) for old_id in playbook_config['agent_ids']]
            
            # Create playbook
            playbook_item = {
                'tenant_id': tenant_id,
                'config_key': f'playbook#{new_playbook_id}',
                'config_type': 'playbook',
                'playbook_id': new_playbook_id,
                'domain_id': template['domain_id'],
                'playbook_type': playbook_config['playbook_type'],
                'agent_ids': new_agent_ids,
                'description': playbook_config.get('description', ''),
                'created_at': int(datetime.utcnow().timestamp()),
                'updated_at': int(datetime.utcnow().timestamp()),
                'created_by': user_id,
                'version': 1
            }
            
            self.table.put_item(Item=playbook_item)
            created_playbooks.append(new_playbook_id)
        
        # Create dependency graphs from template
        created_graphs = []
        
        for graph_config in template.get('dependency_graph_configs', []):
            # Generate new graph_id
            new_graph_id = str(uuid.uuid4())
            
            # Map old agent IDs to new agent IDs in edges
            new_edges = []
            for edge in graph_config['edges']:
                new_edge = {
                    'from': agent_id_mapping.get(edge['from'], edge['from']),
                    'to': agent_id_mapping.get(edge['to'], edge['to'])
                }
                new_edges.append(new_edge)
            
            # Create dependency graph
            graph_item = {
                'tenant_id': tenant_id,
                'config_key': f'dependency_graph#{new_graph_id}',
                'config_type': 'dependency_graph',
                'graph_id': new_graph_id,
                'playbook_id': created_playbooks[0] if created_playbooks else '',
                'edges': new_edges,
                'execution_levels': graph_config.get('execution_levels', []),
                'created_at': int(datetime.utcnow().timestamp()),
                'updated_at': int(datetime.utcnow().timestamp()),
                'created_by': user_id,
                'version': 1
            }
            
            self.table.put_item(Item=graph_item)
            created_graphs.append(new_graph_id)
        
        logger.info(f"Instantiated template {template_id} for tenant {tenant_id}")
        
        return {
            'template_id': template_id,
            'domain_id': template['domain_id'],
            'created_agents': created_agents,
            'created_playbooks': created_playbooks,
            'created_graphs': created_graphs
        }
    
    def _validate_template_config(self, config: Dict[str, Any]) -> None:
        """Validate domain template configuration"""
        # Required fields
        required_fields = ['template_name', 'domain_id', 'agent_configs', 'playbook_configs']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate template_name
        if not isinstance(config['template_name'], str) or len(config['template_name']) == 0:
            raise ValueError("template_name must be a non-empty string")
        
        # Validate domain_id
        if not isinstance(config['domain_id'], str) or len(config['domain_id']) == 0:
            raise ValueError("domain_id must be a non-empty string")
        
        # Validate agent_configs
        if not isinstance(config['agent_configs'], list) or len(config['agent_configs']) == 0:
            raise ValueError("agent_configs must be a non-empty list")
        
        # Validate playbook_configs
        if not isinstance(config['playbook_configs'], list) or len(config['playbook_configs']) == 0:
            raise ValueError("playbook_configs must be a non-empty list")
    
    def _backup_to_s3(self, tenant_id: str, template_id: str, config: Dict[str, Any], deleted: bool = False) -> None:
        """Backup configuration to S3"""
        try:
            version = config.get('version', 1)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Build S3 key
            status = 'deleted' if deleted else 'backup'
            s3_key = f"{tenant_id}/domain_templates/{template_id}_v{version}_{timestamp}_{status}.json"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.backup_bucket,
                Key=s3_key,
                Body=json.dumps(config, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Backed up domain template to S3: {s3_key}")
        
        except Exception as e:
            logger.error(f"Failed to backup to S3: {str(e)}")
            # Don't fail the operation if backup fails
    
    @staticmethod
    def get_builtin_templates() -> List[Dict[str, Any]]:
        """Get pre-built domain templates"""
        return [
            {
                'template_name': 'Civic Complaints',
                'domain_id': 'civic_complaints',
                'description': 'Template for civic complaint reporting and analysis',
                'agent_configs': [
                    {
                        'agent_name': 'Geo Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract location information from the complaint text. Use Amazon Location Service for geocoding.',
                        'tools': ['bedrock', 'location_service', 'web_search'],
                        'output_schema': {
                            'location': 'string',
                            'coordinates': 'array',
                            'address': 'string',
                            'confidence': 'number'
                        }
                    },
                    {
                        'agent_name': 'Temporal Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract time and date information from the complaint text.',
                        'tools': ['bedrock'],
                        'output_schema': {
                            'timestamp': 'string',
                            'time_reference': 'string',
                            'urgency': 'string'
                        }
                    },
                    {
                        'agent_name': 'Entity Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract entities, sentiment, and key phrases from the complaint.',
                        'tools': ['bedrock', 'comprehend'],
                        'output_schema': {
                            'entities': 'array',
                            'sentiment': 'string',
                            'key_phrases': 'array',
                            'category': 'string'
                        }
                    }
                ],
                'playbook_configs': [
                    {
                        'playbook_type': 'ingestion',
                        'agent_ids': ['geo_agent', 'temporal_agent', 'entity_agent'],
                        'description': 'Ingestion pipeline for civic complaints'
                    }
                ],
                'is_builtin': True
            },
            {
                'template_name': 'Disaster Response',
                'domain_id': 'disaster_response',
                'description': 'Template for disaster reporting and emergency response',
                'agent_configs': [
                    {
                        'agent_name': 'Geo Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract precise location information from disaster reports.',
                        'tools': ['bedrock', 'location_service'],
                        'output_schema': {
                            'location': 'string',
                            'coordinates': 'array',
                            'affected_area': 'string'
                        }
                    },
                    {
                        'agent_name': 'Severity Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Assess the severity and urgency of the disaster report.',
                        'tools': ['bedrock'],
                        'output_schema': {
                            'severity': 'string',
                            'urgency_level': 'number',
                            'casualties': 'string',
                            'damage_type': 'string'
                        }
                    }
                ],
                'playbook_configs': [
                    {
                        'playbook_type': 'ingestion',
                        'agent_ids': ['geo_agent', 'severity_agent'],
                        'description': 'Ingestion pipeline for disaster reports'
                    }
                ],
                'is_builtin': True
            },
            {
                'template_name': 'Agriculture',
                'domain_id': 'agriculture',
                'description': 'Template for agricultural reporting and analysis',
                'agent_configs': [
                    {
                        'agent_name': 'Crop Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract crop type, condition, and issues from reports.',
                        'tools': ['bedrock'],
                        'output_schema': {
                            'crop_type': 'string',
                            'condition': 'string',
                            'issues': 'array',
                            'growth_stage': 'string'
                        }
                    },
                    {
                        'agent_name': 'Geo Agent',
                        'agent_type': 'ingestion',
                        'system_prompt': 'Extract farm location and field information.',
                        'tools': ['bedrock', 'location_service'],
                        'output_schema': {
                            'location': 'string',
                            'coordinates': 'array',
                            'field_size': 'string'
                        }
                    }
                ],
                'playbook_configs': [
                    {
                        'playbook_type': 'ingestion',
                        'agent_ids': ['crop_agent', 'geo_agent'],
                        'description': 'Ingestion pipeline for agricultural reports'
                    }
                ],
                'is_builtin': True
            }
        ]
