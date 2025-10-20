#!/usr/bin/env python3
"""
Quick diagnostic script to identify API issues
"""

import os
import json
import boto3
import requests
from datetime import datetime

def test_lambda_directly():
    """Test Lambda function directly"""
    print("=" * 80)
    print("Testing Lambda Function Directly")
    print("=" * 80)
    
    lambda_client = boto3.client('lambda')
    
    # Test payload
    test_event = {
        "httpMethod": "GET",
        "path": "/api/v1/config",
        "queryStringParameters": {"type": "agent"},
        "requestContext": {
            "authorizer": {
                "tenantId": "test-tenant",
                "userId": "test-user"
            }
        },
        "headers": {}
    }
    
    try:
        print(f"\nInvoking Lambda: MultiAgentOrchestration-dev-Api-ConfigHandler")
        print(f"Payload: {json.dumps(test_event, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName='MultiAgentOrchestration-dev-Api-ConfigHandler',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        print(f"\nLambda Response:")
        print(json.dumps(payload, indent=2))
        
        if 'errorMessage' in payload:
            print(f"\n❌ Lambda Error: {payload['errorMessage']}")
            if 'stackTrace' in payload:
                print("\nStack Trace:")
                for line in payload['stackTrace']:
                    print(f"  {line}")
        else:
            print(f"\n✅ Lambda executed successfully")
            print(f"Status Code: {payload.get('statusCode')}")
            
        return payload
        
    except Exception as e:
        print(f"\n❌ Failed to invoke Lambda: {e}")
        return None


def test_dynamodb_access():
    """Test DynamoDB table access"""
    print("\n" + "=" * 80)
    print("Testing DynamoDB Access")
    print("=" * 80)
    
    dynamodb = boto3.resource('dynamodb')
    table_name = 'MultiAgentOrchestration-dev-Data-Configurations'
    
    try:
        table = dynamodb.Table(table_name)
        print(f"\n✅ Table exists: {table_name}")
        print(f"Table status: {table.table_status}")
        print(f"Item count: {table.item_count}")
        
        # Try to scan
        response = table.scan(Limit=5)
        items = response.get('Items', [])
        print(f"Sample items: {len(items)}")
        
        if items:
            print("\nSample item:")
            print(json.dumps(items[0], indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"\n❌ DynamoDB error: {e}")
        return False


def test_api_gateway():
    """Test API Gateway endpoint"""
    print("\n" + "=" * 80)
    print("Testing API Gateway Endpoint")
    print("=" * 80)
    
    # Get API Gateway URL
    api_id = "vluqfpl2zi"
    region = os.getenv('AWS_REGION', 'us-east-1')
    api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod"
    
    print(f"\nAPI URL: {api_url}")
    
    # Test without auth (should get 401)
    print("\n1. Testing without authentication (expect 401)...")
    try:
        response = requests.get(f"{api_url}/api/v1/config?type=agent", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correct - API Gateway is working")
        else:
            print(f"   ⚠️  Unexpected status code")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test with JWT token if available
    jwt_token = os.getenv('JWT_TOKEN')
    if jwt_token:
        print("\n2. Testing with JWT token...")
        try:
            headers = {'Authorization': f'Bearer {jwt_token}'}
            response = requests.get(
                f"{api_url}/api/v1/config?type=agent",
                headers=headers,
                timeout=5
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ API is working correctly")
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:500]}")
            elif response.status_code == 500:
                print("   ❌ Internal Server Error")
                print(f"   Response: {response.text[:500]}")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    else:
        print("\n2. Skipping authenticated test (no JWT_TOKEN)")


def check_lambda_logs():
    """Check recent Lambda logs"""
    print("\n" + "=" * 80)
    print("Checking Lambda Logs")
    print("=" * 80)
    
    logs_client = boto3.client('logs')
    log_group = '/aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler'
    
    try:
        # Get recent log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        streams = response.get('logStreams', [])
        if not streams:
            print(f"\n⚠️  No log streams found")
            return
        
        print(f"\nFound {len(streams)} recent log streams")
        
        # Get events from most recent stream
        latest_stream = streams[0]['logStreamName']
        print(f"\nLatest stream: {latest_stream}")
        
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=latest_stream,
            limit=50
        )
        
        events = events_response.get('events', [])
        print(f"\nRecent log events ({len(events)}):")
        print("-" * 80)
        
        for event in events[-20:]:  # Last 20 events
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
        
    except Exception as e:
        print(f"\n❌ Failed to read logs: {e}")


def main():
    """Run all diagnostics"""
    print("\n🔍 API Diagnostic Tool")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    test_dynamodb_access()
    test_lambda_directly()
    test_api_gateway()
    check_lambda_logs()
    
    print("\n" + "=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
