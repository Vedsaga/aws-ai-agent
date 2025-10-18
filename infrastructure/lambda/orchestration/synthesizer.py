"""
Synthesis Lambda Function

Merges validated outputs into a single JSON document, resolves conflicts
between agent outputs, and formats for database storage.

Requirements: 5.3
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_orchestrator_status

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def merge_agent_outputs(validated_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge all agent outputs into a single structured document.
    
    Args:
        validated_results: List of validated agent results
    
    Returns:
        Merged output document
    """
    merged = {}
    
    for result in validated_results:
        agent_name = result.get('agent_name')
        agent_id = result.get('agent_id')
        output = result.get('output', {})
        validation_status = result.get('validation_status', 'unknown')
        
        # Only include outputs that passed validation
        if validation_status != 'passed':
            logger.warning(f"Skipping agent '{agent_name}' output due to validation failure")
            continue
        
        # Create agent-specific section
        agent_key = agent_id.replace('-', '_')
        merged[agent_key] = {
            'agent_name': agent_name,
            'data': output,
            'execution_time_ms': result.get('execution_time_ms', 0)
        }
    
    return merged


def resolve_conflicts(merged: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve conflicts between agent outputs.
    
    Strategy:
    - For location data: prefer Geo Agent output
    - For temporal data: prefer Temporal Agent output
    - For entities: merge from all sources
    - For sentiment: use Entity Agent output
    
    Args:
        merged: Merged agent outputs
    
    Returns:
        Conflict-resolved document
    """
    resolved = merged.copy()
    
    # Extract common fields from different agents
    location_data = None
    temporal_data = None
    entity_data = []
    sentiment_data = None
    
    for agent_key, agent_output in merged.items():
        agent_name = agent_output.get('agent_name', '').lower()
        data = agent_output.get('data', {})
        
        # Extract location data (prefer Geo Agent)
        if 'geo' in agent_name or 'location' in agent_name:
            if 'location' in data or 'coordinates' in data:
                location_data = {
                    'location': data.get('location'),
                    'coordinates': data.get('coordinates'),
                    'address': data.get('address'),
                    'source': agent_output.get('agent_name')
                }
        
        # Extract temporal data (prefer Temporal Agent)
        if 'temporal' in agent_name or 'time' in agent_name:
            if 'timestamp' in data or 'date' in data:
                temporal_data = {
                    'timestamp': data.get('timestamp'),
                    'date': data.get('date'),
                    'time': data.get('time'),
                    'source': agent_output.get('agent_name')
                }
        
        # Extract entity data (merge from all sources)
        if 'entity' in agent_name or 'entities' in data:
            entities = data.get('entities', [])
            if entities:
                entity_data.extend(entities)
        
        # Extract sentiment (prefer Entity Agent)
        if 'entity' in agent_name or 'sentiment' in data:
            if 'sentiment' in data:
                sentiment_data = {
                    'sentiment': data.get('sentiment'),
                    'sentiment_score': data.get('sentiment_score'),
                    'source': agent_output.get('agent_name')
                }
    
    # Add resolved common fields
    if location_data:
        resolved['_location'] = location_data
    
    if temporal_data:
        resolved['_temporal'] = temporal_data
    
    if entity_data:
        # Deduplicate entities by text
        unique_entities = []
        seen_texts = set()
        for entity in entity_data:
            entity_text = entity.get('Text', entity.get('text', ''))
            if entity_text and entity_text not in seen_texts:
                unique_entities.append(entity)
                seen_texts.add(entity_text)
        resolved['_entities'] = unique_entities
    
    if sentiment_data:
        resolved['_sentiment'] = sentiment_data
    
    return resolved


def format_for_storage(
    synthesized: Dict[str, Any],
    job_id: str,
    tenant_id: str,
    domain_id: str,
    raw_text: str
) -> Dict[str, Any]:
    """
    Format synthesized data for database storage.
    
    Args:
        synthesized: Synthesized agent outputs
        job_id: Job identifier
        tenant_id: Tenant identifier
        domain_id: Domain identifier
        raw_text: Original raw input text
    
    Returns:
        Formatted document ready for storage
    """
    storage_doc = {
        'job_id': job_id,
        'tenant_id': tenant_id,
        'domain_id': domain_id,
        'raw_text': raw_text,
        'structured_data': synthesized,
        'created_at': datetime.utcnow().isoformat(),
        'processing_metadata': {
            'agent_count': len([k for k in synthesized.keys() if not k.startswith('_')]),
            'has_location': '_location' in synthesized,
            'has_temporal': '_temporal' in synthesized,
            'has_entities': '_entities' in synthesized,
            'has_sentiment': '_sentiment' in synthesized
        }
    }
    
    return storage_doc


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for synthesis.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "domain_id": "string",
        "raw_text": "string",
        "validated_results": [
            {
                "agent_name": "string",
                "agent_id": "string",
                "output": {...},
                "validation_status": "passed|failed",
                "execution_time_ms": 123
            }
        ],
        "failed_results": [...],
        "statistics": {...},
        "validation_summary": {...}
    }
    
    Returns:
        Synthesized document ready for storage
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        user_id = event.get('user_id')
        domain_id = event.get('domain_id', 'unknown')
        raw_text = event.get('raw_text', '')
        validated_results = event.get('validated_results', [])
        failed_results = event.get('failed_results', [])
        statistics = event.get('statistics', {})
        validation_summary = event.get('validation_summary', {})
        
        logger.info(f"Synthesizing results for job {job_id}")
        
        # Publish status: synthesizing
        if user_id:
            publish_orchestrator_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                status='synthesizing',
                message=f"Merging outputs from {len(validated_results)} agents"
            )
        
        # Merge agent outputs
        merged = merge_agent_outputs(validated_results)
        logger.info(f"Merged {len(merged)} agent outputs")
        
        # Resolve conflicts
        synthesized = resolve_conflicts(merged)
        logger.info("Resolved conflicts between agent outputs")
        
        # Format for storage
        storage_doc = format_for_storage(
            synthesized=synthesized,
            job_id=job_id,
            tenant_id=tenant_id,
            domain_id=domain_id,
            raw_text=raw_text
        )
        
        # Add processing summary
        storage_doc['processing_summary'] = {
            'total_agents_executed': statistics.get('total_agents', 0),
            'successful_agents': statistics.get('successful_count', 0),
            'failed_agents': statistics.get('failed_count', 0),
            'validation_passed': validation_summary.get('passed_validation', 0),
            'validation_failed': validation_summary.get('failed_validation', 0),
            'total_execution_time_ms': statistics.get('total_execution_time_ms', 0)
        }
        
        # Include failed results for debugging
        if failed_results:
            storage_doc['failed_agents'] = [
                {
                    'agent_name': r.get('agent_name'),
                    'error_message': r.get('error_message')
                }
                for r in failed_results
            ]
        
        logger.info(f"Synthesis complete for job {job_id}")
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'domain_id': domain_id,
            'storage_document': storage_doc,
            'synthesis_status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error in synthesis: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'domain_id': event.get('domain_id', 'unknown'),
            'storage_document': {
                'job_id': event.get('job_id', 'unknown'),
                'tenant_id': event.get('tenant_id', 'unknown'),
                'domain_id': event.get('domain_id', 'unknown'),
                'raw_text': event.get('raw_text', ''),
                'structured_data': {},
                'created_at': datetime.utcnow().isoformat(),
                'error': str(e)
            },
            'synthesis_status': 'error',
            'error_message': str(e)
        }
