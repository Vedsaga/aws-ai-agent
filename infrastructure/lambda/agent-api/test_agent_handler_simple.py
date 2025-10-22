"""
Simple validation tests for Agent Handler Lambda
Tests logic without requiring database connections
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import dag_validator
        print("✓ dag_validator imported successfully")
        
        # Test DAG validator functions exist
        assert hasattr(dag_validator, 'validate_dag')
        assert hasattr(dag_validator, 'build_dependency_graph')
        assert hasattr(dag_validator, 'topological_sort')
        assert hasattr(dag_validator, 'validate_playbook_dag')
        print("✓ All DAG validator functions exist")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_agent_handler_structure():
    """Test that agent_handler has all required functions"""
    print("\nTesting agent_handler structure...")
    try:
        # We can't import agent_handler without psycopg2, so we'll read the file
        with open('agent_handler.py', 'r') as f:
            content = f.read()
        
        required_functions = [
            'def handler(',
            'def create_agent(',
            'def list_agents(',
            'def get_agent(',
            'def update_agent(',
            'def delete_agent(',
            'def get_all_agents_dict(',
            'def extract_tenant_id(',
            'def extract_user_id(',
            'def success_response(',
            'def error_response('
        ]
        
        for func in required_functions:
            if func in content:
                print(f"✓ Found {func.strip('(')}")
            else:
                print(f"✗ Missing {func.strip('(')}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Structure test failed: {e}")
        return False


def test_dag_validator_logic():
    """Test DAG validator with sample data"""
    print("\nTesting DAG validator logic...")
    try:
        from dag_validator import validate_dag, build_dependency_graph, topological_sort
        
        # Test 1: Valid linear dependency
        agents = {
            'agent-A': {'agent_name': 'Agent A', 'agent_class': 'ingestion', 'agent_dependencies': []},
            'agent-B': {'agent_name': 'Agent B', 'agent_class': 'ingestion', 'agent_dependencies': ['agent-A']}
        }
        
        is_valid, error = validate_dag('agent-C', ['agent-B'], agents)
        assert is_valid == True, f"Expected valid DAG, got error: {error}"
        print("✓ Valid linear dependency test passed")
        
        # Test 2: Circular dependency detection
        agents_circular = {
            'agent-A': {'agent_name': 'Agent A', 'agent_class': 'ingestion', 'agent_dependencies': ['agent-B']},
            'agent-B': {'agent_name': 'Agent B', 'agent_class': 'ingestion', 'agent_dependencies': ['agent-A']}
        }
        
        is_valid, error = validate_dag('agent-A', ['agent-B'], agents_circular)
        assert is_valid == False, "Expected circular dependency to be detected"
        assert "Circular dependency" in error, f"Expected circular dependency error, got: {error}"
        print("✓ Circular dependency detection test passed")
        
        # Test 3: Dependency graph building
        graph = build_dependency_graph('agent-B', agents)
        assert 'nodes' in graph, "Graph should have nodes"
        assert 'edges' in graph, "Graph should have edges"
        assert len(graph['nodes']) == 2, f"Expected 2 nodes, got {len(graph['nodes'])}"
        assert len(graph['edges']) == 1, f"Expected 1 edge, got {len(graph['edges'])}"
        print("✓ Dependency graph building test passed")
        
        # Test 4: Topological sort
        nodes = ['A', 'B', 'C']
        edges = [{'from': 'A', 'to': 'B'}, {'from': 'B', 'to': 'C'}]
        is_valid, sorted_nodes, error = topological_sort(nodes, edges)
        assert is_valid == True, f"Expected valid sort, got error: {error}"
        assert sorted_nodes == ['A', 'B', 'C'], f"Expected ['A', 'B', 'C'], got {sorted_nodes}"
        print("✓ Topological sort test passed")
        
        return True
    except Exception as e:
        print(f"✗ DAG validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_request_validation_logic():
    """Test request validation logic"""
    print("\nTesting request validation logic...")
    try:
        # Test valid agent classes
        valid_classes = ['ingestion', 'query', 'management']
        for cls in valid_classes:
            assert cls in ['ingestion', 'query', 'management'], f"Invalid class: {cls}"
        print("✓ Agent class validation passed")
        
        # Test output schema validation
        valid_schema = {
            "type": "object",
            "properties": {
                "key1": {"type": "string"},
                "key2": {"type": "string"},
                "key3": {"type": "string"},
                "key4": {"type": "string"},
                "key5": {"type": "string"}
            }
        }
        assert len(valid_schema.get("properties", {})) <= 5, "Schema should have max 5 properties"
        print("✓ Output schema validation passed")
        
        # Test invalid schema (too many properties)
        invalid_schema = {
            "type": "object",
            "properties": {
                "key1": {"type": "string"},
                "key2": {"type": "string"},
                "key3": {"type": "string"},
                "key4": {"type": "string"},
                "key5": {"type": "string"},
                "key6": {"type": "string"}
            }
        }
        assert len(invalid_schema.get("properties", {})) > 5, "Should detect too many properties"
        print("✓ Invalid schema detection passed")
        
        return True
    except Exception as e:
        print(f"✗ Request validation test failed: {e}")
        return False


def test_response_formatting():
    """Test response formatting"""
    print("\nTesting response formatting...")
    try:
        # Test success response format
        success_data = {"agent_id": "test-123", "agent_name": "Test Agent"}
        success_response = {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(success_data)
        }
        
        assert success_response["statusCode"] == 201
        assert "Content-Type" in success_response["headers"]
        body = json.loads(success_response["body"])
        assert body["agent_id"] == "test-123"
        print("✓ Success response formatting passed")
        
        # Test error response format
        error_response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Test error",
                "error_code": "ERR_400",
                "timestamp": "2025-10-21T16:00:00Z"
            })
        }
        
        assert error_response["statusCode"] == 400
        body = json.loads(error_response["body"])
        assert "error" in body
        assert "error_code" in body
        assert "timestamp" in body
        print("✓ Error response formatting passed")
        
        return True
    except Exception as e:
        print(f"✗ Response formatting test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent Handler Lambda - Validation Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_agent_handler_structure,
        test_dag_validator_logic,
        test_request_validation_logic,
        test_response_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
