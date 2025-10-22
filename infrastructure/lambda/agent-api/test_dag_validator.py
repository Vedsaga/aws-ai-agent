"""
Unit Tests for DAG Validation Module
Tests circular dependency detection and graph operations
"""

import pytest
from dag_validator import (
    validate_dag,
    build_dependency_graph,
    topological_sort,
    validate_playbook_dag,
    get_agent_dependencies,
    find_all_dependencies
)


class TestValidateDAG:
    """Test cases for validate_dag function"""
    
    def test_linear_dependency_chain(self):
        """Test linear dependency chain: A -> B -> C"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-B']}
        }
        
        # Adding C with dependency on B should be valid
        is_valid, error = validate_dag('agent-C', ['agent-B'], agents)
        assert is_valid is True
        assert error is None
    
    def test_parallel_dependencies(self):
        """Test parallel dependencies: A, B -> C"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': []},
            'agent-C': {'agent_dependencies': ['agent-A', 'agent-B']}
        }
        
        # C depends on both A and B (parallel)
        is_valid, error = validate_dag('agent-C', ['agent-A', 'agent-B'], agents)
        assert is_valid is True
        assert error is None
    
    def test_diamond_dependency_structure(self):
        """Test diamond dependency: A -> B, A -> C, B -> D, C -> D"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-A']},
            'agent-D': {'agent_dependencies': ['agent-B', 'agent-C']}
        }
        
        # D depends on both B and C (diamond pattern)
        is_valid, error = validate_dag('agent-D', ['agent-B', 'agent-C'], agents)
        assert is_valid is True
        assert error is None
    
    def test_simple_circular_dependency(self):
        """Test simple circular dependency: A -> B -> A"""
        agents = {
            'agent-A': {'agent_dependencies': ['agent-B']},
            'agent-B': {'agent_dependencies': []}
        }
        
        # B trying to depend on A creates cycle
        is_valid, error = validate_dag('agent-B', ['agent-A'], agents)
        assert is_valid is False
        assert error is not None
        assert 'Circular dependency detected' in error
        assert 'agent-B' in error
        assert 'agent-A' in error
    
    def test_three_node_circular_dependency(self):
        """Test three-node circular dependency: A -> B -> C -> A"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-B']}
        }
        
        # A trying to depend on C creates cycle
        is_valid, error = validate_dag('agent-A', ['agent-C'], agents)
        assert is_valid is False
        assert error is not None
        assert 'Circular dependency detected' in error
    
    def test_self_dependency(self):
        """Test self-dependency: A -> A"""
        agents = {
            'agent-A': {'agent_dependencies': []}
        }
        
        # Agent depending on itself
        is_valid, error = validate_dag('agent-A', ['agent-A'], agents)
        assert is_valid is False
        assert error is not None
        assert 'Circular dependency detected' in error
    
    def test_complex_circular_dependency(self):
        """Test complex circular dependency in larger graph"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-B']},
            'agent-D': {'agent_dependencies': ['agent-C']},
            'agent-E': {'agent_dependencies': ['agent-D']}
        }
        
        # B trying to depend on E creates long cycle
        is_valid, error = validate_dag('agent-B', ['agent-A', 'agent-E'], agents)
        assert is_valid is False
        assert error is not None
        assert 'Circular dependency detected' in error
    
    def test_non_existent_dependency(self):
        """Test dependency on non-existent agent"""
        agents = {
            'agent-A': {'agent_dependencies': []}
        }
        
        # Depending on non-existent agent
        is_valid, error = validate_dag('agent-A', ['agent-NONEXISTENT'], agents)
        assert is_valid is False
        assert error is not None
        assert 'not found' in error
    
    def test_empty_dependencies(self):
        """Test agent with no dependencies"""
        agents = {
            'agent-A': {'agent_dependencies': []}
        }
        
        # No dependencies is always valid
        is_valid, error = validate_dag('agent-A', [], agents)
        assert is_valid is True
        assert error is None
    
    def test_new_agent_with_dependencies(self):
        """Test adding new agent with dependencies"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']}
        }
        
        # New agent C depending on B
        is_valid, error = validate_dag('agent-C', ['agent-B'], agents)
        assert is_valid is True
        assert error is None


class TestBuildDependencyGraph:
    """Test cases for build_dependency_graph function"""
    
    def test_single_node_graph(self):
        """Test graph with single node"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A',
                'agent_class': 'ingestion',
                'agent_dependencies': []
            }
        }
        
        graph = build_dependency_graph('agent-A', agents)
        
        assert len(graph['nodes']) == 1
        assert len(graph['edges']) == 0
        assert graph['nodes'][0]['id'] == 'agent-A'
        assert graph['nodes'][0]['label'] == 'Agent A'
        assert graph['nodes'][0]['class'] == 'ingestion'
    
    def test_linear_chain_graph(self):
        """Test linear dependency chain graph"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A',
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-B': {
                'agent_name': 'Agent B',
                'agent_class': 'query',
                'agent_dependencies': ['agent-A']
            },
            'agent-C': {
                'agent_name': 'Agent C',
                'agent_class': 'management',
                'agent_dependencies': ['agent-B']
            }
        }
        
        graph = build_dependency_graph('agent-C', agents)
        
        assert len(graph['nodes']) == 3
        assert len(graph['edges']) == 2
        
        # Check edges
        edge_pairs = [(e['from'], e['to']) for e in graph['edges']]
        assert ('agent-A', 'agent-B') in edge_pairs
        assert ('agent-B', 'agent-C') in edge_pairs
    
    def test_diamond_structure_graph(self):
        """Test diamond dependency structure"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A',
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-B': {
                'agent_name': 'Agent B',
                'agent_class': 'query',
                'agent_dependencies': ['agent-A']
            },
            'agent-C': {
                'agent_name': 'Agent C',
                'agent_class': 'query',
                'agent_dependencies': ['agent-A']
            },
            'agent-D': {
                'agent_name': 'Agent D',
                'agent_class': 'management',
                'agent_dependencies': ['agent-B', 'agent-C']
            }
        }
        
        graph = build_dependency_graph('agent-D', agents)
        
        assert len(graph['nodes']) == 4
        assert len(graph['edges']) == 4
        
        # Check all edges exist
        edge_pairs = [(e['from'], e['to']) for e in graph['edges']]
        assert ('agent-A', 'agent-B') in edge_pairs
        assert ('agent-A', 'agent-C') in edge_pairs
        assert ('agent-B', 'agent-D') in edge_pairs
        assert ('agent-C', 'agent-D') in edge_pairs
    
    def test_parallel_dependencies_graph(self):
        """Test parallel dependencies"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A',
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-B': {
                'agent_name': 'Agent B',
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-C': {
                'agent_name': 'Agent C',
                'agent_class': 'query',
                'agent_dependencies': ['agent-A', 'agent-B']
            }
        }
        
        graph = build_dependency_graph('agent-C', agents)
        
        assert len(graph['nodes']) == 3
        assert len(graph['edges']) == 2
        
        edge_pairs = [(e['from'], e['to']) for e in graph['edges']]
        assert ('agent-A', 'agent-C') in edge_pairs
        assert ('agent-B', 'agent-C') in edge_pairs
    
    def test_missing_agent_in_graph(self):
        """Test handling of missing agent reference"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A',
                'agent_class': 'ingestion',
                'agent_dependencies': ['agent-MISSING']
            }
        }
        
        # Should not crash, just skip missing agent
        graph = build_dependency_graph('agent-A', agents)
        
        assert len(graph['nodes']) == 1
        assert len(graph['edges']) == 1  # Edge is created but target node missing


class TestTopologicalSort:
    """Test cases for topological_sort function"""
    
    def test_linear_chain_sort(self):
        """Test topological sort of linear chain"""
        nodes = ['A', 'B', 'C']
        edges = [
            {'from': 'A', 'to': 'B'},
            {'from': 'B', 'to': 'C'}
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is True
        assert error is None
        assert order == ['A', 'B', 'C']
    
    def test_parallel_nodes_sort(self):
        """Test topological sort with parallel nodes"""
        nodes = ['A', 'B', 'C']
        edges = [
            {'from': 'A', 'to': 'C'},
            {'from': 'B', 'to': 'C'}
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is True
        assert error is None
        # A and B can be in any order, but both before C
        assert order.index('A') < order.index('C')
        assert order.index('B') < order.index('C')
    
    def test_diamond_structure_sort(self):
        """Test topological sort of diamond structure"""
        nodes = ['A', 'B', 'C', 'D']
        edges = [
            {'from': 'A', 'to': 'B'},
            {'from': 'A', 'to': 'C'},
            {'from': 'B', 'to': 'D'},
            {'from': 'C', 'to': 'D'}
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is True
        assert error is None
        # A must be first, D must be last
        assert order[0] == 'A'
        assert order[3] == 'D'
        # B and C in middle
        assert 'B' in order[1:3]
        assert 'C' in order[1:3]
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependency"""
        nodes = ['A', 'B', 'C']
        edges = [
            {'from': 'A', 'to': 'B'},
            {'from': 'B', 'to': 'C'},
            {'from': 'C', 'to': 'A'}  # Creates cycle
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is False
        assert error is not None
        assert 'Cycle detected' in error
    
    def test_single_node_sort(self):
        """Test topological sort with single node"""
        nodes = ['A']
        edges = []
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is True
        assert error is None
        assert order == ['A']
    
    def test_disconnected_nodes_sort(self):
        """Test topological sort with disconnected nodes"""
        nodes = ['A', 'B', 'C', 'D']
        edges = [
            {'from': 'A', 'to': 'B'},
            {'from': 'C', 'to': 'D'}
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is True
        assert error is None
        assert len(order) == 4
        # A before B, C before D
        assert order.index('A') < order.index('B')
        assert order.index('C') < order.index('D')
    
    def test_invalid_edge_reference(self):
        """Test handling of edge referencing non-existent node"""
        nodes = ['A', 'B']
        edges = [
            {'from': 'A', 'to': 'C'}  # C doesn't exist
        ]
        
        is_valid, order, error = topological_sort(nodes, edges)
        
        assert is_valid is False
        assert error is not None
        assert 'non-existent node' in error


class TestValidatePlaybookDAG:
    """Test cases for validate_playbook_dag function"""
    
    def test_valid_ingestion_playbook(self):
        """Test valid ingestion playbook"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
            }
        }
        agents = {
            'agent-A': {
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-B': {
                'agent_class': 'ingestion',
                'agent_dependencies': ['agent-A']
            }
        }
        
        is_valid, error = validate_playbook_dag(playbook, 'ingestion', agents)
        
        assert is_valid is True
        assert error is None
    
    def test_wrong_agent_class_in_playbook(self):
        """Test playbook with wrong agent class"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
            }
        }
        agents = {
            'agent-A': {
                'agent_class': 'ingestion',
                'agent_dependencies': []
            },
            'agent-B': {
                'agent_class': 'query',  # Wrong class
                'agent_dependencies': ['agent-A']
            }
        }
        
        is_valid, error = validate_playbook_dag(playbook, 'ingestion', agents)
        
        assert is_valid is False
        assert error is not None
        assert 'agent-B' in error
        assert 'query' in error
        assert 'ingestion' in error
    
    def test_circular_dependency_in_playbook(self):
        """Test playbook with circular dependency"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [
                    {'from': 'agent-A', 'to': 'agent-B'},
                    {'from': 'agent-B', 'to': 'agent-A'}
                ]
            }
        }
        agents = {
            'agent-A': {
                'agent_class': 'query',
                'agent_dependencies': ['agent-B']
            },
            'agent-B': {
                'agent_class': 'query',
                'agent_dependencies': ['agent-A']
            }
        }
        
        is_valid, error = validate_playbook_dag(playbook, 'query', agents)
        
        assert is_valid is False
        assert error is not None
        assert 'circular' in error.lower()
    
    def test_missing_agent_in_playbook(self):
        """Test playbook referencing non-existent agent"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-MISSING'],
                'edges': [{'from': 'agent-A', 'to': 'agent-MISSING'}]
            }
        }
        agents = {
            'agent-A': {
                'agent_class': 'management',
                'agent_dependencies': []
            }
        }
        
        is_valid, error = validate_playbook_dag(playbook, 'management', agents)
        
        assert is_valid is False
        assert error is not None
        assert 'not found' in error
    
    def test_missing_execution_graph(self):
        """Test playbook without agent_execution_graph"""
        playbook = {}
        agents = {}
        
        is_valid, error = validate_playbook_dag(playbook, 'query', agents)
        
        assert is_valid is False
        assert error is not None
        assert 'agent_execution_graph' in error
    
    def test_malformed_execution_graph(self):
        """Test playbook with malformed execution graph"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A']
                # Missing 'edges'
            }
        }
        agents = {
            'agent-A': {'agent_class': 'query', 'agent_dependencies': []}
        }
        
        is_valid, error = validate_playbook_dag(playbook, 'query', agents)
        
        assert is_valid is False
        assert error is not None
        assert 'edges' in error


class TestHelperFunctions:
    """Test cases for helper functions"""
    
    def test_get_agent_dependencies(self):
        """Test getting agent dependencies"""
        agents = {
            'agent-A': {'agent_dependencies': ['agent-B', 'agent-C']},
            'agent-B': {'agent_dependencies': []},
            'agent-C': {'agent_dependencies': ['agent-B']}
        }
        
        deps = get_agent_dependencies('agent-A', agents)
        assert deps == ['agent-B', 'agent-C']
        
        deps = get_agent_dependencies('agent-B', agents)
        assert deps == []
        
        deps = get_agent_dependencies('agent-MISSING', agents)
        assert deps == []
    
    def test_find_all_dependencies(self):
        """Test finding all transitive dependencies"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-B']},
            'agent-D': {'agent_dependencies': ['agent-C']}
        }
        
        # D depends on C, which depends on B, which depends on A
        all_deps = find_all_dependencies('agent-D', agents)
        assert all_deps == {'agent-A', 'agent-B', 'agent-C'}
        
        # C depends on B and A
        all_deps = find_all_dependencies('agent-C', agents)
        assert all_deps == {'agent-A', 'agent-B'}
        
        # A has no dependencies
        all_deps = find_all_dependencies('agent-A', agents)
        assert all_deps == set()
    
    def test_find_all_dependencies_diamond(self):
        """Test finding dependencies in diamond structure"""
        agents = {
            'agent-A': {'agent_dependencies': []},
            'agent-B': {'agent_dependencies': ['agent-A']},
            'agent-C': {'agent_dependencies': ['agent-A']},
            'agent-D': {'agent_dependencies': ['agent-B', 'agent-C']}
        }
        
        # D depends on B, C, and A (through both paths)
        all_deps = find_all_dependencies('agent-D', agents)
        assert all_deps == {'agent-A', 'agent-B', 'agent-C'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
