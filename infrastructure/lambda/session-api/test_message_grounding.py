"""
Test Message Grounding Implementation
Tests the create_assistant_message function with references
"""

import json
import sys
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from message_utils import (
    create_assistant_message,
    create_user_message,
    format_references_from_query_result,
)


def test_create_assistant_message_with_references():
    """Test creating an assistant message with grounding references"""
    
    # Mock DynamoDB tables
    mock_messages_table = Mock()
    mock_sessions_table = Mock()
    
    # Mock boto3.resource to return our mocks
    with patch('message_utils.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_messages_table if 'Messages' in name else mock_sessions_table
        )
        
        # Test data
        session_id = "sess_test123"
        content = "I found 5 pothole reports in your area."
        query_id = "qry_abc123"
        references = [
            {
                "type": "report",
                "reference_id": "inc_report1",
                "summary": "Pothole on Main Street",
                "status": "pending",
                "location": {
                    "type": "Point",
                    "coordinates": [36.9, 37.1]
                }
            },
            {
                "type": "report",
                "reference_id": "inc_report2",
                "summary": "Pothole on Oak Avenue",
                "status": "in_progress",
                "location": {
                    "type": "Point",
                    "coordinates": [36.91, 37.11]
                }
            }
        ]
        
        # Call function
        message = create_assistant_message(
            session_id=session_id,
            content=content,
            query_id=query_id,
            references=references,
            messages_table_name="TestMessages",
            sessions_table_name="TestSessions",
        )
        
        # Verify message structure
        assert message["session_id"] == session_id
        assert message["role"] == "assistant"
        assert message["content"] == content
        assert "message_id" in message
        assert message["message_id"].startswith("msg_")
        assert "timestamp" in message
        
        # Verify metadata with references
        assert "metadata" in message
        assert message["metadata"]["query_id"] == query_id
        assert "references" in message["metadata"]
        assert len(message["metadata"]["references"]) == 2
        
        # Verify reference structure
        ref1 = message["metadata"]["references"][0]
        assert ref1["type"] == "report"
        assert ref1["reference_id"] == "inc_report1"
        assert ref1["summary"] == "Pothole on Main Street"
        assert ref1["status"] == "pending"
        assert "location" in ref1
        
        # Verify DynamoDB calls
        assert mock_messages_table.put_item.called
        assert mock_sessions_table.update_item.called
        
        # Verify session update includes last_activity
        update_call = mock_sessions_table.update_item.call_args
        assert "last_activity" in update_call[1]["UpdateExpression"]
        assert "message_count" in update_call[1]["UpdateExpression"]
        
        print("✅ Test passed: create_assistant_message with references")
        return True


def test_create_user_message():
    """Test creating a user message"""
    
    # Mock DynamoDB tables
    mock_messages_table = Mock()
    mock_sessions_table = Mock()
    
    with patch('message_utils.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_messages_table if 'Messages' in name else mock_sessions_table
        )
        
        # Test data
        session_id = "sess_test123"
        content = "Show me all potholes in my area"
        
        # Call function
        message = create_user_message(
            session_id=session_id,
            content=content,
            messages_table_name="TestMessages",
            sessions_table_name="TestSessions",
        )
        
        # Verify message structure
        assert message["session_id"] == session_id
        assert message["role"] == "user"
        assert message["content"] == content
        assert "message_id" in message
        assert "timestamp" in message
        
        # User messages should not have metadata
        assert "metadata" not in message
        
        # Verify DynamoDB calls
        assert mock_messages_table.put_item.called
        assert mock_sessions_table.update_item.called
        
        print("✅ Test passed: create_user_message")
        return True


def test_format_references_from_query_result():
    """Test formatting references from query result"""
    
    query_result = {
        "query_id": "qry_123",
        "references_used": [
            {
                "type": "report",
                "reference_id": "inc_1",
                "summary": "Test report",
                "status": "pending",
                "location": {
                    "type": "Point",
                    "coordinates": [36.9, 37.1]
                },
                "extra_field": "should be ignored"
            }
        ]
    }
    
    references = format_references_from_query_result(query_result)
    
    assert len(references) == 1
    assert references[0]["type"] == "report"
    assert references[0]["reference_id"] == "inc_1"
    assert references[0]["summary"] == "Test report"
    assert references[0]["status"] == "pending"
    assert "location" in references[0]
    assert "extra_field" not in references[0]
    
    print("✅ Test passed: format_references_from_query_result")
    return True


def test_empty_references():
    """Test creating assistant message with empty references"""
    
    mock_messages_table = Mock()
    mock_sessions_table = Mock()
    
    with patch('message_utils.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_messages_table if 'Messages' in name else mock_sessions_table
        )
        
        # Test with empty references
        message = create_assistant_message(
            session_id="sess_test",
            content="No results found",
            query_id="qry_test",
            references=[],
            messages_table_name="TestMessages",
            sessions_table_name="TestSessions",
        )
        
        # Should still have metadata with empty references array
        assert "metadata" in message
        assert message["metadata"]["references"] == []
        
        print("✅ Test passed: empty references")
        return True


if __name__ == "__main__":
    print("\n=== Testing Message Grounding Implementation ===\n")
    
    try:
        test_create_assistant_message_with_references()
        test_create_user_message()
        test_format_references_from_query_result()
        test_empty_references()
        
        print("\n✅ All tests passed!\n")
        print("Message grounding implementation is working correctly:")
        print("  ✓ create_assistant_message() creates messages with references")
        print("  ✓ References array links to source Reports")
        print("  ✓ Session last_activity is updated on message creation")
        print("  ✓ Message metadata includes query_id and references")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
