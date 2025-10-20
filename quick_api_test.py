#!/usr/bin/env python3
"""Quick API Test - Test all endpoints and fix issues"""

import requests
import json
import sys
import os

# Configuration
API_URL = "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
JWT_TOKEN = os.environ.get("JWT_TOKEN", "")

# API Endpoints to test
ENDPOINTS = [
    # Config API
    {"method": "GET", "path": "/api/v1/config", "params": {"type": "agent"}, "name": "List Agents"},
    {"method": "GET", "path": "/api/v1/config", "params": {"type": "domain_template"}, "name": "List Domains"},
    {"method": "GET", "path": "/api/v1/config", "params": {"type": "playbook"}, "name": "List Playbooks"},
    {"method": "GET", "path": "/api/v1/config", "params": {"type": "dependency_graph"}, "name": "List Dependency Graphs"},
    
    # Data API
    {"method": "GET", "path": "/api/v1/data/retrieval", "params": {"domain_id": "civic_complaints"}, "name": "Data Retrieval"},
    {"method": "GET", "path": "/api/v1/data/spatial", "params": {"domain_id": "civic_complaints"}, "name": "Spatial Data"},
    {"method": "GET", "path": "/api/v1/data/analytics", "params": {"domain_id": "civic_complaints"}, "name": "Analytics Data"},
    {"method": "GET", "path": "/api/v1/data/aggregation", "params": {"domain_id": "civic_complaints"}, "name": "Aggregation Data"},
    {"method": "POST", "path": "/api/v1/data/vector-search", "json": {"domain_id": "civic_complaints", "query": "test"}, "name": "Vector Search"},
    
    # Tool Registry API
    {"method": "GET", "path": "/api/v1/tools", "name": "List Tools"},
    
    # Ingest API
    {"method": "POST", "path": "/api/v1/ingest", "json": {"domain_id": "civic_complaints", "text": "Test report", "images": []}, "name": "Ingest Report"},
    
    # Query API
    {"method": "POST", "path": "/api/v1/query", "json": {"domain_id": "civic_complaints", "question": "What are the complaints?"}, "name": "Query"},
]

def test_endpoint(endpoint):
    """Test a single endpoint"""
    method = endpoint["method"]
    path = endpoint["path"]
    name = endpoint["name"]
    
    url = f"{API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    try:
        if method == "GET":
            params = endpoint.get("params", {})
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            json_data = endpoint.get("json", {})
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
        else:
            print(f"❌ {name}: Unsupported method {method}")
            return False
        
        status = response.status_code
        if status == 200:
            print(f"✅ {name}: {status}")
            return True
        else:
            print(f"❌ {name}: {status} - {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

def main():
    if not JWT_TOKEN:
        print("ERROR: JWT_TOKEN environment variable not set")
        print("Run: export JWT_TOKEN=$(./get_jwt_token.sh)")
        sys.exit(1)
    
    print(f"Testing API: {API_URL}")
    print(f"JWT Token: {JWT_TOKEN[:20]}...")
    print("=" * 80)
    
    results = []
    for endpoint in ENDPOINTS:
        result = test_endpoint(endpoint)
        results.append((endpoint["name"], result))
    
    print("=" * 80)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nResults: {passed}/{total} passed")
    
    # Show failed tests
    failed = [name for name, r in results if not r]
    if failed:
        print("\nFailed tests:")
        for name in failed:
            print(f"  - {name}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
