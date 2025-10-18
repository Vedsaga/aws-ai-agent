"""
Agent Utilities

Helper functions for agent deployment, configuration, and testing.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_seed_data() -> Dict[str, Any]:
    """
    Load seed data for custom agents and configurations.
    
    Returns:
        Dict containing seed data
    """
    try:
        with open('seed_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("seed_data.json not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse seed_data.json: {str(e)}")
        return {}


def get_agent_config(agent_id: str, seed_data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Get agent configuration by ID from seed data.
    
    Args:
        agent_id: Agent identifier
        seed_data: Optional seed data dict (will load if not provided)
    
    Returns:
        Agent configuration or None if not found
    """
    if seed_data is None:
        seed_data = load_seed_data()
    
    custom_agents = seed_data.get('custom_agents', [])
    
    for agent in custom_agents:
        if agent.get('agent_id') == agent_id:
            return agent
    
    return None


def validate_dependency_graph(edges: List[Dict[str, str]]) -> tuple[bool, Optional[str]]:
    """
    Validate dependency graph for circular dependencies and multi-level chains.
    
    Args:
        edges: List of dependency edges [{"from": "agent1", "to": "agent2"}]
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Build adjacency list
    graph = {}
    in_degree = {}
    
    for edge in edges:
        from_agent = edge['from']
        to_agent = edge['to']
        
        if from_agent not in graph:
            graph[from_agent] = []
        graph[from_agent].append(to_agent)
        
        if to_agent not in in_degree:
            in_degree[to_agent] = 0
        in_degree[to_agent] += 1
        
        if from_agent not in in_degree:
            in_degree[from_agent] = 0
    
    # Check for multi-level dependencies (each agent can have max 1 parent)
    for agent, degree in in_degree.items():
        if degree > 1:
            return False, f"Agent '{agent}' has multiple parents (multi-level dependencies not allowed)"
    
    # Check for circular dependencies using DFS
    visited = set()
    rec_stack = set()
    
    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return False, "Circular dependency detected"
    
    return True, None


def compute_execution_levels(edges: List[Dict[str, str]], all_agents: List[str]) -> List[Dict[str, Any]]:
    """
    Compute execution levels for agents based on dependency graph.
    Uses topological sort to determine execution order.
    
    Args:
        edges: List of dependency edges
        all_agents: List of all agent IDs in playbook
    
    Returns:
        List of execution levels with agents at each level
    """
    # Build adjacency list and in-degree map
    graph = {agent: [] for agent in all_agents}
    in_degree = {agent: 0 for agent in all_agents}
    
    for edge in edges:
        from_agent = edge['from']
        to_agent = edge['to']
        graph[from_agent].append(to_agent)
        in_degree[to_agent] += 1
    
    # Topological sort with level tracking
    levels = []
    current_level = [agent for agent in all_agents if in_degree[agent] == 0]
    
    while current_level:
        levels.append({
            'level': len(levels),
            'agents': sorted(current_level)
        })
        
        next_level = []
        for agent in current_level:
            for neighbor in graph[agent]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_level.append(neighbor)
        
        current_level = next_level
    
    return levels


def format_agent_output_for_display(output: Dict[str, Any]) -> str:
    """
    Format agent output for human-readable display.
    
    Args:
        output: Agent output dict
    
    Returns:
        Formatted string
    """
    agent_name = output.get('agent_name', 'Unknown')
    status = output.get('status', 'unknown')
    execution_time = output.get('execution_time_ms', 0)
    agent_output = output.get('output', {})
    
    lines = [
        f"Agent: {agent_name}",
        f"Status: {status}",
        f"Execution Time: {execution_time}ms",
        "Output:"
    ]
    
    for key, value in agent_output.items():
        if isinstance(value, (list, dict)):
            lines.append(f"  {key}: {json.dumps(value, indent=4)}")
        else:
            lines.append(f"  {key}: {value}")
    
    if output.get('error_message'):
        lines.append(f"Error: {output['error_message']}")
    
    return '\n'.join(lines)


def create_test_event(
    raw_text: str,
    agent_config: Dict[str, Any],
    job_id: str = "test-job",
    tenant_id: str = "test-tenant",
    parent_output: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create a test Lambda event for agent testing.
    
    Args:
        raw_text: Input text
        agent_config: Agent configuration
        job_id: Job identifier
        tenant_id: Tenant identifier
        parent_output: Optional parent agent output
    
    Returns:
        Lambda event dict
    """
    event = {
        'job_id': job_id,
        'tenant_id': tenant_id,
        'raw_text': raw_text,
        'agent_config': agent_config
    }
    
    if parent_output:
        event['parent_output'] = parent_output
    
    return event


class MockLambdaContext:
    """Mock Lambda context for testing"""
    
    def __init__(self, timeout_ms: int = 300000):
        self.timeout_ms = timeout_ms
        self.start_time = None
    
    def get_remaining_time_in_millis(self) -> int:
        """Return remaining execution time"""
        if self.start_time is None:
            import time
            self.start_time = time.time()
        
        import time
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        return max(0, self.timeout_ms - elapsed_ms)
