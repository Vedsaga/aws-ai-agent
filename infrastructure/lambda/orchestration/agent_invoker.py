"""
Agent Invoker Lambda Function

Routes execution to specific agents by ID, loads configuration from RDS PostgreSQL,
and handles agent timeouts and errors.

Requirements: 7.3, 7.4, 8.1, 8.4
"""

import json
import os
import sys
import boto3
import logging
from typing import Dict, Any, Optional

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_agent_status

# Import RDS utilities
from rds_utils import get_agent_by_id

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
AGENT_LAMBDA_PREFIX = os.environ.get('AGENT_LAMBDA_PREFIX', 'MultiAgentOrch-Agent-')


def load_agent_config(tenant_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Load agent configuration from RDS PostgreSQL.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
    
    Returns:
        Agent configuration dictionary
    
    Raises:
        ValueError: If agent config not found
    """
    try:
        # Get agent from RDS
        config = get_agent_by_id(tenant_id, agent_id)
        
        if not config:
            raise ValueError(f"Agent config not found: {agent_id} for tenant {tenant_id}")
        
        logger.info(f"Loaded config for agent {agent_id}: {config.get('agent_name')}")
        
        return config
        
    except Exception as e:
        logger.error(f"Error loading agent config: {str(e)}")
        raise ValueError(f"Failed to load agent config: {str(e)}")


def invoke_agent_lambda(
    agent_config: Dict[str, Any],
    job_id: str,
    tenant_id: str,
    raw_text: str,
    parent_output: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Invoke the appropriate Lambda function for the agent.
    
    Args:
        agent_config: Agent configuration
        job_id: Job identifier
        tenant_id: Tenant identifier
        raw_text: Raw input text
        parent_output: Optional parent agent output
    
    Returns:
        Agent execution result
    """
    agent_id = agent_config['agent_id']
    agent_name = agent_config.get('agent_name', agent_id)
    agent_class = agent_config.get('agent_class', 'custom')
    is_inbuilt = agent_config.get('is_inbuilt', False)
    
    # Determine Lambda function name based on agent class and builtin status
    if is_inbuilt and agent_class == 'ingestion':
        # Built-in ingestion agents (geo, temporal, entity)
        lambda_name = f"{AGENT_LAMBDA_PREFIX}{agent_name.replace(' ', '')}"
    elif is_inbuilt and agent_class == 'query':
        # Built-in query agents (interrogative-based)
        lambda_name = f"{AGENT_LAMBDA_PREFIX}Query-{agent_name.replace(' ', '')}"
    else:
        # Custom agents use generic custom agent Lambda
        lambda_name = f"{AGENT_LAMBDA_PREFIX}Custom"
    
    # Prepare event payload
    event_payload = {
        'job_id': job_id,
        'tenant_id': tenant_id,
        'raw_text': raw_text,
        'parent_output': parent_output,
        'agent_config': {
            'agent_name': agent_name,
            'system_prompt': agent_config.get('system_prompt', ''),
            'tools': agent_config.get('tools', []),
            'output_schema': agent_config.get('output_schema', {}),
            'interrogative': agent_config.get('interrogative')
        }
    }
    
    try:
        logger.info(f"Invoking Lambda {lambda_name} for agent {agent_name}")
        
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        # Check for Lambda errors
        if 'FunctionError' in response:
            logger.error(f"Lambda function error: {response_payload}")
            return {
                'agent_name': agent_name,
                'agent_id': agent_id,
                'output': {},
                'status': 'error',
                'execution_time_ms': 0,
                'error_message': f"Lambda invocation failed: {response_payload.get('errorMessage', 'Unknown error')}"
            }
        
        # Add agent_id to response
        response_payload['agent_id'] = agent_id
        
        logger.info(f"Agent {agent_name} completed with status: {response_payload.get('status')}")
        
        return response_payload
        
    except ClientError as e:
        logger.error(f"Failed to invoke Lambda {lambda_name}: {str(e)}")
        return {
            'agent_name': agent_name,
            'agent_id': agent_id,
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': f"Lambda invocation error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error invoking agent {agent_name}: {str(e)}")
        return {
            'agent_name': agent_name,
            'agent_id': agent_id,
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': f"Unexpected error: {str(e)}"
        }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for agent invocation.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "agent_id": "string",
        "raw_text": "string",
        "parent_output": {...}  // Optional
    }
    
    Returns:
        Standardized agent output format
    """
    try:
        # Extract inputs
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        user_id = event.get('user_id')
        agent_id = event.get('agent_id')
        raw_text = event.get('raw_text', '')
        parent_output = event.get('parent_output')
        
        # Validate required fields
        if not all([job_id, tenant_id, agent_id]):
            raise ValueError("Missing required fields: job_id, tenant_id, or agent_id")
        
        logger.info(f"Agent invoker starting for job {job_id}, agent {agent_id}")
        
        # Load agent configuration
        agent_config = load_agent_config(tenant_id, agent_id)
        agent_name = agent_config.get('agent_name', agent_id)
        
        # Publish status: invoking agent
        if user_id:
            publish_agent_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=agent_name,
                status='invoking',
                message=f"Starting execution"
            )
        
        # Invoke agent Lambda
        result = invoke_agent_lambda(
            agent_config=agent_config,
            job_id=job_id,
            tenant_id=tenant_id,
            raw_text=raw_text,
            parent_output=parent_output
        )
        
        # Publish status: agent complete
        if user_id and result.get('status') == 'success':
            publish_agent_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=agent_name,
                status='complete',
                message=f"Completed successfully",
                execution_time_ms=result.get('execution_time_ms', 0)
            )
        elif user_id and result.get('status') == 'error':
            publish_agent_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=agent_name,
                status='error',
                message=f"Failed: {result.get('error_message', 'Unknown error')}"
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'agent_name': event.get('agent_id', 'unknown'),
            'agent_id': event.get('agent_id', 'unknown'),
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in agent invoker: {str(e)}", exc_info=True)
        return {
            'agent_name': event.get('agent_id', 'unknown'),
            'agent_id': event.get('agent_id', 'unknown'),
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': f"Agent invoker error: {str(e)}"
        }
