import json
import os
import boto3
import psycopg2
from psycopg2 import sql
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_SECRET_ARN = os.environ['DB_SECRET_ARN']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']
DB_NAME = os.environ['DB_NAME']

secrets_client = boto3.client('secretsmanager')


def handler(event, context):
    """
    Initialize database schema with tables and indexes.
    This function is idempotent and can be run multiple times.
    """
    try:
        # Get database credentials from Secrets Manager
        secret_response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
        secret = json.loads(secret_response['SecretString'])
        
        db_username = secret['username']
        db_password = secret['password']
        
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=db_username,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info("Connected to database successfully")
        
        # Enable PostGIS extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        logger.info("PostGIS extension enabled")
        
        # Create tenants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_name VARCHAR(200) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        logger.info("Tenants table created")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                cognito_sub VARCHAR(255) UNIQUE NOT NULL,
                tenant_id UUID NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
        """)
        logger.info("Users table created")
        
        # Create teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                team_name VARCHAR(200) NOT NULL,
                tenant_id UUID NOT NULL,
                members JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
        """)
        logger.info("Teams table created")
        
        # Create agent_definitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_definitions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(100) UNIQUE NOT NULL,
                tenant_id UUID NOT NULL,
                agent_name VARCHAR(200) NOT NULL,
                agent_class VARCHAR(20) NOT NULL CHECK (agent_class IN ('ingestion', 'query', 'management')),
                system_prompt TEXT NOT NULL,
                tools JSONB DEFAULT '[]',
                agent_dependencies JSONB DEFAULT '[]',
                max_output_keys INTEGER DEFAULT 5,
                output_schema JSONB NOT NULL,
                description TEXT,
                enabled BOOLEAN DEFAULT true,
                is_inbuilt BOOLEAN DEFAULT false,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
        """)
        logger.info("Agent definitions table created")
        
        # Create indexes on agent_definitions table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_tenant_class 
            ON agent_definitions(tenant_id, agent_class);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_enabled 
            ON agent_definitions(enabled);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_tenant 
            ON agent_definitions(tenant_id);
        """)
        
        logger.info("Agent definitions table indexes created")
        
        # Create domain_configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_configurations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                domain_id VARCHAR(100) UNIQUE NOT NULL,
                tenant_id UUID NOT NULL,
                domain_name VARCHAR(200) NOT NULL,
                description TEXT,
                ingestion_playbook JSONB NOT NULL,
                query_playbook JSONB NOT NULL,
                management_playbook JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            );
        """)
        logger.info("Domain configurations table created")
        
        # Create indexes on domain_configurations table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_domains_tenant 
            ON domain_configurations(tenant_id);
        """)
        
        logger.info("Domain configurations table indexes created")
        
        # Create incidents table with partitioning support (legacy - keeping for backward compatibility)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                domain_id VARCHAR(100) NOT NULL,
                raw_text TEXT NOT NULL,
                structured_data JSONB NOT NULL,
                location GEOGRAPHY(POINT, 4326),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
        """)
        logger.info("Incidents table created")
        
        # Create indexes on incidents table
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_tenant_domain 
            ON incidents(tenant_id, domain_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_created_at 
            ON incidents(created_at DESC);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_structured_data 
            ON incidents USING GIN(structured_data);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_incidents_location 
            ON incidents USING GIST(location);
        """)
        
        logger.info("Incidents table indexes created")
        
        # Create image_evidence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_evidence (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
                tenant_id UUID NOT NULL,
                s3_key VARCHAR(500) NOT NULL,
                s3_bucket VARCHAR(200) NOT NULL,
                content_type VARCHAR(100),
                file_size_bytes INTEGER,
                uploaded_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
        """)
        logger.info("Image evidence table created")
        
        # Create index on image_evidence
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_evidence_incident 
            ON image_evidence(incident_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_image_evidence_tenant 
            ON image_evidence(tenant_id);
        """)
        
        logger.info("Image evidence table indexes created")
        
        # Create updated_at trigger function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        logger.info("Updated_at trigger function created")
        
        # Create triggers for all tables with updated_at column
        tables_with_updated_at = [
            'tenants',
            'users',
            'teams',
            'agent_definitions',
            'domain_configurations',
            'incidents'
        ]
        
        for table_name in tables_with_updated_at:
            cursor.execute(f"""
                DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name};
                CREATE TRIGGER update_{table_name}_updated_at
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """)
            logger.info(f"Updated_at trigger created for {table_name} table")
        
        logger.info("Database schema initialization completed successfully")
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database schema initialized successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
