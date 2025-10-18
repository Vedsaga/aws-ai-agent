import json
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']

# AWS credentials for signing requests
session = boto3.Session()
credentials = session.get_credentials()
region = session.region_name or 'us-east-1'

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    'es',
    session_token=credentials.token
)


def handler(event, context):
    """
    Initialize OpenSearch index with knn_vector mapping for embeddings.
    This function is idempotent and can be run multiple times.
    """
    try:
        # Create OpenSearch client
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        logger.info(f"Connected to OpenSearch at {OPENSEARCH_ENDPOINT}")
        
        # Define index name
        index_name = 'incident_embeddings'
        
        # Check if index already exists
        if client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Index {index_name} already exists'
                })
            }
        
        # Define index mapping with knn_vector
        index_body = {
            'settings': {
                'index': {
                    'knn': True,
                    'knn.algo_param.ef_search': 512,
                    'number_of_shards': 2,
                    'number_of_replicas': 1,
                }
            },
            'mappings': {
                'properties': {
                    'incident_id': {
                        'type': 'keyword'
                    },
                    'tenant_id': {
                        'type': 'keyword'
                    },
                    'domain_id': {
                        'type': 'keyword'
                    },
                    'text_embedding': {
                        'type': 'knn_vector',
                        'dimension': 1536,
                        'method': {
                            'name': 'hnsw',
                            'space_type': 'cosinesimil',
                            'engine': 'nmslib',
                            'parameters': {
                                'ef_construction': 512,
                                'm': 16
                            }
                        }
                    },
                    'text_content': {
                        'type': 'text',
                        'analyzer': 'standard'
                    },
                    'structured_data': {
                        'type': 'object',
                        'enabled': True
                    },
                    'created_at': {
                        'type': 'date'
                    }
                }
            }
        }
        
        # Create index
        response = client.indices.create(
            index=index_name,
            body=index_body
        )
        
        logger.info(f"Index {index_name} created successfully: {response}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Index {index_name} created successfully',
                'response': response
            })
        }
        
    except Exception as e:
        logger.error(f"Error initializing OpenSearch index: {str(e)}")
        raise
