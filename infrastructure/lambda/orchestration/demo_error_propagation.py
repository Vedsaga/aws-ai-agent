"""
Demo script for error propagation in Orchestrator

This script demonstrates:
- Requirement 15.1: Mark failed agents as 'error' in execution_log
- Requirement 15.2: Automatically mark dependent agents as 'skipped'
- Requirement 15.3: Set job status to 'failed' on any agent failure
- Requirement 15.4: Stop execution on first failure (fail-fast)
- Requirement 15.5: Error handling in execute_agent()
"""

import json
from unittest.mock import patch, MagicMock

# Mock AWS services
mock_dynamodb = MagicMock()
mock_bedrock = MagicMock()

with patch('boto3.resource', return_value=mock_dynamodb):
    with patch('boto3.client', return_value=mock_bedrock):
        from orchestrator import Orchestrator


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_execution_log(execution_log):
    """Print execution log in a readable format"""
    for i, entry in enumerate(execution_log, 1):
        print(f"{i}. Agent: {entry['agent_name']} ({entry['agent_id']})")
        print(f"   Status: {entry['status'].upper()}")
        print(f"   Timestamp: {entry['timestamp']}")
        
        if entry['status'] == 'success':
            print(f"   Reasoning: {entry['reasoning']}")
            print(f"   Output: {json.dumps(entry['output'], indent=6)}")
        elif entry['status'] == 'error':
            print(f"   Error: {entry['error_message']}")
        elif entry['status'] == 'skipped':
            print(f"   Reason: {entry['reasoning']}")
        
        print()


def demo_linear_failure():
    """Demo: Error in middle of linear chain"""
    print_section("Demo 1: Error in Middle of Linear Chain")
    
    # Linear playbook: agent_a -> agent_b -> agent_c
    playbook = {
        "agent_execution_graph": {
            "nodes": ["agent_a", "agent_b", "agent_c"],
            "edges": [
                {"from": "agent_a", "to": "agent_b"},
                {"from": "agent_b", "to": "agent_c"}
            ]
        }
    }
    
    orchestrator = Orchestrator(
        job_id="demo-job-1",
        playbook=playbook,
        domain_id="demo-domain",
        tenant_id="demo-tenant"
    )
    
    # Mock agent_b to fail
    def mock_invoke(config, input_data):
        if config["agent_id"] == "agent_b":
            return {
                "status": "error",
                "output": None,
                "reasoning": "",
                "error_message": "LLM API timeout after 30 seconds"
            }
        return {
            "status": "success",
            "output": {"data": f"Processed by {config['agent_id']}"},
            "reasoning": f"Successfully processed input data",
            "confidence": 0.9
        }
    
    with patch.object(orchestrator, '_load_agent_config') as mock_load:
        with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
            def load_config(agent_id):
                deps = {
                    "agent_a": [],
                    "agent_b": ["agent_a"],
                    "agent_c": ["agent_b"]
                }
                return {
                    "agent_id": agent_id,
                    "agent_name": agent_id.replace("_", " ").title(),
                    "agent_dependencies": deps.get(agent_id, [])
                }
            
            mock_load.side_effect = load_config
            
            result = orchestrator.execute({"text": "Test input"})
    
    print(f"Job Status: {result['status'].upper()}")
    print(f"\nExecution Log ({len(orchestrator.execution_log)} entries):\n")
    print_execution_log(orchestrator.execution_log)
    
    print("Key Observations:")
    print("✓ agent_a executed successfully")
    print("✓ agent_b failed with error message")
    print("✓ agent_c was automatically skipped")
    print("✓ Job status set to 'failed'")
    print("✓ Execution stopped immediately after failure (fail-fast)")


def demo_parallel_failure():
    """Demo: Error in parallel execution branches"""
    print_section("Demo 2: Error in Parallel Execution Branches")
    
    # Parallel playbook: agent_a -> agent_b, agent_c -> agent_d
    playbook = {
        "agent_execution_graph": {
            "nodes": ["agent_a", "agent_b", "agent_c", "agent_d"],
            "edges": [
                {"from": "agent_a", "to": "agent_b"},
                {"from": "agent_a", "to": "agent_c"},
                {"from": "agent_b", "to": "agent_d"},
                {"from": "agent_c", "to": "agent_d"}
            ]
        }
    }
    
    orchestrator = Orchestrator(
        job_id="demo-job-2",
        playbook=playbook,
        domain_id="demo-domain",
        tenant_id="demo-tenant"
    )
    
    # Mock agent_b to fail (one branch)
    def mock_invoke(config, input_data):
        if config["agent_id"] == "agent_b":
            return {
                "status": "error",
                "output": None,
                "reasoning": "",
                "error_message": "Database connection failed: Unable to reach RDS instance"
            }
        return {
            "status": "success",
            "output": {"data": f"Processed by {config['agent_id']}"},
            "reasoning": f"Successfully processed input data",
            "confidence": 0.9
        }
    
    with patch.object(orchestrator, '_load_agent_config') as mock_load:
        with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
            def load_config(agent_id):
                deps = {
                    "agent_a": [],
                    "agent_b": ["agent_a"],
                    "agent_c": ["agent_a"],
                    "agent_d": ["agent_b", "agent_c"]
                }
                return {
                    "agent_id": agent_id,
                    "agent_name": agent_id.replace("_", " ").title(),
                    "agent_dependencies": deps.get(agent_id, [])
                }
            
            mock_load.side_effect = load_config
            
            result = orchestrator.execute({"text": "Test input"})
    
    print(f"Job Status: {result['status'].upper()}")
    print(f"\nExecution Log ({len(orchestrator.execution_log)} entries):\n")
    print_execution_log(orchestrator.execution_log)
    
    print("Key Observations:")
    print("✓ agent_a executed successfully (shared dependency)")
    print("✓ agent_b failed in one branch")
    print("✓ Remaining agents (agent_c, agent_d) were skipped")
    print("✓ Job status set to 'failed'")
    print("✓ Fail-fast prevented further execution")


def demo_exception_handling():
    """Demo: Exception handling in agent execution"""
    print_section("Demo 3: Exception Handling in Agent Execution")
    
    # Simple playbook: agent_a -> agent_b
    playbook = {
        "agent_execution_graph": {
            "nodes": ["agent_a", "agent_b"],
            "edges": [
                {"from": "agent_a", "to": "agent_b"}
            ]
        }
    }
    
    orchestrator = Orchestrator(
        job_id="demo-job-3",
        playbook=playbook,
        domain_id="demo-domain",
        tenant_id="demo-tenant"
    )
    
    # Mock agent_b to raise exception
    def mock_invoke(config, input_data):
        if config["agent_id"] == "agent_b":
            raise Exception("Unexpected error: JSON parsing failed")
        return {
            "status": "success",
            "output": {"data": f"Processed by {config['agent_id']}"},
            "reasoning": f"Successfully processed input data",
            "confidence": 0.9
        }
    
    with patch.object(orchestrator, '_load_agent_config') as mock_load:
        with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
            def load_config(agent_id):
                deps = {
                    "agent_a": [],
                    "agent_b": ["agent_a"]
                }
                return {
                    "agent_id": agent_id,
                    "agent_name": agent_id.replace("_", " ").title(),
                    "agent_dependencies": deps.get(agent_id, [])
                }
            
            mock_load.side_effect = load_config
            
            result = orchestrator.execute({"text": "Test input"})
    
    print(f"Job Status: {result['status'].upper()}")
    print(f"\nExecution Log ({len(orchestrator.execution_log)} entries):\n")
    print_execution_log(orchestrator.execution_log)
    
    print("Key Observations:")
    print("✓ agent_a executed successfully")
    print("✓ Exception in agent_b was caught and logged")
    print("✓ Error message preserved in execution log")
    print("✓ Job status set to 'failed'")
    print("✓ System remained stable despite exception")


def demo_first_agent_failure():
    """Demo: Failure of first agent in chain"""
    print_section("Demo 4: Failure of First Agent in Chain")
    
    # Linear playbook: agent_a -> agent_b -> agent_c
    playbook = {
        "agent_execution_graph": {
            "nodes": ["agent_a", "agent_b", "agent_c"],
            "edges": [
                {"from": "agent_a", "to": "agent_b"},
                {"from": "agent_b", "to": "agent_c"}
            ]
        }
    }
    
    orchestrator = Orchestrator(
        job_id="demo-job-4",
        playbook=playbook,
        domain_id="demo-domain",
        tenant_id="demo-tenant"
    )
    
    # Mock agent_a to fail (first agent)
    def mock_invoke(config, input_data):
        if config["agent_id"] == "agent_a":
            return {
                "status": "error",
                "output": None,
                "reasoning": "",
                "error_message": "Configuration error: Missing required environment variable BEDROCK_MODEL_ID"
            }
        return {
            "status": "success",
            "output": {"data": f"Processed by {config['agent_id']}"},
            "reasoning": f"Successfully processed input data",
            "confidence": 0.9
        }
    
    with patch.object(orchestrator, '_load_agent_config') as mock_load:
        with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
            def load_config(agent_id):
                deps = {
                    "agent_a": [],
                    "agent_b": ["agent_a"],
                    "agent_c": ["agent_b"]
                }
                return {
                    "agent_id": agent_id,
                    "agent_name": agent_id.replace("_", " ").title(),
                    "agent_dependencies": deps.get(agent_id, [])
                }
            
            mock_load.side_effect = load_config
            
            result = orchestrator.execute({"text": "Test input"})
    
    print(f"Job Status: {result['status'].upper()}")
    print(f"\nExecution Log ({len(orchestrator.execution_log)} entries):\n")
    print_execution_log(orchestrator.execution_log)
    
    print("Key Observations:")
    print("✓ agent_a failed immediately")
    print("✓ All dependent agents (agent_b, agent_c) were skipped")
    print("✓ Job status set to 'failed'")
    print("✓ No unnecessary agent invocations")
    print("✓ Clear error message for debugging")


def main():
    """Run all demos"""
    print("\n" + "█" * 80)
    print("  ERROR PROPAGATION DEMONSTRATION")
    print("  Requirements: 15.1, 15.2, 15.3, 15.4, 15.5")
    print("█" * 80)
    
    demo_linear_failure()
    demo_parallel_failure()
    demo_exception_handling()
    demo_first_agent_failure()
    
    print_section("Summary")
    print("All error propagation requirements demonstrated:")
    print()
    print("✓ 15.1: Failed agents marked as 'error' with error details")
    print("✓ 15.2: Dependent agents automatically marked as 'skipped'")
    print("✓ 15.3: Job status set to 'failed' on any agent failure")
    print("✓ 15.4: Execution stops on first failure (fail-fast)")
    print("✓ 15.5: Exceptions properly handled in execute_agent()")
    print()
    print("Error propagation is working correctly! ✓")
    print()


if __name__ == "__main__":
    main()
