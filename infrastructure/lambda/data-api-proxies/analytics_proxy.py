"""
Analytics API Tool Proxy Lambda

Proxies analytics requests for trend detection and pattern recognition.
"""

import json
import logging
import os
import psycopg2
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

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


def time_series_analysis(
    tenant_id: str,
    domain_id: Optional[str],
    field: str,
    time_bucket: str = 'day'
) -> Dict[str, Any]:
    """
    Perform time series analysis.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        field: Field to analyze
        time_bucket: Time bucket (hour, day, week, month)
    
    Returns:
        Time series data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine time bucket SQL
        if time_bucket == 'hour':
            bucket_sql = "DATE_TRUNC('hour', created_at)"
        elif time_bucket == 'day':
            bucket_sql = "DATE_TRUNC('day', created_at)"
        elif time_bucket == 'week':
            bucket_sql = "DATE_TRUNC('week', created_at)"
        elif time_bucket == 'month':
            bucket_sql = "DATE_TRUNC('month', created_at)"
        else:
            bucket_sql = "DATE_TRUNC('day', created_at)"
        
        query = f"""
            SELECT 
                {bucket_sql} as time_bucket,
                COUNT(*) as count,
                COUNT(DISTINCT structured_data->>%s) as unique_values
            FROM incidents
            WHERE tenant_id = %s
        """
        
        params = [field, tenant_id]
        
        if domain_id:
            query += " AND domain_id = %s"
            params.append(domain_id)
        
        query += f" GROUP BY {bucket_sql} ORDER BY time_bucket DESC LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        time_series = []
        for row in rows:
            time_series.append({
                'timestamp': row[0].isoformat() if row[0] else None,
                'count': int(row[1]),
                'unique_values': int(row[2])
            })
        
        # Calculate trend
        if len(time_series) >= 2:
            recent_avg = sum(t['count'] for t in time_series[:5]) / min(5, len(time_series))
            older_avg = sum(t['count'] for t in time_series[-5:]) / min(5, len(time_series))
            
            if older_avg > 0:
                trend_pct = ((recent_avg - older_avg) / older_avg) * 100
            else:
                trend_pct = 0
            
            trend = 'increasing' if trend_pct > 10 else 'decreasing' if trend_pct < -10 else 'stable'
        else:
            trend = 'insufficient_data'
            trend_pct = 0
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'analysis_type': 'time_series',
            'field': field,
            'time_bucket': time_bucket,
            'data': time_series,
            'trend': trend,
            'trend_percentage': round(trend_pct, 2)
        }
    
    except Exception as e:
        logger.error(f"Error in time series analysis: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def pattern_analysis(
    tenant_id: str,
    domain_id: Optional[str],
    field: str
) -> Dict[str, Any]:
    """
    Perform pattern analysis on a field.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        field: Field to analyze
    
    Returns:
        Pattern analysis results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get value distribution
        query = """
            SELECT 
                structured_data->>%s as value,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
            FROM incidents
            WHERE tenant_id = %s
            AND structured_data->>%s IS NOT NULL
        """
        
        params = [field, tenant_id, field]
        
        if domain_id:
            query += " AND domain_id = %s"
            params.append(domain_id)
        
        query += " GROUP BY structured_data->>%s ORDER BY count DESC LIMIT 20"
        params.append(field)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        patterns = []
        for row in rows:
            patterns.append({
                'value': row[0],
                'count': int(row[1]),
                'percentage': round(float(row[2]), 2)
            })
        
        # Identify top patterns
        top_pattern = patterns[0] if patterns else None
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'analysis_type': 'pattern',
            'field': field,
            'patterns': patterns,
            'top_pattern': top_pattern,
            'total_patterns': len(patterns)
        }
    
    except Exception as e:
        logger.error(f"Error in pattern analysis: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def correlation_analysis(
    tenant_id: str,
    domain_id: Optional[str],
    field1: str,
    field2: str
) -> Dict[str, Any]:
    """
    Analyze correlation between two fields.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Optional domain filter
        field1: First field
        field2: Second field
    
    Returns:
        Correlation analysis results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get co-occurrence matrix
        query = """
            SELECT 
                structured_data->>%s as value1,
                structured_data->>%s as value2,
                COUNT(*) as count
            FROM incidents
            WHERE tenant_id = %s
            AND structured_data->>%s IS NOT NULL
            AND structured_data->>%s IS NOT NULL
        """
        
        params = [field1, field2, tenant_id, field1, field2]
        
        if domain_id:
            query += " AND domain_id = %s"
            params.append(domain_id)
        
        query += " GROUP BY structured_data->>%s, structured_data->>%s ORDER BY count DESC LIMIT 50"
        params.extend([field1, field2])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        correlations = []
        for row in rows:
            correlations.append({
                field1: row[0],
                field2: row[1],
                'count': int(row[2])
            })
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'analysis_type': 'correlation',
            'field1': field1,
            'field2': field2,
            'correlations': correlations,
            'total_correlations': len(correlations)
        }
    
    except Exception as e:
        logger.error(f"Error in correlation analysis: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Analytics API proxy.
    
    Expected input:
    {
        "tenant_id": "string",
        "domain_id": "string (optional)",
        "analysis_type": "time_series|pattern|correlation",
        "field": "string",
        "field2": "string (for correlation)",
        "time_bucket": "hour|day|week|month (for time_series)"
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
        
        analysis_type = body.get('analysis_type', 'time_series')
        domain_id = body.get('domain_id')
        field = body.get('field')
        
        # Route to appropriate analysis
        if analysis_type == 'time_series':
            if not field:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing field'})
                }
            
            time_bucket = body.get('time_bucket', 'day')
            result = time_series_analysis(tenant_id, domain_id, field, time_bucket)
        
        elif analysis_type == 'pattern':
            if not field:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing field'})
                }
            
            result = pattern_analysis(tenant_id, domain_id, field)
        
        elif analysis_type == 'correlation':
            field2 = body.get('field2')
            if not field or not field2:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing field or field2'})
                }
            
            result = correlation_analysis(tenant_id, domain_id, field, field2)
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': f'Invalid analysis_type: {analysis_type}'})
            }
        
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
