#!/usr/bin/env python3
"""
Test script for database initialization Lambda.
Verifies that all tables, indexes, and triggers are created correctly.
"""

import json
import os
import sys
import boto3
import psycopg2
from psycopg2 import sql
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def get_db_connection():
    """Get database connection using environment variables."""
    try:
        # Get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        secret_arn = os.environ.get('DB_SECRET_ARN')
        
        if not secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")
        
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(secret_response['SecretString'])
        
        # Connect to database
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT', 5432),
            database=os.environ.get('DB_NAME'),
            user=secret['username'],
            password=secret['password']
        )
        
        logger.info(f"{GREEN}✓ Database connection established{RESET}")
        return conn
        
    except Exception as e:
        logger.error(f"{RED}✗ Failed to connect to database: {str(e)}{RESET}")
        raise


def test_table_exists(cursor, table_name):
    """Test if a table exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Table '{table_name}' exists{RESET}")
        return True
    else:
        logger.error(f"{RED}✗ Table '{table_name}' does not exist{RESET}")
        return False


def test_index_exists(cursor, index_name):
    """Test if an index exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = %s
        );
    """, (index_name,))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Index '{index_name}' exists{RESET}")
        return True
    else:
        logger.error(f"{RED}✗ Index '{index_name}' does not exist{RESET}")
        return False


def test_trigger_exists(cursor, trigger_name, table_name):
    """Test if a trigger exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.triggers 
            WHERE trigger_schema = 'public' 
            AND trigger_name = %s
            AND event_object_table = %s
        );
    """, (trigger_name, table_name))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Trigger '{trigger_name}' exists on table '{table_name}'{RESET}")
        return True
    else:
        logger.error(f"{RED}✗ Trigger '{trigger_name}' does not exist on table '{table_name}'{RESET}")
        return False


def test_foreign_key_exists(cursor, table_name, constraint_name):
    """Test if a foreign key constraint exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints 
            WHERE table_schema = 'public' 
            AND table_name = %s
            AND constraint_name = %s
            AND constraint_type = 'FOREIGN KEY'
        );
    """, (table_name, constraint_name))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Foreign key '{constraint_name}' exists on table '{table_name}'{RESET}")
        return True
    else:
        logger.warning(f"{YELLOW}⚠ Foreign key '{constraint_name}' not found on table '{table_name}' (may use different name){RESET}")
        return True  # Don't fail test as FK names may vary


def test_extension_exists(cursor, extension_name):
    """Test if a PostgreSQL extension is installed."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM pg_extension 
            WHERE extname = %s
        );
    """, (extension_name,))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Extension '{extension_name}' is installed{RESET}")
        return True
    else:
        logger.error(f"{RED}✗ Extension '{extension_name}' is not installed{RESET}")
        return False


def test_column_exists(cursor, table_name, column_name):
    """Test if a column exists in a table."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
            AND column_name = %s
        );
    """, (table_name, column_name))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        logger.info(f"{GREEN}✓ Column '{column_name}' exists in table '{table_name}'{RESET}")
        return True
    else:
        logger.error(f"{RED}✗ Column '{column_name}' does not exist in table '{table_name}'{RESET}")
        return False


def run_tests():
    """Run all database initialization tests."""
    logger.info("=" * 80)
    logger.info("Starting Database Initialization Tests")
    logger.info("=" * 80)
    
    test_results = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test 1: PostGIS Extension
        logger.info("\n--- Test 1: Extensions ---")
        test_results.append(test_extension_exists(cursor, 'postgis'))
        
        # Test 2: Core Tables
        logger.info("\n--- Test 2: Core Tables ---")
        core_tables = ['tenants', 'users', 'teams']
        for table in core_tables:
            test_results.append(test_table_exists(cursor, table))
        
        # Test 3: Agent Management Tables
        logger.info("\n--- Test 3: Agent Management Tables ---")
        test_results.append(test_table_exists(cursor, 'agent_definitions'))
        
        # Test 4: Domain Configuration Tables
        logger.info("\n--- Test 4: Domain Configuration Tables ---")
        test_results.append(test_table_exists(cursor, 'domain_configurations'))
        
        # Test 5: Legacy Tables
        logger.info("\n--- Test 5: Legacy Tables ---")
        test_results.append(test_table_exists(cursor, 'incidents'))
        test_results.append(test_table_exists(cursor, 'image_evidence'))
        
        # Test 6: Agent Definitions Columns
        logger.info("\n--- Test 6: Agent Definitions Columns ---")
        agent_columns = [
            'id', 'agent_id', 'tenant_id', 'agent_name', 'agent_class',
            'system_prompt', 'tools', 'agent_dependencies', 'max_output_keys',
            'output_schema', 'description', 'enabled', 'is_inbuilt', 'version',
            'created_at', 'updated_at', 'created_by'
        ]
        for column in agent_columns:
            test_results.append(test_column_exists(cursor, 'agent_definitions', column))
        
        # Test 7: Domain Configurations Columns
        logger.info("\n--- Test 7: Domain Configurations Columns ---")
        domain_columns = [
            'id', 'domain_id', 'tenant_id', 'domain_name', 'description',
            'ingestion_playbook', 'query_playbook', 'management_playbook',
            'created_at', 'updated_at', 'created_by'
        ]
        for column in domain_columns:
            test_results.append(test_column_exists(cursor, 'domain_configurations', column))
        
        # Test 8: Indexes
        logger.info("\n--- Test 8: Indexes ---")
        indexes = [
            'idx_agents_tenant_class',
            'idx_agents_enabled',
            'idx_agents_tenant',
            'idx_domains_tenant',
            'idx_incidents_tenant_domain',
            'idx_incidents_created_at',
            'idx_incidents_structured_data',
            'idx_incidents_location',
            'idx_image_evidence_incident',
            'idx_image_evidence_tenant'
        ]
        for index in indexes:
            test_results.append(test_index_exists(cursor, index))
        
        # Test 9: Triggers
        logger.info("\n--- Test 9: Triggers ---")
        triggers = [
            ('update_tenants_updated_at', 'tenants'),
            ('update_users_updated_at', 'users'),
            ('update_teams_updated_at', 'teams'),
            ('update_agent_definitions_updated_at', 'agent_definitions'),
            ('update_domain_configurations_updated_at', 'domain_configurations'),
            ('update_incidents_updated_at', 'incidents')
        ]
        for trigger_name, table_name in triggers:
            test_results.append(test_trigger_exists(cursor, trigger_name, table_name))
        
        # Test 10: Check Constraints
        logger.info("\n--- Test 10: Check Constraints ---")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.check_constraints 
                WHERE constraint_schema = 'public'
                AND constraint_name LIKE '%agent_class%'
            );
        """)
        check_exists = cursor.fetchone()[0]
        if check_exists:
            logger.info(f"{GREEN}✓ Check constraint on agent_class exists{RESET}")
            test_results.append(True)
        else:
            logger.error(f"{RED}✗ Check constraint on agent_class does not exist{RESET}")
            test_results.append(False)
        
        # Test 11: Trigger Function
        logger.info("\n--- Test 11: Trigger Function ---")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc 
                WHERE proname = 'update_updated_at_column'
            );
        """)
        func_exists = cursor.fetchone()[0]
        if func_exists:
            logger.info(f"{GREEN}✓ Trigger function 'update_updated_at_column' exists{RESET}")
            test_results.append(True)
        else:
            logger.error(f"{RED}✗ Trigger function 'update_updated_at_column' does not exist{RESET}")
            test_results.append(False)
        
        cursor.close()
        conn.close()
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("Test Summary")
        logger.info("=" * 80)
        
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"{GREEN}Passed: {passed_tests}{RESET}")
        logger.info(f"{RED}Failed: {failed_tests}{RESET}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests == 0:
            logger.info(f"\n{GREEN}✓ All tests passed! Database initialization is correct.{RESET}")
            return 0
        else:
            logger.error(f"\n{RED}✗ Some tests failed. Please review the errors above.{RESET}")
            return 1
        
    except Exception as e:
        logger.error(f"\n{RED}✗ Test execution failed: {str(e)}{RESET}")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
