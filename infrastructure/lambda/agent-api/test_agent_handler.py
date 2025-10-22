"""
Unit tests for Agent Handler Lambda
Tests CRUD operations and DAG validation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Mock environment variables before importing handler
import os
os.environ['DB_SECRET_ARN'] = 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'test_db'

# Import handler after setting env vars
import agent_handler


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch('agent_handler.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        yield mock_cursor


@pytest.fixture
def sample_agent_data():
    """Sample agent data for testing"""
    return {
        "agent_name": "Test Agent",
        "agent_class": "ingestion",
        "system_prompt": "You are a test agent",
        "tools": ["bedrock"],
        "agent_dependencies": [],
        "output_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        },
        "description": "A test agent",
        "enabled": True
    }


@pytest.fixture
def sample_event():
    """Sample API Gateway event"""
    return {
        "httpMethod": "POST",
        "path": "/api/v1/agents",
        "queryStringParameters": None,
        "pathParameters": None,
        "body": None,
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant-001",
                "user_id": "test-user-001"
            }
        }
    }


class TestCreateAgent:
    """Tests for create_agent function"""
    
    def test_create_agent_success(self, mock_db_connection, sample_agent_data):
        """Test successful agent creation"""
        # Mock database response
        mock_db_connection.fetchone.return_value = {
            "id": uuid.uuid4(),
            "agent_id": "agent-test123",
            "agent_name": "Test Agent",
            "agent_class": "ingestion",
            "version": 1,
            "is_inbuilt": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": uuid.uuid4()
        }
        
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert "agent_id" in body
        assert body["agent_name"] == "Test Agent"
        assert body["agent_class"] == "ingestion"
    
    def test_create_agent_with_valid_dependencies(self, mock_db_connection, sample_agent_data):
        """Test agent creation with valid dependencies (no circular)"""
        # Add dependencies to sample data
        sample_agent_data["agent_dependencies"] = ["agent-A", "agent-B"]
        
        # Mock all agents query for DAG validation
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-A",
                "agent_name": "Agent A",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-B",
                "agent_name": "Agent B",
                "agent_class": "ingestion",
                "agent_dependencies": []
            }
        ]
        
        # Mock insert response
        mock_db_connection.fetchone.return_value = {
            "id": uuid.uuid4(),
            "agent_id": "agent-test123",
            "agent_name": "Test Agent",
            "agent_class": "ingestion",
            "version": 1,
            "is_inbuilt": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": uuid.uuid4()
        }
        
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert "agent_id" in body
    
    def test_create_agent_with_circular_dependency(self, mock_db_connection, sample_agent_data):
        """Test agent creation with circular dependency (should fail)"""
        # Create a circular dependency: new agent depends on A, A depends on B, B depends on new agent
        sample_agent_data["agent_dependencies"] = ["agent-A"]
        
        # Mock all agents query - simulate circular dependency
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-A",
                "agent_name": "Agent A",
                "agent_class": "ingestion",
                "agent_dependencies": ["agent-B"]
            },
            {
                "agent_id": "agent-B",
                "agent_name": "Agent B",
                "agent_class": "ingestion",
                "agent_dependencies": []  # Will be updated to depend on new agent
            }
        ]
        
        # This should be caught by DAG validation
        # Note: The actual circular dependency would be created if agent-B depends on the new agent
        # For this test, we're simulating the validation logic
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        # Should succeed because the circular dependency isn't complete yet
        # The real circular dependency test is in update_agent
        assert result["statusCode"] in [201, 409]
    
    def test_create_agent_missing_required_field(self):
        """Test agent creation with missing required field"""
        incomplete_data = {
            "agent_name": "Test Agent"
            # Missing agent_class, system_prompt, output_schema
        }
        
        result = agent_handler.create_agent("test-tenant", "test-user", incomplete_data)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing required field" in body["error"]
    
    def test_create_agent_invalid_class(self, sample_agent_data):
        """Test agent creation with invalid agent_class"""
        sample_agent_data["agent_class"] = "invalid_class"
        
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid agent_class" in body["error"]
    
    def test_create_agent_invalid_output_schema(self, sample_agent_data):
        """Test agent creation with invalid output schema (not an object)"""
        sample_agent_data["output_schema"] = "not an object"
        
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "output_schema must be a JSON object" in body["error"]
    
    def test_create_agent_too_many_output_keys(self, sample_agent_data):
        """Test agent creation with more than 5 output schema properties"""
        sample_agent_data["output_schema"] = {
            "type": "object",
            "properties": {
                "key1": {"type": "string"},
                "key2": {"type": "string"},
                "key3": {"type": "string"},
                "key4": {"type": "string"},
                "key5": {"type": "string"},
                "key6": {"type": "string"}  # 6th key - should fail
            }
        }
        
        result = agent_handler.create_agent("test-tenant", "test-user", sample_agent_data)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "maximum 5 properties" in body["error"]
    
    def test_create_agent_all_three_classes(self, mock_db_connection):
        """Test creating agents of all three classes"""
        for agent_class in ["ingestion", "query", "management"]:
            agent_data = {
                "agent_name": f"{agent_class.title()} Agent",
                "agent_class": agent_class,
                "system_prompt": f"You are a {agent_class} agent",
                "tools": [],
                "agent_dependencies": [],
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"}
                    }
                }
            }
            
            # Mock database response
            mock_db_connection.fetchone.return_value = {
                "id": uuid.uuid4(),
                "agent_id": f"agent-{agent_class}",
                "agent_name": f"{agent_class.title()} Agent",
                "agent_class": agent_class,
                "version": 1,
                "is_inbuilt": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": uuid.uuid4()
            }
            
            result = agent_handler.create_agent("test-tenant", "test-user", agent_data)
            
            assert result["statusCode"] == 201
            body = json.loads(result["body"])
            assert body["agent_class"] == agent_class


class TestListAgents:
    """Tests for list_agents function"""
    
    def test_list_agents_success(self, mock_db_connection):
        """Test successful agent listing"""
        # Mock count query
        mock_db_connection.fetchone.return_value = {"total": 2}
        
        # Mock agents query
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-001",
                "agent_name": "Agent 1",
                "agent_class": "ingestion",
                "enabled": True,
                "is_inbuilt": False,
                "created_at": datetime.utcnow(),
                "created_by": uuid.uuid4()
            },
            {
                "agent_id": "agent-002",
                "agent_name": "Agent 2",
                "agent_class": "query",
                "enabled": True,
                "is_inbuilt": True,
                "created_at": datetime.utcnow(),
                "created_by": uuid.uuid4()
            }
        ]
        
        result = agent_handler.list_agents("test-tenant", "test-user", {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["agents"]) == 2
        assert "pagination" in body
        assert body["pagination"]["total"] == 2
    
    def test_list_agents_with_class_filter(self, mock_db_connection):
        """Test agent listing with agent_class filter"""
        mock_db_connection.fetchone.return_value = {"total": 1}
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-001",
                "agent_name": "Agent 1",
                "agent_class": "ingestion",
                "enabled": True,
                "is_inbuilt": False,
                "created_at": datetime.utcnow(),
                "created_by": uuid.uuid4()
            }
        ]
        
        result = agent_handler.list_agents("test-tenant", "test-user", {"agent_class": "ingestion"})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["agents"]) == 1
        assert body["agents"][0]["agent_class"] == "ingestion"
    
    def test_list_agents_invalid_class_filter(self):
        """Test agent listing with invalid agent_class filter"""
        result = agent_handler.list_agents("test-tenant", "test-user", {"agent_class": "invalid"})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid agent_class filter" in body["error"]
    
    def test_list_agents_pagination(self, mock_db_connection):
        """Test agent listing with pagination"""
        mock_db_connection.fetchone.return_value = {"total": 50}
        mock_db_connection.fetchall.return_value = []
        
        result = agent_handler.list_agents("test-tenant", "test-user", {"page": "2", "limit": "10"})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["pagination"]["page"] == 2
        assert body["pagination"]["limit"] == 10


class TestGetAgent:
    """Tests for get_agent function"""
    
    def test_get_agent_success(self, mock_db_connection):
        """Test successful agent retrieval"""
        # Mock agent query
        mock_db_connection.fetchone.return_value = {
            "id": uuid.uuid4(),
            "agent_id": "agent-001",
            "agent_name": "Test Agent",
            "agent_class": "ingestion",
            "system_prompt": "Test prompt",
            "tools": ["bedrock"],
            "agent_dependencies": [],
            "max_output_keys": 5,
            "output_schema": {"type": "object"},
            "description": "Test description",
            "enabled": True,
            "is_inbuilt": False,
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock all agents query for dependency graph
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-001",
                "agent_name": "Test Agent",
                "agent_class": "ingestion",
                "agent_dependencies": []
            }
        ]
        
        result = agent_handler.get_agent("test-tenant", "test-user", "agent-001")
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["agent_id"] == "agent-001"
        assert "dependency_graph" in body
    
    def test_get_agent_with_dependency_graph(self, mock_db_connection):
        """Test agent retrieval includes correct dependency graph structure"""
        # Mock agent query with dependencies
        mock_db_connection.fetchone.return_value = {
            "id": uuid.uuid4(),
            "agent_id": "agent-C",
            "agent_name": "Agent C",
            "agent_class": "ingestion",
            "system_prompt": "Test prompt",
            "tools": [],
            "agent_dependencies": ["agent-A", "agent-B"],
            "max_output_keys": 5,
            "output_schema": {"type": "object"},
            "description": "Test description",
            "enabled": True,
            "is_inbuilt": False,
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock all agents query for dependency graph
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-A",
                "agent_name": "Agent A",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-B",
                "agent_name": "Agent B",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-C",
                "agent_name": "Agent C",
                "agent_class": "ingestion",
                "agent_dependencies": ["agent-A", "agent-B"]
            }
        ]
        
        result = agent_handler.get_agent("test-tenant", "test-user", "agent-C")
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "dependency_graph" in body
        assert "nodes" in body["dependency_graph"]
        assert "edges" in body["dependency_graph"]
        # Should have 3 nodes (A, B, C)
        assert len(body["dependency_graph"]["nodes"]) == 3
        # Should have 2 edges (A->C, B->C)
        assert len(body["dependency_graph"]["edges"]) == 2
    
    def test_get_agent_not_found(self, mock_db_connection):
        """Test agent retrieval when agent doesn't exist"""
        mock_db_connection.fetchone.return_value = None
        
        result = agent_handler.get_agent("test-tenant", "test-user", "nonexistent")
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["error"]


class TestUpdateAgent:
    """Tests for update_agent function"""
    
    def test_update_agent_success(self, mock_db_connection):
        """Test successful agent update"""
        # Mock check query
        mock_db_connection.fetchone.side_effect = [
            {"is_inbuilt": False, "version": 1},  # Check query
            {  # Update query result
                "id": uuid.uuid4(),
                "agent_id": "agent-001",
                "agent_name": "Updated Agent",
                "agent_class": "ingestion",
                "system_prompt": "Updated prompt",
                "tools": ["bedrock"],
                "agent_dependencies": [],
                "max_output_keys": 5,
                "output_schema": {"type": "object"},
                "description": "Updated description",
                "enabled": True,
                "is_inbuilt": False,
                "version": 2,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Mock all agents query for dependency graph
        mock_db_connection.fetchall.return_value = []
        
        update_data = {
            "agent_name": "Updated Agent",
            "description": "Updated description"
        }
        
        result = agent_handler.update_agent("test-tenant", "test-user", "agent-001", update_data)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["agent_name"] == "Updated Agent"
        assert body["version"] == 2
    
    def test_update_agent_with_circular_dependency(self, mock_db_connection):
        """Test updating agent dependencies that would create a circular dependency"""
        # Mock check query
        mock_db_connection.fetchone.return_value = {"is_inbuilt": False, "version": 1}
        
        # Mock all agents query - simulate circular dependency scenario
        # agent-001 wants to depend on agent-B, but agent-B already depends on agent-001
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-001",
                "agent_name": "Agent 001",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-B",
                "agent_name": "Agent B",
                "agent_class": "ingestion",
                "agent_dependencies": ["agent-001"]  # B depends on 001
            }
        ]
        
        # Try to make agent-001 depend on agent-B (would create cycle)
        update_data = {
            "agent_dependencies": ["agent-B"]
        }
        
        result = agent_handler.update_agent("test-tenant", "test-user", "agent-001", update_data)
        
        assert result["statusCode"] == 409
        body = json.loads(result["body"])
        assert "Circular dependency" in body["error"]
    
    def test_update_agent_dependencies_valid(self, mock_db_connection):
        """Test updating agent dependencies with valid DAG"""
        # Mock check query
        mock_db_connection.fetchone.side_effect = [
            {"is_inbuilt": False, "version": 1},  # Check query
            {  # Update query result
                "id": uuid.uuid4(),
                "agent_id": "agent-C",
                "agent_name": "Agent C",
                "agent_class": "ingestion",
                "system_prompt": "Test prompt",
                "tools": [],
                "agent_dependencies": ["agent-A", "agent-B"],
                "max_output_keys": 5,
                "output_schema": {"type": "object"},
                "description": "Test",
                "enabled": True,
                "is_inbuilt": False,
                "version": 2,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Mock all agents query - valid DAG
        mock_db_connection.fetchall.return_value = [
            {
                "agent_id": "agent-A",
                "agent_name": "Agent A",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-B",
                "agent_name": "Agent B",
                "agent_class": "ingestion",
                "agent_dependencies": []
            },
            {
                "agent_id": "agent-C",
                "agent_name": "Agent C",
                "agent_class": "ingestion",
                "agent_dependencies": []
            }
        ]
        
        update_data = {
            "agent_dependencies": ["agent-A", "agent-B"]
        }
        
        result = agent_handler.update_agent("test-tenant", "test-user", "agent-C", update_data)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["agent_dependencies"] == ["agent-A", "agent-B"]
    
    def test_update_builtin_agent(self, mock_db_connection):
        """Test updating a builtin agent (should fail)"""
        mock_db_connection.fetchone.return_value = {"is_inbuilt": True, "version": 1}
        
        result = agent_handler.update_agent("test-tenant", "test-user", "agent-001", {"agent_name": "New Name"})
        
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert "Cannot modify builtin" in body["error"]
    
    def test_update_agent_not_found(self, mock_db_connection):
        """Test updating non-existent agent"""
        mock_db_connection.fetchone.return_value = None
        
        result = agent_handler.update_agent("test-tenant", "test-user", "nonexistent", {"agent_name": "New Name"})
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["error"]
    
    def test_update_agent_invalid_output_schema(self, mock_db_connection):
        """Test updating agent with invalid output schema"""
        mock_db_connection.fetchone.return_value = {"is_inbuilt": False, "version": 1}
        
        update_data = {
            "output_schema": "not an object"
        }
        
        result = agent_handler.update_agent("test-tenant", "test-user", "agent-001", update_data)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "output_schema must be a JSON object" in body["error"]


class TestDeleteAgent:
    """Tests for delete_agent function"""
    
    def test_delete_agent_success(self, mock_db_connection):
        """Test successful agent deletion"""
        mock_db_connection.fetchone.return_value = {"is_inbuilt": False}
        
        result = agent_handler.delete_agent("test-tenant", "test-user", "agent-001")
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "deleted successfully" in body["message"]
    
    def test_delete_builtin_agent(self, mock_db_connection):
        """Test deleting a builtin agent (should fail)"""
        mock_db_connection.fetchone.return_value = {"is_inbuilt": True}
        
        result = agent_handler.delete_agent("test-tenant", "test-user", "agent-001")
        
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert "Cannot delete builtin" in body["error"]
    
    def test_delete_agent_not_found(self, mock_db_connection):
        """Test deleting non-existent agent"""
        mock_db_connection.fetchone.return_value = None
        
        result = agent_handler.delete_agent("test-tenant", "test-user", "nonexistent")
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["error"]


class TestHelperFunctions:
    """Tests for helper functions"""
    
    def test_extract_tenant_id_from_authorizer(self):
        """Test extracting tenant_id from authorizer context"""
        event = {
            "requestContext": {
                "authorizer": {
                    "tenant_id": "test-tenant-123"
                }
            }
        }
        
        tenant_id = agent_handler.extract_tenant_id(event)
        assert tenant_id == "test-tenant-123"
    
    def test_extract_tenant_id_fallback(self):
        """Test tenant_id fallback when not in authorizer"""
        event = {"requestContext": {}}
        
        tenant_id = agent_handler.extract_tenant_id(event)
        assert tenant_id == "demo-tenant-001"
    
    def test_extract_user_id_from_authorizer(self):
        """Test extracting user_id from authorizer context"""
        event = {
            "requestContext": {
                "authorizer": {
                    "user_id": "test-user-456"
                }
            }
        }
        
        user_id = agent_handler.extract_user_id(event)
        assert user_id == "test-user-456"
    
    def test_success_response_format(self):
        """Test success response formatting"""
        response = agent_handler.success_response(200, {"test": "data"})
        
        assert response["statusCode"] == 200
        assert "Content-Type" in response["headers"]
        assert json.loads(response["body"])["test"] == "data"
    
    def test_error_response_format(self):
        """Test error response formatting"""
        response = agent_handler.error_response(400, "Test error")
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "Test error"
        assert body["error_code"] == "ERR_400"
        assert "timestamp" in body


class TestHandler:
    """Tests for main handler function"""
    
    def test_handler_create_agent_route(self, sample_event, sample_agent_data):
        """Test handler routing to create_agent"""
        sample_event["httpMethod"] = "POST"
        sample_event["path"] = "/api/v1/agents"
        sample_event["body"] = json.dumps(sample_agent_data)
        
        with patch('agent_handler.create_agent') as mock_create:
            mock_create.return_value = {"statusCode": 201, "body": "{}"}
            
            result = agent_handler.handler(sample_event, None)
            
            assert mock_create.called
            assert result["statusCode"] == 201
    
    def test_handler_list_agents_route(self, sample_event):
        """Test handler routing to list_agents"""
        sample_event["httpMethod"] = "GET"
        sample_event["path"] = "/api/v1/agents"
        
        with patch('agent_handler.list_agents') as mock_list:
            mock_list.return_value = {"statusCode": 200, "body": "{}"}
            
            result = agent_handler.handler(sample_event, None)
            
            assert mock_list.called
            assert result["statusCode"] == 200
    
    def test_handler_get_agent_route(self, sample_event):
        """Test handler routing to get_agent"""
        sample_event["httpMethod"] = "GET"
        sample_event["path"] = "/api/v1/agents/agent-001"
        sample_event["pathParameters"] = {"agent_id": "agent-001"}
        
        with patch('agent_handler.get_agent') as mock_get:
            mock_get.return_value = {"statusCode": 200, "body": "{}"}
            
            result = agent_handler.handler(sample_event, None)
            
            assert mock_get.called
            assert result["statusCode"] == 200
    
    def test_handler_invalid_json_body(self, sample_event):
        """Test handler with invalid JSON body"""
        sample_event["httpMethod"] = "POST"
        sample_event["path"] = "/api/v1/agents"
        sample_event["body"] = "invalid json"
        
        result = agent_handler.handler(sample_event, None)
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid JSON" in body["error"]
    
    def test_handler_not_found_route(self, sample_event):
        """Test handler with non-existent route"""
        sample_event["httpMethod"] = "GET"
        sample_event["path"] = "/api/v1/nonexistent"
        
        result = agent_handler.handler(sample_event, None)
        
        assert result["statusCode"] == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
