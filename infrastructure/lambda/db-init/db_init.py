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


def ensure_system_tenant_and_user(cursor):
    """Ensure system tenant and user exist for builtin agents"""
    # Check if system tenant exists
    cursor.execute("SELECT id FROM tenants WHERE tenant_name = 'system'")
    tenant = cursor.fetchone()
    
    if not tenant:
        cursor.execute("""
            INSERT INTO tenants (tenant_name, created_at, updated_at)
            VALUES ('system', NOW(), NOW())
            RETURNING id
        """)
        tenant_id = cursor.fetchone()[0]
        logger.info(f"Created system tenant: {tenant_id}")
    else:
        tenant_id = tenant[0]
        logger.info(f"System tenant exists: {tenant_id}")
    
    # Check if system user exists
    cursor.execute("SELECT id FROM users WHERE username = 'system'")
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("""
            INSERT INTO users (username, email, cognito_sub, tenant_id, created_at, updated_at)
            VALUES ('system', 'system@domainflow.ai', 'system-builtin', %s, NOW(), NOW())
            RETURNING id
        """, (tenant_id,))
        user_id = cursor.fetchone()[0]
        logger.info(f"Created system user: {user_id}")
    else:
        user_id = user[0]
        logger.info(f"System user exists: {user_id}")
    
    return tenant_id, user_id


def seed_builtin_data(cursor, tenant_id=None, user_id=None):
    """Seed builtin agents and sample domain"""
    from psycopg2.extras import Json
    
    # Ensure system tenant and user exist
    if not tenant_id or not user_id:
        tenant_id, user_id = ensure_system_tenant_and_user(cursor)
    
    logger.info("Seeding builtin agents...")
    
    # Builtin ingestion agents
    ingestion_agents = [
        {
            "agent_id": "builtin-ingestion-geo",
            "agent_name": "Geo Locator",
            "agent_class": "ingestion",
            "system_prompt": "You are a geographic location extraction specialist. Analyze the input text and extract location information including addresses, landmarks, neighborhoods, and geographic references. Use Amazon Location Service for geocoding when specific addresses are mentioned. Output the location as text, coordinates (longitude, latitude), and confidence score (0-1).",
            "tools": ["location_service", "web_search"],
            "output_schema": {
                "location_text": {"type": "string", "description": "Extracted location as text"},
                "geo_location": {"type": "object", "description": "GeoJSON Point geometry"},
                "address": {"type": "string", "description": "Formatted address"},
                "confidence": {"type": "number", "description": "Confidence score 0-1"}
            },
            "description": "Extracts geographic location from unstructured text"
        },
        {
            "agent_id": "builtin-ingestion-temporal",
            "agent_name": "Temporal Analyzer",
            "agent_class": "ingestion",
            "system_prompt": "You are a temporal information extraction specialist. Analyze the input text and extract time and date information. Parse relative time expressions like 'today', 'yesterday', 'last week', 'this morning'. Convert all times to ISO 8601 format timestamps. Determine urgency based on how recent the incident is (immediate, urgent, moderate, low).",
            "tools": [],
            "output_schema": {
                "timestamp": {"type": "string", "description": "ISO 8601 timestamp"},
                "time_reference": {"type": "string", "description": "Original time reference from text"},
                "urgency": {"type": "string", "description": "Urgency level"}
            },
            "description": "Extracts temporal information and determines urgency"
        },
        {
            "agent_id": "builtin-ingestion-entity",
            "agent_name": "Entity Extractor",
            "agent_class": "ingestion",
            "system_prompt": "You are an entity extraction and categorization specialist. Analyze the input text and extract entities, sentiment, and key phrases using AWS Comprehend. Identify named entities (people, organizations, locations). Analyze sentiment (positive, negative, neutral, mixed). Extract key phrases that summarize main issues. Categorize the complaint type (infrastructure, safety, environment, service, other).",
            "tools": ["comprehend"],
            "output_schema": {
                "entities": {"type": "array", "description": "Named entities extracted"},
                "sentiment": {"type": "string", "description": "Overall sentiment"},
                "key_phrases": {"type": "array", "description": "Key phrases summarizing issues"},
                "complaint_type": {"type": "string", "description": "Category of complaint"}
            },
            "description": "Extracts entities, sentiment, and categorizes content"
        }
    ]
    
    # Builtin query agents
    query_agents = [
        {
            "agent_id": "builtin-query-who",
            "agent_name": "Who Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'who' question specialist. Analyze entities and actors involved in incidents. Answer questions about who reported incidents, who was affected, and entity patterns. Use the Retrieval API to get entity information from reports. Provide clear answers with references to source data.",
            "tools": ["retrieval_api", "aggregation_api"],
            "output_schema": {
                "entities": {"type": "array", "description": "Entities involved"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'who' questions about entities and actors"
        },
        {
            "agent_id": "builtin-query-what",
            "agent_name": "What Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'what' question specialist. Analyze what types of incidents occurred. Answer questions about incident categories, common issues, entity types, and content patterns. Use the Retrieval API to get incident details and Aggregation API for statistics.",
            "tools": ["retrieval_api", "aggregation_api"],
            "output_schema": {
                "incident_types": {"type": "array", "description": "Types of incidents"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'what' questions about incident types and content"
        },
        {
            "agent_id": "builtin-query-where",
            "agent_name": "Where Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'where' question specialist. Analyze spatial patterns in the data. Answer questions about where incidents occurred, geographic clusters, hotspots, and spatial distributions. Use the Spatial Query API for geospatial analysis and generate map data for visualization.",
            "tools": ["spatial_api", "retrieval_api"],
            "output_schema": {
                "locations": {"type": "array", "description": "Locations identified"},
                "map_data": {"type": "object", "description": "GeoJSON for map display"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'where' questions about locations and spatial patterns"
        },
        {
            "agent_id": "builtin-query-when",
            "agent_name": "When Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'when' question specialist. Analyze temporal patterns in the data. Answer questions about when incidents occurred, time trends, frequency over time periods, and temporal correlations. Use the Analytics API to retrieve time-series data.",
            "tools": ["analytics_api", "retrieval_api"],
            "output_schema": {
                "time_pattern": {"type": "string", "description": "Temporal pattern identified"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'when' questions about temporal patterns"
        },
        {
            "agent_id": "builtin-query-why",
            "agent_name": "Why Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'why' question specialist. Analyze causal relationships and reasons behind incidents. Answer questions about why incidents occurred, root causes, contributing factors, and correlations. Use the Analytics API for pattern detection and correlation analysis.",
            "tools": ["analytics_api", "retrieval_api"],
            "output_schema": {
                "causes": {"type": "array", "description": "Identified causes"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'why' questions about causes and reasons"
        },
        {
            "agent_id": "builtin-query-how",
            "agent_name": "How Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'how' question specialist. Analyze methods, processes, and mechanisms. Answer questions about how incidents occurred, how they were resolved, and how patterns emerged. Use the Retrieval API for incident details and process analysis.",
            "tools": ["retrieval_api", "analytics_api"],
            "output_schema": {
                "methods": {"type": "array", "description": "Methods identified"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'how' questions about methods and processes"
        }
    ]
    
    # Builtin management agents
    management_agents = [
        {
            "agent_id": "builtin-management-task-assigner",
            "agent_name": "Task Assigner",
            "agent_class": "management",
            "system_prompt": "You are a task assignment specialist. Analyze the user's command to assign tasks to teams or individuals. Extract the assignee information (team ID or user ID) and update the report's management_data with task assignment details. Include assignee_id, assigned_at timestamp, and assignment reason.",
            "tools": ["retrieval_api"],
            "output_schema": {
                "assignee_id": {"type": "string", "description": "Team or user ID"},
                "assigned_at": {"type": "string", "description": "ISO 8601 timestamp"},
                "reason": {"type": "string", "description": "Reason for assignment"}
            },
            "description": "Assigns tasks to teams or users based on commands"
        },
        {
            "agent_id": "builtin-management-status-updater",
            "agent_name": "Status Updater",
            "agent_class": "management",
            "system_prompt": "You are a status update specialist. Analyze the user's command to update report status. Extract the new status (pending, in_progress, resolved, closed) and update the report's management_data. Add a history entry with status, timestamp, and user who made the change.",
            "tools": ["retrieval_api"],
            "output_schema": {
                "status": {"type": "string", "description": "New status"},
                "updated_at": {"type": "string", "description": "ISO 8601 timestamp"},
                "notes": {"type": "string", "description": "Update notes"}
            },
            "description": "Updates report status based on commands"
        },
        {
            "agent_id": "builtin-management-task-details-editor",
            "agent_name": "Task Details Editor",
            "agent_class": "management",
            "system_prompt": "You are a task details editor. Analyze the user's command to update task details like priority, due date, or other metadata. Extract the field to update and the new value. Update the report's management_data.task_details with the changes.",
            "tools": ["retrieval_api"],
            "output_schema": {
                "field": {"type": "string", "description": "Field to update"},
                "value": {"type": "string", "description": "New value"},
                "updated_at": {"type": "string", "description": "ISO 8601 timestamp"}
            },
            "description": "Edits task details like priority and due dates"
        }
    ]
    
    # Insert all agents
    all_agents = ingestion_agents + query_agents + management_agents
    for agent in all_agents:
        try:
            cursor.execute("""
                INSERT INTO agent_definitions (
                    agent_id, tenant_id, agent_name, agent_class, system_prompt,
                    tools, agent_dependencies, max_output_keys, output_schema,
                    description, enabled, is_inbuilt, version, created_at, updated_at, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (agent_id) DO NOTHING
            """, (
                agent["agent_id"],
                tenant_id,
                agent["agent_name"],
                agent["agent_class"],
                agent["system_prompt"],
                Json(agent["tools"]),
                Json([]),
                5,
                Json(agent["output_schema"]),
                agent["description"],
                True,
                True,
                1,
                user_id
            ))
            logger.info(f"Seeded agent: {agent['agent_name']}")
        except Exception as e:
            logger.warning(f"Failed to seed agent {agent['agent_name']}: {e}")
    
    # Seed sample domain
    try:
        cursor.execute("""
            INSERT INTO domain_configurations (
                domain_id, tenant_id, domain_name, description,
                ingestion_playbook, query_playbook, management_playbook,
                created_at, updated_at, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            ON CONFLICT (domain_id) DO NOTHING
        """, (
            "civic_complaints",
            tenant_id,
            "Civic Complaints",
            "Citizen-reported infrastructure and service issues",
            Json({
                "agent_execution_graph": {
                    "nodes": ["builtin-ingestion-geo", "builtin-ingestion-temporal", "builtin-ingestion-entity"],
                    "edges": []
                }
            }),
            Json({
                "agent_execution_graph": {
                    "nodes": ["builtin-query-who", "builtin-query-what", "builtin-query-where", "builtin-query-when", "builtin-query-why", "builtin-query-how"],
                    "edges": []
                }
            }),
            Json({
                "agent_execution_graph": {
                    "nodes": ["builtin-management-task-assigner", "builtin-management-status-updater", "builtin-management-task-details-editor"],
                    "edges": []
                }
            }),
            user_id
        ))
        logger.info("Seeded domain: civic_complaints")
    except Exception as e:
        logger.warning(f"Failed to seed domain: {e}")


def handler(event, context):
    """
    Initialize database schema with tables and indexes.
    This function is idempotent and can be run multiple times.
    
    Event parameters:
    - seed_builtin_data: bool - If True, loads builtin agents and sample domain
    """
    try:
        # Parse event parameters
        seed_data = event.get('seed_builtin_data', False)
        logger.info(f"Database initialization started. Seed data: {seed_data}")
        
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
        
        # Legacy incidents and image_evidence tables removed
        # All reports are now stored in DynamoDB for better scalability
        logger.info("Skipping legacy incidents table creation - using DynamoDB for reports")
        
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
            'domain_configurations'
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
        
        # Seed builtin data if requested
        data_seeded = False
        if seed_data:
            try:
                logger.info("Starting builtin data seeding...")
                seed_builtin_data(cursor, tenant_id=None, user_id=None)
                data_seeded = True
                logger.info("Builtin data seeded successfully")
            except Exception as e:
                logger.error(f"Failed to seed builtin data: {str(e)}")
                # Don't fail the entire initialization if seeding fails
                data_seeded = False
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database initialized successfully',
                'schema_created': True,
                'data_seeded': data_seeded
            })
        }
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'schema_created': False,
                'data_seeded': False
            })
        }
