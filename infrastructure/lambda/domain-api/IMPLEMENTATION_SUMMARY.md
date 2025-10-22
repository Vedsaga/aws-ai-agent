# Playbook Validation Implementation Summary

## Task Completed: Task 8 - Implement playbook validation

### Overview

Successfully implemented comprehensive playbook validation functionality for the Domain Management API. This module validates that domain playbooks have valid agent execution graphs with no circular dependencies and that all agents belong to the correct class.

## Files Created

### 1. `playbook_validator.py` (Main Module)

**Core Functions Implemented:**

- **`validate_agent_class(agent_id, expected_class, all_agents)`**
  - Verifies an agent belongs to the expected class
  - Returns (is_valid, error_message) tuple
  - Handles non-existent agents and class mismatches

- **`validate_playbook(playbook, playbook_type, all_agents)`**
  - Main validation function for domain playbooks
  - Performs 4-stage validation:
    1. Structure validation (graph has nodes and edges)
    2. Agent existence validation
    3. Agent class validation
    4. DAG validation (no circular dependencies)
  - Returns detailed error messages for debugging

- **`validate_domain_playbooks(ingestion_playbook, query_playbook, management_playbook, all_agents)`**
  - Validates all three playbooks for a domain
  - Ensures each playbook type has correct agent classes
  - Returns specific error indicating which playbook failed

**Helper Functions:**

- `get_playbook_agent_count(playbook)` - Returns agent count
- `get_playbook_agents(playbook)` - Returns list of agent IDs

### 2. `test_playbook_validator.py` (Test Suite)

**Test Coverage: 32 tests, 100% passing**

Test classes:
- `TestValidateAgentClass` (6 tests)
  - Valid agent classes (ingestion, query, management)
  - Wrong agent class detection
  - Non-existent agent handling
  - Missing agent_class field

- `TestValidatePlaybook` (16 tests)
  - Valid structures (simple, linear, diamond)
  - Invalid structures (empty, malformed, missing fields)
  - Circular dependency detection
  - Edge validation (malformed, missing fields, invalid references)
  - Agent class mismatches

- `TestValidateDomainPlaybooks` (4 tests)
  - All three valid playbooks
  - Invalid ingestion playbook
  - Invalid query playbook
  - Invalid management playbook

- `TestHelperFunctions` (6 tests)
  - Agent count retrieval
  - Agent list retrieval
  - Handling of invalid/empty playbooks

### 3. `README.md` (Documentation)

Comprehensive documentation including:
- Function signatures and parameters
- Usage examples
- Validation rules
- Error messages
- Testing instructions
- Integration guidelines

### 4. `requirements.txt`

Dependencies:
- pytest>=7.4.0

## Validation Rules Implemented

### Playbook Structure
✅ Must contain `agent_execution_graph` field
✅ Must have `nodes` array (list of agent IDs)
✅ Must have `edges` array (list of {from, to} objects)
✅ Must contain at least one agent

### Agent Class Validation
✅ All agents must exist in the system
✅ All agents must have correct `agent_class`:
  - Ingestion playbook → 'ingestion' agents only
  - Query playbook → 'query' agents only
  - Management playbook → 'management' agents only

### DAG Validation
✅ Graph must be a Directed Acyclic Graph (DAG)
✅ No circular dependencies allowed
✅ All edges must reference existing nodes
✅ Uses topological sort from `dag_validator.py`

## Test Results

```
============================= test session starts ==============================
platform linux -- Python 3.13.7, pytest-7.4.3, pluggy-1.6.0
collected 32 items

test_playbook_validator.py::TestValidateAgentClass::test_valid_ingestion_agent PASSED
test_playbook_validator.py::TestValidateAgentClass::test_valid_query_agent PASSED
test_playbook_validator.py::TestValidateAgentClass::test_valid_management_agent PASSED
test_playbook_validator.py::TestValidateAgentClass::test_wrong_agent_class PASSED
test_playbook_validator.py::TestValidateAgentClass::test_non_existent_agent PASSED
test_playbook_validator.py::TestValidateAgentClass::test_agent_without_class PASSED
test_playbook_validator.py::TestValidatePlaybook::test_valid_simple_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_valid_linear_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_valid_diamond_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_empty_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_missing_execution_graph PASSED
test_playbook_validator.py::TestValidatePlaybook::test_malformed_execution_graph PASSED
test_playbook_validator.py::TestValidatePlaybook::test_missing_nodes PASSED
test_playbook_validator.py::TestValidatePlaybook::test_missing_edges PASSED
test_playbook_validator.py::TestValidatePlaybook::test_empty_nodes_list PASSED
test_playbook_validator.py::TestValidatePlaybook::test_non_existent_agent_in_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_wrong_agent_class_in_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_circular_dependency_in_playbook PASSED
test_playbook_validator.py::TestValidatePlaybook::test_malformed_edge PASSED
test_playbook_validator.py::TestValidatePlaybook::test_edge_missing_from_field PASSED
test_playbook_validator.py::TestValidatePlaybook::test_edge_missing_to_field PASSED
test_playbook_validator.py::TestValidatePlaybook::test_edge_references_non_existent_node PASSED
test_playbook_validator.py::TestValidateDomainPlaybooks::test_valid_all_playbooks PASSED
test_playbook_validator.py::TestValidateDomainPlaybooks::test_invalid_ingestion_playbook PASSED
test_playbook_validator.py::TestValidateDomainPlaybooks::test_invalid_query_playbook PASSED
test_playbook_validator.py::TestValidateDomainPlaybooks::test_invalid_management_playbook PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agent_count PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agent_count_empty PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agent_count_invalid PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agents PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agents_empty PASSED
test_playbook_validator.py::TestHelperFunctions::test_get_playbook_agents_invalid PASSED

============================== 32 passed in 0.06s ==============================
```

## Requirements Satisfied

✅ **Requirement 2.1**: Domain configuration API with three playbooks
✅ **Requirement 9.1**: DAG validation for agent dependencies
✅ **Requirement 9.4**: Playbook validation before saving

## Integration Points

This module will be used by:
1. **Domain Handler Lambda** (Task 9) - For validating playbooks during domain creation/update
2. **API Gateway** (Task 10) - POST /api/v1/domains and PUT /api/v1/domains/{domain_id}

## Error Handling

The validator provides clear, actionable error messages:
- `"Agent not found: agent-X"` - Referenced agent doesn't exist
- `"Agent agent-X (Agent Name) is class 'query', expected 'ingestion'"` - Wrong agent class
- `"Playbook contains circular dependencies: Cycle detected in graph. Nodes involved: ..."` - Cycle detected
- `"Edge references non-existent node: agent-X"` - Invalid edge
- `"Playbook must contain at least one agent"` - Empty playbook
- `"Ingestion playbook validation failed: ..."` - Specific playbook error

## Code Quality

✅ Comprehensive docstrings with examples
✅ Type hints for all function parameters
✅ Detailed error messages for debugging
✅ 100% test coverage of core functionality
✅ Follows Python best practices
✅ Reuses existing DAG validation logic from agent-api

## Next Steps

The playbook validation module is complete and ready for integration. Next tasks:

1. **Task 9**: Create Domain Handler Lambda using this validation module
2. **Task 10**: Add Domain API routes to API Gateway
3. **Task 11**: Write integration tests for Domain Handler

## Dependencies

- `dag_validator.py` from `agent-api` - For topological sort
- Python 3.11+
- pytest 7.4.0+ (for testing)

## File Structure

```
infrastructure/lambda/domain-api/
├── playbook_validator.py          # Main validation module
├── test_playbook_validator.py     # Comprehensive test suite (32 tests)
├── requirements.txt                # Python dependencies
├── README.md                       # Module documentation
└── IMPLEMENTATION_SUMMARY.md       # This file
```

## Conclusion

Task 8 is complete. The playbook validation module provides robust validation for domain playbooks with comprehensive test coverage and clear error messages. It's ready to be integrated into the Domain Handler Lambda.
