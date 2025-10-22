"""
Orchestrator Handler - Executes Agent Pipeline
Processes reports/queries through configured agent chains
"""

import json
import os
import boto3
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal
import traceback
import re
import sys

# Add realtime module to path (in Lambda, realtime/ is at same level)
realtime_path = os.path.join(os.path.dirname(__file__), "realtime")
if os.path.exists(realtime_path):
    sys.path.insert(0, os.path.dirname(__file__))

try:
    from realtime.status_utils import publish_orchestrator_status, publish_agent_status
    print("Status utils loaded successfully")
except ImportError as e:
    print(f"Warning: status_utils not available: {e}")

    def publish_orchestrator_status(*args, **kwargs):
        return False

    def publish_agent_status(*args, **kwargs):
        return False

# Import RDS utilities for data retrieval and agent/domain loading
try:
    from rds_utils import (
        get_incidents_for_query, 
        extract_incident_ids,
        get_domain_by_id,
        get_playbook,
        get_agents_by_ids
    )
    print("RDS utils loaded successfully")
except ImportError as e:
    print(f"Warning: rds_utils not available: {e}")
    
    def get_incidents_for_query(*args, **kwargs):
        return []
    
    def extract_incident_ids(*args, **kwargs):
        return []
    
    def get_domain_by_id(*args, **kwargs):
        return None
    
    def get_playbook(*args, **kwargs):
        return None
    
    def get_agents_by_ids(*args, **kwargs):
        return {}


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
bedrock = boto3.client(
    "bedrock-runtime", region_name=os.environ.get("BEDROCK_REGION", "us-east-1")
)
location_client = boto3.client("location", region_name="us-east-1")

# Environment variables
CONFIGURATIONS_TABLE = os.environ.get(
    "CONFIGURATIONS_TABLE", "MultiAgentOrchestration-dev-Data-Configurations"
)
INCIDENTS_TABLE = os.environ.get(
    "INCIDENTS_TABLE", "MultiAgentOrchestration-dev-Incidents"
)
QUERY_JOBS_TABLE = os.environ.get(
    "QUERY_JOBS_TABLE", "MultiAgentOrchestration-dev-QueryJobs"
)

# Model configurations - use lighter models for individual agents, complex for orchestration
# Load from environment variables with fallbacks
AGENT_MODEL_ID = os.environ.get('BEDROCK_AGENT_MODEL', 'amazon.nova-micro-v1:0')
ORCHESTRATOR_MODEL_ID = os.environ.get('BEDROCK_ORCHESTRATOR_MODEL', 'amazon.nova-pro-v1:0')
GEO_AGENT_USE_LOCATION_SERVICE = True  # Use Amazon Location Service for geocoding

# Initialize tables
config_table = dynamodb.Table(CONFIGURATIONS_TABLE)


def convert_floats_to_decimal(obj):
    """Convert all float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    return obj


def geocode_with_amazon_location(address_text: str) -> Optional[Dict[str, Any]]:
    """
    Use Amazon Location Service to geocode an address
    Returns: {"address": str, "lat": float, "lon": float, "confidence": float}
    """
    try:
        # Extract location entities from text
        location_query = address_text.strip()

        # Call Amazon Location Service SearchPlaceIndexForText
        response = location_client.search_place_index_for_text(
            IndexName="MultiAgentGeoIndex",  # You need to create this index
            Text=location_query,
            MaxResults=5,
        )

        results = response.get("Results", [])

        if not results:
            print(f"No geocoding results for: {location_query}")
            return None

        # Evaluate results for ambiguity
        if len(results) == 1 and results[0].get("Relevance", 0) > 0.9:
            # High confidence single result
            place = results[0]["Place"]
            geometry = place.get("Geometry", {}).get("Point", [])

            return {
                "address": place.get("Label", location_query),
                "lat": geometry[1] if len(geometry) > 1 else None,
                "lon": geometry[0] if len(geometry) > 0 else None,
                "city": place.get("Municipality"),
                "country": place.get("Country"),
                "confidence": results[0].get("Relevance", 0.5),
                "all_results": None,  # Single result, no ambiguity
            }
        elif len(results) > 1:
            # Multiple results - return for clarification
            return {
                "address": location_query,
                "lat": None,
                "lon": None,
                "confidence": 0.3,  # Low confidence due to ambiguity
                "all_results": [
                    {
                        "label": r["Place"].get("Label"),
                        "lat": r["Place"]["Geometry"]["Point"][1],
                        "lon": r["Place"]["Geometry"]["Point"][0],
                        "relevance": r.get("Relevance", 0),
                    }
                    for r in results[:3]
                ],
            }
        else:
            # Low confidence single result
            place = results[0]["Place"]
            geometry = place.get("Geometry", {}).get("Point", [])

            return {
                "address": place.get("Label", location_query),
                "lat": geometry[1] if len(geometry) > 1 else None,
                "lon": geometry[0] if len(geometry) > 0 else None,
                "confidence": results[0].get("Relevance", 0.5),
            }

    except Exception as e:
        print(f"Amazon Location Service error: {e}")
        return None


try:
    incidents_table = dynamodb.Table(INCIDENTS_TABLE)
except Exception as e:
    print(f"Warning: Could not initialize incidents table: {e}")
    incidents_table = None

try:
    query_jobs_table = dynamodb.Table(QUERY_JOBS_TABLE)
except Exception as e:
    print(f"Warning: Could not initialize query jobs table: {e}")
    query_jobs_table = None


def handler(event, context):
    """
    Main orchestrator handler - triggered by SQS or direct invocation
    """
    print(f"Orchestrator invoked: {json.dumps(event, default=str)}")

    try:
        # Parse event (could be from SQS, direct invoke, or EventBridge)
        if "Records" in event:
            # SQS message
            for record in event["Records"]:
                body = json.loads(record["body"])
                process_job(body)
        else:
            # Direct invocation
            process_job(event)

        return {"statusCode": 200, "body": "Orchestration complete"}

    except Exception as e:
        print(f"Orchestrator error: {e}")
        print(traceback.format_exc())
        return {"statusCode": 500, "body": str(e)}


def process_job(job_data: Dict[str, Any]):
    """
    Process a single job through the agent pipeline
    """
    job_id = job_data.get("job_id")
    job_type = job_data.get("job_type", "ingest")  # ingest or query
    domain_id = job_data.get("domain_id")
    text = job_data.get("text") or job_data.get("question")
    tenant_id = job_data.get("tenant_id", "default-tenant")
    user_id = job_data.get("user_id", "demo-user")
    query_id = job_data.get("query_id")  # For query jobs
    incident_id = job_data.get("incident_id")  # For ingestion jobs

    print(f"Processing job: {job_id}, type: {job_type}, domain: {domain_id}")

    try:
        # Publish orchestration start status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="loading_agents",
            message=f"Loading agent configuration for domain: {domain_id}",
        )
        # Step 1: Load domain from RDS
        print(f"Loading domain from RDS: {domain_id}, tenant: {tenant_id}")
        domain = get_domain_by_id(tenant_id, domain_id)
        
        if not domain:
            print(f"Domain not found in RDS: {domain_id}, using fallback")
            # Use fallback for backward compatibility
            domain_config = get_default_domain_config(job_type)
            agent_ids = domain_config.get("ingest_agent_ids" if job_type == "ingest" else "query_agent_ids", [])
        else:
            # Step 2: Get playbook from domain based on job type
            playbook_type_map = {
                'ingest': 'ingestion',
                'query': 'query',
                'management': 'management'
            }
            playbook_type = playbook_type_map.get(job_type, 'query')
            
            print(f"Loading {playbook_type} playbook for domain: {domain_id}")
            playbook = get_playbook(tenant_id, domain_id, playbook_type)
            
            if not playbook:
                print(f"Playbook not found, using fallback")
                domain_config = get_default_domain_config(job_type)
                agent_ids = domain_config.get("ingest_agent_ids" if job_type == "ingest" else "query_agent_ids", [])
            else:
                # Extract agent IDs from playbook
                agent_execution_graph = playbook.get('agent_execution_graph', {})
                agent_ids = agent_execution_graph.get('nodes', [])
                print(f"Loaded agent IDs from playbook: {agent_ids}")

        print(f"Agent pipeline: {agent_ids}")

        # Publish agent pipeline loaded status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="agents_loaded",
            message=f"Agent pipeline loaded: {', '.join(agent_ids)}",
            metadata={"agent_count": len(agent_ids), "agents": agent_ids},
        )

        # Step 3: Load agent configurations from RDS
        print(f"Loading {len(agent_ids)} agents from RDS")
        agents_dict = get_agents_by_ids(tenant_id, agent_ids)
        
        # Convert dict to list and add fallback for missing agents
        agents = []
        for agent_id in agent_ids:
            if agent_id in agents_dict:
                agent_config = agents_dict[agent_id]
                # Ensure agent_id is set
                agent_config['agent_id'] = agent_id
                agents.append(agent_config)
                print(f"Loaded agent from RDS: {agent_id}")
            else:
                # Fallback: create basic config for missing agents
                print(f"Agent not found in RDS, using fallback: {agent_id}")
                agent_config = create_fallback_agent_config(agent_id)
                agents.append(agent_config)

        # Step 3.5: For query jobs, fetch relevant incidents from database
        incidents_data = []
        incident_references = []
        if job_type in ["query", "management"]:
            print(f"Fetching incidents for query analysis from domain: {domain_id}")
            incidents_data = get_incidents_for_query(
                tenant_id=tenant_id,
                domain_id=domain_id,
                limit=20  # Fetch last 20 incidents for analysis
            )
            incident_references = extract_incident_ids(incidents_data)
            print(f"Retrieved {len(incidents_data)} incidents for analysis")
            print(f"Incident references: {incident_references[:5]}...")  # Log first 5

        # Step 4: Build execution plan (handle dependencies)
        execution_plan = build_execution_plan(agents)
        print(f"Execution plan: {[a['agent_id'] for a in execution_plan]}")

        # Step 5: Execute agents in order
        results = {}
        all_incident_references = set()  # Collect all incident references from agents
        
        for idx, agent in enumerate(execution_plan):
            agent_id = agent["agent_id"]

            # Publish agent invocation status
            publish_agent_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=agent_id,
                status="invoking",
                message=f"Executing agent {idx + 1}/{len(execution_plan)}",
            )

            # Get parent output if agent has dependency
            parent_output = None
            if agent.get("dependency_parent"):
                parent_output = results.get(agent["dependency_parent"])

            # Execute agent with incident data for query jobs
            start_time = datetime.utcnow()
            if job_type in ["query", "management"] and incidents_data:
                # Pass incidents as context for query agents
                result = execute_agent(agent, text, parent_output, incidents=incidents_data)
                
                # Collect incident references from this agent
                if "incident_references" in result:
                    all_incident_references.update(result["incident_references"])
            else:
                result = execute_agent(agent, text, parent_output)
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            results[agent_id] = result
            print(
                f"Agent {agent_id} executed: confidence={result.get('confidence', 'N/A')}"
            )

            # Publish agent completion status
            publish_agent_status(
                job_id=job_id,
                user_id=user_id,
                tenant_id=tenant_id,
                agent_name=agent_id,
                status="complete",
                message=f"Agent completed with confidence: {result.get('confidence', 'N/A')}",
                execution_time_ms=execution_time,
            )

        # Step 6: Verify outputs (check confidence scores)
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="verifying",
            message="Verifying agent outputs and confidence scores",
        )

        verified_results = verify_outputs(results)

        # Step 7: Generate summary
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="synthesizing",
            message="Generating summary from agent results",
        )

        summary = generate_summary(verified_results, job_type)

        # Step 8: Save results
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="saving",
            message="Saving results to database",
        )

        # Use collected references from agents, fallback to pre-fetched list
        final_references = list(all_incident_references) if all_incident_references else incident_references
        print(f"Final incident references: {len(final_references)} incidents")
        
        save_results(
            job_id, job_type, domain_id, tenant_id, text, verified_results, summary, final_references, query_id, incident_id
        )

        # Publish completion status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="complete",
            message="Job completed successfully",
            metadata={"summary": summary, "agent_count": len(results)},
        )

        print(f"Job {job_id} completed successfully")
        return {"status": "completed", "job_id": job_id, "summary": summary}

    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        print(traceback.format_exc())

        # Publish error status
        publish_orchestrator_status(
            job_id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status="error",
            message=f"Job failed: {str(e)}",
            metadata={"error": str(e)},
        )

        update_job_status(job_id, "failed", str(e))
        return {"status": "failed", "job_id": job_id, "error": str(e)}


# Removed: load_domain_config() - now using get_domain_by_id() from rds_utils


def get_default_domain_config(job_type: str) -> Dict[str, Any]:
    """Return default agent configuration with CORRECT builtin agent IDs"""
    if job_type == "ingest":
        return {
            "domain_id": "default",
            "ingest_agent_ids": [
                "builtin-ingestion-geo",
                "builtin-ingestion-temporal",
                "builtin-ingestion-entity"
            ],
        }
    elif job_type == "management":
        return {
            "domain_id": "default",
            "query_agent_ids": [
                "builtin-management-task-assigner",
                "builtin-management-status-updater",
                "builtin-management-task-details-editor"
            ],
        }
    else:  # query
        return {
            "domain_id": "default",
            "query_agent_ids": [
                "builtin-query-who",
                "builtin-query-what",
                "builtin-query-where",
                "builtin-query-when"
            ],
        }


# Removed: load_agent_config() - now using get_agents_by_ids() from rds_utils


def create_fallback_agent_config(agent_id: str) -> Dict[str, Any]:
    """Create fallback agent configuration"""
    prompts = {
        "geo_agent": """Extract location information from the text and provide exact coordinates.
CRITICAL: You MUST provide latitude and longitude for mapping. These are REQUIRED fields.

Instructions:
1. Extract the address/location text from the input
2. If coordinates are explicitly mentioned, use them
3. If only an address/place name is given, you MUST estimate reasonable lat/lon coordinates based on your geographic knowledge
4. Use your knowledge of world geography to provide accurate coordinates for known places
5. If you cannot determine exact coordinates, provide approximate center coordinates for the mentioned area

Return JSON format:
{
  "location": {
    "address": "street name or place",
    "lat": number (REQUIRED - use decimal degrees, e.g., 40.7128),
    "lon": number (REQUIRED - use decimal degrees, e.g., -74.0060),
    "city": "optional city name",
    "country": "optional country"
  },
  "confidence": number (1-5, where 5 is highest)
}

Examples:
- Input: "Main Street, New York" → {"location": {"address": "Main Street", "lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "USA"}, "confidence": 4}
- Input: "Central Park" → {"location": {"address": "Central Park", "lat": 40.7829, "lon": -73.9654, "city": "New York"}, "confidence": 5}
- Input: "Washington Avenue near school" → {"location": {"address": "Washington Avenue", "lat": 38.8951, "lon": -77.0364}, "confidence": 3}

NEVER return null for lat/lon. Always provide numeric coordinates.""",
        "temporal_agent": """Extract time/date information from the text.
Return JSON with:
{
  "timestamp": "ISO 8601 date string (e.g., 2025-10-20T10:00:00Z)",
  "duration": "human readable duration (e.g., '3 days', '2 weeks')",
  "relative_time": "when it occurred relative to now (e.g., 'yesterday', 'last week')",
  "confidence": number (1-5)
}""",
        "category_agent": """Categorize the complaint and extract details.
Return JSON with:
{
  "category": "one of: pothole, streetlight, graffiti, garbage, water_leak, noise, other",
  "subcategory": "more specific type",
  "severity": "low, medium, high, critical",
  "details": "brief description",
  "confidence": number (1-5)
}""",
        "what_agent": """Analyze the 'what' aspects of the question by examining the data provided.
Return JSON with:
{
  "answer": "concise summary answering the question",
  "key_points": ["list of important findings"],
  "data_summary": "brief overview of the data analyzed",
  "confidence": number (1-5)
}""",
        "where_agent": """Analyze the 'where' aspects by identifying locations in the data.
Return JSON with:
{
  "locations": ["list of location names found"],
  "geographic_insights": "summary of geographic patterns",
  "hotspots": ["areas with most reports"],
  "confidence": number (1-5)
}""",
        "when_agent": """Analyze the 'when' aspects by examining temporal patterns.
Return JSON with:
{
  "time_periods": ["list of relevant time ranges"],
  "temporal_patterns": "description of timing trends",
  "recency": "how recent the events are",
  "confidence": number (1-5)
}""",
    }

    return {
        "agent_id": agent_id,
        "agent_name": agent_id.replace("_", " ").title(),
        "system_prompt": prompts.get(
            agent_id, "Extract relevant information from the text."
        ),
        "tools": ["bedrock"],
        "is_builtin": True,
    }


def build_execution_plan(agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build execution plan respecting dependencies
    Returns agents in execution order
    """
    # Separate agents with and without dependencies
    independent = [a for a in agents if not a.get("dependency_parent")]
    dependent = [a for a in agents if a.get("dependency_parent")]

    # Execute independent agents first, then dependent ones
    execution_plan = independent + dependent

    return execution_plan


def execute_agent(
    agent: Dict[str, Any], text: str, parent_output: Optional[Dict] = None, incidents: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Execute a single agent using AWS Bedrock
    
    Args:
        agent: Agent configuration from RDS (agent_definitions table)
        text: User question or text to analyze
        parent_output: Output from parent agent (if any)
        incidents: List of incident data for query agents to analyze
    """
    agent_id = agent.get("agent_id")
    
    # Get system prompt from RDS agent config
    system_prompt = agent.get("system_prompt", "Extract relevant information from the text.")
    
    # Log agent execution
    print(f"Executing agent: {agent_id}")
    print(f"Agent name: {agent.get('agent_name', 'Unknown')}")
    print(f"Agent class: {agent.get('agent_class', 'Unknown')}")

    try:
        # Build prompt
        user_prompt = f"Question: {text}\n\n"

        if parent_output:
            user_prompt += f"Parent agent output: {json.dumps(parent_output)}\n\n"

        # Add incident data for query agents
        incident_id_map = {}  # Map index to incident_id for reference tracking
        if incidents and len(incidents) > 0:
            user_prompt += f"Analyze the following {len(incidents)} incidents to answer the question:\n\n"
            # Include first 10 incidents to avoid token limits
            for idx, incident in enumerate(incidents[:10], 1):
                incident_id = incident.get('incident_id', f'unknown-{idx}')
                incident_id_map[idx] = incident_id
                
                incident_text = incident.get('raw_text', '')[:200]  # Limit text length
                structured = incident.get('structured_data', {})
                created_at = incident.get('created_at', '')
                
                user_prompt += f"Incident #{idx} (ID: {incident_id}):\n"
                user_prompt += f"- Text: {incident_text}\n"
                if structured:
                    user_prompt += f"- Category: {structured.get('category', 'N/A')}\n"
                    user_prompt += f"- Location: {structured.get('location', 'N/A')}\n"
                user_prompt += f"- Date: {created_at}\n\n"
            
            if len(incidents) > 10:
                user_prompt += f"(Plus {len(incidents) - 10} more incidents not shown)\n\n"
            
            user_prompt += "\nIMPORTANT: In your response, include a 'references' field listing the incident numbers (e.g., [1, 3, 5]) that you used to formulate your answer.\n"

        user_prompt += "Please analyze the data and return your response as valid JSON."

        # Call Bedrock - use environment variable or default
        model_id = os.environ.get('BEDROCK_DEFAULT_MODEL', 
                                  'anthropic.claude-3-haiku-20240307-v1:0')

        # Check if using Nova model (different format)
        if "nova" in model_id.lower():
            request_body = {
                "messages": [
                    {"role": "user", "content": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
                ],
                "inferenceConfig": {
                    "maxTokens": 1024,
                    "temperature": 0.1
                }
            }
        else:
            # Claude format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.1,
                "messages": [
                    {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                ],
            }

        print(f"Calling Bedrock for {agent_id}...")

        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        
        # Handle different response formats
        if "nova" in model_id.lower():
            # Nova format
            content = response_body["output"]["message"]["content"][0]["text"]
        else:
            # Claude format
            content = response_body["content"][0]["text"]

        # Try to parse JSON from response
        try:
            # Extract JSON from response (might be wrapped in text)
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)

            # Ensure confidence is present
            if "confidence" not in result:
                result["confidence"] = 0.8

            result["agent_id"] = agent_id
            result["raw_response"] = content
            
            # Extract and convert incident references
            if incidents and "references" in result:
                # Convert incident numbers to actual incident IDs
                incident_refs = []
                for ref_num in result.get("references", []):
                    if isinstance(ref_num, int) and ref_num in incident_id_map:
                        incident_refs.append(incident_id_map[ref_num])
                result["incident_references"] = incident_refs
                print(f"Agent {agent_id} referenced {len(incident_refs)} incidents: {incident_refs[:3]}...")

            return result

        except json.JSONDecodeError:
            # If JSON parsing fails, return structured fallback
            print(f"Warning: Could not parse JSON from {agent_id}, returning raw text")
            return {
                "agent_id": agent_id,
                "raw_response": content,
                "confidence": 0.5,
                "error": "Failed to parse JSON",
            }

    except Exception as e:
        print(f"Error executing agent {agent_id}: {e}")
        print(traceback.format_exc())
        return {
            "agent_id": agent_id,
            "error": str(e),
            "confidence": 0.0,
            "status": "failed",
        }


def verify_outputs(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify agent outputs and check confidence scores using orchestrator model
    Confidence scores should be 0.0-1.0 (normalized from 0-5 scale)
    """

    # Use orchestrator model for verification (more complex reasoning)
    verification_prompt = f"""You are a verification agent. Analyze these agent outputs and provide:
1. Normalized confidence score (0.0 to 1.0)
2. Whether clarification is needed
3. Specific clarification questions if needed
4. A brief summary of the findings

Agent outputs:
{json.dumps(results, indent=2)}

Return JSON:
{{
  "overall_confidence": float (0.0-1.0),
  "needs_clarification": boolean,
  "clarification_questions": [list of specific questions],
  "summary": "2-3 sentence summary of what was extracted and its reliability"
}}"""

    try:
        response = bedrock.invoke_model(
            modelId=ORCHESTRATOR_MODEL_ID,  # Use complex model for verification
            body=json.dumps(
                {
                    "messages": [{"role": "user", "content": verification_prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "anthropic_version": "bedrock-2023-05-31",
                }
            ),
        )

        result = json.loads(response["body"].read())
        content = result["content"][0]["text"]

        # Parse JSON from response
        import re

        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            verification_result = json.loads(json_match.group())

            return {
                "agent_results": results,
                "overall_confidence": verification_result.get(
                    "overall_confidence", 0.5
                ),
                "needs_clarification": verification_result.get(
                    "needs_clarification", False
                ),
                "clarification_questions": verification_result.get(
                    "clarification_questions", []
                ),
                "summary": verification_result.get(
                    "summary", "Data extracted from report."
                ),
            }

    except Exception as e:
        print(f"Verification error: {e}, using fallback logic")

    # Fallback verification logic
    verified = {
        "agent_results": results,
        "overall_confidence": 0.0,
        "needs_clarification": False,
        "clarification_questions": [],
        "summary": "",
    }

    # Calculate average confidence (normalize from 0-5 to 0.0-1.0)
    confidences = [
        min(r.get("confidence", 0) / 5.0, 1.0)
        for r in results.values()
        if r.get("confidence") is not None
    ]

    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        verified["overall_confidence"] = avg_confidence

        # Check if clarification needed (low confidence < 0.6)
        if avg_confidence < 0.6:
            verified["needs_clarification"] = True

            # Generate clarification questions based on low-confidence agents
            for agent_id, result in results.items():
                normalized_confidence = result.get("confidence", 5) / 5.0

                if normalized_confidence < 0.6:
                    if "geo" in agent_id:
                        if result.get("needs_clarification"):
                            # Location Service found multiple options
                            options = result.get("clarification_options", [])
                            options_text = ", ".join(
                                [f"'{o['label']}'" for o in options[:3]]
                            )
                            verified["clarification_questions"].append(
                                f"I found multiple locations: {options_text}. Which one are you referring to?"
                            )
                        else:
                            verified["clarification_questions"].append(
                                "Could you provide more specific location details (street name, landmark, or nearby intersection)?"
                            )
                    elif "temporal" in agent_id:
                        verified["clarification_questions"].append(
                            "When did this occur or how long has it been an issue?"
                        )
                    elif "category" in agent_id:
                        verified["clarification_questions"].append(
                            "Could you describe the type of issue in more detail?"
                        )

        # Generate summary
        geo_data = results.get("geo_agent", {}).get("location", {})
        temporal_data = results.get("temporal_agent", {})
        category_data = results.get("category_agent", {})

        summary_parts = []
        if geo_data.get("address"):
            summary_parts.append(f"Location: {geo_data['address']}")
        if temporal_data.get("duration"):
            summary_parts.append(f"Duration: {temporal_data['duration']}")
        if category_data.get("category"):
            summary_parts.append(f"Type: {category_data['category']}")

        verified["summary"] = (
            ". ".join(summary_parts) + f". Confidence: {int(avg_confidence * 100)}%."
        )

    return verified


def build_unified_response(
    job_type: str,
    results: Dict[str, Dict[str, Any]],
    verified: Dict[str, Any],
    job_id: str,
    domain_id: str,
    text: str = None,
    question: str = None,
) -> Dict[str, Any]:
    """
    Build unified response structure for frontend integration
    Follows the structure: status, action, data{ui, map, conversationContext}
    """

    if job_type == "ingest":
        # Data ingestion response
        if verified.get("needs_clarification"):
            return {
                "status": "needs_clarification",
                "action": "ASK_QUESTION",
                "sessionId": job_id,
                "data": {
                    "ui": {
                        "type": "chat_message",
                        "message": verified["clarification_questions"][0]
                        if verified["clarification_questions"]
                        else "Could you provide more details?",
                    },
                    "conversationContext": {
                        "state": "pending_ingestion",
                        "pendingData": results,
                        "lastAgentQuestion": verified["clarification_questions"][0]
                        if verified["clarification_questions"]
                        else "Could you provide more details?",
                    },
                },
            }
        else:
            # Success - build ingested data
            geo_result = results.get("geo_agent", {})
            temporal_result = results.get("temporal_agent", {})
            category_result = results.get("category_agent", {})

            location = geo_result.get("location", {})

            report_data = {
                "reportId": f"R-{job_id[-8:]}",
                "type": category_result.get("category", "unknown"),
                "details": text,
                "location_text": location.get("address", "Unknown location"),
                "latitude": location.get("lat"),
                "longitude": location.get("lon"),
                "status": "Pending",
                "timestamp": temporal_result.get(
                    "timestamp", datetime.utcnow().isoformat()
                ),
                "submittedBy": job_id,
            }

            return {
                "status": "success",
                "action": "SHOW_MESSAGE",
                "sessionId": job_id,
                "data": {
                    "ui": {
                        "type": "toast",
                        "message": f"Report {report_data['reportId']} for '{report_data['type']}' has been created!",
                    },
                    "ingestedData": report_data,
                    "conversationContext": None,
                },
            }

    else:
        # Query response
        if verified.get("needs_clarification"):
            return {
                "status": "needs_clarification",
                "action": "ASK_QUESTION",
                "sessionId": job_id,
                "data": {
                    "ui": {
                        "type": "chat_message",
                        "message": verified["clarification_questions"][0]
                        if verified["clarification_questions"]
                        else "Could you be more specific with your question?",
                    },
                    "conversationContext": {
                        "state": "pending_query",
                        "pendingQuery": question,
                        "lastAgentQuestion": verified["clarification_questions"][0]
                        if verified["clarification_questions"]
                        else "Could you be more specific?",
                    },
                },
            }
        else:
            # Build query response with map data
            what_result = results.get("what_agent", {})
            where_result = results.get("where_agent", {})
            when_result = results.get("when_agent", {})

            # Generate chat summary
            chat_summary = what_result.get("answer", "")
            if not chat_summary and where_result:
                chat_summary = where_result.get("geographic_insights", "")
            if not chat_summary:
                chat_summary = "I analyzed your query. Here are the results on the map."

            # Build map data from query results
            map_data = []
            locations = where_result.get("locations", [])

            # This would typically query DynamoDB for actual report data
            # For now, return structure

            return {
                "status": "success",
                "action": "UPDATE_MAP_AND_CHAT",
                "sessionId": job_id,
                "data": {
                    "ui": {"type": "chat_message", "message": chat_summary},
                    "map": {
                        "action": "FIT_BOUNDS" if map_data else "NO_ACTION",
                        "data": map_data,
                    },
                    "conversationContext": None,
                },
            }


def generate_summary(verified_results: Dict[str, Any], job_type: str) -> str:
    """
    Generate human-readable summary of agent results
    """
    agent_results = verified_results.get("agent_results", {})
    confidence = verified_results.get("overall_confidence", 0)

    summary_parts = []

    if job_type == "ingest":
        summary_parts.append("Report processed by agents:")
        for agent_id, result in agent_results.items():
            agent_name = agent_id.replace("_", " ").title()
            if result.get("error"):
                summary_parts.append(f"- {agent_name}: Processing failed")
            else:
                summary_parts.append(
                    f"- {agent_name}: Confidence {result.get('confidence', 0):.0%}"
                )
    else:
        summary_parts.append("Query analyzed by agents:")
        for agent_id, result in agent_results.items():
            if result.get("answer"):
                summary_parts.append(f"- {agent_id}: {result['answer'][:100]}")

    summary_parts.append(f"\nOverall Confidence: {confidence:.0%}")

    if verified_results.get("needs_clarification"):
        summary_parts.append("\n⚠️ Additional information needed:")
        for q in verified_results.get("clarification_questions", []):
            summary_parts.append(f"  • {q}")

    return "\n".join(summary_parts)


def save_results(
    job_id: str,
    job_type: str,
    domain_id: str,
    tenant_id: str,
    text: str,
    verified_results: Dict[str, Any],
    summary: str,
    incident_references: List[str] = None,
    query_id: str = None,
    incident_id: str = None,
):
    """
    Save processed results to DynamoDB with incident references
    
    Args:
        incident_references: List of incident IDs that were used to generate the response
        query_id: Query ID for query/management jobs
    """
    
    try:
        # For ingestion jobs, update the Reports table
        if job_type == "ingest":
            if not incident_id:
                print("Warning: No incident_id for ingestion job, cannot update report")
                return
            
            # Get Reports table
            reports_table_name = os.environ.get("REPORTS_TABLE", "MultiAgentOrchestration-dev-Data-Reports")
            reports_table = dynamodb.Table(reports_table_name)
            
            # Update the report with ingestion_data
            ingestion_data = convert_floats_to_decimal(verified_results["agent_results"])
            
            reports_table.update_item(
                Key={"incident_id": incident_id},
                UpdateExpression="SET ingestion_data = :data, #status = :status, updated_at = :updated",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":data": ingestion_data,
                    ":status": "completed",
                    ":updated": datetime.utcnow().isoformat()
                }
            )
            print(f"Updated Reports table for incident {incident_id} with ingestion data")
            return
        
        # For query/management jobs, save to Incidents table
        if not incidents_table:
            print("Warning: Incidents table not available, skipping save")
            return
            
        item = {
            "incident_id"
            if job_type == "ingest"
            else "query_id": f"{job_type}_{job_id}",
            "job_id": job_id,
            "tenant_id": tenant_id,
            "domain_id": domain_id,
            "raw_text": text,
            "structured_data": verified_results["agent_results"],
            "overall_confidence": verified_results["overall_confidence"],
            "needs_clarification": verified_results.get("needs_clarification", False),
            "clarification_questions": verified_results.get(
                "clarification_questions", []
            ),
            "summary": summary,
            "references_used": incident_references or [],  # Add references
            "status": "completed",
            "processed_at": datetime.utcnow().isoformat(),
            "job_type": job_type,
        }

        # Convert floats to Decimal for DynamoDB
        item = convert_floats_to_decimal(item)

        incidents_table.put_item(Item=item)
        print(f"Results saved to incidents table for job {job_id}")
        
        # For query jobs, also update the QueryJobs table with results and references
        if job_type in ["query", "management"] and query_jobs_table and query_id:
            try:
                
                # Build execution log from agent results
                execution_log = []
                for agent_id, result in verified_results.get("agent_results", {}).items():
                    execution_log.append({
                        "agent_id": agent_id,
                        "output": result,
                        "confidence": result.get("confidence", 0.5)
                    })
                
                # Update query with results and references
                update_expr = "SET summary = :summary, execution_log = :log, references_used = :refs, #status = :status, updated_at = :updated"
                
                query_jobs_table.update_item(
                    Key={"query_id": query_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":summary": summary,
                        ":log": execution_log,
                        ":refs": incident_references or [],
                        ":status": "completed",
                        ":updated": datetime.utcnow().isoformat()
                    }
                )
                print(f"Updated QueryJobs table with {len(incident_references or [])} references")
            except Exception as query_error:
                print(f"Warning: Could not update QueryJobs table: {query_error}")

    except Exception as e:
        print(f"Error saving results: {e}")
        print(traceback.format_exc())


def update_job_status(job_id: str, status: str, error: Optional[str] = None):
    """Update job status in database"""
    if not incidents_table:
        return

    try:
        incidents_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": status,
                ":updated": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        print(f"Error updating job status: {e}")
