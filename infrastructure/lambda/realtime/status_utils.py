"""
Status Publishing Utilities

Helper functions for publishing status updates from orchestrator and agents.
"""

import json
import os
import boto3
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger()

# Initialize Lambda client for invoking status publisher
lambda_client = boto3.client('lambda')

# Environment variable for status publisher function
STATUS_PUBLISHER_FUNCTION = os.environ.get('STATUS_PUBLISHER_FUNCTION')


def publish_status(
    job_id: str,
    user_id: str,
    tenant_id: str,
    status: str,
    message: str,
    agent_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish a status update by invoking the status publisher Lambda.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        tenant_id: Tenant identifier
        status: Status string (loading_agents, invoking_agent, agent_complete, etc.)
        message: Human-readable status message
        agent_name: Optional agent name
        metadata: Optional additional metadata
        
    Returns:
        True if published successfully, False otherwise
    """
    if not STATUS_PUBLISHER_FUNCTION:
        logger.warning("STATUS_PUBLISHER_FUNCTION not configured, skipping status update")
        return False
    
    try:
        payload = {
            'job_id': job_id,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'status': status,
            'message': message,
            'agent_name': agent_name,
            'metadata': metadata or {}
        }
        
        logger.info(f"Publishing status: {status} - {message}")
        
        # Invoke status publisher asynchronously
        response = lambda_client.invoke(
            FunctionName=STATUS_PUBLISHER_FUNCTION,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        return response['StatusCode'] == 202  # Accepted
        
    except Exception as e:
        logger.error(f"Failed to publish status: {str(e)}")
        # Don't fail the main operation if status publishing fails
        return False


def publish_agent_status(
    job_id: str,
    user_id: str,
    tenant_id: str,
    agent_name: str,
    status: str,
    message: str,
    execution_time_ms: Optional[int] = None
) -> bool:
    """
    Publish agent-specific status update.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        tenant_id: Tenant identifier
        agent_name: Agent name
        status: Status (invoking, calling_tool, complete, error)
        message: Status message
        execution_time_ms: Optional execution time
        
    Returns:
        True if published successfully
    """
    metadata = {}
    if execution_time_ms is not None:
        metadata['execution_time_ms'] = execution_time_ms
    
    return publish_status(
        job_id=job_id,
        user_id=user_id,
        tenant_id=tenant_id,
        status=f"agent_{status}",
        message=f"{agent_name}: {message}",
        agent_name=agent_name,
        metadata=metadata
    )


def publish_tool_status(
    job_id: str,
    user_id: str,
    tenant_id: str,
    agent_name: str,
    tool_name: str,
    reason: str
) -> bool:
    """
    Publish tool invocation status.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        tenant_id: Tenant identifier
        agent_name: Agent name
        tool_name: Tool being invoked
        reason: Reason for tool invocation
        
    Returns:
        True if published successfully
    """
    return publish_status(
        job_id=job_id,
        user_id=user_id,
        tenant_id=tenant_id,
        status='calling_tool',
        message=f"{agent_name} is calling {tool_name}: {reason}",
        agent_name=agent_name,
        metadata={'tool_name': tool_name, 'reason': reason}
    )


def publish_orchestrator_status(
    job_id: str,
    user_id: str,
    tenant_id: str,
    status: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish orchestrator-level status update.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        tenant_id: Tenant identifier
        status: Status (loading_agents, validating, synthesizing, complete, error)
        message: Status message
        metadata: Optional metadata
        
    Returns:
        True if published successfully
    """
    return publish_status(
        job_id=job_id,
        user_id=user_id,
        tenant_id=tenant_id,
        status=status,
        message=message,
        metadata=metadata
    )
