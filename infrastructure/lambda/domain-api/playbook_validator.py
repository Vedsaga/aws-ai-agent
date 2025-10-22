"""
Playbook Validation Module
Provides functions for validating domain playbooks with agent execution graphs
"""

from typing import Dict, List, Tuple, Optional, Any
import logging
import sys
import os

# Add parent directory to path to import dag_validator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-api'))
from dag_validator import topological_sort

logger = logging.getLogger()


def validate_agent_class(
    agent_id: str,
    expected_class: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Verifies that an agent belongs to the expected class.
    
    Args:
        agent_id: The ID of the agent to validate
        expected_class: Expected agent class ('ingestion', 'query', 'management')
        all_agents: Dictionary of all agents {agent_id: agent_data}
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if agent has correct class
        - (False, error_message) if agent has wrong class or doesn't exist
    
    Example:
        >>> agents = {
        ...     'agent-A': {'agent_class': 'ingestion', 'agent_name': 'Agent A'}
        ... }
        >>> validate_agent_class('agent-A', 'ingestion', agents)
        (True, None)
        >>> validate_agent_class('agent-A', 'query', agents)
        (False, "Agent agent-A is class 'ingestion', expected 'query'")
    """
    if agent_id not in all_agents:
        return False, f"Agent not found: {agent_id}"
    
    agent = all_agents[agent_id]
    actual_class = agent.get('agent_class')
    
    if actual_class != expected_class:
        agent_name = agent.get('agent_name', agent_id)
        return False, f"Agent {agent_id} ({agent_name}) is class '{actual_class}', expected '{expected_class}'"
    
    return True, None


def validate_playbook(
    playbook: Dict[str, Any],
    playbook_type: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Validates that a playbook's agent_execution_graph is a valid DAG
    and all agents belong to the correct class.
    
    This is the main validation function for domain playbooks. It performs:
    1. Structure validation (graph has nodes and edges)
    2. Agent existence validation (all referenced agents exist)
    3. Agent class validation (all agents match playbook type)
    4. DAG validation (no circular dependencies)
    
    Args:
        playbook: Playbook configuration with agent_execution_graph
        playbook_type: Playbook type ('ingestion', 'query', 'management')
        all_agents: Dictionary of all agents {agent_id: agent_data}
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if playbook is valid
        - (False, error_message) if validation fails
    
    Example:
        >>> playbook = {
        ...     'agent_execution_graph': {
        ...         'nodes': ['agent-A', 'agent-B'],
        ...         'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
        ...     }
        ... }
        >>> agents = {
        ...     'agent-A': {'agent_class': 'query', 'agent_name': 'Agent A'},
        ...     'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'}
        ... }
        >>> validate_playbook(playbook, 'query', agents)
        (True, None)
    """
    # Validate playbook structure
    if not playbook:
        return False, "Playbook cannot be empty"
    
    if "agent_execution_graph" not in playbook:
        return False, "Playbook missing agent_execution_graph"
    
    graph = playbook["agent_execution_graph"]
    
    if not isinstance(graph, dict):
        return False, "agent_execution_graph must be a dictionary"
    
    if "nodes" not in graph or "edges" not in graph:
        return False, "agent_execution_graph must contain 'nodes' and 'edges'"
    
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    if not isinstance(nodes, list):
        return False, "agent_execution_graph.nodes must be a list"
    
    if not isinstance(edges, list):
        return False, "agent_execution_graph.edges must be a list"
    
    if len(nodes) == 0:
        return False, "Playbook must contain at least one agent"
    
    # Validate all agents exist and have correct class
    for agent_id in nodes:
        # Check agent exists
        if agent_id not in all_agents:
            return False, f"Agent not found in playbook: {agent_id}"
        
        # Check agent class matches playbook type
        is_valid, error = validate_agent_class(agent_id, playbook_type, all_agents)
        if not is_valid:
            return False, error
    
    # Validate edges structure
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            return False, f"Edge {i} must be a dictionary"
        
        if "from" not in edge or "to" not in edge:
            return False, f"Edge {i} must contain 'from' and 'to' fields"
        
        from_node = edge["from"]
        to_node = edge["to"]
        
        if from_node not in nodes:
            return False, f"Edge references non-existent node: {from_node}"
        
        if to_node not in nodes:
            return False, f"Edge references non-existent node: {to_node}"
    
    # Validate DAG (no cycles) using topological sort
    is_valid, _, error = topological_sort(nodes, edges)
    if not is_valid:
        return False, f"Playbook contains circular dependencies: {error}"
    
    return True, None


def validate_domain_playbooks(
    ingestion_playbook: Dict[str, Any],
    query_playbook: Dict[str, Any],
    management_playbook: Dict[str, Any],
    all_agents: Dict[str, Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Validates all three playbooks for a domain configuration.
    
    Args:
        ingestion_playbook: Ingestion playbook configuration
        query_playbook: Query playbook configuration
        management_playbook: Management playbook configuration
        all_agents: Dictionary of all agents
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> ingestion = {'agent_execution_graph': {'nodes': ['ing-1'], 'edges': []}}
        >>> query = {'agent_execution_graph': {'nodes': ['qry-1'], 'edges': []}}
        >>> management = {'agent_execution_graph': {'nodes': ['mgmt-1'], 'edges': []}}
        >>> agents = {
        ...     'ing-1': {'agent_class': 'ingestion'},
        ...     'qry-1': {'agent_class': 'query'},
        ...     'mgmt-1': {'agent_class': 'management'}
        ... }
        >>> validate_domain_playbooks(ingestion, query, management, agents)
        (True, None)
    """
    # Validate ingestion playbook
    is_valid, error = validate_playbook(ingestion_playbook, 'ingestion', all_agents)
    if not is_valid:
        return False, f"Ingestion playbook validation failed: {error}"
    
    # Validate query playbook
    is_valid, error = validate_playbook(query_playbook, 'query', all_agents)
    if not is_valid:
        return False, f"Query playbook validation failed: {error}"
    
    # Validate management playbook
    is_valid, error = validate_playbook(management_playbook, 'management', all_agents)
    if not is_valid:
        return False, f"Management playbook validation failed: {error}"
    
    return True, None


def get_playbook_agent_count(playbook: Dict[str, Any]) -> int:
    """
    Returns the number of agents in a playbook.
    
    Args:
        playbook: Playbook configuration
    
    Returns:
        Number of agents in the playbook
    """
    if not playbook or "agent_execution_graph" not in playbook:
        return 0
    
    graph = playbook["agent_execution_graph"]
    nodes = graph.get("nodes", [])
    
    return len(nodes)


def get_playbook_agents(playbook: Dict[str, Any]) -> List[str]:
    """
    Returns the list of agent IDs in a playbook.
    
    Args:
        playbook: Playbook configuration
    
    Returns:
        List of agent IDs
    """
    if not playbook or "agent_execution_graph" not in playbook:
        return []
    
    graph = playbook["agent_execution_graph"]
    return graph.get("nodes", [])
