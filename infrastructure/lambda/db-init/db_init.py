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
        
        # Create incidents table with partitioning support
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
                created_by UUID NOT NULL
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
                uploaded_at TIMESTAMP DEFAULT NOW()
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
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_incidents_updated_at ON incidents;
            CREATE TRIGGER update_incidents_updated_at
            BEFORE UPDATE ON incidents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
        
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
