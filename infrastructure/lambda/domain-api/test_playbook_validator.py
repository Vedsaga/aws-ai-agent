"""
Unit Tests for Playbook Validation Module
Tests playbook validation and agent class verification
"""

import pytest
from playbook_validator import (
    validate_agent_class,
    validate_playbook,
    validate_domain_playbooks,
    get_playbook_agent_count,
    get_playbook_agents
)


class TestValidateAgentClass:
    """Test cases for validate_agent_class function"""
    
    def test_valid_ingestion_agent(self):
        """Test agent with correct ingestion class"""
        agents = {
            'agent-A': {
                'agent_class': 'ingestion',
                'agent_name': 'Ingestion Agent'
            }
        }
        
        is_valid, error = validate_agent_class('agent-A', 'ingestion', agents)
        assert is_valid is True
        assert error is None
    
    def test_valid_query_agent(self):
        """Test agent with correct query class"""
        agents = {
            'agent-B': {
                'agent_class': 'query',
                'agent_name': 'Query Agent'
            }
        }
        
        is_valid, error = validate_agent_class('agent-B', 'query', agents)
        assert is_valid is True
        assert error is None
    
    def test_valid_management_agent(self):
        """Test agent with correct management class"""
        agents = {
            'agent-C': {
                'agent_class': 'management',
                'agent_name': 'Management Agent'
            }
        }
        
        is_valid, error = validate_agent_class('agent-C', 'management', agents)
        assert is_valid is True
        assert error is None
    
    def test_wrong_agent_class(self):
        """Test agent with wrong class"""
        agents = {
            'agent-A': {
                'agent_class': 'ingestion',
                'agent_name': 'Ingestion Agent'
            }
        }
        
        is_valid, error = validate_agent_class('agent-A', 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'agent-A' in error
        assert 'ingestion' in error
        assert 'query' in error
    
    def test_non_existent_agent(self):
        """Test validation of non-existent agent"""
        agents = {
            'agent-A': {'agent_class': 'ingestion'}
        }
        
        is_valid, error = validate_agent_class('agent-MISSING', 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'not found' in error
        assert 'agent-MISSING' in error
    
    def test_agent_without_class(self):
        """Test agent missing agent_class field"""
        agents = {
            'agent-A': {
                'agent_name': 'Agent A'
                # Missing agent_class
            }
        }
        
        is_valid, error = validate_agent_class('agent-A', 'ingestion', agents)
        assert is_valid is False
        assert error is not None


class TestValidatePlaybook:
    """Test cases for validate_playbook function"""
    
    def test_valid_simple_playbook(self):
        """Test valid playbook with single agent"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A'],
                'edges': []
            }
        }
        agents = {
            'agent-A': {
                'agent_class': 'ingestion',
                'agent_name': 'Agent A'
            }
        }
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is True
        assert error is None
    
    def test_valid_linear_playbook(self):
        """Test valid playbook with linear dependency chain"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B', 'agent-C'],
                'edges': [
                    {'from': 'agent-A', 'to': 'agent-B'},
                    {'from': 'agent-B', 'to': 'agent-C'}
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'query', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'},
            'agent-C': {'agent_class': 'query', 'agent_name': 'Agent C'}
        }
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is True
        assert error is None
    
    def test_valid_diamond_playbook(self):
        """Test valid playbook with diamond structure"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B', 'agent-C', 'agent-D'],
                'edges': [
                    {'from': 'agent-A', 'to': 'agent-B'},
                    {'from': 'agent-A', 'to': 'agent-C'},
                    {'from': 'agent-B', 'to': 'agent-D'},
                    {'from': 'agent-C', 'to': 'agent-D'}
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'management', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'management', 'agent_name': 'Agent B'},
            'agent-C': {'agent_class': 'management', 'agent_name': 'Agent C'},
            'agent-D': {'agent_class': 'management', 'agent_name': 'Agent D'}
        }
        
        is_valid, error = validate_playbook(playbook, 'management', agents)
        assert is_valid is True
        assert error is None
    
    def test_empty_playbook(self):
        """Test validation of empty playbook"""
        playbook = None
        agents = {}
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'empty' in error.lower()
    
    def test_missing_execution_graph(self):
        """Test playbook without agent_execution_graph"""
        playbook = {
            'some_other_field': 'value'
        }
        agents = {}
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'agent_execution_graph' in error
    
    def test_malformed_execution_graph(self):
        """Test playbook with malformed execution graph"""
        playbook = {
            'agent_execution_graph': 'not a dict'
        }
        agents = {}
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'dictionary' in error
    
    def test_missing_nodes(self):
        """Test playbook missing nodes field"""
        playbook = {
            'agent_execution_graph': {
                'edges': []
            }
        }
        agents = {}
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'nodes' in error
    
    def test_missing_edges(self):
        """Test playbook missing edges field"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A']
            }
        }
        agents = {'agent-A': {'agent_class': 'ingestion'}}
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'edges' in error
    
    def test_empty_nodes_list(self):
        """Test playbook with empty nodes list"""
        playbook = {
            'agent_execution_graph': {
                'nodes': [],
                'edges': []
            }
        }
        agents = {}
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'at least one agent' in error
    
    def test_non_existent_agent_in_playbook(self):
        """Test playbook referencing non-existent agent"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-MISSING'],
                'edges': []
            }
        }
        agents = {
            'agent-A': {'agent_class': 'management', 'agent_name': 'Agent A'}
        }
        
        is_valid, error = validate_playbook(playbook, 'management', agents)
        assert is_valid is False
        assert error is not None
        assert 'not found' in error
        assert 'agent-MISSING' in error
    
    def test_wrong_agent_class_in_playbook(self):
        """Test playbook with agent of wrong class"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [{'from': 'agent-A', 'to': 'agent-B'}]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'ingestion', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'}  # Wrong class
        }
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
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
            'agent-A': {'agent_class': 'query', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'}
        }
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'circular' in error.lower()
    
    def test_malformed_edge(self):
        """Test playbook with malformed edge"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [
                    'not a dict'
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'ingestion', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'ingestion', 'agent_name': 'Agent B'}
        }
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'dictionary' in error
    
    def test_edge_missing_from_field(self):
        """Test playbook with edge missing 'from' field"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [
                    {'to': 'agent-B'}  # Missing 'from'
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'management', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'management', 'agent_name': 'Agent B'}
        }
        
        is_valid, error = validate_playbook(playbook, 'management', agents)
        assert is_valid is False
        assert error is not None
        assert 'from' in error
    
    def test_edge_missing_to_field(self):
        """Test playbook with edge missing 'to' field"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [
                    {'from': 'agent-A'}  # Missing 'to'
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'query', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'query', 'agent_name': 'Agent B'}
        }
        
        is_valid, error = validate_playbook(playbook, 'query', agents)
        assert is_valid is False
        assert error is not None
        assert 'to' in error
    
    def test_edge_references_non_existent_node(self):
        """Test playbook with edge referencing non-existent node"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B'],
                'edges': [
                    {'from': 'agent-A', 'to': 'agent-C'}  # agent-C not in nodes
                ]
            }
        }
        agents = {
            'agent-A': {'agent_class': 'ingestion', 'agent_name': 'Agent A'},
            'agent-B': {'agent_class': 'ingestion', 'agent_name': 'Agent B'}
        }
        
        is_valid, error = validate_playbook(playbook, 'ingestion', agents)
        assert is_valid is False
        assert error is not None
        assert 'non-existent node' in error


class TestValidateDomainPlaybooks:
    """Test cases for validate_domain_playbooks function"""
    
    def test_valid_all_playbooks(self):
        """Test validation of all three valid playbooks"""
        ingestion_playbook = {
            'agent_execution_graph': {
                'nodes': ['ing-1', 'ing-2'],
                'edges': [{'from': 'ing-1', 'to': 'ing-2'}]
            }
        }
        query_playbook = {
            'agent_execution_graph': {
                'nodes': ['qry-1', 'qry-2'],
                'edges': [{'from': 'qry-1', 'to': 'qry-2'}]
            }
        }
        management_playbook = {
            'agent_execution_graph': {
                'nodes': ['mgmt-1'],
                'edges': []
            }
        }
        agents = {
            'ing-1': {'agent_class': 'ingestion', 'agent_name': 'Ingestion 1'},
            'ing-2': {'agent_class': 'ingestion', 'agent_name': 'Ingestion 2'},
            'qry-1': {'agent_class': 'query', 'agent_name': 'Query 1'},
            'qry-2': {'agent_class': 'query', 'agent_name': 'Query 2'},
            'mgmt-1': {'agent_class': 'management', 'agent_name': 'Management 1'}
        }
        
        is_valid, error = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            agents
        )
        assert is_valid is True
        assert error is None
    
    def test_invalid_ingestion_playbook(self):
        """Test validation fails on invalid ingestion playbook"""
        ingestion_playbook = {
            'agent_execution_graph': {
                'nodes': ['ing-1', 'qry-1'],  # qry-1 is wrong class
                'edges': []
            }
        }
        query_playbook = {
            'agent_execution_graph': {
                'nodes': ['qry-1'],
                'edges': []
            }
        }
        management_playbook = {
            'agent_execution_graph': {
                'nodes': ['mgmt-1'],
                'edges': []
            }
        }
        agents = {
            'ing-1': {'agent_class': 'ingestion', 'agent_name': 'Ingestion 1'},
            'qry-1': {'agent_class': 'query', 'agent_name': 'Query 1'},
            'mgmt-1': {'agent_class': 'management', 'agent_name': 'Management 1'}
        }
        
        is_valid, error = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            agents
        )
        assert is_valid is False
        assert error is not None
        assert 'Ingestion playbook' in error
    
    def test_invalid_query_playbook(self):
        """Test validation fails on invalid query playbook"""
        ingestion_playbook = {
            'agent_execution_graph': {
                'nodes': ['ing-1'],
                'edges': []
            }
        }
        query_playbook = {
            'agent_execution_graph': {
                'nodes': ['qry-1', 'qry-2'],
                'edges': [
                    {'from': 'qry-1', 'to': 'qry-2'},
                    {'from': 'qry-2', 'to': 'qry-1'}  # Circular
                ]
            }
        }
        management_playbook = {
            'agent_execution_graph': {
                'nodes': ['mgmt-1'],
                'edges': []
            }
        }
        agents = {
            'ing-1': {'agent_class': 'ingestion', 'agent_name': 'Ingestion 1'},
            'qry-1': {'agent_class': 'query', 'agent_name': 'Query 1'},
            'qry-2': {'agent_class': 'query', 'agent_name': 'Query 2'},
            'mgmt-1': {'agent_class': 'management', 'agent_name': 'Management 1'}
        }
        
        is_valid, error = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            agents
        )
        assert is_valid is False
        assert error is not None
        assert 'Query playbook' in error
    
    def test_invalid_management_playbook(self):
        """Test validation fails on invalid management playbook"""
        ingestion_playbook = {
            'agent_execution_graph': {
                'nodes': ['ing-1'],
                'edges': []
            }
        }
        query_playbook = {
            'agent_execution_graph': {
                'nodes': ['qry-1'],
                'edges': []
            }
        }
        management_playbook = {
            'agent_execution_graph': {
                'nodes': [],  # Empty nodes
                'edges': []
            }
        }
        agents = {
            'ing-1': {'agent_class': 'ingestion', 'agent_name': 'Ingestion 1'},
            'qry-1': {'agent_class': 'query', 'agent_name': 'Query 1'}
        }
        
        is_valid, error = validate_domain_playbooks(
            ingestion_playbook,
            query_playbook,
            management_playbook,
            agents
        )
        assert is_valid is False
        assert error is not None
        assert 'Management playbook' in error


class TestHelperFunctions:
    """Test cases for helper functions"""
    
    def test_get_playbook_agent_count(self):
        """Test getting agent count from playbook"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B', 'agent-C'],
                'edges': []
            }
        }
        
        count = get_playbook_agent_count(playbook)
        assert count == 3
    
    def test_get_playbook_agent_count_empty(self):
        """Test getting agent count from empty playbook"""
        playbook = {
            'agent_execution_graph': {
                'nodes': [],
                'edges': []
            }
        }
        
        count = get_playbook_agent_count(playbook)
        assert count == 0
    
    def test_get_playbook_agent_count_invalid(self):
        """Test getting agent count from invalid playbook"""
        playbook = None
        count = get_playbook_agent_count(playbook)
        assert count == 0
        
        playbook = {}
        count = get_playbook_agent_count(playbook)
        assert count == 0
    
    def test_get_playbook_agents(self):
        """Test getting agent list from playbook"""
        playbook = {
            'agent_execution_graph': {
                'nodes': ['agent-A', 'agent-B', 'agent-C'],
                'edges': []
            }
        }
        
        agents = get_playbook_agents(playbook)
        assert agents == ['agent-A', 'agent-B', 'agent-C']
    
    def test_get_playbook_agents_empty(self):
        """Test getting agent list from empty playbook"""
        playbook = {
            'agent_execution_graph': {
                'nodes': [],
                'edges': []
            }
        }
        
        agents = get_playbook_agents(playbook)
        assert agents == []
    
    def test_get_playbook_agents_invalid(self):
        """Test getting agent list from invalid playbook"""
        playbook = None
        agents = get_playbook_agents(playbook)
        assert agents == []
        
        playbook = {}
        agents = get_playbook_agents(playbook)
        assert agents == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
