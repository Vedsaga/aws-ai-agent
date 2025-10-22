#!/usr/bin/env python3
"""Check if builtin agents are seeded in the database"""
import json
import os
import sys

try:
    import boto3
    import psycopg2
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Installing dependencies...")
    os.system("pip3 install boto3 psycopg2-binary --quiet")
    import boto3
    import psycopg2

def main():
    try:
        # Get database credentials from CloudFormation
        cfn = boto3.client('cloudformation', region_name='us-east-1')
        response = cfn.describe_stacks(StackName='MultiAgentOrchestration-dev-Data')
        outputs = {o['OutputKey']: o['OutputValue'] for o in response['Stacks'][0]['Outputs']}
        
        secret_arn = outputs['DatabaseSecretArn']
        db_host = outputs['DatabaseEndpoint']
        
        # Get database password
        secrets = boto3.client('secretsmanager', region_name='us-east-1')
        secret_response = secrets.get_secret_value(SecretId=secret_arn)
        creds = json.loads(secret_response['SecretString'])
        
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database='multi_agent_orchestration',
            user=creds['username'],
            password=creds['password']
        )
        cursor = conn.cursor()
        
        # Check agents
        print("\n" + "="*80)
        print("BUILTIN AGENTS CHECK")
        print("="*80)
        
        cursor.execute("""
            SELECT agent_id, agent_name, agent_class, is_inbuilt, enabled
            FROM agent_definitions
            WHERE is_inbuilt = true
            ORDER BY agent_class, agent_id
        """)
        
        agents = cursor.fetchall()
        
        if not agents:
            print("\n❌ NO BUILTIN AGENTS FOUND - Database needs seeding!")
            return False
        
        print(f"\n✓ Found {len(agents)} builtin agents:\n")
        
        ingestion_count = 0
        query_count = 0
        management_count = 0
        
        for agent_id, agent_name, agent_class, is_inbuilt, enabled in agents:
            status = "✓" if enabled else "✗"
            print(f"  {status} [{agent_class:12}] {agent_id:40} - {agent_name}")
            
            if agent_class == 'ingestion':
                ingestion_count += 1
            elif agent_class == 'query':
                query_count += 1
            elif agent_class == 'management':
                management_count += 1
        
        print(f"\nSummary:")
        print(f"  - Ingestion agents: {ingestion_count}")
        print(f"  - Query agents: {query_count}")
        print(f"  - Management agents: {management_count}")
        
        # Check domains
        print("\n" + "="*80)
        print("DOMAINS CHECK")
        print("="*80)
        
        cursor.execute("""
            SELECT domain_id, domain_name, description
            FROM domain_configurations
        """)
        
        domains = cursor.fetchall()
        
        if not domains:
            print("\n❌ NO DOMAINS FOUND")
        else:
            print(f"\n✓ Found {len(domains)} domain(s):\n")
            for domain_id, domain_name, description in domains:
                print(f"  - {domain_id}: {domain_name}")
                print(f"    {description}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✓ Database is seeded and ready for E2E testing!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
