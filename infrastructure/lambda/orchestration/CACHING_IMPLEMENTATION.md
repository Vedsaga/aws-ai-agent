# Agent Output Caching Implementation

## Overview

This document describes the implementation of agent output caching (memoization) in the Orchestrator class, as specified in task 22 of the API refactoring specification.

## Requirements Implemented

### Requirement 13.1: Cache agent outputs during job execution
- ✅ Cache dictionary added to Orchestrator class
- ✅ Agent outputs stored in cache after execution
- ✅ Cache persists for the duration of the job

### Requirement 13.2: Pass cached output to dependent agents
- ✅ Multiple agents depending on same upstream agent receive cached output
- ✅ No re-execution of shared dependencies
- ✅ Dependency outputs gathered from cache via `_gather_dependency_outputs()`

### Requirement 13.3: Check cache before executing agent
- ✅ Cache checked at start of `execute_agent()`
- ✅ Cached results returned immediately without re-execution
- ✅ Cache miss triggers normal agent execution

### Requirement 13.4: Clear cache after job completion
- ✅ Cache cleared after successful job completion
- ✅ Cache cleared after failed job completion
- ✅ Cache statistics logged before clearing

### Requirement 13.5: Log cache hits in execution_log
- ✅ Cache hits logged with status "cached"
- ✅ Execution time set to 0 for cached results
- ✅ Reasoning indicates output retrieved from cache

## Architecture

### Orchestrator Class

```python
class Orchestrator:
    def __init__(self, job_id, playbook, domain_id, tenant_id, user_id=None):
        self.job_id = job_id
        self.playbook = playbook
        self.domain_id = domain_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.cache = {}  # Agent output cache
        self.execution_log = []  # Execution history
```

### Cache Structure

The cache is a simple dictionary mapping agent IDs to their execution results:

```python
{
    "agent_id": {
        "status": "success",
        "output": {...},
        "reasoning": "...",
        "confidence": 0.9
    }
}
```

### Execution Flow

1. **Topological Sort**: Agents sorted by dependencies using Kahn's algorithm
2. **Execute in Order**: Each agent executed sequentially
3. **Cache Check**: Before execution, check if agent output is cached
4. **Cache Hit**: Return cached result, log as "cached"
5. **Cache Miss**: Execute agent, store result in cache, log as "success"
6. **Gather Dependencies**: Dependent agents receive cached outputs from upstream agents
7. **Clear Cache**: After job completion (success or failure), cache is cleared

## Usage Example

```python
from orchestrator import Orchestrator

# Define playbook with agent execution graph
playbook = {
    "agent_execution_graph": {
        "nodes": ["geo_agent", "temporal_agent", "category_agent"],
        "edges": [
            {"from": "geo_agent", "to": "category_agent"}
        ]
    }
}

# Create orchestrator
orchestrator = Orchestrator(
    job_id="job-123",
    playbook=playbook,
    domain_id="civic_complaints",
    tenant_id="tenant-456",
    user_id="user-789"
)

# Execute with input data
result = orchestrator.execute({
    "text": "There is a pothole on Main Street"
})

# Result includes execution log and cache statistics
print(result["status"])  # "completed" or "failed"
print(result["execution_log"])  # List of agent executions
print(result["cache_stats"])  # Cache hit/miss statistics
```

## Cache Statistics

After execution, the result includes cache statistics:

```python
{
    "status": "completed",
    "execution_log": [...],
    "cache_stats": {
        "cached_agents": 2,  # Number of cache hits
        "executed_agents": 3,  # Number of actual executions
        "total_agents": 5  # Total agents in execution log
    }
}
```

## Execution Log Format

Each entry in the execution log includes:

```python
{
    "agent_id": "geo_agent",
    "agent_name": "Geo Agent",
    "status": "success" | "cached" | "error" | "skipped",
    "timestamp": "2025-10-22T10:30:00Z",
    "reasoning": "Agent's reasoning or cache message",
    "output": {...},  # Agent output (null for errors/skipped)
    "execution_time_ms": 1234,  # 0 for cached results
    "error_message": "..."  # Only present for errors
}
```

## Benefits

### Performance
- **Reduced LLM Calls**: Shared dependencies executed once, not multiple times
- **Faster Execution**: Cache hits return instantly (0ms execution time)
- **Cost Savings**: Fewer Bedrock API calls reduce costs

### Consistency
- **Deterministic Results**: Dependent agents receive identical input from shared dependencies
- **No Drift**: Same upstream output used by all downstream agents

### Observability
- **Cache Visibility**: Execution log clearly shows which results were cached
- **Statistics**: Cache hit/miss rates tracked per job
- **Debugging**: Can identify which agents benefit most from caching

## Diamond Pattern Example

Consider a playbook where two agents depend on the same upstream agent:

```
    agent_a
    /     \
agent_b   agent_c
    \     /
    agent_d
```

**Without Caching**: agent_a would be executed twice (once for agent_b, once for agent_c)

**With Caching**:
1. agent_a executes → output cached
2. agent_b executes → receives cached output from agent_a
3. agent_c executes → receives cached output from agent_a (cache hit!)
4. agent_d executes → receives outputs from agent_b and agent_c

Result: agent_a executed once instead of twice, saving time and cost.

## Testing

Comprehensive unit tests verify all caching requirements:

```bash
python3 -m pytest infrastructure/lambda/orchestration/test_orchestrator_caching.py -v
```

Tests cover:
- ✅ Cache initialization
- ✅ Cache storage of agent outputs
- ✅ Cache hit avoids re-execution
- ✅ Cache hits logged correctly
- ✅ Shared dependencies use cache (diamond pattern)
- ✅ Cache cleared after completion
- ✅ Cache statistics in result
- ✅ Dependency outputs gathered from cache

All tests pass successfully.

## Integration

The Orchestrator class can be integrated into existing orchestration handlers:

```python
# In orchestrator_handler.py or query_handler_simple.py
from orchestrator import Orchestrator

def process_job(job_data):
    # Load playbook
    playbook = load_playbook(job_data["domain_id"], job_data["job_type"])
    
    # Create orchestrator with caching
    orchestrator = Orchestrator(
        job_id=job_data["job_id"],
        playbook=playbook,
        domain_id=job_data["domain_id"],
        tenant_id=job_data["tenant_id"],
        user_id=job_data.get("user_id")
    )
    
    # Execute with caching
    result = orchestrator.execute({
        "text": job_data.get("text") or job_data.get("question")
    })
    
    # Save results with execution log
    save_results(job_data["job_id"], result)
```

## Future Enhancements

Potential improvements for future iterations:

1. **Persistent Cache**: Store cache in Redis/DynamoDB for cross-job caching
2. **TTL-Based Cache**: Cache results for a time period (e.g., 5 minutes)
3. **Selective Caching**: Allow agents to opt-out of caching via configuration
4. **Cache Warming**: Pre-populate cache with common agent outputs
5. **Cache Metrics**: Track cache hit rates across all jobs for optimization

## Conclusion

The agent output caching implementation successfully meets all requirements (13.1-13.5) and provides significant performance and cost benefits for agent orchestration. The implementation is well-tested, documented, and ready for integration into the production system.
