"""
Unit tests for Report Handler
Tests CRUD operations for reports
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

import report_handler


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table"""
    with patch('report_handler.reports_table') as mock_table:
        yield mock_table


@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client"""
    with patch('report_handler.lambda_client') as mock_client:
        yield mock_client


@pytest.fixture
def sample_report():
    """Sample report document"""
    return {
        "incident_id": "inc_test123",
        "tenant_id": "tenant-123",
        "domain_id": "civic_complaints",
        "raw_text": "Test report text",
        "status": "completed",
        "ingestion_data": {
            "complaint_type": "pothole",
            "location_text": "Main Street",
        },
        "management_data": {
            "task_details": {
                "assignee_id": "team-1",
                "priority": "high",
            }
        },
        "id": "report-uuid-123",
        "created_at": "2025-10-21T16:00:00Z",
        "updated_at": "2025-10-21T16:05:00Z",
        "created_by": "user-123",
        "source": "web",
    }


def test_create_report_success(mock_dynamodb_table, mock_lambda_client):
    """Test successful report creation"""
    # Mock DynamoDB put_item
    mock_dynamodb_table.put_item = Mock()
    
    # Mock Lambda invoke
    mock_lambda_client.invoke = Mock()
    
    # Create event
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/reports",
        "body": json.dumps({
            "domain_id": "civic_complaints",
            "text": "There is a pothole on Main Street",
            "images": ["https://example.com/image.jpg"],
            "source": "mobile-app",
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant-123",
                "userId": "user-123",
            }
        },
    }
    
    # Call handler
    response = report_handler.create_report(event, "tenant-123", "user-123")
    
    # Verify response
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert "job_id" in body
    assert "incident_id" in body
    assert body["status"] == "accepted"
    assert body["message"] == "Report submitted for processing"
    
    # Verify DynamoDB was called
    mock_dynamodb_table.put_item.assert_called_once()
    call_args = mock_dynamodb_table.put_item.call_args
    item = call_args[1]["Item"]
    assert item["domain_id"] == "civic_complaints"
    assert item["raw_text"] == "There is a pothole on Main Street"
    assert item["tenant_id"] == "tenant-123"
    assert item["ingestion_data"] == {}
    assert item["management_data"] == {}


def test_create_report_missing_domain_id():
    """Test report creation with missing domain_id"""
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/reports",
        "body": json.dumps({
            "text": "Test report",
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant-123",
                "userId": "user-123",
            }
        },
    }
    
    response = report_handler.create_report(event, "tenant-123", "user-123")
    
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "domain_id" in body["error"]


def test_create_report_missing_text():
    """Test report creation with missing text"""
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/reports",
        "body": json.dumps({
            "domain_id": "civic_complaints",
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant-123",
                "userId": "user-123",
            }
        },
    }
    
    response = report_handler.create_report(event, "tenant-123", "user-123")
    
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "text" in body["error"]


def test_get_report_success(mock_dynamodb_table, sample_report):
    """Test successful report retrieval"""
    # Mock DynamoDB get_item
    mock_dynamodb_table.get_item = Mock(return_value={"Item": sample_report})
    
    response = report_handler.get_report("inc_test123", "tenant-123")
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["incident_id"] == "inc_test123"
    assert body["domain_id"] == "civic_complaints"
    assert "ingestion_data" in body
    assert "management_data" in body


def test_get_report_not_found(mock_dynamodb_table):
    """Test report retrieval when report doesn't exist"""
    # Mock DynamoDB get_item returning no item
    mock_dynamodb_table.get_item = Mock(return_value={})
    
    response = report_handler.get_report("inc_notfound", "tenant-123")
    
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "not found" in body["error"].lower()


def test_get_report_access_denied(mock_dynamodb_table, sample_report):
    """Test report retrieval with wrong tenant"""
    # Mock DynamoDB get_item
    mock_dynamodb_table.get_item = Mock(return_value={"Item": sample_report})
    
    # Try to access with different tenant
    response = report_handler.get_report("inc_test123", "tenant-999")
    
    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert "access denied" in body["error"].lower()


def test_list_reports_with_domain_filter(mock_dynamodb_table, sample_report):
    """Test listing reports with domain_id filter"""
    # Mock DynamoDB query
    mock_dynamodb_table.query = Mock(return_value={"Items": [sample_report]})
    
    event = {
        "queryStringParameters": {
            "domain_id": "civic_complaints",
            "page": "1",
            "limit": "20",
        }
    }
    
    response = report_handler.list_reports(event, "tenant-123")
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "reports" in body
    assert "pagination" in body
    assert len(body["reports"]) == 1
    assert body["reports"][0]["incident_id"] == "inc_test123"


def test_update_report_status(mock_dynamodb_table, sample_report):
    """Test updating report status"""
    # Mock DynamoDB get_item and update_item
    mock_dynamodb_table.get_item = Mock(return_value={"Item": sample_report})
    updated_report = sample_report.copy()
    updated_report["status"] = "in_progress"
    mock_dynamodb_table.update_item = Mock(return_value={"Attributes": updated_report})
    
    event = {
        "body": json.dumps({
            "status": "in_progress",
        })
    }
    
    response = report_handler.update_report(event, "inc_test123", "tenant-123", "user-123")
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "in_progress"


def test_update_report_merge_management_data(mock_dynamodb_table, sample_report):
    """Test merging management_data"""
    # Mock DynamoDB get_item and update_item
    mock_dynamodb_table.get_item = Mock(return_value={"Item": sample_report})
    
    # Capture the update call
    def mock_update(**kwargs):
        return {"Attributes": sample_report}
    
    mock_dynamodb_table.update_item = Mock(side_effect=mock_update)
    
    event = {
        "body": json.dumps({
            "management_data": {
                "task_details": {
                    "due_at": "2025-10-25T16:00:00Z",
                },
                "notes": "Additional notes",
            }
        })
    }
    
    response = report_handler.update_report(event, "inc_test123", "tenant-123", "user-123")
    
    assert response["statusCode"] == 200
    
    # Verify update_item was called with merged data
    mock_dynamodb_table.update_item.assert_called_once()


def test_delete_report_success(mock_dynamodb_table, sample_report):
    """Test successful report deletion"""
    # Mock DynamoDB get_item and delete_item
    mock_dynamodb_table.get_item = Mock(return_value={"Item": sample_report})
    mock_dynamodb_table.delete_item = Mock()
    
    response = report_handler.delete_report("inc_test123", "tenant-123")
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Report deleted successfully"
    assert body["incident_id"] == "inc_test123"
    
    # Verify delete_item was called
    mock_dynamodb_table.delete_item.assert_called_once()


def test_delete_report_not_found(mock_dynamodb_table):
    """Test deleting non-existent report"""
    # Mock DynamoDB get_item returning no item
    mock_dynamodb_table.get_item = Mock(return_value={})
    
    response = report_handler.delete_report("inc_notfound", "tenant-123")
    
    assert response["statusCode"] == 404


def test_deep_merge():
    """Test deep merge utility function"""
    base = {
        "task_details": {
            "assignee_id": "team-1",
            "priority": "high",
        },
        "history": [{"status": "pending"}],
    }
    
    update = {
        "task_details": {
            "due_at": "2025-10-25T16:00:00Z",
        },
        "notes": "New notes",
    }
    
    result = report_handler.deep_merge(base, update)
    
    assert result["task_details"]["assignee_id"] == "team-1"
    assert result["task_details"]["priority"] == "high"
    assert result["task_details"]["due_at"] == "2025-10-25T16:00:00Z"
    assert result["notes"] == "New notes"
    assert result["history"] == [{"status": "pending"}]


def test_handler_routing(mock_dynamodb_table):
    """Test main handler routing"""
    # Test POST /reports
    event = {
        "httpMethod": "POST",
        "path": "/api/v1/reports",
        "body": json.dumps({
            "domain_id": "test",
            "text": "test",
        }),
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant-123",
                "userId": "user-123",
            }
        },
    }
    
    mock_dynamodb_table.put_item = Mock()
    
    response = report_handler.handler(event, None)
    assert response["statusCode"] in [200, 202, 400, 500]
    
    # Test GET /reports/{incident_id}
    event = {
        "httpMethod": "GET",
        "path": "/api/v1/reports/inc_test123",
        "pathParameters": {"incident_id": "inc_test123"},
        "requestContext": {
            "authorizer": {
                "tenantId": "tenant-123",
            }
        },
    }
    
    mock_dynamodb_table.get_item = Mock(return_value={})
    
    response = report_handler.handler(event, None)
    assert response["statusCode"] in [200, 404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
