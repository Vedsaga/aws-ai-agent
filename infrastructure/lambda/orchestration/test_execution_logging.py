"""
Unit tests for Orchestrator execution logging functionality

Tests Requirements:
- 14.1: Log each agent execution with agent_id, agent_name, status, timestamp, reasoning, and output
- 14.2: Return execution_log array with all agent steps
- 14.3: Capture agent reasoning text from LLM response
- 14.4: Store intermediate outputs for debugging
- 14.5: Order log entries chronologically
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import time

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


class TestExecutionLogging(unittest.TestCase):
    """Test execution logging functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.job_id = "test-job-456"
        self.domain_id = "test-domain"
        self.tenant_id = "test-tenant"
        self.user_id = "test-user"
        
        # Linear playbook for testing
        self.playbook = {
            "agent_execution_graph": {
                "nodes": ["agent_a", "agent_b", "agent_c"],
                "edges": [
                    {"from": "agent_a", "to": "agent_b"},
                    {"from": "agent_b", "to": "agent_c"}
                ]
            }
        }
    
    def test_execution_log_initialized(self):
        """Test that execution_log is initialized as empty array"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Requirement 14.1: execution_log array initialized
        self.assertIsInstance(orchestrator.execution_log, list)
        self.assertEqual(len(orchestrator.execution_log), 0)
    
    def test_log_contains_required_fields(self):
        """Test that log entries contain all required fields"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent execution
        mock_result = {
            "status": "success",
            "output": {"location": "New York", "confidence": 0.9},
            "reasoning": "Extracted location from text using pattern matching",
            "confidence": 0.9
        }
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent', return_value=mock_result):
                mock_load.return_value = {
                    "agent_id": "geo_agent",
                    "agent_name": "Geo Locator",
                    "agent_dependencies": []
                }
                
                orchestrator.execute_agent("geo_agent", {"text": "Report from New York"})
                
                # Requirement 14.1: Log contains agent_id, agent_name, status, timestamp, reasoning, output
                self.assertEqual(len(orchestrator.execution_log), 1)
                log_entry = orchestrator.execution_log[0]
                
                self.assertIn("agent_id", log_entry)
                self.assertIn("agent_name", log_entry)
                self.assertIn("status", log_entry)
                self.assertIn("timestamp", log_entry)
                self.assertIn("reasoning", log_entry)
                self.assertIn("output", log_entry)
                
                self.assertEqual(log_entry["agent_id"], "geo_agent")
                self.assertEqual(log_entry["agent_name"], "Geo Locator")
                self.assertEqual(log_entry["status"], "success")
    
    def test_reasoning_captured_from_llm(self):
        """Test that agent reasoning text is captured from LLM response"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock LLM response with reasoning
        reasoning_text = "I analyzed the text and identified the location as New York based on explicit mention"
        mock_result = {
            "status": "success",
            "output": {"location": "New York"},
            "reasoning": reasoning_text,
            "confidence": 0.95
        }
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent', return_value=mock_result):
                mock_load.return_value = {
                    "agent_id": "geo_agent",
                    "agent_name": "Geo Locator",
                    "agent_dependencies": []
                }
                
                orchestrator.execute_agent("geo_agent", {"text": "New York"})
                
                # Requirement 14.3: Capture agent reasoning text from LLM response
                log_entry = orchestrator.execution_log[0]
                self.assertEqual(log_entry["reasoning"], reasoning_text)
    
    def test_intermediate_outputs_stored(self):
        """Test that intermediate outputs are stored for debugging"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent with complex output
        complex_output = {
            "location": {
                "address": "123 Main St",
                "city": "New York",
                "coordinates": {"lat": 40.7128, "lon": -74.0060}
            },
            "confidence": 0.9,
            "metadata": {
                "source": "geocoding_api",
                "alternatives": ["123 Main Street", "Main St 123"]
            }
        }
        
        mock_result = {
            "status": "success",
            "output": complex_output,
            "reasoning": "Geocoded address",
            "confidence": 0.9
        }
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent', return_value=mock_result):
                mock_load.return_value = {
                    "agent_id": "geo_agent",
                    "agent_name": "Geo Locator",
                    "agent_dependencies": []
                }
                
                orchestrator.execute_agent("geo_agent", {"text": "123 Main St"})
                
                # Requirement 14.4: Store intermediate outputs for debugging
                log_entry = orchestrator.execution_log[0]
                self.assertEqual(log_entry["output"], complex_output)
                self.assertIn("metadata", log_entry["output"])
    
    def test_log_entries_chronological_order(self):
        """Test that log entries are ordered chronologically"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        execution_times = []
        
        def mock_invoke(config, input_data):
            # Add small delay to ensure different timestamps
            time.sleep(0.01)
            timestamp = datetime.utcnow().isoformat()
            execution_times.append(timestamp)
            return {
                "status": "success",
                "output": {"agent": config["agent_id"]},
                "reasoning": f"Executed {config['agent_id']}",
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
                
                # Requirement 14.5: Order log entries chronologically
                self.assertEqual(len(orchestrator.execution_log), 3)
                
                # Verify timestamps are in ascending order
                timestamps = [entry["timestamp"] for entry in orchestrator.execution_log]
                self.assertEqual(timestamps, sorted(timestamps))
                
                # Verify execution order matches dependency graph
                agent_ids = [entry["agent_id"] for entry in orchestrator.execution_log]
                self.assertEqual(agent_ids, ["agent_a", "agent_b", "agent_c"])
    
    def test_execution_log_returned_in_result(self):
        """Test that execution_log is returned in the result"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent') as mock_invoke:
                mock_load.return_value = {
                    "agent_id": "agent_a",
                    "agent_name": "Agent A",
                    "agent_dependencies": []
                }
                mock_invoke.return_value = {
                    "status": "success",
                    "output": {"data": "test"},
                    "reasoning": "Test reasoning",
                    "confidence": 0.9
                }
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 14.2: Return execution_log array with all agent steps
                self.assertIn("execution_log", result)
                self.assertIsInstance(result["execution_log"], list)
                self.assertGreater(len(result["execution_log"]), 0)
    
    def test_error_logged_with_details(self):
        """Test that errors are logged with error details"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        error_message = "LLM API timeout after 30 seconds"
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent') as mock_invoke:
                mock_load.return_value = {
                    "agent_id": "agent_a",
                    "agent_name": "Agent A",
                    "agent_dependencies": []
                }
                
                # First agent succeeds
                mock_invoke.side_effect = [
                    {
                        "status": "success",
                        "output": {"data": "test"},
                        "reasoning": "Success",
                        "confidence": 0.9
                    },
                    # Second agent fails
                    {
                        "status": "error",
                        "output": None,
                        "reasoning": "",
                        "error_message": error_message
                    }
                ]
                
                result = orchestrator.execute({"text": "test"})
                
                # Find error log entry
                error_logs = [e for e in orchestrator.execution_log if e["status"] == "error"]
                self.assertGreater(len(error_logs), 0)
                
                error_log = error_logs[0]
                self.assertIn("error_message", error_log)
                self.assertEqual(error_log["error_message"], error_message)
    
    def test_skipped_agents_logged(self):
        """Test that skipped agents are logged when upstream fails"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent') as mock_invoke:
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
                
                # agent_a succeeds, agent_b fails, agent_c should be skipped
                mock_invoke.side_effect = [
                    {
                        "status": "success",
                        "output": {"data": "a"},
                        "reasoning": "Success A",
                        "confidence": 0.9
                    },
                    {
                        "status": "error",
                        "output": None,
                        "reasoning": "",
                        "error_message": "Agent B failed"
                    }
                ]
                
                result = orchestrator.execute({"text": "test"})
                
                # Verify execution log contains all three agents
                self.assertEqual(len(orchestrator.execution_log), 3)
                
                # Verify statuses
                statuses = [e["status"] for e in orchestrator.execution_log]
                self.assertEqual(statuses, ["success", "error", "skipped"])
                
                # Verify skipped agent has reasoning
                skipped_log = orchestrator.execution_log[2]
                self.assertEqual(skipped_log["agent_id"], "agent_c")
                self.assertIn("skipped", skipped_log["reasoning"].lower())
    
    def test_execution_time_tracked(self):
        """Test that execution time is tracked for each agent"""
        orchestrator = Orchestrator(
            self.job_id,
            self.playbook,
            self.domain_id,
            self.tenant_id
        )
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent') as mock_invoke:
                mock_load.return_value = {
                    "agent_id": "agent_a",
                    "agent_name": "Agent A",
                    "agent_dependencies": []
                }
                mock_invoke.return_value = {
                    "status": "success",
                    "output": {"data": "test"},
                    "reasoning": "Test",
                    "confidence": 0.9
                }
                
                orchestrator.execute_agent("agent_a", {"text": "test"})
                
                # Verify execution time is logged
                log_entry = orchestrator.execution_log[0]
                self.assertIn("execution_time_ms", log_entry)
                self.assertIsInstance(log_entry["execution_time_ms"], int)
                self.assertGreaterEqual(log_entry["execution_time_ms"], 0)


if __name__ == "__main__":
    unittest.main()
