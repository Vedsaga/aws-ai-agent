# Domain API - Playbook Validation

This module provides playbook validation functionality for the Domain Management API. It validates that domain playbooks (ingestion, query, management) have valid agent execution graphs with no circular dependencies and that all agents belong to the correct class.

## Overview

The Domain Management API allows administrators to configure domains with three playbooks:
- **Ingestion Playbook**: Defines how ingestion agents process incoming data
- **Query Playbook**: Defines how query agents retrieve and synthesize data
- **Management Playbook**: Defines how management agents update existing data

Each playbook contains an `agent_execution_graph` with nodes (agent IDs) and edges (dependencies).

## Module: playbook_validator.py

### Core Functions

#### `validate_agent_class(agent_id, expected_class, all_agents)`

Verifies that an agent belongs to the expected class.

**Parameters:**
- `agent_id` (str): The ID of the agent to validate
- `expected_class` (str): Expected agent class ('ingestion', 'query', 'management')
- `all_agents` (dict): Dictionary of all agents {agent_id: agent_data}

**Returns:**
- `(True, None)` if agent has correct class
- `(False, error_message)` if agent has wrong class or doesn't exist

**Example:**
```python
agents = {
    'agent-A': {'agent_class': 'ingestion', 'agent_name': 'Agent A'}
}
is_valid, error = validate_agent_class('agent-A', 'ingestion', agents)
# Returns: (True, None)
```

#### `validate_playbook(playbook, playbook_type, all_agents)`

Main validation function for domain playbooks. Performs:
1. Structure validation (graph has nodes and edges)
2. Agent existence validation (all referenced agents exist)
3. Agent class validation (all agents match playbook type)
4. DAG validation (no circular dependencies)

**Parameters:**
- `playbook` (dict): Playbook configuration with agent_execution_graph
- `playbook_type` (str): Playbook type ('ingestion', 'query', 'management')
- `all_agents` (dict): Dictionary of all agents

**Returns:**
- `(True, None)` if playbook is valid
- `(False, error_message)` if validation fails

**Example:**
```python
playbook = {
    'agent_execution_graph': {
        'nodes': ['agent-A', 'agent-B'],
        'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
    }
}
agents = {
    'agent-A': {'agent_class': 'query', 'agent_name': 'Agent A'},
    'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'}
}
is_valid, error = validate_playbook(playbook, 'query', agents)
# Returns: (True, None)
```

#### `validate_domain_playbooks(ingestion_playbook, query_playbook, management_playbook, all_agents)`

Validates all three playbooks for a domain configuration.

**Parameters:**
- `ingestion_playbook` (dict): Ingestion playbook configuration
- `query_playbook` (dict): Query playbook configuration
- `management_playbook` (dict): Management playbook configuration
- `all_agents` (dict): Dictionary of all agents

**Returns:**
- `(True, None)` if all playbooks are valid
- `(False, error_message)` if any validation fails

**Example:**
```python
ingestion = {'agent_execution_graph': {'nodes': ['ing-1'], 'edges': []}}
query = {'agent_execution_graph': {'nodes': ['qry-1'], 'edges': []}}
management = {'agent_execution_graph': {'nodes': ['mgmt-1'], 'edges': []}}
agents = {
    'ing-1': {'agent_class': 'ingestion'},
    'qry-1': {'agent_class': 'query'},
    'mgmt-1': {'agent_class': 'management'}
}
is_valid, error = validate_domain_playbooks(ingestion, query, management, agents)
# Returns: (True, None)
```

### Helper Functions

#### `get_playbook_agent_count(playbook)`

Returns the number of agents in a playbook.

#### `get_playbook_agents(playbook)`

Returns the list of agent IDs in a playbook.

## Validation Rules

### Playbook Structure

A valid playbook must:
- Contain an `agent_execution_graph` field
- Have `nodes` array (list of agent IDs)
- Have `edges` array (list of {from, to} objects)
- Contain at least one agent

### Agent Class Validation

All agents in a playbook must:
- Exist in the system
- Have the correct `agent_class` matching the playbook type
  - Ingestion playbook → all agents must be class 'ingestion'
  - Query playbook → all agents must be class 'query'
  - Management playbook → all agents must be class 'management'

### DAG Validation

The agent execution graph must:
- Form a Directed Acyclic Graph (DAG)
- Have no circular dependencies
- Have valid edges (both from and to nodes must exist)

### Error Messages

The validator provides clear error messages:
- `"Agent not found: agent-X"` - Referenced agent doesn't exist
- `"Agent agent-X (Agent Name) is class 'query', expected 'ingestion'"` - Wrong agent class
- `"Playbook contains circular dependencies: ..."` - Cycle detected
- `"Edge references non-existent node: agent-X"` - Invalid edge
- `"Playbook must contain at least one agent"` - Empty playbook

## Testing

Run the test suite:

```bash
cd infrastructure/lambda/domain-api
../agent-api/venv/bin/python -m pytest test_playbook_validator.py -v
```

### Test Coverage

The test suite includes 32 tests covering:
- ✅ Valid agent class validation
- ✅ Wrong agent class detection
- ✅ Non-existent agent detection
- ✅ Valid playbook structures (simple, linear, diamond)
- ✅ Invalid playbook structures (empty, malformed, missing fields)
- ✅ Circular dependency detection
- ✅ Edge validation (malformed, missing fields, invalid references)
- ✅ Domain-level validation (all three playbooks)
- ✅ Helper functions

All tests pass successfully.

## Dependencies

The module depends on:
- `dag_validator.py` from `agent-api` for topological sort functionality
- Python 3.11+
- pytest (for testing)

## Integration

This module will be used by the Domain Handler Lambda to validate playbooks when:
- Creating a new domain (POST /api/v1/domains)
- Updating a domain (PUT /api/v1/domains/{domain_id})

The validation ensures that only valid, executable playbooks are stored in the system.

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:
- **Requirement 2.1**: Domain configuration with three playbooks
- **Requirement 9.1**: DAG validation for agent dependencies
- **Requirement 9.4**: Playbook validation before saving

## Next Steps

1. Create Domain Handler Lambda (task 9)
2. Add Domain API routes to API Gateway (task 10)
3. Write integration tests for Domain Handler (task 11)
