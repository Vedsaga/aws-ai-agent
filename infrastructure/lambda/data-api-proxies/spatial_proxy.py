"""
Spatial Query API Tool Proxy Lambda

Proxies spatial query requests using PostGIS.
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


def spatial_query(
    tenant_id: str,
    query_type: str,
    parameters: Dict[str, Any],
    domain_id: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Execute spatial query.
    
    Args:
        tenant_id: Tenant identifier
        query_type: Type of spatial query (radius, bbox, polygon)
        parameters: Query-specific parameters
        domain_id: Optional domain filter
        limit: Result limit
    
    Returns:
        Spatial query results
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT 
                i.id,
                i.domain_id,
                i.raw_text,
                i.structured_data,
                i.created_at,
                CAST(i.structured_data->>'latitude' AS FLOAT) as latitude,
                CAST(i.structured_data->>'longitude' AS FLOAT) as longitude
        """
        
        if query_type == 'radius':
            # Radius search around a center point
            center_lat = parameters.get('center_lat')
            center_lon = parameters.get('center_lon')
            radius_km = parameters.get('radius_km', 10)
            
            if center_lat is None or center_lon is None:
                return {
                    'status': 'error',
                    'error': 'Missing center_lat or center_lon for radius query'
                }
            
            query = base_query + """,
                ST_Distance(
                    ST_MakePoint(
                        CAST(i.structured_data->>'longitude' AS FLOAT),
                        CAST(i.structured_data->>'latitude' AS FLOAT)
                    )::geography,
                    ST_MakePoint(%s, %s)::geography
                ) / 1000 as distance_km
                FROM incidents i
                WHERE i.tenant_id = %s
                AND i.structured_data->>'latitude' IS NOT NULL
                AND i.structured_data->>'longitude' IS NOT NULL
                AND ST_DWithin(
                    ST_MakePoint(
                        CAST(i.structured_data->>'longitude' AS FLOAT),
                        CAST(i.structured_data->>'latitude' AS FLOAT)
                    )::geography,
                    ST_MakePoint(%s, %s)::geography,
                    %s
                )
            """
            
            params = [center_lon, center_lat, tenant_id, center_lon, center_lat, radius_km * 1000]
            
            if domain_id:
                query += " AND i.domain_id = %s"
                params.append(domain_id)
            
            query += " ORDER BY distance_km ASC LIMIT %s"
            params.append(limit)
        
        elif query_type == 'bbox':
            # Bounding box query
            min_lat = parameters.get('min_lat')
            max_lat = parameters.get('max_lat')
            min_lon = parameters.get('min_lon')
            max_lon = parameters.get('max_lon')
            
            if None in [min_lat, max_lat, min_lon, max_lon]:
                return {
                    'status': 'error',
                    'error': 'Missing bounding box parameters (min_lat, max_lat, min_lon, max_lon)'
                }
            
            query = base_query + """
                FROM incidents i
                WHERE i.tenant_id = %s
                AND i.structured_data->>'latitude' IS NOT NULL
                AND i.structured_data->>'longitude' IS NOT NULL
                AND CAST(i.structured_data->>'latitude' AS FLOAT) BETWEEN %s AND %s
                AND CAST(i.structured_data->>'longitude' AS FLOAT) BETWEEN %s AND %s
            """
            
            params = [tenant_id, min_lat, max_lat, min_lon, max_lon]
            
            if domain_id:
                query += " AND i.domain_id = %s"
                params.append(domain_id)
            
            query += " ORDER BY i.created_at DESC LIMIT %s"
            params.append(limit)
        
        elif query_type == 'polygon':
            # Polygon intersection query
            polygon_coords = parameters.get('polygon')
            
            if not polygon_coords or len(polygon_coords) < 3:
                return {
                    'status': 'error',
                    'error': 'Invalid polygon coordinates (need at least 3 points)'
                }
            
            # Build polygon WKT
            polygon_wkt = 'POLYGON((' + ', '.join([f"{lon} {lat}" for lat, lon in polygon_coords]) + '))'
            
            query = base_query + """
                FROM incidents i
                WHERE i.tenant_id = %s
                AND i.structured_data->>'latitude' IS NOT NULL
                AND i.structured_data->>'longitude' IS NOT NULL
                AND ST_Within(
                    ST_MakePoint(
                        CAST(i.structured_data->>'longitude' AS FLOAT),
                        CAST(i.structured_data->>'latitude' AS FLOAT)
                    ),
                    ST_GeomFromText(%s, 4326)
                )
            """
            
            params = [tenant_id, polygon_wkt]
            
            if domain_id:
                query += " AND i.domain_id = %s"
                params.append(domain_id)
            
            query += " ORDER BY i.created_at DESC LIMIT %s"
            params.append(limit)
        
        else:
            return {
                'status': 'error',
                'error': f'Invalid query_type: {query_type}'
            }
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results
        results = []
        for row in rows:
            result = {
                'id': str(row[0]),
                'domain_id': row[1],
                'raw_text': row[2],
                'structured_data': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'coordinates': {
                    'latitude': row[5],
                    'longitude': row[6]
                }
            }
            
            # Add distance for radius queries
            if query_type == 'radius' and len(row) > 7:
                result['distance_km'] = round(row[7], 2)
            
            results.append(result)
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'query_type': query_type,
            'data': results,
            'count': len(results)
        }
    
    except Exception as e:
        logger.error(f"Error executing spatial query: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Spatial Query API proxy.
    
    Expected input:
    {
        "tenant_id": "string",
        "query_type": "radius|bbox|polygon",
        "parameters": {
            // For radius:
            "center_lat": float,
            "center_lon": float,
            "radius_km": float,
            
            // For bbox:
            "min_lat": float,
            "max_lat": float,
            "min_lon": float,
            "max_lon": float,
            
            // For polygon:
            "polygon": [[lat, lon], ...]
        },
        "domain_id": "string (optional)",
        "limit": int (optional, default: 100)
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
        
        query_type = body.get('query_type')
        if not query_type:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing query_type'})
            }
        
        parameters = body.get('parameters', {})
        domain_id = body.get('domain_id')
        limit = body.get('limit', 100)
        
        # Execute spatial query
        result = spatial_query(tenant_id, query_type, parameters, domain_id, limit)
        
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
