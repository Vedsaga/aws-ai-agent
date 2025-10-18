"""
Build Execution Plan Lambda Function

Builds execution plan using topological sort based on dependency graph.
Assigns execution levels for parallel execution within levels.

Requirements: 7.3
"""

import json
import logging
from typing import Dict, Any, List, Set
from collections import defaultdict, deque

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def topological_sort(agent_ids: List[str], edges: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Perform topological sort to determine execution levels.
    
    Args:
        agent_ids: List of all agent IDs
        edges: List of dependency edges [{"from": "parent", "to": "child"}]
    
    Returns:
        List of execution levels, where each level is a list of agent IDs
        that can be executed in parallel
    """
    # Build adjacency list and in-degree map
    graph = defaultdict(list)
    in_degree = {agent_id: 0 for agent_id in agent_ids}
    
    for edge in edges:
        parent = edge.get('from')
        child = edge.get('to')
        
        if parent in in_degree and child in in_degree:
            graph[parent].append(child)
            in_degree[child] += 1
    
    # Find all nodes with in-degree 0 (no dependencies)
    queue = deque([agent_id for agent_id, degree in in_degree.items() if degree == 0])
    
    levels = []
    
    while queue:
        # All agents in current queue can execute in parallel (same level)
        current_level = list(queue)
        levels.append(current_level)
        
        # Process all agents in current level
        next_queue = []
        for agent_id in current_level:
            # Reduce in-degree for all children
            for child in graph[agent_id]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_queue.append(child)
        
        queue = deque(next_queue)
    
    # Check if all agents were processed (no cycles)
    processed_count = sum(len(level) for level in levels)
    if processed_count < len(agent_ids):
        unprocessed = [aid for aid in agent_ids if in_degree[aid] > 0]
        logger.error(f"Circular dependency detected. Unprocessed agents: {unprocessed}")
        raise ValueError(f"Circular dependency detected involving agents: {unprocessed}")
    
    return levels


def build_execution_plan(
    agent_ids: List[str],
    edges: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build execution plan with levels and dependencies.
    
    Args:
        agent_ids: List of agent IDs
        edges: List of dependency edges
    
    Returns:
        Execution plan with agent metadata
    """
    # Perform topological sort
    levels = topological_sort(agent_ids, edges)
    
    # Build dependency map for quick lookup
    dependencies = {}
    for edge in edges:
        child = edge.get('to')
        parent = edge.get('from')
        dependencies[child] = parent
    
    # Build execution plan
    execution_plan = []
    
    for level_num, level_agents in enumerate(levels):
        for agent_id in level_agents:
            execution_plan.append({
                'agent_id': agent_id,
                'level': level_num,
                'depends_on': dependencies.get(agent_id),
                'can_parallel': True  # All agents in same level can run in parallel
            })
    
    logger.info(
        f"Built execution plan with {len(levels)} levels, "
        f"{len(execution_plan)} total agents"
    )
    
    return execution_plan


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for building execution plan.
    
    Event structure:
    {
        "job_id": "string",
        "tenant_id": "string",
        "agent_ids": ["agent1", "agent2", ...],
        "edges": [
            {"from": "parent_agent", "to": "child_agent"}
        ]
    }
    
    Returns:
        Execution plan with levels
    """
    try:
        job_id = event.get('job_id')
        tenant_id = event.get('tenant_id')
        agent_ids = event.get('agent_ids', [])
        edges = event.get('edges', [])
        
        if not agent_ids:
            logger.warning("No agents to execute")
            return {
                'job_id': job_id,
                'tenant_id': tenant_id,
                'execution_plan': [],
                'level_count': 0,
                'status': 'success'
            }
        
        logger.info(
            f"Building execution plan for {len(agent_ids)} agents "
            f"with {len(edges)} dependencies"
        )
        
        # Build execution plan
        execution_plan = build_execution_plan(agent_ids, edges)
        
        # Calculate statistics
        level_count = max([item['level'] for item in execution_plan]) + 1 if execution_plan else 0
        parallel_count = len([item for item in execution_plan if item['level'] == 0])
        dependent_count = len([item for item in execution_plan if item['depends_on']])
        
        logger.info(
            f"Execution plan: {level_count} levels, "
            f"{parallel_count} parallel agents, "
            f"{dependent_count} dependent agents"
        )
        
        return {
            'job_id': job_id,
            'tenant_id': tenant_id,
            'execution_plan': execution_plan,
            'level_count': level_count,
            'statistics': {
                'total_agents': len(agent_ids),
                'parallel_agents': parallel_count,
                'dependent_agents': dependent_count,
                'dependency_edges': len(edges)
            },
            'status': 'success'
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'execution_plan': [],
            'level_count': 0,
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"Error building execution plan: {str(e)}", exc_info=True)
        return {
            'job_id': event.get('job_id', 'unknown'),
            'tenant_id': event.get('tenant_id', 'unknown'),
            'execution_plan': [],
            'level_count': 0,
            'status': 'error',
            'error_message': f"Execution plan error: {str(e)}"
        }
