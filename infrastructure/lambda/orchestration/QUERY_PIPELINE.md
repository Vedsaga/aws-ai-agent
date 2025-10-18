# Query Pipeline Implementation

## Overview

The query pipeline orchestrates multiple query agents to analyze stored data from different interrogative perspectives (When, Where, Why, How, What, Who, Which, etc.). It formats responses as bullet points with a synthesized summary and optional map visualizations.

## Architecture

The query pipeline reuses the core orchestration infrastructure with query-specific components:

### Core Components (Reused)
- **LoadPlaybook**: Loads query playbook configuration
- **LoadDependencyGraph**: Loads agent dependencies
- **BuildExecutionPlan**: Creates topological execution order
- **AgentInvoker**: Routes to specific query agents
- **ResultAggregator**: Collects agent outputs
- **Validator**: Validates agent outputs against schemas

### Query-Specific Components (New)
- **ResponseFormatter**: Formats agent outputs as bullet points
- **SummaryGenerator**: Synthesizes insights using Bedrock
- **VisualizationGenerator**: Creates map update instructions

## State Machine Flow

```
LoadQueryPlaybook
  ↓
LoadDependencyGraph
  ↓
BuildExecutionPlan
  ↓
ExecuteQueryAgents (Map state - parallel execution)
  ↓
AggregateResults
  ↓
ValidateOutputs
  ↓
FormatResponse (bullet points)
  ↓
GenerateSummary (Bedrock synthesis)
  ↓
GenerateVisualization (map updates)
  ↓
QuerySuccess
```

## Input Format

```json
{
  "job_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "domain_id": "civic-complaints",
  "question": "What are the trends in pothole complaints?",
  "playbook_type": "query"
}
```

## Output Format

```json
{
  "job_id": "uuid",
  "tenant_id": "uuid",
  "format_result": {
    "bullet_points": [
      "• What: Pothole complaints have increased 25% in the last month",
      "• Where: Most complaints concentrated in downtown area",
      "• When: Peak complaints occur on Monday mornings",
      "• Why: Recent heavy rainfall has worsened road conditions"
    ],
    "formatted_text": "..."
  },
  "summary_result": {
    "summary": "Pothole complaints show a 25% increase concentrated in downtown, peaking Monday mornings due to recent heavy rainfall.",
    "final_response": "• What: ...\n• Where: ...\n\nSummary: ..."
  },
  "visualization_result": {
    "visualization_config": {
      "has_spatial_data": true,
      "visualization_type": "heatmap",
      "heatmap": [...],
      "map_update": {
        "action": "update_view",
        "center": {"latitude": 40.7, "longitude": -74.0},
        "zoom": "auto"
      }
    }
  }
}
```

## Lambda Functions

### 1. Response Formatter (`response_formatter.py`)

**Purpose**: Format agent outputs as concise bullet points

**Key Features**:
- Maps interrogative types to prefixes (When:, Where:, etc.)
- Extracts key insights from agent outputs
- Limits each bullet to 1-2 lines (~150 chars)
- Preserves execution order

**Input Fields**:
- `insight`, `summary`, or `answer` from agent output
- Falls back to first 3 output values if not present

**Output**:
```json
{
  "bullet_points": ["• When: ...", "• Where: ..."],
  "bullet_count": 2,
  "formatted_text": "• When: ...\n• Where: ..."
}
```

### 2. Summary Generator (`summary_generator.py`)

**Purpose**: Synthesize all agent insights into 2-3 sentence summary

**Key Features**:
- Uses Bedrock (Claude 3 Sonnet) for synthesis
- Combines bullet points and full agent data
- Generates concise 2-3 sentence summary
- Combines bullets + summary into final response

**Bedrock Configuration**:
- Model: `anthropic.claude-3-sonnet-20240229-v1:0`
- Max tokens: 200
- Temperature: 0.3 (factual, consistent)

**Output**:
```json
{
  "summary": "Pothole complaints show a 25% increase...",
  "final_response": "• What: ...\n\nSummary: ...",
  "response_length": 450
}
```

### 3. Visualization Generator (`visualization_generator.py`)

**Purpose**: Generate map visualizations from spatial data

**Key Features**:
- Extracts coordinates from agent outputs
- Supports multiple coordinate formats (lat/lng, coordinates, location)
- Generates heatmap clusters for concentrations
- Calculates map bounds with padding
- Determines visualization type based on point count

**Visualization Types**:
- `marker`: Single point
- `markers`: 2-10 points
- `heatmap`: 11+ points (clustered)
- `none`: No spatial data

**Heatmap Clustering**:
- Groups points within ~1km (0.01 degrees)
- Calculates intensity based on point count
- Averages positions within cluster

**Output**:
```json
{
  "visualization_config": {
    "has_spatial_data": true,
    "visualization_type": "heatmap",
    "point_count": 45,
    "cluster_count": 8,
    "heatmap": [
      {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "intensity": 12,
        "point_count": 12
      }
    ],
    "bounds": {
      "min_latitude": 40.7,
      "max_latitude": 40.8,
      "center_latitude": 40.75,
      "center_longitude": -74.0
    },
    "map_update": {
      "action": "update_view",
      "center": {"latitude": 40.75, "longitude": -74.0},
      "zoom": "auto"
    }
  }
}
```

## Query Agent Requirements

Query agents must include specific output fields for proper formatting:

### Required Output Fields

**For Bullet Points**:
- `insight` (preferred): 1-2 sentence insight
- `summary` (fallback): Brief summary
- `answer` (fallback): Direct answer

**For Visualization**:
- `latitude` + `longitude`, OR
- `lat` + `lng`, OR
- `coordinates`: `[lat, lng]` or `{"lat": x, "lng": y}`, OR
- `location`: `{"latitude": x, "longitude": y}`

### Example Query Agent Output

```json
{
  "agent_name": "When Agent",
  "interrogative": "when",
  "output": {
    "insight": "Most complaints occur on Monday mornings between 7-9 AM",
    "time_pattern": "weekday_morning",
    "peak_hour": 8,
    "confidence": 0.85
  },
  "status": "success"
}
```

## Dependency Support

Query agents support single-level dependencies:

**Example**: Priority Scorer depends on Temporal Agent
```json
{
  "agent_id": "priority-scorer",
  "depends_on": "temporal-agent"
}
```

**Execution**:
1. Temporal Agent receives raw question text
2. Priority Scorer receives raw question + Temporal Agent output appended

## Integration with Frontend

### WebSocket Status Updates

The pipeline publishes real-time status via AppSync:

```javascript
subscription OnStatusUpdate($userId: ID!) {
  onStatusUpdate(userId: $userId) {
    jobId
    agentName
    status  // loading_agents, invoking, complete, error
    message
    timestamp
  }
}
```

### Response Display

Frontend should:
1. Display bullet points as formatted list
2. Show summary below bullets
3. Update map if `has_spatial_data: true`
4. Center map on `bounds.center`
5. Render heatmap or markers based on `visualization_type`

### Map Update Example

```javascript
if (response.visualization_result.visualization_config.has_spatial_data) {
  const config = response.visualization_result.visualization_config;
  
  // Update map center
  map.setCenter({
    lat: config.map_update.center.latitude,
    lng: config.map_update.center.longitude
  });
  
  // Render visualization
  if (config.visualization_type === 'heatmap') {
    renderHeatmap(config.heatmap);
  } else if (config.visualization_type === 'markers') {
    renderMarkers(config.markers);
  }
}
```

## Error Handling

### Partial Failures

If some query agents fail:
- Successful agents still generate bullet points
- Summary includes available insights
- Visualization uses available spatial data
- Failed agents logged but don't block pipeline

### Fallback Behavior

**Response Formatter**:
- Missing insight field → uses first 3 output values
- No interrogative → uses agent name as prefix

**Summary Generator**:
- Bedrock failure → generic fallback summary
- Empty bullet points → summary only

**Visualization Generator**:
- No spatial data → returns `visualization_type: none`
- Invalid coordinates → skips invalid points
- Single point → marker instead of heatmap

## Performance Considerations

### Parallel Execution

Query agents execute in parallel by default (MaxConcurrency: 10)

### Timeouts

- Agent execution: 5 minutes
- Response formatting: 30 seconds
- Summary generation: 30 seconds (Bedrock call)
- Visualization generation: 30 seconds

### Token Optimization

Summary generator limits context:
- First 5 agent outputs only
- Truncates long insights
- Max 200 tokens for summary

## Testing

### Unit Tests

Test each Lambda function independently:

```bash
# Response formatter
python -m pytest test_response_formatter.py

# Summary generator
python -m pytest test_summary_generator.py

# Visualization generator
python -m pytest test_visualization_generator.py
```

### Integration Test

Test full query pipeline:

```bash
# Start state machine execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:...:stateMachine:QueryPipeline \
  --input file://test_query_input.json

# Check execution status
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:...:execution:...
```

### Sample Test Input

```json
{
  "job_id": "test-job-123",
  "tenant_id": "test-tenant",
  "user_id": "test-user",
  "domain_id": "civic-complaints",
  "question": "What are the trends in pothole complaints?",
  "playbook_type": "query"
}
```

## Deployment

The query pipeline is deployed as part of the orchestration stack:

```typescript
// In orchestration-stack.ts
const queryStateMachine = new sfn.StateMachine(this, 'QueryPipeline', {
  definitionBody: sfn.DefinitionBody.fromFile(
    'lambda/orchestration/query_state_machine_definition.json'
  ),
  // ... Lambda function ARNs
});
```

## Requirements Satisfied

- ✅ **6.1**: Query pipeline routes to /api/v1/query endpoint
- ✅ **6.2**: Loads user's configured query playbook
- ✅ **6.5**: Passes raw question text to all agents, appends parent output to dependent agents
- ✅ **9.1**: Generates one bullet point per agent (1-2 lines)
- ✅ **9.2**: Aggregates bullet points in execution order
- ✅ **9.3**: Formats response as bullets + summary
- ✅ **9.4**: Uses Bedrock to synthesize 2-3 sentence summary
- ✅ **9.5**: Generates map visualizations for spatial data

## Next Steps

1. Deploy Lambda functions to AWS
2. Update orchestration stack with new functions
3. Create query playbook configurations
4. Implement query agents (When, Where, Why, etc.)
5. Test end-to-end query pipeline
6. Integrate with frontend chat interface
