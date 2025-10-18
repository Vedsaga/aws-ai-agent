"""
Comprehend Tool Proxy Lambda

Proxies requests to AWS Comprehend with IAM authentication.
"""

import json
import logging
import boto3
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

comprehend = boto3.client('comprehend')


def detect_entities(text: str, language_code: str = 'en') -> Dict[str, Any]:
    """
    Detect named entities in text.
    
    Args:
        text: Input text
        language_code: Language code (default: en)
    
    Returns:
        Entities detection result
    """
    try:
        response = comprehend.detect_entities(
            Text=text,
            LanguageCode=language_code
        )
        
        return {
            'status': 'success',
            'entities': response.get('Entities', [])
        }
    
    except Exception as e:
        logger.error(f"Error detecting entities: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def detect_sentiment(text: str, language_code: str = 'en') -> Dict[str, Any]:
    """
    Detect sentiment in text.
    
    Args:
        text: Input text
        language_code: Language code (default: en)
    
    Returns:
        Sentiment detection result
    """
    try:
        response = comprehend.detect_sentiment(
            Text=text,
            LanguageCode=language_code
        )
        
        return {
            'status': 'success',
            'sentiment': response.get('Sentiment'),
            'sentiment_score': response.get('SentimentScore', {})
        }
    
    except Exception as e:
        logger.error(f"Error detecting sentiment: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def detect_key_phrases(text: str, language_code: str = 'en') -> Dict[str, Any]:
    """
    Detect key phrases in text.
    
    Args:
        text: Input text
        language_code: Language code (default: en)
    
    Returns:
        Key phrases detection result
    """
    try:
        response = comprehend.detect_key_phrases(
            Text=text,
            LanguageCode=language_code
        )
        
        return {
            'status': 'success',
            'key_phrases': response.get('KeyPhrases', [])
        }
    
    except Exception as e:
        logger.error(f"Error detecting key phrases: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def analyze_all(text: str, language_code: str = 'en') -> Dict[str, Any]:
    """
    Run all Comprehend analyses on text.
    
    Args:
        text: Input text
        language_code: Language code (default: en)
    
    Returns:
        Combined analysis results
    """
    entities_result = detect_entities(text, language_code)
    sentiment_result = detect_sentiment(text, language_code)
    key_phrases_result = detect_key_phrases(text, language_code)
    
    return {
        'status': 'success',
        'entities': entities_result.get('entities', []),
        'sentiment': sentiment_result.get('sentiment'),
        'sentiment_score': sentiment_result.get('sentiment_score', {}),
        'key_phrases': key_phrases_result.get('key_phrases', [])
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Comprehend proxy.
    
    Expected input:
    {
        "text": "string",
        "language_code": "string (optional, default: en)",
        "analysis_type": "entities|sentiment|key_phrases|all (optional, default: all)"
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
        text = body.get('text')
        if not text:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'bad_request', 'message': 'Missing text'})
            }
        
        language_code = body.get('language_code', 'en')
        analysis_type = body.get('analysis_type', 'all')
        
        # Route to appropriate analysis
        if analysis_type == 'entities':
            result = detect_entities(text, language_code)
        elif analysis_type == 'sentiment':
            result = detect_sentiment(text, language_code)
        elif analysis_type == 'key_phrases':
            result = detect_key_phrases(text, language_code)
        else:
            result = analyze_all(text, language_code)
        
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
