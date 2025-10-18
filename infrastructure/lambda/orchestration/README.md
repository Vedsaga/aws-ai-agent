# Orchestration System

This directory contains the Lambda functions and Step Functions state machine for the Multi-Agent Orchestration System.

## Overview

The orchestration system coordinates the execution of multiple AI agents based on playbooks and dependency graphs. It handles:

- Loading playbook configurations
- Building execution plans with topological sort
- Parallel and sequential agent execution
- Result aggregation and validation
- Data synthesis and storage

## Components

### Lambda Functions

1. **load_playbook.py** - Loads playbook configuration from DynamoDB
2. **load_dependency_graph.py** - Loads dependency graph for agent execution order
3. **build_execution_plan.py** - Performs topological sort to create execution levels
4. **agent_invoker.py** - Routes execution to specific agents by ID
5. **result_aggregator.py** - Collects and aggregates agent outputs
6. **validator.py** - Validates outputs against schemas (max 5 keys)
7. **synthesizer.py** - Merges validated outputs into single document
8. **save_results.py** - Saves to RDS, OpenSearch, triggers events

### Step Functions State Machine

The state machine (`state_machine_definition.json`) orchestrates the entire pipeline:

```
LoadPlaybook → LoadDependencyGraph → BuildExecutionPlan → 
ExecuteAgents (Map) → AggregateResults → ValidateOutputs → 
SynthesizeResults → SaveResults → Success
```

## Execution Flow

### 1. Load Playbook
- Queries DynamoDB for playbook by domain_id and playbook_type
- Returns list of agent_ids to execute

### 2. Load Dependency Graph
- Queries DynamoDB for dependency edges
- Validates single-level dependencies (no multi-level chains)
- Filters edges to only include agents in playbook

### 3. Build Execution Plan
- Performs topological sort on agents and dependencies
- Creates execution levels (agents in same level run in parallel)
- Detects circular dependencies

### 4. Execute Agents (Map State)
- Executes agents in parallel within each level
- Passes raw_text to all agents
- Passes parent_output to dependent agents
- Handles agent failures gracefully

### 5. Aggregate Results
- Collects outputs from all agents
- Preserves execution order
- Separates successful and failed results
- Calculates statistics

### 6. Validate Outputs
- Loads output schemas from DynamoDB
- Validates max 5 keys constraint
- Validates against schema definitions
- Cross-validates consistency

### 7. Synthesize Results
- Merges validated outputs into single document
- Resolves conflicts (prefers specific agents for location, temporal data)
- Formats for database storage

### 8. Save Results
- Inserts structured data into RDS PostgreSQL
- Creates embeddings using Bedrock
- Indexes embeddings in OpenSearch
- Stores image metadata
- Triggers EventBridge event for map update

## Error Handling

### Retry Logic
- All Lambda tasks have 3 retry attempts with exponential backoff
- Agent invocations have 2 retry attempts

### Partial Failures
- System continues if some agents fail
- Failed agents are tracked in results
- Validation and synthesis work with partial data

### Error States
- Validation errors in playbook/graph → HandleError
- Circular dependencies → Fail
- All agents failed → Partial success with warnings

## Environment Variables

Required environment variables for Lambda functions:

```bash
AGENT_CONFIGS_TABLE=agent_configs
PLAYBOOK_CONFIGS_TABLE=playbook_configs
DEPENDENCY_GRAPHS_TABLE=dependency_graphs
DB_SECRET_ARN=arn:aws:secretsmanager:...
OPENSEARCH_ENDPOINT=https://...
EVENT_BUS_NAME=default
AGENT_LAMBDA_PREFIX=MultiAgentOrch-Agent-
```

## Deployment

The orchestration stack is deployed via CDK:

```typescript
import { OrchestrationStack } from './lib/stacks/orchestration-stack';

new OrchestrationStack(app, 'MultiAgentOrch-Orchestration', {
  agentConfigsTable: dataStack.agentConfigsTable,
  playbookConfigsTable: dataStack.playbookConfigsTable,
  dependencyGraphsTable: dataStack.dependencyGraphsTable,
  dbSecretArn: dataStack.dbSecretArn,
  opensearchEndpoint: dataStack.opensearchEndpoint,
  eventBusName: 'default',
});
```

## Testing

### Unit Testing
Test individual Lambda functions:

```bash
python -m pytest test_load_playbook.py
python -m pytest test_build_execution_plan.py
```

### Integration Testing
Test the full state machine:

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:... \
  --input file://test_input.json
```

### Test Input Example

```json
{
  "job_id": "test-job-123",
  "tenant_id": "tenant-456",
  "domain_id": "civic-complaints",
  "playbook_type": "ingestion",
  "raw_text": "Pothole on Main Street near the library",
  "images": [],
  "created_by": "user-789"
}
```

## Monitoring

### CloudWatch Metrics
- State machine execution duration
- Lambda function duration and errors
- Agent success/failure rates

### CloudWatch Logs
- State machine execution history
- Lambda function logs (structured JSON)
- Agent execution traces

### X-Ray Tracing
- End-to-end request tracing
- Performance bottleneck identification

## Performance

### Concurrency
- Map state supports up to 10 concurrent agent executions
- Adjust `MaxConcurrency` in state machine definition

### Timeouts
- Individual agents: 5 minutes
- State machine: 15 minutes
- Adjust based on workload

### Cost Optimization
- Use provisioned concurrency for critical functions
- Set appropriate memory sizes (256MB-512MB)
- Monitor Lambda duration and optimize

## Requirements

Implements requirements:
- 2.2: Domain selection and playbook loading
- 2.3: Agent execution routing
- 5.1: Output validation
- 5.2: Schema validation
- 5.3: Result synthesis
- 5.4: Database storage
- 5.5: Vector embedding and indexing
- 7.1: Playbook configuration
- 7.2: Dependency graph management
- 7.3: Execution plan with topological sort
- 7.4: Agent timeout handling
- 7.5: Result aggregation
