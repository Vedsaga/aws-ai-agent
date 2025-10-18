"""
Location Service Tool Proxy Lambda

Proxies requests to Amazon Location Service with IAM authentication.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

location_client = boto3.client('location')

# Environment variables
PLACE_INDEX_NAME = os.environ.get('PLACE_INDEX_NAME', 'default-place-index')


def geocode_address(address: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Convert address to coordinates (geocoding).
    
    Args:
        address: Address string
        max_results: Maximum number of results
    
    Returns:
        Geocoding results
    """
    try:
        response = location_client.search_place_index_for_text(
            IndexName=PLACE_INDEX_NAME,
            Text=address,
            MaxResults=max_results
        )
        
        results = []
        for result in response.get('Results', []):
            place = result.get('Place', {})
            geometry = place.get('Geometry', {})
            point = geometry.get('Point', [])
            
            results.append({
                'label': place.get('Label'),
                'address': place.get('AddressNumber', '') + ' ' + place.get('Street', ''),
                'municipality': place.get('Municipality'),
                'region': place.get('Region'),
                'country': place.get('Country'),
                'postal_code': place.get('PostalCode'),
                'coordinates': {
                    'longitude': point[0] if len(point) > 0 else None,
                    'latitude': point[1] if len(point) > 1 else None
                },
                'relevance': result.get('Relevance', 0)
            })
        
        return {
            'status': 'success',
            'results': results,
            'count': len(results)
        }
    
    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def reverse_geocode(latitude: float, longitude: float, max_results: int = 1) -> Dict[str, Any]:
    """
    Convert coordinates to address (reverse geocoding).
    
    Args:
        latitude: Latitude
        longitude: Longitude
        max_results: Maximum number of results
    
    Returns:
        Reverse geocoding results
    """
    try:
        response = location_client.search_place_index_for_position(
            IndexName=PLACE_INDEX_NAME,
            Position=[longitude, latitude],
            MaxResults=max_results
        )
        
        results = []
        for result in response.get('Results', []):
            place = result.get('Place', {})
            
            results.append({
                'label': place.get('Label'),
                'address': place.get('AddressNumber', '') + ' ' + place.get('Street', ''),
                'municipality': place.get('Municipality'),
                'region': place.get('Region'),
                'country': place.get('Country'),
                'postal_code': place.get('PostalCode'),
                'distance': result.get('Distance', 0)
            })
        
        return {
            'status': 'success',
            'results': results,
            'count': len(results)
        }
    
    except Exception as e:
        logger.error(f"Error reverse geocoding: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def calculate_route(
    departure_position: List[float],
    destination_position: List[float],
    travel_mode: str = 'Car'
) -> Dict[str, Any]:
    """
    Calculate route between two positions.
    
    Args:
        departure_position: [longitude, latitude]
        destination_position: [longitude, latitude]
        travel_mode: Travel mode (Car, Truck, Walking)
    
    Returns:
        Route calculation results
    """
    try:
        # Note: This requires a route calculator resource
        calculator_name = os.environ.get('ROUTE_CALCULATOR_NAME', 'default-route-calculator')
        
        response = location_client.calculate_route(
            CalculatorName=calculator_name,
            DeparturePosition=departure_position,
            DestinationPosition=destination_position,
            TravelMode=travel_mode
        )
        
        summary = response.get('Summary', {})
        
        return {
            'status': 'success',
            'distance_km': summary.get('Distance', 0),
            'duration_seconds': summary.get('DurationSeconds', 0),
            'route_bbox': summary.get('RouteBBox', []),
            'legs': response.get('Legs', [])
        }
    
    except Exception as e:
        logger.error(f"Error calculating route: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Location Service proxy.
    
    Expected input:
    {
        "operation": "geocode|reverse_geocode|calculate_route",
        "address": "string (for geocode)",
        "latitude": float (for reverse_geocode),
        "longitude": float (for reverse_geocode),
        "departure_position": [lon, lat] (for calculate_route),
        "destination_position": [lon, lat] (for calculate_route),
        "travel_mode": "string (optional, for calculate_route)",
        "max_results": int (optional)
    }
    """
    try:
        # Parse body
        body = event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']
        
        # Extract operation
        operation = body.get('operation', 'geocode')
        
        # Route to appropriate operation
        if operation == 'geocode':
            address = body.get('address')
            if not address:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing address'})
                }
            
            max_results = body.get('max_results', 5)
            result = geocode_address(address, max_results)
        
        elif operation == 'reverse_geocode':
            latitude = body.get('latitude')
            longitude = body.get('longitude')
            
            if latitude is None or longitude is None:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing latitude or longitude'})
                }
            
            max_results = body.get('max_results', 1)
            result = reverse_geocode(latitude, longitude, max_results)
        
        elif operation == 'calculate_route':
            departure = body.get('departure_position')
            destination = body.get('destination_position')
            
            if not departure or not destination:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'bad_request', 'message': 'Missing departure or destination'})
                }
            
            travel_mode = body.get('travel_mode', 'Car')
            result = calculate_route(departure, destination, travel_mode)
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': f'Invalid operation: {operation}'})
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
