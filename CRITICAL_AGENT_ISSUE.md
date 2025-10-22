# CRITICAL ISSUE: Agents Are NOT Being Triggered from Database Playbooks

## Problem Summary

After thorough code analysis, I discovered that **the orchestrator is NOT loading playbooks from the RDS database**. Instead, it's using hardcoded agent IDs, which means:

❌ The builtin agents seeded in the database are **NOT being used**
❌ Domain playbooks configured in the database are **IGNORED**
❌ The E2E test will NOT trigger the expected agents

## Evidence

### 1. Orchestrator Handler (orchestrator_handler.py)

**Lines 220-235:**
```python
def process_job(job_data: Dict[str, Any]):
    # Step 1: Load domain configuration
    domain_config = load_domain_config(domain_id)
    if not domain_config:
        print(f"Domain not found: {domain_id}, using default agents")
        domain_config = get_default_domain_config(job_type)  # ❌ HARDCODED!

    # Step 2: Get agent list based on job type
    if job_type == "ingest":
        agent_ids = domain_config.get(
            "ingest_agent_ids", ["geo_agent", "temporal_agent"]  # ❌ HARDCODED!
        )
    else:
        agent_ids = domain_config.get(
            "query_agent_ids", ["what_agent", "where_agent", "when_agent"]  # ❌ HARDCODED!
        )
```

**Lines 450-465:**
```python
def get_default_domain_config(job_type: str) -> Dict[str, Any]:
    """Return default agent configuration"""
    if job_type == "ingest":
        return {
            "domain_id": "default",
            "ingest_agent_ids": ["geo_agent", "temporal_agent", "category_agent"],  # ❌ WRONG IDs!
        }
    else:
        return {
            "domain_id": "default",
            "query_agent_ids": ["what_agent", "where_agent", "when_agent"],  # ❌ WRONG IDs!
        }
```

### 2. What SHOULD Happen

The orchestrator should:
1. Load domain from RDS using `get_domain_by_id(tenant_id, domain_id)`
2. Extract the playbook: `domain['ingestion_playbook']` or `domain['query_playbook']`
3. Get agent IDs from playbook: `playbook['agent_execution_graph']['nodes']`
4. Load agent configs from RDS: `get_agents_by_ids(tenant_id, agent_ids)`

**Example from rds_utils.py (lines 188-220):**
```python
def get_playbook(tenant_id: str, domain_id: str, playbook_type: str) -> Optional[Dict[str, Any]]:
    """Get a specific playbook from domain configuration."""
    domain = get_domain_by_id(tenant_id, domain_id)
    
    playbook_column_map = {
        'ingestion': 'ingestion_playbook',
        'query': 'query_playbook',
        'management': 'management_playbook'
    }
    
    playbook = domain.get(playbook_column_map[playbook_type])
    return playbook
```

### 3. Correct Agent IDs in Database

**Ingestion Agents:**
- `builtin-ingestion-geo` (NOT `geo_agent`)
- `builtin-ingestion-temporal` (NOT `temporal_agent`)
- `builtin-ingestion-entity` (NOT `category_agent`)

**Query Agents:**
- `builtin-query-who` (NOT `who_agent`)
- `builtin-query-what` (NOT `what_agent`)
- `builtin-query-where` (NOT `where_agent`)
- `builtin-query-when` (NOT `when_agent`)
- `builtin-query-why`
- `builtin-query-how`

**Management Agents:**
- `builtin-management-task-assigner`
- `builtin-management-status-updater`
- `builtin-management-task-details-editor`

## Impact on E2E Testing

### Current Behavior (BROKEN):
1. User creates domain with playbook: `["builtin-ingestion-geo", "builtin-ingestion-temporal", "builtin-ingestion-entity"]`
2. User submits report
3. Orchestrator loads domain config from **DynamoDB Configurations table** (NOT RDS!)
4. Orchestrator uses hardcoded fallback: `["geo_agent", "temporal_agent", "category_agent"]`
5. Orchestrator tries to load agents with wrong IDs
6. **Agents fail to execute or use fallback configs**

### Expected Behavior (CORRECT):
1. User creates domain with playbook in **RDS database**
2. User submits report
3. Orchestrator loads domain from **RDS** using `get_domain_by_id()`
4. Orchestrator extracts playbook: `domain['ingestion_playbook']['agent_execution_graph']['nodes']`
5. Gets: `["builtin-ingestion-geo", "builtin-ingestion-temporal", "builtin-ingestion-entity"]`
6. Loads agent configs from **RDS** using `get_agents_by_ids()`
7. **Agents execute successfully with correct configurations**

## Root Cause

The orchestrator has **TWO SEPARATE DATA SOURCES**:

1. **DynamoDB Configurations Table** - Used by `load_domain_config()` (WRONG!)
   - Stores domain configs in format: `tenant_id + config_key`
   - Does NOT match RDS schema

2. **RDS PostgreSQL** - Contains the actual domain and agent data (CORRECT!)
   - Table: `domain_configurations` with columns: `ingestion_playbook`, `query_playbook`, `management_playbook`
   - Table: `agent_definitions` with builtin agents

**The orchestrator is using #1 when it should use #2!**

## Solution Required

### Fix orchestrator_handler.py:

```python
# REPLACE THIS:
def process_job(job_data: Dict[str, Any]):
    domain_config = load_domain_config(domain_id)  # ❌ Uses DynamoDB
    
# WITH THIS:
def process_job(job_data: Dict[str, Any]):
    from rds_utils import get_domain_by_id, get_playbook, get_agents_by_ids
    
    # Load domain from RDS
    domain = get_domain_by_id(tenant_id, domain_id)
    
    # Get playbook based on job type
    playbook_type = 'ingestion' if job_type == 'ingest' else 'query'
    playbook = get_playbook(tenant_id, domain_id, playbook_type)
    
    # Extract agent IDs from playbook
    agent_ids = playbook['agent_execution_graph']['nodes']
    
    # Load agent configs from RDS
    agents = get_agents_by_ids(tenant_id, agent_ids)
```

## Verification Steps

After fixing, verify:

1. ✓ Domain created in RDS with correct playbook
2. ✓ Orchestrator loads domain from RDS (not DynamoDB)
3. ✓ Orchestrator extracts agent IDs from playbook
4. ✓ Orchestrator loads agent configs from RDS
5. ✓ Agents execute with correct system prompts and tools
6. ✓ Results saved with agent execution logs

## Environment Variables

From `infrastructure/.env`:
```
API_BASE_URL=https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1
COGNITO_CLIENT_ID=6gobbpage9af3nd7ahm3lchkct
TEST_USERNAME=testuser
TEST_PASSWORD=TestPassword123!
AWS_REGION=us-east-1
```

## Next Steps

1. **FIX** orchestrator_handler.py to use RDS instead of DynamoDB
2. **UPDATE** E2E test to verify agent IDs match database
3. **RUN** E2E test to confirm agents are triggered
4. **VERIFY** execution logs show correct agent outputs

## Files to Modify

1. `infrastructure/lambda/orchestration/orchestrator_handler.py`
   - Import rds_utils functions
   - Replace `load_domain_config()` with `get_domain_by_id()`
   - Replace `load_agent_config()` with `get_agents_by_ids()`
   - Remove hardcoded agent IDs

2. `test_e2e_flows.py`
   - Update environment variables from infrastructure/.env
   - Add verification that correct agent IDs are used

## Summary

**The system has all the right pieces (RDS schema, seeded agents, playbooks) but the orchestrator is looking in the wrong place (DynamoDB instead of RDS).**

This is why the E2E test will fail - the agents won't be triggered because the orchestrator can't find them with the wrong IDs in the wrong database.
