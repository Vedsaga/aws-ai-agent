#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Tests all endpoints with real-world scenarios
"""

import requests
import json
import sys
import os
import subprocess
import time
from datetime import datetime

# API Configuration
API_URL = "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# Test Results Tracking
test_results = {"total": 0, "passed": 0, "failed": 0, "tests": []}


def get_jwt_token():
    """Get JWT token from Cognito"""
    print("🔐 Getting JWT token...")
    try:
        result = subprocess.run(
            [
                "aws",
                "cognito-idp",
                "initiate-auth",
                "--auth-flow",
                "USER_PASSWORD_AUTH",
                "--client-id",
                "6gobbpage9af3nd7ahm3lchkct",
                "--auth-parameters",
                "USERNAME=testuser,PASSWORD=TestPassword123!",
                "--region",
                "us-east-1",
                "--query",
                "AuthenticationResult.IdToken",
                "--output",
                "text",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        token = result.stdout.strip()
        if token and len(token) > 100:
            print(f"✓ Got JWT token ({len(token)} chars)")
            return token
        else:
            print(f"✗ Failed to get token: {result.stderr}")
            return None
    except Exception as e:
        print(f"✗ Error getting token: {e}")
        return None


def test_api(name, method, endpoint, data=None, expected_status=200, description=""):
    """Test an API endpoint"""
    global test_results

    test_results["total"] += 1
    test_num = test_results["total"]

    print(f"\n{'=' * 80}")
    print(f"TEST {test_num}: {name}")
    print(f"{'=' * 80}")
    if description:
        print(f"Description: {description}")
    print(f"Method: {method} {endpoint}")
    if data:
        print(f"Payload: {json.dumps(data, indent=2)[:200]}")

    try:
        url = f"{API_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json",
        }

        start_time = time.time()

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)

        elapsed = time.time() - start_time

        print(f"Status: {response.status_code} (expected: {expected_status})")
        print(f"Response Time: {elapsed:.2f}s")

        # Parse response
        try:
            response_data = response.json()
            print(
                f"Response Preview: {json.dumps(response_data, indent=2, default=str)[:500]}"
            )
        except:
            print(f"Response Text: {response.text[:500]}")
            response_data = {}

        # Check status
        passed = response.status_code == expected_status

        if passed:
            print(f"✓ PASS")
            test_results["passed"] += 1
        else:
            print(f"✗ FAIL - Expected {expected_status}, got {response.status_code}")
            test_results["failed"] += 1

        # Store result
        test_results["tests"].append(
            {
                "num": test_num,
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status": response.status_code,
                "expected": expected_status,
                "passed": passed,
                "response_time": elapsed,
                "response_preview": str(response_data)[:200]
                if response_data
                else response.text[:200],
            }
        )

        return passed, response_data

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        test_results["failed"] += 1
        test_results["tests"].append(
            {
                "num": test_num,
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status": "ERROR",
                "expected": expected_status,
                "passed": False,
                "error": str(e),
            }
        )
        return False, {}


# Get JWT Token
JWT_TOKEN = get_jwt_token()
if not JWT_TOKEN:
    print("\n❌ Cannot proceed without JWT token")
    sys.exit(1)

print("\n" + "=" * 80)
print("STARTING API TESTS")
print("=" * 80)

# =============================================================================
# CONFIG API TESTS
# =============================================================================
print("\n" + "=" * 80)
print("CONFIG API - Core Configuration Management")
print("=" * 80)

# Test 1: List Agents
test_api(
    "List All Agents",
    "GET",
    "/api/v1/config?type=agent",
    expected_status=200,
    description="Get all available agents (built-in and custom)",
)

# Test 2: List Domain Templates
test_api(
    "List Domain Templates",
    "GET",
    "/api/v1/config?type=domain_template",
    expected_status=200,
    description="Get all configured domain templates",
)

# Test 3: List Playbooks
test_api(
    "List Playbooks",
    "GET",
    "/api/v1/config?type=playbook",
    expected_status=200,
    description="Get all agent playbooks",
)

# Test 4: Create Custom Agent
passed, response = test_api(
    "Create Custom Agent",
    "POST",
    "/api/v1/config",
    data={
        "type": "agent",
        "config": {
            "agent_name": "Test Custom Agent",
            "agent_type": "custom",
            "system_prompt": "You are a helpful assistant that analyzes civic complaints.",
            "tools": ["bedrock"],
            "output_schema": {
                "analysis": "string",
                "confidence": "number",
                "category": "string",
            },
        },
    },
    expected_status=201,
    description="Create a new custom agent",
)

created_agent_id = None
if passed and response:
    created_agent_id = response.get("config_key") or response.get("agent_id")
    print(f"Created agent ID: {created_agent_id}")

# Test 5: Get Specific Agent
if created_agent_id:
    test_api(
        "Get Specific Agent",
        "GET",
        f"/api/v1/config/agent/{created_agent_id}",
        expected_status=200,
        description="Retrieve details of created agent",
    )

# Test 6: Update Agent
if created_agent_id:
    test_api(
        "Update Agent",
        "PUT",
        f"/api/v1/config/agent/{created_agent_id}",
        data={
            "config": {
                "system_prompt": "Updated prompt for the agent",
                "agent_name": "Updated Custom Agent",
            }
        },
        expected_status=200,
        description="Update agent configuration",
    )

# Test 7: Create Domain Template
passed, response = test_api(
    "Create Domain Template",
    "POST",
    "/api/v1/config",
    data={
        "type": "domain_template",
        "config": {
            "template_name": "Test Domain",
            "domain_id": "test_domain_" + str(int(time.time())),
            "description": "Test domain for API testing",
            "ingest_agent_ids": ["geo_agent", "temporal_agent"],
            "query_agent_ids": ["what_agent", "where_agent"],
        },
    },
    expected_status=201,
    description="Create a new domain template",
)

# =============================================================================
# INGEST API TESTS
# =============================================================================
print("\n" + "=" * 80)
print("INGEST API - Data Ingestion & Report Submission")
print("=" * 80)

# Test 8: Submit Simple Report
passed, response = test_api(
    "Submit Simple Report",
    "POST",
    "/api/v1/ingest",
    data={
        "domain_id": "civic_complaints",
        "text": "There is a large pothole on Main Street near the library intersection. It has been there for over two weeks and is causing traffic issues.",
    },
    expected_status=202,
    description="Submit a basic civic complaint report",
)

job_id_1 = response.get("job_id") if passed else None

# Test 9: Submit Report with Priority
passed, response = test_api(
    "Submit High Priority Report",
    "POST",
    "/api/v1/ingest",
    data={
        "domain_id": "civic_complaints",
        "text": "Emergency: Gas leak reported on Elm Street near apartment building #45. Strong odor detected by multiple residents.",
        "priority": "high",
    },
    expected_status=202,
    description="Submit high-priority emergency report",
)

# Test 10: Submit Report with Contact Info
test_api(
    "Submit Report with Contact",
    "POST",
    "/api/v1/ingest",
    data={
        "domain_id": "civic_complaints",
        "text": "The traffic light at Oak and 5th Avenue has been malfunctioning. It stays red in all directions for extended periods.",
        "reporter_contact": "citizen@example.com",
        "source": "mobile_app",
    },
    expected_status=202,
    description="Submit report with reporter contact information",
)

# Test 11: Submit Complex Infrastructure Report
test_api(
    "Submit Infrastructure Report",
    "POST",
    "/api/v1/ingest",
    data={
        "domain_id": "civic_complaints",
        "text": "Multiple streetlights are out on Park Avenue between 1st and 5th streets. This has been ongoing for 3 days, making the area unsafe at night. Residents are concerned about security.",
    },
    expected_status=202,
    description="Submit detailed infrastructure complaint",
)

# Test 12: Error - Missing Domain ID
test_api(
    "Error: Missing Domain ID",
    "POST",
    "/api/v1/ingest",
    data={"text": "Test report without domain"},
    expected_status=400,
    description="Expect validation error for missing domain_id",
)

# Test 13: Error - Missing Text
test_api(
    "Error: Missing Text",
    "POST",
    "/api/v1/ingest",
    data={"domain_id": "civic_complaints"},
    expected_status=400,
    description="Expect validation error for missing text",
)

# Test 14: Error - Text Too Long
test_api(
    "Error: Text Too Long",
    "POST",
    "/api/v1/ingest",
    data={"domain_id": "civic_complaints", "text": "A" * 10001},
    expected_status=400,
    description="Expect validation error for text exceeding 10000 chars",
)

# =============================================================================
# QUERY API TESTS
# =============================================================================
print("\n" + "=" * 80)
print("QUERY API - Natural Language Questions")
print("=" * 80)

# Test 15: Simple What Query
passed, response = test_api(
    "What Query - Common Complaints",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "What are the most common types of complaints?",
    },
    expected_status=202,
    description="Ask 'what' interrogative question",
)

# Test 16: Where Query
test_api(
    "Where Query - Geographic Distribution",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "Where are most infrastructure complaints located?",
    },
    expected_status=202,
    description="Ask 'where' interrogative question",
)

# Test 17: When Query
test_api(
    "When Query - Time Analysis",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "When do most complaints get reported?",
    },
    expected_status=202,
    description="Ask 'when' interrogative question",
)

# Test 18: How Many Query
test_api(
    "How Many Query - Count Analysis",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "How many pothole complaints were reported this month?",
    },
    expected_status=202,
    description="Ask 'how many' interrogative question",
)

# Test 19: Query with Date Filter
test_api(
    "Query with Date Range Filter",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "What complaints were reported recently?",
        "filters": {"date_range": {"start": "2025-01-01", "end": "2025-01-31"}},
    },
    expected_status=202,
    description="Query with temporal filter",
)

# Test 20: Query with Category Filter
test_api(
    "Query with Category Filter",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "Summarize the infrastructure issues",
        "filters": {"category": "infrastructure"},
    },
    expected_status=202,
    description="Query with category filter",
)

# Test 21: Complex Multi-Agent Query
test_api(
    "Complex Multi-Agent Query",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "What are the top 5 complaint categories in downtown during the last 30 days, and where are they concentrated?",
    },
    expected_status=202,
    description="Complex query requiring multiple agents",
)

# Test 22: Query with Visualization Request
test_api(
    "Query with Visualizations",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": "civic_complaints",
        "question": "Show me a breakdown of complaints by type",
        "include_visualizations": True,
    },
    expected_status=202,
    description="Request query results with visualizations",
)

# Test 23: Error - Missing Domain ID
test_api(
    "Error: Missing Domain ID",
    "POST",
    "/api/v1/query",
    data={"question": "Test question without domain"},
    expected_status=400,
    description="Expect validation error for missing domain_id",
)

# Test 24: Error - Missing Question
test_api(
    "Error: Missing Question",
    "POST",
    "/api/v1/query",
    data={"domain_id": "civic_complaints"},
    expected_status=400,
    description="Expect validation error for missing question",
)

# Test 25: Error - Question Too Long
test_api(
    "Error: Question Too Long",
    "POST",
    "/api/v1/query",
    data={"domain_id": "civic_complaints", "question": "A" * 1001},
    expected_status=400,
    description="Expect validation error for question exceeding 1000 chars",
)

# =============================================================================
# TOOLS API TESTS (if available)
# =============================================================================
print("\n" + "=" * 80)
print("TOOLS API - Tool Registry")
print("=" * 80)

# Test 26: List Available Tools
test_api(
    "List Available Tools",
    "GET",
    "/api/v1/tools",
    expected_status=200,
    description="Get all registered tools in the system",
)

# =============================================================================
# DATA API TESTS (if available)
# =============================================================================
print("\n" + "=" * 80)
print("DATA API - Data Retrieval")
print("=" * 80)

# Test 27: Retrieve Data
test_api(
    "Retrieve Incident Data",
    "GET",
    "/api/v1/data?domain_id=civic_complaints&limit=10",
    expected_status=200,
    description="Retrieve stored incident data",
)

# =============================================================================
# EDGE CASES & ERROR HANDLING
# =============================================================================
print("\n" + "=" * 80)
print("EDGE CASES & ERROR HANDLING")
print("=" * 80)

# Test 28: Unauthorized - No Token
print(f"\n{'=' * 80}")
print(f"TEST {test_results['total'] + 1}: Unauthorized Access - No Token")
print(f"{'=' * 80}")
test_results["total"] += 1
try:
    response = requests.get(
        f"{API_URL}/api/v1/config?type=agent",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    passed = response.status_code == 401
    print(f"Status: {response.status_code} (expected: 401)")
    if passed:
        print("✓ PASS - Correctly rejected unauthorized request")
        test_results["passed"] += 1
    else:
        print("✗ FAIL - Should return 401 for missing token")
        test_results["failed"] += 1
except Exception as e:
    print(f"✗ ERROR: {e}")
    test_results["failed"] += 1

# Test 29: Invalid Config Type
test_api(
    "Error: Invalid Config Type",
    "GET",
    "/api/v1/config?type=invalid_type",
    expected_status=200,
    description="Query with invalid type should return empty list",
)

# Test 30: Delete Agent (if created)
if created_agent_id:
    test_api(
        "Delete Custom Agent",
        "DELETE",
        f"/api/v1/config/agent/{created_agent_id}",
        expected_status=200,
        description="Delete previously created custom agent",
    )

# =============================================================================
# END-TO-END SCENARIOS
# =============================================================================
print("\n" + "=" * 80)
print("END-TO-END SCENARIOS")
print("=" * 80)

# Scenario 1: Complete Civic Complaint Workflow
print("\n📋 SCENARIO 1: Civic Complaint Workflow")
print("-" * 80)

print("Step 1: Create custom domain...")
passed, domain_response = test_api(
    "E2E: Create Domain",
    "POST",
    "/api/v1/config",
    data={
        "type": "domain_template",
        "config": {
            "template_name": "E2E Test Domain",
            "domain_id": "e2e_test_" + str(int(time.time())),
            "description": "End-to-end testing domain",
            "ingest_agent_ids": ["geo_agent", "temporal_agent", "category_agent"],
            "query_agent_ids": ["what_agent", "where_agent", "when_agent"],
        },
    },
    expected_status=201,
)

e2e_domain_id = (
    domain_response.get("domain_id", "civic_complaints")
    if passed
    else "civic_complaints"
)

print("\nStep 2: Submit multiple reports...")
reports = [
    "Broken streetlight on Oak Street",
    "Pothole at Main and 5th intersection",
    "Graffiti on public building at City Hall",
]

for i, report_text in enumerate(reports):
    test_api(
        f"E2E: Submit Report {i + 1}",
        "POST",
        "/api/v1/ingest",
        data={"domain_id": e2e_domain_id, "text": report_text},
        expected_status=202,
    )
    time.sleep(0.5)

print("\nStep 3: Query the data...")
test_api(
    "E2E: Query Submitted Reports",
    "POST",
    "/api/v1/query",
    data={
        "domain_id": e2e_domain_id,
        "question": "What types of issues were reported?",
    },
    expected_status=202,
)

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("TEST EXECUTION SUMMARY")
print("=" * 80)

print(f"\nTotal Tests: {test_results['total']}")
print(f"✓ Passed: {test_results['passed']}")
print(f"✗ Failed: {test_results['failed']}")
print(f"Success Rate: {(test_results['passed'] / test_results['total'] * 100):.1f}%")

# Print failed tests
if test_results["failed"] > 0:
    print("\n" + "=" * 80)
    print("FAILED TESTS")
    print("=" * 80)
    for test in test_results["tests"]:
        if not test.get("passed", False):
            print(f"\n❌ Test {test['num']}: {test['name']}")
            print(f"   Method: {test['method']} {test['endpoint']}")
            print(
                f"   Status: {test.get('status', 'N/A')} (expected: {test['expected']})"
            )
            if "error" in test:
                print(f"   Error: {test['error']}")

# Export results to JSON
results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(results_file, "w") as f:
    json.dump(test_results, f, indent=2, default=str)
print(f"\n📄 Detailed results saved to: {results_file}")

# Print API Status
print("\n" + "=" * 80)
print("API ENDPOINT STATUS")
print("=" * 80)

api_status = {
    "Config API": 0,
    "Ingest API": 0,
    "Query API": 0,
    "Tools API": 0,
    "Data API": 0,
}

for test in test_results["tests"]:
    if test.get("passed"):
        if "/config" in test["endpoint"]:
            api_status["Config API"] += 1
        elif "/ingest" in test["endpoint"]:
            api_status["Ingest API"] += 1
        elif "/query" in test["endpoint"]:
            api_status["Query API"] += 1
        elif "/tools" in test["endpoint"]:
            api_status["Tools API"] += 1
        elif "/data" in test["endpoint"]:
            api_status["Data API"] += 1

print("\nWorking Endpoints:")
for api, count in api_status.items():
    status = "✓" if count > 0 else "✗"
    print(f"  {status} {api}: {count} tests passed")

# Exit code
exit_code = 0 if test_results["failed"] == 0 else 1
print(f"\n{'=' * 80}")
if exit_code == 0:
    print("✓ ALL TESTS PASSED - SYSTEM READY FOR DEMO")
else:
    print(f"⚠ {test_results['failed']} TEST(S) FAILED - REVIEW REQUIRED")
print("=" * 80)

sys.exit(exit_code)
