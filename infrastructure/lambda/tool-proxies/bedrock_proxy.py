"""
Bedrock Tool Proxy Lambda

Proxies requests to AWS Bedrock with IAM authentication.
"""

import json
import logging
import os
import boto3
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_runtime = boto3.client('bedrock-runtime')

# Default model configuration
DEFAULT_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
DEFAULT_MAX_TOKENS = int(os.environ.get('DEFAULT_MAX_TOKENS', '1000'))


def invoke_bedrock(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = None,
    temperature: float = 0.7,
    model_id: str = None
) -> Dict[str, Any]:
    """
    Invoke Bedrock model with given parameters.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        model_id: Model identifier
    
    Returns:
        Model response
    """
    model_id = model_id or DEFAULT_MODEL_ID
    max_tokens = max_tokens or DEFAULT_MAX_TOKENS
    
    # Prepare request body based on model
    if 'claude' in model_id.lower():
        # Claude 3 format
        messages = [{'role': 'user', 'content': prompt}]
        
        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        if system_prompt:
            request_body['system'] = system_prompt
    
    else:
        # Generic format
        request_body = {
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract text based on model
        if 'claude' in model_id.lower():
            text = response_body.get('content', [{}])[0].get('text', '')
        else:
            text = response_body.get('completion', response_body.get('text', ''))
        
        return {
            'status': 'success',
            'text': text,
            'model_id': model_id,
            'usage': response_body.get('usage', {})
        }
    
    except Exception as e:
        logger.error(f"Error invoking Bedrock: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'model_id': model_id
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Bedrock proxy.
    
    Expected input:
    {
        "prompt": "string",
        "system_prompt": "string (optional)",
        "max_tokens": int (optional),
        "temperature": float (optional),
        "model_id": "string (optional)"
    }
    """
    try:
        # Parse body
        body = event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']
        
        # Extract parameters
        prompt = body.get('prompt')
        if not prompt:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing prompt'})
            }
        
        system_prompt = body.get('system_prompt')
        max_tokens = body.get('max_tokens')
        temperature = body.get('temperature', 0.7)
        model_id = body.get('model_id')
        
        # Invoke Bedrock
        result = invoke_bedrock(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id
        )
        
        if result['status'] == 'success':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'internal_error', 'message': str(e)})
        }
