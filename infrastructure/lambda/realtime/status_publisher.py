"""
Status Publisher Lambda Function

Accepts status messages from orchestrator and agents, looks up user connection_id,
and publishes to AppSync via GraphQL mutation.
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
appsync_client = boto3.client('appsync')

# Environment variables
USER_SESSIONS_TABLE = os.environ['USER_SESSIONS_TABLE']
APPSYNC_API_URL = os.environ['APPSYNC_API_URL']
APPSYNC_API_ID = os.environ['APPSYNC_API_ID']

# DynamoDB table
sessions_table = dynamodb.Table(USER_SESSIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for publishing status updates.
    
    Expected event format:
    {
        "job_id": "string",
        "user_id": "string",
        "tenant_id": "string",
        "agent_name": "string" (optional),
        "status": "string",
        "message": "string",
        "metadata": {} (optional)
    }
    """
    try:
        logger.info(f"Received status update: {json.dumps(event)}")
        
        # Extract required fields
        job_id = event.get('job_id')
        user_id = event.get('user_id')
        tenant_id = event.get('tenant_id')
        agent_name = event.get('agent_name')
        status = event.get('status')
        message = event.get('message')
        metadata = event.get('metadata', {})
        
        # Validate required fields
        if not all([job_id, user_id, status, message]):
            raise ValueError("Missing required fields: job_id, user_id, status, message")
        
        # Look up user session to get connection_id
        connection_id = get_user_connection(user_id, tenant_id)
        
        if not connection_id:
            logger.warning(f"No active connection found for user {user_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No active connection',
                    'user_id': user_id
                })
            }
        
        # Publish to AppSync
        publish_result = publish_to_appsync(
            job_id=job_id,
            user_id=user_id,
            agent_name=agent_name,
            status=status,
            message=message,
            metadata=metadata
        )
        
        logger.info(f"Successfully published status update for job {job_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Status published successfully',
                'job_id': job_id,
                'user_id': user_id,
                'status': status
            })
        }
        
    except Exception as e:
        logger.error(f"Error publishing status: {str(e)}", exc_info=True)
        
        # Handle gracefully - don't fail the orchestration
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to publish status',
                'message': str(e)
            })
        }


def get_user_connection(user_id: str, tenant_id: str) -> Optional[str]:
    """
    Look up user's active connection_id from DynamoDB.
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        
    Returns:
        connection_id if found, None otherwise
    """
    try:
        # Query for active sessions
        response = sessions_table.query(
            KeyConditionExpression='user_id = :uid',
            FilterExpression='tenant_id = :tid AND attribute_exists(connection_id)',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':tid': tenant_id
            },
            ScanIndexForward=False,  # Get most recent first
            Limit=1
        )
        
        items = response.get('Items', [])
        
        if items:
            connection_id = items[0].get('connection_id')
            logger.info(f"Found connection_id {connection_id} for user {user_id}")
            return connection_id
        
        return None
        
    except Exception as e:
        logger.error(f"Error looking up connection: {str(e)}")
        return None


def publish_to_appsync(
    job_id: str,
    user_id: str,
    agent_name: Optional[str],
    status: str,
    message: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Publish status update to AppSync GraphQL API.
    
    Args:
        job_id: Job identifier
        user_id: User identifier
        agent_name: Agent name (optional)
        status: Status string
        message: Status message
        metadata: Additional metadata
        
    Returns:
        AppSync response
    """
    # Build GraphQL mutation
    mutation = """
    mutation PublishStatus(
        $jobId: ID!,
        $userId: ID!,
        $agentName: String,
        $status: String!,
        $message: String!,
        $metadata: AWSJSON
    ) {
        publishStatus(
            jobId: $jobId,
            userId: $userId,
            agentName: $agentName,
            status: $status,
            message: $message,
            metadata: $metadata
        ) {
            jobId
            userId
            agentName
            status
            message
            timestamp
        }
    }
    """
    
    variables = {
        'jobId': job_id,
        'userId': user_id,
        'agentName': agent_name,
        'status': status,
        'message': message,
        'metadata': json.dumps(metadata) if metadata else None
    }
    
    try:
        # Use AWS SDK to execute GraphQL mutation
        # Note: This requires IAM authentication
        import requests
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
        }
        
        body = json.dumps({
            'query': mutation,
            'variables': variables
        })
        
        # Create AWS request for signing
        request = AWSRequest(
            method='POST',
            url=APPSYNC_API_URL,
            data=body,
            headers=headers
        )
        
        # Sign request with SigV4
        SigV4Auth(
            boto3.Session().get_credentials(),
            'appsync',
            os.environ['AWS_REGION']
        ).add_auth(request)
        
        # Execute request
        response = requests.post(
            APPSYNC_API_URL,
            headers=dict(request.headers),
            data=body,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'errors' in result:
            logger.error(f"GraphQL errors: {result['errors']}")
            raise Exception(f"GraphQL mutation failed: {result['errors']}")
        
        return result.get('data', {}).get('publishStatus', {})
        
    except Exception as e:
        logger.error(f"Error publishing to AppSync: {str(e)}")
        raise
