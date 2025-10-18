"""
Temporal Agent - Time and Date Extraction

Extracts temporal information from text and converts to ISO timestamps.
Handles relative time expressions (today, yesterday, last week, etc.).
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from base_agent import BaseAgent, parse_json_from_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TemporalAgent(BaseAgent):
    """
    Agent for extracting and normalizing temporal information.
    
    Output Schema (max 5 keys):
    - timestamp: ISO 8601 timestamp
    - time_expression: Original time expression from text
    - time_type: Type (absolute, relative, range)
    - confidence: Confidence score (0-1)
    - timezone: Timezone if specified
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Set default output schema if not provided
        if 'output_schema' not in config:
            config['output_schema'] = {
                'timestamp': {'type': 'string', 'required': True},
                'time_expression': {'type': 'string', 'required': True},
                'time_type': {'type': 'string', 'required': True},
                'confidence': {'type': 'number', 'required': True},
                'timezone': {'type': 'string', 'required': False}
            }
        
        # Set default system prompt if not provided
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a temporal information extraction specialist.
Your task is to identify and extract time/date information from text.

Extract the following information:
1. time_expression: The exact time/date phrase from the text
2. time_type: Classification (absolute, relative, range, recurring)
3. confidence: Your confidence in the extraction (0.0 to 1.0)
4. timezone: Timezone if mentioned (or null)

For relative expressions like "today", "yesterday", "last week", identify them clearly.
Return ONLY a JSON object with these fields."""
        
        super().__init__(config)
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract temporal information from text and convert to ISO timestamp.
        
        Args:
            raw_text: Raw input text
            parent_output: Not used for this agent
        
        Returns:
            Dict with temporal information (max 5 keys)
        """
        logger.info(f"TemporalAgent processing text: {raw_text[:100]}...")
        
        # Get current time for relative calculations
        current_time = datetime.utcnow()
        
        # Step 1: Use Bedrock to extract temporal information
        prompt = f"""Extract temporal information from the following text:

Text: {raw_text}

Current date/time for reference: {current_time.isoformat()}

Return a JSON object with:
- time_expression: The time/date phrase from the text
- time_type: Type (absolute, relative, range, recurring)
- confidence: Your confidence score (0.0 to 1.0)
- timezone: Timezone if mentioned (or null)

JSON:"""
        
        try:
            bedrock_response = self.invoke_bedrock(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse JSON from response
            temporal_data = parse_json_from_text(bedrock_response)
            
            # Extract fields
            time_expression = temporal_data.get('time_expression', 'unknown')
            time_type = temporal_data.get('time_type', 'unknown')
            confidence = float(temporal_data.get('confidence', 0.0))
            timezone = temporal_data.get('timezone')
            
            # Step 2: Convert to ISO timestamp
            timestamp = self._parse_time_expression(
                time_expression,
                time_type,
                current_time
            )
            
            # Step 3: Format output (max 5 keys)
            output = {
                'timestamp': timestamp,
                'time_expression': time_expression,
                'time_type': time_type,
                'confidence': confidence,
                'timezone': timezone
            }
            
            logger.info(
                f"TemporalAgent extracted time: {time_expression} -> {timestamp} "
                f"(confidence: {confidence})"
            )
            
            return output
            
        except Exception as e:
            logger.error(f"TemporalAgent execution failed: {str(e)}")
            # Return current time as default
            return {
                'timestamp': current_time.isoformat() + 'Z',
                'time_expression': 'now',
                'time_type': 'relative',
                'confidence': 0.5,
                'timezone': 'UTC'
            }
    
    def _parse_time_expression(
        self,
        expression: str,
        time_type: str,
        reference_time: datetime
    ) -> str:
        """
        Parse time expression and convert to ISO timestamp.
        
        Args:
            expression: Time expression from text
            time_type: Type of time expression
            reference_time: Reference datetime for relative calculations
        
        Returns:
            ISO 8601 timestamp string
        """
        expression_lower = expression.lower()
        
        # Handle relative expressions
        if time_type == 'relative':
            if 'today' in expression_lower or 'now' in expression_lower:
                return reference_time.isoformat() + 'Z'
            
            elif 'yesterday' in expression_lower:
                result_time = reference_time - timedelta(days=1)
                return result_time.isoformat() + 'Z'
            
            elif 'last week' in expression_lower or 'a week ago' in expression_lower:
                result_time = reference_time - timedelta(weeks=1)
                return result_time.isoformat() + 'Z'
            
            elif 'last month' in expression_lower or 'a month ago' in expression_lower:
                result_time = reference_time - timedelta(days=30)
                return result_time.isoformat() + 'Z'
            
            elif 'last year' in expression_lower or 'a year ago' in expression_lower:
                result_time = reference_time - timedelta(days=365)
                return result_time.isoformat() + 'Z'
            
            elif 'tomorrow' in expression_lower:
                result_time = reference_time + timedelta(days=1)
                return result_time.isoformat() + 'Z'
            
            elif 'next week' in expression_lower:
                result_time = reference_time + timedelta(weeks=1)
                return result_time.isoformat() + 'Z'
        
        # For absolute times, try to parse common formats
        # This is a simplified parser - production would use dateutil
        try:
            # Try ISO format
            if 'T' in expression or '-' in expression:
                parsed = datetime.fromisoformat(expression.replace('Z', '+00:00'))
                return parsed.isoformat() + 'Z'
        except:
            pass
        
        # Default to reference time if parsing fails
        return reference_time.isoformat() + 'Z'


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Temporal Agent.
    
    Args:
        event: Lambda event with agent configuration and input
        context: Lambda context
    
    Returns:
        Standardized agent output
    """
    # Get agent configuration from event or use defaults
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'TemporalAgent'
    
    # Ensure required tools are available
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    # Create agent instance
    agent = TemporalAgent(agent_config)
    
    # Execute with error handling
    return agent.handle_execution(event, context)
