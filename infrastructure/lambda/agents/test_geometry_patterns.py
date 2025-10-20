"""
Simple test for geometry type detection patterns
Tests the regex patterns without requiring boto3
"""

import re


def detect_geometry_type(text: str) -> str:
    """
    Detect geometry type from text patterns.
    (Copied from geo_agent.py for testing)
    """
    text_lower = text.lower()
    
    # LineString patterns - routes, paths, connections
    linestring_patterns = [
        r'from\s+.+\s+to\s+.+',
        r'along\s+.+\s+street',
        r'along\s+.+\s+road',
        r'between\s+.+\s+and\s+.+',
        r'route\s+',
        r'path\s+',
        r'corridor',
        r'highway',
        r'freeway'
    ]
    
    for pattern in linestring_patterns:
        if re.search(pattern, text_lower):
            return 'LineString'
    
    # Polygon patterns - areas, zones, regions
    polygon_patterns = [
        r'\barea\b',
        r'\bzone\b',
        r'neighborhood',
        r'\bblock\b',
        r'region',
        r'district',
        r'entire\s+',
        r'throughout\s+',
        r'across\s+the\s+',
        r'perimeter',
        r'boundary'
    ]
    
    for pattern in polygon_patterns:
        if re.search(pattern, text_lower):
            return 'Polygon'
    
    # Default to Point for single locations
    return 'Point'


def test_geometry_detection():
    """Test geometry type detection with various text patterns"""
    
    # Test cases
    test_cases = [
        # Point geometry tests
        ("There's a pothole at Main Street and 5th Avenue", "Point"),
        ("Fire at 123 Oak Street", "Point"),
        ("Accident at the intersection", "Point"),
        ("Water main break on Elm Street", "Point"),
        
        # LineString geometry tests
        ("Traffic congestion from Downtown to Airport", "LineString"),
        ("Road closure along Highway 101", "LineString"),
        ("Construction between Main Street and Park Avenue", "LineString"),
        ("Bike path along the river", "LineString"),
        ("Route 66 is closed", "LineString"),
        ("Accident on the freeway", "LineString"),
        ("Corridor is blocked", "LineString"),
        
        # Polygon geometry tests
        ("Power outage in the downtown area", "Polygon"),
        ("Flooding throughout the neighborhood", "Polygon"),
        ("Construction zone covering the entire block", "Polygon"),
        ("Fire in the industrial district", "Polygon"),
        ("Evacuation of the region", "Polygon"),
        ("Across the entire city", "Polygon"),
        ("Security perimeter established", "Polygon"),
        ("Restricted zone", "Polygon"),
    ]
    
    print("Testing Geometry Type Detection Patterns")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for text, expected_type in test_cases:
        detected_type = detect_geometry_type(text)
        status = "✓" if detected_type == expected_type else "✗"
        
        if detected_type == expected_type:
            passed += 1
        else:
            failed += 1
        
        # Truncate text for display
        display_text = text if len(text) <= 50 else text[:47] + "..."
        
        print(f"{status} {display_text:<50} | Expected: {expected_type:<10} | Got: {detected_type}")
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success rate: {(passed/len(test_cases)*100):.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = test_geometry_detection()
    sys.exit(0 if success else 1)
