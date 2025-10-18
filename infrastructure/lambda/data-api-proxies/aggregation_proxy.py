"""
Aggregation API Tool Proxy Lambda

Proxies data aggregation requests for statistics and summaries.
"""

import json
import logging
import os
import psycopg2
from typing import Dict, Any, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def aggregate_data(
    tenant_id: str,
    domain_id: Optional[str],
    group_by: str,
    metric: str,
    field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregate incident data.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        group_by: Field to group by (domain, date, category, location)
        metric: Aggregation metric (count, avg, sum, min, max)
        field: Field to aggregate (for numeric metrics)
    
    Returns:
        Aggregation results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build aggregation query based on group_by
        if group_by == 'domain':
            query = """
                SELECT 
                    domain_id,
                    COUNT(*) as count
                FROM incidents
                WHERE tenant_id = %s
            """
            params = [tenant_id]
            
            if domain_id:
                query += " AND domain_id = %s"
                params.append(domain_id)
            
            query += " GROUP BY domain_id ORDER BY count DESC"
        
        elif group_by == 'date':
            query = """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM incidents
                WHERE tenant_id = %s
            """
            params = [tenant_id]
            
            if domain_id:
                query += " AND domain_id = %s"
                params.append(domain_id)
            
            query += " GROUP BY DATE(created_at) ORDER BY date DESC"
        
        elif group_by == 'category':
            query = """
                SELECT 
                    structured_data->>'category' as category,
                    COUNT(*) as count
                FROM incidents
                WHERE tenant_id = %s
                AND structured_data->>'category' IS NOT NULL
            """
            params = [tenant_id]
            
            if domain_id:
                query += " AND domain_id = %s"
                params.append(domain_id)
            
            query += " GROUP BY structured_data->>'category' ORDER BY count DESC"
        
        elif group_by == 'location':
            query = """
                SELECT 
                    COALESCE(
                        structured_data->>'municipality',
                        structured_data->>'location'
                    ) as location,
                    COUNT(*) as count
                FROM incidents
                WHERE tenant_id = %s
                AND (
                    structured_data->>'municipality' IS NOT NULL
                    OR structured_data->>'location' IS NOT NULL
                )
            """
            params = [tenant_id]
            
            if domain_id:
                query += " AND domain_id = %s"
                params.append(domain_id)
            
            query += " GROUP BY location ORDER BY count DESC"
        
        else:
            return {
                'status': 'error',
                'error': f'Invalid group_by value: {group_by}'
            }
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        results = []
        for row in rows:
            results.append({
                'group': str(row[0]) if row[0] else 'Unknown',
                'count': int(row[1])
            })
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'group_by': group_by,
            'metric': metric,
            'data': results,
            'total_groups': len(results)
        }
    
    except Exception as e:
        logger.error(f"Error aggregating data: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Aggregation API proxy.
    
    Expected input:
    {
        "tenant_id": "string",
        "domain_id": "string (optional)",
        "group_by": "domain|date|category|location",
        "metric": "count|avg|sum|min|max",
        "field": "string (optional, for numeric metrics)"
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
        
        group_by = body.get('group_by')
        if not group_by:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing group_by'})
            }
        
        metric = body.get('metric', 'count')
        domain_id = body.get('domain_id')
        field = body.get('field')
        
        # Aggregate data
        result = aggregate_data(tenant_id, domain_id, group_by, metric, field)
        
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
