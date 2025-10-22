"""
DAG Validation Module
Provides functions for validating Directed Acyclic Graphs (DAGs) in agent dependencies
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import logging

logger = logging.getLogger()


def validate_dag(
    agent_id: str,
    dependencies: List[str],
    all_agents: Dict[str, Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Validates that adding dependencies doesn't create cycles.
    Uses DFS (Depth-First Search) to detect cycles in the dependency graph.
    
    Args:
        agent_id: The ID of the agent being validated
        dependencies: List of agent IDs that this agent depends on
        all_agents: Dictionary of all agents {agent_id: agent_data}
    
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if DAG is valid
        - (False, error_message) if cycle detected
    
    Example:
        >>> agents = {
        ...     'agent-A': {'agent_dependencies': []},
        ...     'agent-B': {'agent_dependencies': ['agent-A']},
        ...     'agent-C': {'agent_dependencies': ['agent-B']}
        ... }
        >>> validate_dag('agent-C', ['agent-B'], agents)
        (True, None)
        >>> validate_dag('agent-A', ['agent-C'], agents)
        (False, 'Circular dependency detected: agent-A -> agent-C -> agent-B -> agent-A')
    """
    # Validate that all dependencies exist
    for dep_id in dependencies:
        if dep_id not in all_agents:
            return False, f"Dependency agent not found: {dep_id}"
    
    # Build a temporary graph with the new dependencies
    temp_graph = {}
    for aid, agent_data in all_agents.items():
        temp_graph[aid] = agent_data.get('agent_dependencies', [])
    
    # Add the new agent with its dependencies
    temp_graph[agent_id] = dependencies
    
    # Check for cycles using DFS
    visited = set()
    rec_stack = set()
    path = []
    
    def has_cycle(node: str) -> Tuple[bool, Optional[List[str]]]:
        """
        DFS helper function to detect cycles.
        
        Returns:
            Tuple of (has_cycle, cycle_path)
        """
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Get dependencies of current node
        node_deps = temp_graph.get(node, [])
        
        for dep in node_deps:
            if dep not in visited:
                # Recursively check dependency
                cycle_found, cycle_path = has_cycle(dep)
                if cycle_found:
                    return True, cycle_path
            elif dep in rec_stack:
                # Cycle detected - build the cycle path
                cycle_start_idx = path.index(dep)
                cycle_path = path[cycle_start_idx:] + [dep]
                return True, cycle_path
        
        # Backtrack
        rec_stack.remove(node)
        path.pop()
        return False, None
    
    # Check if adding new dependencies creates a cycle
    cycle_found, cycle_path = has_cycle(agent_id)
    
    if cycle_found:
        cycle_str = ' -> '.join(cycle_path)
        return False, f"Circular dependency detected: {cycle_str}"
    
    return True, None


def build_dependency_graph(
    agent_id: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Builds a visual dependency graph for an agent.
    Returns nodes and edges for frontend visualization.
    
    Args:
        agent_id: The ID of the agent to build graph for
        all_agents: Dictionary of all agents {agent_id: agent_data}
    
    Returns:
        Dictionary with 'nodes' and 'edges' arrays:
        {
            "nodes": [
                {"id": "agent-A", "label": "Agent A", "class": "ingestion"},
                {"id": "agent-B", "label": "Agent B", "class": "query"}
            ],
            "edges": [
                {"from": "agent-A", "to": "agent-B"}
            ]
        }
    
    Example:
        >>> agents = {
        ...     'agent-A': {'agent_name': 'Agent A', 'agent_class': 'ingestion', 'agent_dependencies': []},
        ...     'agent-B': {'agent_name': 'Agent B', 'agent_class': 'query', 'agent_dependencies': ['agent-A']}
        ... }
        >>> graph = build_dependency_graph('agent-B', agents)
        >>> len(graph['nodes'])
        2
        >>> len(graph['edges'])
        1
    """
    nodes = []
    edges = []
    visited = set()
    
    def traverse(node_id: str) -> None:
        """
        Recursively traverse the dependency tree.
        """
        if node_id in visited:
            return
        
        if node_id not in all_agents:
            logger.warning(f"Agent not found in graph traversal: {node_id}")
            return
        
        visited.add(node_id)
        
        agent = all_agents[node_id]
        nodes.append({
            "id": node_id,
            "label": agent.get("agent_name", node_id),
            "class": agent.get("agent_class", "unknown")
        })
        
        # Traverse dependencies
        for dep_id in agent.get("agent_dependencies", []):
            edges.append({"from": dep_id, "to": node_id})
            traverse(dep_id)
    
    # Start traversal from the target agent
    traverse(agent_id)
    
    return {
        "nodes": nodes,
        "edges": edges
    }


def topological_sort(
    nodes: List[str],
    edges: List[Dict[str, str]]
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Performs topological sort on a graph using Kahn's algorithm.
    Returns execution order for agents.
    
    Args:
        nodes: List of node IDs
        edges: List of edges [{"from": "node1", "to": "node2"}]
    
    Returns:
        Tuple of (is_valid, sorted_nodes, error_message)
        - (True, sorted_list, None) if DAG is valid
        - (False, [], error_message) if cycle detected
    
    Example:
        >>> nodes = ['A', 'B', 'C']
        >>> edges = [{'from': 'A', 'to': 'B'}, {'from': 'B', 'to': 'C'}]
        >>> is_valid, order, err = topological_sort(nodes, edges)
        >>> is_valid
        True
        >>> order
        ['A', 'B', 'C']
    """
    # Build adjacency list and in-degree map
    adj_list = {node: [] for node in nodes}
    in_degree = {node: 0 for node in nodes}
    
    for edge in edges:
        from_node = edge["from"]
        to_node = edge["to"]
        
        if from_node not in adj_list or to_node not in adj_list:
            return False, [], f"Edge references non-existent node: {from_node} -> {to_node}"
        
        adj_list[from_node].append(to_node)
        in_degree[to_node] += 1
    
    # Find all nodes with no incoming edges
    queue = [node for node in nodes if in_degree[node] == 0]
    sorted_nodes = []
    
    while queue:
        # Remove node from queue
        node = queue.pop(0)
        sorted_nodes.append(node)
        
        # Reduce in-degree for neighbors
        for neighbor in adj_list[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check if all nodes were processed
    if len(sorted_nodes) != len(nodes):
        # Cycle detected - find remaining nodes
        remaining = [node for node in nodes if node not in sorted_nodes]
        return False, [], f"Cycle detected in graph. Nodes involved: {', '.join(remaining)}"
    
    return True, sorted_nodes, None


def validate_playbook_dag(
    playbook: Dict[str, Any],
    agent_class: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Validates that a playbook's agent_execution_graph is a valid DAG
    and all agents belong to the correct class.
    
    Args:
        playbook: Playbook configuration with agent_execution_graph
        agent_class: Expected agent class ('ingestion', 'query', 'management')
        all_agents: Dictionary of all agents {agent_id: agent_data}
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> playbook = {
        ...     'agent_execution_graph': {
        ...         'nodes': ['agent-A', 'agent-B'],
        ...         'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
        ...     }
        ... }
        >>> agents = {
        ...     'agent-A': {'agent_class': 'query', 'agent_dependencies': []},
        ...     'agent-B': {'agent_class': 'query', 'agent_dependencies': ['agent-A']}
        ... }
        >>> validate_playbook_dag(playbook, 'query', agents)
        (True, None)
    """
    if "agent_execution_graph" not in playbook:
        return False, "Playbook missing agent_execution_graph"
    
    graph = playbook["agent_execution_graph"]
    
    if "nodes" not in graph or "edges" not in graph:
        return False, "agent_execution_graph must contain 'nodes' and 'edges'"
    
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    # Validate all agents exist and have correct class
    for agent_id in nodes:
        if agent_id not in all_agents:
            return False, f"Agent not found: {agent_id}"
        
        agent = all_agents[agent_id]
        if agent.get("agent_class") != agent_class:
            return False, f"Agent {agent_id} is class '{agent.get('agent_class')}', expected '{agent_class}'"
    
    # Validate DAG (no cycles)
    is_valid, _, error = topological_sort(nodes, edges)
    if not is_valid:
        return False, f"Playbook contains circular dependencies: {error}"
    
    return True, None


def get_agent_dependencies(
    agent_id: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> List[str]:
    """
    Helper function to get dependencies for an agent.
    
    Args:
        agent_id: The agent ID
        all_agents: Dictionary of all agents
    
    Returns:
        List of dependency agent IDs
    """
    if agent_id not in all_agents:
        return []
    
    return all_agents[agent_id].get("agent_dependencies", [])


def find_all_dependencies(
    agent_id: str,
    all_agents: Dict[str, Dict[str, Any]]
) -> Set[str]:
    """
    Finds all transitive dependencies for an agent (recursive).
    
    Args:
        agent_id: The agent ID
        all_agents: Dictionary of all agents
    
    Returns:
        Set of all dependency agent IDs (direct and indirect)
    
    Example:
        >>> agents = {
        ...     'A': {'agent_dependencies': []},
        ...     'B': {'agent_dependencies': ['A']},
        ...     'C': {'agent_dependencies': ['B']}
        ... }
        >>> find_all_dependencies('C', agents)
        {'A', 'B'}
    """
    all_deps = set()
    visited = set()
    
    def traverse(node_id: str) -> None:
        if node_id in visited or node_id not in all_agents:
            return
        
        visited.add(node_id)
        deps = all_agents[node_id].get("agent_dependencies", [])
        
        for dep_id in deps:
            all_deps.add(dep_id)
            traverse(dep_id)
    
    traverse(agent_id)
    return all_deps
