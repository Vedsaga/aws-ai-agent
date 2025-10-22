#!/usr/bin/env python3
"""
Demo script showing DAG validator in action
Run: python demo_dag_validator.py
"""

from dag_validator import (
    validate_dag,
    build_dependency_graph,
    topological_sort,
    validate_playbook_dag
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_valid_linear_chain():
    """Demo: Valid linear dependency chain"""
    print_section("Demo 1: Valid Linear Chain (A → B → C)")
    
    agents = {
        'agent-A': {
            'agent_name': 'Geo Locator',
            'agent_class': 'ingestion',
            'agent_dependencies': []
        },
        'agent-B': {
            'agent_name': 'Complaint Classifier',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-A']
        },
        'agent-C': {
            'agent_name': 'Priority Assessor',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-B']
        }
    }
    
    print("\nValidating agent-C with dependency on agent-B...")
    is_valid, error = validate_dag('agent-C', ['agent-B'], agents)
    print(f"✅ Valid: {is_valid}")
    print(f"   Error: {error}")
    
    print("\nBuilding dependency graph for agent-C...")
    graph = build_dependency_graph('agent-C', agents)
    print(f"   Nodes: {len(graph['nodes'])}")
    for node in graph['nodes']:
        print(f"     - {node['id']}: {node['label']} ({node['class']})")
    print(f"   Edges: {len(graph['edges'])}")
    for edge in graph['edges']:
        print(f"     - {edge['from']} → {edge['to']}")


def demo_circular_dependency():
    """Demo: Circular dependency detection"""
    print_section("Demo 2: Circular Dependency Detection (A → B → A)")
    
    agents = {
        'agent-A': {
            'agent_name': 'Agent A',
            'agent_class': 'query',
            'agent_dependencies': ['agent-B']
        },
        'agent-B': {
            'agent_name': 'Agent B',
            'agent_class': 'query',
            'agent_dependencies': []
        }
    }
    
    print("\nAttempting to make agent-B depend on agent-A (creates cycle)...")
    is_valid, error = validate_dag('agent-B', ['agent-A'], agents)
    print(f"❌ Valid: {is_valid}")
    print(f"   Error: {error}")


def demo_diamond_structure():
    """Demo: Diamond dependency structure"""
    print_section("Demo 3: Diamond Structure (A → B,C → D)")
    
    agents = {
        'agent-A': {
            'agent_name': 'Data Extractor',
            'agent_class': 'ingestion',
            'agent_dependencies': []
        },
        'agent-B': {
            'agent_name': 'Location Parser',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-A']
        },
        'agent-C': {
            'agent_name': 'Category Parser',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-A']
        },
        'agent-D': {
            'agent_name': 'Data Merger',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-B', 'agent-C']
        }
    }
    
    print("\nValidating agent-D with dependencies on agent-B and agent-C...")
    is_valid, error = validate_dag('agent-D', ['agent-B', 'agent-C'], agents)
    print(f"✅ Valid: {is_valid}")
    print(f"   Error: {error}")
    
    print("\nBuilding dependency graph for agent-D...")
    graph = build_dependency_graph('agent-D', agents)
    print(f"   Nodes: {len(graph['nodes'])}")
    for node in graph['nodes']:
        print(f"     - {node['id']}: {node['label']}")
    print(f"   Edges: {len(graph['edges'])}")
    for edge in graph['edges']:
        print(f"     - {edge['from']} → {edge['to']}")


def demo_topological_sort():
    """Demo: Topological sort for execution order"""
    print_section("Demo 4: Topological Sort (Execution Order)")
    
    nodes = ['geo', 'temporal', 'classifier', 'priority', 'merger']
    edges = [
        {'from': 'geo', 'to': 'merger'},
        {'from': 'temporal', 'to': 'merger'},
        {'from': 'classifier', 'to': 'priority'},
        {'from': 'priority', 'to': 'merger'}
    ]
    
    print("\nGraph structure:")
    print("  geo → merger")
    print("  temporal → merger")
    print("  classifier → priority → merger")
    
    print("\nComputing execution order...")
    is_valid, order, error = topological_sort(nodes, edges)
    print(f"✅ Valid: {is_valid}")
    print(f"   Execution order: {' → '.join(order)}")


def demo_playbook_validation():
    """Demo: Playbook validation"""
    print_section("Demo 5: Playbook Validation")
    
    agents = {
        'agent-geo': {
            'agent_name': 'Geo Locator',
            'agent_class': 'ingestion',
            'agent_dependencies': []
        },
        'agent-classifier': {
            'agent_name': 'Classifier',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-geo']
        },
        'agent-priority': {
            'agent_name': 'Priority',
            'agent_class': 'ingestion',
            'agent_dependencies': ['agent-classifier']
        }
    }
    
    playbook = {
        'agent_execution_graph': {
            'nodes': ['agent-geo', 'agent-classifier', 'agent-priority'],
            'edges': [
                {'from': 'agent-geo', 'to': 'agent-classifier'},
                {'from': 'agent-classifier', 'to': 'agent-priority'}
            ]
        }
    }
    
    print("\nValidating ingestion playbook...")
    print("  Nodes: agent-geo, agent-classifier, agent-priority")
    print("  Edges: geo → classifier → priority")
    
    is_valid, error = validate_playbook_dag(playbook, 'ingestion', agents)
    print(f"✅ Valid: {is_valid}")
    print(f"   Error: {error}")
    
    # Now try with wrong agent class
    print("\nValidating with wrong agent class (query instead of ingestion)...")
    agents['agent-priority']['agent_class'] = 'query'
    
    is_valid, error = validate_playbook_dag(playbook, 'ingestion', agents)
    print(f"❌ Valid: {is_valid}")
    print(f"   Error: {error}")


def demo_complex_circular():
    """Demo: Complex circular dependency"""
    print_section("Demo 6: Complex Circular Dependency (5 nodes)")
    
    agents = {
        'agent-A': {'agent_name': 'A', 'agent_class': 'query', 'agent_dependencies': []},
        'agent-B': {'agent_name': 'B', 'agent_class': 'query', 'agent_dependencies': ['agent-A']},
        'agent-C': {'agent_name': 'C', 'agent_class': 'query', 'agent_dependencies': ['agent-B']},
        'agent-D': {'agent_name': 'D', 'agent_class': 'query', 'agent_dependencies': ['agent-C']},
        'agent-E': {'agent_name': 'E', 'agent_class': 'query', 'agent_dependencies': ['agent-D']}
    }
    
    print("\nCurrent chain: A → B → C → D → E")
    print("Attempting to make B depend on E (creates long cycle)...")
    
    is_valid, error = validate_dag('agent-B', ['agent-A', 'agent-E'], agents)
    print(f"❌ Valid: {is_valid}")
    print(f"   Error: {error}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  DAG Validator Demo")
    print("  Testing various graph structures and validations")
    print("="*60)
    
    demo_valid_linear_chain()
    demo_circular_dependency()
    demo_diamond_structure()
    demo_topological_sort()
    demo_playbook_validation()
    demo_complex_circular()
    
    print("\n" + "="*60)
    print("  Demo Complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
