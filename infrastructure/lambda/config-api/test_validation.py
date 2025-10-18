"""
Simple validation tests for configuration managers
Run with: python test_validation.py
"""

def test_circular_dependency_detection():
    """Test circular dependency detection"""
    from dependency_graph_manager import DependencyGraphManager
    
    # Create mock manager (bypass __init__)
    manager = object.__new__(DependencyGraphManager)
    
    # Test case 1: Simple cycle A -> B -> A
    edges1 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'B', 'to': 'A'}
    ]
    assert manager._has_circular_dependency(edges1) == True, "Should detect simple cycle"
    
    # Test case 2: No cycle A -> B -> C
    edges2 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'B', 'to': 'C'}
    ]
    assert manager._has_circular_dependency(edges2) == False, "Should not detect cycle in linear graph"
    
    # Test case 3: Complex cycle A -> B -> C -> A
    edges3 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'B', 'to': 'C'},
        {'from': 'C', 'to': 'A'}
    ]
    assert manager._has_circular_dependency(edges3) == True, "Should detect complex cycle"
    
    # Test case 4: No cycle with branching
    edges4 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'A', 'to': 'C'},
        {'from': 'B', 'to': 'D'}
    ]
    assert manager._has_circular_dependency(edges4) == False, "Should not detect cycle in branching graph"
    
    print("✓ Circular dependency detection tests passed")


def test_single_level_dependency_validation():
    """Test single-level dependency validation"""
    from dependency_graph_manager import DependencyGraphManager
    
    # Create mock manager (bypass __init__)
    manager = object.__new__(DependencyGraphManager)
    
    # Test case 1: Valid single-level (each node has max 1 parent)
    edges1 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'A', 'to': 'C'}
    ]
    assert manager._validate_single_level_dependencies(edges1) == True, "Should allow single-level dependencies"
    
    # Test case 2: Invalid multi-level (B has 2 parents)
    edges2 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'C', 'to': 'B'}
    ]
    assert manager._validate_single_level_dependencies(edges2) == False, "Should reject multi-level dependencies"
    
    # Test case 3: Valid chain A -> B -> C (each has 1 parent)
    edges3 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'B', 'to': 'C'}
    ]
    assert manager._validate_single_level_dependencies(edges3) == True, "Should allow chain with single parents"
    
    print("✓ Single-level dependency validation tests passed")


def test_topological_sort():
    """Test execution level generation via topological sort"""
    from dependency_graph_manager import DependencyGraphManager
    
    # Create mock manager (bypass __init__)
    manager = object.__new__(DependencyGraphManager)
    
    # Test case 1: Linear dependency A -> B -> C
    edges1 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'B', 'to': 'C'}
    ]
    levels1 = manager._generate_execution_levels(edges1)
    assert levels1 == [['A'], ['B'], ['C']], f"Expected [['A'], ['B'], ['C']], got {levels1}"
    
    # Test case 2: Parallel execution (no dependencies)
    edges2 = []
    levels2 = manager._generate_execution_levels(edges2)
    assert levels2 == [], "Expected empty levels for no edges"
    
    # Test case 3: Branching A -> B, A -> C
    edges3 = [
        {'from': 'A', 'to': 'B'},
        {'from': 'A', 'to': 'C'}
    ]
    levels3 = manager._generate_execution_levels(edges3)
    assert levels3[0] == ['A'], "A should be in first level"
    assert set(levels3[1]) == {'B', 'C'}, "B and C should be in second level (parallel)"
    
    print("✓ Topological sort tests passed")


def test_agent_config_validation():
    """Test agent configuration validation"""
    from agent_config_manager import AgentConfigManager
    
    # Create mock manager (bypass __init__)
    manager = object.__new__(AgentConfigManager)
    
    # Test case 1: Valid config
    valid_config = {
        'agent_name': 'Test Agent',
        'agent_type': 'ingestion',
        'system_prompt': 'This is a test prompt with enough characters',
        'output_schema': {
            'key1': 'string',
            'key2': 'number',
            'key3': 'array'
        }
    }
    try:
        manager._validate_agent_config(valid_config)
        print("✓ Valid agent config accepted")
    except ValueError as e:
        print(f"✗ Valid config rejected: {e}")
    
    # Test case 2: Too many keys in output_schema
    invalid_config = {
        'agent_name': 'Test Agent',
        'agent_type': 'ingestion',
        'system_prompt': 'This is a test prompt',
        'output_schema': {
            'key1': 'string',
            'key2': 'number',
            'key3': 'array',
            'key4': 'boolean',
            'key5': 'object',
            'key6': 'string'  # 6th key - should fail
        }
    }
    try:
        manager._validate_agent_config(invalid_config)
        print("✗ Invalid config (too many keys) accepted")
    except ValueError as e:
        if "cannot have more than 5 keys" in str(e):
            print("✓ Invalid config (too many keys) rejected correctly")
        else:
            print(f"✗ Wrong error message: {e}")
    
    # Test case 3: Invalid agent_type
    invalid_type_config = {
        'agent_name': 'Test Agent',
        'agent_type': 'invalid_type',
        'system_prompt': 'This is a test prompt',
        'output_schema': {'key1': 'string'}
    }
    try:
        manager._validate_agent_config(invalid_type_config)
        print("✗ Invalid agent_type accepted")
    except ValueError as e:
        if "Invalid agent_type" in str(e):
            print("✓ Invalid agent_type rejected correctly")
        else:
            print(f"✗ Wrong error message: {e}")


if __name__ == '__main__':
    print("Running configuration validation tests...\n")
    
    test_circular_dependency_detection()
    test_single_level_dependency_validation()
    test_topological_sort()
    test_agent_config_validation()
    
    print("\n✓ All validation tests passed!")
