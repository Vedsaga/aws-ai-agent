"""
Orchestrator Class - Executes Agent Playbooks with Caching

Implements agent output caching (memoization) to avoid redundant execution
of shared dependencies during job processing.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 8.1, 8.4
"""

import json
import os
import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

# Import RDS utilities
from rds_utils import get_agent_by_id, get_agents_by_ids

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client(
    "bedrock-runtime", region_name=os.environ.get("BEDROCK_REGION", "us-east-1")
)

# Model configurations
AGENT_MODEL_ID = os.environ.get('BEDROCK_AGENT_MODEL', 'amazon.nova-micro-v1:0')
ORCHESTRATOR_MODEL_ID = os.environ.get('BEDROCK_ORCHESTRATOR_MODEL', 'amazon.nova-pro-v1:0')


class Orchestrator:
    """
    Orchestrator class for executing agent playbooks with caching.
    
    Features:
    - Agent output caching (memoization) for shared dependencies
    - Execution logging with reasoning and outputs
    - Error propagation with fail-fast behavior
    - Topological sorting for DAG execution
    """
    
    def __init__(self, job_id: str, playbook: Dict[str, Any], domain_id: str, tenant_id: str, user_id: str = None):
        """
        Initialize orchestrator for a job.
        
        Args:
            job_id: Unique job identifier
            playbook: Agent execution graph with nodes and edges
            domain_id: Domain identifier
            tenant_id: Tenant identifier
            user_id: Optional user identifier for status updates
        """
        self.job_id = job_id
        self.playbook = playbook
        self.domain_id = domain_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        
        # Agent output cache - stores results by agent_id
        # Requirement 13.1: Cache agent outputs during job execution
        self.cache = {}
        
        # Execution log - tracks all agent executions
        # Requirement 14.1: Log each agent execution
        self.execution_log = []
        
        logger.info(f"Orchestrator initialized for job {job_id}, domain {domain_id}")
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute playbook agents in topological order with caching.
        
        Args:
            input_data: Initial input data (text, question, etc.)
        
        Returns:
            Dictionary with status, execution_log, and results
        
        Requirements:
        - 13.1: Cache agent outputs during execution
        - 13.2: Pass cached output to dependent agents
        - 13.3: Check cache before execution
        - 14.1: Log each agent execution
        """
        logger.info(f"Starting execution for job {self.job_id}")
        
        try:
            graph = self.playbook.get("agent_execution_graph", {})
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            
            # Build adjacency list and in-degree map for topological sort
            adj_list = {node: [] for node in nodes}
            in_degree = {node: 0 for node in nodes}
            
            for edge in edges:
                from_node = edge.get("from")
                to_node = edge.get("to")
                if from_node and to_node:
                    adj_list[from_node].append(to_node)
                    in_degree[to_node] += 1
            
            # Topological sort using Kahn's algorithm
            queue = [node for node in nodes if in_degree[node] == 0]
            execution_order = []
            
            while queue:
                node = queue.pop(0)
                execution_order.append(node)
                
                for neighbor in adj_list[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            # Verify all nodes were processed (no cycles)
            if len(execution_order) != len(nodes):
                raise ValueError("Circular dependency detected in playbook")
            
            logger.info(f"Execution order: {execution_order}")
            
            # Execute agents in topological order
            for agent_id in execution_order:
                try:
                    result = self.execute_agent(agent_id, input_data)
                    
                    if result.get("status") == "error":
                        # Requirement 15.1: Mark failed agents as 'error'
                        # Requirement 15.2: Mark dependent agents as 'skipped'
                        self._mark_remaining_as_skipped(execution_order, agent_id)
                        break
                        
                except Exception as e:
                    logger.error(f"Error executing agent {agent_id}: {str(e)}")
                    self._log_agent_error(agent_id, str(e))
                    self._mark_remaining_as_skipped(execution_order, agent_id)
                    break
            
            # Determine final status
            final_status = "completed"
            for log_entry in self.execution_log:
                if log_entry["status"] == "error":
                    final_status = "failed"
                    break
            
            # Requirement 13.4: Clear cache after job completion
            logger.info(f"Job {self.job_id} {final_status}. Clearing cache.")
            cache_stats = {
                "cached_agents": len([e for e in self.execution_log if e["status"] == "cached"]),
                "executed_agents": len([e for e in self.execution_log if e["status"] == "success"]),
                "total_agents": len(self.execution_log)
            }
            
            # Clear cache
            self.cache.clear()
            
            return {
                "status": final_status,
                "execution_log": self.execution_log,
                "cache_stats": cache_stats
            }
            
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {str(e)}")
            return {
                "status": "failed",
                "execution_log": self.execution_log,
                "error": str(e)
            }
    
    def execute_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single agent with caching.
        
        Args:
            agent_id: Agent identifier
            input_data: Input data for the agent
        
        Returns:
            Agent execution result
        
        Requirements:
        - 13.2: Pass cached output to dependent agents
        - 13.3: Check cache before executing
        - 13.5: Log cache hits in execution_log
        """
        # Requirement 13.3: Check cache first
        if agent_id in self.cache:
            logger.info(f"Cache hit for agent {agent_id}")
            self._log_agent_cached(agent_id)
            return self.cache[agent_id]
        
        logger.info(f"Executing agent {agent_id} (cache miss)")
        
        # Load agent configuration
        agent_config = self._load_agent_config(agent_id)
        if not agent_config:
            raise ValueError(f"Agent configuration not found: {agent_id}")
        
        # Requirement 13.2: Gather inputs from cached dependencies
        agent_input = self._gather_dependency_outputs(agent_config)
        agent_input.update(input_data)
        
        # Execute agent
        start_time = datetime.utcnow()
        result = self._invoke_agent(agent_config, agent_input)
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Requirement 13.1: Store agent output in cache
        self.cache[agent_id] = result
        logger.info(f"Cached output for agent {agent_id}")
        
        # Log execution based on result status
        # Requirement 14.1: Log each agent execution with status
        if result.get("status") == "error":
            self._log_agent_error(
                agent_id,
                result.get("error_message", "Unknown error")
            )
        else:
            self._log_agent_success(
                agent_id,
                agent_config.get("agent_name", agent_id),
                result,
                execution_time
            )
        
        return result
    
    def _gather_dependency_outputs(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect outputs from all dependency agents (from cache).
        
        Requirement 13.2: Multiple agents depend on same upstream agent,
        pass cached output to all dependent agents without re-execution.
        """
        inputs = {}
        dependencies = agent_config.get("agent_dependencies", [])
        
        for dep_id in dependencies:
            if dep_id in self.cache:
                # Use cached output
                inputs[f"{dep_id}_output"] = self.cache[dep_id].get("output", {})
                logger.debug(f"Using cached output from {dep_id}")
        
        return inputs
    
    def _load_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent configuration from RDS PostgreSQL.
        
        Requirement 8.1: Query agent_definitions table from RDS.
        """
        try:
            config = get_agent_by_id(self.tenant_id, agent_id)
            
            if not config:
                logger.error(f"Agent configuration not found: {agent_id}")
                return None
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading agent config for {agent_id}: {str(e)}")
            return None
    
    def _invoke_agent(self, agent_config: Dict[str, Any], agent_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke agent using Bedrock.
        
        Returns:
            Dictionary with status, output, reasoning, confidence
        """
        agent_id = agent_config["agent_id"]
        system_prompt = agent_config.get("system_prompt", "")
        
        try:
            # Build prompt
            user_prompt = f"Input data: {json.dumps(agent_input)}\n\n"
            user_prompt += "Please analyze the data and return your response as valid JSON."
            
            # Call Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.1,
                "messages": [
                    {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                ],
            }
            
            response = bedrock.invoke_model(
                modelId=AGENT_MODEL_ID,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )
            
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]
            
            # Parse JSON from response
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                output = json.loads(json_str)
                
                return {
                    "status": "success",
                    "output": output,
                    "reasoning": output.get("reasoning", "Agent processed the input"),
                    "confidence": output.get("confidence", 0.8)
                }
                
            except json.JSONDecodeError:
                logger.warning(f"Could not parse JSON from {agent_id}")
                return {
                    "status": "success",
                    "output": {"raw_response": content},
                    "reasoning": "Response could not be parsed as JSON",
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error invoking agent {agent_id}: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "reasoning": "",
                "error_message": str(e)
            }
    
    def _log_agent_success(
        self,
        agent_id: str,
        agent_name: str,
        result: Dict[str, Any],
        execution_time_ms: int
    ):
        """
        Log successful agent execution.
        
        Requirement 14.1: Log each agent execution with agent_id, agent_name,
        status, timestamp, reasoning, and output.
        """
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": result.get("reasoning", ""),
            "output": result.get("output", {}),
            "execution_time_ms": execution_time_ms
        })
        logger.info(f"Logged success for agent {agent_name}")
    
    def _log_agent_cached(self, agent_id: str):
        """
        Log cached agent output reuse.
        
        Requirement 13.5: Indicate whether output was computed or retrieved from cache.
        """
        cached_result = self.cache[agent_id]
        agent_name = agent_id.replace("_", " ").title()
        
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "cached",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": "Output retrieved from cache (not re-executed)",
            "output": cached_result.get("output", {}),
            "execution_time_ms": 0
        })
        logger.info(f"Logged cache hit for agent {agent_name}")
    
    def _log_agent_error(self, agent_id: str, error_message: str):
        """
        Log agent execution error.
        
        Requirement 15.1: Mark failed agents as 'error' in execution_log with error details.
        """
        agent_name = agent_id.replace("_", " ").title()
        
        self.execution_log.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "reasoning": "",
            "output": None,
            "error_message": error_message
        })
        logger.error(f"Logged error for agent {agent_name}: {error_message}")
    
    def _mark_remaining_as_skipped(self, execution_order: List[str], failed_agent_id: str):
        """
        Mark all agents after failed agent as skipped.
        
        Requirement 15.2: Automatically mark dependent agents as 'skipped'
        when an agent fails.
        """
        skip_remaining = False
        
        for agent_id in execution_order:
            if agent_id == failed_agent_id:
                skip_remaining = True
                continue
            
            if skip_remaining:
                agent_name = agent_id.replace("_", " ").title()
                
                self.execution_log.append({
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "status": "skipped",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reasoning": f"Skipped due to failure of {failed_agent_id}",
                    "output": None
                })
                logger.info(f"Marked agent {agent_name} as skipped")
