"""
Lambda function to verify database seeding by querying builtin agents and domains.
"""
import json
import os
import boto3
import psycopg2
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_SECRET_ARN = os.environ['DB_SECRET_ARN']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']

secrets_client = boto3.client('secretsmanager')

def handler(event, context):
    """Query and return builtin agents and domains from database."""
    try:
        # Get database credentials
        secret_response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
        secret = json.loads(secret_response['SecretString'])
        
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=secret['username'],
            password=secret['password']
        )
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Query builtin agents
        cursor.execute("""
            SELECT agent_id, agent_name, agent_class, tenant_id
            FROM agent_definitions
            WHERE is_inbuilt = true
            ORDER BY agent_class, agent_name
        """)
        agents = cursor.fetchall()
        
        agents_list = [
            {
                'agent_id': row[0],
                'agent_name': row[1],
                'agent_class': row[2],
                'tenant_id': str(row[3])
            }
            for row in agents
        ]
        
        logger.info(f"Found {len(agents_list)} builtin agents")
        
        # Query domains
        cursor.execute("""
            SELECT domain_id, domain_name, description, tenant_id
            FROM domain_configurations
            ORDER BY domain_name
        """)
        domains = cursor.fetchall()
        
        domains_list = [
            {
                'domain_id': row[0],
                'domain_name': row[1],
                'description': row[2],
                'tenant_id': str(row[3])
            }
            for row in domains
        ]
        
        logger.info(f"Found {len(domains_list)} domains")
        
        # Get system tenant
        cursor.execute("SELECT id, tenant_name FROM tenants WHERE tenant_name = 'system'")
        tenant = cursor.fetchone()
        system_tenant = {
            'id': str(tenant[0]),
            'name': tenant[1]
        } if tenant else None
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database verification successful',
                'system_tenant': system_tenant,
                'builtin_agents_count': len(agents_list),
                'builtin_agents': agents_list,
                'domains_count': len(domains_list),
                'domains': domains_list
            })
        }
        
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
