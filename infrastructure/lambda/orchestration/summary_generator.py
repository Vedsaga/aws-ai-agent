"""
Summary Generator Lambda Function

Uses Bedrock to synthesize all query agent insights into a 2-3 sentence summary.
Combines bullet points and summary into final response.

Requirements: 9.3, 9.4
"""

import json
import os
import logging
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime')

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')


def generate_summary_with_bedrock(
    question: str,
    bullet_points: List[str],
    validated_results: List[Dict[str, Any]]
) -> str:
    """
    Generate a 2-3 sentence summary using Bedrock.
    
    Args:
        question: Original user question
        bullet_points: Formatted bullet points from agents
        validated_results: Full agent outputs for context
    
    Returns:
        Summary text (2-3 sentences)
    """
    # Prepare context from agent outputs
    agent_insights = []
    for result in validated_results:
        if result.get('status') == 'success':
            agent_name = result.get('agent_name', 'Unknown')
            output = result.get('output', {})
            agent_insights.append(f"{agent_name}: {json.dumps(output)}")
    
    # Build prompt for summary generation
    system_prompt = """You are a data analyst synthesizing insights from multiple AI agents.
Your task is to create a concise 2-3 sentence summary that answers the user's question
by combining insights from all agents. Focus on the most important findings and patterns.
Be direct and factual. Do not use phrases like "Based on the analysis" or "The agents found".
Just state the key findings clearly."""

    user_prompt = f"""Question: {question}

Agent Insights:
{chr(10).join(bullet_points)}

Full Agent Data:
{chr(10).join(agent_insights[:5])}  # Limit to first 5 to avoid token limits

Generate a 2-3 sentence summary that directly answers the question by synthesizing these insights."""

    try:
        # Call Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract summary text
        summary = response_body.get('content', [{}])[0].get('text', '')
        
        # Clean up summary
        summary = summary.strip()
        
        # Ensure it's not too long (max ~300 chars for 2-3 sentences)
        if len(summary) > 300:
            # Truncate at last sentence boundary
            sentences = summary.split('. ')
            summary = '. '.join(sentences[:3])
            if not summary.endswith('.'):
                summary += '.'
        
        logger.info(f"Generated summary: {summary[:100]}...")
        
        return summary
        
    except ClientError as e:
        logger.error(f"Bedrock API error: {str(e)}")
        # Fallback summary
        return "Multiple insights were gathered from the analysis. Please review the detailed findings above."
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return "Summary generation failed. Please review the detailed findings above."


def combine_response(
    bullet_points: List[str],
    summary: str
) -> str:
    """
    Combine bullet points and summary into final response.
    
    Args:
        bullet_points: List of formatted bullet points
        summary: Generated summary text
    
    Returns:
        Combined response text
    """
    # Format: bullet points followed by blank line and summary
    response_parts = []
    
    # Add bullet points
    if bullet_points:
        response_parts.append('\n'.join(bullet_points))
    
    # Add summary
    if summary:
        response_parts.append('')  # Blank line
        response_parts.append(f"Summary: {summary}")
    
    return '\n'.join(response_parts)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for summary generation.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "question": "string",
        "bullet_points": [...],
        "validated_results": [...]
    }
    
    Returns:
        Summary and combined response
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        question = event.get('question', '')
        bullet_points = event.get('bullet_points', [])
        validated_results = event.get('validated_results', [])
        
        # Validate required fields
        if not all([job_id, tenant_id]):
            raise ValueError("Missing required fields: job_id or tenant_id")
        
        logger.info(
            f"Generating summary for job {job_id} with "
            f"{len(bullet_points)} bullet points"
        )
        
        # Generate summary using Bedrock
        summary = generate_summary_with_bedrock(
            question=question,
            bullet_points=bullet_points,
            validated_results=validated_results
        )
        
        # Combine bullet points and summary
        final_response = combine_response(bullet_points, summary)
        
        logger.info(f"Generated final response ({len(final_response)} chars)")
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'summary': summary,
            'final_response': final_response,
            'response_length': len(final_response),
            'status': 'success'
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'summary': '',
            'final_response': '',
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error generating summary: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'summary': '',
            'final_response': '',
            'status': 'error',
            'error_message': f"Summary generation error: {str(e)}"
        }
