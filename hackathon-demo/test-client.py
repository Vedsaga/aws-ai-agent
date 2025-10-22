#!/usr/bin/env python3
"""
Simple test client for DomainFlow API
"""
import requests
import json
import sys
import uuid
import boto3

def get_api_endpoint():
    """Get API endpoint from CloudFormation"""
    cfn = boto3.client('cloudformation')
    response = cfn.describe_stacks(StackName='DomainFlowDemo')
    outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
    return outputs['ApiEndpoint']

def test_ingestion_vague():
    """Test ingestion with vague location"""
    print("\n=== Test 1: Ingestion with vague location ===")
    
    api_url = get_api_endpoint()
    response = requests.post(
        f"{api_url}orchestrate",
        json={
            "mode": "ingestion",
            "message": "Street light broken near the post office"
        }
    )
    
    data = response.json()
    print(json.dumps(data, indent=2))
    
    return data

def test_ingestion_clarification():
    """Test ingestion with clarification"""
    print("\n=== Test 2: Ingestion with clarification ===")
    
    api_url = get_api_endpoint()
    session_id = str(uuid.uuid4())
    
    # First message
    response1 = requests.post(
        f"{api_url}orchestrate",
        json={
            "mode": "ingestion",
            "message": "Pothole on Main Street",
            "session_id": session_id
        }
    )
    
    data1 = response1.json()
    print("First response:")
    print(json.dumps(data1, indent=2))
    
    # Check if clarification needed
    if data1['result'].get('needs_clarification'):
        print("\nAgent needs clarification, providing details...")
        
        response2 = requests.post(
            f"{api_url}orchestrate",
            json={
                "mode": "ingestion",
                "message": "Yes, it's at the intersection of Main Street and 5th Avenue",
                "session_id": session_id,
                "conversation_history": [
                    {"role": "user", "content": "Pothole on Main Street"},
                    {"role": "assistant", "content": data1['result']['agent_response']}
                ]
            }
        )
        
        data2 = response2.json()
        print("\nSecond response:")
        print(json.dumps(data2, indent=2))
        
        return data2
    
    return data1

def test_query():
    """Test query mode"""
    print("\n=== Test 3: Query mode ===")
    
    api_url = get_api_endpoint()
    response = requests.post(
        f"{api_url}orchestrate",
        json={
            "mode": "query",
            "message": "Show me all high-priority issues"
        }
    )
    
    data = response.json()
    print(json.dumps(data, indent=2))
    
    return data

def test_management():
    """Test management mode"""
    print("\n=== Test 4: Management mode ===")
    
    api_url = get_api_endpoint()
    
    # First get a report ID
    reports_response = requests.get(f"{api_url}reports")
    reports = reports_response.json()
    
    if not reports.get('reports'):
        print("No reports found. Run ingestion tests first.")
        return None
    
    report_id = reports['reports'][0]['report_id']
    print(f"Using report ID: {report_id}")
    
    response = requests.post(
        f"{api_url}orchestrate",
        json={
            "mode": "management",
            "message": "Assign this to Team B and make it due in 48 hours",
            "report_id": report_id
        }
    )
    
    data = response.json()
    print(json.dumps(data, indent=2))
    
    return data

def test_list_reports():
    """Test listing all reports"""
    print("\n=== Test 5: List all reports ===")
    
    api_url = get_api_endpoint()
    response = requests.get(f"{api_url}reports")
    
    data = response.json()
    print(f"Found {len(data.get('reports', []))} reports")
    print(json.dumps(data, indent=2))
    
    return data

def main():
    """Run all tests"""
    try:
        print("🚀 DomainFlow API Test Client")
        print("=" * 60)
        
        # Run tests
        test_ingestion_vague()
        test_ingestion_clarification()
        test_query()
        test_list_reports()
        test_management()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
