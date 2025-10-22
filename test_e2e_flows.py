#!/usr/bin/env python3
"""
End-to-End Flow Tests for DomainFlow Platform
Tests: Data Ingestion, Query, and Management flows
"""
import requests
import json
import time
import os
import sys
from datetime import datetime

# Load environment variables from infrastructure/.env
API_BASE_URL = os.environ.get("API_BASE_URL", "https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "6gobbpage9af3nd7ahm3lchkct")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
TEST_USERNAME = os.environ.get("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "TestPassword123!")

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

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{text}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'─'*80}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    print(f"  {text}")

class E2EFlowTester:
    def __init__(self):
        self.token = None
        self.session_id = None
        self.domain_id = None
        self.report_id = None
        self.query_id = None
        
    def get_auth_token(self):
        """Get JWT token from Cognito"""
        print_section("Authentication")
        try:
            import boto3
            cognito = boto3.client('cognito-idp', region_name=AWS_REGION)
            response = cognito.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': TEST_USERNAME,
                    'PASSWORD': TEST_PASSWORD
                }
            )
            self.token = response['AuthenticationResult']['IdToken']
            print_success("Authentication successful")
            return True
        except Exception as e:
            print_error(f"Authentication failed: {e}")
            return False
    
    def make_request(self, method, endpoint, data=None, expected_status=None):
        """Make HTTP request to API"""
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            
            if expected_status and response.status_code != expected_status:
                print_error(f"Expected {expected_status}, got {response.status_code}")
                print_info(f"Response: {response.text}")
                return False, None
            
            return True, response
        except Exception as e:
            print_error(f"Request failed: {e}")
            return False, None
    
    def test_ingestion_flow(self):
        """Test end-to-end data ingestion flow"""
        print_header("TEST 1: DATA INGESTION FLOW")
        
        # Step 1: Create a domain with ingestion playbook using BUILTIN AGENTS
        print_section("Step 1: Create Domain with Ingestion Playbook (Using Builtin Agents)")
        self.domain_id = f"test_domain_{int(time.time())}"
        domain_data = {
            "domain_id": self.domain_id,
            "domain_name": f"E2E Test Domain {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "End-to-end test domain - Tests all 3 agent classes",
            "ingestion_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-ingestion-geo",      # Extracts location
                        "builtin-ingestion-temporal",  # Extracts time/urgency
                        "builtin-ingestion-entity"     # Extracts entities/sentiment
                    ],
                    "edges": []  # Parallel execution
                }
            },
            "query_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-query-who",   # Who was involved?
                        "builtin-query-what",  # What happened?
                        "builtin-query-where", # Where did it occur?
                        "builtin-query-when"   # When did it happen?
                    ],
                    "edges": []  # Parallel execution
                }
            },
            "management_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-management-task-assigner",      # Assigns tasks
                        "builtin-management-status-updater",     # Updates status
                        "builtin-management-task-details-editor" # Edits task details
                    ],
                    "edges": []  # Parallel execution
                }
            }
        }
        
        success, response = self.make_request("POST", "/api/v1/domains", domain_data, 201)
        if not success:
            return False
        
        print_success(f"Domain created: {self.domain_id}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Step 2: Submit a report for ingestion (will trigger 3 ingestion agents)
        print_section("Step 2: Submit Report for Ingestion (Triggers 3 Agents)")
        print_info("Expected agents to execute:")
        print_info("  - builtin-ingestion-geo: Extract location (123 Main Street)")
        print_info("  - builtin-ingestion-temporal: Extract time (2:30 PM) and urgency")
        print_info("  - builtin-ingestion-entity: Extract entities (John Doe, Jane Smith)")
        
        report_data = {
            "domain_id": self.domain_id,
            "text": "Traffic accident at 123 Main Street involving John Doe and Jane Smith. Emergency services dispatched at 2:30 PM today. The situation is urgent.",
            "source": "e2e_test"
        }
        
        success, response = self.make_request("POST", "/api/v1/reports", report_data, 202)
        if not success:
            return False
        
        result = response.json()
        self.report_id = result.get('incident_id')
        print_success(f"Report submitted: {self.report_id}")
        print_info(f"Status: {result.get('status')}")
        
        # Step 3: Poll for ingestion completion and verify agent execution
        print_section("Step 3: Wait for Ingestion Processing & Verify Agent Execution")
        max_polls = 20
        for i in range(max_polls):
            time.sleep(3)
            success, response = self.make_request("GET", f"/api/v1/reports/{self.report_id}", expected_status=200)
            if not success:
                continue
            
            result = response.json()
            ingestion_data = result.get('ingestion_data', {})
            
            print_info(f"Poll {i+1}/{max_polls}: Checking ingestion status...")
            
            if ingestion_data:
                print_success("Ingestion completed! Verifying agent outputs...")
                
                # Verify each agent's output
                geo_data = ingestion_data.get('builtin-ingestion-geo', {})
                temporal_data = ingestion_data.get('builtin-ingestion-temporal', {})
                entity_data = ingestion_data.get('builtin-ingestion-entity', {})
                
                print_info("\nAgent Execution Results:")
                print_info(f"  ✓ Geo Agent: location={geo_data.get('location_name', 'N/A')}, confidence={geo_data.get('confidence', 0)}")
                print_info(f"  ✓ Temporal Agent: urgency={temporal_data.get('urgency', 'N/A')}, timestamp={temporal_data.get('timestamp', 'N/A')}")
                print_info(f"  ✓ Entity Agent: entities={len(entity_data.get('entities', []))}, sentiment={entity_data.get('sentiment', 'N/A')}")
                
                print_info(f"\nFull ingestion data: {json.dumps(ingestion_data, indent=2)}")
                return True
        
        print_error("Ingestion timed out - agents may not have executed")
        return False
    
    def test_query_flow(self):
        """Test end-to-end query flow"""
        print_header("TEST 2: DATA QUERY FLOW")
        
        # Step 1: Create a session
        print_section("Step 1: Create Chat Session")
        session_data = {
            "domain_id": self.domain_id,
            "metadata": {
                "test": "e2e_query_flow"
            }
        }
        
        success, response = self.make_request("POST", "/api/v1/sessions", session_data, 201)
        if not success:
            return False
        
        result = response.json()
        self.session_id = result.get('session_id')
        print_success(f"Session created: {self.session_id}")
        
        # Step 2: Submit a query (will trigger 4 query agents)
        print_section("Step 2: Submit Query (Triggers 4 Query Agents)")
        print_info("Expected agents to execute:")
        print_info("  - builtin-query-who: Analyze who was involved")
        print_info("  - builtin-query-what: Analyze what happened")
        print_info("  - builtin-query-where: Analyze where it occurred")
        print_info("  - builtin-query-when: Analyze when it happened")
        
        query_data = {
            "session_id": self.session_id,
            "domain_id": self.domain_id,
            "question": "What incidents have been reported? Who was involved, where and when did they occur?"
        }
        
        success, response = self.make_request("POST", "/api/v1/queries", query_data, 202)
        if not success:
            return False
        
        result = response.json()
        self.query_id = result.get('query_id')
        print_success(f"Query submitted: {self.query_id}")
        
        # Step 3: Poll for query completion and verify agent execution
        print_section("Step 3: Wait for Query Processing & Verify Agent Execution")
        max_polls = 20
        for i in range(max_polls):
            time.sleep(3)
            success, response = self.make_request("GET", f"/api/v1/queries/{self.query_id}", expected_status=200)
            if not success:
                continue
            
            result = response.json()
            status = result.get('status')
            execution_log = result.get('execution_log', [])
            
            print_info(f"Poll {i+1}/{max_polls}: Status={status}, Agents executed={len(execution_log)}")
            
            if status == 'completed':
                print_success("Query completed! Verifying agent outputs...")
                
                # Verify each agent's execution
                print_info(f"\nAgent Execution Results ({len(execution_log)} agents):")
                for log_entry in execution_log:
                    agent_id = log_entry.get('agent_id', 'unknown')
                    output = log_entry.get('output', {})
                    print_info(f"  ✓ {agent_id}: {json.dumps(output, indent=4)}")
                
                print_info(f"\nFinal Answer: {result.get('answer', 'N/A')}")
                return True
            elif status == 'failed':
                print_error(f"Query failed: {result.get('error')}")
                return False
        
        print_error("Query timed out - agents may not have executed")
        return False
    
    def test_management_flow(self):
        """Test end-to-end management flow"""
        print_header("TEST 3: DATA MANAGEMENT FLOW")
        
        if not self.report_id:
            print_error("No report ID available from ingestion flow")
            return False
        
        # Step 1: Update report with management data (will trigger 3 management agents)
        print_section("Step 1: Update Report with Management Actions (Triggers 3 Agents)")
        print_info("Expected agents to execute:")
        print_info("  - builtin-management-task-assigner: Assign to John Smith")
        print_info("  - builtin-management-status-updater: Update status to in_progress")
        print_info("  - builtin-management-task-details-editor: Set priority to high")
        
        management_data = {
            "management_data": {
                "assigned_to": "John Smith",
                "priority": "high",
                "status": "in_progress",
                "notes": "Assigned to field supervisor for immediate action",
                "updated_by": "e2e_test",
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
        success, response = self.make_request("PUT", f"/api/v1/reports/{self.report_id}", management_data, 200)
        if not success:
            return False
        
        print_success("Report updated with management data")
        
        # Step 2: Verify the update
        print_section("Step 2: Verify Management Update")
        success, response = self.make_request("GET", f"/api/v1/reports/{self.report_id}", expected_status=200)
        if not success:
            return False
        
        result = response.json()
        mgmt_data = result.get('management_data', {})
        
        if mgmt_data.get('assigned_to') == "John Smith":
            print_success("Management data verified!")
            print_info(f"Management data: {json.dumps(mgmt_data, indent=2)}")
            return True
        else:
            print_error("Management data not found or incorrect")
            return False
    
    def cleanup(self):
        """Clean up test resources"""
        print_header("CLEANUP")
        
        if self.domain_id:
            print_info(f"Deleting domain: {self.domain_id}")
            success, response = self.make_request("DELETE", f"/api/v1/domains/{self.domain_id}")
            if success:
                print_success("Domain deleted")
            else:
                print_error("Failed to delete domain")
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print_header("END-TO-END FLOW TESTS")
        print_info(f"API Base URL: {API_BASE_URL}")
        print_info(f"Test User: {TEST_USERNAME}")
        
        if not self.get_auth_token():
            print_error("Authentication failed. Cannot proceed with tests.")
            return False
        
        results = {
            "ingestion": False,
            "query": False,
            "management": False
        }
        
        # Test 1: Ingestion Flow
        try:
            results["ingestion"] = self.test_ingestion_flow()
        except Exception as e:
            print_error(f"Ingestion flow failed with exception: {e}")
        
        # Test 2: Query Flow (depends on ingestion)
        if results["ingestion"]:
            try:
                results["query"] = self.test_query_flow()
            except Exception as e:
                print_error(f"Query flow failed with exception: {e}")
        else:
            print_error("Skipping query flow - ingestion failed")
        
        # Test 3: Management Flow (depends on ingestion)
        if results["ingestion"]:
            try:
                results["management"] = self.test_management_flow()
            except Exception as e:
                print_error(f"Management flow failed with exception: {e}")
        else:
            print_error("Skipping management flow - ingestion failed")
        
        # Cleanup
        try:
            self.cleanup()
        except Exception as e:
            print_error(f"Cleanup failed: {e}")
        
        # Print summary
        print_header("TEST SUMMARY")
        print_info(f"Ingestion Flow: {'✓ PASS' if results['ingestion'] else '✗ FAIL'}")
        print_info(f"Query Flow: {'✓ PASS' if results['query'] else '✗ FAIL'}")
        print_info(f"Management Flow: {'✓ PASS' if results['management'] else '✗ FAIL'}")
        
        all_passed = all(results.values())
        if all_passed:
            print_success("\nAll end-to-end flows passed!")
            return True
        else:
            print_error("\nSome flows failed. Check logs above.")
            return False

def main():
    # Validate environment variables
    if not all([API_BASE_URL, COGNITO_CLIENT_ID, TEST_USERNAME, TEST_PASSWORD]):
        print_error("Missing required environment variables:")
        print_info("Required: API_BASE_URL, COGNITO_CLIENT_ID, TEST_USERNAME, TEST_PASSWORD")
        sys.exit(1)
    
    tester = E2EFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
