"""
Entity Agent - Entity Extraction and Sentiment Analysis

Extracts named entities, sentiment, and key phrases using AWS Comprehend
and Bedrock for enhanced entity understanding.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from base_agent import BaseAgent, parse_json_from_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class EntityAgent(BaseAgent):
    """
    Agent for extracting entities, sentiment, and key information.
    
    Output Schema (max 5 keys):
    - entities: List of named entities (people, organizations, locations)
    - sentiment: Overall sentiment (POSITIVE, NEGATIVE, NEUTRAL, MIXED)
    - key_phrases: Important phrases from text
    - category: Primary category/topic
    - confidence: Confidence score (0-1)
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Set default output schema if not provided
        if 'output_schema' not in config:
            config['output_schema'] = {
                'entities': {'type': 'array', 'required': True},
                'sentiment': {'type': 'string', 'required': True},
                'key_phrases': {'type': 'array', 'required': True},
                'category': {'type': 'string', 'required': False},
                'confidence': {'type': 'number', 'required': True}
            }
        
        # Set default system prompt if not provided
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are an entity extraction and categorization specialist.
Your task is to identify key entities and categorize the content.

Analyze the text and provide:
1. category: Primary category/topic of the text (e.g., infrastructure, safety, health, environment)
2. confidence: Your confidence in the categorization (0.0 to 1.0)

Return ONLY a JSON object with these fields."""
        
        super().__init__(config)
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract entities, sentiment, and key phrases from text.
        
        Args:
            raw_text: Raw input text
            parent_output: Not used for this agent
        
        Returns:
            Dict with entity information (max 5 keys)
        """
        logger.info(f"EntityAgent processing text: {raw_text[:100]}...")
        
        entities = []
        sentiment = 'NEUTRAL'
        key_phrases = []
        category = 'general'
        confidence = 0.5
        
        try:
            # Step 1: Use AWS Comprehend for entity extraction and sentiment
            if 'comprehend' in self.tools:
                try:
                    comprehend_result = self.invoke_tool(
                        'comprehend',
                        {'text': raw_text, 'language': 'en'}
                    )
                    
                    # Extract entities
                    raw_entities = comprehend_result.get('entities', [])
                    entities = [
                        {
                            'text': e.get('Text', ''),
                            'type': e.get('Type', ''),
                            'score': e.get('Score', 0.0)
                        }
                        for e in raw_entities[:10]  # Limit to top 10
                    ]
                    
                    # Extract sentiment
                    sentiment = comprehend_result.get('sentiment', 'NEUTRAL')
                    
                    # Extract key phrases
                    raw_phrases = comprehend_result.get('key_phrases', [])
                    key_phrases = [
                        p.get('Text', '')
                        for p in raw_phrases[:10]  # Limit to top 10
                    ]
                    
                    logger.info(
                        f"Comprehend extracted {len(entities)} entities, "
                        f"sentiment: {sentiment}"
                    )
                    
                except Exception as e:
                    logger.warning(f"Comprehend invocation failed: {str(e)}")
            
            # Step 2: Use Bedrock for categorization and enhanced understanding
            prompt = f"""Analyze the following text and provide categorization:

Text: {raw_text}

Entities found: {json.dumps([e['text'] for e in entities])}
Sentiment: {sentiment}

Return a JSON object with:
- category: Primary category (infrastructure, safety, health, environment, transportation, utilities, other)
- confidence: Your confidence score (0.0 to 1.0)

JSON:"""
            
            bedrock_response = self.invoke_bedrock(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse JSON from response
            categorization = parse_json_from_text(bedrock_response)
            category = categorization.get('category', 'general')
            confidence = float(categorization.get('confidence', 0.5))
            
            # Step 3: Format output (max 5 keys)
            output = {
                'entities': entities,
                'sentiment': sentiment,
                'key_phrases': key_phrases,
                'category': category,
                'confidence': confidence
            }
            
            logger.info(
                f"EntityAgent categorized as '{category}' with confidence {confidence}"
            )
            
            return output
            
        except Exception as e:
            logger.error(f"EntityAgent execution failed: {str(e)}")
            # Return minimal output on error
            return {
                'entities': entities,
                'sentiment': sentiment,
                'key_phrases': key_phrases,
                'category': 'unknown',
                'confidence': 0.0
            }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Entity Agent.
    
    Args:
        event: Lambda event with agent configuration and input
        context: Lambda context
    
    Returns:
        Standardized agent output
    """
    # Get agent configuration from event or use defaults
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'EntityAgent'
    
    # Ensure required tools are available
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock', 'comprehend']
    
    # Create agent instance
    agent = EntityAgent(agent_config)
    
    # Execute with error handling
    return agent.handle_execution(event, context)
