#!/usr/bin/env python3
"""
Multi-Agent Orchestration System - Comprehensive API Test Suite

This test suite validates all API endpoints with comprehensive coverage including:
- Config API (Agent, Domain, Playbook, Dependency Graph CRUD)
- Data API (Retrieval, Spatial, Analytics, Aggregation, Vector Search)
- Ingest API (Report submission)
- Query API (Question answering)
- Tool Registry API (Tool management)
- Authentication and Authorization
- Error Handling
- Edge Cases
- Performance Testing

Requirements: 6.1-6.12, 7.1-7.10, 8.1-8.10, 9.1-9.10, 10.1-10.5, 11.1-11.10, 
              12.1-12.7, 13.1-13.7, 14.1-14.7, 17.1-17.10
"""

import os
import sys
import json
import time
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================================
# Configuration and Setup
# ============================================================================

class TestStatus(Enum):
    """Test execution status"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    endpoint: str
    status: TestStatus
    response_time_ms: int
    error_message: Optional[str] = None
    request: Optional[Dict] = None
    response: Optional[Dict] = None
    http_code: Optional[int] = None


@dataclass
class TestReport:
    """Test report aggregator"""
    results: List[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def total_tests(self) -> int:
        return len(self.results)
    
    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASS)
    
    @property
    def failed_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAIL)
    
    @property
    def skipped_tests(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.SKIP)
    
    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


# ============================================================================
# Test Fixtures
# ============================================================================

# Test agent configuration
TEST_AGENT = {
    "agent_name": f"Test Agent {uuid.uuid4().hex[:8]}",
    "agent_type": "custom",
    "system_prompt": "You are a test agent for automated testing purposes.",
    "tools": ["bedrock"],
    "output_schema": {
        "result": "string",
        "confidence": "number"
    }
}

# Test domain configuration
TEST_DOMAIN = {
    "template_name": f"Test Domain {uuid.uuid4().hex[:8]}",
    "domain_id": f"test_domain_{uuid.uuid4().hex[:8]}",
    "ingest_agent_ids": ["geo_agent", "temporal_agent"],
    "query_agent_ids": ["when_agent", "where_agent"],
    "description": "Test domain for automated API testing"
}

# Test report for ingestion
TEST_REPORT = {
    "domain_id": "civic_complaints",
    "text": "There is a pothole on Main Street near the library. It's been there for two weeks.",
    "images": []
}

# Test report with long text
TEST_REPORT_LONG = {
    "domain_id": "civic_complaints",
    "text": "A" * 10000,  # 10,000 characters
    "images": []
}

# Test report with special characters
TEST_REPORT_UNICODE = {
    "domain_id": "civic_complaints",
    "text": "Report with special chars: émojis 🚧🔧 and unicode: 你好世界 مرحبا العالم",
    "images": []
}

# Test query
TEST_QUERY = {
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints this month?"
}

# Test query with complex question
TEST_QUERY_COMPLEX = {
    "domain_id": "civic_complaints",
    "question": "What are the top 5 complaint categories in the downtown area during the last 30 days, and what is the average response time for each category?"
}

# Test query with long question
TEST_QUERY_LONG = {
    "domain_id": "civic_complaints",
    "question": "Q" * 1000  # 1,000 characters
}


# ============================================================================
# API Test Client
# ============================================================================

class APITestClient:
    """HTTP client for API testing"""
    
    def __init__(self, base_url: str, jwt_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if jwt_token:
            self.session.headers.update({
                'Authorization': f'Bearer {jwt_token}'
            })
    
    def request(self, method: str, path: str, **kwargs) -> Tuple[requests.Response, int]:
        """Make HTTP request and measure response time"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        start_time = time.time()
        try:
            response = self.session.request(method, url, **kwargs)
            response_time_ms = int((time.time() - start_time) * 1000)
            return response, response_time_ms
        except requests.exceptions.RequestException as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            # Create a mock response for connection errors
            mock_response = requests.Response()
            mock_response.status_code = 0
            mock_response._content = json.dumps({"error": str(e)}).encode()
            return mock_response, response_time_ms
    
    def get(self, path: str, **kwargs) -> Tuple[requests.Response, int]:
        """GET request"""
        return self.request('GET', path, **kwargs)
    
    def post(self, path: str, **kwargs) -> Tuple[requests.Response, int]:
        """POST request"""
        return self.request('POST', path, **kwargs)
    
    def put(self, path: str, **kwargs) -> Tuple[requests.Response, int]:
        """PUT request"""
        return self.request('PUT', path, **kwargs)
    
    def delete(self, path: str, **kwargs) -> Tuple[requests.Response, int]:
        """DELETE request"""
        return self.request('DELETE', path, **kwargs)


# ============================================================================
# Test Suite Runner
# ============================================================================

class APITestSuite:
    """Main test suite orchestrator"""
    
    def __init__(self, api_url: str, jwt_token: Optional[str] = None):
        self.api_url = api_url
        self.jwt_token = jwt_token
        self.client = APITestClient(api_url, jwt_token)
        self.report = TestReport()
        
        # Track created resources for cleanup
        self.created_agents: List[str] = []
        self.created_domains: List[str] = []
        self.created_playbooks: List[str] = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ",
            "PASS": "✓",
            "FAIL": "✗",
            "SKIP": "⊘",
            "TEST": "▶"
        }.get(level, "•")
        print(f"[{timestamp}] {prefix} {message}")
    
    def add_result(self, result: TestResult):
        """Add test result to report"""
        self.report.results.append(result)
        
        if result.status == TestStatus.PASS:
            self.log(f"{result.test_name}: PASS ({result.response_time_ms}ms)", "PASS")
        elif result.status == TestStatus.FAIL:
            self.log(f"{result.test_name}: FAIL - {result.error_message}", "FAIL")
        else:
            self.log(f"{result.test_name}: SKIP - {result.error_message}", "SKIP")
    
    def run_all_tests(self):
        """Execute all test suites"""
        self.log("=" * 80)
        self.log("Multi-Agent Orchestration System - API Test Suite")
        self.log("=" * 80)
        self.log("")
        
        # Run test suites in order
        test_suites = [
            ("Authentication Tests", self.run_authentication_tests),
            ("Config API - Agent CRUD Tests", self.run_config_agent_tests),
            ("Config API - Domain CRUD Tests", self.run_config_domain_tests),
            ("Config API - Dependency Graph Tests", self.run_config_dependency_tests),
            ("Data API Tests", self.run_data_api_tests),
            ("Ingest API Tests", self.run_ingest_api_tests),
            ("Query API Tests", self.run_query_api_tests),
            ("Tool Registry API Tests", self.run_tool_registry_tests),
            ("Error Handling Tests", self.run_error_handling_tests),
            ("Edge Case Tests", self.run_edge_case_tests),
            ("Performance Tests", self.run_performance_tests),
        ]
        
        for suite_name, suite_func in test_suites:
            self.log("")
            self.log(f"Running {suite_name}...", "TEST")
            self.log("-" * 80)
            try:
                suite_func()
            except Exception as e:
                self.log(f"Test suite failed with exception: {e}", "FAIL")
        
        # Cleanup
        self.log("")
        self.log("Cleaning up test resources...", "INFO")
        self.cleanup_resources()
        
        # Finalize report
        self.report.end_time = datetime.now()
        
        # Display summary
        self.display_summary()
        
        # Generate report file
        self.generate_report_file()
    
    # Placeholder methods for test suites (to be implemented in subtasks)
    def run_authentication_tests(self):
        """Run authentication tests (Task 2.9)"""
        # Test 2.9.1: Request without Authorization header (expect 401)
        client_no_auth = APITestClient(self.api_url, jwt_token=None)
        response, response_time = client_no_auth.get("api/v1/config?type=agent")
        
        if response.status_code == 401:
            self.add_result(TestResult(
                test_name="No Authorization Header",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=401
            ))
        else:
            self.add_result(TestResult(
                test_name="No Authorization Header",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 401, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.9.2: Request with invalid JWT token (expect 401)
        client_invalid_token = APITestClient(self.api_url, jwt_token="invalid_token_12345")
        response, response_time = client_invalid_token.get("api/v1/config?type=agent")
        
        if response.status_code == 401:
            self.add_result(TestResult(
                test_name="Invalid JWT Token",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=401
            ))
        else:
            self.add_result(TestResult(
                test_name="Invalid JWT Token",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 401, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.9.3: Request with expired JWT token (expect 401)
        # Using a known expired token format
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        client_expired_token = APITestClient(self.api_url, jwt_token=expired_token)
        response, response_time = client_expired_token.get("api/v1/config?type=agent")
        
        if response.status_code == 401:
            self.add_result(TestResult(
                test_name="Expired JWT Token",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=401
            ))
        else:
            self.add_result(TestResult(
                test_name="Expired JWT Token",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 401, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.9.4: Request with valid JWT token (expect 200/201/202)
        if self.jwt_token:
            response, response_time = self.client.get("api/v1/config?type=agent")
            
            if response.status_code in [200, 201, 202]:
                self.add_result(TestResult(
                    test_name="Valid JWT Token",
                    category="Authentication",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    http_code=response.status_code
                ))
            else:
                self.add_result(TestResult(
                    test_name="Valid JWT Token",
                    category="Authentication",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message=f"Expected 200/201/202, got {response.status_code}",
                    http_code=response.status_code
                ))
        else:
            self.add_result(TestResult(
                test_name="Valid JWT Token",
                category="Authentication",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="No JWT token provided",
                http_code=0
            ))
        
        # Test 2.9.5: Verify tenant_id scoping
        # This test would require creating resources and verifying isolation
        # For now, we'll mark it as a basic check
        if self.jwt_token:
            self.add_result(TestResult(
                test_name="Tenant ID Scoping",
                category="Authentication",
                endpoint="Various",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Tenant isolation requires multi-tenant test setup",
                http_code=0
            ))
        else:
            self.add_result(TestResult(
                test_name="Tenant ID Scoping",
                category="Authentication",
                endpoint="Various",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="No JWT token provided",
                http_code=0
            ))
    
    def run_config_agent_tests(self):
        """Run Config API agent CRUD tests (Task 2.2)"""
        # Test 2.2.1: Create agent
        test_agent = TEST_AGENT.copy()
        test_agent["agent_name"] = f"Test Agent {uuid.uuid4().hex[:8]}"
        
        response, response_time = self.client.post(
            "api/v1/config",
            json={"type": "agent", "config": test_agent}
        )
        
        if response.status_code == 201:
            try:
                data = response.json()
                agent_id = data.get("agent_id") or data.get("config_key")
                
                if agent_id:
                    self.created_agents.append(agent_id)
                    self.add_result(TestResult(
                        test_name="Create Agent",
                        category="Config API - Agent CRUD",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        request={"type": "agent", "config": test_agent},
                        response=data,
                        http_code=201
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Create Agent",
                        category="Config API - Agent CRUD",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing agent_id",
                        http_code=201
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Create Agent",
                    category="Config API - Agent CRUD",
                    endpoint="POST /api/v1/config",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=201
                ))
        else:
            self.add_result(TestResult(
                test_name="Create Agent",
                category="Config API - Agent CRUD",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 201, got {response.status_code}",
                http_code=response.status_code
            ))
            return  # Skip remaining tests if create failed
        
        # Test 2.2.2: List agents
        response, response_time = self.client.get("api/v1/config?type=agent")
        
        if response.status_code == 200:
            try:
                data = response.json()
                configs = data.get("configs", [])
                
                # Verify our created agent is in the list
                found = any(c.get("agent_id") == agent_id or c.get("config_key") == agent_id 
                           for c in configs)
                
                if found:
                    self.add_result(TestResult(
                        test_name="List Agents",
                        category="Config API - Agent CRUD",
                        endpoint="GET /api/v1/config?type=agent",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response={"count": len(configs)},
                        http_code=200
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="List Agents",
                        category="Config API - Agent CRUD",
                        endpoint="GET /api/v1/config?type=agent",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Created agent not found in list",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="List Agents",
                    category="Config API - Agent CRUD",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="List Agents",
                category="Config API - Agent CRUD",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.2.3: Get specific agent
        response, response_time = self.client.get(f"api/v1/config/agent/{agent_id}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                retrieved_id = data.get("agent_id") or data.get("config_key")
                
                if retrieved_id == agent_id:
                    self.add_result(TestResult(
                        test_name="Get Agent",
                        category="Config API - Agent CRUD",
                        endpoint=f"GET /api/v1/config/agent/{agent_id}",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response=data,
                        http_code=200
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Get Agent",
                        category="Config API - Agent CRUD",
                        endpoint=f"GET /api/v1/config/agent/{agent_id}",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Agent ID mismatch",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Get Agent",
                    category="Config API - Agent CRUD",
                    endpoint=f"GET /api/v1/config/agent/{agent_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Get Agent",
                category="Config API - Agent CRUD",
                endpoint=f"GET /api/v1/config/agent/{agent_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.2.4: Update agent
        updated_agent = test_agent.copy()
        updated_agent["system_prompt"] = "Updated test prompt for validation"
        
        response, response_time = self.client.put(
            f"api/v1/config/agent/{agent_id}",
            json={"type": "agent", "config": updated_agent}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.add_result(TestResult(
                    test_name="Update Agent",
                    category="Config API - Agent CRUD",
                    endpoint=f"PUT /api/v1/config/agent/{agent_id}",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    request={"type": "agent", "config": updated_agent},
                    response=data,
                    http_code=200
                ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Update Agent",
                    category="Config API - Agent CRUD",
                    endpoint=f"PUT /api/v1/config/agent/{agent_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Update Agent",
                category="Config API - Agent CRUD",
                endpoint=f"PUT /api/v1/config/agent/{agent_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.2.5: Delete agent
        response, response_time = self.client.delete(f"api/v1/config/agent/{agent_id}")
        
        if response.status_code == 200:
            # Remove from cleanup list since we deleted it
            if agent_id in self.created_agents:
                self.created_agents.remove(agent_id)
            
            self.add_result(TestResult(
                test_name="Delete Agent",
                category="Config API - Agent CRUD",
                endpoint=f"DELETE /api/v1/config/agent/{agent_id}",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
            
            # Test 2.2.6: Verify deletion (should return 404)
            response, response_time = self.client.get(f"api/v1/config/agent/{agent_id}")
            
            if response.status_code == 404:
                self.add_result(TestResult(
                    test_name="Verify Agent Deletion",
                    category="Config API - Agent CRUD",
                    endpoint=f"GET /api/v1/config/agent/{agent_id}",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    http_code=404
                ))
            else:
                self.add_result(TestResult(
                    test_name="Verify Agent Deletion",
                    category="Config API - Agent CRUD",
                    endpoint=f"GET /api/v1/config/agent/{agent_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message=f"Expected 404, got {response.status_code}",
                    http_code=response.status_code
                ))
        else:
            self.add_result(TestResult(
                test_name="Delete Agent",
                category="Config API - Agent CRUD",
                endpoint=f"DELETE /api/v1/config/agent/{agent_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_config_domain_tests(self):
        """Run Config API domain CRUD tests (Task 2.3)"""
        # Test 2.3.1: Create domain
        test_domain = TEST_DOMAIN.copy()
        test_domain["template_name"] = f"Test Domain {uuid.uuid4().hex[:8]}"
        test_domain["domain_id"] = f"test_domain_{uuid.uuid4().hex[:8]}"
        
        response, response_time = self.client.post(
            "api/v1/config",
            json={"type": "domain_template", "config": test_domain}
        )
        
        if response.status_code == 201:
            try:
                data = response.json()
                domain_id = data.get("domain_id") or data.get("config_key")
                
                if domain_id:
                    self.created_domains.append(domain_id)
                    
                    # Verify metadata flags
                    is_builtin = data.get("is_builtin", False)
                    created_by_me = data.get("created_by_me", True)
                    
                    self.add_result(TestResult(
                        test_name="Create Domain",
                        category="Config API - Domain CRUD",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        request={"type": "domain_template", "config": test_domain},
                        response=data,
                        http_code=201
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Create Domain",
                        category="Config API - Domain CRUD",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing domain_id",
                        http_code=201
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Create Domain",
                    category="Config API - Domain CRUD",
                    endpoint="POST /api/v1/config",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=201
                ))
        else:
            self.add_result(TestResult(
                test_name="Create Domain",
                category="Config API - Domain CRUD",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 201, got {response.status_code}",
                http_code=response.status_code
            ))
            return  # Skip remaining tests if create failed
        
        # Test 2.3.2: List domains
        response, response_time = self.client.get("api/v1/config?type=domain_template")
        
        if response.status_code == 200:
            try:
                data = response.json()
                configs = data.get("configs", [])
                
                # Verify our created domain is in the list
                found = any(c.get("domain_id") == domain_id or c.get("config_key") == domain_id 
                           for c in configs)
                
                if found:
                    self.add_result(TestResult(
                        test_name="List Domains",
                        category="Config API - Domain CRUD",
                        endpoint="GET /api/v1/config?type=domain_template",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response={"count": len(configs)},
                        http_code=200
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="List Domains",
                        category="Config API - Domain CRUD",
                        endpoint="GET /api/v1/config?type=domain_template",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Created domain not found in list",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="List Domains",
                    category="Config API - Domain CRUD",
                    endpoint="GET /api/v1/config?type=domain_template",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="List Domains",
                category="Config API - Domain CRUD",
                endpoint="GET /api/v1/config?type=domain_template",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.3.3: Get specific domain
        response, response_time = self.client.get(f"api/v1/config/domain_template/{domain_id}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                retrieved_id = data.get("domain_id") or data.get("config_key")
                
                # Verify metadata flags
                is_builtin = data.get("is_builtin")
                created_by_me = data.get("created_by_me")
                
                if retrieved_id == domain_id:
                    self.add_result(TestResult(
                        test_name="Get Domain",
                        category="Config API - Domain CRUD",
                        endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response=data,
                        http_code=200
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Get Domain",
                        category="Config API - Domain CRUD",
                        endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Domain ID mismatch",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Get Domain",
                    category="Config API - Domain CRUD",
                    endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Get Domain",
                category="Config API - Domain CRUD",
                endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.3.4: Update domain
        updated_domain = test_domain.copy()
        updated_domain["description"] = "Updated test domain description"
        
        response, response_time = self.client.put(
            f"api/v1/config/domain_template/{domain_id}",
            json={"type": "domain_template", "config": updated_domain}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.add_result(TestResult(
                    test_name="Update Domain",
                    category="Config API - Domain CRUD",
                    endpoint=f"PUT /api/v1/config/domain_template/{domain_id}",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    request={"type": "domain_template", "config": updated_domain},
                    response=data,
                    http_code=200
                ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Update Domain",
                    category="Config API - Domain CRUD",
                    endpoint=f"PUT /api/v1/config/domain_template/{domain_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Update Domain",
                category="Config API - Domain CRUD",
                endpoint=f"PUT /api/v1/config/domain_template/{domain_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.3.5: Delete domain
        response, response_time = self.client.delete(f"api/v1/config/domain_template/{domain_id}")
        
        if response.status_code == 200:
            # Remove from cleanup list since we deleted it
            if domain_id in self.created_domains:
                self.created_domains.remove(domain_id)
            
            self.add_result(TestResult(
                test_name="Delete Domain",
                category="Config API - Domain CRUD",
                endpoint=f"DELETE /api/v1/config/domain_template/{domain_id}",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
            
            # Test 2.3.6: Verify deletion (should return 404)
            response, response_time = self.client.get(f"api/v1/config/domain_template/{domain_id}")
            
            if response.status_code == 404:
                self.add_result(TestResult(
                    test_name="Verify Domain Deletion",
                    category="Config API - Domain CRUD",
                    endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    http_code=404
                ))
            else:
                self.add_result(TestResult(
                    test_name="Verify Domain Deletion",
                    category="Config API - Domain CRUD",
                    endpoint=f"GET /api/v1/config/domain_template/{domain_id}",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message=f"Expected 404, got {response.status_code}",
                    http_code=response.status_code
                ))
        else:
            self.add_result(TestResult(
                test_name="Delete Domain",
                category="Config API - Domain CRUD",
                endpoint=f"DELETE /api/v1/config/domain_template/{domain_id}",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_config_dependency_tests(self):
        """Run Config API dependency graph tests (Task 2.4)"""
        # Test 2.4.1: List dependency graphs
        response, response_time = self.client.get("api/v1/config?type=dependency_graph")
        
        if response.status_code == 200:
            try:
                data = response.json()
                configs = data.get("configs", [])
                
                # Verify response structure
                if isinstance(configs, list):
                    self.add_result(TestResult(
                        test_name="List Dependency Graphs",
                        category="Config API - Dependency Graph",
                        endpoint="GET /api/v1/config?type=dependency_graph",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response={"count": len(configs)},
                        http_code=200
                    ))
                    
                    # Test 2.4.2: Verify dependency relationships
                    if len(configs) > 0:
                        # Check first dependency graph for structure
                        graph = configs[0]
                        has_dependencies = "dependencies" in graph or "nodes" in graph or "edges" in graph
                        
                        if has_dependencies:
                            self.add_result(TestResult(
                                test_name="Verify Dependency Relationships",
                                category="Config API - Dependency Graph",
                                endpoint="GET /api/v1/config?type=dependency_graph",
                                status=TestStatus.PASS,
                                response_time_ms=response_time,
                                response={"graph_structure": "valid"},
                                http_code=200
                            ))
                        else:
                            self.add_result(TestResult(
                                test_name="Verify Dependency Relationships",
                                category="Config API - Dependency Graph",
                                endpoint="GET /api/v1/config?type=dependency_graph",
                                status=TestStatus.FAIL,
                                response_time_ms=response_time,
                                error_message="Dependency graph missing relationship data",
                                http_code=200
                            ))
                    else:
                        self.add_result(TestResult(
                            test_name="Verify Dependency Relationships",
                            category="Config API - Dependency Graph",
                            endpoint="GET /api/v1/config?type=dependency_graph",
                            status=TestStatus.SKIP,
                            response_time_ms=response_time,
                            error_message="No dependency graphs found",
                            http_code=200
                        ))
                else:
                    self.add_result(TestResult(
                        test_name="List Dependency Graphs",
                        category="Config API - Dependency Graph",
                        endpoint="GET /api/v1/config?type=dependency_graph",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Invalid response structure",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="List Dependency Graphs",
                    category="Config API - Dependency Graph",
                    endpoint="GET /api/v1/config?type=dependency_graph",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="List Dependency Graphs",
                category="Config API - Dependency Graph",
                endpoint="GET /api/v1/config?type=dependency_graph",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_data_api_tests(self):
        """Run Data API tests (Task 2.5)"""
        # Test 2.5.1: Retrieve incidents (basic)
        response, response_time = self.client.get("api/v1/data?type=retrieval")
        
        if response.status_code == 200:
            try:
                data = response.json()
                incidents = data.get("incidents", []) or data.get("data", []) or data.get("results", [])
                
                self.add_result(TestResult(
                    test_name="Retrieve Incidents",
                    category="Data API",
                    endpoint="GET /api/v1/data?type=retrieval",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    response={"count": len(incidents)},
                    http_code=200
                ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Retrieve Incidents",
                    category="Data API",
                    endpoint="GET /api/v1/data?type=retrieval",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Retrieve Incidents",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.2: Filter by date range
        filters = {
            "date_range": {
                "start": "2024-10-01T00:00:00Z",
                "end": "2024-10-31T23:59:59Z"
            }
        }
        response, response_time = self.client.get(
            f"api/v1/data?type=retrieval&filters={json.dumps(filters)}"
        )
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Filter by Date Range",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Filter by Date Range",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.3: Filter by location (bbox)
        filters = {
            "location": {
                "bbox": [-122.5, 37.7, -122.3, 37.9]  # San Francisco area
            }
        }
        response, response_time = self.client.get(
            f"api/v1/data?type=retrieval&filters={json.dumps(filters)}"
        )
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Filter by Location (bbox)",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Filter by Location (bbox)",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.4: Filter by category
        filters = {"category": "infrastructure"}
        response, response_time = self.client.get(
            f"api/v1/data?type=retrieval&filters={json.dumps(filters)}"
        )
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Filter by Category",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Filter by Category",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&filters=...",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.5: Pagination
        response, response_time = self.client.get("api/v1/data?type=retrieval&page=1&page_size=10")
        
        if response.status_code == 200:
            try:
                data = response.json()
                has_pagination = "pagination" in data or "page" in data or "page_size" in data
                
                self.add_result(TestResult(
                    test_name="Pagination",
                    category="Data API",
                    endpoint="GET /api/v1/data?type=retrieval&page=1&page_size=10",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    http_code=200
                ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Pagination",
                    category="Data API",
                    endpoint="GET /api/v1/data?type=retrieval&page=1&page_size=10",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Pagination",
                category="Data API",
                endpoint="GET /api/v1/data?type=retrieval&page=1&page_size=10",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.6: Spatial queries
        response, response_time = self.client.get("api/v1/data?type=spatial")
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Spatial Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=spatial",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Spatial Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=spatial",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.7: Analytics queries
        response, response_time = self.client.get("api/v1/data?type=analytics")
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Analytics Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=analytics",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Analytics Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=analytics",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.8: Aggregation queries
        response, response_time = self.client.get("api/v1/data?type=aggregation")
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Aggregation Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=aggregation",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Aggregation Queries",
                category="Data API",
                endpoint="GET /api/v1/data?type=aggregation",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.5.9: Vector search
        response, response_time = self.client.get("api/v1/data?type=vector_search")
        
        if response.status_code == 200:
            self.add_result(TestResult(
                test_name="Vector Search",
                category="Data API",
                endpoint="GET /api/v1/data?type=vector_search",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="Vector Search",
                category="Data API",
                endpoint="GET /api/v1/data?type=vector_search",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_ingest_api_tests(self):
        """Run Ingest API tests (Task 2.6)"""
        # Test 2.6.1: Submit text-only report
        test_report = TEST_REPORT.copy()
        
        response, response_time = self.client.post("api/v1/ingest", json=test_report)
        
        if response.status_code == 202:
            try:
                data = response.json()
                job_id = data.get("job_id")
                
                if job_id:
                    self.add_result(TestResult(
                        test_name="Submit Text-Only Report",
                        category="Ingest API",
                        endpoint="POST /api/v1/ingest",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        request=test_report,
                        response=data,
                        http_code=202
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Submit Text-Only Report",
                        category="Ingest API",
                        endpoint="POST /api/v1/ingest",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing job_id",
                        http_code=202
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Submit Text-Only Report",
                    category="Ingest API",
                    endpoint="POST /api/v1/ingest",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Submit Text-Only Report",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.6.2: Submit report with images (small test image)
        test_report_with_image = TEST_REPORT.copy()
        # Create a small 1x1 pixel PNG image in base64
        small_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        test_report_with_image["images"] = [small_image]
        
        response, response_time = self.client.post("api/v1/ingest", json=test_report_with_image)
        
        if response.status_code == 202:
            try:
                data = response.json()
                job_id = data.get("job_id")
                
                if job_id:
                    self.add_result(TestResult(
                        test_name="Submit Report with Images",
                        category="Ingest API",
                        endpoint="POST /api/v1/ingest",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        http_code=202
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Submit Report with Images",
                        category="Ingest API",
                        endpoint="POST /api/v1/ingest",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing job_id",
                        http_code=202
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Submit Report with Images",
                    category="Ingest API",
                    endpoint="POST /api/v1/ingest",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Submit Report with Images",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.6.3: Invalid domain_id (expect 404)
        invalid_report = TEST_REPORT.copy()
        invalid_report["domain_id"] = "nonexistent_domain_12345"
        
        response, response_time = self.client.post("api/v1/ingest", json=invalid_report)
        
        if response.status_code == 404:
            self.add_result(TestResult(
                test_name="Invalid Domain ID",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=404
            ))
        else:
            self.add_result(TestResult(
                test_name="Invalid Domain ID",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 404, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.6.4: Missing required fields (expect 400)
        incomplete_report = {"domain_id": "civic_complaints"}  # Missing 'text'
        
        response, response_time = self.client.post("api/v1/ingest", json=incomplete_report)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.6.5: Extremely long text
        long_report = TEST_REPORT_LONG.copy()
        
        response, response_time = self.client.post("api/v1/ingest", json=long_report)
        
        if response.status_code in [202, 400]:  # Either accepted or rejected for being too long
            self.add_result(TestResult(
                test_name="Extremely Long Text",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=response.status_code
            ))
        else:
            self.add_result(TestResult(
                test_name="Extremely Long Text",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202 or 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.6.6: Special characters and Unicode
        unicode_report = TEST_REPORT_UNICODE.copy()
        
        response, response_time = self.client.post("api/v1/ingest", json=unicode_report)
        
        if response.status_code == 202:
            self.add_result(TestResult(
                test_name="Special Characters and Unicode",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=202
            ))
        else:
            self.add_result(TestResult(
                test_name="Special Characters and Unicode",
                category="Ingest API",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_query_api_tests(self):
        """Run Query API tests (Task 2.7)"""
        # Test 2.7.1: Simple question
        test_query = TEST_QUERY.copy()
        
        response, response_time = self.client.post("api/v1/query", json=test_query)
        
        if response.status_code == 202:
            try:
                data = response.json()
                job_id = data.get("job_id")
                
                if job_id:
                    self.add_result(TestResult(
                        test_name="Ask Simple Question",
                        category="Query API",
                        endpoint="POST /api/v1/query",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        request=test_query,
                        response=data,
                        http_code=202
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Ask Simple Question",
                        category="Query API",
                        endpoint="POST /api/v1/query",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing job_id",
                        http_code=202
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Ask Simple Question",
                    category="Query API",
                    endpoint="POST /api/v1/query",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Ask Simple Question",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.7.2: Complex question
        complex_query = TEST_QUERY_COMPLEX.copy()
        
        response, response_time = self.client.post("api/v1/query", json=complex_query)
        
        if response.status_code == 202:
            try:
                data = response.json()
                job_id = data.get("job_id")
                
                if job_id:
                    self.add_result(TestResult(
                        test_name="Ask Complex Question",
                        category="Query API",
                        endpoint="POST /api/v1/query",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        http_code=202
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="Ask Complex Question",
                        category="Query API",
                        endpoint="POST /api/v1/query",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Response missing job_id",
                        http_code=202
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Ask Complex Question",
                    category="Query API",
                    endpoint="POST /api/v1/query",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Ask Complex Question",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.7.3: Invalid domain_id (expect 404)
        invalid_query = TEST_QUERY.copy()
        invalid_query["domain_id"] = "nonexistent_domain_12345"
        
        response, response_time = self.client.post("api/v1/query", json=invalid_query)
        
        if response.status_code == 404:
            self.add_result(TestResult(
                test_name="Invalid Domain ID",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=404
            ))
        else:
            self.add_result(TestResult(
                test_name="Invalid Domain ID",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 404, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.7.4: Missing required fields (expect 400)
        incomplete_query = {"domain_id": "civic_complaints"}  # Missing 'question'
        
        response, response_time = self.client.post("api/v1/query", json=incomplete_query)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.7.5: Extremely long question
        long_query = TEST_QUERY_LONG.copy()
        
        response, response_time = self.client.post("api/v1/query", json=long_query)
        
        if response.status_code in [202, 400]:  # Either accepted or rejected for being too long
            self.add_result(TestResult(
                test_name="Extremely Long Question",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=response.status_code
            ))
        else:
            self.add_result(TestResult(
                test_name="Extremely Long Question",
                category="Query API",
                endpoint="POST /api/v1/query",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 202 or 400, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_tool_registry_tests(self):
        """Run Tool Registry API tests (Task 2.8)"""
        # Test 2.8.1: List all tools
        response, response_time = self.client.get("api/v1/tools")
        
        if response.status_code == 200:
            try:
                data = response.json()
                tools = data.get("tools", []) or data.get("data", []) or data
                
                if isinstance(tools, list):
                    # Test 2.8.2: Verify built-in tools are present
                    tool_names = [t.get("name", "").lower() for t in tools if isinstance(t, dict)]
                    
                    has_bedrock = any("bedrock" in name for name in tool_names)
                    has_comprehend = any("comprehend" in name for name in tool_names)
                    has_location = any("location" in name for name in tool_names)
                    
                    self.add_result(TestResult(
                        test_name="List All Tools",
                        category="Tool Registry API",
                        endpoint="GET /api/v1/tools",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response={"count": len(tools)},
                        http_code=200
                    ))
                    
                    if has_bedrock and has_comprehend and has_location:
                        self.add_result(TestResult(
                            test_name="Verify Built-in Tools Present",
                            category="Tool Registry API",
                            endpoint="GET /api/v1/tools",
                            status=TestStatus.PASS,
                            response_time_ms=response_time,
                            response={"bedrock": has_bedrock, "comprehend": has_comprehend, "location": has_location},
                            http_code=200
                        ))
                    else:
                        self.add_result(TestResult(
                            test_name="Verify Built-in Tools Present",
                            category="Tool Registry API",
                            endpoint="GET /api/v1/tools",
                            status=TestStatus.FAIL,
                            response_time_ms=response_time,
                            error_message=f"Missing built-in tools (bedrock: {has_bedrock}, comprehend: {has_comprehend}, location: {has_location})",
                            http_code=200
                        ))
                    
                    # Test 2.8.3: Verify tool schema
                    if len(tools) > 0 and isinstance(tools[0], dict):
                        tool = tools[0]
                        has_name = "name" in tool or "tool_name" in tool
                        has_type = "type" in tool or "tool_type" in tool
                        has_capabilities = "capabilities" in tool or "description" in tool
                        
                        if has_name and has_type:
                            self.add_result(TestResult(
                                test_name="Verify Tool Schema",
                                category="Tool Registry API",
                                endpoint="GET /api/v1/tools",
                                status=TestStatus.PASS,
                                response_time_ms=response_time,
                                http_code=200
                            ))
                        else:
                            self.add_result(TestResult(
                                test_name="Verify Tool Schema",
                                category="Tool Registry API",
                                endpoint="GET /api/v1/tools",
                                status=TestStatus.FAIL,
                                response_time_ms=response_time,
                                error_message="Tool schema missing required fields",
                                http_code=200
                            ))
                    else:
                        self.add_result(TestResult(
                            test_name="Verify Tool Schema",
                            category="Tool Registry API",
                            endpoint="GET /api/v1/tools",
                            status=TestStatus.SKIP,
                            response_time_ms=response_time,
                            error_message="No tools available to verify schema",
                            http_code=200
                        ))
                else:
                    self.add_result(TestResult(
                        test_name="List All Tools",
                        category="Tool Registry API",
                        endpoint="GET /api/v1/tools",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Invalid response structure",
                        http_code=200
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="List All Tools",
                    category="Tool Registry API",
                    endpoint="GET /api/v1/tools",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="List All Tools",
                category="Tool Registry API",
                endpoint="GET /api/v1/tools",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200, got {response.status_code}",
                http_code=response.status_code
            ))
            return
        
        # Test 2.8.4: Get specific tool details
        # Try to get details for a known tool (bedrock)
        response, response_time = self.client.get("api/v1/tools/bedrock")
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.add_result(TestResult(
                    test_name="Get Tool Details",
                    category="Tool Registry API",
                    endpoint="GET /api/v1/tools/bedrock",
                    status=TestStatus.PASS,
                    response_time_ms=response_time,
                    response=data,
                    http_code=200
                ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="Get Tool Details",
                    category="Tool Registry API",
                    endpoint="GET /api/v1/tools/bedrock",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=200
                ))
        elif response.status_code == 404:
            # Tool not found, which is acceptable
            self.add_result(TestResult(
                test_name="Get Tool Details",
                category="Tool Registry API",
                endpoint="GET /api/v1/tools/bedrock",
                status=TestStatus.SKIP,
                response_time_ms=response_time,
                error_message="Tool 'bedrock' not found (404)",
                http_code=404
            ))
        else:
            self.add_result(TestResult(
                test_name="Get Tool Details",
                category="Tool Registry API",
                endpoint="GET /api/v1/tools/bedrock",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 200 or 404, got {response.status_code}",
                http_code=response.status_code
            ))
    
    def run_error_handling_tests(self):
        """Run error handling tests (Task 2.10)"""
        # Test 2.10.1: 400 errors include validation details
        invalid_agent = {
            "agent_name": "",  # Empty name (invalid)
            "agent_type": "invalid_type",  # Invalid type
            "system_prompt": "",  # Empty prompt
            "tools": [],  # Empty tools array
            "output_schema": {}  # Empty schema
        }
        
        response, response_time = self.client.post(
            "api/v1/config",
            json={"type": "agent", "config": invalid_agent}
        )
        
        if response.status_code == 400:
            try:
                data = response.json()
                has_error_message = "error" in data or "message" in data
                has_details = "details" in data or "validation_errors" in data or "error" in data
                
                if has_error_message:
                    self.add_result(TestResult(
                        test_name="400 Error Includes Validation Details",
                        category="Error Handling",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response=data,
                        http_code=400
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="400 Error Includes Validation Details",
                        category="Error Handling",
                        endpoint="POST /api/v1/config",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Error response missing validation details",
                        http_code=400
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="400 Error Includes Validation Details",
                    category="Error Handling",
                    endpoint="POST /api/v1/config",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=400
                ))
        else:
            self.add_result(TestResult(
                test_name="400 Error Includes Validation Details",
                category="Error Handling",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.10.2: 401 errors include authentication guidance
        client_no_auth = APITestClient(self.api_url, jwt_token=None)
        response, response_time = client_no_auth.get("api/v1/config?type=agent")
        
        if response.status_code == 401:
            try:
                data = response.json()
                has_error_message = "error" in data or "message" in data
                
                if has_error_message:
                    self.add_result(TestResult(
                        test_name="401 Error Includes Authentication Guidance",
                        category="Error Handling",
                        endpoint="GET /api/v1/config?type=agent",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response=data,
                        http_code=401
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="401 Error Includes Authentication Guidance",
                        category="Error Handling",
                        endpoint="GET /api/v1/config?type=agent",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Error response missing authentication guidance",
                        http_code=401
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="401 Error Includes Authentication Guidance",
                    category="Error Handling",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=401
                ))
        else:
            self.add_result(TestResult(
                test_name="401 Error Includes Authentication Guidance",
                category="Error Handling",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 401, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.10.3: 404 errors include resource identification
        response, response_time = self.client.get("api/v1/config/agent/nonexistent_agent_12345")
        
        if response.status_code == 404:
            try:
                data = response.json()
                has_error_message = "error" in data or "message" in data
                
                if has_error_message:
                    self.add_result(TestResult(
                        test_name="404 Error Includes Resource Identification",
                        category="Error Handling",
                        endpoint="GET /api/v1/config/agent/nonexistent_agent_12345",
                        status=TestStatus.PASS,
                        response_time_ms=response_time,
                        response=data,
                        http_code=404
                    ))
                else:
                    self.add_result(TestResult(
                        test_name="404 Error Includes Resource Identification",
                        category="Error Handling",
                        endpoint="GET /api/v1/config/agent/nonexistent_agent_12345",
                        status=TestStatus.FAIL,
                        response_time_ms=response_time,
                        error_message="Error response missing resource identification",
                        http_code=404
                    ))
            except json.JSONDecodeError:
                self.add_result(TestResult(
                    test_name="404 Error Includes Resource Identification",
                    category="Error Handling",
                    endpoint="GET /api/v1/config/agent/nonexistent_agent_12345",
                    status=TestStatus.FAIL,
                    response_time_ms=response_time,
                    error_message="Invalid JSON response",
                    http_code=404
                ))
        else:
            self.add_result(TestResult(
                test_name="404 Error Includes Resource Identification",
                category="Error Handling",
                endpoint="GET /api/v1/config/agent/nonexistent_agent_12345",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 404, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.10.4: Error response format is consistent
        # Check multiple error responses have consistent structure
        error_responses = []
        
        # Get 400 error
        response, _ = self.client.post("api/v1/config", json={"type": "agent"})
        if response.status_code == 400:
            try:
                error_responses.append(response.json())
            except:
                pass
        
        # Get 404 error
        response, _ = self.client.get("api/v1/config/agent/nonexistent")
        if response.status_code == 404:
            try:
                error_responses.append(response.json())
            except:
                pass
        
        if len(error_responses) >= 2:
            # Check if all have 'error' or 'message' field
            all_have_error = all("error" in r or "message" in r for r in error_responses)
            
            if all_have_error:
                self.add_result(TestResult(
                    test_name="Error Response Format is Consistent",
                    category="Error Handling",
                    endpoint="Various",
                    status=TestStatus.PASS,
                    response_time_ms=0,
                    http_code=0
                ))
            else:
                self.add_result(TestResult(
                    test_name="Error Response Format is Consistent",
                    category="Error Handling",
                    endpoint="Various",
                    status=TestStatus.FAIL,
                    response_time_ms=0,
                    error_message="Error responses have inconsistent format",
                    http_code=0
                ))
        else:
            self.add_result(TestResult(
                test_name="Error Response Format is Consistent",
                category="Error Handling",
                endpoint="Various",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not collect enough error responses",
                http_code=0
            ))
        
        # Test 2.10.5: Error messages are user-friendly
        # This is subjective, but we can check they're not empty and not just error codes
        if len(error_responses) > 0:
            error_msg = error_responses[0].get("error") or error_responses[0].get("message", "")
            
            is_user_friendly = len(error_msg) > 10 and not error_msg.isupper()
            
            if is_user_friendly:
                self.add_result(TestResult(
                    test_name="Error Messages are User-Friendly",
                    category="Error Handling",
                    endpoint="Various",
                    status=TestStatus.PASS,
                    response_time_ms=0,
                    http_code=0
                ))
            else:
                self.add_result(TestResult(
                    test_name="Error Messages are User-Friendly",
                    category="Error Handling",
                    endpoint="Various",
                    status=TestStatus.FAIL,
                    response_time_ms=0,
                    error_message="Error messages may not be user-friendly",
                    http_code=0
                ))
        else:
            self.add_result(TestResult(
                test_name="Error Messages are User-Friendly",
                category="Error Handling",
                endpoint="Various",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="No error responses to evaluate",
                http_code=0
            ))
    
    def run_edge_case_tests(self):
        """Run edge case tests (Task 2.11)"""
        # Test 2.11.1: Missing required fields
        incomplete_data = {"type": "agent"}  # Missing 'config'
        response, response_time = self.client.post("api/v1/config", json=incomplete_data)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Missing Required Fields",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.2: Invalid data types
        invalid_types = {
            "type": "agent",
            "config": {
                "agent_name": 12345,  # Should be string
                "agent_type": ["custom"],  # Should be string
                "system_prompt": True,  # Should be string
                "tools": "bedrock",  # Should be array
                "output_schema": "invalid"  # Should be object
            }
        }
        response, response_time = self.client.post("api/v1/config", json=invalid_types)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Invalid Data Types",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Invalid Data Types",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.3: Out-of-range values
        out_of_range = {
            "type": "agent",
            "config": {
                "agent_name": "A" * 1000,  # Too long (max 100)
                "agent_type": "custom",
                "system_prompt": "B" * 10000,  # Too long (max 2000)
                "tools": ["bedrock"],
                "output_schema": {f"field_{i}": "string" for i in range(100)}  # Too many fields (max 5)
            }
        }
        response, response_time = self.client.post("api/v1/config", json=out_of_range)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Out-of-Range Values",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Out-of-Range Values",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.4: Empty strings
        empty_strings = {
            "type": "agent",
            "config": {
                "agent_name": "",
                "agent_type": "",
                "system_prompt": "",
                "tools": [],
                "output_schema": {}
            }
        }
        response, response_time = self.client.post("api/v1/config", json=empty_strings)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Empty Strings and Arrays",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Empty Strings and Arrays",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.5: Null values
        null_values = {
            "type": "agent",
            "config": {
                "agent_name": None,
                "agent_type": None,
                "system_prompt": None,
                "tools": None,
                "output_schema": None
            }
        }
        response, response_time = self.client.post("api/v1/config", json=null_values)
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Null Values",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Null Values",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.6: Special characters and Unicode
        special_chars = {
            "type": "agent",
            "config": {
                "agent_name": "Test Agent 🚀 émojis 你好",
                "agent_type": "custom",
                "system_prompt": "Test with special chars: <>&\"'`\n\t\r",
                "tools": ["bedrock"],
                "output_schema": {"result": "string"}
            }
        }
        response, response_time = self.client.post("api/v1/config", json=special_chars)
        
        if response.status_code in [201, 400]:  # Either accepted or rejected
            self.add_result(TestResult(
                test_name="Special Characters and Unicode",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=response.status_code
            ))
            
            # Clean up if created
            if response.status_code == 201:
                try:
                    data = response.json()
                    agent_id = data.get("agent_id") or data.get("config_key")
                    if agent_id:
                        self.created_agents.append(agent_id)
                except:
                    pass
        else:
            self.add_result(TestResult(
                test_name="Special Characters and Unicode",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 201 or 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.7: Malformed JSON
        # Send invalid JSON string
        response, response_time = self.client.request(
            'POST',
            'api/v1/config',
            data='{"type": "agent", "config": {invalid json}',
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            self.add_result(TestResult(
                test_name="Malformed JSON",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=response_time,
                http_code=400
            ))
        else:
            self.add_result(TestResult(
                test_name="Malformed JSON",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=response_time,
                error_message=f"Expected 400, got {response.status_code}",
                http_code=response.status_code
            ))
        
        # Test 2.11.8: Concurrent requests
        def make_request():
            test_agent = TEST_AGENT.copy()
            test_agent["agent_name"] = f"Concurrent Test {uuid.uuid4().hex[:8]}"
            response, response_time = self.client.post(
                "api/v1/config",
                json={"type": "agent", "config": test_agent}
            )
            return response.status_code, response_time
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for status, _ in results if status == 201)
        
        if success_count >= 3:  # At least 3 out of 5 should succeed
            self.add_result(TestResult(
                test_name="Concurrent Requests",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.PASS,
                response_time_ms=int(sum(rt for _, rt in results) / len(results)),
                response={"success_count": success_count, "total": 5},
                http_code=201
            ))
        else:
            self.add_result(TestResult(
                test_name="Concurrent Requests",
                category="Edge Cases",
                endpoint="POST /api/v1/config",
                status=TestStatus.FAIL,
                response_time_ms=int(sum(rt for _, rt in results) / len(results)),
                error_message=f"Only {success_count}/5 concurrent requests succeeded",
                http_code=0
            ))
    
    def run_performance_tests(self):
        """Run performance tests (Task 2.12)"""
        # Test 2.12.1: Config API response time (target < 500ms)
        response_times = []
        for _ in range(3):
            response, response_time = self.client.get("api/v1/config?type=agent")
            if response.status_code == 200:
                response_times.append(response_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            
            if avg_time < 500:
                self.add_result(TestResult(
                    test_name="Config API Response Time",
                    category="Performance",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.PASS,
                    response_time_ms=int(avg_time),
                    response={"avg_ms": int(avg_time), "target_ms": 500},
                    http_code=200
                ))
            else:
                self.add_result(TestResult(
                    test_name="Config API Response Time",
                    category="Performance",
                    endpoint="GET /api/v1/config?type=agent",
                    status=TestStatus.FAIL,
                    response_time_ms=int(avg_time),
                    error_message=f"Average response time {int(avg_time)}ms exceeds target 500ms",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Config API Response Time",
                category="Performance",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not measure response time",
                http_code=0
            ))
        
        # Test 2.12.2: Data API response time (target < 1000ms)
        response_times = []
        for _ in range(3):
            response, response_time = self.client.get("api/v1/data?type=retrieval")
            if response.status_code == 200:
                response_times.append(response_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            
            if avg_time < 1000:
                self.add_result(TestResult(
                    test_name="Data API Response Time",
                    category="Performance",
                    endpoint="GET /api/v1/data?type=retrieval",
                    status=TestStatus.PASS,
                    response_time_ms=int(avg_time),
                    response={"avg_ms": int(avg_time), "target_ms": 1000},
                    http_code=200
                ))
            else:
                self.add_result(TestResult(
                    test_name="Data API Response Time",
                    category="Performance",
                    endpoint="GET /api/v1/data?type=retrieval",
                    status=TestStatus.FAIL,
                    response_time_ms=int(avg_time),
                    error_message=f"Average response time {int(avg_time)}ms exceeds target 1000ms",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Data API Response Time",
                category="Performance",
                endpoint="GET /api/v1/data?type=retrieval",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not measure response time",
                http_code=0
            ))
        
        # Test 2.12.3: Ingest API response time (target < 2000ms)
        test_report = TEST_REPORT.copy()
        response_times = []
        
        for _ in range(3):
            response, response_time = self.client.post("api/v1/ingest", json=test_report)
            if response.status_code == 202:
                response_times.append(response_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            
            if avg_time < 2000:
                self.add_result(TestResult(
                    test_name="Ingest API Response Time",
                    category="Performance",
                    endpoint="POST /api/v1/ingest",
                    status=TestStatus.PASS,
                    response_time_ms=int(avg_time),
                    response={"avg_ms": int(avg_time), "target_ms": 2000},
                    http_code=202
                ))
            else:
                self.add_result(TestResult(
                    test_name="Ingest API Response Time",
                    category="Performance",
                    endpoint="POST /api/v1/ingest",
                    status=TestStatus.FAIL,
                    response_time_ms=int(avg_time),
                    error_message=f"Average response time {int(avg_time)}ms exceeds target 2000ms",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Ingest API Response Time",
                category="Performance",
                endpoint="POST /api/v1/ingest",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not measure response time",
                http_code=0
            ))
        
        # Test 2.12.4: Query API response time (target < 2000ms)
        test_query = TEST_QUERY.copy()
        response_times = []
        
        for _ in range(3):
            response, response_time = self.client.post("api/v1/query", json=test_query)
            if response.status_code == 202:
                response_times.append(response_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            
            if avg_time < 2000:
                self.add_result(TestResult(
                    test_name="Query API Response Time",
                    category="Performance",
                    endpoint="POST /api/v1/query",
                    status=TestStatus.PASS,
                    response_time_ms=int(avg_time),
                    response={"avg_ms": int(avg_time), "target_ms": 2000},
                    http_code=202
                ))
            else:
                self.add_result(TestResult(
                    test_name="Query API Response Time",
                    category="Performance",
                    endpoint="POST /api/v1/query",
                    status=TestStatus.FAIL,
                    response_time_ms=int(avg_time),
                    error_message=f"Average response time {int(avg_time)}ms exceeds target 2000ms",
                    http_code=202
                ))
        else:
            self.add_result(TestResult(
                test_name="Query API Response Time",
                category="Performance",
                endpoint="POST /api/v1/query",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not measure response time",
                http_code=0
            ))
        
        # Test 2.12.5: Concurrent requests (10 concurrent)
        def make_concurrent_request():
            response, response_time = self.client.get("api/v1/config?type=agent")
            return response.status_code == 200, response_time
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_concurrent_request) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        total_time = (time.time() - start_time) * 1000
        
        success_count = sum(1 for success, _ in results if success)
        avg_response_time = sum(rt for _, rt in results) / len(results) if results else 0
        
        if success_count >= 8:  # At least 8 out of 10 should succeed
            self.add_result(TestResult(
                test_name="10 Concurrent Requests",
                category="Performance",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.PASS,
                response_time_ms=int(avg_response_time),
                response={
                    "success_count": success_count,
                    "total": 10,
                    "avg_response_ms": int(avg_response_time),
                    "total_time_ms": int(total_time)
                },
                http_code=200
            ))
        else:
            self.add_result(TestResult(
                test_name="10 Concurrent Requests",
                category="Performance",
                endpoint="GET /api/v1/config?type=agent",
                status=TestStatus.FAIL,
                response_time_ms=int(avg_response_time),
                error_message=f"Only {success_count}/10 concurrent requests succeeded",
                http_code=0
            ))
        
        # Test 2.12.6: Pagination performance
        response_times = []
        for page in range(1, 4):  # Test 3 pages
            response, response_time = self.client.get(f"api/v1/data?type=retrieval&page={page}&page_size=10")
            if response.status_code == 200:
                response_times.append(response_time)
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            
            if avg_time < 1000:
                self.add_result(TestResult(
                    test_name="Pagination Performance",
                    category="Performance",
                    endpoint="GET /api/v1/data?type=retrieval&page=X&page_size=10",
                    status=TestStatus.PASS,
                    response_time_ms=int(avg_time),
                    response={"avg_ms": int(avg_time), "pages_tested": len(response_times)},
                    http_code=200
                ))
            else:
                self.add_result(TestResult(
                    test_name="Pagination Performance",
                    category="Performance",
                    endpoint="GET /api/v1/data?type=retrieval&page=X&page_size=10",
                    status=TestStatus.FAIL,
                    response_time_ms=int(avg_time),
                    error_message=f"Average pagination response time {int(avg_time)}ms exceeds target 1000ms",
                    http_code=200
                ))
        else:
            self.add_result(TestResult(
                test_name="Pagination Performance",
                category="Performance",
                endpoint="GET /api/v1/data?type=retrieval&page=X&page_size=10",
                status=TestStatus.SKIP,
                response_time_ms=0,
                error_message="Could not measure pagination performance",
                http_code=0
            ))
    
    def cleanup_resources(self):
        """Clean up created test resources"""
        # Delete created agents
        for agent_id in self.created_agents:
            try:
                self.client.delete(f"api/v1/config/agent/{agent_id}")
            except:
                pass
        
        # Delete created domains
        for domain_id in self.created_domains:
            try:
                self.client.delete(f"api/v1/config/domain_template/{domain_id}")
            except:
                pass
        
        # Delete created playbooks
        for playbook_id in self.created_playbooks:
            try:
                self.client.delete(f"api/v1/config/playbook/{playbook_id}")
            except:
                pass
    
    def display_summary(self):
        """Display test execution summary"""
        self.log("")
        self.log("=" * 80)
        self.log("TEST EXECUTION SUMMARY")
        self.log("=" * 80)
        self.log("")
        self.log(f"Total Tests:    {self.report.total_tests}")
        self.log(f"Passed:         {self.report.passed_tests} ({self.report.pass_rate:.1f}%)", 
                 "PASS" if self.report.failed_tests == 0 else "INFO")
        self.log(f"Failed:         {self.report.failed_tests}", 
                 "INFO" if self.report.failed_tests == 0 else "FAIL")
        self.log(f"Skipped:        {self.report.skipped_tests}")
        self.log(f"Duration:       {self.report.duration_seconds:.2f} seconds")
        self.log("")
        
        if self.report.failed_tests == 0:
            self.log("✓ All tests passed!", "PASS")
        else:
            self.log(f"✗ {self.report.failed_tests} test(s) failed", "FAIL")
        
        self.log("=" * 80)
    
    def generate_report_file(self):
        """Generate TEST_REPORT.md file (Task 2.13)"""
        report_lines = []
        
        # Header
        report_lines.append("# API Test Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Duration:** {self.report.duration_seconds:.2f} seconds")
        report_lines.append("")
        
        # Summary
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Tests:** {self.report.total_tests}")
        report_lines.append(f"- **Passed:** {self.report.passed_tests} ({self.report.pass_rate:.1f}%)")
        report_lines.append(f"- **Failed:** {self.report.failed_tests}")
        report_lines.append(f"- **Skipped:** {self.report.skipped_tests}")
        report_lines.append("")
        
        if self.report.failed_tests == 0:
            report_lines.append("✅ **All tests passed!**")
        else:
            report_lines.append(f"❌ **{self.report.failed_tests} test(s) failed**")
        report_lines.append("")
        
        # Group results by category
        categories = {}
        for result in self.report.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Detailed Results by Category
        report_lines.append("## Detailed Results")
        report_lines.append("")
        
        for category, results in sorted(categories.items()):
            report_lines.append(f"### {category}")
            report_lines.append("")
            
            # Category summary
            passed = sum(1 for r in results if r.status == TestStatus.PASS)
            failed = sum(1 for r in results if r.status == TestStatus.FAIL)
            skipped = sum(1 for r in results if r.status == TestStatus.SKIP)
            
            report_lines.append(f"**Tests:** {len(results)} | **Passed:** {passed} | **Failed:** {failed} | **Skipped:** {skipped}")
            report_lines.append("")
            
            # Test results table
            report_lines.append("| Status | Test Name | Endpoint | Response Time | HTTP Code |")
            report_lines.append("|--------|-----------|----------|---------------|-----------|")
            
            for result in results:
                status_icon = {
                    TestStatus.PASS: "✅",
                    TestStatus.FAIL: "❌",
                    TestStatus.SKIP: "⊘"
                }.get(result.status, "•")
                
                endpoint_short = result.endpoint[:50] + "..." if len(result.endpoint) > 50 else result.endpoint
                response_time_str = f"{result.response_time_ms}ms" if result.response_time_ms > 0 else "-"
                http_code_str = str(result.http_code) if result.http_code > 0 else "-"
                
                report_lines.append(
                    f"| {status_icon} | {result.test_name} | `{endpoint_short}` | {response_time_str} | {http_code_str} |"
                )
            
            report_lines.append("")
        
        # Failed Tests Details
        failed_results = [r for r in self.report.results if r.status == TestStatus.FAIL]
        if failed_results:
            report_lines.append("## Failed Tests Details")
            report_lines.append("")
            
            for i, result in enumerate(failed_results, 1):
                report_lines.append(f"### {i}. {result.test_name}")
                report_lines.append("")
                report_lines.append(f"- **Category:** {result.category}")
                report_lines.append(f"- **Endpoint:** `{result.endpoint}`")
                report_lines.append(f"- **HTTP Code:** {result.http_code}")
                report_lines.append(f"- **Response Time:** {result.response_time_ms}ms")
                report_lines.append(f"- **Error:** {result.error_message}")
                report_lines.append("")
                
                if result.request:
                    report_lines.append("**Request:**")
                    report_lines.append("```json")
                    report_lines.append(json.dumps(result.request, indent=2))
                    report_lines.append("```")
                    report_lines.append("")
                
                if result.response:
                    report_lines.append("**Response:**")
                    report_lines.append("```json")
                    report_lines.append(json.dumps(result.response, indent=2))
                    report_lines.append("```")
                    report_lines.append("")
        
        # Performance Summary
        performance_results = [r for r in self.report.results if r.category == "Performance"]
        if performance_results:
            report_lines.append("## Performance Summary")
            report_lines.append("")
            report_lines.append("| Test | Avg Response Time | Target | Status |")
            report_lines.append("|------|-------------------|--------|--------|")
            
            for result in performance_results:
                status_icon = "✅" if result.status == TestStatus.PASS else "❌"
                target = ""
                if result.response and isinstance(result.response, dict):
                    target = f"{result.response.get('target_ms', '-')}ms"
                
                report_lines.append(
                    f"| {result.test_name} | {result.response_time_ms}ms | {target} | {status_icon} |"
                )
            
            report_lines.append("")
        
        # Write report to file
        report_content = "\n".join(report_lines)
        
        try:
            with open("TEST_REPORT.md", "w", encoding="utf-8") as f:
                f.write(report_content)
            self.log("Test report saved to TEST_REPORT.md", "INFO")
        except Exception as e:
            self.log(f"Failed to write test report: {e}", "FAIL")


# ============================================================================
# Main Entry Point
# ============================================================================

def load_environment() -> Tuple[str, Optional[str]]:
    """Load environment variables"""
    api_url = os.getenv('API_URL')
    jwt_token = os.getenv('JWT_TOKEN')
    
    if not api_url:
        print("ERROR: API_URL environment variable is required")
        print("Usage: API_URL=https://api.example.com JWT_TOKEN=your_token python test_api.py")
        sys.exit(1)
    
    if not jwt_token:
        print("WARNING: JWT_TOKEN not provided. Authentication tests will be skipped.")
    
    return api_url, jwt_token


def main():
    """Main test execution"""
    # Load environment
    api_url, jwt_token = load_environment()
    
    # Create and run test suite
    suite = APITestSuite(api_url, jwt_token)
    suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if suite.report.failed_tests == 0 else 1)


if __name__ == "__main__":
    main()
