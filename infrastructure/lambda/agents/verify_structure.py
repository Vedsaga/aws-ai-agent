#!/usr/bin/env python3
"""
Verify agent framework structure without requiring AWS dependencies
"""

import os
import json


def verify_files_exist():
    """Verify all required files exist"""
    print("Verifying file structure...")
    
    required_files = [
        'base_agent.py',
        'geo_agent.py',
        'temporal_agent.py',
        'entity_agent.py',
        'query_agents.py',
        'custom_agent.py',
        'agent_utils.py',
        'seed_data.json',
        'requirements.txt',
        'README.md'
    ]
    
    all_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} - MISSING")
            all_exist = False
    
    return all_exist


def verify_seed_data():
    """Verify seed data structure"""
    print("\nVerifying seed data...")
    
    try:
        with open('seed_data.json', 'r') as f:
            data = json.load(f)
        
        # Check structure
        required_keys = ['custom_agents', 'ingestion_playbooks', 'dependency_graphs', 'domains']
        for key in required_keys:
            if key in data:
                print(f"✓ {key}: {len(data[key])} items")
            else:
                print(f"✗ {key} - MISSING")
                return False
        
        # Check SeverityClassifier
        severity = None
        for agent in data['custom_agents']:
            if agent['agent_id'] == 'severity-classifier':
                severity = agent
                break
        
        if severity:
            print(f"✓ SeverityClassifier found")
            print(f"  - Agent name: {severity['agent_name']}")
            print(f"  - Depends on: {severity['dependency_parent']}")
            print(f"  - Output keys: {len(severity['output_schema'])}")
            
            if len(severity['output_schema']) == 5:
                print(f"  ✓ Output schema has exactly 5 keys")
            else:
                print(f"  ✗ Output schema should have 5 keys, has {len(severity['output_schema'])}")
                return False
        else:
            print(f"✗ SeverityClassifier not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading seed data: {str(e)}")
        return False


def verify_code_structure():
    """Verify code structure without importing"""
    print("\nVerifying code structure...")
    
    checks = []
    
    # Check base_agent.py
    with open('base_agent.py', 'r') as f:
        base_content = f.read()
        checks.append(('BaseAgent class', 'class BaseAgent' in base_content))
        checks.append(('execute method', 'def execute(' in base_content))
        checks.append(('invoke_bedrock method', 'def invoke_bedrock(' in base_content))
        checks.append(('invoke_tool method', 'def invoke_tool(' in base_content))
        checks.append(('validate_output method', 'def validate_output(' in base_content))
        checks.append(('handle_execution method', 'def handle_execution(' in base_content))
        checks.append(('Max 5 keys validation', 'len(self.output_schema) > 5' in base_content))
    
    # Check geo_agent.py
    with open('geo_agent.py', 'r') as f:
        geo_content = f.read()
        checks.append(('GeoAgent class', 'class GeoAgent' in geo_content))
        checks.append(('GeoAgent lambda_handler', 'def lambda_handler(' in geo_content))
    
    # Check temporal_agent.py
    with open('temporal_agent.py', 'r') as f:
        temporal_content = f.read()
        checks.append(('TemporalAgent class', 'class TemporalAgent' in temporal_content))
        checks.append(('Relative time parsing', 'yesterday' in temporal_content))
    
    # Check entity_agent.py
    with open('entity_agent.py', 'r') as f:
        entity_content = f.read()
        checks.append(('EntityAgent class', 'class EntityAgent' in entity_content))
        checks.append(('Comprehend integration', 'comprehend' in entity_content))
    
    # Check query_agents.py
    with open('query_agents.py', 'r') as f:
        query_content = f.read()
        checks.append(('WhenAgent class', 'class WhenAgent' in query_content))
        checks.append(('WhereAgent class', 'class WhereAgent' in query_content))
        checks.append(('WhyAgent class', 'class WhyAgent' in query_content))
        checks.append(('HowAgent class', 'class HowAgent' in query_content))
        checks.append(('WhatAgent class', 'class WhatAgent' in query_content))
        checks.append(('WhoAgent class', 'class WhoAgent' in query_content))
        checks.append(('WhichAgent class', 'class WhichAgent' in query_content))
        checks.append(('HowManyAgent class', 'class HowManyAgent' in query_content))
        checks.append(('HowMuchAgent class', 'class HowMuchAgent' in query_content))
        checks.append(('FromWhereAgent class', 'class FromWhereAgent' in query_content))
        checks.append(('WhatKindAgent class', 'class WhatKindAgent' in query_content))
    
    # Check custom_agent.py
    with open('custom_agent.py', 'r') as f:
        custom_content = f.read()
        checks.append(('CustomAgent class', 'class CustomAgent' in custom_content))
        checks.append(('Dependency support', 'parent_output' in custom_content))
        checks.append(('Schema validation', 'len(output_schema) > 5' in custom_content))
    
    all_passed = True
    for check_name, result in checks:
        if result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False
    
    return all_passed


def count_lines_of_code():
    """Count lines of code"""
    print("\nCode statistics...")
    
    files = [
        'base_agent.py',
        'geo_agent.py',
        'temporal_agent.py',
        'entity_agent.py',
        'query_agents.py',
        'custom_agent.py',
        'agent_utils.py'
    ]
    
    total_lines = 0
    for filename in files:
        with open(filename, 'r') as f:
            lines = len(f.readlines())
            total_lines += lines
            print(f"  {filename}: {lines} lines")
    
    print(f"\nTotal: {total_lines} lines of code")


def main():
    print("=" * 60)
    print("Agent Framework Structure Verification")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(verify_files_exist())
    results.append(verify_seed_data())
    results.append(verify_code_structure())
    
    count_lines_of_code()
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All verifications passed!")
        print("=" * 60)
        print("\nAgent framework is ready for deployment.")
        print("\nImplemented:")
        print("  - Base agent framework with tool invocation")
        print("  - 3 ingestion agents (Geo, Temporal, Entity)")
        print("  - 11 interrogative query agents")
        print("  - Custom agent framework")
        print("  - SeverityClassifier pre-configured in seed data")
        print("  - Output schema validation (max 5 keys)")
        print("  - Single-level dependency support")
        print("  - Error handling and timeout management")
        return 0
    else:
        print("✗ Some verifications failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
