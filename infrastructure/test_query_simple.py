#!/usr/bin/env python3
"""
Simple test to submit a query and check if orchestrator runs
"""
import requests
import json
import time
import os

# Load from .env file manually
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
except:
    pass

API_URL = env_vars.get('API_URL', 'https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1')
TOKEN = env_vars.get('JWT_TOKEN')

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Use an existing domain with builtin agents
domain_id = "test_domain_1761149019"  # From previous test run
session_id = "sess_aa370fe6"  # From previous test run

print(f"Testing query submission to domain: {domain_id}")
print(f"API URL: {API_URL}")

# Submit query
query_data = {
    "session_id": session_id,
    "domain_id": domain_id,
    "question": "What incidents have been reported?"
}

print("\n1. Submitting query...")
response = requests.post(
    f"{API_URL}/api/v1/queries",
    headers=headers,
    json=query_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 202:
    query_id = response.json()['query_id']
    print(f"\n2. Query submitted: {query_id}")
    print("3. Polling for results...")
    
    for i in range(20):  # Poll for 60 seconds
        time.sleep(3)
        result = requests.get(
            f"{API_URL}/api/v1/queries/{query_id}",
            headers=headers
        )
        
        data = result.json()
        status = data.get('status')
        exec_log = data.get('execution_log', [])
        refs = data.get('references_used', [])
        
        print(f"  Poll {i+1}: status={status}, exec_log_entries={len(exec_log)}, references={len(refs)}")
        
        if status == 'completed':
            print("\n✅ Query completed!")
            print(f"Execution log entries: {len(exec_log)}")
            print(f"References used: {refs}")
            if exec_log:
                print("\nFirst agent output:")
                print(json.dumps(exec_log[0], indent=2))
            break
        elif status == 'failed':
            print("\n❌ Query failed!")
            print(json.dumps(data, indent=2))
            break
    else:
        print("\n⏱️ Timeout - query still processing")
        print(f"Final status: {status}")
        print(f"Full response: {json.dumps(data, indent=2)}")
