"""
Unit tests for Orchestrator caching functionality

Tests Requirements:
- 13.1: Cache agent outputs during job execution
- 13.2: Pass cached output to dependent agents
- 13.3: Check cache before execution
- 13.4: Clear cache after job completion
- 13.5: Log cache hits in execution_log
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


class TestOrchestratorCaching(unittest.TestCase):
    """Test agent output caching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.job_id = "test-job-123"
        self.domain_id = "test-domain"
        self.tenant_id = "test-tenant"
        self.user_id = "test-user"
        
        # Simple linear playbook: agent_a -> agent_b -> agent_c
        self.linear_playbook = {
            "agent_execution_graph": {
                "nodes": ["agent_a", "agent_b", "agent_c"],
                "edges": [
                    {"from": "agent_a", "to": "agent_b"},
                    {"from": "agent_b", "to": "agent_c"}
                ]
            }
        }
        
        # Diamond playbook: agent_a -> agent_b, agent_c -> agent_d
        # Both agent_b and agent_c depend on agent_a
        self.diamond_playbook = {
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
    
    def test_cache_initialization(self):
        """Test that cache is initialized empty"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Requirement 13.1: Cache dictionary initialized
        self.assertIsInstance(orchestrator.cache, dict)
        self.assertEqual(len(orchestrator.cache), 0)
    
    def test_cache_stores_agent_output(self):
        """Test that agent outputs are stored in cache"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Mock agent execution
        mock_result = {
            "status": "success",
            "output": {"data": "test"},
            "reasoning": "Test reasoning",
            "confidence": 0.9
        }
        
        with patch.object(orchestrator, '_load_agent_config') as mock_load:
            with patch.object(orchestrator, '_invoke_agent', return_value=mock_result):
                mock_load.return_value = {
                    "agent_id": "agent_a",
                    "agent_name": "Agent A",
                    "agent_dependencies": []
                }
                
                result = orchestrator.execute_agent("agent_a", {"text": "test"})
                
                # Requirement 13.1: Agent output stored in cache
                self.assertIn("agent_a", orchestrator.cache)
                self.assertEqual(orchestrator.cache["agent_a"], mock_result)
    
    def test_cache_hit_avoids_reexecution(self):
        """Test that cached agents are not re-executed"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Pre-populate cache
        cached_result = {
            "status": "success",
            "output": {"data": "cached"},
            "reasoning": "Cached reasoning",
            "confidence": 0.95
        }
        orchestrator.cache["agent_a"] = cached_result
        
        with patch.object(orchestrator, '_invoke_agent') as mock_invoke:
            result = orchestrator.execute_agent("agent_a", {"text": "test"})
            
            # Requirement 13.3: Cache checked before execution
            # Agent should not be invoked if cached
            mock_invoke.assert_not_called()
            self.assertEqual(result, cached_result)
    
    def test_cache_hit_logged(self):
        """Test that cache hits are logged in execution_log"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Pre-populate cache
        cached_result = {
            "status": "success",
            "output": {"data": "cached"},
            "reasoning": "Original reasoning",
            "confidence": 0.95
        }
        orchestrator.cache["agent_a"] = cached_result
        
        result = orchestrator.execute_agent("agent_a", {"text": "test"})
        
        # Requirement 13.5: Log cache hits in execution_log
        self.assertEqual(len(orchestrator.execution_log), 1)
        log_entry = orchestrator.execution_log[0]
        
        self.assertEqual(log_entry["agent_id"], "agent_a")
        self.assertEqual(log_entry["status"], "cached")
        self.assertIn("cache", log_entry["reasoning"].lower())
        self.assertEqual(log_entry["execution_time_ms"], 0)
    
    def test_shared_dependency_uses_cache(self):
        """Test that shared dependencies use cached output (diamond pattern)"""
        orchestrator = Orchestrator(
            self.job_id,
            self.diamond_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        invoke_count = {"count": 0}
        
        def mock_invoke(config, input_data):
            invoke_count["count"] += 1
            return {
                "status": "success",
                "output": {"agent": config["agent_id"], "count": invoke_count["count"]},
                "reasoning": f"Executed {config['agent_id']}",
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
                
                # Requirement 13.2: agent_a should be executed once, then cached
                # agent_b and agent_c should both use cached output from agent_a
                
                # agent_a executed once
                # agent_b executed once (uses cached agent_a)
                # agent_c executed once (uses cached agent_a)
                # agent_d executed once (uses cached agent_b and agent_c)
                # Total: 4 invocations (one per agent)
                self.assertEqual(invoke_count["count"], 4)
                
                # Check execution log for cache hits
                cache_hits = [e for e in orchestrator.execution_log if e["status"] == "cached"]
                # agent_a is used by both agent_b and agent_c, but only logged once per execution
                # No cache hits in this scenario since each agent executes once
                # But agent_a's output is reused from cache by agent_b and agent_c
                
                # Requirement 13.4: Cache is cleared after job completion
                self.assertEqual(len(orchestrator.cache), 0)
                
                # Verify all agents were executed successfully
                self.assertEqual(result["status"], "completed")
                self.assertEqual(len(orchestrator.execution_log), 4)
    
    def test_cache_cleared_after_completion(self):
        """Test that cache is cleared after job completion"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Requirement 13.4: Cache cleared after job completion
                self.assertEqual(len(orchestrator.cache), 0)
    
    def test_cache_stats_in_result(self):
        """Test that cache statistics are included in result"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
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
                
                result = orchestrator.execute({"text": "test"})
                
                # Check cache stats
                self.assertIn("cache_stats", result)
                self.assertIn("cached_agents", result["cache_stats"])
                self.assertIn("executed_agents", result["cache_stats"])
                self.assertIn("total_agents", result["cache_stats"])
    
    def test_dependency_outputs_gathered_from_cache(self):
        """Test that dependency outputs are gathered from cache"""
        orchestrator = Orchestrator(
            self.job_id,
            self.linear_playbook,
            self.domain_id,
            self.tenant_id
        )
        
        # Pre-populate cache with dependency output
        orchestrator.cache["agent_a"] = {
            "status": "success",
            "output": {"location": "New York"},
            "reasoning": "Found location",
            "confidence": 0.9
        }
        
        agent_config = {
            "agent_id": "agent_b",
            "agent_name": "Agent B",
            "agent_dependencies": ["agent_a"]
        }
        
        # Requirement 13.2: Gather inputs from cached dependencies
        inputs = orchestrator._gather_dependency_outputs(agent_config)
        
        self.assertIn("agent_a_output", inputs)
        self.assertEqual(inputs["agent_a_output"], {"location": "New York"})


if __name__ == "__main__":
    unittest.main()
