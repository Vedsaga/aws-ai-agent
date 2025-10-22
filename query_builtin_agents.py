#!/usr/bin/env python3
"""Query builtin agents from the database to verify seeding."""
import json
import boto3
import os
import sys

# Add psycopg to path
sys.path.insert(0, '/opt/python')

try:
    import psycopg
except ImportError:
    print("Installing psycopg...")
    os.system("pip install psycopg[binary] -q")
    import psycopg

def main():
    # Get database credentials
    cfn = boto3.client('cloudformation')
    response = cfn.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')
    outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
    
    secret_arn = outputs['DatabaseSecretArn']
    db_host = outputs['DatabaseEndpoint']
    
    secrets = boto3.client('secretsmanager')
    secret_response = secrets.get_secret_value(SecretId=secret_arn)
    creds = json.loads(secret_response['SecretString'])
    
    print(f"Connecting to {db_host}...")
    
    # Connect
    conn = psycopg.connect(
        host=db_host,
        port=5432,
        dbname='multi_agent_orchestration',
        user=creds['username'],
        password=creds['password'],
        connect_timeout=30
    )
    
    cursor = conn.cursor()
    
    # Query builtin agents
    print("\n=== Builtin Agents ===")
    cursor.execute("""
        SELECT agent_id, agent_name, agent_class, is_inbuilt, tenant_id
        FROM agent_definitions
        WHERE is_inbuilt = true
        ORDER BY agent_class, agent_name
    """)
    agents = cursor.fetchall()
    
    if agents:
        print(f"Found {len(agents)} builtin agents:")
        for agent in agents:
            print(f"  [{agent[2]}] {agent[1]} (ID: {agent[0]}, Tenant: {agent[4]})")
    else:
        print("No builtin agents found!")
    
    # Query domains
    print("\n=== Domains ===")
    cursor.execute("""
        SELECT domain_id, domain_name, description, tenant_id
        FROM domain_configurations
        ORDER BY domain_name
    """)
    domains = cursor.fetchall()
    
    if domains:
        print(f"Found {len(domains)} domains:")
        for domain in domains:
            print(f"  {domain[1]}: {domain[2]} (ID: {domain[0]}, Tenant: {domain[3]})")
    else:
        print("No domains found!")
    
    # Get system tenant ID
    print("\n=== System Tenant ===")
    cursor.execute("SELECT id, tenant_name FROM tenants WHERE tenant_name = 'system'")
    tenant = cursor.fetchone()
    if tenant:
        print(f"System tenant ID: {tenant[0]}")
        print(f"System tenant name: {tenant[1]}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Database verification complete!")
    return len(agents) > 0 and len(domains) > 0

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
