"""
Query Agents - Interrogative Analysis Agents

Implements 11 interrogative query agents that analyze data from different perspectives:
When, Where, Why, How, What, Who, Which, How Many, How Much, From Where, What Kind
"""

import json
import logging
from typing import Dict, Any, Optional
from base_agent import BaseAgent, parse_json_from_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class InterrogativeAgent(BaseAgent):
    """
    Base class for interrogative query agents.
    All query agents share similar structure but different analysis perspectives.
    """
    
    def __init__(self, config: Dict[str, Any], interrogative: str):
        self.interrogative = interrogative
        
        # Set default output schema (max 5 keys)
        if 'output_schema' not in config:
            config['output_schema'] = {
                'insight': {'type': 'string', 'required': True},
                'data_points': {'type': 'array', 'required': False},
                'confidence': {'type': 'number', 'required': True},
                'source': {'type': 'string', 'required': False},
                'summary': {'type': 'string', 'required': True}
            }
        
        super().__init__(config)
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute interrogative analysis on the question.
        
        Args:
            raw_text: User's question
            parent_output: Optional output from parent agent
        
        Returns:
            Analysis from interrogative perspective (max 5 keys)
        """
        logger.info(f"{self.interrogative}Agent analyzing: {raw_text[:100]}...")
        
        # Prepare context with parent output if available
        context = raw_text
        if parent_output:
            context += f"\n\nContext from parent agent: {json.dumps(parent_output)}"
        
        # Build analysis prompt
        prompt = f"""Question: {raw_text}

Analyze this question from the "{self.interrogative}" perspective.
Provide a concise 1-2 line insight that directly answers the {self.interrogative} aspect.

Return a JSON object with:
- insight: Your 1-2 line answer (focus on {self.interrogative})
- confidence: Your confidence score (0.0 to 1.0)
- summary: Brief summary of your analysis
- data_points: Key data points supporting your insight (optional, max 5 items)

JSON:"""
        
        try:
            # Invoke Bedrock for analysis
            bedrock_response = self.invoke_bedrock(
                prompt=prompt,
                max_tokens=800,
                temperature=0.5
            )
            
            # Parse response
            analysis = parse_json_from_text(bedrock_response)
            
            # Format output (max 5 keys)
            output = {
                'insight': analysis.get('insight', f'No {self.interrogative} insight available'),
                'data_points': analysis.get('data_points', [])[:5],  # Limit to 5
                'confidence': float(analysis.get('confidence', 0.5)),
                'source': 'bedrock_analysis',
                'summary': analysis.get('summary', '')
            }
            
            logger.info(f"{self.interrogative}Agent completed with confidence {output['confidence']}")
            
            return output
            
        except Exception as e:
            logger.error(f"{self.interrogative}Agent execution failed: {str(e)}")
            return {
                'insight': f'Unable to provide {self.interrogative} analysis',
                'data_points': [],
                'confidence': 0.0,
                'source': 'error',
                'summary': f'Analysis failed: {str(e)}'
            }


# Individual Agent Classes

class WhenAgent(InterrogativeAgent):
    """Temporal analysis - When did events occur? When will they happen?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a temporal analysis specialist.
Focus on WHEN events occurred, patterns over time, temporal trends, and timing relationships.
Provide insights about time-based patterns, frequencies, and temporal correlations."""
        
        super().__init__(config, 'When')


class WhereAgent(InterrogativeAgent):
    """Spatial analysis - Where are events located? Geographic patterns?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a spatial analysis specialist.
Focus on WHERE events occur, geographic patterns, location clusters, and spatial relationships.
Provide insights about geographic distributions, hotspots, and location-based trends."""
        
        super().__init__(config, 'Where')


class WhyAgent(InterrogativeAgent):
    """Causal analysis - Why did events happen? What are the causes?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a causal analysis specialist.
Focus on WHY events occur, root causes, contributing factors, and causal relationships.
Provide insights about underlying reasons, motivations, and cause-effect patterns."""
        
        super().__init__(config, 'Why')


class HowAgent(InterrogativeAgent):
    """Method analysis - How did events happen? What methods were used?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a method analysis specialist.
Focus on HOW events occur, processes, methods, mechanisms, and procedures.
Provide insights about approaches, techniques, and operational patterns."""
        
        super().__init__(config, 'How')


class WhatAgent(InterrogativeAgent):
    """Entity analysis - What entities are involved? What happened?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are an entity and event analysis specialist.
Focus on WHAT entities are involved, what events occurred, and what things are present.
Provide insights about key entities, objects, events, and their characteristics."""
        
        super().__init__(config, 'What')


class WhoAgent(InterrogativeAgent):
    """Person analysis - Who is involved? Who reported? Who is affected?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a person and stakeholder analysis specialist.
Focus on WHO is involved, who reported issues, who is affected, and stakeholder patterns.
Provide insights about people, groups, roles, and human factors."""
        
        super().__init__(config, 'Who')


class WhichAgent(InterrogativeAgent):
    """Selection analysis - Which items? Which categories? Which options?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a selection and categorization specialist.
Focus on WHICH items, categories, types, or options are most relevant or significant.
Provide insights about selections, preferences, and categorical distinctions."""
        
        super().__init__(config, 'Which')


class HowManyAgent(InterrogativeAgent):
    """Count analysis - How many incidents? What are the quantities?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a quantitative count analysis specialist.
Focus on HOW MANY items, incidents, occurrences, and discrete quantities.
Provide insights about counts, frequencies, and numerical distributions."""
        
        super().__init__(config, 'HowMany')


class HowMuchAgent(InterrogativeAgent):
    """Quantity analysis - How much impact? What is the magnitude?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a magnitude and impact analysis specialist.
Focus on HOW MUCH impact, severity, extent, and continuous quantities.
Provide insights about magnitudes, scales, degrees, and impact levels."""
        
        super().__init__(config, 'HowMuch')


class FromWhereAgent(InterrogativeAgent):
    """Origin analysis - From where did it originate? What is the source?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are an origin and source analysis specialist.
Focus on FROM WHERE things originate, source locations, and origin patterns.
Provide insights about sources, origins, starting points, and provenance."""
        
        super().__init__(config, 'FromWhere')


class WhatKindAgent(InterrogativeAgent):
    """Type analysis - What kind of events? What types are present?"""
    
    def __init__(self, config: Dict[str, Any]):
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a type and classification specialist.
Focus on WHAT KIND of events, types, categories, and classifications.
Provide insights about types, varieties, classifications, and taxonomies."""
        
        super().__init__(config, 'WhatKind')


# Lambda Handlers for each agent

def when_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for When Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhenAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhenAgent(agent_config)
    return agent.handle_execution(event, context)


def where_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Where Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhereAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhereAgent(agent_config)
    return agent.handle_execution(event, context)


def why_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Why Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhyAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhyAgent(agent_config)
    return agent.handle_execution(event, context)


def how_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for How Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'HowAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = HowAgent(agent_config)
    return agent.handle_execution(event, context)


def what_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for What Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhatAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhatAgent(agent_config)
    return agent.handle_execution(event, context)


def who_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Who Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhoAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhoAgent(agent_config)
    return agent.handle_execution(event, context)


def which_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Which Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhichAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhichAgent(agent_config)
    return agent.handle_execution(event, context)


def how_many_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for How Many Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'HowManyAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = HowManyAgent(agent_config)
    return agent.handle_execution(event, context)


def how_much_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for How Much Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'HowMuchAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = HowMuchAgent(agent_config)
    return agent.handle_execution(event, context)


def from_where_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for From Where Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'FromWhereAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = FromWhereAgent(agent_config)
    return agent.handle_execution(event, context)


def what_kind_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for What Kind Agent"""
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'WhatKindAgent'
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock']
    
    agent = WhatKindAgent(agent_config)
    return agent.handle_execution(event, context)
