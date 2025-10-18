"""
Response Formatter Lambda Function

Collects query agent outputs and formats them as bullet points with interrogative prefixes.
Preserves execution order and generates concise 1-2 line insights per agent.

Requirements: 9.1, 9.2, 9.3
"""

import json
import os
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Interrogative prefix mapping
INTERROGATIVE_PREFIXES = {
    'when': 'When:',
    'where': 'Where:',
    'why': 'Why:',
    'how': 'How:',
    'what': 'What:',
    'who': 'Who:',
    'which': 'Which:',
    'how_many': 'How Many:',
    'how_much': 'How Much:',
    'from_where': 'From Where:',
    'what_kind': 'What Kind:'
}


def format_agent_output_as_bullet(
    agent_name: str,
    agent_output: Dict[str, Any],
    interrogative: str = None
) -> str:
    """
    Format a single agent's output as a bullet point (1-2 lines).
    
    Args:
        agent_name: Name of the agent
        agent_output: Agent's output dictionary
        interrogative: Interrogative type (when, where, why, etc.)
    
    Returns:
        Formatted bullet point string
    """
    # Get interrogative prefix
    prefix = INTERROGATIVE_PREFIXES.get(interrogative, f"{agent_name}:")
    
    # Extract key insights from agent output
    # Agents should provide a 'summary' or 'insight' field for bullet points
    if 'insight' in agent_output:
        insight = agent_output['insight']
    elif 'summary' in agent_output:
        insight = agent_output['summary']
    elif 'answer' in agent_output:
        insight = agent_output['answer']
    else:
        # Fallback: concatenate first few values
        values = []
        for key, value in list(agent_output.items())[:3]:
            if isinstance(value, (str, int, float)) and key not in ['confidence', 'execution_time_ms']:
                values.append(str(value))
        insight = ', '.join(values) if values else 'No insight available'
    
    # Ensure insight is concise (1-2 lines, max ~150 chars)
    if len(insight) > 150:
        insight = insight[:147] + '...'
    
    return f"• {prefix} {insight}"


def format_response(
    validated_results: List[Dict[str, Any]],
    execution_plan: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Format all query agent outputs as bullet points.
    
    Args:
        validated_results: List of validated agent outputs
        execution_plan: Execution plan with agent order
    
    Returns:
        Formatted response with bullet points
    """
    bullet_points = []
    agent_outputs = {}
    
    # Index validated results by agent_id
    for result in validated_results:
        agent_id = result.get('agent_id')
        if agent_id:
            agent_outputs[agent_id] = result
    
    # Process agents in execution order
    for plan_item in execution_plan:
        agent_id = plan_item.get('agent_id')
        
        if agent_id not in agent_outputs:
            logger.warning(f"Agent {agent_id} not found in validated results")
            continue
        
        result = agent_outputs[agent_id]
        agent_name = result.get('agent_name', agent_id)
        output = result.get('output', {})
        interrogative = result.get('interrogative')
        
        # Skip if agent failed or has no output
        if result.get('status') != 'success' or not output:
            logger.info(f"Skipping agent {agent_name} - status: {result.get('status')}")
            continue
        
        # Format as bullet point
        bullet = format_agent_output_as_bullet(agent_name, output, interrogative)
        bullet_points.append(bullet)
        
        logger.info(f"Formatted bullet for {agent_name}: {bullet[:50]}...")
    
    return {
        'bullet_points': bullet_points,
        'bullet_count': len(bullet_points),
        'formatted_text': '\n'.join(bullet_points)
    }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for response formatting.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "validated_results": [...],
        "execution_plan": [...]
    }
    
    Returns:
        Formatted response with bullet points
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        validated_results = event.get('validated_results', [])
        execution_plan = event.get('execution_plan', [])
        
        # Validate required fields
        if not all([job_id, tenant_id]):
            raise ValueError("Missing required fields: job_id or tenant_id")
        
        logger.info(
            f"Formatting response for job {job_id} with "
            f"{len(validated_results)} validated results"
        )
        
        # Format response
        formatted_response = format_response(validated_results, execution_plan)
        
        logger.info(
            f"Generated {formatted_response['bullet_count']} bullet points"
        )
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'bullet_points': formatted_response['bullet_points'],
            'bullet_count': formatted_response['bullet_count'],
            'formatted_text': formatted_response['formatted_text'],
            'status': 'success'
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'bullet_points': [],
            'bullet_count': 0,
            'formatted_text': '',
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error formatting response: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'bullet_points': [],
            'bullet_count': 0,
            'formatted_text': '',
            'status': 'error',
            'error_message': f"Response formatting error: {str(e)}"
        }
