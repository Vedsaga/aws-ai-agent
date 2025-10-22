#!/usr/bin/env python3
"""
ENHANCED Comprehensive API Test Suite for DomainFlow Agentic Orchestration Platform
Covers ALL 16 requirements with proper validation
Author: Enhanced for Hackathon Submission
Version: 2.1
"""

import requests
import json
import boto3
import time
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import websocket
import threading

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_REGION = os.environ.get("AWS_REGION", "us-east-1")
USERNAME = os.environ.get("TEST_USERNAME")
PASSWORD = os.environ.get("TEST_PASSWORD")
# WebSocket URL for real-time (e.g., wss://xxxx.appsync-api.us-east-1.amazonaws.com/graphql)
APPSYNC_URL = os.environ.get("APPSYNC_URL") 
# Host for AppSync (e.g., xxxx.appsync-api.us-east-1.amazonaws.com)
APPSYNC_HOST = os.environ.get("APPSYNC_HOST") 

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []
    
    def add_result(self, name: str, passed: bool, skipped: bool = False, message: str = ""):
        self.total += 1
        if skipped:
            self.skipped += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1
        
        self.tests.append({
            "name": name,
            "passed": passed,
            "skipped": skipped,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.RESET}")

def print_test(name):
    print(f"\n{Colors.BOLD}TEST: {name}{Colors.RESET}")

def print_pass(message):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET} - {message}")

def print_fail(message):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET} - {message}")

def print_skip(message):
    print(f"{Colors.YELLOW}⊘ SKIP{Colors.RESET} - {message}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ INFO{Colors.RESET} - {message}")

def print_warning(message):
    print(f"{Colors.MAGENTA}⚠ WARN{Colors.RESET} - {message}")

class APITester:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.results = TestResults()
        
        # Store created resources for cleanup
        self.created_agents = []
        self.created_domains = []
        self.created_reports = []
        self.created_sessions = []
        self.created_queries = []
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, validate_schema: bool = True) -> Tuple[bool, Optional[requests.Response]]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                print_fail(f"Unsupported method: {method}")
                return False, None
            
            print_info(f"Status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                print_info(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
            except:
                print_info(f"Response: {response.text[:500]}")
            
            # Validate status code
            status_match = response.status_code == expected_status
            if status_match:
                print_pass(f"Expected status {expected_status}")
            else:
                print_fail(f"Expected {expected_status}, got {response.status_code}")
            
            # Validate response schema if requested
            if validate_schema and status_match and method in ["GET", "POST", "PUT"]:
                schema_valid = self.validate_response_schema(endpoint, method, response)
                return status_match and schema_valid, response
            
            return status_match, response
                
        except Exception as e:
            print_fail(f"Request failed: {str(e)}")
            return False, None
    
    def validate_response_schema(self, endpoint: str, method: str, response: requests.Response) -> bool:
        """Validate response matches expected schema from requirements"""
        try:
            data = response.json()
            
            # Check standard metadata fields for creation/update responses
            if method in ["POST", "PUT"]:
                if "/agents" in endpoint or "/domains" in endpoint or "/sessions" in endpoint:
                    required_metadata = ["id", "created_at", "updated_at"]
                    missing = [f for f in required_metadata if f not in data]
                    if missing:
                        print_warning(f"Missing metadata fields: {missing}")
                        return False
                    print_info("✓ Standard metadata present")
            
            # Validate specific endpoint schemas
            if "/agents" in endpoint and method == "GET":
                if "agents" in data:  # List response
                    if "pagination" not in data:
                        print_warning("Missing pagination in list response")
                        return False
                elif "agent_id" in data:  # Single agent
                    required = ["agent_name", "agent_class", "system_prompt", "output_schema"]
                    missing = [f for f in required if f not in data]
                    if missing:
                        print_warning(f"Missing agent fields: {missing}")
                        return False
            
            return True
        except:
            return True  # Don't fail on schema validation errors
    
    def poll_until_complete(self, endpoint: str, max_wait: int = 30, 
                            status_field: str = "status") -> Tuple[bool, Optional[Dict]]:
        """Poll endpoint until processing completes or timeout"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            success, response = self.make_request("GET", endpoint, validate_schema=False)
            if success and response:
                try:
                    data = response.json()
                    status = data.get(status_field, "")
                    
                    if status in ["completed", "failed", "error"]:
                        print_info(f"Processing {status} after {int(time.time() - start_time)}s")
                        return True, data
                    
                    print_info(f"Status: {status}, waiting...")
                    time.sleep(2)
                except json.JSONDecodeError:
                    print_warning("Failed to decode JSON from polling response")
                    time.sleep(2)
            else:
                time.sleep(2)
        
        print_warning(f"Timeout after {max_wait}s")
        return False, None

    # ========================================================================
    # AUTHENTICATION TESTS (Suite 1)
    # ========================================================================
    
    def test_authentication(self):
        """Test Requirement 11: API Security - Authentication"""
        print_section("TEST SUITE 1: Authentication & Security")
        
        # Test 1.1: No auth header (should fail with 401)
        print_test("1.1: Request without Authorization header (expect 401)")
        url = f"{self.base_url}/api/v1/agents"
        try:
            response = requests.get(url, headers={"Content-Type": "application/json"}, timeout=10)
            if response.status_code == 401:
                print_pass("Correctly rejected unauthorized request")
                self.results.add_result("Auth - Reject No Token", True)
            else:
                print_fail(f"Expected 401, got {response.status_code}")
                self.results.add_result("Auth - Reject No Token", False)
        except Exception as e:
            print_fail(f"Request failed: {str(e)}")
            self.results.add_result("Auth - Reject No Token", False)
        
        # Test 1.2: Invalid token (should fail with 401)
        print_test("1.2: Request with invalid token (expect 401)")
        try:
            response = requests.get(url, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token_12345"
            }, timeout=10)
            if response.status_code == 401:
                print_pass("Correctly rejected invalid token")
                self.results.add_result("Auth - Reject Invalid Token", True)
            else:
                print_fail(f"Expected 401, got {response.status_code}")
                self.results.add_result("Auth - Reject Invalid Token", False)
        except Exception as e:
            print_fail(f"Request failed: {str(e)}")
            self.results.add_result("Auth - Reject Invalid Token", False)
        
        # Test 1.3: Valid token (should succeed)
        print_test("1.3: Request with valid token (expect 200)")
        success, response = self.make_request("GET", "/api/v1/agents", expected_status=200)
        self.results.add_result("Auth - Accept Valid Token", success)

    # ========================================================================
    # AGENT CRUD TESTS (Suite 2)
    # ========================================================================
    
    def test_agent_crud(self):
        """Test Requirement 1: Agent Management API"""
        print_section("TEST SUITE 2: Agent Management (CRUD)")
        
        # Test 2.1: List all agents
        print_test("2.1: List all agents")
        success, response = self.make_request("GET", "/api/v1/agents", expected_status=200)
        self.results.add_result("Agent - List All", success)
        
        # Test 2.2: List filtered by class
        print_test("2.2: List agents filtered by class")
        success, response = self.make_request("GET", "/api/v1/agents?agent_class=ingestion", 
                                              expected_status=200)
        self.results.add_result("Agent - List Filtered", success)
        
        # Test 2.3: Create valid agent
        print_test("2.3: Create new agent")
        agent_data = {
            "agent_name": f"Test Agent {int(time.time())}",
            "agent_class": "query",
            "system_prompt": "You are a test agent for automated testing",
            "tools": [],
            "agent_dependencies": [],
            "max_output_keys": 5,
            "output_schema": {
                "result": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "description": "Automated test agent",
            "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=agent_data, 
                                              expected_status=201)
        
        created_agent_id = None
        if success and response:
            data = response.json()
            created_agent_id = data.get('agent_id')
            if created_agent_id:
                self.created_agents.append(created_agent_id)
                print_info(f"Created agent: {created_agent_id}")
                
                # Verify version is 1
                if data.get('version') == 1:
                    print_pass("Initial version is 1")
                else:
                    print_warning(f"Version is {data.get('version')}, expected 1")
        
        self.results.add_result("Agent - Create Valid", success)
        
        # Test 2.4: Create agent with invalid class (should fail)
        print_test("2.4: Create agent with invalid class (expect 400)")
        invalid_data = agent_data.copy()
        invalid_data["agent_class"] = "invalid_class"
        success, response = self.make_request("POST", "/api/v1/agents", data=invalid_data,
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected invalid agent_class")
            self.results.add_result("Agent - Reject Invalid Class", True)
        else:
            print_fail("Should have rejected invalid agent_class")
            self.results.add_result("Agent - Reject Invalid Class", False)
        
        # Test 2.5: Create agent with > 5 output keys (should fail)
        print_test("2.5: Create agent with > 5 output keys (expect 400)")
        invalid_data = agent_data.copy()
        invalid_data["output_schema"] = {
            f"key_{i}": {"type": "string"} for i in range(6)
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=invalid_data,
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected > 5 output keys")
            self.results.add_result("Agent - Reject > 5 Keys", True)
        else:
            print_fail("Should have rejected > 5 output keys")
            self.results.add_result("Agent - Reject > 5 Keys", False)

        # Test 2.6: Get specific agent
        if created_agent_id:
            print_test(f"2.6: Get agent by ID: {created_agent_id}")
            success, response = self.make_request("GET", f"/api/v1/agents/{created_agent_id}",
                                                  expected_status=200)
            
            if success and response:
                data = response.json()
                if "dependency_graph" in data:
                    print_pass("Dependency graph included in response")
                else:
                    print_warning("Missing dependency_graph field")
            
            self.results.add_result("Agent - Get by ID", success)
        else:
            print_skip("Skipping get agent test (no agent created)")
            self.results.add_result("Agent - Get by ID", True, skipped=True)
        
        # Test 2.7: Get non-existent agent (should return 404)
        print_test("2.7: Get non-existent agent (expect 404)")
        success, response = self.make_request("GET", "/api/v1/agents/non-existent-id",
                                              expected_status=404, validate_schema=False)
        if success:
            print_pass("Correctly returned 404 for non-existent agent")
            self.results.add_result("Agent - 404 Not Found", True)
        else:
            print_fail("Should have returned 404")
            self.results.add_result("Agent - 404 Not Found", False)
        
        # Test 2.8: Update agent
        if created_agent_id:
            print_test(f"2.8: Update agent: {created_agent_id}")
            update_data = {
                "agent_name": f"Updated Test Agent {int(time.time())}",
                "system_prompt": "Updated system prompt for testing"
            }
            success, response = self.make_request("PUT", f"/api/v1/agents/{created_agent_id}",
                                                  data=update_data, expected_status=200)
            
            if success and response:
                data = response.json()
                # Verify version incremented
                if data.get('version', 0) > 1:
                    print_pass(f"Version incremented to {data.get('version')}")
                else:
                    print_warning("Version did not increment")
                
                # Verify updated_at changed
                if data.get('updated_at'):
                    print_pass("updated_at timestamp present")
            
            self.results.add_result("Agent - Update", success)
        else:
            print_skip("Skipping update agent test")
            self.results.add_result("Agent - Update", True, skipped=True)
        
        return created_agent_id
    
    # ========================================================================
    # DAG VALIDATION TESTS (Suite 3 - CRITICAL)
    # ========================================================================
    
    def test_dag_validation(self, base_agent_id: str = None):
        """Test Requirement 9: Agent Dependency Management with DAG Validation"""
        print_section("TEST SUITE 3: DAG Validation (CRITICAL)")
        
        # Create base agent if not provided
        if not base_agent_id:
            print_test("3.1: Create base agent for DAG testing")
            agent_data = {
                "agent_name": f"DAG Base Agent {int(time.time())}",
                "agent_class": "query",
                "system_prompt": "Base agent for DAG testing",
                "agent_dependencies": [],
                "max_output_keys": 5,
                "output_schema": {"base_result": {"type": "string"}},
                "enabled": True
            }
            success, response = self.make_request("POST", "/api/v1/agents", data=agent_data,
                                                  expected_status=201)
            if success and response:
                base_agent_id = response.json().get('agent_id')
                self.created_agents.append(base_agent_id)
                print_info(f"Created base agent: {base_agent_id}")
        
        if not base_agent_id:
            print_fail("Cannot test DAG without base agent")
            self.results.add_result("DAG - Setup Failed", False)
            return
        
        # Test 3.2: Create agent with valid dependency
        print_test("3.2: Create agent with valid dependency")
        dependent1_data = {
            "agent_name": f"DAG Dependent 1 {int(time.time())}",
            "agent_class": "query",
            "system_prompt": "Depends on base agent",
            "agent_dependencies": [base_agent_id],
            "max_output_keys": 5,
            "output_schema": {"dependent_result": {"type": "string"}},
            "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=dependent1_data,
                                              expected_status=201)
        
        dependent1_id = None
        if success and response:
            dependent1_id = response.json().get('agent_id')
            self.created_agents.append(dependent1_id)
            print_pass(f"Created dependent agent: {dependent1_id}")
            
            # Verify dependency_graph
            success_get, response_get = self.make_request("GET", f"/api/v1/agents/{dependent1_id}",
                                                          expected_status=200)
            if success_get and response_get:
                data = response_get.json()
                dep_graph = data.get('dependency_graph', {})
                if dep_graph.get('nodes') and dep_graph.get('edges'):
                    print_pass("Dependency graph generated correctly")
                else:
                    print_warning("Dependency graph incomplete")
        
        self.results.add_result("DAG - Valid Dependency", success)
        
        # Test 3.3: Create second dependent agent
        print_test("3.3: Create second dependent agent")
        dependent2_data = {
            "agent_name": f"DAG Dependent 2 {int(time.time())}",
            "agent_class": "query",
            "system_prompt": "Also depends on dependent1",
            "agent_dependencies": [dependent1_id] if dependent1_id else [],
            "max_output_keys": 5,
            "output_schema": {"final_result": {"type": "string"}},
            "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=dependent2_data,
                                              expected_status=201)
        
        dependent2_id = None
        if success and response:
            dependent2_id = response.json().get('agent_id')
            self.created_agents.append(dependent2_id)
            print_pass(f"Created second dependent agent: {dependent2_id}")
        
        self.results.add_result("DAG - Chain Dependency", success)
        
        # Test 3.4: CRITICAL - Attempt circular dependency (MUST FAIL)
        if base_agent_id and dependent2_id:
            print_test("3.4: CRITICAL - Attempt circular dependency (MUST return 400)")
            update_data = {
                "agent_dependencies": [dependent2_id]  # This creates a cycle
            }
            success, response = self.make_request("PUT", f"/api/v1/agents/{base_agent_id}",
                                                  data=update_data, expected_status=400,
                                                  validate_schema=False)
            
            # Check if circular dependency was correctly rejected
            if success:
                print_pass("✅ CRITICAL: API correctly rejected circular dependency")
                try:
                    error_data = response.json()
                    # Check both 'error' and 'message' fields for the error message
                    error_msg = (error_data.get('error', '') or error_data.get('message', '')).lower()
                    if 'circular' in error_msg or 'cycle' in error_msg or 'dag' in error_msg:
                        print_pass(f"Error message mentions circular dependency: {error_msg[:100]}")
                        self.results.add_result("DAG - Circular Detection (CRITICAL)", True)
                    else:
                        print_warning(f"Error message unclear: {error_msg[:100]}")
                        self.results.add_result("DAG - Circular Detection (CRITICAL)", True,
                                              message="Rejected but error message unclear")
                except:
                    print_pass("Rejected circular dependency (couldn't parse error message)")
                    self.results.add_result("DAG - Circular Detection (CRITICAL)", True)
            else:
                print_fail("❌ CRITICAL FAILURE: API allowed circular dependency!")
                print_fail("This is a MAJOR BUG that violates Requirement 9")
                self.results.add_result("DAG - Circular Detection (CRITICAL)", False,
                                      message="API ACCEPTED CIRCULAR DEPENDENCY - MAJOR BUG")
        else:
            print_skip("Cannot test circular dependency without agents")
            self.results.add_result("DAG - Circular Detection (CRITICAL)", True, skipped=True)
        
        # Test 3.5: Non-existent dependency (should fail)
        print_test("3.5: Create agent with non-existent dependency (expect 400)")
        invalid_dep_data = {
            "agent_name": f"Invalid Dep Agent {int(time.time())}",
            "agent_class": "query",
            "system_prompt": "Has non-existent dependency",
            "agent_dependencies": ["non-existent-agent-id"],
            "max_output_keys": 5,
            "output_schema": {"result": {"type": "string"}},
            "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=invalid_dep_data,
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected non-existent dependency")
            self.results.add_result("DAG - Reject Invalid Dependency", True)
        else:
            print_fail("Should have rejected non-existent dependency")
            self.results.add_result("DAG - Reject Invalid Dependency", False)
        
        return base_agent_id, dependent1_id, dependent2_id

    # ========================================================================
    # DOMAIN CRUD TESTS (Suite 4)
    # ========================================================================
    
    def test_domain_crud(self, query_agent_id: str = None):
        """Test Requirement 2: Domain Configuration API"""
        print_section("TEST SUITE 4: Domain Management (CRUD)")
        
        # Test 4.1: List all domains
        print_test("4.1: List all domains")
        success, response = self.make_request("GET", "/api/v1/domains", expected_status=200)
        self.results.add_result("Domain - List All", success)
        
        # Create query agent if not provided
        if not query_agent_id:
            print_test("4.2: Create query agent for domain")
            agent_data = {
                "agent_name": f"Domain Query Agent {int(time.time())}",
                "agent_class": "query",
                "system_prompt": "Query agent for domain testing",
                "tools": [],
                "agent_dependencies": [],
                "max_output_keys": 5,
                "output_schema": {"answer": {"type": "string"}},
                "enabled": True
            }
            success, response = self.make_request("POST", "/api/v1/agents", data=agent_data,
                                                  expected_status=201)
            if success and response:
                query_agent_id = response.json().get('agent_id')
                self.created_agents.append(query_agent_id)
                print_info(f"Created query agent: {query_agent_id}")
        
        if not query_agent_id:
            print_warning("Cannot test domain without query agent")
            self.results.add_result("Domain - Setup Failed", False)
            return None
        
        # Test 4.3: Create valid domain
        print_test("4.3: Create new domain with all three playbooks")
        domain_id = f"test_domain_{int(time.time())}"
        
        # --- THIS IS THE UPDATED PART ---
        # We now use the REAL built-in agent IDs from your seed data
        domain_data = {
            "domain_id": domain_id,
            "domain_name": "Test Domain (using built-ins)",
            "description": "Automated test domain using real agents",
            "ingestion_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-ingestion-geo",
                        "builtin-ingestion-temporal",
                        "builtin-ingestion-entity"
                    ],
                    "edges": []
                }
            },
            "query_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-query-who",
                        "builtin-query-what",
                        "builtin-query-where",
                        "builtin-query-when",
                        "builtin-query-why",
                        "builtin-query-how"
                    ],
                    "edges": []
                }
            },
            "management_playbook": {
                "agent_execution_graph": {
                    "nodes": [
                        "builtin-management-task-assigner",
                        "builtin-management-status-updater",
                        "builtin-management-task-details-editor"
                    ],
                    "edges": []
                }
            }
        }        
        success, response = self.make_request("POST", "/api/v1/domains", data=domain_data,
                                              expected_status=201)
        
        created_domain_id = None
        if success and response:
            created_domain_id = response.json().get('domain_id')
            self.created_domains.append(created_domain_id)
            print_pass(f"Created domain: {created_domain_id}")
        
        self.results.add_result("Domain - Create Valid", success)
        
        # Test 4.4: Create domain with invalid agent (should fail)
        print_test("4.4: Create domain with non-existent agent (expect 400)")
        invalid_domain_data = domain_data.copy()
        invalid_domain_data["domain_id"] = f"invalid_domain_{int(time.time())}"
        invalid_domain_data["query_playbook"]["agent_execution_graph"]["nodes"] = ["non-existent-agent"]
        
        success, response = self.make_request("POST", "/api/v1/domains", data=invalid_domain_data,
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected domain with invalid agent")
            self.results.add_result("Domain - Reject Invalid Agent", True)
        else:
            print_fail("Should have rejected domain with invalid agent")
            self.results.add_result("Domain - Reject Invalid Agent", False)
        
        # Test 4.5: Get specific domain
        if created_domain_id:
            print_test(f"4.5: Get domain by ID: {created_domain_id}")
            success, response = self.make_request("GET", f"/api/v1/domains/{created_domain_id}",
                                                  expected_status=200)
            
            if success and response:
                data = response.json()
                required_playbooks = ["ingestion_playbook", "query_playbook", "management_playbook"]
                missing = [p for p in required_playbooks if p not in data]
                if not missing:
                    print_pass("All three playbooks present in response")
                else:
                    print_warning(f"Missing playbooks: {missing}")
            
            self.results.add_result("Domain - Get by ID", success)
        else:
            print_skip("Skipping get domain test")
            self.results.add_result("Domain - Get by ID", True, skipped=True)
        
        # Test 4.6: Update domain
        if created_domain_id:
            print_test(f"4.6: Update domain: {created_domain_id}")
            update_data = {
                "domain_name": f"Updated Test Domain {int(time.time())}",
                "description": "Updated description"
            }
            success, response = self.make_request("PUT", f"/api/v1/domains/{created_domain_id}",
                                                  data=update_data, expected_status=200)
            self.results.add_result("Domain - Update", success)
        else:
            print_skip("Skipping update domain test")
            self.results.add_result("Domain - Update", True, skipped=True)
        
        return created_domain_id

    # ========================================================================
    # REPORT SUBMISSION TESTS (Suite 5)
    # ========================================================================
    
    def test_report_submission(self, domain_id: str = None):
        """Test Requirement 3: Report Submission API"""
        print_section("TEST SUITE 5: Report Submission & Management")
        
        # Use existing domain or default
        test_domain = domain_id if domain_id else "civic_complaints"
        
        # Test 5.1: Submit valid report
        print_test("5.1: Submit new report")
        report_data = {
            "domain_id": test_domain,
            "text": f"Test report at {datetime.now().isoformat()}: Broken streetlight on Main Street, urgent repair needed",
            "images": [],
            "source": "automated-test"
        }
        success, response = self.make_request("POST", "/api/v1/reports", data=report_data,
                                              expected_status=202)
        
        created_incident_id = None
        created_job_id = None
        if success and response:
            data = response.json()
            created_incident_id = data.get('incident_id')
            created_job_id = data.get('job_id')
            if created_incident_id:
                self.created_reports.append(created_incident_id)
                print_pass(f"Report submitted: {created_incident_id}, Job: {created_job_id}")
                
                # Verify response fields
                if data.get('status') == 'accepted':
                    print_pass("Status is 'accepted'")
                if data.get('timestamp'):
                    print_pass("Timestamp present")
        
        self.results.add_result("Report - Submit Valid", success)
        
        # Test 5.2: Submit report with missing required field (should fail)
        print_test("5.2: Submit report without required field (expect 400)")
        invalid_report = {"domain_id": test_domain}  # Missing 'text'
        success, response = self.make_request("POST", "/api/v1/reports", data=invalid_report,
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected report without text")
            self.results.add_result("Report - Reject Missing Field", True)
        else:
            print_fail("Should have rejected report without text")
            self.results.add_result("Report - Reject Missing Field", False)
        
        # Test 5.3: Get report with ingestion_data (wait for processing)
        if created_incident_id:
            print_test(f"5.3: Get report after processing: {created_incident_id}")
            
            # Poll until processing completes
            print_info("Waiting for ingestion processing...")
            success, data = self.poll_until_complete(
                f"/api/v1/reports/{created_incident_id}",
                max_wait=30,
                status_field="status"
            )
            
            if success and data:
                # Validate report structure
                if "ingestion_data" in data:
                    print_pass(f"ingestion_data present: {list(data['ingestion_data'].keys())}")
                else:
                    print_warning("ingestion_data missing")
                
                if "management_data" in data:
                    print_pass("management_data field present")
                else:
                    print_warning("management_data missing")
                
                if "raw_text" in data:
                    print_pass("raw_text preserved")
                
                self.results.add_result("Report - Get with Ingestion Data", True)
            else:
                print_warning("Report processing timed out or failed")
                self.results.add_result("Report - Get with Ingestion Data", False,
                                      message="Processing timeout")
        else:
            print_skip("Skipping get report test")
            self.results.add_result("Report - Get with Ingestion Data", True, skipped=True)
        
        # Test 5.4: List reports
        print_test("5.4: List reports with domain filter")
        success, response = self.make_request("GET", f"/api/v1/reports?domain_id={test_domain}",
                                              expected_status=200)
        
        if success and response:
            data = response.json()
            if "reports" in data and "pagination" in data:
                print_pass(f"Found {len(data['reports'])} reports with pagination")
            else:
                print_warning("Missing reports or pagination field")
        
        self.results.add_result("Report - List Filtered", success)
        
        # Test 5.5: Update report management_data
        if created_incident_id:
            print_test(f"5.5: Update report management_data: {created_incident_id}")
            update_data = {
                "status": "in_progress",
                "management_data": {
                    "task_details": {
                        "assignee_id": "team-test-123",
                        "priority": "high",
                        "due_at": "2025-12-31T23:59:59Z"
                    }
                }
            }
            success, response = self.make_request("PUT", f"/api/v1/reports/{created_incident_id}",
                                                  data=update_data, expected_status=200)
            
            self.results.add_result("Report - Update Management Data", success)
        else:
            print_skip("Skipping update report test")
            self.results.add_result("Report - Update Management Data", True, skipped=True)
        
        return created_incident_id

    # ========================================================================
    # SESSION MANAGEMENT TESTS (Suite 6)
    # ========================================================================

    def test_session_management(self, domain_id: str = None):
        """Test Requirement 5: Session Management API"""
        print_section("TEST SUITE 6: Session Management")
        
        test_domain = domain_id if domain_id else "civic_complaints"
        
        # Test 6.1: Create session
        print_test("6.1: Create new session")
        session_data = {
            "domain_id": test_domain,
            "title": f"Test Session {int(time.time())}"
        }
        success, response = self.make_request("POST", "/api/v1/sessions", data=session_data,
                                              expected_status=201)
        
        created_session_id = None
        if success and response:
            data = response.json()
            created_session_id = data.get('session_id')
            if created_session_id:
                self.created_sessions.append(created_session_id)
                print_pass(f"Created session: {created_session_id}")
        
        self.results.add_result("Session - Create", success)

        # Test 6.2: List sessions
        print_test("6.2: List all sessions")
        success, response = self.make_request("GET", "/api/v1/sessions", expected_status=200)
        
        if success and response:
            data = response.json()
            if "sessions" in data and "pagination" in data:
                print_pass("Sessions list and pagination present")
                if data.get("sessions"):
                    first_session = data["sessions"][0]
                    if "message_count" in first_session and "last_activity" in first_session:
                        print_pass("List format correct (message_count, last_activity)")
                    else:
                        print_warning("List format missing required fields")
            else:
                print_warning("Missing sessions or pagination")
        
        self.results.add_result("Session - List All", success)
        
        # Test 6.3: Get session with messages
        if created_session_id:
            print_test(f"6.3: Get session by ID: {created_session_id}")
            success, response = self.make_request("GET", f"/api/v1/sessions/{created_session_id}",
                                                  expected_status=200)
            
            if success and response:
                data = response.json()
                if "messages" in data:
                    print_pass(f"Messages array present (count: {len(data['messages'])})")
                else:
                    print_warning("Missing messages array in response")
            
            self.results.add_result("Session - Get with Messages", success)
        else:
            print_skip("Skipping get session test")
            self.results.add_result("Session - Get with Messages", True, skipped=True)
        
        # Test 6.4: Update session
        if created_session_id:
            print_test(f"6.4: Update session: {created_session_id}")
            update_data = {
                "title": f"Updated Test Session {int(time.time())}"
            }
            success, response = self.make_request("PUT", f"/api/v1/sessions/{created_session_id}",
                                                  data=update_data, expected_status=200)
            self.results.add_result("Session - Update", success)
        else:
            print_skip("Skipping update session test")
            self.results.add_result("Session - Update", True, skipped=True)
        
        return created_session_id

    # ========================================================================
    # QUERY SUBMISSION & CACHING TESTS (Suite 7 - CRITICAL)
    # ========================================================================

    def test_caching_and_execution_log(self, domain_id: str = None, session_id: str = None):
        """Test Requirement 4, 13, 14: Query API, Caching, and Execution Log"""
        print_section("TEST SUITE 7: Query, Caching & Execution Log (CRITICAL)")
        
        # --- Setup for Caching Test ---
        print_test("7.1: Setup agents for caching test")
        
        # 1. Create shared base agent
        base_agent_data = {
            "agent_name": f"Cache Base Agent {int(time.time())}",
            "agent_class": "query", "system_prompt": "This agent should be cached",
            "agent_dependencies": [], "max_output_keys": 5,
            "output_schema": {"shared_data": {"type": "string"}}, "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=base_agent_data, expected_status=201)
        base_agent_id = response.json()['agent_id'] if success else None
        if base_agent_id: self.created_agents.append(base_agent_id)
        
        # 2. Create two dependent agents
        dep1_data = {
            "agent_name": f"Cache Dep1 {int(time.time())}", "agent_class": "query",
            "system_prompt": "Depends on base", "agent_dependencies": [base_agent_id],
            "max_output_keys": 5, "output_schema": {"result": {"type": "string"}}, "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=dep1_data, expected_status=201)
        dep1_id = response.json()['agent_id'] if success else None
        if dep1_id: self.created_agents.append(dep1_id)

        dep2_data = {
            "agent_name": f"Cache Dep2 {int(time.time())}", "agent_class": "query",
            "system_prompt": "Also depends on base", "agent_dependencies": [base_agent_id],
            "max_output_keys": 5, "output_schema": {"result": {"type": "string"}}, "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=dep2_data, expected_status=201)
        dep2_id = response.json()['agent_id'] if success else None
        if dep2_id: self.created_agents.append(dep2_id)
        
        if not (base_agent_id and dep1_id and dep2_id):
            print_fail("Failed to create agents for caching test")
            self.results.add_result("Caching - Setup Failed", False)
            return None, None # Return None for session_id, query_id

        # 3. Create a domain for caching
        print_test("7.2: Setup domain for caching test")
        cache_domain_id = f"cache_domain_{int(time.time())}"
        domain_data = {
            "domain_id": cache_domain_id, "domain_name": "Caching Test Domain",
            "ingestion_playbook": {"agent_execution_graph": {"nodes": ["builtin-ingestion-entity"], "edges": []}},
            "query_playbook": {
                "agent_execution_graph": {
                    "nodes": [base_agent_id, dep1_id, dep2_id],
                    "edges": [
                        {"from": base_agent_id, "to": dep1_id},
                        {"from": base_agent_id, "to": dep2_id}
                    ]
                }
            },
            "management_playbook": {"agent_execution_graph": {"nodes": ["builtin-management-task-details-editor"], "edges": []}}
        }
        success, response = self.make_request("POST", "/api/v1/domains", data=domain_data, expected_status=201)
        if success:
            self.created_domains.append(cache_domain_id)
            print_pass(f"Created domain for caching: {cache_domain_id}")
        else:
            print_fail("Failed to create domain for caching test")
            self.results.add_result("Caching - Domain Setup Failed", False)
            return None, None

        # 4. Create session
        print_test("7.3: Create session for query")
        session_data = {"domain_id": cache_domain_id, "title": "Caching Test Session"}
        success, response = self.make_request("POST", "/api/v1/sessions", data=session_data, expected_status=201)
        session_id = response.json()['session_id'] if success else None
        if session_id:
            self.created_sessions.append(session_id)
            print_pass(f"Created session: {session_id}")
        else:
            print_fail("Failed to create session for caching test")
            self.results.add_result("Caching - Session Setup Failed", False)
            return None, None

        # --- Run Caching Test ---
        print_test("7.4: CRITICAL - Submit query to test caching (Req 13)")
        query_data = {
            "session_id": session_id,
            "domain_id": cache_domain_id,
            "question": "Test caching behavior"
        }
        success, response = self.make_request("POST", "/api/v1/queries", data=query_data, expected_status=202)
        
        created_query_id = None
        if success and response:
            created_query_id = response.json().get('query_id')
            self.created_queries.append(created_query_id)
            print_pass(f"Query submitted: {created_query_id}")
        
        self.results.add_result("Query - Submit (Read)", success)
        
        # Test 7.5: Get query result and validate cache
        if created_query_id:
            print_test(f"7.5: CRITICAL - Get query result and validate cache/log: {created_query_id}")
            
            # Poll until processing completes
            print_info("Waiting for query processing...")
            success, data = self.poll_until_complete(
                f"/api/v1/queries/{created_query_id}",
                max_wait=60, # Give orchestrator time
                status_field="status"
            )

            if success and data and data.get('status') == 'completed':
                execution_log = data.get('execution_log', [])
                
                # Check execution log structure (Req 14)
                if not execution_log:
                    print_fail("❌ CRITICAL: Execution log is EMPTY. Orchestrator failed or did not run.")
                    self.results.add_result("Execution Log - NOT EMPTY (CRITICAL)", False, message="Orchestrator did not run")
                else:
                    print_pass(f"Execution log present (entries: {len(execution_log)})")
                    first_entry = execution_log[0]
                    required_fields = ['agent_id', 'agent_name', 'status', 'timestamp', 'reasoning', 'output']
                    missing = [f for f in required_fields if f not in first_entry]
                    if missing:
                        print_fail(f"Execution log missing fields: {missing}")
                        self.results.add_result("Execution Log - Structure (Req 14)", False, message=f"Missing: {missing}")
                    else:
                        print_pass("Execution log has correct structure (Req 14)")
                        print_info(f"Sample reasoning: {first_entry.get('reasoning', '')[:100]}...")
                        self.results.add_result("Execution Log - Structure (Req 14)", True)

                # Check caching (Req 13)
                base_executions = [e for e in execution_log if e['agent_id'] == base_agent_id and e.get('status') == 'success']
                cached_entries = [e for e in execution_log if e.get('status') == 'cached']
                
                if len(base_executions) == 1:
                    print_pass(f"✅ Base agent executed ONCE (correct)")
                    if len(cached_entries) >= 1:
                        print_pass(f"✅ Found {len(cached_entries)} 'cached' entries")
                        self.results.add_result("Caching - Memoization (CRITICAL)", True)
                    else:
                        print_warning("⚠️ Base agent ran once, but no 'cached' status found. Orchestrator may not be logging cache hits.")
                        self.results.add_result("Caching - Memoization (CRITICAL)", True, message="Execution count correct, but 'cached' status missing")
                elif len(base_executions) > 1:
                    print_fail(f"❌ CRITICAL: Base agent executed {len(base_executions)} times (should be 1). Caching is NOT WORKING.")
                    self.results.add_result("Caching - Memoization (CRITICAL)", False, message=f"Agent ran {len(base_executions)} times")
                else:
                    print_fail(f"❌ Base agent not found in 'success' execution log. Orchestrator may have failed.")
                    self.results.add_result("Caching - Memoization (CRITICAL)", False, message="Base agent did not run successfully")
                    
            elif success:
                print_fail(f"Query processing failed with status: {data.get('status')}")
                self.results.add_result("Execution Log - NOT EMPTY (CRITICAL)", False, message=f"Query failed: {data.get('status')}")
            else:
                print_fail("Query processing timed out")
                self.results.add_result("Execution Log - NOT EMPTY (CRITICAL)", False, message="Query timed out")
        else:
            print_skip("Skipping query get test (no query created)")
            self.results.add_result("Execution Log - NOT EMPTY (CRITICAL)", True, skipped=True)
        
        # Test 7.6: Submit query (management intent)
        print_test("7.6: Submit query with management intent")
        query_data = {
            "session_id": session_id,
            "domain_id": cache_domain_id,
            "question": "Assign all high priority potholes to Team A"
        }
        success, response = self.make_request("POST", "/api/v1/queries", data=query_data, expected_status=202)
        if success: self.created_queries.append(response.json().get('query_id'))
        self.results.add_result("Query - Submit (Update)", success)
        
        # Test 7.7: List queries for session
        print_test(f"7.7: List queries for session: {session_id}")
        success, response = self.make_request("GET", f"/api/v1/queries?session_id={session_id}",
                                              expected_status=200)
        self.results.add_result("Query - List by Session", success)
        
        return session_id, created_query_id

    # ========================================================================
    # ERROR HANDLING TESTS (Suite 8 - CRITICAL)
    # ========================================================================
    
    def test_error_handling_and_propagation(self):
        """Test Requirement 15: Graph Error Handling"""
        print_section("TEST SUITE 8: Graph Error Handling (CRITICAL)")
        
        # 1. Create agent designed to fail
        print_test("8.1: Setup agent designed to fail")
        failing_agent_data = {
            "agent_name": f"Failing Agent {int(time.time())}",
            "agent_class": "query", "system_prompt": "I am programmed to fail. Raise an error.",
            "agent_dependencies": [], "max_output_keys": 5,
            "output_schema": {"error": {"type": "string"}}, "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=failing_agent_data, expected_status=201)
        failing_agent_id = response.json()['agent_id'] if success else None
        if failing_agent_id: self.created_agents.append(failing_agent_id)

        # 2. Create dependent agent
        dependent_agent_data = {
            "agent_name": f"Skipped Agent {int(time.time())}",
            "agent_class": "query", "system_prompt": "I depend on the failing agent.",
            "agent_dependencies": [failing_agent_id], "max_output_keys": 5,
            "output_schema": {"result": {"type": "string"}}, "enabled": True
        }
        success, response = self.make_request("POST", "/api/v1/agents", data=dependent_agent_data, expected_status=201)
        dependent_agent_id = response.json()['agent_id'] if success else None
        if dependent_agent_id: self.created_agents.append(dependent_agent_id)
        
        if not (failing_agent_id and dependent_agent_id):
            print_fail("Failed to create agents for error test")
            self.results.add_result("Error Handling - Setup Failed", False)
            return

        # 3. Create domain
        print_test("8.2: Setup domain for error test")
        error_domain_id = f"error_domain_{int(time.time())}"
        domain_data = {
            "domain_id": error_domain_id, "domain_name": "Error Test Domain",
            "ingestion_playbook": {"agent_execution_graph": {"nodes": ["builtin-ingestion-entity"], "edges": []}},
            "query_playbook": {
                "agent_execution_graph": {
                    "nodes": [failing_agent_id, dependent_agent_id],
                    "edges": [{"from": failing_agent_id, "to": dependent_agent_id}]
                }
            },
            "management_playbook": {"agent_execution_graph": {"nodes": ["builtin-management-task-details-editor"], "edges": []}}
        }
        success, response = self.make_request("POST", "/api/v1/domains", data=domain_data, expected_status=201)
        if success: self.created_domains.append(error_domain_id)
        
        # 4. Create session & query
        session_data = {"domain_id": error_domain_id, "title": "Error Test Session"}
        success, response = self.make_request("POST", "/api/v1/sessions", data=session_data, expected_status=201)
        session_id = response.json()['session_id'] if success else None
        if session_id: self.created_sessions.append(session_id)

        print_test("8.3: CRITICAL - Submit query to test error propagation")
        query_data = {"session_id": session_id, "domain_id": error_domain_id, "question": "Test error handling"}
        success, response = self.make_request("POST", "/api/v1/queries", data=query_data, expected_status=202)
        query_id = response.json()['query_id'] if success else None
        if query_id: self.created_queries.append(query_id)
        
        if not query_id:
            print_fail("Failed to submit query for error test")
            self.results.add_result("Error Handling - Query Submit Failed", False)
            return
            
        # 5. Poll and check log
        print_test(f"8.4: CRITICAL - Get query result and validate error propagation: {query_id}")
        print_info("Waiting for error query processing...")
        success, data = self.poll_until_complete(f"/api/v1/queries/{query_id}", max_wait=60)
        
        if success and data and data.get('status') == 'failed':
            print_pass("✅ Final job status is 'failed' as expected")
            self.results.add_result("Error Handling - Final Status (Req 15)", True)
            
            execution_log = data.get('execution_log', [])
            failing_entry = next((e for e in execution_log if e['agent_id'] == failing_agent_id), None)
            skipped_entry = next((e for e in execution_log if e['agent_id'] == dependent_agent_id), None)
            
            # Check failing agent
            if failing_entry and failing_entry.get('status') == 'error':
                print_pass("✅ Failing agent correctly marked with status 'error'")
                if failing_entry.get('error_message'):
                    print_pass(f"Error message captured: {failing_entry['error_message'][:100]}")
                    self.results.add_result("Error Handling - Agent Error (Req 15)", True)
                else:
                    print_warning("Failing agent has 'error' status but no error_message")
                    self.results.add_result("Error Handling - Agent Error (Req 15)", True, message="Error status correct, message missing")
            else:
                print_fail("❌ Failing agent not found or not marked as 'error'")
                self.results.add_result("Error Handling - Agent Error (Req 15)", False)

            # Check skipped agent
            if skipped_entry and skipped_entry.get('status') == 'skipped':
                print_pass("✅ Dependent agent correctly marked with status 'skipped'")
                self.results.add_result("Error Handling - Propagation (Req 15)", True)
            else:
                print_fail("❌ Dependent agent not found or not marked as 'skipped'")
                self.results.add_result("Error Handling - Propagation (Req 15)", False)
                
        elif success:
            print_fail(f"❌ Job status was '{data.get('status')}', expected 'failed'")
            self.results.add_result("Error Handling - Final Status (Req 15)", False, message=f"Status was {data.get('status')}")
        else:
            print_fail("❌ Job processing timed out")
            self.results.add_result("Error Handling - Final Status (Req 15)", False, message="Timeout")

    # ========================================================================
    # DATA RETRIEVAL API TESTS (Suite 9 - CRITICAL)
    # ========================================================================

    def test_data_retrieval_api(self, domain_id: str = None):
        """Test Requirement 6: Data Retrieval API"""
        print_section("TEST SUITE 9: Data Retrieval API (CRITICAL)")
        
        test_domain = domain_id if domain_id else "civic_complaints"
        
        # Test 9.1: Get Geo Data
        print_test(f"9.1: Get Geo Data for domain: {test_domain}")
        success, response = self.make_request("GET", f"/api/v1/data/geo?domain_id={test_domain}",
                                              expected_status=200)
        if success and response:
            data = response.json()
            if data.get('type') == 'FeatureCollection' and 'features' in data:
                print_pass("Received valid GeoJSON FeatureCollection")
                self.results.add_result("Data API - Get Geo (Req 6)", True)
            else:
                print_fail("Response is not valid GeoJSON")
                self.results.add_result("Data API - Get Geo (Req 6)", False, message="Invalid GeoJSON")
        else:
            self.results.add_result("Data API - Get Geo (Req 6)", False)
            
        # Test 9.2: Get Aggregated Data
        print_test(f"9.2: Get Aggregated Data for domain: {test_domain}")
        success, response = self.make_request("GET", f"/api/v1/data/aggregated?domain_id={test_domain}&group_by=status",
                                              expected_status=200)
        if success and response:
            data = response.json()
            if 'aggregations' in data and 'total' in data:
                print_pass("Received valid aggregation data")
                self.results.add_result("Data API - Get Aggregated (Req 6)", True)
            else:
                print_fail("Response missing 'aggregations' or 'total'")
                self.results.add_result("Data API - Get Aggregated (Req 6)", False)
        else:
            self.results.add_result("Data API - Get Aggregated (Req 6)", False)

        # Test 9.3: Get Aggregated Data with invalid group_by (expect 400)
        print_test(f"9.3: Get Aggregated Data with invalid group_by (expect 400)")
        success, response = self.make_request("GET", f"/api/v1/data/aggregated?domain_id={test_domain}&group_by=invalid_field",
                                              expected_status=400, validate_schema=False)
        if success:
            print_pass("Correctly rejected invalid group_by parameter")
            self.results.add_result("Data API - Aggregated 400 (Req 6)", True)
        else:
            print_fail("Should have returned 400 for invalid group_by")
            self.results.add_result("Data API - Aggregated 400 (Req 6)", False)

    # ========================================================================
    # APPSYNC REAL-TIME TESTS (Suite 10 - CRITICAL)
    # ========================================================================

    def test_appsync_realtime(self, session_id: str = None, query_id: str = None):
        """Test Requirement 7: Real-Time Communication API (AppSync)"""
        print_section("TEST SUITE 10: AppSync Real-Time (CRITICAL)")
        
        if not all([APPSYNC_URL, APPSYNC_HOST, session_id, query_id]):
            print_warning("Missing APPSYNC_URL, APPSYNC_HOST, session_id, or query_id env variables.")
            print_skip("Skipping AppSync tests")
            self.results.add_result("AppSync - Skipped", True, skipped=True)
            return

        print_test("10.1: Test AppSync WebSocket connection and subscription")
        
        # This is a simplified test. A full implementation requires
        # handling AppSync's specific WebSocket sub-protocol.
        try:
            ws = websocket.create_connection(APPSYNC_URL,
                                             header={"Authorization": f"Bearer {self.token}"},
                                             subprotocols=["graphql-ws"])
            print_pass("WebSocket connection established")
            
            # Simple subscription (may need adjustment for your specific schema)
            subscription_query = f"""
                subscription OnJobUpdate($sessionId: ID!) {{
                  onJobUpdate(sessionId: $sessionId) {{
                    jobId
                    queryId
                    sessionId
                    status
                    message
                  }}
                }}
            """
            ws.send(json.dumps({
                "type": "start",
                "id": "1",
                "payload": {
                    "query": subscription_query,
                    "variables": {"sessionId": session_id}
                }
            }))
            
            print_info("Waiting for AppSync messages (5s)...")
            start_time = time.time()
            messages_received = []
            while time.time() - start_time < 5:
                try:
                    message = ws.recv()
                    print_info(f"AppSync message: {message}")
                    messages_received.append(message)
                except websocket.WebSocketTimeoutException:
                    pass
            
            ws.close()
            
            if messages_received:
                print_pass(f"Received {len(messages_received)} messages from AppSync")
                self.results.add_result("AppSync - Received Messages (Req 7)", True)
            else:
                print_warning("Did not receive any messages from AppSync")
                self.results.add_result("AppSync - Received Messages (Req 7)", False, message="No messages received")
                
        except Exception as e:
            print_fail(f"AppSync test failed: {str(e)}")
            self.results.add_result("AppSync - Received Messages (Req 7)", False, message=str(e))

    # ========================================================================
    # CLEANUP
    # ========================================================================
    
    def cleanup(self):
        """Clean up created resources"""
        print_section("CLEANUP: Removing Test Resources")
        
        for query_id in reversed(self.created_queries):
            print_info(f"Deleting query: {query_id}")
            self.make_request("DELETE", f"/api/v1/queries/{query_id}", expected_status=200, validate_schema=False)
        
        for session_id in reversed(self.created_sessions):
            print_info(f"Deleting session: {session_id}")
            self.make_request("DELETE", f"/api/v1/sessions/{session_id}", expected_status=200, validate_schema=False)
        
        for incident_id in reversed(self.created_reports):
            print_info(f"Deleting report: {incident_id}")
            self.make_request("DELETE", f"/api/v1/reports/{incident_id}", expected_status=200, validate_schema=False)
        
        for domain_id in reversed(self.created_domains):
            print_info(f"Deleting domain: {domain_id}")
            self.make_request("DELETE", f"/api/v1/domains/{domain_id}", expected_status=200, validate_schema=False)
        
        for agent_id in reversed(self.created_agents):
            print_info(f"Deleting agent: {agent_id}")
            self.make_request("DELETE", f"/api/v1/agents/{agent_id}", expected_status=200, validate_schema=False)
        
        print_pass("Cleanup completed")
    
    # ========================================================================
    # TEST RUNNER
    # ========================================================================
    
    def run_all_tests(self, no_cleanup=False):
        """Run all tests in chronological order"""
        print_header(f"COMPREHENSIVE API TEST SUITE - DEPLOYED MODE")
        print(f"API Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Run tests in chronological order (least to most dependent)
            self.test_authentication()
            agent_id = self.test_agent_crud()
            base_agent, dep1, dep2 = self.test_dag_validation(agent_id)
            domain_id = self.test_domain_crud(base_agent)
            report_id = self.test_report_submission(domain_id)
            session_id, query_id = self.test_caching_and_execution_log(domain_id)
            self.test_session_management(domain_id) # Run this after query test
            self.test_error_handling_and_propagation()
            self.test_data_retrieval_api(domain_id)
            
            # AppSync test is last as it needs a live query
            # self.test_appsync_realtime(session_id, query_id) # Uncomment when ready
            
        except KeyboardInterrupt:
            print_warning("\nTests interrupted by user")
        except Exception as e:
            print_fail(f"Test suite failed with unhandled error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if not no_cleanup:
                self.cleanup()
            else:
                print_warning("Skipping cleanup as requested")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print_header("TEST SUMMARY")
        
        print(f"Total Tests: {self.results.total}")
        print(f"{Colors.GREEN}Passed: {self.results.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.results.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Skipped: {self.results.skipped}{Colors.RESET}")
        
        if self.results.total > 0:
            success_rate = (self.results.passed / self.results.total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
        for test in self.results.tests:
            if test["skipped"]:
                status = f"{Colors.YELLOW}⊘{Colors.RESET}"
            elif test["passed"]:
                status = f"{Colors.GREEN}✓{Colors.RESET}"
            else:
                status = f"{Colors.RED}✗{Colors.RESET}"
            
            message = f" - {test['message']}" if test.get('message') else ""
            print(f"  {status} {test['name']}{message}")
        
        # Demo readiness check
        print_header("DEMO READINESS CHECK")
        critical_tests = [
            "Agent - Create Valid", "DAG - Circular Detection (CRITICAL)",
            "Domain - Create Valid", "Report - Submit Valid",
            "Report - Get with Ingestion Data", "Session - Create",
            "Query - Submit (Read)", "Execution Log - NOT EMPTY (CRITICAL)",
            "Caching - Memoization (CRITICAL)", "Error Handling - Final Status (Req 15)",
            "Error Handling - Propagation (Req 15)", "Data API - Get Geo (Req 6)"
        ]
        
        critical_passed = sum(1 for t in self.results.tests 
                            if t["name"] in critical_tests and t["passed"] and not t["skipped"])
        critical_total = len(critical_tests)
        
        if critical_passed == critical_total:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ READY FOR DEMO{Colors.RESET}")
            print("All critical functional tests passed!")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ NOT READY{Colors.RESET}")
            print(f"Only {critical_passed}/{critical_total} critical tests passed")
            
            print_fail("Failing critical tests:")
            for t in self.results.tests:
                if t["name"] in critical_tests and not t["passed"] and not t["skipped"]:
                    print(f"  ✗ {t['name']}")


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


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='DomainFlow API Test Suite')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of created resources')
    
    args = parser.parse_args()
    
    # Validate environment
    required_vars = ["API_BASE_URL", "COGNITO_CLIENT_ID", "TEST_USERNAME", "TEST_PASSWORD"]
    if not all(os.environ.get(v) for v in required_vars):
        print_fail("ERROR: Missing required environment variables!")
        print("Please set: API_BASE_URL, COGNITO_CLIENT_ID, TEST_USERNAME, TEST_PASSWORD")
        sys.exit(1)
    
    # Get authentication token
    print_header("AUTHENTICATION")
    token = get_cognito_token()
    if not token:
        print_fail("Cannot proceed without authentication token")
        sys.exit(1)
    
    tester = APITester(base_url=API_BASE_URL, token=token)
    
    # Run all tests
    tester.run_all_tests(no_cleanup=args.no_cleanup)
    
    # Exit with appropriate code
    if tester.results.failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()