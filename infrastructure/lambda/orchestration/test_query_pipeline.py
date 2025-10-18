"""
Simple tests for query pipeline components
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from response_formatter import format_agent_output_as_bullet, format_response
from visualization_generator import extract_spatial_data, generate_heatmap_data


def test_response_formatter():
    """Test response formatter with sample agent outputs"""
    print("Testing Response Formatter...")
    
    # Sample agent output
    agent_output = {
        "insight": "Most complaints occur on Monday mornings between 7-9 AM",
        "time_pattern": "weekday_morning",
        "confidence": 0.85
    }
    
    # Format as bullet
    bullet = format_agent_output_as_bullet(
        agent_name="When Agent",
        agent_output=agent_output,
        interrogative="when"
    )
    
    print(f"  Bullet: {bullet}")
    assert bullet.startswith("• When:")
    assert "Monday mornings" in bullet
    
    # Test full formatting
    validated_results = [
        {
            "agent_id": "when-agent",
            "agent_name": "When Agent",
            "interrogative": "when",
            "output": agent_output,
            "status": "success"
        },
        {
            "agent_id": "where-agent",
            "agent_name": "Where Agent",
            "interrogative": "where",
            "output": {
                "insight": "Downtown area shows highest concentration"
            },
            "status": "success"
        }
    ]
    
    execution_plan = [
        {"agent_id": "when-agent"},
        {"agent_id": "where-agent"}
    ]
    
    result = format_response(validated_results, execution_plan)
    
    print(f"  Bullet count: {result['bullet_count']}")
    print(f"  Formatted text:\n{result['formatted_text']}")
    
    assert result['bullet_count'] == 2
    assert "When:" in result['formatted_text']
    assert "Where:" in result['formatted_text']
    
    print("✓ Response Formatter tests passed\n")


def test_visualization_generator():
    """Test visualization generator with spatial data"""
    print("Testing Visualization Generator...")
    
    # Sample agent outputs with spatial data
    validated_results = [
        {
            "agent_id": "geo-agent",
            "agent_name": "Geo Agent",
            "output": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "location_name": "New York"
            },
            "status": "success"
        },
        {
            "agent_id": "spatial-agent",
            "agent_name": "Spatial Agent",
            "output": {
                "coordinates": [40.7580, -73.9855],
                "area": "Times Square"
            },
            "status": "success"
        }
    ]
    
    # Extract spatial data
    spatial_data = extract_spatial_data(validated_results)
    
    print(f"  Extracted {len(spatial_data)} spatial points")
    assert len(spatial_data) == 2
    assert spatial_data[0]['latitude'] == 40.7128
    assert spatial_data[1]['latitude'] == 40.7580
    
    # Generate heatmap
    heatmap_data = generate_heatmap_data(spatial_data)
    
    print(f"  Generated {len(heatmap_data)} heatmap clusters")
    assert len(heatmap_data) >= 1
    
    print("✓ Visualization Generator tests passed\n")


def test_no_spatial_data():
    """Test visualization generator with no spatial data"""
    print("Testing Visualization Generator (no spatial data)...")
    
    validated_results = [
        {
            "agent_id": "temporal-agent",
            "agent_name": "Temporal Agent",
            "output": {
                "time_pattern": "morning",
                "peak_hour": 8
            },
            "status": "success"
        }
    ]
    
    spatial_data = extract_spatial_data(validated_results)
    
    print(f"  Extracted {len(spatial_data)} spatial points")
    assert len(spatial_data) == 0
    
    print("✓ No spatial data test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Query Pipeline Component Tests")
    print("=" * 60 + "\n")
    
    try:
        test_response_formatter()
        test_visualization_generator()
        test_no_spatial_data()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
