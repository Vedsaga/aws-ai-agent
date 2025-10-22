"""
RDS Utility Module for Orchestration

Provides database connection pooling and query functions for accessing
agent_definitions and domain_configurations tables in RDS PostgreSQL.

Requirements: 8.1, 8.4
"""

import json
import os
import boto3
import psycopg
from psycopg.rows import dict_row
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_SECRET_ARN = os.environ.get('DB_SECRET_ARN')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'domainflow')

secrets_client = boto3.client('secretsmanager')

# Database connection pool (reuse across invocations)
_db_connection = None


def get_db_connection():
    """
    Get or create database connection with connection pooling.
    Reuses connection across Lambda invocations for better performance.
    
    Returns:
        psycopg.Connection: Database connection with dict_row factory
    """
    global _db_connection
    
    if _db_connection is None or _db_connection.closed:
        # Get database credentials from Secrets Manager
        secret_response = secrets_client.get_secret_value(SecretId=DB_SECRET_ARN)
        secret = json.loads(secret_response['SecretString'])
        
        db_username = secret['username']
        db_password = secret['password']
        
        # Connect to database using psycopg3
        _db_connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=db_username,
            password=db_password,
            row_factory=dict_row,
            autocommit=True  # Auto-commit for read operations
        )
        logger.info("RDS connection established")
    
    return _db_connection


def get_agent_by_id(tenant_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get agent configuration from RDS by agent_id.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
    
    Returns:
        Agent configuration dictionary or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT agent_id, agent_name, agent_class, system_prompt, tools,
                   agent_dependencies, max_output_keys, output_schema,
                   description, enabled, is_inbuilt, version
            FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = %s AND enabled = true;
        """
        
        cursor.execute(query, (tenant_id, agent_id))
        agent = cursor.fetchone()
        
        if agent:
            logger.info(f"Loaded agent {agent_id}: {agent['agent_name']}")
            return dict(agent)
        else:
            logger.warning(f"Agent not found: {agent_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading agent {agent_id}: {str(e)}")
        return None


def get_all_agents(tenant_id: str, agent_class: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all agents for a tenant, optionally filtered by agent_class.
    
    Args:
        tenant_id: Tenant identifier
        agent_class: Optional filter ('ingestion', 'query', 'management')
    
    Returns:
        List of agent configuration dictionaries
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if agent_class:
            query = """
                SELECT agent_id, agent_name, agent_class, system_prompt, tools,
                       agent_dependencies, max_output_keys, output_schema,
                       description, enabled, is_inbuilt, version
                FROM agent_definitions
                WHERE tenant_id = %s AND agent_class = %s AND enabled = true
                ORDER BY agent_name;
            """
            cursor.execute(query, (tenant_id, agent_class))
        else:
            query = """
                SELECT agent_id, agent_name, agent_class, system_prompt, tools,
                       agent_dependencies, max_output_keys, output_schema,
                       description, enabled, is_inbuilt, version
                FROM agent_definitions
                WHERE tenant_id = %s AND enabled = true
                ORDER BY agent_name;
            """
            cursor.execute(query, (tenant_id,))
        
        agents = cursor.fetchall()
        logger.info(f"Loaded {len(agents)} agents for tenant {tenant_id}")
        
        return [dict(agent) for agent in agents]
        
    except Exception as e:
        logger.error(f"Error loading agents: {str(e)}")
        return []


def get_domain_by_id(tenant_id: str, domain_id: str) -> Optional[Dict[str, Any]]:
    """
    Get domain configuration from RDS by domain_id.
    Checks both tenant-specific and system domains.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Domain identifier
    
    Returns:
        Domain configuration dictionary with all three playbooks or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT domain_id, domain_name, description,
                   ingestion_playbook, query_playbook, management_playbook,
                   created_at, updated_at, tenant_id
            FROM domain_configurations
            WHERE tenant_id = %s AND domain_id = %s;
        """
        
        # Try tenant-specific domain first
        cursor.execute(query, (tenant_id, domain_id))
        domain = cursor.fetchone()
        
        # If not found, try system tenant for builtin domains
        if not domain:
            logger.info(f"Domain not found for tenant {tenant_id}, checking system tenant")
            cursor.execute(query, ('system', domain_id))
            domain = cursor.fetchone()
        
        if domain:
            logger.info(f"Loaded domain {domain_id}: {domain['domain_name']} (tenant: {domain['tenant_id']})")
            return dict(domain)
        else:
            logger.warning(f"Domain not found in any tenant: {domain_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading domain {domain_id}: {str(e)}")
        return None


def get_playbook(tenant_id: str, domain_id: str, playbook_type: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific playbook from domain configuration.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        playbook_type: Type of playbook ('ingestion', 'query', 'management')
    
    Returns:
        Playbook configuration with agent_execution_graph or None if not found
    """
    try:
        domain = get_domain_by_id(tenant_id, domain_id)
        
        if not domain:
            return None
        
        # Map playbook_type to column name
        playbook_column_map = {
            'ingestion': 'ingestion_playbook',
            'query': 'query_playbook',
            'management': 'management_playbook'
        }
        
        playbook_column = playbook_column_map.get(playbook_type)
        
        if not playbook_column:
            logger.error(f"Invalid playbook_type: {playbook_type}")
            return None
        
        playbook = domain.get(playbook_column)
        
        if playbook:
            logger.info(f"Loaded {playbook_type} playbook for domain {domain_id}")
            return playbook
        else:
            logger.warning(f"Playbook not found: {playbook_type} for domain {domain_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading playbook: {str(e)}")
        return None


def get_agents_by_ids(tenant_id: str, agent_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get multiple agents by their IDs in a single query.
    Checks both tenant-specific and system (builtin) agents.
    
    Args:
        tenant_id: Tenant identifier
        agent_ids: List of agent identifiers
    
    Returns:
        Dictionary mapping agent_id to agent configuration
    """
    try:
        if not agent_ids:
            return {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First try tenant-specific agents
        query = """
            SELECT agent_id, agent_name, agent_class, system_prompt, tools,
                   agent_dependencies, max_output_keys, output_schema,
                   description, enabled, is_inbuilt, version, tenant_id
            FROM agent_definitions
            WHERE tenant_id = %s AND agent_id = ANY(%s) AND enabled = true;
        """
        
        cursor.execute(query, (tenant_id, agent_ids))
        agents = cursor.fetchall()
        
        # Convert to dictionary
        agents_dict = {agent['agent_id']: dict(agent) for agent in agents}
        
        # Check for missing agents and try system tenant for builtin agents
        missing = set(agent_ids) - set(agents_dict.keys())
        if missing:
            logger.info(f"Checking system tenant for {len(missing)} missing agents")
            
            # Try system tenant for builtin agents
            cursor.execute(query, ('system', list(missing)))
            system_agents = cursor.fetchall()
            
            for agent in system_agents:
                agents_dict[agent['agent_id']] = dict(agent)
            
            # Update missing list
            missing = set(agent_ids) - set(agents_dict.keys())
        
        logger.info(f"Loaded {len(agents_dict)} agents from {len(agent_ids)} requested")
        
        # Log any still missing agents
        if missing:
            logger.warning(f"Agents not found in any tenant: {missing}")
        
        return agents_dict
        
    except Exception as e:
        logger.error(f"Error loading agents by IDs: {str(e)}")
        return {}


def close_connection():
    """
    Close the database connection.
    Should be called at the end of Lambda execution if needed.
    """
    global _db_connection
    
    if _db_connection and not _db_connection.closed:
        _db_connection.close()
        _db_connection = None
        logger.info("RDS connection closed")


def get_incidents_for_query(
    tenant_id: str,
    domain_id: str,
    limit: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get incidents for query agents to analyze.
    Retrieves recent incidents from the domain with optional date filtering.
    
    Args:
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        limit: Maximum number of incidents to return (default: 20)
        date_from: Optional start date filter (ISO format)
        date_to: Optional end date filter (ISO format)
    
    Returns:
        List of incident dictionaries with id, raw_text, structured_data, created_at
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with optional date filters
        query = """
            SELECT id, incident_id, raw_text, structured_data, 
                   created_at, updated_at, created_by
            FROM incidents
            WHERE tenant_id = %s AND domain_id = %s
        """
        params = [tenant_id, domain_id]
        
        if date_from:
            query += " AND created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND created_at <= %s"
            params.append(date_to)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        incidents = cursor.fetchall()
        
        logger.info(f"Retrieved {len(incidents)} incidents for query analysis")
        
        return [dict(incident) for incident in incidents]
        
    except Exception as e:
        logger.error(f"Error retrieving incidents: {str(e)}")
        return []


def extract_incident_ids(incidents: List[Dict[str, Any]]) -> List[str]:
    """
    Extract incident IDs from incident list for references.
    
    Args:
        incidents: List of incident dictionaries
    
    Returns:
        List of incident IDs
    """
    return [str(incident.get('incident_id') or incident.get('id')) for incident in incidents]
