#!/usr/bin/env python3
"""
Check what data is in RDS tables
"""
import boto3
import json
import psycopg

# Get DB credentials
secrets = boto3.client('secretsmanager', region_name='us-east-1')
cf = boto3.client('cloudformation', region_name='us-east-1')

# Get secret ARN and endpoint from stack
stack = cf.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')['Stacks'][0]
secret_arn = None
db_host = None

for output in stack['Outputs']:
    if output['OutputKey'] == 'DatabaseSecretArn':
        secret_arn = output['OutputValue']
    elif output['OutputKey'] == 'DatabaseEndpoint':
        db_host = output['OutputValue']

if not secret_arn or not db_host:
    print("ERROR: Could not find database secret ARN or endpoint")
    print(f"Secret ARN: {secret_arn}")
    print(f"DB Host: {db_host}")
    exit(1)

print(f"Secret ARN: {secret_arn}")
print(f"DB Host: {db_host}")

# Get credentials
secret = json.loads(secrets.get_secret_value(SecretId=secret_arn)['SecretString'])

# Connect to database
conn = psycopg.connect(
    host=db_host,
    port=5432,
    dbname='multi_agent_orchestration',
    user=secret['username'],
    password=secret['password']
)

print("\n=== RDS Tables and Row Counts ===\n")

tables = [
    'tenants',
    'users', 
    'teams',
    'agent_definitions',
    'domain_configurations',
    'incidents',
    'image_evidence'
]

with conn.cursor() as cur:
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table:30} {count:>5} rows")
    
    # Show sample incidents
    print("\n=== Sample Incidents (if any) ===\n")
    cur.execute("SELECT incident_id, domain_id, raw_text, created_at FROM incidents LIMIT 5")
    incidents = cur.fetchall()
    
    if incidents:
        for inc in incidents:
            print(f"ID: {inc[0]}")
            print(f"Domain: {inc[1]}")
            print(f"Text: {inc[2][:100]}...")
            print(f"Created: {inc[3]}")
            print()
    else:
        print("No incidents found in RDS")
    
    # Show agent definitions
    print("\n=== Agent Definitions in RDS ===\n")
    cur.execute("SELECT agent_id, agent_name, agent_class FROM agent_definitions LIMIT 10")
    agents = cur.fetchall()
    
    if agents:
        for agent in agents:
            print(f"  {agent[0]:40} {agent[1]:30} [{agent[2]}]")
    else:
        print("No agents found in RDS")
    
    # Show domain configurations
    print("\n=== Domain Configurations in RDS ===\n")
    cur.execute("SELECT domain_id, domain_name FROM domain_configurations LIMIT 10")
    domains = cur.fetchall()
    
    if domains:
        for domain in domains:
            print(f"  {domain[0]:40} {domain[1]}")
    else:
        print("No domains found in RDS")

conn.close()

print("\n=== DynamoDB Tables (for comparison) ===\n")
print("Reports table: Stores incident reports (unstructured)")
print("QueryJobs table: Stores query execution results")
print("Sessions table: Stores chat sessions")
print("Messages table: Stores chat messages")
print("Configurations table: Stores agent/domain configs (legacy)")
