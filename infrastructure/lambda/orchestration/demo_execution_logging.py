"""
Demo script to show execution logging in action

This demonstrates how the orchestrator logs agent executions with
reasoning, outputs, and timestamps.
"""

import json
from unittest.mock import patch, MagicMock

# Mock AWS services
mock_dynamodb = MagicMock()
mock_bedrock = MagicMock()

with patch('boto3.resource', return_value=mock_dynamodb):
    with patch('boto3.client', return_value=mock_bedrock):
        from orchestrator import Orchestrator


def demo_execution_logging():
    """Demonstrate execution logging with a sample playbook"""
    
    print("=" * 80)
    print("EXECUTION LOGGING DEMO")
    print("=" * 80)
    print()
    
    # Create a sample playbook
    playbook = {
        "agent_execution_graph": {
            "nodes": ["geo_agent", "temporal_agent", "category_agent"],
            "edges": [
                {"from": "geo_agent", "to": "category_agent"}
            ]
        }
    }
    
    # Initialize orchestrator
    orchestrator = Orchestrator(
        job_id="demo-job-123",
        playbook=playbook,
        domain_id="civic_complaints",
        tenant_id="demo-tenant",
        user_id="demo-user"
    )
    
    print("Playbook Configuration:")
    print(f"  Agents: {playbook['agent_execution_graph']['nodes']}")
    print(f"  Dependencies: {playbook['agent_execution_graph']['edges']}")
    print()
    
    # Mock agent configurations and results
    def mock_load_config(agent_id):
        configs = {
            "geo_agent": {
                "agent_id": "geo_agent",
                "agent_name": "Geo Locator",
                "agent_dependencies": []
            },
            "temporal_agent": {
                "agent_id": "temporal_agent",
                "agent_name": "Temporal Analyzer",
                "agent_dependencies": []
            },
            "category_agent": {
                "agent_id": "category_agent",
                "agent_name": "Category Classifier",
                "agent_dependencies": ["geo_agent"]
            }
        }
        return configs.get(agent_id)
    
    def mock_invoke(config, input_data):
        agent_id = config["agent_id"]
        
        results = {
            "geo_agent": {
                "status": "success",
                "output": {
                    "location": {
                        "address": "123 Main Street, New York",
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "city": "New York",
                        "country": "USA"
                    }
                },
                "reasoning": "Extracted location from text using pattern matching and geocoding. High confidence match found for '123 Main Street'.",
                "confidence": 0.95
            },
            "temporal_agent": {
                "status": "success",
                "output": {
                    "timestamp": "2025-10-21T14:30:00Z",
                    "relative_time": "yesterday afternoon",
                    "duration": "ongoing"
                },
                "reasoning": "Identified temporal reference 'yesterday afternoon' and converted to absolute timestamp based on current time.",
                "confidence": 0.9
            },
            "category_agent": {
                "status": "success",
                "output": {
                    "category": "pothole",
                    "subcategory": "road_damage",
                    "severity": "high",
                    "details": "Large pothole causing traffic hazard"
                },
                "reasoning": "Classified as pothole based on keywords 'hole in road' and 'causing damage'. Severity assessed as high due to safety concerns.",
                "confidence": 0.88
            }
        }
        
        return results.get(agent_id, {
            "status": "success",
            "output": {},
            "reasoning": "Default response",
            "confidence": 0.5
        })
    
    # Execute with mocked functions
    with patch.object(orchestrator, '_load_agent_config', side_effect=mock_load_config):
        with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
            
            input_data = {
                "text": "There's a huge hole in the road at 123 Main Street that damaged my car yesterday afternoon"
            }
            
            print("Input Data:")
            print(f"  {input_data['text']}")
            print()
            
            print("Executing agents...")
            print()
            
            result = orchestrator.execute(input_data)
    
    # Display execution log
    print("=" * 80)
    print("EXECUTION LOG")
    print("=" * 80)
    print()
    
    for i, log_entry in enumerate(result["execution_log"], 1):
        print(f"Agent {i}: {log_entry['agent_name']} ({log_entry['agent_id']})")
        print(f"  Status: {log_entry['status']}")
        print(f"  Timestamp: {log_entry['timestamp']}")
        print(f"  Execution Time: {log_entry['execution_time_ms']}ms")
        print(f"  Reasoning: {log_entry['reasoning']}")
        print(f"  Output: {json.dumps(log_entry['output'], indent=4)}")
        print()
    
    # Display summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Job Status: {result['status']}")
    print(f"Total Agents: {result['cache_stats']['total_agents']}")
    print(f"Executed: {result['cache_stats']['executed_agents']}")
    print(f"Cached: {result['cache_stats']['cached_agents']}")
    print()
    
    print("✅ Execution logging captures:")
    print("  • Agent ID and name")
    print("  • Execution status (success/error/cached/skipped)")
    print("  • Timestamp for chronological ordering")
    print("  • Agent reasoning/thought process")
    print("  • Complete intermediate outputs")
    print("  • Execution time in milliseconds")
    print()


if __name__ == "__main__":
    demo_execution_logging()
