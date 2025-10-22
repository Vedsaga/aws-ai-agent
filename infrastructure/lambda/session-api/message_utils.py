"""
Message Utilities
Helper functions for creating and managing messages with grounding references.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3

dynamodb = boto3.resource("dynamodb")


def create_user_message(
    session_id: str,
    content: str,
    messages_table_name: str,
    sessions_table_name: str,
) -> Dict[str, Any]:
    """
    Create a user message in a session.
    
    Args:
        session_id: The session ID
        content: The message content
        messages_table_name: DynamoDB table name for messages
        sessions_table_name: DynamoDB table name for sessions
    
    Returns:
        The created message document
    """
    messages_table = dynamodb.Table(messages_table_name)
    sessions_table = dynamodb.Table(sessions_table_name)
    
    # Create message
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat()
    
    message = {
        "message_id": message_id,
        "session_id": session_id,
        "role": "user",
        "content": content,
        "timestamp": timestamp,
    }
    
    # Store message
    messages_table.put_item(Item=message)
    
    # Update session last_activity and message_count
    sessions_table.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET last_activity = :timestamp, message_count = message_count + :inc, updated_at = :timestamp",
        ExpressionAttributeValues={
            ":timestamp": timestamp,
            ":inc": 1,
        },
    )
    
    return message


def create_assistant_message(
    session_id: str,
    content: str,
    query_id: str,
    references: List[Dict[str, Any]],
    messages_table_name: str,
    sessions_table_name: str,
) -> Dict[str, Any]:
    """
    Create an assistant message with grounding references.
    
    Args:
        session_id: The session ID
        content: The message content (summary/answer)
        query_id: The query ID that generated this response
        references: Array of source Reports used to generate the answer
        messages_table_name: DynamoDB table name for messages
        sessions_table_name: DynamoDB table name for sessions
    
    Returns:
        The created message document with metadata
    
    Example references:
    [
        {
            "type": "report",
            "reference_id": "inc_abc123",
            "summary": "Pothole on Main St",
            "status": "pending",
            "location": {
                "type": "Point",
                "coordinates": [36.9, 37.1]
            }
        }
    ]
    """
    messages_table = dynamodb.Table(messages_table_name)
    sessions_table = dynamodb.Table(sessions_table_name)
    
    # Create message with metadata
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat()
    
    message = {
        "message_id": message_id,
        "session_id": session_id,
        "role": "assistant",
        "content": content,
        "timestamp": timestamp,
        "metadata": {
            "query_id": query_id,
            "references": references,
        },
    }
    
    # Store message
    messages_table.put_item(Item=message)
    
    # Update session last_activity and message_count
    sessions_table.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET last_activity = :timestamp, message_count = message_count + :inc, updated_at = :timestamp",
        ExpressionAttributeValues={
            ":timestamp": timestamp,
            ":inc": 1,
        },
    )
    
    return message


def get_session_messages(
    session_id: str,
    messages_table_name: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get all messages for a session in chronological order.
    
    Args:
        session_id: The session ID
        messages_table_name: DynamoDB table name for messages
        limit: Optional limit on number of messages to return
    
    Returns:
        List of messages sorted by timestamp
    """
    messages_table = dynamodb.Table(messages_table_name)
    
    query_kwargs = {
        "IndexName": "session-timestamp-index",
        "KeyConditionExpression": "session_id = :session_id",
        "ExpressionAttributeValues": {":session_id": session_id},
        "ScanIndexForward": True,  # Sort by timestamp ascending
    }
    
    if limit:
        query_kwargs["Limit"] = limit
    
    response = messages_table.query(**query_kwargs)
    
    return response.get("Items", [])


def delete_session_messages(
    session_id: str,
    messages_table_name: str,
) -> int:
    """
    Delete all messages for a session (cascade delete).
    
    Args:
        session_id: The session ID
        messages_table_name: DynamoDB table name for messages
    
    Returns:
        Number of messages deleted
    """
    messages_table = dynamodb.Table(messages_table_name)
    
    # Query all messages for this session
    response = messages_table.query(
        IndexName="session-timestamp-index",
        KeyConditionExpression="session_id = :session_id",
        ExpressionAttributeValues={":session_id": session_id},
    )
    
    messages = response.get("Items", [])
    
    # Delete each message
    for msg in messages:
        messages_table.delete_item(Key={"message_id": msg["message_id"]})
    
    return len(messages)


def format_references_from_query_result(query_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract and format references from a query result.
    
    Args:
        query_result: The query result from query handler
    
    Returns:
        Formatted references array for message metadata
    """
    references_used = query_result.get("references_used", [])
    
    # References are already in the correct format from query handler
    # Just ensure they have the required fields
    formatted_references = []
    
    for ref in references_used:
        formatted_ref = {
            "type": ref.get("type", "report"),
            "reference_id": ref.get("reference_id", ""),
            "summary": ref.get("summary", ""),
        }
        
        # Add optional fields if present
        if "status" in ref:
            formatted_ref["status"] = ref["status"]
        
        if "location" in ref:
            formatted_ref["location"] = ref["location"]
        
        formatted_references.append(formatted_ref)
    
    return formatted_references
