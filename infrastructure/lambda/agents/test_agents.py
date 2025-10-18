#!/usr/bin/env python3
"""
Simple test script for agent framework

Tests basic functionality of each agent type without requiring AWS credentials.
"""

import json
import sys
from agent_utils import create_test_event, MockLambdaContext, format_agent_output_for_display


def test_base_agent_structure():
    """Test that base agent can be imported and has required methods"""
    print("Testing base agent structure...")
    
    try:
        from base_agent import BaseAgent, AgentError, ToolInvocationError, OutputValidationError
        
        # Check required methods exist
        required_methods = [
            'execute', 'invoke_bedrock', 'invoke_tool', 
            'validate_output', 'format_output', 'handle_execution'
        ]
        
        for method in required_methods:
            assert hasattr(BaseAgent, method), f"Missing method: {method}"
        
        print("✓ Base agent structure is valid")
        return True
    except Exception as e:
        print(f"✗ Base agent structure test failed: {str(e)}")
        return False


def test_agent_imports():
    """Test that all agent modules can be imported"""
    print("\nTesting agent imports...")
    
    agents = [
        ('geo_agent', 'GeoAgent'),
        ('temporal_agent', 'TemporalAgent'),
        ('entity_agent', 'EntityAgent'),
        ('query_agents', 'WhenAgent'),
        ('custom_agent', 'CustomAgent')
    ]
    
    all_passed = True
    for module_name, class_name in agents:
        try:
            module = __import__(module_name)
            assert hasattr(module, class_name), f"Missing class: {class_name}"
            print(f"✓ {class_name} imported successfully")
        except Exception as e:
            print(f"✗ Failed to import {class_name}: {str(e)}")
            all_passed = False
    
    return all_passed


def test_output_schema_validation():
    """Test output schema validation (max 5 keys)"""
    print("\nTesting output schema validation...")
    
    try:
        from base_agent import BaseAgent, OutputValidationError
        
        # Create a test agent with valid schema (5 keys)
        valid_config = {
            'agent_name': 'TestAgent',
            'system_prompt': 'Test prompt',
            'tools': ['bedrock'],
            'output_schema': {
                'key1': {'type': 'string', 'required': True},
                'key2': {'type': 'string', 'required': True},
                'key3': {'type': 'string', 'required': True},
                'key4': {'type': 'string', 'required': True},
                'key5': {'type': 'string', 'required': True}
            }
        }
        
        # This should work (5 keys)
        class TestAgent(BaseAgent):
            def execute(self, raw_text, parent_output=None):
                return {'key1': 'val1', 'key2': 'val2', 'key3': 'val3', 'key4': 'val4', 'key5': 'val5'}
        
        agent = TestAgent(valid_config)
        print("✓ Valid schema (5 keys) accepted")
        
        # Test invalid schema (6 keys)
        invalid_config = valid_config.copy()
        invalid_config['output_schema']['key6'] = {'type': 'string', 'required': True}
        
        try:
            agent = TestAgent(invalid_config)
            print("✗ Invalid schema (6 keys) should have been rejected")
            return False
        except OutputValidationError:
            print("✓ Invalid schema (6 keys) correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema validation test failed: {str(e)}")
        return False


def test_seed_data_loading():
    """Test seed data can be loaded"""
    print("\nTesting seed data loading...")
    
    try:
        from agent_utils import load_seed_data, get_agent_config
        
        seed_data = load_seed_data()
        
        # Check for expected keys
        assert 'custom_agents' in seed_data, "Missing custom_agents in seed data"
        assert 'ingestion_playbooks' in seed_data, "Missing ingestion_playbooks in seed data"
        assert 'dependency_graphs' in seed_data, "Missing dependency_graphs in seed data"
        
        # Check for SeverityClassifier
        severity_config = get_agent_config('severity-classifier', seed_data)
        assert severity_config is not None, "SeverityClassifier not found in seed data"
        assert severity_config['agent_name'] == 'SeverityClassifier'
        assert severity_config['dependency_parent'] == 'EntityAgent'
        assert len(severity_config['output_schema']) == 5, "SeverityClassifier should have 5 output keys"
        
        print("✓ Seed data loaded successfully")
        print(f"  - Found {len(seed_data['custom_agents'])} custom agents")
        print(f"  - Found {len(seed_data['ingestion_playbooks'])} playbooks")
        print(f"  - SeverityClassifier configured correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Seed data loading failed: {str(e)}")
        return False


def test_dependency_validation():
    """Test dependency graph validation"""
    print("\nTesting dependency graph validation...")
    
    try:
        from agent_utils import validate_dependency_graph, compute_execution_levels
        
        # Test valid single-level dependency
        valid_edges = [
            {'from': 'EntityAgent', 'to': 'SeverityClassifier'}
        ]
        is_valid, error = validate_dependency_graph(valid_edges)
        assert is_valid, f"Valid dependency rejected: {error}"
        print("✓ Valid single-level dependency accepted")
        
        # Test invalid multi-level dependency
        invalid_edges = [
            {'from': 'EntityAgent', 'to': 'SeverityClassifier'},
            {'from': 'GeoAgent', 'to': 'SeverityClassifier'}  # Multiple parents
        ]
        is_valid, error = validate_dependency_graph(invalid_edges)
        assert not is_valid, "Multi-level dependency should be rejected"
        print("✓ Multi-level dependency correctly rejected")
        
        # Test circular dependency
        circular_edges = [
            {'from': 'Agent1', 'to': 'Agent2'},
            {'from': 'Agent2', 'to': 'Agent1'}
        ]
        is_valid, error = validate_dependency_graph(circular_edges)
        assert not is_valid, "Circular dependency should be rejected"
        print("✓ Circular dependency correctly rejected")
        
        # Test execution level computation
        all_agents = ['GeoAgent', 'TemporalAgent', 'EntityAgent', 'SeverityClassifier']
        levels = compute_execution_levels(valid_edges, all_agents)
        assert len(levels) == 2, "Should have 2 execution levels"
        assert 'EntityAgent' in levels[0]['agents'], "EntityAgent should be in level 0"
        assert 'SeverityClassifier' in levels[1]['agents'], "SeverityClassifier should be in level 1"
        print("✓ Execution levels computed correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Dependency validation test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent Framework Test Suite")
    print("=" * 60)
    
    tests = [
        test_base_agent_structure,
        test_agent_imports,
        test_output_schema_validation,
        test_seed_data_loading,
        test_dependency_validation
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
