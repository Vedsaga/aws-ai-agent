# Agent API - DAG Validation Module

This module provides Directed Acyclic Graph (DAG) validation for agent dependencies in the DomainFlow Agentic Orchestration Platform.

## Overview

The DAG validation module ensures that agent dependencies form valid execution graphs without circular dependencies. It provides functions for:

- **Cycle Detection**: Validates that adding dependencies doesn't create circular references
- **Graph Visualization**: Builds dependency graphs for frontend display
- **Topological Sorting**: Determines correct execution order for agents
- **Playbook Validation**: Validates entire playbooks with multiple agents

## Key Functions

### `validate_dag(agent_id, dependencies, all_agents)`

Validates that adding dependencies to an agent doesn't create cycles using Depth-First Search (DFS).

**Parameters:**
- `agent_id` (str): The ID of the agent being validated
- `dependencies` (List[str]): List of agent IDs that this agent depends on
- `all_agents` (Dict): Dictionary of all agents {agent_id: agent_data}

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_valid, error_message)

**Example:**
```python
agents = {
    'agent-A': {'agent_dependencies': []},
    'agent-B': {'agent_dependencies': ['agent-A']},
}

# Valid dependency
is_valid, error = validate_dag('agent-C', ['agent-B'], agents)
# Returns: (True, None)

# Invalid - creates cycle
is_valid, error = validate_dag('agent-A', ['agent-B'], agents)
# Returns: (False, 'Circular dependency detected: agent-A -> agent-B -> agent-A')
```

### `build_dependency_graph(agent_id, all_agents)`

Builds a visual dependency graph for an agent showing all dependencies.

**Parameters:**
- `agent_id` (str): The ID of the agent to build graph for
- `all_agents` (Dict): Dictionary of all agents

**Returns:**
- `Dict`: Graph with 'nodes' and 'edges' arrays for visualization

**Example:**
```python
agents = {
    'agent-A': {'agent_name': 'Geo Locator', 'agent_class': 'ingestion', 'agent_dependencies': []},
    'agent-B': {'agent_name': 'Classifier', 'agent_class': 'ingestion', 'agent_dependencies': ['agent-A']}
}

graph = build_dependency_graph('agent-B', agents)
# Returns:
# {
#     "nodes": [
#         {"id": "agent-A", "label": "Geo Locator", "class": "ingestion"},
#         {"id": "agent-B", "label": "Classifier", "class": "ingestion"}
#     ],
#     "edges": [
#         {"from": "agent-A", "to": "agent-B"}
#     ]
# }
```

### `topological_sort(nodes, edges)`

Performs topological sort using Kahn's algorithm to determine execution order.

**Parameters:**
- `nodes` (List[str]): List of node IDs
- `edges` (List[Dict]): List of edges [{"from": "node1", "to": "node2"}]

**Returns:**
- `Tuple[bool, List[str], Optional[str]]`: (is_valid, sorted_nodes, error_message)

**Example:**
```python
nodes = ['A', 'B', 'C']
edges = [{'from': 'A', 'to': 'B'}, {'from': 'B', 'to': 'C'}]

is_valid, order, error = topological_sort(nodes, edges)
# Returns: (True, ['A', 'B', 'C'], None)
```

### `validate_playbook_dag(playbook, agent_class, all_agents)`

Validates that a playbook's execution graph is a valid DAG and all agents have the correct class.

**Parameters:**
- `playbook` (Dict): Playbook configuration with agent_execution_graph
- `agent_class` (str): Expected agent class ('ingestion', 'query', 'management')
- `all_agents` (Dict): Dictionary of all agents

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_valid, error_message)

**Example:**
```python
playbook = {
    'agent_execution_graph': {
        'nodes': ['agent-A', 'agent-B'],
        'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
    }
}

is_valid, error = validate_playbook_dag(playbook, 'ingestion', agents)
# Returns: (True, None)
```

## Graph Structures Tested

### Linear Chain
```
A → B → C
```
Valid execution order: A, B, C

### Parallel Dependencies
```
A ↘
    C
B ↗
```
Valid execution order: A, B, C (or B, A, C)

### Diamond Structure
```
    A
   ↙ ↘
  B   C
   ↘ ↙
    D
```
Valid execution order: A, B, C, D (or A, C, B, D)

### Circular (Invalid)
```
A → B → C → A
```
Invalid - cycle detected

## Running Tests

Install dependencies:
```bash
pip install -r requirements.txt
```

Run all tests:
```bash
pytest test_dag_validator.py -v
```

Run with coverage:
```bash
pytest test_dag_validator.py --cov=dag_validator --cov-report=html
```

## Test Coverage

The test suite includes:

- ✅ Linear dependency chains
- ✅ Parallel dependencies
- ✅ Diamond dependency structures
- ✅ Simple circular dependencies (2 nodes)
- ✅ Complex circular dependencies (3+ nodes)
- ✅ Self-dependencies
- ✅ Non-existent agent references
- ✅ Empty dependencies
- ✅ Graph visualization
- ✅ Topological sorting
- ✅ Playbook validation
- ✅ Agent class verification
- ✅ Transitive dependency resolution

## Algorithm Details

### DFS Cycle Detection

The `validate_dag` function uses Depth-First Search with a recursion stack to detect cycles:

1. Maintain a `visited` set for all explored nodes
2. Maintain a `rec_stack` set for nodes in current recursion path
3. For each dependency:
   - If not visited, recursively explore
   - If in recursion stack, cycle detected
4. Backtrack by removing from recursion stack

**Time Complexity:** O(V + E) where V = vertices, E = edges
**Space Complexity:** O(V) for visited and recursion stack

### Kahn's Algorithm (Topological Sort)

The `topological_sort` function uses Kahn's algorithm:

1. Calculate in-degree for each node
2. Add all nodes with in-degree 0 to queue
3. Process queue:
   - Remove node and add to sorted list
   - Reduce in-degree of neighbors
   - Add neighbors with in-degree 0 to queue
4. If all nodes processed, graph is valid DAG

**Time Complexity:** O(V + E)
**Space Complexity:** O(V)

## Integration with Agent Handler

The DAG validator is used by the Agent Handler Lambda to:

1. **Agent Creation**: Validate dependencies before creating agent
2. **Agent Update**: Validate new dependencies before updating
3. **Agent Retrieval**: Build dependency graph for visualization
4. **Domain Creation**: Validate playbook execution graphs

## Error Messages

The module provides clear error messages:

- `"Circular dependency detected: agent-A -> agent-B -> agent-A"` - Shows the cycle path
- `"Dependency agent not found: agent-X"` - Missing agent reference
- `"Agent agent-X is class 'query', expected 'ingestion'"` - Wrong agent class in playbook
- `"Cycle detected in graph. Nodes involved: agent-A, agent-B"` - Cycle in topological sort

## Future Enhancements

- [ ] Add graph visualization export (DOT format)
- [ ] Add performance metrics for large graphs
- [ ] Add graph complexity analysis
- [ ] Add dependency impact analysis (what breaks if agent removed)
- [ ] Add graph optimization suggestions
