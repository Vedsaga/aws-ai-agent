#!/usr/bin/env python3
"""
Verify database initialization by querying agents and domains tables.
"""
import json
import boto3
import os

def get_db_credentials():
    """Get database credentials from Secrets Manager."""
    secret_arn = os.environ.get('DB_SECRET_ARN')
    if not secret_arn:
        # Get from CloudFormation outputs
        cfn = boto3.client('cloudformation')
        response = cfn.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')
        outputs = response['Stacks'][0]['Outputs']
        for output in outputs:
            if output['OutputKey'] == 'DatabaseSecretArn':
                secret_arn = output['OutputValue']
                break
    
    secrets = boto3.client('secretsmanager')
    response = secrets.get_secret_value(SecretId=secret_arn)
    return json.loads(response['SecretString'])

def get_db_endpoint():
    """Get database endpoint from CloudFormation outputs."""
    cfn = boto3.client('cloudformation')
    response = cfn.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')
    outputs = response['Stacks'][0]['Outputs']
    for output in outputs:
        if output['OutputKey'] == 'DatabaseEndpoint':
            return output['OutputValue']
    return None

def query_database():
    """Query database to verify data."""
    import psycopg
    
    # Get credentials and endpoint
    creds = get_db_credentials()
    endpoint = get_db_endpoint()
    
    print(f"Connecting to database at {endpoint}...")
    
    # Connect to database
    conn = psycopg.connect(
        host=endpoint,
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
        SELECT agent_id, name, agent_type, is_builtin 
        FROM agent_definitions 
        WHERE is_builtin = true
        ORDER BY name
    """)
    agents = cursor.fetchall()
    print(f"Found {len(agents)} builtin agents:")
    for agent in agents:
        print(f"  - {agent[1]} ({agent[2]})")
    
    # Query domains
    print("\n=== Domains ===")
    cursor.execute("""
        SELECT domain_id, name, description 
        FROM domain_configurations
        ORDER BY name
    """)
    domains = cursor.fetchall()
    print(f"Found {len(domains)} domains:")
    for domain in domains:
        print(f"  - {domain[1]}: {domain[2]}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Database verification complete!")
    print(f"  - {len(agents)} builtin agents loaded")
    print(f"  - {len(domains)} sample domains loaded")
    
    return len(agents) > 0 and len(domains) > 0

if __name__ == '__main__':
    try:
        success = query_database()
        exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
