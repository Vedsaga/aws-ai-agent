"""
Load Playbook Lambda Function

Loads playbook configuration from RDS PostgreSQL based on domain_id and playbook_type.

Requirements: 2.2, 7.1, 8.1, 8.4
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_orchestrator_status

# Import RDS utilities
from rds_utils import get_playbook

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_playbook(tenant_id: str, domain_id: str, playbook_type: str) -> Dict[str, Any]:
    """
    Load playbook configuration from RDS PostgreSQL.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        playbook_type: Type of playbook ('ingestion', 'query', or 'management')
    
    Returns:
        Playbook configuration with agent_execution_graph
    
    Raises:
        ValueError: If playbook not found
    """
    try:
        # Get playbook from RDS
        playbook = get_playbook(tenant_id, domain_id, playbook_type)
        
        if not playbook:
            raise ValueError(
                f"Playbook not found for domain '{domain_id}', type '{playbook_type}'"
            )
        
        # Extract agent IDs from execution graph
        agent_execution_graph = playbook.get('agent_execution_graph', {})
        agent_ids = agent_execution_graph.get('nodes', [])
        
        logger.info(
            f"Loaded {playbook_type} playbook for domain '{domain_id}' with "
            f"{len(agent_ids)} agents"
        )
        
        return playbook
        
    except Exception as e:
        logger.error(f"Error loading playbook: {str(e)}")
        raise ValueError(f"Failed to load playbook: {str(e)}")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for loading playbook.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "domain_id": "string",
        "playbook_type": "ingestion|query"
    }
    
    Returns:
        Playbook configuration with agent list
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        domain_id = event.get('domain_id')
        user_id = event.get('user_id')
        playbook_type = event.get('playbook_type', 'ingestion')
        
        # Validate required fields
        if not all([job_id, tenant_id, domain_id]):
            raise ValueError("Missing required fields: job_id, tenant_id, or domain_id")
        
        logger.info(
            f"Loading playbook for job {job_id}, domain {domain_id}, type {playbook_type}"
        )
        
        # Publish status: loading agents
        if user_id:
            publish_orchestrator_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                status='loading_agents',
                message=f"Loading {playbook_type} playbook for domain {domain_id}"
            )
        
        # Load playbook
        playbook = load_playbook(tenant_id, domain_id, playbook_type)
        
        # Extract agent execution graph
        agent_execution_graph = playbook.get('agent_execution_graph', {})
        agent_ids = agent_execution_graph.get('nodes', [])
        edges = agent_execution_graph.get('edges', [])
        
        if not agent_ids:
            logger.warning(f"Playbook has no agents configured")
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'domain_id': domain_id,
            'playbook_type': playbook_type,
            'agent_execution_graph': agent_execution_graph,
            'agent_ids': agent_ids,
            'status': 'success'
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'domain_id': event.get('domain_id', 'unknown'),
            'playbook_type': event.get('playbook_type', 'unknown'),
            'agent_ids': [],
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error loading playbook: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'domain_id': event.get('domain_id', 'unknown'),
            'playbook_type': event.get('playbook_type', 'unknown'),
            'agent_ids': [],
            'status': 'error',
            'error_message': f"Playbook loading error: {str(e)}"
        }
