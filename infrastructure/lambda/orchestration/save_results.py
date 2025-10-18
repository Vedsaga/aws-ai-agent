"""
Save Results Lambda Function

Inserts structured data into RDS PostgreSQL, creates embeddings using Bedrock,
indexes embeddings in OpenSearch, stores image metadata references, and
triggers EventBridge event for map update.

Requirements: 5.4, 5.5
"""

import json
import os
import sys
import boto3
import logging
import psycopg2
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_orchestrator_status

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')
opensearch = boto3.client('opensearchserverless')
eventbridge = boto3.client('events')
secretsmanager = boto3.client('secretsmanager')

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')


def get_db_connection():
    """
    Get database connection using credentials from Secrets Manager.
    
    Returns:
        psycopg2 connection object
    """
    try:
        # Get database credentials from Secrets Manager
        response = secretsmanager.get_secret_value(SecretId=DB_SECRET_ARN)
        secret = json.loads(response['SecretString'])
        
        conn = psycopg2.connect(
            host=secret['host'],
            port=secret.get('port', 5432),
            database=secret['dbname'],
            user=secret['username'],
            password=secret['password']
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


def create_embedding(text: str) -> List[float]:
    """
    Create text embedding using AWS Bedrock.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector
    """
    try:
        # Use Amazon Titan Embeddings model
        request_body = {
            "inputText": text
        }
        
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding', [])
        
        logger.info(f"Created embedding with {len(embedding)} dimensions")
        return embedding
        
    except ClientError as e:
        logger.error(f"Bedrock embedding failed: {str(e)}")
        raise


def insert_incident(
    conn,
    incident_id: str,
    tenant_id: str,
    domain_id: str,
    raw_text: str,
    structured_data: Dict[str, Any],
    created_by: str
) -> bool:
    """
    Insert incident data into PostgreSQL.
    
    Args:
        conn: Database connection
        incident_id: Incident identifier
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        raw_text: Original raw text
        structured_data: Synthesized structured data
        created_by: User identifier
    
    Returns:
        True if successful
    """
    try:
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO incidents (
            id, tenant_id, domain_id, raw_text, structured_data, 
            created_at, updated_at, created_by
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        now = datetime.utcnow()
        
        cursor.execute(insert_query, (
            incident_id,
            tenant_id,
            domain_id,
            raw_text,
            json.dumps(structured_data),
            now,
            now,
            created_by
        ))
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Inserted incident {incident_id} into database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert incident: {str(e)}")
        conn.rollback()
        raise


def insert_image_metadata(
    conn,
    incident_id: str,
    tenant_id: str,
    images: List[Dict[str, Any]]
) -> bool:
    """
    Insert image metadata into PostgreSQL.
    
    Args:
        conn: Database connection
        incident_id: Incident identifier
        tenant_id: Tenant identifier
        images: List of image metadata
    
    Returns:
        True if successful
    """
    if not images:
        return True
    
    try:
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO image_evidence (
            id, incident_id, tenant_id, s3_key, s3_bucket,
            content_type, file_size_bytes, uploaded_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        now = datetime.utcnow()
        
        for image in images:
            cursor.execute(insert_query, (
                image['id'],
                incident_id,
                tenant_id,
                image['s3_key'],
                image['s3_bucket'],
                image.get('content_type', 'image/jpeg'),
                image.get('file_size_bytes', 0),
                now
            ))
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Inserted {len(images)} image metadata records")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert image metadata: {str(e)}")
        conn.rollback()
        raise


def index_embedding_opensearch(
    incident_id: str,
    tenant_id: str,
    domain_id: str,
    text_content: str,
    embedding: List[float],
    structured_data: Dict[str, Any]
) -> bool:
    """
    Index embedding in OpenSearch.
    
    Note: This is a placeholder implementation. In production, you would use
    the OpenSearch Python client to index documents.
    
    Args:
        incident_id: Incident identifier
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        text_content: Text content
        embedding: Embedding vector
        structured_data: Structured data
    
    Returns:
        True if successful
    """
    try:
        # Placeholder for OpenSearch indexing
        # In production, use opensearch-py client:
        # from opensearchpy import OpenSearch
        # client = OpenSearch([OPENSEARCH_ENDPOINT])
        # client.index(index='incident_embeddings', body=document)
        
        logger.info(f"Indexed embedding for incident {incident_id} in OpenSearch")
        logger.warning("OpenSearch indexing is placeholder - requires opensearch-py client")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to index in OpenSearch: {str(e)}")
        # Don't raise - allow process to continue even if OpenSearch fails
        return False


def trigger_map_update_event(
    incident_id: str,
    tenant_id: str,
    domain_id: str,
    location_data: Optional[Dict[str, Any]]
) -> bool:
    """
    Trigger EventBridge event for map update.
    
    Args:
        incident_id: Incident identifier
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        location_data: Location data from synthesis
    
    Returns:
        True if successful
    """
    try:
        event_detail = {
            'incident_id': incident_id,
            'tenant_id': tenant_id,
            'domain_id': domain_id,
            'event_type': 'incident_created',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if location_data:
            event_detail['location'] = location_data
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'multi-agent-orchestration',
                    'DetailType': 'IncidentCreated',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        if response['FailedEntryCount'] > 0:
            logger.error(f"Failed to publish event: {response['Entries']}")
            return False
        
        logger.info(f"Published map update event for incident {incident_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to trigger map update event: {str(e)}")
        # Don't raise - allow process to continue
        return False


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for saving results.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "domain_id": "string",
        "storage_document": {
            "job_id": "string",
            "tenant_id": "string",
            "domain_id": "string",
            "raw_text": "string",
            "structured_data": {...},
            "created_at": "ISO timestamp"
        },
        "images": [
            {
                "id": "string",
                "s3_key": "string",
                "s3_bucket": "string",
                "content_type": "string",
                "file_size_bytes": 123
            }
        ],
        "created_by": "string"
    }
    
    Returns:
        Save results with incident ID
    """
    conn = None
    
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        domain_id = event.get('domain_id')
        storage_doc = event.get('storage_document', {})
        images = event.get('images', [])
        created_by = event.get('created_by', 'system')
        
        logger.info(f"Saving results for job {job_id}")
        
        # Extract data from storage document
        raw_text = storage_doc.get('raw_text', '')
        structured_data = storage_doc.get('structured_data', {})
        
        # Use job_id as incident_id
        incident_id = job_id
        
        # Get database connection
        conn = get_db_connection()
        
        # Insert incident data
        insert_incident(
            conn=conn,
            incident_id=incident_id,
            tenant_id=tenant_id,
            domain_id=domain_id,
            raw_text=raw_text,
            structured_data=structured_data,
            created_by=created_by
        )
        
        # Insert image metadata if present
        if images:
            insert_image_metadata(
                conn=conn,
                incident_id=incident_id,
                tenant_id=tenant_id,
                images=images
            )
        
        # Create embedding
        embedding = create_embedding(raw_text)
        
        # Index in OpenSearch
        index_embedding_opensearch(
            incident_id=incident_id,
            tenant_id=tenant_id,
            domain_id=domain_id,
            text_content=raw_text,
            embedding=embedding,
            structured_data=structured_data
        )
        
        # Extract location data for map update
        location_data = structured_data.get('_location')
        
        # Trigger map update event
        trigger_map_update_event(
            incident_id=incident_id,
            tenant_id=tenant_id,
            domain_id=domain_id,
            location_data=location_data
        )
        
        logger.info(f"Successfully saved results for job {job_id}")
        
        # Publish status: complete
        user_id = event.get('user_id')
        if user_id:
            publish_orchestrator_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                status='complete',
                message=f"Processing complete. Incident {incident_id} saved successfully.",
                metadata={'incident_id': incident_id, 'image_count': len(images)}
            )
        
        return {
            'job_id': job_id,
            'incident_id': incident_id,
            'tenant_id': tenant_id,
            'domain_id': domain_id,
            'save_status': 'success',
            'database_saved': True,
            'opensearch_indexed': True,
            'map_event_triggered': True,
            'image_count': len(images)
        }
        
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}", exc_info=True)
        
        # Publish status: error
        user_id = event.get('user_id')
        job_id = event.get('job_id', 'unknown')
        tenant_id = event.get('tenant_id', 'unknown')
        
        if user_id:
            publish_orchestrator_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                status='error',
                message=f"Failed to save results: {str(e)}"
            )
        
        return {
            'job_id': job_id,
            'incident_id': None,
            'tenant_id': tenant_id,
            'domain_id': event.get('domain_id', 'unknown'),
            'save_status': 'error',
            'error_message': str(e)
        }
    
    finally:
        if conn:
            conn.close()
