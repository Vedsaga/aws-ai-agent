#!/usr/bin/env python3
"""
Seed DynamoDB with configuration data
"""
import json
import boto3
import sys
from datetime import datetime
import uuid

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'MultiAgentOrchestration-dev-Data-Configurations'

def seed_data():
    """Seed configuration data into DynamoDB"""
    try:
        table = dynamodb.Table(table_name)
        
        # Load seed data
        with open('../lambda/config-api/seed_configs.json', 'r') as f:
            seed_data = json.load(f)
        
        print(f"Seeding data into table: {table_name}")
        
        # Seed domain templates
        for template in seed_data.get('domain_templates', []):
            domain_id = template['domain_id']
            
            # Store domain template
            item = {
                'PK': f'DOMAIN#{domain_id}',
                'SK': 'METADATA',
                'entity_type': 'domain_template',
                'domain_id': domain_id,
                'template_name': template['template_name'],
                'description': template['description'],
                'is_builtin': template.get('is_builtin', True),
                'ui_template': template.get('ui_template', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            table.put_item(Item=item)
            print(f"✓ Seeded domain template: {template['template_name']}")
            
            # Store agent configs
            for agent in template.get('agent_configs', []):
                agent_id = agent['agent_id']
                item = {
                    'PK': f'DOMAIN#{domain_id}',
                    'SK': f'AGENT#{agent_id}',
                    'entity_type': 'agent_config',
                    'agent_id': agent_id,
                    'agent_name': agent['agent_name'],
                    'agent_type': agent['agent_type'],
                    'system_prompt': agent['system_prompt'],
                    'tools': agent['tools'],
                    'output_schema': agent['output_schema'],
                    'is_builtin': agent.get('is_builtin', True),
                    'dependency_parent': agent.get('dependency_parent'),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                table.put_item(Item=item)
                print(f"  ✓ Seeded agent: {agent['agent_name']}")
            
            # Store playbook configs
            for idx, playbook in enumerate(template.get('playbook_configs', [])):
                playbook_id = f"{domain_id}_{playbook['playbook_type']}"
                item = {
                    'PK': f'DOMAIN#{domain_id}',
                    'SK': f'PLAYBOOK#{playbook_id}',
                    'entity_type': 'playbook_config',
                    'playbook_id': playbook_id,
                    'playbook_type': playbook['playbook_type'],
                    'agent_ids': playbook['agent_ids'],
                    'description': playbook['description'],
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                table.put_item(Item=item)
                print(f"  ✓ Seeded playbook: {playbook['playbook_type']}")
            
            # Store dependency graphs
            for idx, dep_graph in enumerate(template.get('dependency_graph_configs', [])):
                graph_id = f"{domain_id}_graph_{idx}"
                item = {
                    'PK': f'DOMAIN#{domain_id}',
                    'SK': f'DEPGRAPH#{graph_id}',
                    'entity_type': 'dependency_graph',
                    'graph_id': graph_id,
                    'edges': dep_graph.get('edges', []),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                table.put_item(Item=item)
                print(f"  ✓ Seeded dependency graph")
        
        # Seed query agents
        for agent in seed_data.get('query_agents', []):
            agent_id = f"query_{agent['interrogative']}_agent"
            item = {
                'PK': 'QUERY_AGENTS',
                'SK': f'AGENT#{agent_id}',
                'entity_type': 'query_agent',
                'agent_id': agent_id,
                'agent_name': agent['agent_name'],
                'agent_type': agent['agent_type'],
                'interrogative': agent['interrogative'],
                'system_prompt': agent['system_prompt'],
                'tools': agent['tools'],
                'output_schema': agent['output_schema'],
                'is_builtin': agent.get('is_builtin', True),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            table.put_item(Item=item)
            print(f"✓ Seeded query agent: {agent['agent_name']}")
        
        print("\n✅ Successfully seeded all configuration data!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = seed_data()
    sys.exit(0 if success else 1)
