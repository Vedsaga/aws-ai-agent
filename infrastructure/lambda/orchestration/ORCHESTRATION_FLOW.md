# Orchestration Flow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Step Functions State Machine                     │
│                     (15-minute timeout)                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 1: Configuration Loading                                     │
├─────────────────────────────────────────────────────────────────────┤
│  1. LoadPlaybook                                                     │
│     ├─ Query DynamoDB (playbook_configs)                            │
│     ├─ Filter by tenant_id, domain_id, playbook_type               │
│     └─ Return agent_ids list                                        │
│                                                                      │
│  2. LoadDependencyGraph                                             │
│     ├─ Query DynamoDB (dependency_graphs)                           │
│     ├─ Validate single-level dependencies                           │
│     └─ Return edges list                                            │
│                                                                      │
│  3. BuildExecutionPlan                                              │
│     ├─ Topological sort (Kahn's algorithm)                          │
│     ├─ Detect circular dependencies                                 │
│     └─ Return execution levels                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 2: Agent Execution (Map State)                               │
├─────────────────────────────────────────────────────────────────────┤
│  ExecuteAgents (MaxConcurrency: 10)                                 │
│                                                                      │
│  Level 0 (Parallel):                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │                         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                         │
│       │             │             │                                 │
│       └─────────────┴─────────────┘                                │
│                     │                                               │
│  Level 1 (Depends on Level 0):                                     │
│                ┌────▼─────┐                                         │
│                │ Agent D  │  (depends on Agent A)                  │
│                └──────────┘                                         │
│                                                                      │
│  Each agent:                                                        │
│  ├─ AgentInvoker loads config from DynamoDB                        │
│  ├─ Invokes appropriate Lambda (Geo, Temporal, Entity, Custom)    │
│  ├─ Passes raw_text + parent_output (if dependent)                │
│  └─ Returns standardized output                                    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 3: Result Processing                                         │
├─────────────────────────────────────────────────────────────────────┤
│  4. AggregateResults                                                │
│     ├─ Collect all agent outputs                                   │
│     ├─ Preserve execution order                                    │
│     ├─ Separate successful vs failed                               │
│     └─ Calculate statistics                                        │
│                                                                      │
│  5. ValidateOutputs                                                 │
│     ├─ Load schemas from DynamoDB                                  │
│     ├─ Check max 5 keys constraint                                 │
│     ├─ Validate against schema                                     │
│     └─ Cross-validate consistency                                  │
│                                                                      │
│  6. SynthesizeResults                                               │
│     ├─ Merge validated outputs                                     │
│     ├─ Resolve conflicts (prefer Geo for location, etc)           │
│     ├─ Deduplicate entities                                        │
│     └─ Format for storage                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 4: Data Persistence                                          │
├─────────────────────────────────────────────────────────────────────┤
│  7. SaveResults                                                     │
│     ├─ Insert into RDS PostgreSQL (incidents table)                │
│     ├─ Create embeddings (Bedrock Titan)                           │
│     ├─ Index in OpenSearch (vector search)                         │
│     ├─ Store image metadata (image_evidence table)                 │
│     └─ Trigger EventBridge event (map update)                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                              ┌────────┐
                              │Success │
                              └────────┘
```

## Execution Example

### Input
```json
{
  "job_id": "job-123",
  "tenant_id": "tenant-456",
  "domain_id": "civic-complaints",
  "playbook_type": "ingestion",
  "raw_text": "Pothole on Main Street near the library",
  "images": [],
  "created_by": "user-789"
}
```

### Step 1: Load Playbook
```json
{
  "playbook_id": "civic-complaints-ingestion",
  "agent_ids": ["geo-agent", "temporal-agent", "entity-agent", "severity-classifier"]
}
```

### Step 2: Load Dependency Graph
```json
{
  "edges": [
    {"from": "entity-agent", "to": "severity-classifier"}
  ]
}
```

### Step 3: Build Execution Plan
```json
{
  "execution_plan": [
    {"agent_id": "geo-agent", "level": 0, "depends_on": null},
    {"agent_id": "temporal-agent", "level": 0, "depends_on": null},
    {"agent_id": "entity-agent", "level": 0, "depends_on": null},
    {"agent_id": "severity-classifier", "level": 1, "depends_on": "entity-agent"}
  ],
  "level_count": 2
}
```

### Step 4: Execute Agents

**Level 0 (Parallel):**
- Geo Agent → `{"location": "Main Street", "coordinates": [40.7, -74.0]}`
- Temporal Agent → `{"timestamp": "2024-01-15T10:30:00Z", "date": "2024-01-15"}`
- Entity Agent → `{"entities": ["Main Street", "library"], "sentiment": "NEGATIVE"}`

**Level 1 (Sequential):**
- Severity Classifier (depends on Entity Agent) → `{"severity": "medium", "priority": 7}`

### Step 5: Aggregate Results
```json
{
  "successful_results": [
    {"agent_name": "Geo Agent", "output": {...}},
    {"agent_name": "Temporal Agent", "output": {...}},
    {"agent_name": "Entity Agent", "output": {...}},
    {"agent_name": "Severity Classifier", "output": {...}}
  ],
  "statistics": {
    "total_agents": 4,
    "successful_count": 4,
    "failed_count": 0,
    "success_rate": 100
  }
}
```

### Step 6: Validate Outputs
- All outputs have ≤ 5 keys ✓
- All keys match schemas ✓
- No consistency conflicts ✓

### Step 7: Synthesize Results
```json
{
  "geo_agent": {"agent_name": "Geo Agent", "data": {...}},
  "temporal_agent": {"agent_name": "Temporal Agent", "data": {...}},
  "entity_agent": {"agent_name": "Entity Agent", "data": {...}},
  "severity_classifier": {"agent_name": "Severity Classifier", "data": {...}},
  "_location": {"location": "Main Street", "coordinates": [40.7, -74.0]},
  "_temporal": {"timestamp": "2024-01-15T10:30:00Z"},
  "_entities": ["Main Street", "library"],
  "_sentiment": {"sentiment": "NEGATIVE"}
}
```

### Step 8: Save Results
- PostgreSQL: incident record created ✓
- OpenSearch: embedding indexed ✓
- EventBridge: map update event triggered ✓

### Output
```json
{
  "job_id": "job-123",
  "incident_id": "job-123",
  "save_status": "success",
  "database_saved": true,
  "opensearch_indexed": true,
  "map_event_triggered": true
}
```

## Error Handling Flow

```
┌─────────────────┐
│  Any Lambda     │
│  Task Fails     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Retry Logic    │
│  (3 attempts)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌──────────┐
│Success │  │Still Fail│
└────────┘  └─────┬────┘
                  │
                  ▼
            ┌──────────┐
            │  Catch   │
            │  Block   │
            └─────┬────┘
                  │
                  ▼
            ┌──────────┐
            │HandleError│
            └─────┬────┘
                  │
                  ▼
            ┌──────────┐
            │   Fail   │
            └──────────┘
```

## Dependency Graph Example

```
Input: 5 agents with dependencies

Agents: A, B, C, D, E
Edges: 
  - A → D (D depends on A)
  - B → D (D depends on B) ❌ INVALID (multiple parents)
  - C → E (E depends on C)

Valid Graph:
  - A → D (D depends on A)
  - C → E (E depends on C)

Execution Levels:
  Level 0: [A, B, C]  (parallel)
  Level 1: [D, E]     (parallel, after their parents)
```

## Performance Characteristics

- **Parallel Execution**: Up to 10 agents concurrently
- **Total Timeout**: 15 minutes
- **Agent Timeout**: 5 minutes per agent
- **Retry Attempts**: 3 for most tasks, 2 for agent invocations
- **Backoff**: Exponential (2x multiplier)

## Monitoring Points

1. **LoadPlaybook**: Playbook found/not found
2. **LoadDependencyGraph**: Dependency validation
3. **BuildExecutionPlan**: Circular dependency detection
4. **ExecuteAgents**: Agent success/failure rates
5. **AggregateResults**: Partial failure handling
6. **ValidateOutputs**: Schema validation errors
7. **SynthesizeResults**: Conflict resolution
8. **SaveResults**: Database/OpenSearch success

## CloudWatch Metrics

- `ExecutionTime` - Total orchestration duration
- `AgentSuccessRate` - Percentage of successful agents
- `ValidationErrors` - Count of validation failures
- `PartialFailures` - Jobs with some failed agents
- `CircularDependencies` - Dependency graph errors
