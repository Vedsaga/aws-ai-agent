# Database Initialization Lambda

This Lambda function initializes the RDS PostgreSQL database schema for the DomainFlow Agentic Orchestration Platform.

## Overview

The database uses a hybrid storage strategy:
- **RDS PostgreSQL**: Structured, relational data requiring joins and transactional integrity
- **DynamoDB**: High-volume, dynamic data with flexible schema

## RDS Tables

### Core Tables

#### tenants
Multi-tenancy support for isolating customer data.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| tenant_name | VARCHAR(200) | Tenant display name |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### users
User accounts linked to AWS Cognito.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| username | VARCHAR(100) | Unique username |
| email | VARCHAR(255) | Unique email address |
| cognito_sub | VARCHAR(255) | Cognito user ID |
| tenant_id | UUID | Foreign key to tenants |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### teams
User groups for collaboration and task assignment.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| team_name | VARCHAR(200) | Team display name |
| tenant_id | UUID | Foreign key to tenants |
| members | JSONB | Array of user IDs |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_by | UUID | Foreign key to users |

### Agent Management Tables

#### agent_definitions
Unified storage for all three agent classes (ingestion, query, management).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_id | VARCHAR(100) | Unique agent identifier |
| tenant_id | UUID | Foreign key to tenants |
| agent_name | VARCHAR(200) | Agent display name |
| agent_class | VARCHAR(20) | 'ingestion', 'query', or 'management' |
| system_prompt | TEXT | LLM system prompt |
| tools | JSONB | Array of tool names |
| agent_dependencies | JSONB | Array of agent IDs |
| max_output_keys | INTEGER | Max output properties (locked at 5) |
| output_schema | JSONB | JSON schema for output |
| description | TEXT | Agent description |
| enabled | BOOLEAN | Active status |
| is_inbuilt | BOOLEAN | Built-in agent flag |
| version | INTEGER | Version number |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_by | UUID | Foreign key to users |

**Indexes:**
- `idx_agents_tenant_class`: (tenant_id, agent_class)
- `idx_agents_enabled`: (enabled)
- `idx_agents_tenant`: (tenant_id)

### Domain Configuration Tables

#### domain_configurations
Business domains with three playbooks (ingestion, query, management).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| domain_id | VARCHAR(100) | Unique domain identifier |
| tenant_id | UUID | Foreign key to tenants |
| domain_name | VARCHAR(200) | Domain display name |
| description | TEXT | Domain description |
| ingestion_playbook | JSONB | Agent execution graph for data creation |
| query_playbook | JSONB | Agent execution graph for data reading |
| management_playbook | JSONB | Agent execution graph for data updates |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_by | UUID | Foreign key to users |

**Indexes:**
- `idx_domains_tenant`: (tenant_id)

**Playbook Structure:**
```json
{
  "agent_execution_graph": {
    "nodes": ["agent-id-1", "agent-id-2", "agent-id-3"],
    "edges": [
      {"from": "agent-id-1", "to": "agent-id-3"},
      {"from": "agent-id-2", "to": "agent-id-3"}
    ]
  }
}
```

### Legacy Tables

#### incidents
Legacy table for backward compatibility. New reports are stored in DynamoDB.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Foreign key to tenants |
| domain_id | VARCHAR(100) | Domain identifier |
| raw_text | TEXT | Original report text |
| structured_data | JSONB | Extracted structured data |
| location | GEOGRAPHY(POINT) | Geographic coordinates |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| created_by | UUID | Foreign key to users |

**Indexes:**
- `idx_incidents_tenant_domain`: (tenant_id, domain_id)
- `idx_incidents_created_at`: (created_at DESC)
- `idx_incidents_structured_data`: GIN index on JSONB
- `idx_incidents_location`: GIST index on geography

#### image_evidence
S3 references for incident images.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| incident_id | UUID | Foreign key to incidents |
| tenant_id | UUID | Foreign key to tenants |
| s3_key | VARCHAR(500) | S3 object key |
| s3_bucket | VARCHAR(200) | S3 bucket name |
| content_type | VARCHAR(100) | MIME type |
| file_size_bytes | INTEGER | File size |
| uploaded_at | TIMESTAMP | Upload timestamp |

## DynamoDB Tables

The following tables are stored in DynamoDB (not RDS):

### Reports
High-volume report documents with flexible schema.

**Partition Key:** incident_id (String)

**GSIs:**
- `tenant-domain-index`: (tenant_id, domain_id)
- `domain-created-index`: (domain_id, created_at)

**Attributes:**
- incident_id, tenant_id, domain_id
- raw_text, images, source, status
- ingestion_data (JSONB - flexible schema)
- management_data (JSONB - flexible schema)
- id, created_at, updated_at, created_by

### Sessions
Chat session metadata.

**Partition Key:** session_id (String)

**GSI:** `user-activity-index` (user_id, last_activity)

**Attributes:**
- session_id, user_id, tenant_id, domain_id
- title, message_count, last_activity
- id, created_at, updated_at

### Messages
Chat messages with references to source data.

**Partition Key:** message_id (String)

**GSI:** `session-timestamp-index` (session_id, timestamp)

**Attributes:**
- message_id, session_id, role, content
- timestamp, metadata (with references array)

### QueryJobs
Query execution results and logs.

**Partition Key:** query_id (String)

**GSI:** `session-created-index` (session_id, created_at)

**Attributes:**
- query_id, job_id, session_id, tenant_id, domain_id
- question, status, summary
- map_data, references_used, execution_log
- id, created_at, completed_at

## Triggers

All tables with `updated_at` column have an automatic trigger that updates the timestamp on every UPDATE operation.

**Trigger Function:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

**Applied to:**
- tenants
- users
- teams
- agent_definitions
- domain_configurations
- incidents

## Environment Variables

The Lambda function requires the following environment variables:

- `DB_SECRET_ARN`: ARN of the Secrets Manager secret containing database credentials
- `DB_HOST`: RDS cluster endpoint
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name

## Deployment

The Lambda function is deployed as part of the CDK stack and is invoked automatically during stack creation to initialize the database schema.

### Manual Invocation

To manually reinitialize the schema:

```bash
aws lambda invoke \
  --function-name <db-init-function-name> \
  --payload '{}' \
  response.json
```

## Idempotency

The initialization script is idempotent and can be run multiple times safely. All `CREATE TABLE` and `CREATE INDEX` statements use `IF NOT EXISTS` to prevent errors on subsequent runs.

## Schema Updates

To update the schema:

1. Modify `db_init.py` with new table definitions or indexes
2. Deploy the updated Lambda function
3. Invoke the function to apply changes

**Note:** The function only creates new tables/indexes. It does not modify or drop existing ones. For schema migrations, use a separate migration script.

## Requirements

See `requirements.txt` for Python dependencies:
- boto3
- psycopg2

## Testing

To test the database initialization locally:

1. Set up environment variables
2. Run the Lambda function locally using AWS SAM or similar tools
3. Verify tables and indexes are created correctly

## Security

- Database credentials are stored in AWS Secrets Manager
- The Lambda function has IAM permissions to read the secret
- All database connections use SSL/TLS
- Foreign key constraints enforce referential integrity
- Check constraints validate data (e.g., agent_class values)

## Standard Metadata

All primary objects include standard metadata fields:

- `id`: UUID primary key
- `created_at`: ISO8601 timestamp of creation
- `updated_at`: ISO8601 timestamp of last update (auto-updated)
- `created_by`: User ID who created the record

## Agent Classes

The system supports three agent classes:

1. **ingestion**: CREATE new data from unstructured input
2. **query**: READ data and answer questions
3. **management**: UPDATE existing data

Each agent class has its own playbook in the domain configuration.

## References

- Design Document: `.kiro/specs/api-refactoring-single-responsibility/design.md`
- Requirements Document: `.kiro/specs/api-refactoring-single-responsibility/requirements.md`
- Tasks Document: `.kiro/specs/api-refactoring-single-responsibility/tasks.md`
