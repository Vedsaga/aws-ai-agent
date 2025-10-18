"""
Dependency Graph Configuration Manager
Handles CRUD operations for dependency graph configurations with validation
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger()


class DependencyGraphManager:
    """Manages dependency graph configuration CRUD operations"""
    
    def __init__(self, dynamodb, s3, table_name: str, backup_bucket: str):
        self.dynamodb = dynamodb
        self.s3 = s3
        self.table = dynamodb.Table(table_name)
        self.backup_bucket = backup_bucket
    
    def create(self, tenant_id: str, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dependency graph configuration"""
        # Validate required fields
        self._validate_dependency_graph(config, tenant_id)
        
        # Generate graph_id if not provided
        graph_id = config.get('graph_id') or str(uuid.uuid4())
        
        # Generate execution levels via topological sort
        execution_levels = self._generate_execution_levels(config['edges'])
        
        # Build configuration item
        timestamp = int(datetime.utcnow().timestamp())
        config_item = {
            'tenant_id': tenant_id,
            'config_key': f'dependency_graph#{graph_id}',
            'config_type': 'dependency_graph',
            'graph_id': graph_id,
            'playbook_id': config['playbook_id'],
            'edges': config['edges'],
            'execution_levels': execution_levels,
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id,
            'version': 1
        }
        
        # Save to DynamoDB
        self.table.put_item(Item=config_item)
        
        logger.info(f"Created dependency graph: {graph_id} for tenant {tenant_id}")
        
        return config_item
    
    def get(self, tenant_id: str, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get a dependency graph configuration"""
        response = self.table.get_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'dependency_graph#{graph_id}'
            }
        )
        
        return response.get('Item')
    
    def list(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all dependency graph configurations for a tenant"""
        response = self.table.query(
            KeyConditionExpression='tenant_id = :tenant_id AND begins_with(config_key, :prefix)',
            ExpressionAttributeValues={
                ':tenant_id': tenant_id,
                ':prefix': 'dependency_graph#'
            }
        )
        
        return response.get('Items', [])
    
    def update(self, tenant_id: str, user_id: str, graph_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing dependency graph configuration"""
        # Get existing config
        existing = self.get(tenant_id, graph_id)
        if not existing:
            return None
        
        # Validate new config
        self._validate_dependency_graph(config, tenant_id)
        
        # Backup old version to S3
        self._backup_to_s3(tenant_id, graph_id, existing)
        
        # Generate execution levels
        execution_levels = self._generate_execution_levels(config['edges'])
        
        # Update configuration
        timestamp = int(datetime.utcnow().timestamp())
        new_version = existing.get('version', 1) + 1
        
        updated_item = {
            'tenant_id': tenant_id,
            'config_key': f'dependency_graph#{graph_id}',
            'config_type': 'dependency_graph',
            'graph_id': graph_id,
            'playbook_id': config['playbook_id'],
            'edges': config['edges'],
            'execution_levels': execution_levels,
            'created_at': existing['created_at'],
            'updated_at': timestamp,
            'created_by': existing['created_by'],
            'updated_by': user_id,
            'version': new_version
        }
        
        self.table.put_item(Item=updated_item)
        
        logger.info(f"Updated dependency graph: {graph_id} to version {new_version}")
        
        return updated_item
    
    def delete(self, tenant_id: str, graph_id: str) -> bool:
        """Delete a dependency graph configuration"""
        # Get existing config for backup
        existing = self.get(tenant_id, graph_id)
        if not existing:
            return False
        
        # Backup before deletion
        self._backup_to_s3(tenant_id, graph_id, existing, deleted=True)
        
        # Delete from DynamoDB
        self.table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'config_key': f'dependency_graph#{graph_id}'
            }
        )
        
        logger.info(f"Deleted dependency graph: {graph_id}")
        
        return True
    
    def _validate_dependency_graph(self, config: Dict[str, Any], tenant_id: str) -> None:
        """Validate dependency graph configuration"""
        # Required fields
        required_fields = ['playbook_id', 'edges']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate edges
        edges = config['edges']
        if not isinstance(edges, list):
            raise ValueError("edges must be a list")
        
        # Validate each edge
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("Each edge must be a dictionary")
            
            if 'from' not in edge or 'to' not in edge:
                raise ValueError("Each edge must have 'from' and 'to' fields")
        
        # Verify playbook exists
        if not self._playbook_exists(tenant_id, config['playbook_id']):
            raise ValueError(f"Playbook not found: {config['playbook_id']}")
        
        # Get playbook to verify agents
        playbook = self._get_playbook(tenant_id, config['playbook_id'])
        if not playbook:
            raise ValueError(f"Playbook not found: {config['playbook_id']}")
        
        playbook_agent_ids = set(playbook.get('agent_ids', []))
        
        # Verify all agents in edges exist in playbook
        for edge in edges:
            from_agent = edge['from']
            to_agent = edge['to']
            
            if from_agent not in playbook_agent_ids:
                raise ValueError(f"Agent '{from_agent}' not found in playbook")
            
            if to_agent not in playbook_agent_ids:
                raise ValueError(f"Agent '{to_agent}' not found in playbook")
        
        # Validate no circular dependencies
        if self._has_circular_dependency(edges):
            raise ValueError("Circular dependency detected")
        
        # Validate single-level dependencies (each agent has at most one parent)
        if not self._validate_single_level_dependencies(edges):
            raise ValueError("Multi-level dependencies detected. Each agent can only depend on one parent agent")
    
    def _playbook_exists(self, tenant_id: str, playbook_id: str) -> bool:
        """Check if a playbook exists"""
        try:
            response = self.table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'config_key': f'playbook#{playbook_id}'
                }
            )
            return 'Item' in response
        except Exception as e:
            logger.error(f"Error checking playbook existence: {str(e)}")
            return False
    
    def _get_playbook(self, tenant_id: str, playbook_id: str) -> Optional[Dict[str, Any]]:
        """Get playbook configuration"""
        try:
            response = self.table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'config_key': f'playbook#{playbook_id}'
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting playbook: {str(e)}")
            return None
    
    def _has_circular_dependency(self, edges: List[Dict[str, str]]) -> bool:
        """Check for circular dependencies using DFS"""
        # Build adjacency list
        graph = {}
        for edge in edges:
            from_node = edge['from']
            to_node = edge['to']
            
            if from_node not in graph:
                graph[from_node] = []
            graph[from_node].append(to_node)
        
        # Track visited nodes and recursion stack
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            # Check all neighbors
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check all nodes
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def _validate_single_level_dependencies(self, edges: List[Dict[str, str]]) -> bool:
        """Validate that each agent has at most one parent (single-level dependency)"""
        # Count incoming edges for each node
        incoming_count = {}
        
        for edge in edges:
            to_node = edge['to']
            incoming_count[to_node] = incoming_count.get(to_node, 0) + 1
        
        # Check if any node has more than one parent
        for node, count in incoming_count.items():
            if count > 1:
                logger.error(f"Agent '{node}' has {count} parents (multi-level dependency)")
                return False
        
        return True
    
    def _generate_execution_levels(self, edges: List[Dict[str, str]]) -> List[List[str]]:
        """Generate execution levels via topological sort"""
        # Build adjacency list and in-degree count
        graph = {}
        in_degree = {}
        all_nodes = set()
        
        for edge in edges:
            from_node = edge['from']
            to_node = edge['to']
            
            all_nodes.add(from_node)
            all_nodes.add(to_node)
            
            if from_node not in graph:
                graph[from_node] = []
            graph[from_node].append(to_node)
            
            in_degree[to_node] = in_degree.get(to_node, 0) + 1
            if from_node not in in_degree:
                in_degree[from_node] = 0
        
        # Initialize nodes with no dependencies
        for node in all_nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        # Topological sort by levels
        levels = []
        current_level = [node for node in all_nodes if in_degree[node] == 0]
        
        while current_level:
            levels.append(sorted(current_level))
            next_level = []
            
            for node in current_level:
                for neighbor in graph.get(node, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            
            current_level = next_level
        
        return levels
    
    def _backup_to_s3(self, tenant_id: str, graph_id: str, config: Dict[str, Any], deleted: bool = False) -> None:
        """Backup configuration to S3"""
        try:
            version = config.get('version', 1)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            # Build S3 key
            status = 'deleted' if deleted else 'backup'
            s3_key = f"{tenant_id}/dependency_graphs/{graph_id}_v{version}_{timestamp}_{status}.json"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.backup_bucket,
                Key=s3_key,
                Body=json.dumps(config, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Backed up dependency graph to S3: {s3_key}")
        
        except Exception as e:
            logger.error(f"Failed to backup to S3: {str(e)}")
            # Don't fail the operation if backup fails
