"""
Custom Agent Framework

Supports user-defined agents with custom system prompts, tool selections,
output schemas, and single-level dependencies.
"""

import json
import logging
from typing import Dict, Any, Optional
from base_agent import BaseAgent, parse_json_from_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CustomAgent(BaseAgent):
    """
    Dynamically configured agent that executes user-defined logic.
    
    Supports:
    - User-defined system prompts
    - User-selected tools from registry
    - User-defined output schemas (max 5 keys)
    - Single-level dependency on one parent agent
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize custom agent with user configuration.
        
        Args:
            config: Configuration containing:
                - agent_name: Custom agent name
                - system_prompt: User-defined system prompt
                - tools: List of allowed tools
                - output_schema: User-defined schema (max 5 keys)
                - dependency_parent: Optional parent agent ID
        """
        # Validate output schema has max 5 keys
        output_schema = config.get('output_schema', {})
        if len(output_schema) > 5:
            raise ValueError(f"Output schema cannot exceed 5 keys, got {len(output_schema)}")
        
        # Validate single-level dependency
        dependency_parent = config.get('dependency_parent')
        if dependency_parent:
            logger.info(f"Custom agent depends on parent: {dependency_parent}")
        
        super().__init__(config)
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute custom agent logic based on user configuration.
        
        Args:
            raw_text: Raw input text
            parent_output: Optional output from parent agent (if dependency exists)
        
        Returns:
            Dict with custom output (max 5 keys)
        """
        logger.info(f"CustomAgent '{self.agent_name}' executing...")
        
        # Prepare input context
        context = raw_text
        
        # Append parent output if available (for dependency support)
        if parent_output:
            logger.info(f"Including parent output in context")
            context += f"\n\nParent Agent Output:\n{json.dumps(parent_output, indent=2)}"
        
        # Build prompt with output schema
        schema_description = self._format_schema_description()
        
        prompt = f"""Input: {context}

Based on the input above, provide analysis according to your role.

Return a JSON object with the following fields:
{schema_description}

Ensure all required fields are present and the output has exactly {len(self.output_schema)} keys.

JSON:"""
        
        try:
            # Invoke Bedrock with custom system prompt
            bedrock_response = self.invoke_bedrock(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5
            )
            
            # Parse JSON response
            output = parse_json_from_text(bedrock_response)
            
            # Ensure output matches schema
            validated_output = self._validate_and_format_output(output)
            
            logger.info(f"CustomAgent '{self.agent_name}' completed successfully")
            
            return validated_output
            
        except Exception as e:
            logger.error(f"CustomAgent '{self.agent_name}' execution failed: {str(e)}")
            # Return default output based on schema
            return self._get_default_output()
    
    def _format_schema_description(self) -> str:
        """Format output schema as human-readable description"""
        lines = []
        for key, schema in self.output_schema.items():
            key_type = schema.get('type', 'string')
            required = schema.get('required', False)
            req_str = '(required)' if required else '(optional)'
            lines.append(f"- {key}: {key_type} {req_str}")
        return '\n'.join(lines)
    
    def _validate_and_format_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate output against schema and format correctly.
        
        Args:
            output: Raw output from Bedrock
        
        Returns:
            Validated and formatted output
        """
        validated = {}
        
        for key, schema in self.output_schema.items():
            if key in output:
                validated[key] = output[key]
            elif schema.get('required', False):
                # Provide default for required missing fields
                key_type = schema.get('type', 'string')
                if key_type == 'number':
                    validated[key] = 0.0
                elif key_type == 'array':
                    validated[key] = []
                elif key_type == 'boolean':
                    validated[key] = False
                else:
                    validated[key] = 'unknown'
            else:
                # Optional field, set to None
                validated[key] = None
        
        return validated
    
    def _get_default_output(self) -> Dict[str, Any]:
        """Generate default output based on schema"""
        default = {}
        
        for key, schema in self.output_schema.items():
            key_type = schema.get('type', 'string')
            if key_type == 'number':
                default[key] = 0.0
            elif key_type == 'array':
                default[key] = []
            elif key_type == 'boolean':
                default[key] = False
            else:
                default[key] = 'error'
        
        return default


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Custom Agent.
    
    Args:
        event: Lambda event with agent configuration and input
        context: Lambda context
    
    Returns:
        Standardized agent output
    """
    # Get agent configuration from event
    agent_config = event.get('agent_config', {})
    
    # Validate required configuration
    if 'agent_name' not in agent_config:
        return {
            'agent_name': 'CustomAgent',
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': 'Missing agent_name in configuration'
        }
    
    if 'system_prompt' not in agent_config:
        return {
            'agent_name': agent_config['agent_name'],
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': 'Missing system_prompt in configuration'
        }
    
    if 'output_schema' not in agent_config:
        return {
            'agent_name': agent_config['agent_name'],
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': 'Missing output_schema in configuration'
        }
    
    # Ensure tools are specified
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']  # Default to Bedrock only
    
    try:
        # Create custom agent instance
        agent = CustomAgent(agent_config)
        
        # Execute with error handling
        return agent.handle_execution(event, context)
        
    except Exception as e:
        logger.error(f"Failed to create custom agent: {str(e)}")
        return {
            'agent_name': agent_config.get('agent_name', 'CustomAgent'),
            'output': {},
            'status': 'error',
            'execution_time_ms': 0,
            'error_message': f'Agent creation failed: {str(e)}'
        }
