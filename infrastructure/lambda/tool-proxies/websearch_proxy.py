"""
Web Search Tool Proxy Lambda

Proxies requests to external web search API with API key from Secrets Manager.
"""

import json
import logging
import os
import boto3
import urllib.request
import urllib.parse
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')

# Environment variables
SEARCH_API_SECRET_NAME = os.environ.get('SEARCH_API_SECRET_NAME', 'web-search-api-key')


def get_api_key() -> str:
    """
    Retrieve web search API key from Secrets Manager.
    
    Returns:
        API key string
    """
    try:
        response = secrets_client.get_secret_value(SecretId=SEARCH_API_SECRET_NAME)
        
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            return secret.get('api_key', '')
        
        return ''
    
    except Exception as e:
        logger.error(f"Error retrieving API key: {str(e)}")
        raise


def search_web(query: str, max_results: int = 5, api_key: str = None) -> Dict[str, Any]:
    """
    Perform web search using external API.
    
    This is a generic implementation that can be adapted to various search APIs
    (Google Custom Search, Bing Search, SerpAPI, etc.)
    
    Args:
        query: Search query
        max_results: Maximum number of results
        api_key: API key (will retrieve from Secrets Manager if not provided)
    
    Returns:
        Search results
    """
    if not api_key:
        api_key = get_api_key()
    
    if not api_key:
        return {
            'status': 'error',
            'error': 'API key not configured'
        }
    
    try:
        # Example implementation for a generic search API
        # This should be adapted based on the actual search API being used
        
        # For demonstration, using a mock structure
        # In production, replace with actual API call
        
        # Example for Google Custom Search API:
        # base_url = "https://www.googleapis.com/customsearch/v1"
        # params = {
        #     'key': api_key,
        #     'cx': search_engine_id,
        #     'q': query,
        #     'num': max_results
        # }
        
        # For now, return a structured response format
        logger.info(f"Web search query: {query}")
        
        # Mock implementation - replace with actual API call
        results = []
        
        # In production, make actual HTTP request:
        # url = f"{base_url}?{urllib.parse.urlencode(params)}"
        # req = urllib.request.Request(url)
        # with urllib.request.urlopen(req) as response:
        #     data = json.loads(response.read().decode())
        #     for item in data.get('items', [])[:max_results]:
        #         results.append({
        #             'title': item.get('title'),
        #             'link': item.get('link'),
        #             'snippet': item.get('snippet'),
        #             'source': item.get('displayLink')
        #         })
        
        return {
            'status': 'success',
            'query': query,
            'results': results,
            'count': len(results),
            'message': 'Web search API not fully configured - implement with actual search provider'
        }
    
    except Exception as e:
        logger.error(f"Error performing web search: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Web Search proxy.
    
    Expected input:
    {
        "query": "string",
        "max_results": int (optional, default: 5)
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
        query = body.get('query')
        if not query:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing query'})
            }
        
        max_results = body.get('max_results', 5)
        
        # Perform search
        result = search_web(query, max_results)
        
        if result['status'] == 'success':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
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
