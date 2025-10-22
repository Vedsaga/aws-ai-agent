# Ingest Handler Update Summary

## Task 13: Update Report Submission Flow

### Changes Made

Updated `ingest_handler_simple.py` to align with the new unified API architecture:

#### 1. **Migrated to Reports Table**
- Changed from `INCIDENTS_TABLE` to `REPORTS_TABLE` environment variable
- Updated DynamoDB table initialization to use the new Reports table
- Modified table name default: `MultiAgentOrchestration-dev-Reports`

#### 2. **Added Standard Metadata**
All reports now include the required standard metadata fields:
- `id`: UUID for the report (separate from incident_id)
- `created_at`: ISO8601 timestamp when report was created
- `updated_at`: ISO8601 timestamp when report was last modified
- `created_by`: User ID from the authorizer context

#### 3. **Updated Report Structure**
Reports now follow the new schema with:
- `ingestion_data`: Empty dict (populated by ingestion agents)
- `management_data`: Empty dict (populated by management agents)
- Removed legacy fields: `priority`, `reporter_contact`, `structured_data`
- Kept essential fields: `incident_id`, `tenant_id`, `domain_id`, `raw_text`, `status`, `source`, `images`

#### 4. **Added RDS Integration**
Implemented `load_ingestion_playbook()` function to:
- Connect to RDS PostgreSQL database
- Query `domain_configurations` table for the domain's ingestion_playbook
- Return the playbook configuration to pass to the orchestrator
- Fallback to default playbook if domain not found or RDS unavailable

Added RDS connection parameters:
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
- Uses psycopg2 with RealDictCursor for JSON-friendly results

#### 5. **Enhanced Orchestrator Invocation**
Updated the orchestrator payload to include:
- `job_type`: "ingest" (explicitly set)
- `user_id`: Extracted from authorizer context
- `playbook`: The ingestion_playbook loaded from RDS
- Removed legacy fields: `priority`

#### 6. **Improved Error Handling**
- Returns 404 if domain not found or has no ingestion playbook
- Provides fallback playbook with basic agents (geo, temporal, category)
- Better error messages for debugging

### Requirements Satisfied

✅ **Requirement 3.1**: Report submission uses new Reports DynamoDB table
✅ **Requirement 12.1**: Standard metadata (id, created_at, updated_at, created_by) added to all reports
✅ **Requirement 12.2**: Orchestrator receives ingestion_playbook from domain configuration

### Dependencies

**Python Packages:**
- `psycopg2`: For RDS PostgreSQL connectivity (provided via Lambda layer)
- `boto3`: For DynamoDB and Lambda invocation

**Infrastructure:**
- Requires psycopg2 Lambda layer to be attached to the ingest handler function
- Requires RDS environment variables to be configured
- Requires Reports DynamoDB table to exist
- Requires domain_configurations table in RDS

### Deployment Notes

1. **Lambda Layer**: The ingest handler Lambda function must include the psycopg2 layer (already exists in `infrastructure/layers/psycopg2`)

2. **Environment Variables**: Ensure these are set:
   ```
   REPORTS_TABLE=MultiAgentOrchestration-dev-Reports
   ORCHESTRATOR_FUNCTION=MultiAgentOrchestration-dev-Orchestrator
   DB_HOST=<rds-endpoint>
   DB_NAME=orchestration_db
   DB_USER=postgres
   DB_PASSWORD=<secret>
   DB_PORT=5432
   ```

3. **IAM Permissions**: Lambda execution role needs:
   - DynamoDB: PutItem on Reports table
   - Lambda: InvokeFunction on Orchestrator
   - RDS: Network access via VPC configuration (if RDS is in VPC)

### Testing Recommendations

1. **Unit Tests**: Test `load_ingestion_playbook()` with:
   - Valid domain_id
   - Non-existent domain_id (should use fallback)
   - RDS connection failure (should use fallback)

2. **Integration Tests**: Test full report submission flow:
   - Submit report with valid domain_id
   - Verify report stored in Reports table with correct structure
   - Verify orchestrator invoked with playbook
   - Verify standard metadata fields populated

3. **Error Cases**: Test error handling:
   - Missing domain_id
   - Missing text
   - Text exceeds 10000 characters
   - Reports table unavailable
   - Domain not found

### Next Steps

- Task 14: Write integration tests for report flow (marked as optional)
- Task 15: Update Query Handler for mode selection
- Ensure orchestration stack includes psycopg2 layer for ingest handler
