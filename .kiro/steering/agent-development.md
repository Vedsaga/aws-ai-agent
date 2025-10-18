---
inclusion: always
---

# Agent Development Guidelines

## Agent Structure

All agents must follow this standard structure:

```python
import json
import boto3
from typing import Dict, Any

class BaseAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bedrock = boto3.client('bedrock-runtime')
        self.system_prompt = config['system_prompt']
        self.tools = config['tools']
        self.output_schema = config['output_schema']
    
    def execute(self, raw_text: str, parent_output: Dict = None) -> Dict[str, Any]:
        # 1. Prepare input
        # 2. Call tools if needed
        # 3. Call Bedrock for analysis
        # 4. Validate output (max 5 keys)
        # 5. Return standardized format
        pass
```

## Output Requirements

- **Max 5 keys** in output JSON
- All keys must be defined in output_schema
- Include confidence scores where applicable
- Return None for missing data, not empty strings
- Always include execution_time_ms

## Tool Usage

- Check tool permissions before calling
- Handle tool failures gracefully
- Log all tool invocations
- Implement retries for transient failures
- Cache tool responses when appropriate

## Error Handling

- Catch all exceptions and return error status
- Include error message and stack trace in logs
- Never expose sensitive data in error messages
- Return partial results if some processing succeeded

## Bedrock Integration

- Use Claude 3 Sonnet model
- Set max_tokens appropriately (1000 for extraction, 200 for classification)
- Include system prompt and output schema in prompt
- Parse JSON response carefully
- Handle rate limits with exponential backoff

## Dependency Handling

- Check if parent_output is provided
- Append parent data to raw_text for context
- Never assume parent output structure
- Handle missing parent data gracefully

## Testing

- Test with various input formats
- Test with missing/malformed data
- Test tool failures
- Test timeout scenarios
- Verify output schema compliance

## Performance

- Minimize Bedrock API calls
- Use batch operations when possible
- Cache frequently accessed data
- Set appropriate Lambda memory based on workload
- Monitor cold start times
