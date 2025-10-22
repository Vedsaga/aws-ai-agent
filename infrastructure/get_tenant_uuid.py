#!/usr/bin/env python3
"""Get the system tenant UUID from the database"""
import json
import boto3
import psycopg

# Get database credentials
cfn = boto3.client('cloudformation', region_name='us-east-1')
response = cfn.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')
outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}

secret_arn = outputs['DatabaseSecretArn']
endpoint = outputs['DatabaseEndpoint']

secrets = boto3.client('secretsmanager', region_name='us-east-1')
secret_response = secrets.get_secret_value(SecretId=secret_arn)
creds = json.loads(secret_response['SecretString'])

# Connect and query
conn = psycopg.connect(
    host=endpoint,
    port=5432,
    dbname='multi_agent_orchestration',
    user=creds['username'],
    password=creds['password']
)

cursor = conn.cursor()

# Get system tenant
cursor.execute("SELECT id, tenant_name FROM tenants WHERE tenant_name = 'system'")
tenant = cursor.fetchone()

if tenant:
    print(f"System Tenant UUID: {tenant[0]}")
    print(f"Tenant Name: {tenant[1]}")
else:
    print("No system tenant found!")

cursor.close()
conn.close()
