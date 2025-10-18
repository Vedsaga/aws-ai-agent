import json
import os
import boto3
from typing import Dict, Any
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USER_POOL_ID = os.environ['USER_POOL_ID']
USER_POOL_CLIENT_ID = os.environ['USER_POOL_CLIENT_ID']
REGION = os.environ.get('REGION', os.environ.get('AWS_REGION', 'us-east-1'))

# Cognito JWKS URL
JWKS_URL = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'

# Initialize JWKS client
jwks_client = PyJWKClient(JWKS_URL)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer for API Gateway.
    Validates JWT token from Cognito and extracts tenant_id.
    """
    try:
        # Extract token from Authorization header
        token = extract_token(event)
        
        if not token:
            logger.error("No token found in request")
            raise Exception('Unauthorized')
        
        # Verify and decode JWT token
        decoded_token = verify_token(token)
        
        # Extract user information
        user_id = decoded_token.get('sub')
        tenant_id = decoded_token.get('custom:tenant_id', 'default')
        username = decoded_token.get('cognito:username', user_id)
        
        logger.info(f"Authorized user: {username}, tenant: {tenant_id}")
        
        # Generate IAM policy
        policy = generate_policy(
            principal_id=user_id,
            effect='Allow',
            resource=event['methodArn'],
            context={
                'userId': user_id,
                'tenantId': tenant_id,
                'username': username,
            }
        )
        
        return policy
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise Exception('Unauthorized: Token expired')
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise Exception('Unauthorized: Invalid token')
    except Exception as e:
        logger.error(f"Authorization error: {str(e)}")
        raise Exception('Unauthorized')


def extract_token(event: Dict[str, Any]) -> str:
    """Extract JWT token from Authorization header."""
    auth_header = event.get('headers', {}).get('Authorization') or \
                  event.get('headers', {}).get('authorization')
    
    if not auth_header:
        return None
    
    # Remove 'Bearer ' prefix if present
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    return auth_header


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token signature and decode claims.
    """
    # Get signing key from JWKS
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    
    # Verify and decode token
    decoded_token = jwt.decode(
        token,
        signing_key.key,
        algorithms=['RS256'],
        audience=USER_POOL_CLIENT_ID,
        options={
            'verify_signature': True,
            'verify_exp': True,
            'verify_aud': True,
        }
    )
    
    return decoded_token


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Generate IAM policy document for API Gateway.
    """
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource,
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy
