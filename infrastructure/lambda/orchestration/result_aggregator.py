"""
Result Aggregation Lambda Function

Collects outputs from all executed agents, preserves execution order,
handles partial failures, and prepares data for validation.

Requirements: 7.5
"""

import json
import logging
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def aggregate_results(agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple agent executions.
    
    Args:
        agent_results: List of agent execution results
    
    Returns:
        Aggregated results with metadata
    """
    successful_results = []
    failed_results = []
    total_execution_time_ms = 0
    
    for result in agent_results:
        agent_name = result.get('agent_name', 'unknown')
        agent_id = result.get('agent_id', 'unknown')
        status = result.get('status', 'unknown')
        execution_time_ms = result.get('execution_time_ms', 0)
        
        total_execution_time_ms += execution_time_ms
        
        if status == 'success':
            successful_results.append({
                'agent_name': agent_name,
                'agent_id': agent_id,
                'output': result.get('output', {}),
                'execution_time_ms': execution_time_ms
            })
            logger.info(f"Agent {agent_name} succeeded in {execution_time_ms}ms")
        else:
            error_message = result.get('error_message', 'Unknown error')
            failed_results.append({
                'agent_name': agent_name,
                'agent_id': agent_id,
                'error_message': error_message,
                'execution_time_ms': execution_time_ms
            })
            logger.warning(f"Agent {agent_name} failed: {error_message}")
    
    # Calculate statistics
    total_agents = len(agent_results)
    successful_count = len(successful_results)
    failed_count = len(failed_results)
    success_rate = (successful_count / total_agents * 100) if total_agents > 0 else 0
    
    aggregated = {
        'successful_results': successful_results,
        'failed_results': failed_results,
        'statistics': {
            'total_agents': total_agents,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'success_rate': round(success_rate, 2),
            'total_execution_time_ms': total_execution_time_ms
        },
        'has_failures': failed_count > 0,
        'all_failed': successful_count == 0
    }
    
    logger.info(
        f"Aggregation complete: {successful_count}/{total_agents} agents succeeded "
        f"({success_rate:.1f}% success rate)"
    )
    
    return aggregated


def preserve_execution_order(
    agent_results: List[Dict[str, Any]],
    execution_plan: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Reorder agent results to match the original execution plan order.
    
    Args:
        agent_results: List of agent results (may be out of order)
        execution_plan: Original execution plan with agent order
    
    Returns:
        Ordered list of agent results
    """
    # Create a map of agent_id to result
    result_map = {
        result.get('agent_id'): result
        for result in agent_results
    }
    
    # Reorder based on execution plan
    ordered_results = []
    for plan_item in execution_plan:
        agent_id = plan_item.get('agent_id')
        if agent_id in result_map:
            ordered_results.append(result_map[agent_id])
        else:
            # Agent didn't execute (shouldn't happen, but handle gracefully)
            logger.warning(f"Agent {agent_id} in plan but no result found")
            ordered_results.append({
                'agent_name': plan_item.get('agent_name', agent_id),
                'agent_id': agent_id,
                'output': {},
                'status': 'error',
                'execution_time_ms': 0,
                'error_message': 'Agent did not execute'
            })
    
    return ordered_results


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for result aggregation.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "agent_results": [
            {
                "agent_name": "string",
                "agent_id": "string",
                "output": {...},
                "status": "success|error",
                "execution_time_ms": 123,
                "error_message": "string"  // if error
            }
        ],
        "execution_plan": [
            {
                "agent_id": "string",
                "agent_name": "string",
                "level": 0
            }
        ]
    }
    
    Returns:
        Aggregated results ready for validation
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        agent_results = event.get('agent_results', [])
        execution_plan = event.get('execution_plan', [])
        
        logger.info(f"Aggregating results for job {job_id}: {len(agent_results)} agents")
        
        # Preserve execution order if plan provided
        if execution_plan:
            agent_results = preserve_execution_order(agent_results, execution_plan)
        
        # Aggregate results
        aggregated = aggregate_results(agent_results)
        
        # Add job metadata
        aggregated['job_id'] = job_id
        aggregated['tenant_id'] = tenant_id
        
        # Determine overall status
        if aggregated['all_failed']:
            aggregated['overall_status'] = 'failed'
            logger.error(f"Job {job_id}: All agents failed")
        elif aggregated['has_failures']:
            aggregated['overall_status'] = 'partial_success'
            logger.warning(f"Job {job_id}: Partial success with some failures")
        else:
            aggregated['overall_status'] = 'success'
            logger.info(f"Job {job_id}: All agents succeeded")
        
        return aggregated
        
    except Exception as e:
        logger.error(f"Error in result aggregation: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'successful_results': [],
            'failed_results': [],
            'statistics': {
                'total_agents': 0,
                'successful_count': 0,
                'failed_count': 0,
                'success_rate': 0,
                'total_execution_time_ms': 0
            },
            'has_failures': True,
            'all_failed': True,
            'overall_status': 'failed',
            'error_message': f"Aggregation error: {str(e)}"
        }
