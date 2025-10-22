"""
Test script for RDS utilities

Tests the RDS connection and query functions for agents and domains.
"""

import json
import os
from rds_utils import (
    get_agent_by_id,
    get_all_agents,
    get_domain_by_id,
    get_playbook,
    get_agents_by_ids,
    close_connection
)


def test_rds_connection():
    """Test basic RDS connection"""
    print("Testing RDS connection...")
    
    try:
        # Test getting all agents
        tenant_id = "demo-tenant-001"
        agents = get_all_agents(tenant_id)
        
        print(f"✓ Successfully connected to RDS")
        print(f"✓ Found {len(agents)} agents for tenant {tenant_id}")
        
        if agents:
            print(f"\nSample agent:")
            print(json.dumps(agents[0], indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"✗ RDS connection failed: {str(e)}")
        return False


def test_get_agent():
    """Test getting a specific agent"""
    print("\n\nTesting get_agent_by_id...")
    
    try:
        tenant_id = "demo-tenant-001"
        
        # First get all agents to find one
        agents = get_all_agents(tenant_id)
        
        if not agents:
            print("⚠ No agents found to test with")
            return True
        
        agent_id = agents[0]['agent_id']
        agent = get_agent_by_id(tenant_id, agent_id)
        
        if agent:
            print(f"✓ Successfully retrieved agent: {agent['agent_name']}")
            print(f"  - Agent ID: {agent['agent_id']}")
            print(f"  - Agent Class: {agent['agent_class']}")
            print(f"  - Enabled: {agent['enabled']}")
            return True
        else:
            print(f"✗ Agent not found: {agent_id}")
            return False
            
    except Exception as e:
        print(f"✗ get_agent_by_id failed: {str(e)}")
        return False


def test_get_agents_by_class():
    """Test filtering agents by class"""
    print("\n\nTesting get_all_agents with class filter...")
    
    try:
        tenant_id = "demo-tenant-001"
        
        for agent_class in ['ingestion', 'query', 'management']:
            agents = get_all_agents(tenant_id, agent_class)
            print(f"✓ Found {len(agents)} {agent_class} agents")
        
        return True
        
    except Exception as e:
        print(f"✗ get_all_agents with filter failed: {str(e)}")
        return False


def test_get_domain():
    """Test getting a domain configuration"""
    print("\n\nTesting get_domain_by_id...")
    
    try:
        tenant_id = "demo-tenant-001"
        domain_id = "civic_complaints"  # Common test domain
        
        domain = get_domain_by_id(tenant_id, domain_id)
        
        if domain:
            print(f"✓ Successfully retrieved domain: {domain['domain_name']}")
            print(f"  - Domain ID: {domain['domain_id']}")
            print(f"  - Has ingestion_playbook: {'ingestion_playbook' in domain}")
            print(f"  - Has query_playbook: {'query_playbook' in domain}")
            print(f"  - Has management_playbook: {'management_playbook' in domain}")
            return True
        else:
            print(f"⚠ Domain not found: {domain_id} (this is OK if not seeded yet)")
            return True
            
    except Exception as e:
        print(f"✗ get_domain_by_id failed: {str(e)}")
        return False


def test_get_playbook():
    """Test getting a specific playbook"""
    print("\n\nTesting get_playbook...")
    
    try:
        tenant_id = "demo-tenant-001"
        domain_id = "civic_complaints"
        
        for playbook_type in ['ingestion', 'query', 'management']:
            playbook = get_playbook(tenant_id, domain_id, playbook_type)
            
            if playbook:
                graph = playbook.get('agent_execution_graph', {})
                nodes = graph.get('nodes', [])
                edges = graph.get('edges', [])
                
                print(f"✓ Retrieved {playbook_type} playbook:")
                print(f"  - Nodes: {len(nodes)} agents")
                print(f"  - Edges: {len(edges)} dependencies")
            else:
                print(f"⚠ {playbook_type} playbook not found (OK if not seeded)")
        
        return True
        
    except Exception as e:
        print(f"✗ get_playbook failed: {str(e)}")
        return False


def test_get_agents_batch():
    """Test batch loading of agents"""
    print("\n\nTesting get_agents_by_ids...")
    
    try:
        tenant_id = "demo-tenant-001"
        
        # Get some agent IDs first
        all_agents = get_all_agents(tenant_id)
        
        if not all_agents:
            print("⚠ No agents to test batch loading")
            return True
        
        # Take first 3 agent IDs
        agent_ids = [a['agent_id'] for a in all_agents[:3]]
        
        agents_dict = get_agents_by_ids(tenant_id, agent_ids)
        
        print(f"✓ Batch loaded {len(agents_dict)} agents from {len(agent_ids)} requested")
        
        for agent_id, agent in agents_dict.items():
            print(f"  - {agent['agent_name']} ({agent['agent_class']})")
        
        return True
        
    except Exception as e:
        print(f"✗ get_agents_by_ids failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("RDS Utilities Test Suite")
    print("=" * 60)
    
    tests = [
        test_rds_connection,
        test_get_agent,
        test_get_agents_by_class,
        test_get_domain,
        test_get_playbook,
        test_get_agents_batch
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {str(e)}")
            results.append(False)
    
    # Close connection
    close_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
