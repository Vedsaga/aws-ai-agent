"""
Visualization Generator Lambda Function

Checks for spatial data in query results and generates map update instructions.
Creates heatmap data for concentrations and returns visualization config.

Requirements: 9.5
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_spatial_data(validated_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract spatial data from agent outputs.
    
    Args:
        validated_results: List of validated agent outputs
    
    Returns:
        List of spatial data points with coordinates
    """
    spatial_data = []
    
    for result in validated_results:
        if result.get('status') != 'success':
            continue
        
        output = result.get('output', {})
        agent_name = result.get('agent_name', 'Unknown')
        
        # Look for coordinate fields
        lat = None
        lng = None
        
        # Common field names for coordinates
        if 'latitude' in output and 'longitude' in output:
            lat = output['latitude']
            lng = output['longitude']
        elif 'lat' in output and 'lng' in output:
            lat = output['lat']
            lng = output['lng']
        elif 'coordinates' in output:
            coords = output['coordinates']
            if isinstance(coords, list) and len(coords) >= 2:
                lat = coords[0]
                lng = coords[1]
            elif isinstance(coords, dict):
                lat = coords.get('lat') or coords.get('latitude')
                lng = coords.get('lng') or coords.get('longitude')
        elif 'location' in output:
            location = output['location']
            if isinstance(location, dict):
                lat = location.get('lat') or location.get('latitude')
                lng = location.get('lng') or location.get('longitude')
        
        # Validate coordinates
        if lat is not None and lng is not None:
            try:
                lat = float(lat)
                lng = float(lng)
                
                # Basic validation
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    spatial_data.append({
                        'agent_name': agent_name,
                        'latitude': lat,
                        'longitude': lng,
                        'data': output
                    })
                    logger.info(f"Extracted spatial data from {agent_name}: ({lat}, {lng})")
            except (ValueError, TypeError):
                logger.warning(f"Invalid coordinate values from {agent_name}")
    
    return spatial_data


def generate_heatmap_data(spatial_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate heatmap data for spatial concentrations.
    
    Args:
        spatial_data: List of spatial data points
    
    Returns:
        Heatmap data with intensity values
    """
    if not spatial_data:
        return []
    
    # Group nearby points (within ~0.01 degrees, roughly 1km)
    CLUSTER_THRESHOLD = 0.01
    clusters = defaultdict(list)
    
    for point in spatial_data:
        lat = point['latitude']
        lng = point['longitude']
        
        # Round to cluster threshold
        cluster_key = (
            round(lat / CLUSTER_THRESHOLD) * CLUSTER_THRESHOLD,
            round(lng / CLUSTER_THRESHOLD) * CLUSTER_THRESHOLD
        )
        
        clusters[cluster_key].append(point)
    
    # Generate heatmap points with intensity
    heatmap_data = []
    
    for (cluster_lat, cluster_lng), points in clusters.items():
        intensity = len(points)
        
        # Calculate average position within cluster
        avg_lat = sum(p['latitude'] for p in points) / len(points)
        avg_lng = sum(p['longitude'] for p in points) / len(points)
        
        heatmap_data.append({
            'latitude': avg_lat,
            'longitude': avg_lng,
            'intensity': intensity,
            'point_count': len(points)
        })
    
    logger.info(f"Generated {len(heatmap_data)} heatmap clusters from {len(spatial_data)} points")
    
    return heatmap_data


def calculate_map_bounds(spatial_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Calculate bounding box for map view.
    
    Args:
        spatial_data: List of spatial data points
    
    Returns:
        Bounding box with min/max lat/lng
    """
    if not spatial_data:
        return None
    
    lats = [p['latitude'] for p in spatial_data]
    lngs = [p['longitude'] for p in spatial_data]
    
    # Add padding (10% of range)
    lat_range = max(lats) - min(lats)
    lng_range = max(lngs) - min(lngs)
    
    lat_padding = max(lat_range * 0.1, 0.01)  # At least 0.01 degrees
    lng_padding = max(lng_range * 0.1, 0.01)
    
    return {
        'min_latitude': min(lats) - lat_padding,
        'max_latitude': max(lats) + lat_padding,
        'min_longitude': min(lngs) - lng_padding,
        'max_longitude': max(lngs) + lng_padding,
        'center_latitude': sum(lats) / len(lats),
        'center_longitude': sum(lngs) / len(lngs)
    }


def generate_visualization_config(
    spatial_data: List[Dict[str, Any]],
    heatmap_data: List[Dict[str, Any]],
    bounds: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate complete visualization configuration.
    
    Args:
        spatial_data: Raw spatial data points
        heatmap_data: Heatmap cluster data
        bounds: Map bounding box
    
    Returns:
        Visualization configuration
    """
    config = {
        'has_spatial_data': len(spatial_data) > 0,
        'point_count': len(spatial_data),
        'cluster_count': len(heatmap_data),
        'visualization_type': 'none'
    }
    
    if not spatial_data:
        return config
    
    # Determine visualization type based on data
    if len(spatial_data) == 1:
        config['visualization_type'] = 'marker'
        config['marker'] = {
            'latitude': spatial_data[0]['latitude'],
            'longitude': spatial_data[0]['longitude'],
            'data': spatial_data[0]['data']
        }
    elif len(spatial_data) <= 10:
        config['visualization_type'] = 'markers'
        config['markers'] = [
            {
                'latitude': p['latitude'],
                'longitude': p['longitude'],
                'agent_name': p['agent_name'],
                'data': p['data']
            }
            for p in spatial_data
        ]
    else:
        config['visualization_type'] = 'heatmap'
        config['heatmap'] = heatmap_data
    
    # Add bounds for map centering
    if bounds:
        config['bounds'] = bounds
    
    # Add map update instructions
    config['map_update'] = {
        'action': 'update_view',
        'center': {
            'latitude': bounds['center_latitude'] if bounds else spatial_data[0]['latitude'],
            'longitude': bounds['center_longitude'] if bounds else spatial_data[0]['longitude']
        },
        'zoom': 'auto'  # Frontend will calculate based on bounds
    }
    
    return config


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for visualization generation.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "validated_results": [...]
    }
    
    Returns:
        Visualization configuration
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        validated_results = event.get('validated_results', [])
        
        # Validate required fields
        if not all([job_id, tenant_id]):
            raise ValueError("Missing required fields: job_id or tenant_id")
        
        logger.info(
            f"Generating visualization for job {job_id} with "
            f"{len(validated_results)} validated results"
        )
        
        # Extract spatial data
        spatial_data = extract_spatial_data(validated_results)
        
        if not spatial_data:
            logger.info("No spatial data found in query results")
            return {
                'job_id': job_id,
                'tenant_id': tenant_id,
                'visualization_config': {
                    'has_spatial_data': False,
                    'visualization_type': 'none'
                },
                'status': 'success'
            }
        
        # Generate heatmap data
        heatmap_data = generate_heatmap_data(spatial_data)
        
        # Calculate map bounds
        bounds = calculate_map_bounds(spatial_data)
        
        # Generate visualization config
        viz_config = generate_visualization_config(
            spatial_data=spatial_data,
            heatmap_data=heatmap_data,
            bounds=bounds
        )
        
        logger.info(
            f"Generated visualization config: type={viz_config['visualization_type']}, "
            f"points={viz_config['point_count']}"
        )
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'visualization_config': viz_config,
            'status': 'success'
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'visualization_config': {
                'has_spatial_data': False,
                'visualization_type': 'none'
            },
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error generating visualization: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'visualization_config': {
                'has_spatial_data': False,
                'visualization_type': 'none'
            },
            'status': 'error',
            'error_message': f"Visualization generation error: {str(e)}"
        }
