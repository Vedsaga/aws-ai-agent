#!/usr/bin/env python3
"""
Quick test for circular dependency detection
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
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    
    return response

print("=" * 80)
print("CIRCULAR DEPENDENCY TEST")
print("=" * 80)

# Step 1: Create base agent
print("\n1. Creating base agent...")
base_data = {
    "agent_name": f"Test Base {int(time.time())}",
    "agent_class": "query",
    "system_prompt": "Base agent",
    "agent_dependencies": [],
    "max_output_keys": 5,
    "output_schema": {"result": {"type": "string"}},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", base_data)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    base_agent_id = response.json()['agent_id']
    print(f"✓ Created base agent: {base_agent_id}")
else:
    print(f"✗ Failed to create base agent: {response.text}")
    exit(1)

# Step 2: Create dependent1 (depends on base)
print("\n2. Creating dependent1 (depends on base)...")
dep1_data = {
    "agent_name": f"Test Dep1 {int(time.time())}",
    "agent_class": "query",
    "system_prompt": "Dependent 1",
    "agent_dependencies": [base_agent_id],
    "max_output_keys": 5,
    "output_schema": {"result": {"type": "string"}},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", dep1_data)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    dep1_id = response.json()['agent_id']
    print(f"✓ Created dependent1: {dep1_id}")
else:
    print(f"✗ Failed to create dependent1: {response.text}")
    exit(1)

# Step 3: Create dependent2 (depends on dependent1)
print("\n3. Creating dependent2 (depends on dependent1)...")
dep2_data = {
    "agent_name": f"Test Dep2 {int(time.time())}",
    "agent_class": "query",
    "system_prompt": "Dependent 2",
    "agent_dependencies": [dep1_id],
    "max_output_keys": 5,
    "output_schema": {"result": {"type": "string"}},
    "enabled": True
}
response = make_request("POST", "/api/v1/agents", dep2_data)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    dep2_id = response.json()['agent_id']
    print(f"✓ Created dependent2: {dep2_id}")
else:
    print(f"✗ Failed to create dependent2: {response.text}")
    exit(1)

# Step 4: Try to update base to depend on dependent2 (creates cycle)
print("\n4. CRITICAL TEST: Updating base to depend on dependent2 (should fail)...")
print(f"   This creates cycle: {base_agent_id} -> {dep2_id} -> {dep1_id} -> {base_agent_id}")
update_data = {
    "agent_dependencies": [dep2_id]
}
response = make_request("PUT", f"/api/v1/agents/{base_agent_id}", update_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 400:
    error_data = response.json()
    error_msg = (error_data.get('error', '') or error_data.get('message', '')).lower()
    if 'circular' in error_msg or 'cycle' in error_msg or 'dag' in error_msg:
        print(f"\n✓✓✓ SUCCESS! API correctly rejected circular dependency")
        print(f"    Error message: {error_msg[:100]}")
    else:
        print(f"\n⚠ WARNING: Rejected but error message unclear: {error_msg[:100]}")
else:
    print(f"\n✗✗✗ FAILURE! API accepted circular dependency (status {response.status_code})")
    print(f"    This is a MAJOR BUG!")

# Cleanup
print("\n5. Cleaning up...")
for agent_id in [dep2_id, dep1_id, base_agent_id]:
    response = make_request("DELETE", f"/api/v1/agents/{agent_id}")
    print(f"   Deleted {agent_id}: {response.status_code}")

print("\n" + "=" * 80)
