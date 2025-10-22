#!/usr/bin/env python3
"""
Invoke the db-init Lambda to add test user
"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Payload to add test user
payload = {
    "action": "add_test_user",
    "user_data": {
        "cognito_sub": "d4188428-4071-704d-015a-189f11510585",
        "username": "testuser",
        "email": "test@example.com",
        "tenant_name": "test-tenant"
    }
}

# Invoke the Lambda
response = lambda_client.invoke(
    FunctionName='MultiAgentOrchestration-dev-Data-DBInit',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
