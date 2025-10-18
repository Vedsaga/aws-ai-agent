"""
Custom API Tool Proxy Lambda

Proxies requests to custom domain APIs with user credentials from Secrets Manager.
"""

import json
import logging
import os
import boto3
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')


def get_api_credentials(api_name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve API credentials from Secrets Manager.
    
    Args:
        api_name: API identifier
        tenant_id: Tenant identifier
    
    Returns:
        Credentials dict or None
    """
    try:
        secret_name = f"custom-api/{tenant_id}/{api_name}"
        response = secrets_client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        
        return None
    
    except secrets_client.exceptions.ResourceNotFoundException:
        logger.warning(f"Credentials not found for API: {api_name}")
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving credentials: {str(e)}")
        return None


def make_api_request(
    endpoint: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Make HTTP request to custom API.
    
    Args:
        endpoint: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Request headers
        body: Request body (for POST/PUT)
        params: Query parameters
    
    Returns:
        API response
    """
    try:
        # Build URL with query parameters
        url = endpoint
        if params:
            url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        
        # Prepare request
        req_data = None
        if body:
            req_data = json.dumps(body).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        
        req = urllib.request.Request(
            url,
            data=req_data,
            headers=headers,
            method=method
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            
            # Try to parse as JSON
            try:
                response_json = json.loads(response_data)
            except json.JSONDecodeError:
                response_json = {'raw_response': response_data}
            
            return {
                'status': 'success',
                'status_code': response.status,
                'data': response_json
            }
    
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error: {e.code} - {e.reason}")
        error_body = e.read().decode('utf-8') if e.fp else ''
        
        return {
            'status': 'error',
            'status_code': e.code,
            'error': e.reason,
            'error_body': error_body
        }
    
    except urllib.error.URLError as e:
        logger.error(f"URL error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    except Exception as e:
        logger.error(f"Error making API request: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Custom API proxy.
    
    Expected input:
    {
        "api_name": "string",
        "tenant_id": "string",
        "endpoint": "string",
        "method": "GET|POST|PUT|DELETE",
        "headers": {},
        "body": {},
        "params": {}
    }
    """
    try:
        # Parse body
        body = event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']
        
        # Extract parameters
        api_name = body.get('api_name')
        tenant_id = body.get('tenant_id')
        endpoint = body.get('endpoint')
        method = body.get('method', 'GET')
        
        if not api_name or not tenant_id or not endpoint:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'bad_request',
                    'message': 'Missing required fields: api_name, tenant_id, endpoint'
                })
            }
        
        # Get credentials
        credentials = get_api_credentials(api_name, tenant_id)
        
        if not credentials:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'unauthorized',
                    'message': f'Credentials not found for API: {api_name}'
                })
            }
        
        # Prepare headers with credentials
        headers = body.get('headers', {})
        
        # Add authentication based on credential type
        if 'api_key' in credentials:
            # API key authentication
            key_header = credentials.get('key_header', 'X-API-Key')
            headers[key_header] = credentials['api_key']
        
        elif 'bearer_token' in credentials:
            # Bearer token authentication
            headers['Authorization'] = f"Bearer {credentials['bearer_token']}"
        
        elif 'username' in credentials and 'password' in credentials:
            # Basic authentication
            import base64
            auth_string = f"{credentials['username']}:{credentials['password']}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            headers['Authorization'] = f"Basic {auth_b64}"
        
        # Make API request
        result = make_api_request(
            endpoint=endpoint,
            method=method,
            headers=headers,
            body=body.get('body'),
            params=body.get('params')
        )
        
        if result['status'] == 'success':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            status_code = result.get('status_code', 500)
            return {
                'statusCode': status_code,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal_error', 'message': str(e)})
        }
