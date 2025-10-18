# Agent Framework

This directory contains the implementation of all agents for the Multi-Agent Orchestration System.

## Architecture

All agents inherit from `BaseAgent` which provides:
- Standard input/output interface
- Tool invocation framework with access control
- Output schema validation (max 5 keys)
- Error handling and timeout management
- Bedrock integration for LLM capabilities

## Agent Types

### Ingestion Agents

Extract structured data from raw text input:

1. **GeoAgent** (`geo_agent.py`)
   - Extracts location information
   - Performs geocoding via Amazon Location Service
   - Web search fallback for ambiguous locations
   - Output: location_name, coordinates, address, confidence, location_type

2. **TemporalAgent** (`temporal_agent.py`)
   - Extracts time/date information
   - Parses relative expressions (today, yesterday, last week)
   - Converts to ISO timestamps
   - Output: timestamp, time_expression, time_type, confidence, timezone

3. **EntityAgent** (`entity_agent.py`)
   - Extracts named entities via AWS Comprehend
   - Performs sentiment analysis
   - Identifies key phrases
   - Categorizes content
   - Output: entities, sentiment, key_phrases, category, confidence

### Query Agents

Analyze data from interrogative perspectives (`query_agents.py`):

1. **WhenAgent** - Temporal analysis
2. **WhereAgent** - Spatial analysis
3. **WhyAgent** - Causal analysis
4. **HowAgent** - Method analysis
5. **WhatAgent** - Entity analysis
6. **WhoAgent** - Person analysis
7. **WhichAgent** - Selection analysis
8. **HowManyAgent** - Count analysis
9. **HowMuchAgent** - Quantity analysis
10. **FromWhereAgent** - Origin analysis
11. **WhatKindAgent** - Type analysis

Each query agent:
- Accepts natural language questions
- Provides 1-2 line insights from their perspective
- Supports single-level dependencies
- Output: insight, data_points, confidence, source, summary

### Custom Agents

**CustomAgent** (`custom_agent.py`)
- Dynamically configured with user-defined:
  - System prompts
  - Tool selections
  - Output schemas (max 5 keys)
  - Single-level dependencies
- Example: SeverityClassifier (pre-configured in seed data)

## Base Framework

**BaseAgent** (`base_agent.py`)
- Abstract base class for all agents
- Provides common functionality:
  - `invoke_bedrock()` - Call Claude 3 Sonnet
  - `invoke_tool()` - Call authorized tools with access control
  - `validate_output()` - Enforce max 5 keys constraint
  - `format_output()` - Standardize response format
  - `handle_execution()` - Main Lambda handler with error handling

## Tools

Agents can invoke the following tools (with access control):

- **bedrock** - AWS Bedrock (Claude 3 Sonnet)
- **comprehend** - AWS Comprehend (entities, sentiment, key phrases)
- **location** - Amazon Location Service (geocoding)
- **web_search** - External web search API
- **data_query** - Internal data retrieval APIs

## Output Schema

All agents must return output with **maximum 5 keys**. This constraint:
- Keeps responses focused and concise
- Reduces token usage
- Simplifies downstream processing
- Enforces clear agent responsibilities

## Dependency Support

Agents can declare a **single-level dependency** on one parent agent:
- Parent agent executes first
- Parent output is appended to child agent's input
- No multi-level chains allowed (prevents complexity)
- Example: SeverityClassifier depends on EntityAgent

## Error Handling

Agents implement comprehensive error handling:
- Tool invocation failures → graceful degradation
- Bedrock API errors → retry with exponential backoff
- Output validation errors → return default values
- Timeout management → check remaining Lambda time
- Structured logging → JSON format for CloudWatch

## Seed Data

`seed_data.json` contains pre-configured agents and playbooks:
- SeverityClassifier custom agent
- Civic Complaints ingestion playbook
- Dependency graph configuration
- Domain templates

## Testing

Use `agent_utils.py` for testing:

```python
from agent_utils import create_test_event, MockLambdaContext
from geo_agent import lambda_handler

# Create test event
event = create_test_event(
    raw_text="Pothole on Main Street",
    agent_config={
        'agent_name': 'GeoAgent',
        'tools': ['bedrock', 'location']
    }
)

# Create mock context
context = MockLambdaContext()

# Execute agent
result = lambda_handler(event, context)
print(result)
```

## Deployment

Each agent is deployed as a separate Lambda function:
- Runtime: Python 3.11
- Memory: 512 MB (agents), 256 MB (APIs)
- Timeout: 5 minutes (agents), 30 seconds (APIs)
- Environment variables: Bedrock model ID, region, etc.

## Dependencies

See `requirements.txt`:
- boto3 >= 1.28.0 (AWS SDK)
- botocore >= 1.31.0

## Lambda Handlers

Each agent file exports a `lambda_handler` function:
- `geo_agent.lambda_handler`
- `temporal_agent.lambda_handler`
- `entity_agent.lambda_handler`
- `query_agents.when_handler`, `where_handler`, etc.
- `custom_agent.lambda_handler`

## Configuration

Agents are configured via DynamoDB:
- Agent configurations table
- Playbook configurations table
- Dependency graph configurations table
- Tool permissions table

## Monitoring

All agents log to CloudWatch:
- Structured JSON logs
- Execution time metrics
- Tool invocation tracking
- Error rates and types

## Future Enhancements

- Add more built-in tools (S3, DynamoDB, etc.)
- Support for agent chaining (multi-step workflows)
- Agent performance optimization
- Caching layer for repeated queries
- A/B testing framework for agent prompts
