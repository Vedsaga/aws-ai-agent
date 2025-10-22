"""
Unit tests for Query Handler with mode selection
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from query_handler_simple import (
    handler,
    handle_submit_query,
    handle_get_query,
    handle_list_queries,
    handle_delete_query,
)


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    with patch("query_handler_simple.query_jobs_table") as mock_table:
        yield mock_table


@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client"""
    with patch("query_handler_simple.lambda_client") as mock_client:
        yield mock_client


def test_submit_query_with_query_mode(mock_dynamodb_table, mock_lambda_client):
    """Test submitting a query with mode='query'"""
    # Arrange
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/queries",
        "body": json.dumps({
            "session_id": "sess_123",
            "domain_id": "civic_complaints_v1",
            "question": "Show me all potholes",
            "mode": "query"
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    mock_dynamodb_table.put_item = Mock()
    mock_lambda_client.invoke = Mock()
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert "job_id" in body
    assert "query_id" in body
    assert body["status"] == "accepted"
    
    # Verify DynamoDB put_item was called
    mock_dynamodb_table.put_item.assert_called_once()
    call_args = mock_dynamodb_table.put_item.call_args[1]
    item = call_args["Item"]
    assert item["mode"] == "query"
    assert item["question"] == "Show me all potholes"
    assert "execution_log" in item
    assert "map_data" in item
    assert "references_used" in item
    
    # Verify Lambda invoke was called with correct playbook_type
    mock_lambda_client.invoke.assert_called_once()
    invoke_args = mock_lambda_client.invoke.call_args[1]
    payload = json.loads(invoke_args["Payload"])
    assert payload["playbook_type"] == "query_playbook"
    assert payload["job_type"] == "query"


def test_submit_query_with_management_mode(mock_dynamodb_table, mock_lambda_client):
    """Test submitting a query with mode='management'"""
    # Arrange
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/queries",
        "body": json.dumps({
            "session_id": "sess_123",
            "domain_id": "civic_complaints_v1",
            "question": "Assign this to Team B",
            "mode": "management"
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    mock_dynamodb_table.put_item = Mock()
    mock_lambda_client.invoke = Mock()
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    
    # Verify Lambda invoke was called with management_playbook
    invoke_args = mock_lambda_client.invoke.call_args[1]
    payload = json.loads(invoke_args["Payload"])
    assert payload["playbook_type"] == "management_playbook"
    assert payload["job_type"] == "management"


def test_submit_query_missing_session_id(mock_dynamodb_table, mock_lambda_client):
    """Test submitting a query without session_id"""
    # Arrange
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/queries",
        "body": json.dumps({
            "domain_id": "civic_complaints_v1",
            "question": "Show me all potholes"
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "session_id" in body["error"]


def test_submit_query_invalid_mode(mock_dynamodb_table, mock_lambda_client):
    """Test submitting a query with invalid mode"""
    # Arrange
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/queries",
        "body": json.dumps({
            "session_id": "sess_123",
            "domain_id": "civic_complaints_v1",
            "question": "Show me all potholes",
            "mode": "invalid"
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "mode" in body["error"]


def test_get_query(mock_dynamodb_table):
    """Test getting a query by ID"""
    # Arrange
    query_id = "qry_12345678"
    mock_query = {
        "query_id": query_id,
        "job_id": "query_abc123",
        "session_id": "sess_123",
        "tenant_id": "tenant_123",
        "question": "Show me all potholes",
        "mode": "query",
        "status": "completed",
        "summary": "Found 5 potholes",
        "execution_log": [
            {
                "agent_id": "agent_1",
                "agent_name": "Query Agent",
                "status": "success",
                "timestamp": "2025-10-21T10:00:00Z",
                "reasoning": "Searched for potholes",
                "output": {"count": 5}
            }
        ],
        "map_data": {},
        "references_used": []
    }
    
    mock_dynamodb_table.get_item = Mock(return_value={"Item": mock_query})
    
    event = {
        "httpMethod": "GET",
        "path": f"/api/v1/queries/{query_id}",
        "pathParameters": {"query_id": query_id},
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["query_id"] == query_id
    assert body["status"] == "completed"
    assert "execution_log" in body
    assert len(body["execution_log"]) == 1
    assert "map_data" in body
    assert "references_used" in body


def test_get_query_not_found(mock_dynamodb_table):
    """Test getting a non-existent query"""
    # Arrange
    query_id = "qry_notfound"
    mock_dynamodb_table.get_item = Mock(return_value={})
    
    event = {
        "httpMethod": "GET",
        "path": f"/api/v1/queries/{query_id}",
        "pathParameters": {"query_id": query_id},
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 404


def test_list_queries(mock_dynamodb_table):
    """Test listing queries"""
    # Arrange
    mock_queries = [
        {
            "query_id": "qry_1",
            "question": "Question 1",
            "status": "completed",
            "created_at": "2025-10-21T10:00:00Z",
            "tenant_id": "tenant_123"
        },
        {
            "query_id": "qry_2",
            "question": "Question 2",
            "status": "processing",
            "created_at": "2025-10-21T11:00:00Z",
            "tenant_id": "tenant_123"
        }
    ]
    
    mock_dynamodb_table.scan = Mock(return_value={"Items": mock_queries})
    
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/queries",
        "queryStringParameters": {"page": "1", "limit": "20"},
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "queries" in body
    assert len(body["queries"]) == 2
    assert "pagination" in body


def test_delete_query(mock_dynamodb_table):
    """Test deleting a query"""
    # Arrange
    query_id = "qry_12345678"
    mock_query = {
        "query_id": query_id,
        "tenant_id": "tenant_123"
    }
    
    mock_dynamodb_table.get_item = Mock(return_value={"Item": mock_query})
    mock_dynamodb_table.delete_item = Mock()
    
    event = {
        "httpMethod": "DELETE",
        "path": f"/api/v1/queries/{query_id}",
        "pathParameters": {"query_id": query_id},
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant_123",
                "userId": "user_123"
            }
        }
    }
    
    # Act
    response = handler(event, {})
    
    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "deleted successfully" in body["message"]
    mock_dynamodb_table.delete_item.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
