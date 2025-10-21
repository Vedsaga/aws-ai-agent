-- DomainFlow Agentic Orchestration Platform
-- RDS PostgreSQL Database Schema
-- This file documents the database schema created by db_init.py

-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- Core Tables: Tenants, Users, Teams
-- ============================================================================

-- Tenants table: Multi-tenancy support
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table: User accounts linked to Cognito
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

-- Teams table: User groups for collaboration
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

-- ============================================================================
-- Agent Management Tables
-- ============================================================================

-- Agent Definitions table: Unified storage for all three agent classes
-- (ingestion, query, management)
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

-- Indexes for agent_definitions
CREATE INDEX IF NOT EXISTS idx_agents_tenant_class 
ON agent_definitions(tenant_id, agent_class);

CREATE INDEX IF NOT EXISTS idx_agents_enabled 
ON agent_definitions(enabled);

CREATE INDEX IF NOT EXISTS idx_agents_tenant 
ON agent_definitions(tenant_id);

-- ============================================================================
-- Domain Configuration Tables
-- ============================================================================

-- Domain Configurations table: Business domains with three playbooks
-- (ingestion_playbook, query_playbook, management_playbook)
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

-- Indexes for domain_configurations
CREATE INDEX IF NOT EXISTS idx_domains_tenant 
ON domain_configurations(tenant_id);

-- ============================================================================
-- Legacy Tables (Backward Compatibility)
-- ============================================================================

-- Incidents table: Legacy table for backward compatibility
-- New reports will be stored in DynamoDB
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

-- Indexes for incidents
CREATE INDEX IF NOT EXISTS idx_incidents_tenant_domain 
ON incidents(tenant_id, domain_id);

CREATE INDEX IF NOT EXISTS idx_incidents_created_at 
ON incidents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_incidents_structured_data 
ON incidents USING GIN(structured_data);

CREATE INDEX IF NOT EXISTS idx_incidents_location 
ON incidents USING GIST(location);

-- Image Evidence table: S3 references for incident images
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

-- Indexes for image_evidence
CREATE INDEX IF NOT EXISTS idx_image_evidence_incident 
ON image_evidence(incident_id);

CREATE INDEX IF NOT EXISTS idx_image_evidence_tenant 
ON image_evidence(tenant_id);

-- ============================================================================
-- Triggers
-- ============================================================================

-- Trigger function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
CREATE TRIGGER update_tenants_updated_at
BEFORE UPDATE ON tenants
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_teams_updated_at ON teams;
CREATE TRIGGER update_teams_updated_at
BEFORE UPDATE ON teams
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_definitions_updated_at ON agent_definitions;
CREATE TRIGGER update_agent_definitions_updated_at
BEFORE UPDATE ON agent_definitions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_domain_configurations_updated_at ON domain_configurations;
CREATE TRIGGER update_domain_configurations_updated_at
BEFORE UPDATE ON domain_configurations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_incidents_updated_at ON incidents;
CREATE TRIGGER update_incidents_updated_at
BEFORE UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Notes
-- ============================================================================

-- DynamoDB Tables (not in RDS):
-- - Reports: High-volume report documents with flexible schema
-- - Sessions: Chat session metadata
-- - Messages: Chat messages with references
-- - QueryJobs: Query execution results and logs

-- Standard Metadata Fields:
-- All primary objects include:
-- - id: UUID primary key
-- - created_at: Timestamp of creation
-- - updated_at: Timestamp of last update (auto-updated by trigger)
-- - created_by: User ID who created the record

-- Agent Classes:
-- - ingestion: CREATE new data from unstructured input
-- - query: READ data and answer questions
-- - management: UPDATE existing data

-- Playbook Structure (JSONB):
-- {
--   "agent_execution_graph": {
--     "nodes": ["agent-id-1", "agent-id-2"],
--     "edges": [{"from": "agent-id-1", "to": "agent-id-2"}]
--   }
-- }
