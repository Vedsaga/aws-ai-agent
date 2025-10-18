# Diagram 03: Unified Orchestrator Deep Dive

## Purpose
This diagram shows the AWS Step Functions orchestrator that handles both ingestion and query pipelines with dependency graph execution.

## AWS Services Used
- AWS Step Functions (State Machine)
- AWS Lambda (Agent functions)
- Amazon DynamoDB (Configuration Store)
- AWS AppSync (Status broadcasting)

## Diagram

```mermaid
flowchart TB
    subgraph Trigger["Trigger Sources"]
        IngestAPI["POST /ingest<br/>Lambda Handler"]
        QueryAPI["POST /query<br/>Lambda Handler"]
    end
    
    subgraph StepFunctions["AWS Step Functions State Machine"]
        StartState["Start<br/>Receive job_id, tenant_id, type"]
        
        LoadPlaybook["Load Playbook<br/>Lambda: Get from DynamoDB"]
        
        LoadDepGraph["Load Dependency Graph<br/>Lambda: Get from DynamoDB"]
        
        PublishLoading["Publish Status<br/>Lambda: AppSync mutation<br/>Status: loading_agents"]
        
        BuildExecPlan["Build Execution Plan<br/>Lambda: Topological sort<br/>Parallel + Sequential groups"]
        
        ExecParallelGroup["Execute Parallel Group<br/>Map State: Invoke agents"]
        
        CheckDependencies["Check Dependencies<br/>Choice State"]
        
        WaitForParent["Wait for Parent<br/>Wait State: Poll parent status"]
        
        ExecDependentAgent["Execute Dependent Agent<br/>Task State: Invoke Lambda"]
        
        PublishAgentStatus["Publish Agent Status<br/>Lambda: AppSync mutation<br/>Status: agent_complete"]
        
        AllAgentsComplete["All Agents Complete?<br/>Choice State"]
        
        AggregateResults["Aggregate Results<br/>Lambda: Collect outputs"]
        
        ValidateOutputs["Validate Outputs<br/>Lambda: Schema validation"]
        
        PublishValidating["Publish Status<br/>Lambda: AppSync mutation<br/>Status: validating"]
        
        SynthesizeResults["Synthesize Results<br/>Lambda: Merge into JSON"]
        
        PublishSynthesizing["Publish Status<br/>Lambda: AppSync mutation<br/>Status: synthesizing"]
        
        SaveResults["Save Results<br/>Lambda: Store in RDS/OpenSearch"]
        
        PublishComplete["Publish Status<br/>Lambda: AppSync mutation<br/>Status: complete"]
        
        EndState["End<br/>Return job_id, status"]
        
        ErrorHandler["Error Handler<br/>Catch State"]
        PublishError["Publish Error<br/>Lambda: AppSync mutation<br/>Status: error"]
    end
    
    subgraph ConfigStore["DynamoDB Configuration Store"]
        PlaybookTable[("playbook_configs<br/>PK tenant_id<br/>SK playbook_id")]
        DepGraphTable[("dependency_graphs<br/>PK tenant_id<br/>SK graph_id")]
        AgentTable[("agent_configs<br/>PK tenant_id<br/>SK agent_id")]
    end
    
    subgraph AgentExecution["Agent Execution Layer"]
        AgentLambda1["Agent Lambda 1<br/>Parallel execution"]
        AgentLambda2["Agent Lambda 2<br/>Parallel execution"]
        AgentLambda3["Agent Lambda 3<br/>Depends on Agent 1"]
    end
    
    subgraph StatusBroadcast["Real-Time Status"]
        AppSync["AWS AppSync<br/>WebSocket broadcast"]
    end
    
    %% Flow
    IngestAPI -->|StartExecution| StartState
    QueryAPI -->|StartExecution| StartState
    
    StartState --> LoadPlaybook
    LoadPlaybook -->|Query DynamoDB| PlaybookTable
    PlaybookTable -->|Return agent_ids| LoadDepGraph
    
    LoadDepGraph -->|Query DynamoDB| DepGraphTable
    DepGraphTable -->|Return edges list| PublishLoading
    
    PublishLoading -->|Broadcast| AppSync
    PublishLoading --> BuildExecPlan
    
    BuildExecPlan -->|Group agents| ExecParallelGroup
    
    ExecParallelGroup -->|Invoke| AgentLambda1
    ExecParallelGroup -->|Invoke| AgentLambda2
    
    AgentLambda1 -->|Output| PublishAgentStatus
    AgentLambda2 -->|Output| PublishAgentStatus
    
    PublishAgentStatus -->|Broadcast| AppSync
    PublishAgentStatus --> CheckDependencies
    
    CheckDependencies -->|Has dependent agents| WaitForParent
    CheckDependencies -->|No dependencies| AllAgentsComplete
    
    WaitForParent -->|Parent complete| ExecDependentAgent
    ExecDependentAgent -->|Invoke with parent output| AgentLambda3
    AgentLambda3 -->|Output| PublishAgentStatus
    
    AllAgentsComplete -->|More agents| ExecParallelGroup
    AllAgentsComplete -->|All complete| AggregateResults
    
    AggregateResults --> ValidateOutputs
    ValidateOutputs --> PublishValidating
    PublishValidating -->|Broadcast| AppSync
    PublishValidating --> SynthesizeResults
    
    SynthesizeResults --> PublishSynthesizing
    PublishSynthesizing -->|Broadcast| AppSync
    PublishSynthesizing --> SaveResults
    
    SaveResults --> PublishComplete
    PublishComplete -->|Broadcast| AppSync
    PublishComplete --> EndState
    
    %% Error Handling
    LoadPlaybook -.->|Error| ErrorHandler
    LoadDepGraph -.->|Error| ErrorHandler
    ExecParallelGroup -.->|Error| ErrorHandler
    ValidateOutputs -.->|Error| ErrorHandler
    SynthesizeResults -.->|Error| ErrorHandler
    SaveResults -.->|Error| ErrorHandler
    
    ErrorHandler --> PublishError
    PublishError -->|Broadcast| AppSync
    PublishError --> EndState

    classDef triggerBox fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef stepFnBox fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    classDef configBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef agentBox fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef statusBox fill:#e0f7fa,stroke:#00838f,stroke-width:2px
    
    class IngestAPI,QueryAPI triggerBox
    class StartState,LoadPlaybook,LoadDepGraph,PublishLoading,BuildExecPlan,ExecParallelGroup,CheckDependencies,WaitForParent,ExecDependentAgent,PublishAgentStatus,AllAgentsComplete,AggregateResults,ValidateOutputs,PublishValidating,SynthesizeResults,PublishSynthesizing,SaveResults,PublishComplete,EndState,ErrorHandler,PublishError stepFnBox
    class PlaybookTable,DepGraphTable,AgentTable configBox
    class AgentLambda1,AgentLambda2,AgentLambda3 agentBox
    class AppSync statusBox
```

## Component Descriptions

### AWS Step Functions State Machine

**State Machine Type**: Standard (for long-running workflows)

**Execution Role**: Permissions to invoke Lambda, read DynamoDB, publish to AppSync

**Timeout**: 15 minutes (max agent execution time)

**Retry Strategy**:
- Agent invocation: 3 retries with exponential backoff
- DynamoDB queries: 2 retries with exponential backoff
- AppSync mutations: 2 retries

### State Definitions

**Start State (Pass)**
- Receives input: `{ "job_id", "tenant_id", "type": "ingestion|query", "data": {...} }`
- Adds timestamp and execution ARN to context

**Load Playbook (Task - Lambda)**
- Function: `LoadPlaybookFunction`
- Input: `{ "tenant_id", "domain_id", "type": "ingestion|query" }`
- Output: `{ "agent_ids": ["agent1", "agent2", ...] }`
- Timeout: 5 seconds

**Load Dependency Graph (Task - Lambda)**
- Function: `LoadDependencyGraphFunction`
- Input: `{ "tenant_id", "playbook_id" }`
- Output: `{ "edges": [{"from": "agent1", "to": "agent2"}] }`
- Timeout: 5 seconds

**Build Execution Plan (Task - Lambda)**
- Function: `BuildExecutionPlanFunction`
- Algorithm: Topological sort with level grouping
- Input: `{ "agent_ids", "edges" }`
- Output: `{ "levels": [[agent1, agent2], [agent3]] }`
- Timeout: 10 seconds

**Execute Parallel Group (Map State)**
- Iterator: Agent invocation
- Max Concurrency: 10 agents
- Input: `{ "agent_id", "raw_data", "parent_output": null }`
- Output: Array of agent outputs

**Check Dependencies (Choice State)**
- Condition: Check if agent has `dependency_parent` in config
- Branch 1: Has dependency → Wait for Parent
- Branch 2: No dependency → Continue

**Wait for Parent (Wait State)**
- Wait type: Dynamic (based on parent execution time)
- Max wait: 5 minutes
- Poll interval: 5 seconds

**Execute Dependent Agent (Task - Lambda)**
- Function: Agent Lambda (dynamic)
- Input: `{ "agent_id", "raw_data", "parent_output": {...} }`
- Output: Agent output
- Timeout: 5 minutes

**Aggregate Results (Task - Lambda)**
- Function: `AggregateResultsFunction`
- Input: Array of agent outputs
- Output: `{ "aggregated": {...} }`
- Timeout: 10 seconds

**Validate Outputs (Task - Lambda)**
- Function: `ValidateOutputsFunction`
- Validation: Check against output schemas (max 5 keys)
- Input: `{ "aggregated", "schemas": [...] }`
- Output: `{ "valid": true/false, "errors": [...] }`
- Timeout: 10 seconds

**Synthesize Results (Task - Lambda)**
- Function: `SynthesizeResultsFunction`
- Purpose: Merge agent outputs into coherent JSON
- Input: `{ "aggregated" }`
- Output: `{ "synthesized": {...} }`
- Timeout: 10 seconds

**Save Results (Task - Lambda)**
- Function: `SaveResultsFunction`
- Actions: Store in RDS, create embeddings, save to OpenSearch
- Input: `{ "synthesized", "job_id", "tenant_id" }`
- Output: `{ "incident_id", "status": "saved" }`
- Timeout: 30 seconds

**Error Handler (Catch State)**
- Catches: All errors (States.ALL)
- ResultPath: `$.error`
- Next: PublishError

### Execution Plan Algorithm

**Topological Sort with Level Grouping:**

```python
def build_execution_plan(agent_ids, edges):
    # Build adjacency list
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    for edge in edges:
        graph[edge['from']].append(edge['to'])
        in_degree[edge['to']] += 1
    
    # Find agents with no dependencies (level 0)
    levels = []
    current_level = [agent for agent in agent_ids if in_degree[agent] == 0]
    
    while current_level:
        levels.append(current_level)
        next_level = []
        
        for agent in current_level:
            for neighbor in graph[agent]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_level.append(neighbor)
        
        current_level = next_level
    
    return levels  # [[agent1, agent2], [agent3], [agent4, agent5]]
```

**Example:**
- Agents: A, B, C, D, E
- Dependencies: C depends on A, D depends on B, E depends on C
- Execution Plan:
  - Level 0: [A, B] (parallel)
  - Level 1: [C, D] (parallel, wait for level 0)
  - Level 2: [E] (wait for C)

### Status Broadcasting

**AppSync Mutations:**

```graphql
mutation PublishStatus($input: StatusInput!) {
  publishStatus(input: $input) {
    jobId
    status
    message
    timestamp
  }
}
```

**Status Types:**
- `loading_agents`: Orchestrator loading configuration
- `invoking_{agent_name}`: Starting agent execution
- `agent_complete_{agent_name}`: Agent finished
- `validating`: Validation in progress
- `synthesizing`: Synthesis in progress
- `complete`: Job finished successfully
- `error`: Job failed

### Error Handling Strategy

**Retry Logic:**
- Agent timeout: Retry 3 times with 2x backoff (2s, 4s, 8s)
- DynamoDB throttling: Retry 2 times with 1.5x backoff
- AppSync errors: Retry 2 times, continue on failure (non-blocking)

**Partial Success:**
- If some agents fail, continue with successful outputs
- Mark failed agents in final result
- Include error messages in synthesis

**Dead Letter Queue:**
- Failed executions sent to SQS DLQ
- CloudWatch alarm on DLQ depth > 10
- Manual review and retry

### Performance Optimization

**Parallel Execution:**
- Agents in same level execute concurrently
- Max 10 concurrent Lambda invocations
- Reduces total execution time by ~60%

**Caching:**
- Playbook configurations cached in Lambda memory (5 min TTL)
- Dependency graphs cached in Lambda memory (5 min TTL)
- Agent configurations loaded once per execution

**Async Status Updates:**
- AppSync mutations non-blocking
- Failures don't stop execution
- Logged for debugging

## State Machine Definition (JSON)

```json
{
  "Comment": "Unified Orchestrator for Ingestion and Query Pipelines",
  "StartAt": "LoadPlaybook",
  "States": {
    "LoadPlaybook": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:LoadPlaybookFunction",
      "TimeoutSeconds": 5,
      "Retry": [
        {
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 2,
          "MaxAttempts": 2,
          "BackoffRate": 1.5
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ErrorHandler"
        }
      ],
      "Next": "LoadDependencyGraph"
    },
    "LoadDependencyGraph": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:LoadDependencyGraphFunction",
      "TimeoutSeconds": 5,
      "Next": "PublishLoadingStatus"
    },
    "PublishLoadingStatus": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:PublishStatusFunction",
      "Parameters": {
        "status": "loading_agents"
      },
      "Next": "BuildExecutionPlan"
    },
    "BuildExecutionPlan": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:BuildExecutionPlanFunction",
      "TimeoutSeconds": 10,
      "Next": "ExecuteAgentLevels"
    },
    "ExecuteAgentLevels": {
      "Type": "Map",
      "ItemsPath": "$.levels",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "InvokeAgent",
        "States": {
          "InvokeAgent": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:AgentInvokerFunction",
            "TimeoutSeconds": 300,
            "Retry": [
              {
                "ErrorEquals": ["States.Timeout"],
                "IntervalSeconds": 2,
                "MaxAttempts": 3,
                "BackoffRate": 2.0
              }
            ],
            "End": true
          }
        }
      },
      "Next": "AggregateResults"
    },
    "AggregateResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:AggregateResultsFunction",
      "Next": "ValidateOutputs"
    },
    "ValidateOutputs": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:ValidateOutputsFunction",
      "Next": "SynthesizeResults"
    },
    "SynthesizeResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:SynthesizeResultsFunction",
      "Next": "SaveResults"
    },
    "SaveResults": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:SaveResultsFunction",
      "TimeoutSeconds": 30,
      "Next": "PublishCompleteStatus"
    },
    "PublishCompleteStatus": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:PublishStatusFunction",
      "Parameters": {
        "status": "complete"
      },
      "End": true
    },
    "ErrorHandler": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:PublishStatusFunction",
      "Parameters": {
        "status": "error"
      },
      "End": true
    }
  }
}
```
