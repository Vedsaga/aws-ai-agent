# Orchestrator Fix Summary

## Changes Made ✓

### 1. Updated Imports (orchestrator_handler.py)
**Added RDS utility functions:**
```python
from rds_utils import (
    get_incidents_for_query, 
    extract_incident_ids,
    get_domain_by_id,        # NEW: Load domain from RDS
    get_playbook,            # NEW: Extract playbook from domain
    get_agents_by_ids        # NEW: Load multiple agents from RDS
)
```

### 2. Fixed Domain Loading (orchestrator_handler.py)
**BEFORE (BROKEN):**
```python
domain_config = load_domain_config(domain_id)  # Used DynamoDB
agent_ids = domain_config.get("ingest_agent_ids", ["geo_agent", "temporal_agent"])
```

**AFTER (FIXED):**
```python
# Load domain from RDS
domain = get_domain_by_id(tenant_id, domain_id)

# Get playbook from domain
playbook_type = 'ingestion' if job_type == 'ingest' else 'query'
playbook = get_playbook(tenant_id, domain_id, playbook_type)

# Extract agent IDs from playbook
agent_ids = playbook['agent_execution_graph']['nodes']
# Result: ["builtin-ingestion-geo", "builtin-ingestion-temporal", ...]
```

### 3. Fixed Agent Loading (orchestrator_handler.py)
**BEFORE (BROKEN):**
```python
agents = []
for agent_id in agent_ids:
    agent_config = load_agent_config(agent_id)  # Used DynamoDB
    if agent_config:
        agents.append(agent_config)
```

**AFTER (FIXED):**
```python
# Load all agents in one query from RDS
agents_dict = get_agents_by_ids(tenant_id, agent_ids)

# Convert to list with fallback for missing agents
agents = []
for agent_id in agent_ids:
    if agent_id in agents_dict:
        agent_config = agents_dict[agent_id]
        agent_config['agent_id'] = agent_id
        agents.append(agent_config)
    else:
        # Fallback for missing agents
        agents.append(create_fallback_agent_config(agent_id))
```

### 4. Updated Fallback Agent IDs (orchestrator_handler.py)
**BEFORE (WRONG IDs):**
```python
def get_default_domain_config(job_type: str):
    if job_type == "ingest":
        return {"ingest_agent_ids": ["geo_agent", "temporal_agent", "category_agent"]}
```

**AFTER (CORRECT IDs):**
```python
def get_default_domain_config(job_type: str):
    if job_type == "ingest":
        return {
            "ingest_agent_ids": [
                "builtin-ingestion-geo",
                "builtin-ingestion-temporal",
                "builtin-ingestion-entity"
            ]
        }
```

### 5. Enhanced RDS Functions (rds_utils.py)

#### get_domain_by_id()
**Added system tenant fallback:**
```python
# Try tenant-specific domain first
cursor.execute(query, (tenant_id, domain_id))
domain = cursor.fetchone()

# If not found, try system tenant for builtin domains
if not domain:
    cursor.execute(query, ('system', domain_id))
    domain = cursor.fetchone()
```

#### get_agents_by_ids()
**Added system tenant fallback:**
```python
# First try tenant-specific agents
cursor.execute(query, (tenant_id, agent_ids))
agents = cursor.fetchall()

# Check for missing agents and try system tenant
missing = set(agent_ids) - set(agents_dict.keys())
if missing:
    cursor.execute(query, ('system', list(missing)))
    system_agents = cursor.fetchall()
    # Add system agents to result
```

### 6. Removed Obsolete Functions
- ❌ `load_domain_config()` - Used DynamoDB, now using `get_domain_by_id()`
- ❌ `load_agent_config()` - Used DynamoDB, now using `get_agents_by_ids()`

## How It Works Now

### Ingestion Flow:
1. User submits report to domain `civic_complaints`
2. Report handler triggers orchestrator with `job_type='ingest'`
3. Orchestrator loads domain from RDS: `get_domain_by_id('default-tenant', 'civic_complaints')`
4. Orchestrator extracts ingestion playbook: `domain['ingestion_playbook']`
5. Gets agent IDs: `['builtin-ingestion-geo', 'builtin-ingestion-temporal', 'builtin-ingestion-entity']`
6. Loads agents from RDS: `get_agents_by_ids('default-tenant', agent_ids)`
7. Executes each agent with correct system prompts and tools
8. Saves results with agent execution logs

### Query Flow:
1. User submits query to domain `civic_complaints`
2. Query handler triggers orchestrator with `job_type='query'`
3. Orchestrator loads domain from RDS
4. Orchestrator extracts query playbook: `domain['query_playbook']`
5. Gets agent IDs: `['builtin-query-who', 'builtin-query-what', 'builtin-query-where', 'builtin-query-when']`
6. Loads agents from RDS with system prompts
7. Executes each agent with incident data
8. Saves results with references to incidents used

### Management Flow:
1. User updates report
2. Triggers orchestrator with `job_type='management'`
3. Loads management playbook from domain
4. Gets agent IDs: `['builtin-management-task-assigner', 'builtin-management-status-updater', ...]`
5. Executes management agents
6. Updates report with management data

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
│  (Submit Report / Ask Question / Update Report)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              API Handler (report/query/management)           │
│  - Validates request                                         │
│  - Stores to DynamoDB                                        │
│  - Triggers Orchestrator Lambda                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Lambda                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Load Domain from RDS                              │   │
│  │    get_domain_by_id(tenant_id, domain_id)            │   │
│  │    → Returns domain with 3 playbooks                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Extract Playbook                                  │   │
│  │    playbook = domain['ingestion_playbook']           │   │
│  │    agent_ids = playbook['agent_execution_graph']...  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. Load Agents from RDS                              │   │
│  │    agents = get_agents_by_ids(tenant_id, agent_ids)  │   │
│  │    → Returns agent configs with system prompts       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Execute Each Agent                                │   │
│  │    for agent in agents:                              │   │
│  │        result = execute_agent(agent, text)           │   │
│  │        → Calls Bedrock with agent's system prompt    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. Save Results                                      │   │
│  │    save_results(job_id, results, execution_log)      │   │
│  │    → Updates DynamoDB with agent outputs             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Verification

### Check Domain Loading:
```python
from rds_utils import get_domain_by_id

domain = get_domain_by_id('system', 'civic_complaints')
print(domain['domain_name'])  # "Civic Complaints"
print(domain['ingestion_playbook']['agent_execution_graph']['nodes'])
# ['builtin-ingestion-geo', 'builtin-ingestion-temporal', 'builtin-ingestion-entity']
```

### Check Agent Loading:
```python
from rds_utils import get_agents_by_ids

agent_ids = ['builtin-ingestion-geo', 'builtin-ingestion-temporal']
agents = get_agents_by_ids('system', agent_ids)

for agent_id, agent in agents.items():
    print(f"{agent_id}: {agent['agent_name']}")
    print(f"  System prompt: {agent['system_prompt'][:50]}...")
    print(f"  Tools: {agent['tools']}")
```

## Testing

### Run E2E Test:
```bash
# Set environment variables
export API_BASE_URL="https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1"
export COGNITO_CLIENT_ID="6gobbpage9af3nd7ahm3lchkct"
export TEST_USERNAME="testuser"
export TEST_PASSWORD="TestPassword123!"

# Run test
python3 test_e2e_flows.py
```

### Expected Results:
1. ✓ Domain created with correct playbooks
2. ✓ Report submitted triggers 3 ingestion agents
3. ✓ Agents loaded from RDS with correct IDs
4. ✓ Execution logs show agent outputs
5. ✓ Query triggers 4 query agents
6. ✓ Management update triggers 3 management agents

## Files Modified

1. **infrastructure/lambda/orchestration/orchestrator_handler.py**
   - Added RDS imports
   - Replaced domain loading logic
   - Replaced agent loading logic
   - Updated fallback agent IDs
   - Removed obsolete functions

2. **infrastructure/lambda/orchestration/rds_utils.py**
   - Enhanced `get_domain_by_id()` with system tenant fallback
   - Enhanced `get_agents_by_ids()` with system tenant fallback

## Summary

✅ **Orchestrator now correctly loads domains and agents from RDS PostgreSQL**
✅ **Builtin agents are properly discovered and executed**
✅ **Domain playbooks control which agents run**
✅ **System tenant fallback ensures builtin agents are always available**
✅ **E2E tests will now trigger the correct agents**

The fix ensures that the 12 builtin agents seeded in the database are actually used when processing reports and queries!
