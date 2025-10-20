"""
Geo Agent - Location Extraction and Geocoding

Extracts location information from text and performs geocoding using
Amazon Location Service with web search fallback for ambiguous locations.
"""

import json
import logging
import re
from typing import Dict, Any, Optional
from base_agent import BaseAgent, parse_json_from_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GeoAgent(BaseAgent):
    """
    Agent for extracting and geocoding location information.
    
    Output Schema (max 5 keys):
    - location_name: Extracted location name
    - coordinates: [latitude, longitude] or None
    - geometry_type: Type of geometry (Point, LineString, Polygon)
    - confidence: Confidence score (0-1)
    - address: Full address if available
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Set default output schema if not provided
        if 'output_schema' not in config:
            config['output_schema'] = {
                'location_name': {'type': 'string', 'required': True},
                'coordinates': {'type': 'array', 'required': False},
                'geometry_type': {'type': 'string', 'required': True},
                'confidence': {'type': 'number', 'required': True},
                'address': {'type': 'string', 'required': False}
            }
        
        # Set default system prompt if not provided
        if 'system_prompt' not in config:
            config['system_prompt'] = """You are a location extraction specialist. 
Your task is to identify and extract location information from text.

Extract the following information:
1. location_name: The primary location mentioned (city, street, landmark)
2. address: Full address if available
3. location_type: Type of location (city, street, landmark, building, region, etc.)
4. confidence: Your confidence in the extraction (0.0 to 1.0)

Return ONLY a JSON object with these fields. If no location is found, set location_name to "unknown" and confidence to 0.0."""
        
        super().__init__(config)
    
    def detect_geometry_type(self, text: str) -> str:
        """
        Detect geometry type from text patterns.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Geometry type: 'Point', 'LineString', or 'Polygon'
        """
        text_lower = text.lower()
        
        # LineString patterns - routes, paths, connections
        linestring_patterns = [
            r'from\s+.+\s+to\s+.+',
            r'along\s+.+\s+street',
            r'along\s+.+\s+road',
            r'between\s+.+\s+and\s+.+',
            r'route\s+',
            r'path\s+',
            r'corridor',
            r'highway',
            r'freeway'
        ]
        
        for pattern in linestring_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"Detected LineString pattern: {pattern}")
                return 'LineString'
        
        # Polygon patterns - areas, zones, regions
        polygon_patterns = [
            r'\barea\b',
            r'\bzone\b',
            r'neighborhood',
            r'\bblock\b',
            r'region',
            r'district',
            r'entire\s+',
            r'throughout\s+',
            r'across\s+the\s+',
            r'perimeter',
            r'boundary'
        ]
        
        for pattern in polygon_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"Detected Polygon pattern: {pattern}")
                return 'Polygon'
        
        # Default to Point for single locations
        logger.info("Defaulting to Point geometry")
        return 'Point'
    
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract location information from text and geocode it.
        
        Args:
            raw_text: Raw input text
            parent_output: Not used for this agent
        
        Returns:
            Dict with location information (max 5 keys)
        """
        logger.info(f"GeoAgent processing text: {raw_text[:100]}...")
        
        # Step 1: Detect geometry type from text patterns
        geometry_type = self.detect_geometry_type(raw_text)
        
        # Step 2: Use Bedrock to extract location information
        prompt = f"""Extract location information from the following text:

Text: {raw_text}

Return a JSON object with:
- location_name: The main location mentioned
- address: Full address if available (or null)
- confidence: Your confidence score (0.0 to 1.0)

JSON:"""
        
        try:
            bedrock_response = self.invoke_bedrock(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent extraction
            )
            
            # Parse JSON from response
            location_data = parse_json_from_text(bedrock_response)
            
            # Extract fields
            location_name = location_data.get('location_name', 'unknown')
            address = location_data.get('address')
            confidence = float(location_data.get('confidence', 0.0))
            
            # Step 3: Attempt geocoding if location found
            coordinates = None
            
            if location_name and location_name != 'unknown' and confidence > 0.3:
                # Try to geocode using Location Service
                geocode_query = address if address else location_name
                
                try:
                    # Attempt Location Service geocoding
                    if 'location' in self.tools:
                        location_result = self.invoke_tool(
                            'location',
                            {'address': geocode_query}
                        )
                        coordinates = location_result.get('coordinates')
                except Exception as e:
                    logger.warning(f"Location Service geocoding failed: {str(e)}")
                
                # Fallback to web search for ambiguous locations
                if not coordinates and 'web_search' in self.tools and confidence < 0.7:
                    try:
                        search_result = self.invoke_tool(
                            'web_search',
                            {
                                'query': f"coordinates of {geocode_query}",
                                'max_results': 3
                            }
                        )
                        # Would parse coordinates from search results
                        logger.info("Web search fallback attempted")
                    except Exception as e:
                        logger.warning(f"Web search fallback failed: {str(e)}")
            
            # Step 4: Format output (max 5 keys)
            output = {
                'location_name': location_name,
                'coordinates': coordinates,
                'geometry_type': geometry_type,
                'confidence': confidence,
                'address': address
            }
            
            logger.info(f"GeoAgent extracted location: {location_name} (geometry: {geometry_type}, confidence: {confidence})")
            
            return output
            
        except Exception as e:
            logger.error(f"GeoAgent execution failed: {str(e)}")
            # Return default output on error
            return {
                'location_name': 'unknown',
                'coordinates': None,
                'geometry_type': 'Point',
                'confidence': 0.0,
                'address': None
            }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Geo Agent.
    
    Args:
        event: Lambda event with agent configuration and input
        context: Lambda context
    
    Returns:
        Standardized agent output
    """
    # Get agent configuration from event or use defaults
    agent_config = event.get('agent_config', {})
    agent_config['agent_name'] = 'GeoAgent'
    
    # Ensure required tools are available
    if 'tools' not in agent_config:
        agent_config['tools'] = ['bedrock', 'location', 'web_search']
    
    # Create agent instance
    agent = GeoAgent(agent_config)
    
    # Execute with error handling
    return agent.handle_execution(event, context)
