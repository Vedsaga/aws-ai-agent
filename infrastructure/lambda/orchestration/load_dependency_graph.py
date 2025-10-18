"""
Load Dependency Graph Lambda Function

Loads dependency graph configuration from DynamoDB for the playbook.

Requirements: 7.2
"""

import json
import os
import boto3
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
DEPENDENCY_GRAPHS_TABLE = os.environ.get('DEPENDENCY_GRAPHS_TABLE', 'dependency_graphs')


def load_dependency_graph(tenant_id: str, playbook_id: str) -> Dict[str, Any]:
    """
    Load dependency graph configuration from DynamoDB.
    
    Args:
        tenant_id: Tenant identifier
        playbook_id: Playbook identifier
    
    Returns:
        Dependency graph configuration
    """
    try:
        table = dynamodb.Table(DEPENDENCY_GRAPHS_TABLE)
        
        # Query for dependency graph by tenant_id and playbook_id
        response = table.query(
            KeyConditionExpression='tenant_id = :tid',
            FilterExpression='playbook_id = :pid',
            ExpressionAttributeValues={
                ':tid': tenant_id,
                ':pid': playbook_id
            }
        )
        
        items = response.get('Items', [])
        
        if not items:
            # No dependency graph found - return empty graph (all agents run in parallel)
            logger.info(f"No dependency graph found for playbook '{playbook_id}', using parallel execution")
            return {
                'graph_id': f"{playbook_id}_default",
                'playbook_id': playbook_id,
                'edges': []
            }
        
        # Use the first matching graph
        graph = items[0]
        
        edges = graph.get('edges', [])
        logger.info(f"Loaded dependency graph with {len(edges)} edges")
        
        return graph
        
    except ClientError as e:
        logger.error(f"DynamoDB error loading dependency graph: {str(e)}")
        # Return empty graph on error
        return {
            'graph_id': f"{playbook_id}_error",
            'playbook_id': playbook_id,
            'edges': []
        }


def validate_single_level_dependencies(edges: List[Dict[str, Any]]) -> List[str]:
    """
    Validate that dependencies are single-level only (no multi-level chains).
    
    Args:
        edges: List of dependency edges [{"from": "agent_id", "to": "agent_id"}]
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Build dependency map: child -> parent
    dependencies = {}
    for edge in edges:
        from_agent = edge.get('from')
        to_agent = edge.get('to')
        
        if to_agent in dependencies:
            errors.append(
                f"Agent '{to_agent}' has multiple parents: "
                f"'{dependencies[to_agent]}' and '{from_agent}'"
            )
        else:
            dependencies[to_agent] = from_agent
    
    # Check for multi-level chains: if a parent is also a child
    for child, parent in dependencies.items():
        if parent in dependencies:
            errors.append(
                f"Multi-level dependency detected: '{child}' depends on '{parent}', "
                f"which depends on '{dependencies[parent]}'"
            )
    
    return errors


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for loading dependency graph.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "playbook_id": "string",
        "agent_ids": ["agent1", "agent2", ...]
    }
    
    Returns:
        Dependency graph with edges
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        playbook_id = event.get('playbook_id')
        agent_ids = event.get('agent_ids', [])
        
        logger.info(f"Loading dependency graph for playbook {playbook_id}")
        
        # Load dependency graph
        graph = load_dependency_graph(tenant_id, playbook_id)
        
        edges = graph.get('edges', [])
        
        # Validate single-level dependencies
        validation_errors = validate_single_level_dependencies(edges)
        
        if validation_errors:
            logger.error(f"Dependency validation failed: {validation_errors}")
            return {
                'job_id': job_id,
                'tenant_id': tenant_id,
                'playbook_id': playbook_id,
                'graph_id': graph.get('graph_id'),
                'edges': [],
                'status': 'error',
                'error_message': f"Invalid dependencies: {'; '.join(validation_errors)}"
            }
        
        # Filter edges to only include agents in the playbook
        filtered_edges = [
            edge for edge in edges
            if edge.get('from') in agent_ids and edge.get('to') in agent_ids
        ]
        
        if len(filtered_edges) < len(edges):
            logger.warning(
                f"Filtered {len(edges) - len(filtered_edges)} edges with agents "
                f"not in playbook"
            )
        
        logger.info(f"Loaded dependency graph with {len(filtered_edges)} valid edges")
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'playbook_id': playbook_id,
            'graph_id': graph.get('graph_id'),
            'edges': filtered_edges,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error loading dependency graph: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'playbook_id': event.get('playbook_id', 'unknown'),
            'edges': [],
            'status': 'error',
            'error_message': f"Dependency graph error: {str(e)}"
        }
