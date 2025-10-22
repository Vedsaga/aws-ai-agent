"""
Unit tests for Orchestrator error propagation functionality

Tests Requirements:
- 15.1: Mark failed agents as 'error' in execution_log
- 15.2: Automatically mark dependent agents as 'skipped'
- 15.3: Set job status to 'failed' on any agent failure
- 15.4: Stop execution on first failure (fail-fast)
- 15.5: Error handling in execute_agent()
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Mock AWS services before importing orchestrator
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock boto3
mock_dynamodb = MagicMock()
mock_bedrock = MagicMock()

with patch('boto3.resource', return_value=mock_dynamodb):
    with patch('boto3.client', return_value=mock_bedrock):
        from orchestrator import Orchestrator


class TestOrchestratorErrorPropagation(unittest.TestCase):
    """Test error propagation and fail-fast behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.job_id = "test-job-error-123"
        self.domain_id = "test-domain"
        self.tenant_id = "test-tenant"
        self.user_id = "test-user"
        
        # Linear playbook: agent_a -> agent_b -> agent_c
        self.linear_playbook = {
            "agent_execution_graph": {
                "nodes": ["agent_a", "agent_b", "agent_c"],
                "edges": [
                    {"from": "agent_a", "to": "agent_b"},
                    {"from": "agent_b", "to": "agent_c"}
                ]
            }
        }
        
        # Parallel playbook with shared dependency
        # agent_a -> agent_b, agent_c -> agent_d
        self.parallel_playbook = {
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
    
    def test_agent_error_marked_in_log(self):
        """Test that failed agents are marked as 'error' in execution_log"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
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
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 15.1: Failed agent marked as 'error'
                error_logs = [e for e in orchestrator.execution_log if e["status"] == "error"]
                self.assertEqual(len(error_logs), 1)
                self.assertEqual(error_logs[0]["agent_id"], "agent_b")
                self.assertIn("error_message", error_logs[0])
                self.assertEqual(error_logs[0]["error_message"], "LLM API timeout after 30 seconds")
    
    def test_dependent_agents_marked_skipped(self):
        """Test that dependent agents are automatically marked as 'skipped'"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent_b to fail
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_b":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": "Agent execution failed"
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 15.2: Dependent agents marked as 'skipped'
                skipped_logs = [e for e in orchestrator.execution_log if e["status"] == "skipped"]
                self.assertEqual(len(skipped_logs), 1)
                self.assertEqual(skipped_logs[0]["agent_id"], "agent_c")
                self.assertIn("agent_b", skipped_logs[0]["reasoning"])
    
    def test_job_status_failed_on_error(self):
        """Test that job status is set to 'failed' on any agent failure"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent_a to fail (first agent)
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_a":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": "Configuration error"
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 15.3: Job status set to 'failed'
                self.assertEqual(result["status"], "failed")
    
    def test_fail_fast_stops_execution(self):
        """Test that execution stops on first failure (fail-fast)"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        invoke_count = {"count": 0}
        
        # Mock agent_b to fail
        def mock_invoke(config, input_data):
            invoke_count["count"] += 1
            if config["agent_id"] == "agent_b":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": "Fail fast test"
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 15.4: Stop execution on first failure
                # Only agent_a and agent_b should be invoked, not agent_c
                self.assertEqual(invoke_count["count"], 2)
                
                # Verify execution log
                self.assertEqual(len(orchestrator.execution_log), 3)  # success, error, skipped
                self.assertEqual(orchestrator.execution_log[0]["status"], "success")  # agent_a
                self.assertEqual(orchestrator.execution_log[1]["status"], "error")    # agent_b
                self.assertEqual(orchestrator.execution_log[2]["status"], "skipped")  # agent_c
    
    def test_exception_handling_in_execute_agent(self):
        """Test that exceptions in execute_agent are properly handled"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent_b to raise exception
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_b":
                raise Exception("Unexpected error in agent execution")
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 15.5: Error handling in execute_agent()
                # Exception should be caught and logged
                error_logs = [e for e in orchestrator.execution_log if e["status"] == "error"]
                self.assertEqual(len(error_logs), 1)
                self.assertEqual(error_logs[0]["agent_id"], "agent_b")
                self.assertIn("Unexpected error", error_logs[0]["error_message"])
                
                # Job should fail
                self.assertEqual(result["status"], "failed")
    
    def test_error_in_parallel_branches(self):
        """Test error propagation in parallel execution branches"""
        orchestrator = Orchestrator(
            self.job_id,
            self.parallel_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent_b to fail (one branch)
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_b":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": "Branch failure"
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # agent_a should succeed
                # agent_b should fail
                # agent_c and agent_d should be skipped
                success_logs = [e for e in orchestrator.execution_log if e["status"] == "success"]
                error_logs = [e for e in orchestrator.execution_log if e["status"] == "error"]
                skipped_logs = [e for e in orchestrator.execution_log if e["status"] == "skipped"]
                
                self.assertEqual(len(success_logs), 1)  # agent_a
                self.assertEqual(len(error_logs), 1)    # agent_b
                self.assertGreaterEqual(len(skipped_logs), 1)  # agent_c and/or agent_d
                
                # Job should fail
                self.assertEqual(result["status"], "failed")
    
    def test_error_message_details_preserved(self):
        """Test that error message details are preserved in execution log"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        error_message = "Database connection timeout: Could not connect to RDS instance after 30 seconds"
        
        # Mock agent_a to fail with detailed error
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_a":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": error_message
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
                "confidence": 0.9
            }
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent', side_effect=mock_invoke):
                def load_config(agent_id):
                    return {
                        "agent_id": agent_id,
                        "agent_name": agent_id.replace("_", " ").title(),
                        "agent_dependencies": []
                    }
                
                mock_load.side_effect = load_config
                
                result = orchestrator.execute({"text": "test"})
                
                # Verify error message is preserved
                error_logs = [e for e in orchestrator.execution_log if e["status"] == "error"]
                self.assertEqual(len(error_logs), 1)
                self.assertEqual(error_logs[0]["error_message"], error_message)
                
                # Verify error log structure
                error_log = error_logs[0]
                self.assertIn("agent_id", error_log)
                self.assertIn("agent_name", error_log)
                self.assertIn("status", error_log)
                self.assertIn("timestamp", error_log)
                self.assertIn("reasoning", error_log)
                self.assertIn("output", error_log)
                self.assertIn("error_message", error_log)
                
                # Output should be None for failed agents
                self.assertIsNone(error_log["output"])
    
    def test_skipped_agents_reference_failed_agent(self):
        """Test that skipped agents reference which agent caused the skip"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent_b to fail
        def mock_invoke(config, input_data):
            if config["agent_id"] == "agent_b":
                return {
                    "status": "error",
                    "output": None,
                    "reasoning": "",
                    "error_message": "Test failure"
                }
            return {
                "status": "success",
                "output": {"data": "test"},
                "reasoning": "Success",
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Find skipped agent log
                skipped_logs = [e for e in orchestrator.execution_log if e["status"] == "skipped"]
                self.assertEqual(len(skipped_logs), 1)
                
                # Verify reasoning references the failed agent
                skipped_log = skipped_logs[0]
                self.assertIn("agent_b", skipped_log["reasoning"])
                self.assertIn("failure", skipped_log["reasoning"].lower())


if __name__ == "__main__":
    unittest.main()
