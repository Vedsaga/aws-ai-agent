"""
Test script for RAG Engine Lambda

Tests the RAG engine functionality with mock data.
"""

import json
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock AWS services before importing rag_engine
sys.modules['boto3'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['opensearchpy'] = MagicMock()
sys.modules['requests_aws4auth'] = MagicMock()

# Set environment variables
import os
os.environ['OPENSEARCH_ENDPOINT'] = 'test-endpoint.us-east-1.es.amazonaws.com'
os.environ['DB_HOST'] = 'test-db.us-east-1.rds.amazonaws.com'
os.environ['DB_NAME'] = 'test_db'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_password'

# Now import rag_engine
import rag_engine


def test_lambda_handler_missing_params():
    """Test lambda handler with missing parameters."""
    print("Test 1: Missing parameters")
    
    event = {
        'body': json.dumps({
            'question': 'What are the trends?'
            # Missing tenant_id
        })
    }
    
    response = rag_engine.lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'bad_request'
    print("✓ Correctly rejects missing tenant_id")


def test_lambda_handler_valid_request():
    """Test lambda handler with valid request."""
    print("\nTest 2: Valid request structure")
    
    # Mock the rag_query function
    with patch.object(rag_engine, 'rag_query') as mock_rag:
        mock_rag.return_value = {
            'status': 'success',
            'context': [
                {
                    'incident_id': 'test-123',
                    'domain_id': 'civic',
                    'created_at': '2024-01-15T10:30:00',
                    'preview': 'Test incident'
                }
            ],
            'response': 'Test response',
            'incident_count': 1
        }
        
        event = {
            'body': json.dumps({
                'question': 'What are the trends?',
                'tenant_id': 'test-tenant',
                'domain_id': 'civic',
                'top_k': 5
            })
        }
        
        response = rag_engine.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert body['incident_count'] == 1
        print("✓ Handles valid request correctly")


def test_create_embedding():
    """Test embedding creation."""
    print("\nTest 3: Embedding creation")
    
    # Mock Bedrock client
    mock_bedrock = MagicMock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]
    }).encode()
    mock_bedrock.invoke_model.return_value = mock_response
    
    with patch.object(rag_engine, 'bedrock_runtime', mock_bedrock):
        embedding = rag_engine.create_embedding("test text")
        
        assert len(embedding) == 5
        assert embedding[0] == 0.1
        print("✓ Creates embeddings correctly")


def test_vector_search_no_opensearch():
    """Test vector search when OpenSearch is not configured."""
    print("\nTest 4: Vector search without OpenSearch")
    
    with patch.object(rag_engine, 'opensearch_client', None):
        results = rag_engine.vector_search(
            query_text="test query",
            tenant_id="test-tenant"
        )
        
        assert results == []
        print("✓ Handles missing OpenSearch gracefully")


def test_vector_search_with_results():
    """Test vector search with mock results."""
    print("\nTest 5: Vector search with results")
    
    # Mock OpenSearch client
    mock_opensearch = MagicMock()
    mock_opensearch.search.return_value = {
        'hits': {
            'hits': [
                {
                    '_source': {
                        'incident_id': 'incident-1',
                        'text_content': 'Test incident 1'
                    },
                    '_score': 0.95
                },
                {
                    '_source': {
                        'incident_id': 'incident-2',
                        'text_content': 'Test incident 2'
                    },
                    '_score': 0.85
                }
            ],
            'total': {'value': 2}
        }
    }
    
    with patch.object(rag_engine, 'opensearch_client', mock_opensearch):
        with patch.object(rag_engine, 'create_embedding', return_value=[0.1] * 1536):
            results = rag_engine.vector_search(
                query_text="test query",
                tenant_id="test-tenant",
                top_k=10
            )
            
            assert len(results) == 2
            assert results[0]['incident_id'] == 'incident-1'
            assert results[0]['score'] == 0.95
            print("✓ Performs vector search correctly")


def test_retrieve_full_incidents():
    """Test full incident retrieval."""
    print("\nTest 6: Full incident retrieval")
    
    from datetime import datetime
    
    # Mock database connection
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        (
            'incident-1',
            'tenant-1',
            'civic',
            'Test raw text',
            {'category': 'pothole'},
            datetime(2024, 1, 15, 10, 30, 0),
            datetime(2024, 1, 15, 10, 30, 0)
        )
    ]
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    with patch.object(rag_engine, 'get_db_connection', return_value=mock_conn):
        incidents = rag_engine.retrieve_full_incidents(
            incident_ids=['incident-1'],
            tenant_id='tenant-1'
        )
        
        assert len(incidents) == 1
        assert incidents[0]['id'] == 'incident-1'
        assert incidents[0]['structured_data']['category'] == 'pothole'
        print("✓ Retrieves full incidents correctly")


def test_generate_contextual_response():
    """Test contextual response generation."""
    print("\nTest 7: Contextual response generation")
    
    # Mock Bedrock client
    mock_bedrock = MagicMock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [
            {
                'text': 'Based on the incident data, there is a trend of increasing pothole complaints.'
            }
        ],
        'usage': {}
    }).encode()
    mock_bedrock.invoke_model.return_value = mock_response
    
    incidents = [
        {
            'id': 'incident-1',
            'raw_text': 'Pothole on Main Street',
            'structured_data': {'category': 'pothole', 'severity': 'high'}
        }
    ]
    
    with patch.object(rag_engine, 'bedrock_runtime', mock_bedrock):
        response = rag_engine.generate_contextual_response(
            question="What are the trends?",
            incidents=incidents,
            agent_context="Analyzing temporal patterns"
        )
        
        assert 'trend' in response.lower()
        assert len(response) > 0
        print("✓ Generates contextual responses correctly")


def test_rag_query_no_results():
    """Test RAG query with no vector search results."""
    print("\nTest 8: RAG query with no results")
    
    with patch.object(rag_engine, 'vector_search', return_value=[]):
        result = rag_engine.rag_query(
            question="test question",
            tenant_id="test-tenant"
        )
        
        assert result['status'] == 'success'
        assert result['incident_count'] == 0
        assert 'No relevant incidents' in result['response']
        print("✓ Handles no results gracefully")


def test_rag_query_full_flow():
    """Test complete RAG query flow."""
    print("\nTest 9: Complete RAG query flow")
    
    # Mock vector search
    mock_vector_results = [
        {'incident_id': 'incident-1', 'score': 0.95, 'text_preview': 'Test'}
    ]
    
    # Mock full incidents
    mock_incidents = [
        {
            'id': 'incident-1',
            'tenant_id': 'tenant-1',
            'domain_id': 'civic',
            'raw_text': 'Pothole on Main Street',
            'structured_data': {'category': 'pothole'},
            'created_at': '2024-01-15T10:30:00',
            'updated_at': '2024-01-15T10:30:00'
        }
    ]
    
    # Mock response
    mock_response = "Based on the data, pothole complaints are increasing."
    
    with patch.object(rag_engine, 'vector_search', return_value=mock_vector_results):
        with patch.object(rag_engine, 'retrieve_full_incidents', return_value=mock_incidents):
            with patch.object(rag_engine, 'generate_contextual_response', return_value=mock_response):
                result = rag_engine.rag_query(
                    question="What are the trends?",
                    tenant_id="tenant-1",
                    domain_id="civic"
                )
                
                assert result['status'] == 'success'
                assert result['incident_count'] == 1
                assert result['response'] == mock_response
                assert len(result['context']) == 1
                print("✓ Complete RAG flow works correctly")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RAG Engine Lambda Tests")
    print("=" * 60)
    
    try:
        test_lambda_handler_missing_params()
        test_lambda_handler_valid_request()
        test_create_embedding()
        test_vector_search_no_opensearch()
        test_vector_search_with_results()
        test_retrieve_full_incidents()
        test_generate_contextual_response()
        test_rag_query_no_results()
        test_rag_query_full_flow()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
