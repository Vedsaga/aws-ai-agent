#!/usr/bin/env python3
"""
Comprehensive API Test Suite
Tests all endpoints independently with detailed reporting
"""

import requests
import json
import boto3
import time
import os
from datetime import datetime

# Configuration - Load from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_REGION = os.environ.get("AWS_REGION", "us-east-1")
USERNAME = os.environ.get("TEST_USERNAME")
PASSWORD = os.environ.get("TEST_PASSWORD")

# Validate required environment variables
if not all([API_BASE_URL, COGNITO_CLIENT_ID, USERNAME, PASSWORD]):
    print("ERROR: Missing required environment variables!")
    print("Please set: API_BASE_URL, COGNITO_CLIENT_ID, TEST_USERNAME, TEST_PASSWORD")
    print("You can copy .env.example to .env and fill in the values")
    exit(1)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_test(name):
    print(f"{Colors.BOLD}TEST: {name}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - {message}")

def print_fail(message):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET} - {message}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ INFO{Colors.RESET} - {message}")

def get_cognito_token():
    """Get JWT token from Cognito"""
    print_test("Getting Cognito JWT Token")
    try:
        client = boto3.client('cognito-idp', region_name=COGNITO_REGION)
        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': USERNAME,
                'PASSWORD': PASSWORD
            }
        )
        token = response['AuthenticationResult']['IdToken']
        print_pass(f"Token obtained (length: {len(token)})")
        return token
    except Exception as e:
        print_fail(f"Failed to get token: {str(e)}")
        return None

def test_endpoint(name, method, endpoint, headers=None, data=None, expected_status=200):
    """Test a single endpoint"""
    print_test(name)
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        print_info(f"Status: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print_info(f"Response: {json.dumps(response_data, indent=2)[:200]}...")
        except:
            print_info(f"Response: {response.text[:200]}")
        
        if response.status_code == expected_status:
            print_pass(f"Expected status {expected_status}")
            return True, response
        else:
            print_fail(f"Expected {expected_status}, got {response.status_code}")
            return False, response
            
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False, None

def main():
    print_header("COMPREHENSIVE API TEST SUITE")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test User: {USERNAME}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    # Get authentication token
    print_header("AUTHENTICATION")
    token = get_cognito_token()
    if not token:
        print_fail("Cannot proceed without authentication token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: No Auth (should fail)
    print_header("TEST 1: Authentication Validation")
    success, _ = test_endpoint(
        "No Auth Header (should return 401)",
        "GET",
        "/api/v1/config?type=agent",
        headers={"Content-Type": "application/json"},
        expected_status=401
    )
    results["total"] += 1
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append({"name": "No Auth", "passed": success})
    
    # Test 2: Config API - List Agents
    print_header("TEST 2: Config API - List Agents")
    success, response = test_endpoint(
        "GET /api/v1/config?type=agent",
        "GET",
        "/api/v1/config?type=agent",
        headers=headers,
        expected_status=200
    )
    results["total"] += 1
    if success:
        results["passed"] += 1
        if response:
            data = response.json()
            if "configs" in data:
                print_info(f"Found {len(data['configs'])} agents")
                for agent in data['configs'][:3]:
                    print_info(f"  - {agent.get('agent_name')} ({agent.get('agent_id')})")
    else:
        results["failed"] += 1
    results["tests"].append({"name": "List Agents", "passed": success})
    
    # Test 3: Config API - List Domain Templates
    print_header("TEST 3: Config API - List Domain Templates")
    success, response = test_endpoint(
        "GET /api/v1/config?type=domain_template",
        "GET",
        "/api/v1/config?type=domain_template",
        headers=headers,
        expected_status=200
    )
    results["total"] += 1
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append({"name": "List Domains", "passed": success})
    
    # Test 4: Config API - Create Agent
    print_header("TEST 4: Config API - Create Custom Agent")
    agent_config = {
        "type": "agent",
        "config": {
            "agent_name": f"Test Agent {int(time.time())}",
            "agent_type": "custom",
            "system_prompt": "You are a test agent",
            "tools": ["bedrock"],
            "output_schema": {
                "result": "string",
                "confidence": "number"
            }
        }
    }
    success, response = test_endpoint(
        "POST /api/v1/config (create agent)",
        "POST",
        "/api/v1/config",
        headers=headers,
        data=agent_config,
        expected_status=201
    )
    results["total"] += 1
    created_agent_id = None
    if success and response:
        results["passed"] += 1
        data = response.json()
        created_agent_id = data.get('agent_id')
        print_info(f"Created agent: {created_agent_id}")
    else:
        results["failed"] += 1
    results["tests"].append({"name": "Create Agent", "passed": success})
    
    # Test 5: Config API - Get Specific Agent
    if created_agent_id:
        print_header("TEST 5: Config API - Get Specific Agent")
        success, response = test_endpoint(
            f"GET /api/v1/config/agent/{created_agent_id}",
            "GET",
            f"/api/v1/config/agent/{created_agent_id}",
            headers=headers,
            expected_status=200
        )
        results["total"] += 1
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["tests"].append({"name": "Get Agent", "passed": success})
    
    # Test 6: Config API - Update Agent
    if created_agent_id:
        print_header("TEST 6: Config API - Update Agent")
        update_config = {
            "config": {
                "agent_name": f"Updated Test Agent {int(time.time())}",
                "system_prompt": "Updated prompt"
            }
        }
        success, response = test_endpoint(
            f"PUT /api/v1/config/agent/{created_agent_id}",
            "PUT",
            f"/api/v1/config/agent/{created_agent_id}",
            headers=headers,
            data=update_config,
            expected_status=200
        )
        results["total"] += 1
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["tests"].append({"name": "Update Agent", "passed": success})
    
    # Test 7: Config API - Delete Agent
    if created_agent_id:
        print_header("TEST 7: Config API - Delete Agent")
        success, response = test_endpoint(
            f"DELETE /api/v1/config/agent/{created_agent_id}",
            "DELETE",
            f"/api/v1/config/agent/{created_agent_id}",
            headers=headers,
            expected_status=200
        )
        results["total"] += 1
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["tests"].append({"name": "Delete Agent", "passed": success})
    
    # Test 8: Ingest API - Submit Report
    print_header("TEST 8: Ingest API - Submit Report")
    ingest_data = {
        "domain_id": "civic_complaints",
        "text": f"Test report submitted at {datetime.now().isoformat()}: Broken streetlight on Main Street"
    }
    success, response = test_endpoint(
        "POST /api/v1/ingest",
        "POST",
        "/api/v1/ingest",
        headers=headers,
        data=ingest_data,
        expected_status=202
    )
    results["total"] += 1
    if success and response:
        results["passed"] += 1
        data = response.json()
        print_info(f"Job ID: {data.get('job_id')}")
    else:
        results["failed"] += 1
    results["tests"].append({"name": "Submit Report", "passed": success})
    
    # Test 9: Query API - Ask Question
    print_header("TEST 9: Query API - Ask Question")
    query_data = {
        "domain_id": "civic_complaints",
        "question": "What are the most common complaints this month?"
    }
    success, response = test_endpoint(
        "POST /api/v1/query",
        "POST",
        "/api/v1/query",
        headers=headers,
        data=query_data,
        expected_status=202
    )
    results["total"] += 1
    if success and response:
        results["passed"] += 1
        data = response.json()
        print_info(f"Job ID: {data.get('job_id')}")
    else:
        results["failed"] += 1
    results["tests"].append({"name": "Ask Question", "passed": success})
    
    # Test 10: Tools API - List Tools
    print_header("TEST 10: Tools API - List Tools")
    success, response = test_endpoint(
        "GET /api/v1/tools",
        "GET",
        "/api/v1/tools",
        headers=headers,
        expected_status=200
    )
    results["total"] += 1
    if success and response:
        results["passed"] += 1
        data = response.json()
        if "tools" in data:
            print_info(f"Found {len(data['tools'])} tools")
    else:
        results["failed"] += 1
    results["tests"].append({"name": "List Tools", "passed": success})
    
    # Test 11: Data API - Retrieve Data
    print_header("TEST 11: Data API - Retrieve Data")
    success, response = test_endpoint(
        "GET /api/v1/data?type=retrieval",
        "GET",
        "/api/v1/data?type=retrieval",
        headers=headers,
        expected_status=200
    )
    results["total"] += 1
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    results["tests"].append({"name": "Retrieve Data", "passed": success})
    
    # Print Summary
    print_header("TEST SUMMARY")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.RESET}")
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
    for test in results["tests"]:
        status = f"{Colors.GREEN}✓{Colors.RESET}" if test["passed"] else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status} {test['name']}")
    
    # Check demo readiness
    print_header("DEMO READINESS CHECK")
    critical_tests = ["List Agents", "Create Agent", "Submit Report", "Ask Question"]
    critical_passed = sum(1 for t in results["tests"] if t["name"] in critical_tests and t["passed"])
    
    if critical_passed == len(critical_tests):
        print(f"{Colors.GREEN}{Colors.BOLD}✓ READY FOR DEMO{Colors.RESET}")
        print("All critical endpoints are working!")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ NOT READY{Colors.RESET}")
        print(f"Only {critical_passed}/{len(critical_tests)} critical tests passed")
    
    return results

if __name__ == "__main__":
    main()
