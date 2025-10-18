# Agent Framework Quick Start Guide

## Directory Structure

```
infrastructure/lambda/agents/
├── base_agent.py           # Base class for all agents
├── geo_agent.py            # Location extraction agent
├── temporal_agent.py       # Time/date extraction agent
├── entity_agent.py         # Entity & sentiment analysis agent
├── query_agents.py         # 11 interrogative query agents
├── custom_agent.py         # Custom agent framework
├── agent_utils.py          # Helper utilities
├── seed_data.json          # Pre-configured agents & playbooks
├── requirements.txt        # Python dependencies
├── README.md               # Full documentation
├── IMPLEMENTATION_SUMMARY.md  # Implementation details
└── QUICK_START.md          # This file
```

## Creating a New Agent

### Step 1: Inherit from BaseAgent

```python
from base_agent import BaseAgent
from typing import Dict, Any, Optional

class MyCustomAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        # Set default output schema (max 5 keys!)
        if 'output_schema' not in config:
            config['output_schema'] = {
                'key1': {'type': 'string', 'required': True},
                'key2': {'type': 'number', 'required': True},
                'key3': {'type': 'array', 'required': False},
                'key4': {'type': 'string', 'required': False},
                'key5': {'type': 'boolean', 'required': False}
            }
        
        # Set default system prompt
        if 'system_prompt' not in config:
            config['system_prompt'] = "Your agent's role and instructions"
        
        super().__init__(config)
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        # Your agent logic here
        
        # Use Bedrock for LLM analysis
        response = self.invoke_bedrock(
            prompt=f"Analyze: {raw_text}",
            max_tokens=500,
            temperature=0.5
        )
        
        # Use tools if needed
        if 'comprehend' in self.tools:
            result = self.invoke_tool('comprehend', {'text': raw_text})
        
        # Return output (max 5 keys!)
        return {
            'key1': 'value1',
            'key2': 42,
            'key3': ['item1', 'item2'],
            'key4': 'value4',
            'key5': True
        }
```

### Step 2: Create Lambda Handler

```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'MyCustomAgent'
    
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock', 'comprehend']
    
    agent = MyCustomAgent(agent_config)
    return agent.handle_execution(event, context)
```

## Using Existing Agents

### Ingestion Agents

```python
# GeoAgent - Extract location
from geo_agent import lambda_handler as geo_handler

event = {
    'job_id': 'test-123',
    'tenant_id': 'tenant-456',
    'raw_text': 'Pothole on Main Street near City Hall',
    'agent_config': {
        'agent_name': 'GeoAgent',
        'tools': ['bedrock', 'location', 'web_search']
    }
}

result = geo_handler(event, context)
# Output: location_name, coordinates, address, confidence, location_type
```

```python
# TemporalAgent - Extract time
from temporal_agent import lambda_handler as temporal_handler

event = {
    'raw_text': 'I saw this yesterday around 3pm',
    'agent_config': {'agent_name': 'TemporalAgent'}
}

result = temporal_handler(event, context)
# Output: timestamp, time_expression, time_type, confidence, timezone
```

```python
# EntityAgent - Extract entities & sentiment
from entity_agent import lambda_handler as entity_handler

event = {
    'raw_text': 'The mayor needs to fix the broken streetlight',
    'agent_config': {'agent_name': 'EntityAgent', 'tools': ['bedrock', 'comprehend']}
}

result = entity_handler(event, context)
# Output: entities, sentiment, key_phrases, category, confidence
```

### Query Agents

```python
from query_agents import when_handler, where_handler, why_handler

# When Agent - Temporal analysis
event = {
    'raw_text': 'What are the trends in pothole complaints?',
    'agent_config': {'agent_name': 'WhenAgent'}
}

result = when_handler(event, context)
# Output: insight, data_points, confidence, source, summary
```

### Custom Agents

```python
from custom_agent import lambda_handler as custom_handler

# Load SeverityClassifier from seed data
import json
with open('seed_data.json') as f:
    seed_data = json.load(f)

severity_config = seed_data['custom_agents'][0]  # SeverityClassifier

event = {
    'raw_text': 'Major gas leak on 5th Avenue',
    'parent_output': {  # From EntityAgent
        'entities': [{'text': 'gas leak', 'type': 'EVENT'}],
        'sentiment': 'NEGATIVE',
        'category': 'safety'
    },
    'agent_config': severity_config
}

result = custom_handler(event, context)
# Output: severity_score, severity_level, risk_factors, urgency, reasoning
```

## Key Concepts

### 1. Output Schema (Max 5 Keys)

**Why?** Keeps agents focused, reduces token usage, simplifies processing.

```python
# ✓ GOOD - 5 keys
output = {
    'location': 'Main Street',
    'coordinates': [40.7, -74.0],
    'confidence': 0.9,
    'type': 'street',
    'address': '123 Main St'
}

# ✗ BAD - 6 keys (will fail validation)
output = {
    'location': 'Main Street',
    'coordinates': [40.7, -74.0],
    'confidence': 0.9,
    'type': 'street',
    'address': '123 Main St',
    'extra_key': 'not allowed'  # 6th key!
}
```

### 2. Single-Level Dependencies

**Why?** Prevents complexity, ensures predictable execution order.

```python
# ✓ GOOD - Single parent
# EntityAgent → SeverityClassifier

# ✗ BAD - Multiple parents
# EntityAgent → SeverityClassifier
# GeoAgent → SeverityClassifier  # Not allowed!

# ✗ BAD - Multi-level chain
# EntityAgent → SeverityClassifier → PriorityAgent  # Not allowed!
```

### 3. Tool Access Control

Agents must declare tools in configuration:

```python
agent_config = {
    'agent_name': 'MyAgent',
    'tools': ['bedrock', 'comprehend', 'location']  # Only these allowed
}

# This will work
self.invoke_tool('comprehend', {...})

# This will fail (not in tools list)
self.invoke_tool('web_search', {...})  # ToolInvocationError
```

### 4. Error Handling

All errors are caught and returned in standardized format:

```python
{
    'agent_name': 'GeoAgent',
    'output': {},  # Empty on error
    'status': 'error',
    'execution_time_ms': 1234,
    'error_message': 'Tool invocation failed: ...'
}
```

## Testing Locally

```python
from agent_utils import create_test_event, MockLambdaContext

# Create test event
event = create_test_event(
    raw_text="Test input",
    agent_config={
        'agent_name': 'TestAgent',
        'system_prompt': 'Test prompt',
        'tools': ['bedrock'],
        'output_schema': {
            'result': {'type': 'string', 'required': True}
        }
    }
)

# Create mock context
context = MockLambdaContext(timeout_ms=300000)

# Run agent
from geo_agent import lambda_handler
result = lambda_handler(event, context)

print(result)
```

## Deployment Checklist

- [ ] Create Lambda function in CDK
- [ ] Set runtime to Python 3.11
- [ ] Set memory to 512 MB (agents) or 256 MB (APIs)
- [ ] Set timeout to 5 minutes (agents) or 30 seconds (APIs)
- [ ] Add IAM role with permissions:
  - [ ] Bedrock InvokeModel
  - [ ] Comprehend DetectEntities, DetectSentiment, DetectKeyPhrases
  - [ ] Location SearchPlaceIndexForText
  - [ ] CloudWatch Logs
- [ ] Set environment variables:
  - [ ] BEDROCK_MODEL_ID
  - [ ] AWS_REGION
- [ ] Deploy seed data to DynamoDB
- [ ] Test with sample events

## Common Issues

### Issue: "No module named 'boto3'"
**Solution:** boto3 is included in Lambda runtime, no need to package it.

### Issue: "Output has 6 keys, maximum is 5"
**Solution:** Reduce output schema to 5 keys or fewer.

### Issue: "Tool 'xyz' not authorized"
**Solution:** Add tool to agent's tools list in configuration.

### Issue: "Circular dependency detected"
**Solution:** Check dependency graph, remove circular references.

### Issue: "Multi-level dependency not allowed"
**Solution:** Each agent can have max 1 parent. Flatten dependency chain.

## Next Steps

1. Review `README.md` for full documentation
2. Check `IMPLEMENTATION_SUMMARY.md` for implementation details
3. Examine `seed_data.json` for configuration examples
4. Run `verify_structure.py` to validate setup
5. Deploy to AWS Lambda
6. Test with Step Functions orchestrator

## Support

For questions or issues:
1. Check `README.md` for detailed documentation
2. Review agent code for implementation examples
3. Examine `seed_data.json` for configuration patterns
4. Use `agent_utils.py` helper functions
