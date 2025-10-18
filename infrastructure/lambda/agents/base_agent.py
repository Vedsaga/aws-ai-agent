"""
Base Agent Framework for Multi-Agent Orchestration System

This module provides the base class and utilities for all agents in the system.
All agents must inherit from BaseAgent and implement the execute method.
"""

import json
import os
import sys
import time
import boto3
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
from botocore.exceptions import ClientError

# Add realtime module to path for status publishing
sys.path.append(os.path.join(os.path.dirname(__file__), '../realtime'))
from status_utils import publish_tool_status, publish_agent_status

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class AgentError(Exception):
    """Custom exception for agent execution errors"""
    pass


class ToolInvocationError(Exception):
    """Custom exception for tool invocation failures"""
    pass


class OutputValidationError(Exception):
    """Custom exception for output schema validation failures"""
    pass


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides:
    - Standard input/output interface
    - Tool invocation framework
    - Output schema validation (max 5 keys)
    - Error handling and timeout management
    - Bedrock integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Agent configuration containing:
                - agent_name: Name of the agent
                - system_prompt: System prompt for LLM
                - tools: List of allowed tool names
                - output_schema: Expected output schema (max 5 keys)
        """
        self.config = config
        self.agent_name = config.get('agent_name', self.__class__.__name__)
        self.system_prompt = config.get('system_prompt', '')
        self.tools = config.get('tools', [])
        self.output_schema = config.get('output_schema', {})
        
        # Initialize AWS clients
        self.bedrock = boto3.client('bedrock-runtime')
        self.comprehend = boto3.client('comprehend')
        self.location = boto3.client('location')
        
        # Validate output schema
        if len(self.output_schema) > 5:
            raise OutputValidationError(
                f"Output schema cannot have more than 5 keys. Got {len(self.output_schema)}"
            )
    
    @abstractmethod
    def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        Args:
            raw_text: Raw input text from user
            parent_output: Optional output from parent agent (if dependency exists)
        
        Returns:
            Dict containing agent output with max 5 keys
        """
        pass
    
    def invoke_bedrock(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke AWS Bedrock with Claude 3 Sonnet model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        
        Returns:
            Model response as string
        """
        try:
            # Construct the request body for Claude 3
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Add system prompt if provided
            if self.system_prompt:
                request_body["system"] = self.system_prompt
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {str(e)}")
            raise ToolInvocationError(f"Bedrock API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock invocation: {str(e)}")
            raise ToolInvocationError(f"Bedrock invocation failed: {str(e)}")
    
    def invoke_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke a tool with access control check and status publishing.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Parameters for the tool
            job_id: Job identifier for status publishing (uses self.job_id if not provided)
            user_id: User identifier for status publishing (uses self.user_id if not provided)
            tenant_id: Tenant identifier for status publishing (uses self.tenant_id if not provided)
            reason: Reason for tool invocation
        
        Returns:
            Tool response
        """
        # Check if tool is allowed
        if tool_name not in self.tools:
            raise ToolInvocationError(
                f"Tool '{tool_name}' not authorized for agent '{self.agent_name}'"
            )
        
        logger.info(f"Agent '{self.agent_name}' invoking tool '{tool_name}'")
        
        # Use instance variables if not provided
        job_id = job_id or getattr(self, 'job_id', None)
        user_id = user_id or getattr(self, 'user_id', None)
        tenant_id = tenant_id or getattr(self, 'tenant_id', None)
        
        # Publish status: calling tool
        if job_id and user_id and tenant_id:
            publish_tool_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=self.agent_name,
                tool_name=tool_name,
                reason=reason or f"Invoking {tool_name}"
            )
        
        try:
            if tool_name == 'comprehend':
                return self._invoke_comprehend(parameters)
            elif tool_name == 'location':
                return self._invoke_location(parameters)
            elif tool_name == 'web_search':
                return self._invoke_web_search(parameters)
            else:
                raise ToolInvocationError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"Tool invocation failed for '{tool_name}': {str(e)}")
            raise ToolInvocationError(f"Tool '{tool_name}' failed: {str(e)}")
    
    def _invoke_comprehend(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke AWS Comprehend for entity extraction and sentiment analysis"""
        text = parameters.get('text', '')
        language = parameters.get('language', 'en')
        
        result = {}
        
        try:
            # Detect entities
            entities_response = self.comprehend.detect_entities(
                Text=text,
                LanguageCode=language
            )
            result['entities'] = entities_response.get('Entities', [])
            
            # Detect sentiment
            sentiment_response = self.comprehend.detect_sentiment(
                Text=text,
                LanguageCode=language
            )
            result['sentiment'] = sentiment_response.get('Sentiment', 'NEUTRAL')
            result['sentiment_scores'] = sentiment_response.get('SentimentScore', {})
            
            # Detect key phrases
            phrases_response = self.comprehend.detect_key_phrases(
                Text=text,
                LanguageCode=language
            )
            result['key_phrases'] = phrases_response.get('KeyPhrases', [])
            
            return result
        except ClientError as e:
            logger.error(f"Comprehend API error: {str(e)}")
            raise ToolInvocationError(f"Comprehend failed: {str(e)}")
    
    def _invoke_location(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Amazon Location Service for geocoding"""
        address = parameters.get('address', '')
        
        try:
            # Note: This requires a Place Index to be created in Location Service
            # For now, return a placeholder structure
            # In production, use: self.location.search_place_index_for_text()
            
            logger.warning("Location Service integration requires Place Index setup")
            return {
                'coordinates': None,
                'location': None,
                'error': 'Location Service not fully configured'
            }
        except ClientError as e:
            logger.error(f"Location Service API error: {str(e)}")
            raise ToolInvocationError(f"Location Service failed: {str(e)}")
    
    def _invoke_web_search(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke web search API (placeholder for external API)"""
        query = parameters.get('query', '')
        max_results = parameters.get('max_results', 5)
        
        # Placeholder - would integrate with actual search API
        logger.warning("Web search integration not implemented")
        return {
            'results': [],
            'error': 'Web search not configured'
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate agent output against schema.
        
        Args:
            output: Agent output to validate
        
        Returns:
            True if valid
        
        Raises:
            OutputValidationError if validation fails
        """
        # Check max 5 keys constraint
        if len(output) > 5:
            raise OutputValidationError(
                f"Output has {len(output)} keys, maximum is 5"
            )
        
        # Check all keys are in schema
        for key in output.keys():
            if key not in self.output_schema:
                raise OutputValidationError(
                    f"Key '{key}' not in output schema"
                )
        
        # Check required keys are present
        for key, schema in self.output_schema.items():
            if schema.get('required', False) and key not in output:
                raise OutputValidationError(
                    f"Required key '{key}' missing from output"
                )
        
        return True
    
    def format_output(
        self,
        output: Dict[str, Any],
        status: str = 'success',
        execution_time_ms: int = 0,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format agent output in standardized format.
        
        Args:
            output: Agent-specific output data
            status: Execution status ('success' or 'error')
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if status is 'error'
        
        Returns:
            Standardized output format
        """
        return {
            'agent_name': self.agent_name,
            'output': output,
            'status': status,
            'execution_time_ms': execution_time_ms,
            'error_message': error_message
        }
    
    def handle_execution(
        self,
        event: Dict[str, Any],
        context: Any
    ) -> Dict[str, Any]:
        """
        Main handler for Lambda execution with error handling and timeout management.
        
        Args:
            event: Lambda event containing:
                - job_id: Job identifier
                - tenant_id: Tenant identifier
                - raw_text: Raw input text
                - parent_output: Optional parent agent output
                - agent_config: Agent configuration
            context: Lambda context
        
        Returns:
            Standardized agent output
        """
        start_time = time.time()
        
        try:
            # Extract inputs
            raw_text = event.get('raw_text', '')
            parent_output = event.get('parent_output')
            job_id = event.get('job_id', 'unknown')
            tenant_id = event.get('tenant_id', 'unknown')
            user_id = event.get('user_id')
            
            logger.info(f"Agent '{self.agent_name}' starting execution for job {job_id}")
            
            # Store context for tool invocations
            self.job_id = job_id
            self.user_id = user_id
            self.tenant_id = tenant_id
            
            # Check remaining time
            remaining_time_ms = context.get_remaining_time_in_millis()
            if remaining_time_ms < 10000:  # Less than 10 seconds
                raise AgentError("Insufficient time remaining for execution")
            
            # Execute agent logic
            output = self.execute(raw_text, parent_output)
            
            # Validate output
            self.validate_output(output)
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Agent '{self.agent_name}' completed successfully in {execution_time_ms}ms"
            )
            
            # Publish completion status
            if user_id:
                publish_agent_status(
                    job_id=job_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    agent_name=self.agent_name,
                    status='complete',
                    message='Completed successfully',
                    execution_time_ms=execution_time_ms
                )
            
            return self.format_output(
                output=output,
                status='success',
                execution_time_ms=execution_time_ms
            )
            
        except OutputValidationError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Output validation failed: {str(e)}")
            
            # Publish error status
            user_id = event.get('user_id')
            if user_id:
                publish_agent_status(
                    job_id=event.get('job_id', 'unknown'),
                    user_id=user_id,
                    tenant_id=event.get('tenant_id', 'unknown'),
                    agent_name=self.agent_name,
                    status='error',
                    message=error_msg
                )
            
            return self.format_output(
                output={},
                status='error',
                execution_time_ms=execution_time_ms,
                error_message=error_msg
            )
        
        except ToolInvocationError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Tool error: {str(e)}"
            logger.error(f"Tool invocation failed: {str(e)}")
            
            # Publish error status
            user_id = event.get('user_id')
            if user_id:
                publish_agent_status(
                    job_id=event.get('job_id', 'unknown'),
                    user_id=user_id,
                    tenant_id=event.get('tenant_id', 'unknown'),
                    agent_name=self.agent_name,
                    status='error',
                    message=error_msg
                )
            
            return self.format_output(
                output={},
                status='error',
                execution_time_ms=execution_time_ms,
                error_message=error_msg
            )
        
        except AgentError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Agent execution failed: {error_msg}")
            
            # Publish error status
            user_id = event.get('user_id')
            if user_id:
                publish_agent_status(
                    job_id=event.get('job_id', 'unknown'),
                    user_id=user_id,
                    tenant_id=event.get('tenant_id', 'unknown'),
                    agent_name=self.agent_name,
                    status='error',
                    message=error_msg
                )
            
            return self.format_output(
                output={},
                status='error',
                execution_time_ms=execution_time_ms,
                error_message=error_msg
            )
        
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Publish error status
            user_id = event.get('user_id')
            if user_id:
                publish_agent_status(
                    job_id=event.get('job_id', 'unknown'),
                    user_id=user_id,
                    tenant_id=event.get('tenant_id', 'unknown'),
                    agent_name=self.agent_name,
                    status='error',
                    message=error_msg
                )
            
            return self.format_output(
                output={},
                status='error',
                execution_time_ms=execution_time_ms,
                error_message=f"Unexpected error: {str(e)}"
            )


def parse_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from text that may contain markdown or other formatting.
    
    Args:
        text: Text potentially containing JSON
    
    Returns:
        Parsed JSON object
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    import re
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in text
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError("No valid JSON found in text")
