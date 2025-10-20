#!/usr/bin/env python3
"""
Test all API endpoints and verify they return 200 status
"""

import requests
import json
import sys
import os

# API Configuration
API_URL = "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# Get JWT token from environment or use test token
JWT_TOKEN = os.environ.get('JWT_TOKEN', '')

if not JWT_TOKEN:
    print("⚠️  No JWT_TOKEN found. Please run: export JWT_TOKEN=$(./get_jwt_token.sh)")
    print("Attempting to get token...")
    import subprocess
    try:
        result = subprocess.run(['bash', 'get_jwt_token.sh'], capture_output=True, text=True)
        JWT_TOKEN = result.stdout.strip()
        if JWT_TOKEN:
            print("✓ Got JWT token")
        else:
            print("✗ Failed to get JWT token")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error getting token: {e}")
        sys.exit(1)

headers = {
    'Authorization': f'Bearer {JWT_TOKEN}',
    'Content-Type': 'application/json'
}

def test_endpoint(name, method, url, data=None, expected_status=200):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Method: {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"✓ PASS - Got expected status {expected_status}")
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)[:500]}")
            except:
                print(f"Response: {response.text[:500]}")
            return True
        else:
            print(f"✗ FAIL - Expected {expected_status}, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

# Run tests
print("="*60)
print("API ENDPOINT TESTING")
print("="*60)

results = []

# 1. Test Config API - List Agents
results.append(test_endpoint(
    "Config API - List Agents",
    "GET",
    f"{API_URL}/api/v1/config?type=agent",
    expected_status=200
))

# 2. Test Config API - List Domain Templates
results.append(test_endpoint(
    "Config API - List Domain Templates",
    "GET",
    f"{API_URL}/api/v1/config?type=domain_template",
    expected_status=200
))

# 3. Test Ingest API
results.append(test_endpoint(
    "Ingest API - Submit Report",
    "POST",
    f"{API_URL}/api/v1/ingest",
    data={
        "domain_id": "civic_complaints",
        "text": "There is a pothole on Main Street near the library. It's been there for weeks and is getting worse."
    },
    expected_status=202
))

# 4. Test Query API
results.append(test_endpoint(
    "Query API - Ask Question",
    "POST",
    f"{API_URL}/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "What are the most common types of complaints?"
    },
    expected_status=202
))

# 5. Test Tools API
results.append(test_endpoint(
    "Tools API - List Tools",
    "GET",
    f"{API_URL}/api/v1/tools",
    expected_status=200
))

# 6. Test Data API
results.append(test_endpoint(
    "Data API - Retrieve Data",
    "GET",
    f"{API_URL}/api/v1/data?type=retrieval",
    expected_status=200
))

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
passed = sum(results)
total = len(results)
print(f"Passed: {passed}/{total}")
print(f"Failed: {total - passed}/{total}")

if passed == total:
    print("\n✓ ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("\n✗ SOME TESTS FAILED")
    sys.exit(1)
