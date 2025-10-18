"""
Load Playbook Lambda Function

Loads playbook configuration from DynamoDB based on domain_id and playbook_type.

Requirements: 2.2, 7.1
"""

import json
import os
import sys
import boto3
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_orchestrator_status

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
PLAYBOOK_CONFIGS_TABLE = os.environ.get('PLAYBOOK_CONFIGS_TABLE', 'playbook_configs')


def load_playbook(tenant_id: str, domain_id: str, playbook_type: str) -> Dict[str, Any]:
    """
    Load playbook configuration from DynamoDB.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        playbook_type: Type of playbook ('ingestion' or 'query')
    
    Returns:
        Playbook configuration
    
    Raises:
        ValueError: If playbook not found
    """
    try:
        table = dynamodb.Table(PLAYBOOK_CONFIGS_TABLE)
        
        # Query for playbook by tenant_id and domain_id
        response = table.query(
            KeyConditionExpression='tenant_id = :tid AND begins_with(playbook_id, :did)',
            FilterExpression='domain_id = :did AND playbook_type = :ptype',
            ExpressionAttributeValues={
                ':tid': tenant_id,
                ':did': domain_id,
                ':ptype': playbook_type
            }
        )
        
        items = response.get('Items', [])
        
        if not items:
            raise ValueError(
                f"Playbook not found for domain '{domain_id}', type '{playbook_type}'"
            )
        
        # Use the first matching playbook
        playbook = items[0]
        
        logger.info(
            f"Loaded playbook '{playbook.get('playbook_id')}' with "
            f"{len(playbook.get('agent_ids', []))} agents"
        )
        
        return playbook
        
    except ClientError as e:
        logger.error(f"DynamoDB error loading playbook: {str(e)}")
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
        
        # Extract agent IDs
        agent_ids = playbook.get('agent_ids', [])
        
        if not agent_ids:
            logger.warning(f"Playbook has no agents configured")
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'domain_id': domain_id,
            'playbook_type': playbook_type,
            'playbook_id': playbook.get('playbook_id'),
            'agent_ids': agent_ids,
            'description': playbook.get('description', ''),
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
