"""
Test script for Geo Agent geometry type detection
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from geo_agent import GeoAgent


def test_geometry_detection():
    """Test geometry type detection with various text patterns"""
    
    # Create agent instance
    config = {
        'agent_name': 'GeoAgent',
        'tools': ['bedrock']
    }
    agent = GeoAgent(config)
    
    # Test cases
    test_cases = [
        # Point geometry tests
        ("There's a pothole at Main Street and 5th Avenue", "Point"),
        ("Fire at 123 Oak Street", "Point"),
        ("Accident at the intersection", "Point"),
        
        # LineString geometry tests
        ("Traffic congestion from Downtown to Airport", "LineString"),
        ("Road closure along Highway 101", "LineString"),
        ("Construction between Main Street and Park Avenue", "LineString"),
        ("Bike path along the river", "LineString"),
        ("Route 66 is closed", "LineString"),
        
        # Polygon geometry tests
        ("Power outage in the downtown area", "Polygon"),
        ("Flooding throughout the neighborhood", "Polygon"),
        ("Construction zone covering the entire block", "Polygon"),
        ("Fire in the industrial district", "Polygon"),
        ("Evacuation of the region", "Polygon"),
        ("Across the entire city", "Polygon"),
    ]
    
    print("Testing Geo Agent Geometry Type Detection")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for text, expected_type in test_cases:
        detected_type = agent.detect_geometry_type(text)
        status = "✓" if detected_type == expected_type else "✗"
        
        if detected_type == expected_type:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Text: {text[:50]}...")
        print(f"  Expected: {expected_type}, Detected: {detected_type}")
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success rate: {(passed/len(test_cases)*100):.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    success = test_geometry_detection()
    sys.exit(0 if success else 1)
