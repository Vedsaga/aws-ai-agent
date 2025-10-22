#!/usr/bin/env python3
"""
Seed script for builtin agents and sample domain (civic_complaints)
This script populates the RDS database with:
1. Builtin ingestion agents (geo, temporal, entity)
2. Builtin query agents (who, what, where, when, why, how)
3. Builtin management agents (task_assigner, status_updater, task_details_editor)
4. Sample domain configuration (civic_complaints)
"""

import json
import os
import sys
import boto3
import psycopg2
from psycopg2.extras import Json
import uuid
from datetime import datetime

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'domainflow')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)


def get_db_connection():
    """Get database connection using credentials from Secrets Manager"""
    try:
        # Get database credentials
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
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise


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
        print(f"✓ Created system tenant: {tenant_id}")
    else:
        tenant_id = tenant[0]
        print(f"✓ System tenant exists: {tenant_id}")
    
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
        print(f"✓ Created system user: {user_id}")
    else:
        user_id = user[0]
        print(f"✓ System user exists: {user_id}")
    
    return tenant_id, user_id


def seed_builtin_ingestion_agents(cursor, tenant_id, user_id):
    """Seed builtin ingestion agents"""
    print("\n=== Seeding Builtin Ingestion Agents ===")
    
    agents = [
        {
            "agent_id": "builtin-ingestion-geo",
            "agent_name": "Geo Locator",
            "agent_class": "ingestion",
            "system_prompt": "You are a geographic location extraction specialist. Analyze the input text and extract location information including addresses, landmarks, neighborhoods, and geographic references. Use Amazon Location Service for geocoding when specific addresses are mentioned. Output the location as text, coordinates (longitude, latitude), and confidence score (0-1).",
            "tools": ["location_service", "web_search"],
            "agent_dependencies": [],
            "output_schema": {
                "location_text": {"type": "string", "description": "Extracted location as text"},
                "geo_location": {
                    "type": "object",
                    "description": "GeoJSON Point geometry",
                    "properties": {
                        "type": {"type": "string", "enum": ["Point"]},
                        "coordinates": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}
                    }
                },
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
            "agent_dependencies": [],
            "output_schema": {
                "timestamp": {"type": "string", "description": "ISO 8601 timestamp"},
                "time_reference": {"type": "string", "description": "Original time reference from text"},
                "urgency": {"type": "string", "enum": ["immediate", "urgent", "moderate", "low"], "description": "Urgency level"}
            },
            "description": "Extracts temporal information and determines urgency"
        },
        {
            "agent_id": "builtin-ingestion-entity",
            "agent_name": "Entity Extractor",
            "agent_class": "ingestion",
            "system_prompt": "You are an entity extraction and categorization specialist. Analyze the input text and extract entities, sentiment, and key phrases using AWS Comprehend. Identify named entities (people, organizations, locations). Analyze sentiment (positive, negative, neutral, mixed). Extract key phrases that summarize main issues. Categorize the complaint type (infrastructure, safety, environment, service, other).",
            "tools": ["comprehend"],
            "agent_dependencies": [],
            "output_schema": {
                "entities": {"type": "array", "description": "Named entities extracted"},
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral", "mixed"], "description": "Overall sentiment"},
                "key_phrases": {"type": "array", "description": "Key phrases summarizing issues"},
                "complaint_type": {"type": "string", "description": "Category of complaint"}
            },
            "description": "Extracts entities, sentiment, and categorizes content"
        }
    ]
    
    for agent in agents:
        try:
            cursor.execute("""
                INSERT INTO agent_definitions (
                    agent_id, tenant_id, agent_name, agent_class, system_prompt,
                    tools, agent_dependencies, max_output_keys, output_schema,
                    description, enabled, is_inbuilt, version, created_at, updated_at, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (agent_id) DO UPDATE SET
                    agent_name = EXCLUDED.agent_name,
                    system_prompt = EXCLUDED.system_prompt,
                    tools = EXCLUDED.tools,
                    output_schema = EXCLUDED.output_schema,
                    updated_at = NOW()
            """, (
                agent["agent_id"],
                tenant_id,
                agent["agent_name"],
                agent["agent_class"],
                agent["system_prompt"],
                Json(agent["tools"]),
                Json(agent["agent_dependencies"]),
                5,
                Json(agent["output_schema"]),
                agent["description"],
                True,
                True,
                1,
                user_id
            ))
            print(f"✓ Seeded ingestion agent: {agent['agent_name']}")
        except Exception as e:
            print(f"✗ Failed to seed agent {agent['agent_name']}: {e}")


def seed_builtin_query_agents(cursor, tenant_id, user_id):
    """Seed builtin query agents"""
    print("\n=== Seeding Builtin Query Agents ===")
    
    agents = [
        {
            "agent_id": "builtin-query-who",
            "agent_name": "Who Agent",
            "agent_class": "query",
            "system_prompt": "You are a 'who' question specialist. Analyze entities and actors involved in incidents. Answer questions about who reported incidents, who was affected, and entity patterns. Use the Retrieval API to get entity information from reports. Provide clear answers with references to source data.",
            "tools": ["retrieval_api", "aggregation_api"],
            "agent_dependencies": [],
            "output_schema": {
                "entities": {"type": "array", "description": "Entities involved"},
                "reporters": {"type": "string", "description": "Who reported"},
                "affected": {"type": "string", "description": "Who was affected"},
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
            "agent_dependencies": [],
            "output_schema": {
                "incident_types": {"type": "array", "description": "Types of incidents"},
                "common_issues": {"type": "array", "description": "Common issues found"},
                "summary": {"type": "string", "description": "Summary of findings"},
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
            "agent_dependencies": [],
            "output_schema": {
                "locations": {"type": "array", "description": "Locations identified"},
                "hotspots": {"type": "array", "description": "Geographic hotspots"},
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
            "agent_dependencies": [],
            "output_schema": {
                "time_pattern": {"type": "string", "description": "Temporal pattern identified"},
                "frequency": {"type": "string", "description": "Frequency analysis"},
                "trend": {"type": "string", "description": "Trend description"},
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
            "agent_dependencies": [],
            "output_schema": {
                "causes": {"type": "array", "description": "Identified causes"},
                "factors": {"type": "array", "description": "Contributing factors"},
                "analysis": {"type": "string", "description": "Causal analysis"},
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
            "agent_dependencies": [],
            "output_schema": {
                "methods": {"type": "array", "description": "Methods identified"},
                "process": {"type": "string", "description": "Process description"},
                "insights": {"type": "string", "description": "Insights about mechanisms"},
                "answer": {"type": "string", "description": "Natural language answer"}
            },
            "description": "Answers 'how' questions about methods and processes"
        }
    ]
    
    for agent in agents:
        try:
            cursor.execute("""
                INSERT INTO agent_definitions (
                    agent_id, tenant_id, agent_name, agent_class, system_prompt,
                    tools, agent_dependencies, max_output_keys, output_schema,
                    description, enabled, is_inbuilt, version, created_at, updated_at, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (agent_id) DO UPDATE SET
                    agent_name = EXCLUDED.agent_name,
                    system_prompt = EXCLUDED.system_prompt,
                    tools = EXCLUDED.tools,
                    output_schema = EXCLUDED.output_schema,
                    updated_at = NOW()
            """, (
                agent["agent_id"],
                tenant_id,
                agent["agent_name"],
                agent["agent_class"],
                agent["system_prompt"],
                Json(agent["tools"]),
                Json(agent["agent_dependencies"]),
                5,
                Json(agent["output_schema"]),
                agent["description"],
                True,
                True,
                1,
                user_id
            ))
            print(f"✓ Seeded query agent: {agent['agent_name']}")
        except Exception as e:
            print(f"✗ Failed to seed agent {agent['agent_name']}: {e}")


def seed_builtin_management_agents(cursor, tenant_id, user_id):
    """Seed builtin management agents"""
    print("\n=== Seeding Builtin Management Agents ===")
    
    agents = [
        {
            "agent_id": "builtin-management-task-assigner",
            "agent_name": "Task Assigner",
            "agent_class": "management",
            "system_prompt": "You are a task assignment specialist. Analyze the user's command to assign tasks to teams or individuals. Extract the assignee information (team ID or user ID) and update the report's management_data with task assignment details. Include assignee_id, assigned_at timestamp, and assignment reason.",
            "tools": ["retrieval_api"],
            "agent_dependencies": [],
            "output_schema": {
                "assignee_id": {"type": "string", "description": "Team or user ID"},
                "assignee_type": {"type": "string", "enum": ["team", "user"], "description": "Type of assignee"},
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
            "agent_dependencies": [],
            "output_schema": {
                "status": {"type": "string", "enum": ["pending", "in_progress", "resolved", "closed"], "description": "New status"},
                "updated_at": {"type": "string", "description": "ISO 8601 timestamp"},
                "updated_by": {"type": "string", "description": "User ID who updated"},
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
            "agent_dependencies": [],
            "output_schema": {
                "field": {"type": "string", "description": "Field to update (priority, due_at, etc)"},
                "value": {"type": "string", "description": "New value"},
                "updated_at": {"type": "string", "description": "ISO 8601 timestamp"},
                "reason": {"type": "string", "description": "Reason for change"}
            },
            "description": "Edits task details like priority and due dates"
        }
    ]
    
    for agent in agents:
        try:
            cursor.execute("""
                INSERT INTO agent_definitions (
                    agent_id, tenant_id, agent_name, agent_class, system_prompt,
                    tools, agent_dependencies, max_output_keys, output_schema,
                    description, enabled, is_inbuilt, version, created_at, updated_at, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (agent_id) DO UPDATE SET
                    agent_name = EXCLUDED.agent_name,
                    system_prompt = EXCLUDED.system_prompt,
                    tools = EXCLUDED.tools,
                    output_schema = EXCLUDED.output_schema,
                    updated_at = NOW()
            """, (
                agent["agent_id"],
                tenant_id,
                agent["agent_name"],
                agent["agent_class"],
                agent["system_prompt"],
                Json(agent["tools"]),
                Json(agent["agent_dependencies"]),
                5,
                Json(agent["output_schema"]),
                agent["description"],
                True,
                True,
                1,
                user_id
            ))
            print(f"✓ Seeded management agent: {agent['agent_name']}")
        except Exception as e:
            print(f"✗ Failed to seed agent {agent['agent_name']}: {e}")


def seed_sample_domain(cursor, tenant_id, user_id):
    """Seed sample civic_complaints domain"""
    print("\n=== Seeding Sample Domain (civic_complaints) ===")
    
    domain = {
        "domain_id": "civic_complaints",
        "domain_name": "Civic Complaints",
        "description": "Citizen-reported infrastructure and service issues with location, time, and entity extraction",
        "ingestion_playbook": {
            "agent_execution_graph": {
                "nodes": [
                    "builtin-ingestion-geo",
                    "builtin-ingestion-temporal",
                    "builtin-ingestion-entity"
                ],
                "edges": []  # All agents run in parallel (no dependencies)
            }
        },
        "query_playbook": {
            "agent_execution_graph": {
                "nodes": [
                    "builtin-query-who",
                    "builtin-query-what",
                    "builtin-query-where",
                    "builtin-query-when",
                    "builtin-query-why",
                    "builtin-query-how"
                ],
                "edges": []  # All agents run in parallel
            }
        },
        "management_playbook": {
            "agent_execution_graph": {
                "nodes": [
                    "builtin-management-task-assigner",
                    "builtin-management-status-updater",
                    "builtin-management-task-details-editor"
                ],
                "edges": []  # All agents run in parallel
            }
        }
    }
    
    try:
        cursor.execute("""
            INSERT INTO domain_configurations (
                domain_id, tenant_id, domain_name, description,
                ingestion_playbook, query_playbook, management_playbook,
                created_at, updated_at, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            ON CONFLICT (domain_id) DO UPDATE SET
                domain_name = EXCLUDED.domain_name,
                description = EXCLUDED.description,
                ingestion_playbook = EXCLUDED.ingestion_playbook,
                query_playbook = EXCLUDED.query_playbook,
                management_playbook = EXCLUDED.management_playbook,
                updated_at = NOW()
        """, (
            domain["domain_id"],
            tenant_id,
            domain["domain_name"],
            domain["description"],
            Json(domain["ingestion_playbook"]),
            Json(domain["query_playbook"]),
            Json(domain["management_playbook"]),
            user_id
        ))
        print(f"✓ Seeded domain: {domain['domain_name']}")
    except Exception as e:
        print(f"✗ Failed to seed domain {domain['domain_name']}: {e}")


def verify_seeded_data(cursor):
    """Verify that builtin agents are marked correctly"""
    print("\n=== Verifying Seeded Data ===")
    
    # Count builtin agents by class
    cursor.execute("""
        SELECT agent_class, COUNT(*) 
        FROM agent_definitions 
        WHERE is_inbuilt = true 
        GROUP BY agent_class
    """)
    
    results = cursor.fetchall()
    for agent_class, count in results:
        print(f"✓ {agent_class} agents: {count}")
    
    # Verify domain exists
    cursor.execute("""
        SELECT domain_id, domain_name 
        FROM domain_configurations 
        WHERE domain_id = 'civic_complaints'
    """)
    
    domain = cursor.fetchone()
    if domain:
        print(f"✓ Domain exists: {domain[1]} ({domain[0]})")
    else:
        print("✗ Domain not found")
    
    # List all builtin agents
    cursor.execute("""
        SELECT agent_id, agent_name, agent_class, is_inbuilt
        FROM agent_definitions
        WHERE is_inbuilt = true
        ORDER BY agent_class, agent_name
    """)
    
    print("\n=== Builtin Agents ===")
    for row in cursor.fetchall():
        print(f"  {row[2]:12} | {row[1]:25} | {row[0]}")


def main():
    """Main function"""
    print("=" * 60)
    print("DomainFlow - Seed Builtin Data")
    print("=" * 60)
    
    # Check required environment variables
    if not DB_SECRET_ARN or not DB_HOST:
        print("✗ Error: DB_SECRET_ARN and DB_HOST environment variables required")
        sys.exit(1)
    
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure system tenant and user exist
        tenant_id, user_id = ensure_system_tenant_and_user(cursor)
        
        # Seed builtin agents
        seed_builtin_ingestion_agents(cursor, tenant_id, user_id)
        seed_builtin_query_agents(cursor, tenant_id, user_id)
        seed_builtin_management_agents(cursor, tenant_id, user_id)
        
        # Seed sample domain
        seed_sample_domain(cursor, tenant_id, user_id)
        
        # Verify seeded data
        verify_seeded_data(cursor)
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ Seed completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
