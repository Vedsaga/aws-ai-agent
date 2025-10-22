#!/usr/bin/env python3
"""
Quick test for Data API authorization
"""
import requests
import json
import os
import time

API_BASE_URL = os.environ.get("API_BASE_URL")
TOKEN = None

def get_token():
    """Get auth token from Cognito"""
    import boto3
    
    cognito = boto3.client('cognito-idp', region_name=os.environ.get("AWS_REGION", "us-east-1"))
    response = cognito.initiate_auth(
        ClientId=os.environ.get("COGNITO_CLIENT_ID"),
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': os.environ.get("TEST_USERNAME"),
            'PASSWORD': os.environ.get("TEST_PASSWORD")
        }
    )
    return response['AuthenticationResult']['IdToken']

def make_request(method, endpoint, data=None):
    """Make HTTP request"""
    global TOKEN
    if not TOKEN:
        TOKEN = get_token()
    
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"Request: {method} {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    
    return response

print("=" * 80)
print("DATA API AUTHORIZATION TEST")
print("=" * 80)

# First create a domain to test with
print("\n1. Creating test domain...")
domain_id = f"test_domain_{int(time.time())}"
domain_data = {
    "domain_id": domain_id,
    "domain_name": f"Test Domain {int(time.time())}",
    "description": "Test domain for data API",
    "ingestion_playbook": {
        "agent_execution_graph": {
            "nodes": ["builtin-ingestion-geo"],
            "edges": []
        }
    },
    "query_playbook": {
        "agent_execution_graph": {
            "nodes": ["builtin-query-who"],
            "edges": []
        }
    },
    "management_playbook": {
        "agent_execution_graph": {
            "nodes": ["builtin-management-task-assigner"],
            "edges": []
        }
    }
}
response = make_request("POST", "/api/v1/domains", domain_data)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    domain_id = response.json()['domain_id']
    print(f"✓ Created domain: {domain_id}")
else:
    print(f"✗ Failed to create domain")
    print(f"Response: {response.text}")
    exit(1)

# Test Geo Data API
print(f"\n2. Testing GET /api/v1/data/geo?domain_id={domain_id}")
response = make_request("GET", f"/api/v1/data/geo?domain_id={domain_id}")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✓✓✓ SUCCESS! Geo data API working")
elif response.status_code == 403:
    print("\n✗✗✗ FAILURE! 403 Forbidden - Authorization issue")
    print("Error details:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"\n⚠ Unexpected status: {response.status_code}")

# Test Aggregated Data API
print(f"\n3. Testing GET /api/v1/data/aggregated?domain_id={domain_id}&group_by=status")
response = make_request("GET", f"/api/v1/data/aggregated?domain_id={domain_id}&group_by=status")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✓✓✓ SUCCESS! Aggregated data API working")
elif response.status_code == 403:
    print("\n✗✗✗ FAILURE! 403 Forbidden - Authorization issue")
else:
    print(f"\n⚠ Unexpected status: {response.status_code}")

# Cleanup
print("\n4. Cleaning up...")
response = make_request("DELETE", f"/api/v1/domains/{domain_id}", None)
print(f"   Deleted domain: {response.status_code}")

print("\n" + "=" * 80)
