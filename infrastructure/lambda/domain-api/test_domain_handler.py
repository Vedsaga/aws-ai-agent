"""
Unit tests for Domain Handler Lambda
Tests CRUD operations for domain management
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from domain_handler import (
    handler,
    create_domain,
    list_domains,
    get_domain,
    update_domain,
    delete_domain,
    extract_tenant_id,
    extract_user_id
)


# Mock database connection
@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor"""
    with patch('domain_handler.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        yield mock_cursor, mock_connection


# Test helper functions

def test_extract_tenant_id_from_authorizer():
    """Test extracting tenant_id from authorizer context"""
    event = {
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant-123"
            }
        }
    }
    assert extract_tenant_id(event) == "test-tenant-123"


def test_extract_tenant_id_from_claims():
    """Test extracting tenant_id from JWT claims"""
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "custom:tenant_id": "test-tenant-456"
                }
            }
        }
    }
    assert extract_tenant_id(event) == "test-tenant-456"


def test_extract_tenant_id_fallback():
    """Test fallback to default tenant_id"""
    event = {"requestContext": {}}
    assert extract_tenant_id(event) == "demo-tenant-001"


def test_extract_user_id_from_authorizer():
    """Test extracting user_id from authorizer context"""
    event = {
        "requestContext": {
            "authorizer": {
                "user_id": "test-user-123"
            }
        }
    }
    assert extract_user_id(event) == "test-user-123"


def test_extract_user_id_from_claims():
    """Test extracting user_id from JWT claims (sub)"""
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user-456"
                }
            }
        }
    }
    assert extract_user_id(event) == "test-user-456"


def test_extract_user_id_fallback():
    """Test fallback to default user_id"""
    event = {"requestContext": {}}
    assert extract_user_id(event) == "demo-user-001"


# Test handler routing

def test_handler_routes_create_domain(mock_db_connection):
    """Test handler routes POST /domains to create_domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock agents query (called first) - need agents for each class
    mock_cursor.fetchall.return_value = [
        {
            "agent_id": "agent-ing-1",
            "agent_name": "Ingestion Agent",
            "agent_class": "ingestion",
            "agent_dependencies": []
        },
        {
            "agent_id": "agent-qry-1",
            "agent_name": "Query Agent",
            "agent_class": "query",
            "agent_dependencies": []
        },
        {
            "agent_id": "agent-mgmt-1",
            "agent_name": "Management Agent",
            "agent_class": "management",
            "agent_dependencies": []
        }
    ]
    
    # Mock successful domain creation
    mock_cursor.fetchone.return_value = {
        "id": "uuid-123",
        "domain_id": "test-domain",
        "domain_name": "Test Domain",
        "created_at": datetime(2025, 10, 21, 10, 0, 0),
        "updated_at": datetime(2025, 10, 21, 10, 0, 0),
        "created_by": "user-123"
    }
    
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/domains",
        "body": json.dumps({
            "domain_id": "test-domain",
            "domain_name": "Test Domain",
            "ingestion_playbook": {
                "agent_execution_graph": {
                    "nodes": ["agent-ing-1"],
                    "edges": []
                }
            },
            "query_playbook": {
                "agent_execution_graph": {
                    "nodes": ["agent-qry-1"],
                    "edges": []
                }
            },
            "management_playbook": {
                "agent_execution_graph": {
                    "nodes": ["agent-mgmt-1"],
                    "edges": []
                }
            }
        }),
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 201


def test_handler_routes_list_domains(mock_db_connection):
    """Test handler routes GET /domains to list_domains"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock count query
    mock_cursor.fetchone.return_value = {"total": 2}
    
    # Mock list query
    mock_cursor.fetchall.return_value = [
        {
            "domain_id": "domain-1",
            "domain_name": "Domain 1",
            "description": "Test domain 1",
            "id": "uuid-1",
            "created_at": datetime(2025, 10, 21, 10, 0, 0)
        },
        {
            "domain_id": "domain-2",
            "domain_name": "Domain 2",
            "description": "Test domain 2",
            "id": "uuid-2",
            "created_at": datetime(2025, 10, 21, 11, 0, 0)
        }
    ]
    
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/domains",
        "queryStringParameters": {},
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert len(body["domains"]) == 2
    assert body["pagination"]["total"] == 2


def test_handler_routes_get_domain(mock_db_connection):
    """Test handler routes GET /domains/{domain_id} to get_domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock domain query
    mock_cursor.fetchone.return_value = {
        "id": "uuid-123",
        "domain_id": "test-domain",
        "domain_name": "Test Domain",
        "description": "Test description",
        "ingestion_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}},
        "query_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}},
        "management_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}},
        "created_at": datetime(2025, 10, 21, 10, 0, 0),
        "updated_at": datetime(2025, 10, 21, 10, 0, 0),
        "created_by": "user-123"
    }
    
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/domains/test-domain",
        "pathParameters": {"domain_id": "test-domain"},
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["domain_id"] == "test-domain"


def test_handler_routes_update_domain(mock_db_connection):
    """Test handler routes PUT /domains/{domain_id} to update_domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock agents query (called first)
    mock_cursor.fetchall.return_value = [
        {
            "agent_id": "agent-ing-1",
            "agent_name": "Ingestion Agent",
            "agent_class": "ingestion",
            "agent_dependencies": []
        },
        {
            "agent_id": "agent-qry-1",
            "agent_name": "Query Agent",
            "agent_class": "query",
            "agent_dependencies": []
        },
        {
            "agent_id": "agent-mgmt-1",
            "agent_name": "Management Agent",
            "agent_class": "management",
            "agent_dependencies": []
        }
    ]
    
    # Mock check query and update result
    mock_cursor.fetchone.side_effect = [
        {
            "id": "uuid-123",
            "ingestion_playbook": {"agent_execution_graph": {"nodes": ["agent-ing-1"], "edges": []}},
            "query_playbook": {"agent_execution_graph": {"nodes": ["agent-qry-1"], "edges": []}},
            "management_playbook": {"agent_execution_graph": {"nodes": ["agent-mgmt-1"], "edges": []}}
        },
        # Mock update result
        {
            "id": "uuid-123",
            "domain_id": "test-domain",
            "domain_name": "Updated Domain",
            "description": "Updated description",
            "ingestion_playbook": {"agent_execution_graph": {"nodes": ["agent-ing-1"], "edges": []}},
            "query_playbook": {"agent_execution_graph": {"nodes": ["agent-qry-1"], "edges": []}},
            "management_playbook": {"agent_execution_graph": {"nodes": ["agent-mgmt-1"], "edges": []}},
            "created_at": datetime(2025, 10, 21, 10, 0, 0),
            "updated_at": datetime(2025, 10, 21, 11, 0, 0),
            "created_by": "user-123"
        }
    ]
    
    event = {
        "httpMethod": "PUT",
        "path": "/api/v1/domains/test-domain",
        "pathParameters": {"domain_id": "test-domain"},
        "body": json.dumps({
            "domain_name": "Updated Domain",
            "description": "Updated description"
        }),
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 200


def test_handler_routes_delete_domain(mock_db_connection):
    """Test handler routes DELETE /domains/{domain_id} to delete_domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock check query
    mock_cursor.fetchone.return_value = {"id": "uuid-123"}
    
    event = {
        "httpMethod": "DELETE",
        "path": "/api/v1/domains/test-domain",
        "pathParameters": {"domain_id": "test-domain"},
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["message"] == "Domain deleted successfully"


def test_handler_invalid_json_body():
    """Test handler returns 400 for invalid JSON"""
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/domains",
        "body": "invalid json{",
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 400


def test_handler_endpoint_not_found():
    """Test handler returns 404 for unknown endpoint"""
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/unknown",
        "requestContext": {
            "authorizer": {
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        }
    }
    
    response = handler(event, {})
    assert response["statusCode"] == 404


# Test create_domain validation

def test_create_domain_missing_required_field(mock_db_connection):
    """Test create_domain returns 400 for missing required fields"""
    body = {
        "domain_id": "test-domain"
        # Missing domain_name and playbooks
    }
    
    response = create_domain("tenant-1", "user-1", body)
    assert response["statusCode"] == 400
    assert "Missing required field" in json.loads(response["body"])["error"]


def test_create_domain_duplicate_id(mock_db_connection):
    """Test create_domain returns 409 for duplicate domain_id"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock agents query
    mock_cursor.fetchall.return_value = [
        {
            "agent_id": "agent-1",
            "agent_name": "Agent 1",
            "agent_class": "ingestion",
            "agent_dependencies": []
        }
    ]
    
    # Mock UniqueViolation error
    import psycopg.errors
    mock_cursor.execute.side_effect = psycopg.errors.UniqueViolation("duplicate key")
    
    body = {
        "domain_id": "test-domain",
        "domain_name": "Test Domain",
        "ingestion_playbook": {
            "agent_execution_graph": {
                "nodes": ["agent-1"],
                "edges": []
            }
        },
        "query_playbook": {
            "agent_execution_graph": {
                "nodes": ["agent-1"],
                "edges": []
            }
        },
        "management_playbook": {
            "agent_execution_graph": {
                "nodes": ["agent-1"],
                "edges": []
            }
        }
    }
    
    response = create_domain("tenant-1", "user-1", body)
    assert response["statusCode"] == 409


# Test list_domains pagination

def test_list_domains_with_pagination(mock_db_connection):
    """Test list_domains respects pagination parameters"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock count query
    mock_cursor.fetchone.return_value = {"total": 50}
    
    # Mock list query
    mock_cursor.fetchall.return_value = []
    
    query_params = {"page": "2", "limit": "10"}
    
    response = list_domains("tenant-1", "user-1", query_params)
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["limit"] == 10
    assert body["pagination"]["total"] == 50


def test_list_domains_max_limit(mock_db_connection):
    """Test list_domains enforces max limit of 100"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock count query
    mock_cursor.fetchone.return_value = {"total": 200}
    
    # Mock list query
    mock_cursor.fetchall.return_value = []
    
    query_params = {"limit": "500"}  # Request more than max
    
    response = list_domains("tenant-1", "user-1", query_params)
    assert response["statusCode"] == 200
    
    body = json.loads(response["body"])
    assert body["pagination"]["limit"] == 100  # Capped at 100


# Test get_domain not found

def test_get_domain_not_found(mock_db_connection):
    """Test get_domain returns 404 for non-existent domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock domain not found
    mock_cursor.fetchone.return_value = None
    
    response = get_domain("tenant-1", "user-1", "non-existent-domain")
    assert response["statusCode"] == 404


# Test update_domain validation

def test_update_domain_not_found(mock_db_connection):
    """Test update_domain returns 404 for non-existent domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock domain not found
    mock_cursor.fetchone.return_value = None
    
    body = {"domain_name": "Updated Name"}
    
    response = update_domain("tenant-1", "user-1", "non-existent-domain", body)
    assert response["statusCode"] == 404


def test_update_domain_no_fields(mock_db_connection):
    """Test update_domain returns 400 when no fields to update"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock existing domain
    mock_cursor.fetchone.return_value = {
        "id": "uuid-123",
        "ingestion_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}},
        "query_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}},
        "management_playbook": {"agent_execution_graph": {"nodes": [], "edges": []}}
    }
    
    # Mock agents query
    mock_cursor.fetchall.return_value = []
    
    body = {}  # No fields to update
    
    response = update_domain("tenant-1", "user-1", "test-domain", body)
    assert response["statusCode"] == 400


# Test delete_domain

def test_delete_domain_not_found(mock_db_connection):
    """Test delete_domain returns 404 for non-existent domain"""
    mock_cursor, mock_connection = mock_db_connection
    
    # Mock domain not found
    mock_cursor.fetchone.return_value = None
    
    response = delete_domain("tenant-1", "user-1", "non-existent-domain")
    assert response["statusCode"] == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
