"""
Vector Search Tool Proxy Lambda

Proxies vector search requests to OpenSearch for semantic similarity.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
session = boto3.Session()
credentials = session.get_credentials()

# OpenSearch configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_REGION = os.environ.get('AWS_REGION', 'us-east-1')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'incident_embeddings')

# Bedrock model for embeddings
EMBEDDING_MODEL_ID = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')

# AWS4Auth for OpenSearch
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    OPENSEARCH_REGION,
    'es',
    session_token=credentials.token
)

# OpenSearch client
opensearch_client = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
) if OPENSEARCH_ENDPOINT else None


def create_embedding(text: str) -> List[float]:
    """
    Create text embedding using Bedrock.
    
    Args:
        text: Input text
    
    Returns:
        Embedding vector
    """
    try:
        # Prepare request for Titan embeddings
        request_body = json.dumps({
            'inputText': text
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            body=request_body
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])
        
        return embedding
    
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}", exc_info=True)
        raise


def vector_search(
    query_text: str,
    tenant_id: str,
    domain_id: Optional[str] = None,
    top_k: int = 10,
    min_score: float = 0.7
) -> Dict[str, Any]:
    """
    Perform vector similarity search.
    
    Args:
        query_text: Query text
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        top_k: Number of results to return
        min_score: Minimum similarity score
    
    Returns:
        Search results
    """
    if not opensearch_client:
        return {
            'status': 'error',
            'error': 'OpenSearch not configured'
        }
    
    try:
        # Create query embedding
        query_embedding = create_embedding(query_text)
        
        # Build OpenSearch query
        query = {
            'size': top_k,
            'query': {
                'bool': {
                    'must': [
                        {
                            'knn': {
                                'text_embedding': {
                                    'vector': query_embedding,
                                    'k': top_k
                                }
                            }
                        },
                        {
                            'term': {
                                'tenant_id': tenant_id
                            }
                        }
                    ]
                }
            },
            'min_score': min_score
        }
        
        # Add domain filter if provided
        if domain_id:
            query['query']['bool']['must'].append({
                'term': {
                    'domain_id': domain_id
                }
            })
        
        # Execute search
        response = opensearch_client.search(
            index=OPENSEARCH_INDEX,
            body=query
        )
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'incident_id': source.get('incident_id'),
                'text_content': source.get('text_content'),
                'structured_data': source.get('structured_data'),
                'created_at': source.get('created_at'),
                'score': hit['_score']
            })
        
        return {
            'status': 'success',
            'query': query_text,
            'results': results,
            'count': len(results),
            'total_hits': response['hits']['total']['value']
        }
    
    except Exception as e:
        logger.error(f"Error performing vector search: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Vector Search proxy.
    
    Expected input:
    {
        "query_text": "string",
        "tenant_id": "string",
        "domain_id": "string (optional)",
        "top_k": int (optional, default: 10),
        "min_score": float (optional, default: 0.7)
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
        query_text = body.get('query_text')
        tenant_id = body.get('tenant_id')
        
        if not query_text or not tenant_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing query_text or tenant_id'})
            }
        
        domain_id = body.get('domain_id')
        top_k = body.get('top_k', 10)
        min_score = body.get('min_score', 0.7)
        
        # Perform vector search
        result = vector_search(query_text, tenant_id, domain_id, top_k, min_score)
        
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
