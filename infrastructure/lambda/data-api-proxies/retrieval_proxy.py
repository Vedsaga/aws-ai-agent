"""
Retrieval API Tool Proxy Lambda

Proxies data retrieval requests with filtering capabilities.
"""

import json
import logging
import os
import boto3
import psycopg2
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Database connection parameters from environment
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# S3 client for image URLs
s3_client = boto3.client('s3')


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def build_retrieval_query(
    tenant_id: str,
    domain_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    custom_filters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    offset: int = 0
) -> tuple[str, List[Any]]:
    """
    Build SQL query for data retrieval with filters.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        date_from: Optional start date (ISO format)
        date_to: Optional end date (ISO format)
        location: Optional location filter
        category: Optional category filter
        custom_filters: Optional custom JSONB filters
        limit: Result limit
        offset: Result offset for pagination
    
    Returns:
        Tuple of (query_string, parameters)
    """
    query = """
        SELECT 
            i.id,
            i.tenant_id,
            i.domain_id,
            i.raw_text,
            i.structured_data,
            i.created_at,
            i.updated_at,
            i.created_by,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id', ie.id,
                        's3_key', ie.s3_key,
                        's3_bucket', ie.s3_bucket,
                        'content_type', ie.content_type,
                        'file_size_bytes', ie.file_size_bytes
                    )
                ) FILTER (WHERE ie.id IS NOT NULL),
                '[]'
            ) as images
        FROM incidents i
        LEFT JOIN image_evidence ie ON i.id = ie.incident_id
        WHERE i.tenant_id = %s
    """
    
    params = [tenant_id]
    
    # Add filters
    if domain_id:
        query += " AND i.domain_id = %s"
        params.append(domain_id)
    
    if date_from:
        query += " AND i.created_at >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND i.created_at <= %s"
        params.append(date_to)
    
    if location:
        # Search in structured_data for location-related fields
        query += " AND (i.structured_data->>'location' ILIKE %s OR i.structured_data->>'address' ILIKE %s)"
        location_pattern = f"%{location}%"
        params.extend([location_pattern, location_pattern])
    
    if category:
        query += " AND i.structured_data->>'category' = %s"
        params.append(category)
    
    if custom_filters:
        for key, value in custom_filters.items():
            query += f" AND i.structured_data->>%s = %s"
            params.extend([key, str(value)])
    
    # Group by incident
    query += " GROUP BY i.id"
    
    # Order by created_at descending
    query += " ORDER BY i.created_at DESC"
    
    # Add pagination
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    return query, params


def retrieve_incidents(
    tenant_id: str,
    filters: Dict[str, Any],
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieve incidents with filters.
    
    Args:
        tenant_id: Tenant identifier
        filters: Filter parameters
        limit: Result limit
        offset: Result offset
    
    Returns:
        Retrieval results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query, params = build_retrieval_query(
            tenant_id=tenant_id,
            domain_id=filters.get('domain_id'),
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to'),
            location=filters.get('location'),
            category=filters.get('category'),
            custom_filters=filters.get('custom_filters'),
            limit=limit,
            offset=offset
        )
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        results = []
        for row in rows:
            incident = {
                'id': str(row[0]),
                'tenant_id': str(row[1]),
                'domain_id': row[2],
                'raw_text': row[3],
                'structured_data': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'updated_at': row[6].isoformat() if row[6] else None,
                'created_by': str(row[7]),
                'images': row[8] if row[8] else []
            }
            
            # Generate presigned URLs for images
            for image in incident['images']:
                if image.get('s3_bucket') and image.get('s3_key'):
                    try:
                        url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={
                                'Bucket': image['s3_bucket'],
                                'Key': image['s3_key']
                            },
                            ExpiresIn=3600  # 1 hour
                        )
                        image['url'] = url
                    except Exception as e:
                        logger.warning(f"Error generating presigned URL: {str(e)}")
                        image['url'] = None
            
            results.append(incident)
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'data': results,
            'count': len(results),
            'limit': limit,
            'offset': offset
        }
    
    except Exception as e:
        logger.error(f"Error retrieving incidents: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Retrieval API proxy.
    
    Expected input:
    {
        "tenant_id": "string",
        "filters": {
            "domain_id": "string (optional)",
            "date_from": "ISO date string (optional)",
            "date_to": "ISO date string (optional)",
            "location": "string (optional)",
            "category": "string (optional)",
            "custom_filters": {} (optional)
        },
        "limit": int (optional, default: 100),
        "offset": int (optional, default: 0)
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
        tenant_id = body.get('tenant_id')
        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing tenant_id'})
            }
        
        filters = body.get('filters', {})
        limit = body.get('limit', 100)
        offset = body.get('offset', 0)
        
        # Retrieve incidents
        result = retrieve_incidents(tenant_id, filters, limit, offset)
        
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
