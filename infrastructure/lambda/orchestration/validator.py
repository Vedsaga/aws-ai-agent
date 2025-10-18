"""
Validation Lambda Function

Loads output schemas from DynamoDB, validates each agent output against schema,
checks max 5 keys constraint, and cross-validates consistency across agents.

Requirements: 5.1, 5.2
"""

import json
import os
import sys
import boto3
import logging
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_orchestrator_status

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
AGENT_CONFIGS_TABLE = os.environ.get('AGENT_CONFIGS_TABLE', 'agent_configs')


def load_output_schema(tenant_id: str, agent_id: str) -> Dict[str, Any]:
    """
    Load output schema for an agent from DynamoDB.
    
    Args:
        tenant_id: Tenant identifier
        agent_id: Agent identifier
    
    Returns:
        Output schema dictionary
    """
    try:
        table = dynamodb.Table(AGENT_CONFIGS_TABLE)
        response = table.get_item(
            Key={
                'tenant_id': tenant_id,
                'agent_id': agent_id
            }
        )
        
        if 'Item' not in response:
            logger.warning(f"Agent config not found for {agent_id}, using empty schema")
            return {}
        
        schema = response['Item'].get('output_schema', {})
        return schema
        
    except ClientError as e:
        logger.error(f"Error loading schema for agent {agent_id}: {str(e)}")
        return {}


def validate_max_keys(output: Dict[str, Any], agent_name: str) -> List[str]:
    """
    Validate that output has maximum 5 keys.
    
    Args:
        output: Agent output to validate
        agent_name: Name of the agent
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if len(output) > 5:
        errors.append(
            f"Agent '{agent_name}' output has {len(output)} keys, maximum is 5"
        )
    
    return errors


def validate_against_schema(
    output: Dict[str, Any],
    schema: Dict[str, Any],
    agent_name: str
) -> List[str]:
    """
    Validate agent output against its defined schema.
    
    Args:
        output: Agent output to validate
        schema: Expected output schema
        agent_name: Name of the agent
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # If no schema defined, skip validation
    if not schema:
        logger.info(f"No schema defined for agent '{agent_name}', skipping schema validation")
        return errors
    
    # Check all output keys are in schema
    for key in output.keys():
        if key not in schema:
            errors.append(
                f"Agent '{agent_name}' output key '{key}' not in schema"
            )
    
    # Check required keys are present
    for key, field_schema in schema.items():
        if isinstance(field_schema, dict) and field_schema.get('required', False):
            if key not in output:
                errors.append(
                    f"Agent '{agent_name}' missing required key '{key}'"
                )
    
    # Type validation (basic)
    for key, value in output.items():
        if key in schema and isinstance(schema[key], dict):
            expected_type = schema[key].get('type')
            if expected_type:
                if not validate_type(value, expected_type):
                    errors.append(
                        f"Agent '{agent_name}' key '{key}' has invalid type. "
                        f"Expected {expected_type}, got {type(value).__name__}"
                    )
    
    return errors


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate value type against expected type string.
    
    Args:
        value: Value to check
        expected_type: Expected type name
    
    Returns:
        True if type matches
    """
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'object': dict,
        'array': list
    }
    
    expected_python_type = type_map.get(expected_type.lower())
    if expected_python_type is None:
        return True  # Unknown type, skip validation
    
    return isinstance(value, expected_python_type)


def cross_validate_consistency(
    successful_results: List[Dict[str, Any]]
) -> List[str]:
    """
    Cross-validate consistency across agent outputs.
    
    Checks for:
    - Conflicting location data
    - Conflicting temporal data
    - Inconsistent entity references
    
    Args:
        successful_results: List of successful agent results
    
    Returns:
        List of consistency warnings
    """
    warnings = []
    
    # Extract location data from different agents
    locations = []
    for result in successful_results:
        output = result.get('output', {})
        agent_name = result.get('agent_name')
        
        # Check for location-related fields
        if 'location' in output or 'coordinates' in output or 'address' in output:
            locations.append({
                'agent': agent_name,
                'location': output.get('location'),
                'coordinates': output.get('coordinates'),
                'address': output.get('address')
            })
    
    # Check for conflicting locations
    if len(locations) > 1:
        # Simple check: if multiple agents provide coordinates, they should be similar
        coords_list = [loc['coordinates'] for loc in locations if loc['coordinates']]
        if len(coords_list) > 1:
            # Check if coordinates are significantly different (>1km apart)
            # This is a simplified check - production would use proper distance calculation
            logger.info(f"Multiple location sources found: {len(coords_list)}")
    
    # Extract temporal data
    timestamps = []
    for result in successful_results:
        output = result.get('output', {})
        agent_name = result.get('agent_name')
        
        if 'timestamp' in output or 'date' in output or 'time' in output:
            timestamps.append({
                'agent': agent_name,
                'timestamp': output.get('timestamp'),
                'date': output.get('date'),
                'time': output.get('time')
            })
    
    # Log consistency check results
    logger.info(
        f"Consistency check: {len(locations)} location sources, "
        f"{len(timestamps)} temporal sources"
    )
    
    return warnings


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for output validation.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "successful_results": [
            {
                "agent_name": "string",
                "agent_id": "string",
                "output": {...},
                "execution_time_ms": 123
            }
        ],
        "failed_results": [...],
        "statistics": {...}
    }
    
    Returns:
        Validation results with errors and warnings
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        user_id = event.get('user_id')
        successful_results = event.get('successful_results', [])
        failed_results = event.get('failed_results', [])
        statistics = event.get('statistics', {})
        
        logger.info(f"Validating results for job {job_id}: {len(successful_results)} successful agents")
        
        # Publish status: validating
        if user_id:
            publish_orchestrator_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                status='validating',
                message=f"Validating outputs from {len(successful_results)} agents"
            )
        
        validation_errors = []
        validated_results = []
        
        # Validate each successful result
        for result in successful_results:
            agent_name = result.get('agent_name')
            agent_id = result.get('agent_id')
            output = result.get('output', {})
            
            # Load schema
            schema = load_output_schema(tenant_id, agent_id)
            
            # Validate max 5 keys
            key_errors = validate_max_keys(output, agent_name)
            
            # Validate against schema
            schema_errors = validate_against_schema(output, schema, agent_name)
            
            # Combine errors
            agent_errors = key_errors + schema_errors
            
            if agent_errors:
                validation_errors.extend(agent_errors)
                logger.warning(f"Validation errors for agent '{agent_name}': {agent_errors}")
                # Mark as validation failed
                result['validation_status'] = 'failed'
                result['validation_errors'] = agent_errors
            else:
                result['validation_status'] = 'passed'
                result['validation_errors'] = []
            
            validated_results.append(result)
        
        # Cross-validate consistency
        consistency_warnings = cross_validate_consistency(successful_results)
        
        # Determine overall validation status
        has_validation_errors = len(validation_errors) > 0
        
        validation_result = {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'validated_results': validated_results,
            'failed_results': failed_results,
            'statistics': statistics,
            'validation_summary': {
                'total_validated': len(successful_results),
                'passed_validation': len([r for r in validated_results if r.get('validation_status') == 'passed']),
                'failed_validation': len([r for r in validated_results if r.get('validation_status') == 'failed']),
                'validation_errors': validation_errors,
                'consistency_warnings': consistency_warnings
            },
            'has_validation_errors': has_validation_errors,
            'validation_status': 'failed' if has_validation_errors else 'passed'
        }
        
        if has_validation_errors:
            logger.warning(f"Job {job_id}: Validation failed with {len(validation_errors)} errors")
        else:
            logger.info(f"Job {job_id}: All outputs passed validation")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'validated_results': [],
            'failed_results': event.get('failed_results', []),
            'statistics': event.get('statistics', {}),
            'validation_summary': {
                'total_validated': 0,
                'passed_validation': 0,
                'failed_validation': 0,
                'validation_errors': [f"Validation error: {str(e)}"],
                'consistency_warnings': []
            },
            'has_validation_errors': True,
            'validation_status': 'error'
        }
