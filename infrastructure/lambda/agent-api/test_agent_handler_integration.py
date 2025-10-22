"""
Integration tests for Agent Handler Lambda with actual database
Tests CRUD operations against a real PostgreSQL database
"""

import pytest
import json
import os
import sys
import boto3
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
import uuid
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables before importing handler
os.environ['DB_SECRET_ARN'] = os.environ.get('DB_SECRET_ARN', 'test-secret')
os.environ['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
os.environ['DB_PORT'] = os.environ.get('DB_PORT', '5432')
os.environ['DB_NAME'] = os.environ.get('DB_NAME', 'domainflow')

import agent_handler


@pytest.fixture(scope="session")
def db_connection():
    """Create a database connection for testing"""
    try:
        # Try to get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        
        try:
            secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
            secret = json.loads(secret_response['SecretString'])
            db_username = secret['username']
            db_password = secret['password']
        except:
            # Fallback to environment variables for local testing
            db_username = os.environ.get('DB_USER', 'postgres')
            db_password = os.environ.get('DB_PASSWORD', 'postgres')
        
        # Connect to database
        conn = psycopg.connect(
            host=os.environ.get('DB_HOST'),
            port=int(os.environ.get('DB_PORT', 5432)),
            dbname=os.environ.get('DB_NAME'),
            user=db_username,
            password=db_password,
            row_factory=dict_row,
            autocommit=False
        )
        
        print(f"✓ Database connection established")
        yield conn
        
        conn.close()
        print(f"✓ Database connection closed")
        
    except Exception as e:
        pytest.skip(f"Database not available: {str(e)}")


@pytest.fixture(scope="session")
def test_tenant_and_user(db_connection):
    """Create a test tenant and user"""
    cursor = db_connection.cursor()
    
    try:
        # Create test tenant
        cursor.execute("""
            INSERT INTO tenants (id, tenant_name)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (str(uuid.uuid4()), 'Test Tenant'))
        
        result = cursor.fetchone()
        if result:
            tenant_id = str(result['id'])
        else:
            # Tenant already exists, get it
            cursor.execute("SELECT id FROM tenants WHERE tenant_name = %s", ('Test Tenant',))
            tenant_id = str(cursor.fetchone()['id'])
        
        # Create test user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, username, email, cognito_sub, tenant_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cognito_sub) DO NOTHING
            RETURNING id;
        """, (user_id, 'testuser', 'test@example.com', 'test-cognito-sub', tenant_id))
        
        result = cursor.fetchone()
        if result:
            user_id = str(result['id'])
        else:
            # User already exists, get it
            cursor.execute("SELECT id FROM users WHERE cognito_sub = %s", ('test-cognito-sub',))
            user_id = str(cursor.fetchone()['id'])
        
        db_connection.commit()
        
        print(f"✓ Test tenant and user created: tenant_id={tenant_id}, user_id={user_id}")
        
        yield tenant_id, user_id
        
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"Failed to create test tenant and user: {str(e)}")


@pytest.fixture
def clean_agents(db_connection, test_tenant_and_user):
    """Clean up test agents before and after each test"""
    tenant_id, user_id = test_tenant_and_user
    cursor = db_connection.cursor()
    
    # Clean before test
    cursor.execute("""
        DELETE FROM agent_definitions 
        WHERE tenant_id = %s AND is_inbuilt = false;
    """, (tenant_id,))
    db_connection.commit()
    
    yield
    
    # Clean after test
    cursor.execute("""
        DELETE FROM agent_definitions 
        WHERE tenant_id = %s AND is_inbuilt = false;
    """, (tenant_id,))
    db_connection.commit()


@pytest.fixture
def mock_secrets_manager():
    """Mock Secrets Manager for testing"""
    with patch('agent_handler.secrets_client') as mock_client:
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'username': os.environ.get('DB_USER', 'postgres'),
                'password': os.environ.get('DB_PASSWORD', 'postgres')
            })
        }
        yield mock_client


class TestCreateAgent:
    """Integration tests for create_agent"""
    
    def test_create_agent_success(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test successful agent creation"""
        tenant_id, user_id = test_tenant_and_user
        
        agent_data = {
            "agent_name": "Test Ingestion Agent",
            "agent_class": "ingestion",
            "system_prompt": "You are a test ingestion agent",
            "tools": ["bedrock", "comprehend"],
            "agent_dependencies": [],
            "output_schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "location": {"type": "string"}
                }
            },
            "description": "A test agent for ingestion",
            "enabled": True
        }
        
        # Patch get_db_connection to use our test connection
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert "agent_id" in body
        assert body["agent_name"] == "Test Ingestion Agent"
        assert body["agent_class"] == "ingestion"
        assert body["version"] == 1
        
        # Verify in database
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT * FROM agent_definitions 
            WHERE agent_id = %s AND tenant_id = %s;
        """, (body["agent_id"], tenant_id))
        
        db_agent = cursor.fetchone()
        assert db_agent is not None
        assert db_agent["agent_name"] == "Test Ingestion Agent"
        
        print(f"✓ Agent created successfully: {body['agent_id']}")
    
    def test_create_agent_with_dependencies(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test agent creation with dependencies"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create first agent
        agent1_data = {
            "agent_name": "Base Agent",
            "agent_class": "ingestion",
            "system_prompt": "Base agent",
            "tools": [],
            "agent_dependencies": [],
            "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result1 = agent_handler.create_agent(tenant_id, user_id, agent1_data)
        
        agent1_id = json.loads(result1["body"])["agent_id"]
        
        # Create second agent that depends on first
        agent2_data = {
            "agent_name": "Dependent Agent",
            "agent_class": "ingestion",
            "system_prompt": "Dependent agent",
            "tools": [],
            "agent_dependencies": [agent1_id],
            "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result2 = agent_handler.create_agent(tenant_id, user_id, agent2_data)
        
        assert result2["statusCode"] == 201
        body = json.loads(result2["body"])
        assert body["agent_name"] == "Dependent Agent"
        
        print(f"✓ Agent with dependencies created successfully")
    
    def test_create_agent_circular_dependency(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test that circular dependencies are detected"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create agent A
        agent_a_data = {
            "agent_name": "Agent A",
            "agent_class": "ingestion",
            "system_prompt": "Agent A",
            "tools": [],
            "agent_dependencies": [],
            "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result_a = agent_handler.create_agent(tenant_id, user_id, agent_a_data)
        
        agent_a_id = json.loads(result_a["body"])["agent_id"]
        
        # Create agent B that depends on A
        agent_b_data = {
            "agent_name": "Agent B",
            "agent_class": "ingestion",
            "system_prompt": "Agent B",
            "tools": [],
            "agent_dependencies": [agent_a_id],
            "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result_b = agent_handler.create_agent(tenant_id, user_id, agent_b_data)
        
        agent_b_id = json.loads(result_b["body"])["agent_id"]
        
        # Try to update agent A to depend on B (creating a cycle)
        update_data = {
            "agent_dependencies": [agent_b_id]
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.update_agent(tenant_id, user_id, agent_a_id, update_data)
        
        assert result["statusCode"] == 409
        body = json.loads(result["body"])
        assert "Circular dependency" in body["error"]
        
        print(f"✓ Circular dependency correctly detected")


class TestListAgents:
    """Integration tests for list_agents"""
    
    def test_list_agents_empty(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test listing agents when none exist"""
        tenant_id, user_id = test_tenant_and_user
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.list_agents(tenant_id, user_id, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "agents" in body
        assert len(body["agents"]) == 0
        assert body["pagination"]["total"] == 0
        
        print(f"✓ Empty agent list returned correctly")
    
    def test_list_agents_with_data(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test listing agents with data"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create multiple agents
        for i in range(3):
            agent_data = {
                "agent_name": f"Test Agent {i}",
                "agent_class": "ingestion" if i < 2 else "query",
                "system_prompt": f"Agent {i}",
                "tools": [],
                "agent_dependencies": [],
                "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
            }
            
            with patch('agent_handler.get_db_connection', return_value=db_connection):
                agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        # List all agents
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.list_agents(tenant_id, user_id, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["agents"]) == 3
        assert body["pagination"]["total"] == 3
        
        print(f"✓ Agent list with data returned correctly")
    
    def test_list_agents_with_class_filter(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test listing agents with class filter"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create agents of different classes
        for agent_class in ["ingestion", "query", "management"]:
            agent_data = {
                "agent_name": f"{agent_class.title()} Agent",
                "agent_class": agent_class,
                "system_prompt": f"{agent_class} agent",
                "tools": [],
                "agent_dependencies": [],
                "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
            }
            
            with patch('agent_handler.get_db_connection', return_value=db_connection):
                agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        # List only ingestion agents
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.list_agents(tenant_id, user_id, {"agent_class": "ingestion"})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["agents"]) == 1
        assert body["agents"][0]["agent_class"] == "ingestion"
        
        print(f"✓ Agent list with class filter returned correctly")


class TestGetAgent:
    """Integration tests for get_agent"""
    
    def test_get_agent_success(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test getting a specific agent"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create an agent
        agent_data = {
            "agent_name": "Test Agent",
            "agent_class": "query",
            "system_prompt": "Test agent",
            "tools": ["bedrock"],
            "agent_dependencies": [],
            "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            create_result = agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        agent_id = json.loads(create_result["body"])["agent_id"]
        
        # Get the agent
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.get_agent(tenant_id, user_id, agent_id)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["agent_id"] == agent_id
        assert body["agent_name"] == "Test Agent"
        assert "dependency_graph" in body
        assert "nodes" in body["dependency_graph"]
        assert "edges" in body["dependency_graph"]
        
        print(f"✓ Agent retrieved successfully with dependency graph")
    
    def test_get_agent_not_found(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test getting a non-existent agent"""
        tenant_id, user_id = test_tenant_and_user
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.get_agent(tenant_id, user_id, "nonexistent-agent")
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["error"]
        
        print(f"✓ Non-existent agent correctly returns 404")


class TestUpdateAgent:
    """Integration tests for update_agent"""
    
    def test_update_agent_success(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test updating an agent"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create an agent
        agent_data = {
            "agent_name": "Original Name",
            "agent_class": "management",
            "system_prompt": "Original prompt",
            "tools": [],
            "agent_dependencies": [],
            "output_schema": {"type": "object", "properties": {"status": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            create_result = agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        agent_id = json.loads(create_result["body"])["agent_id"]
        
        # Update the agent
        update_data = {
            "agent_name": "Updated Name",
            "description": "Updated description"
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.update_agent(tenant_id, user_id, agent_id, update_data)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["agent_name"] == "Updated Name"
        assert body["description"] == "Updated description"
        assert body["version"] == 2  # Version should increment
        
        print(f"✓ Agent updated successfully with version increment")


class TestDeleteAgent:
    """Integration tests for delete_agent"""
    
    def test_delete_agent_success(self, db_connection, test_tenant_and_user, clean_agents, mock_secrets_manager):
        """Test deleting an agent"""
        tenant_id, user_id = test_tenant_and_user
        
        # Create an agent
        agent_data = {
            "agent_name": "Agent to Delete",
            "agent_class": "ingestion",
            "system_prompt": "Delete me",
            "tools": [],
            "agent_dependencies": [],
            "output_schema": {"type": "object", "properties": {"data": {"type": "string"}}}
        }
        
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            create_result = agent_handler.create_agent(tenant_id, user_id, agent_data)
        
        agent_id = json.loads(create_result["body"])["agent_id"]
        
        # Delete the agent
        with patch('agent_handler.get_db_connection', return_value=db_connection):
            result = agent_handler.delete_agent(tenant_id, user_id, agent_id)
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "deleted successfully" in body["message"]
        
        # Verify it's deleted
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT * FROM agent_definitions 
            WHERE agent_id = %s AND tenant_id = %s;
        """, (agent_id, tenant_id))
        
        assert cursor.fetchone() is None
        
        print(f"✓ Agent deleted successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
