#!/usr/bin/env python3
"""
Quick test for validation error handling
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
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    
    return response

print("=" * 80)
print("VALIDATION ERROR TESTS")
print("=" * 80)

# Test 1: Invalid agent class
print("\n1. Testing invalid agent_class (should return 400)...")
invalid_data = {
    "agent_name": f"Invalid Class Test {int(time.time())}",
    "agent_class": "invalid_class",
    "system_prompt": "Test",
    "agent_dependencies": [],
    "max_output_keys": 5,
    "output_schema": {"result": {"type": "string"}},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", invalid_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
if response.status_code == 400:
    print("✓ Correctly rejected invalid agent_class")
else:
    print(f"✗ Expected 400, got {response.status_code}")

# Test 2: > 5 output keys
print("\n2. Testing > 5 output keys (should return 400)...")
invalid_data = {
    "agent_name": f"Too Many Keys Test {int(time.time())}",
    "agent_class": "query",
    "system_prompt": "Test",
    "agent_dependencies": [],
    "max_output_keys": 5,
    "output_schema": {f"key_{i}": {"type": "string"} for i in range(6)},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", invalid_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
if response.status_code == 400:
    print("✓ Correctly rejected > 5 output keys")
else:
    print(f"✗ Expected 400, got {response.status_code}")

# Test 3: Get non-existent agent (should return 404)
print("\n3. Testing GET non-existent agent (should return 404)...")
response = make_request("GET", "/api/v1/agents/non-existent-agent-id", None)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
if response.status_code == 404:
    print("✓ Correctly returned 404")
else:
    print(f"✗ Expected 404, got {response.status_code}")

# Test 4: Non-existent dependency (should return 400)
print("\n4. Testing non-existent dependency (should return 400)...")
invalid_data = {
    "agent_name": f"Invalid Dep Test {int(time.time())}",
    "agent_class": "query",
    "system_prompt": "Test",
    "agent_dependencies": ["non-existent-agent-id"],
    "max_output_keys": 5,
    "output_schema": {"result": {"type": "string"}},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", invalid_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
if response.status_code == 400:
    print("✓ Correctly rejected non-existent dependency")
else:
    print(f"✗ Expected 400, got {response.status_code}")

# Test 5: Report without required field
print("\n5. Testing report without required field (should return 400)...")
invalid_data = {
    "domain_id": "test_domain",
    "source": "test",
    # Missing 'text' field
}
response = make_request("POST", "/api/v1/reports", invalid_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
if response.status_code == 400:
    print("✓ Correctly rejected report without text")
else:
    print(f"✗ Expected 400, got {response.status_code}")

print("\n" + "=" * 80)
