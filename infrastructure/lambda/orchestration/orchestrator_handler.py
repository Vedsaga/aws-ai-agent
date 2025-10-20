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

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
bedrock = boto3.client(
    "bedrock-runtime", region_name=os.environ.get("BEDROCK_REGION", "us-east-1")
)

# Environment variables
CONFIGURATIONS_TABLE = os.environ.get(
    "CONFIGURATIONS_TABLE", "MultiAgentOrchestration-dev-Data-Configurations"
)
INCIDENTS_TABLE = os.environ.get(
    "INCIDENTS_TABLE", "MultiAgentOrchestration-dev-Incidents"
)

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


try:
    incidents_table = dynamodb.Table(INCIDENTS_TABLE)
except Exception as e:
    print(f"Warning: Could not initialize incidents table: {e}")
    incidents_table = None


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

    print(f"Processing job: {job_id}, type: {job_type}, domain: {domain_id}")

    try:
        # Step 1: Load domain configuration
        domain_config = load_domain_config(domain_id)
        if not domain_config:
            print(f"Domain not found: {domain_id}, using default agents")
            domain_config = get_default_domain_config(job_type)

        # Step 2: Get agent list based on job type
        if job_type == "ingest":
            agent_ids = domain_config.get(
                "ingest_agent_ids", ["geo_agent", "temporal_agent"]
            )
        else:
            agent_ids = domain_config.get(
                "query_agent_ids", ["what_agent", "where_agent", "when_agent"]
            )

        print(f"Agent pipeline: {agent_ids}")

        # Step 3: Load agent configurations
        agents = []
        for agent_id in agent_ids:
            agent_config = load_agent_config(agent_id)
            if agent_config:
                agents.append(agent_config)

        # Step 4: Build execution plan (handle dependencies)
        execution_plan = build_execution_plan(agents)
        print(f"Execution plan: {[a['agent_id'] for a in execution_plan]}")

        # Step 5: Execute agents in order
        results = {}
        for agent in execution_plan:
            agent_id = agent["agent_id"]

            # Get parent output if agent has dependency
            parent_output = None
            if agent.get("dependency_parent"):
                parent_output = results.get(agent["dependency_parent"])

            # Execute agent
            result = execute_agent(agent, text, parent_output)
            results[agent_id] = result
            print(
                f"Agent {agent_id} executed: confidence={result.get('confidence', 'N/A')}"
            )

        # Step 6: Verify outputs (check confidence scores)
        verified_results = verify_outputs(results)

        # Step 7: Generate summary
        summary = generate_summary(verified_results, job_type)

        # Step 8: Save results
        save_results(
            job_id, job_type, domain_id, tenant_id, text, verified_results, summary
        )

        print(f"Job {job_id} completed successfully")
        return {"status": "completed", "job_id": job_id, "summary": summary}

    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        print(traceback.format_exc())
        update_job_status(job_id, "failed", str(e))
        return {"status": "failed", "job_id": job_id, "error": str(e)}


def load_domain_config(domain_id: str) -> Optional[Dict[str, Any]]:
    """Load domain configuration from DynamoDB"""
    try:
        # Try to find domain in system tenant
        response = config_table.get_item(
            Key={"tenant_id": "system", "config_key": f"DOMAIN#{domain_id}"}
        )

        if "Item" in response:
            return response["Item"]

        # Try default-tenant
        response = config_table.get_item(
            Key={"tenant_id": "default-tenant", "config_key": f"domain_{domain_id}"}
        )

        if "Item" in response:
            return response["Item"]

        return None

    except Exception as e:
        print(f"Error loading domain config: {e}")
        return None


def get_default_domain_config(job_type: str) -> Dict[str, Any]:
    """Return default agent configuration"""
    if job_type == "ingest":
        return {
            "domain_id": "default",
            "ingest_agent_ids": ["geo_agent", "temporal_agent", "category_agent"],
        }
    else:
        return {
            "domain_id": "default",
            "query_agent_ids": ["what_agent", "where_agent", "when_agent"],
        }


def load_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
    """Load agent configuration from DynamoDB"""
    try:
        # Try system tenant first
        response = config_table.query(
            IndexName="ConfigTypeIndex",
            KeyConditionExpression="config_type = :type",
            FilterExpression="agent_id = :agent_id",
            ExpressionAttributeValues={":type": "agent_config", ":agent_id": agent_id},
            Limit=1,
        )

        if response.get("Items"):
            return response["Items"][0]

        # Try by config_key pattern
        for tenant in ["system", "default-tenant"]:
            try:
                response = config_table.get_item(
                    Key={"tenant_id": tenant, "config_key": agent_id}
                )
                if "Item" in response:
                    return response["Item"]
            except:
                pass

        # Fallback: create basic config
        return create_fallback_agent_config(agent_id)

    except Exception as e:
        print(f"Error loading agent {agent_id}: {e}")
        return create_fallback_agent_config(agent_id)


def create_fallback_agent_config(agent_id: str) -> Dict[str, Any]:
    """Create fallback agent configuration"""
    prompts = {
        "geo_agent": 'Extract location information (address, coordinates, place names) from the text. Return JSON with: {"location": {"address": "string", "lat": number, "lon": number}, "confidence": number}',
        "temporal_agent": 'Extract time/date information from the text. Return JSON with: {"timestamp": "ISO date", "duration": "string", "confidence": number}',
        "category_agent": 'Categorize the complaint into: infrastructure, public_safety, environmental, or other. Return JSON with: {"category": "string", "subcategory": "string", "confidence": number}',
        "what_agent": 'Analyze and answer the \'what\' aspects of the question. Return JSON with: {"answer": "string", "key_points": ["string"], "confidence": number}',
        "where_agent": 'Analyze and answer the \'where\' aspects of the question. Return JSON with: {"locations": ["string"], "geographic_insights": "string", "confidence": number}',
        "when_agent": 'Analyze and answer the \'when\' aspects of the question. Return JSON with: {"time_periods": ["string"], "temporal_patterns": "string", "confidence": number}',
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
    agent: Dict[str, Any], text: str, parent_output: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Execute a single agent using AWS Bedrock
    """
    agent_id = agent["agent_id"]
    system_prompt = agent.get(
        "system_prompt", "Extract relevant information from the text."
    )

    try:
        # Build prompt
        user_prompt = f"Text to analyze: {text}\n\n"

        if parent_output:
            user_prompt += f"Parent agent output: {json.dumps(parent_output)}\n\n"

        user_prompt += "Please analyze the text and return your response as valid JSON."

        # Call Bedrock
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

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
    Verify agent outputs and check confidence scores
    """
    verified = {
        "agent_results": results,
        "overall_confidence": 0.0,
        "needs_clarification": False,
        "clarification_questions": [],
    }

    # Calculate average confidence
    confidences = [
        r.get("confidence", 0)
        for r in results.values()
        if r.get("confidence") is not None
    ]

    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        verified["overall_confidence"] = avg_confidence

        # Check if clarification needed (low confidence)
        if avg_confidence < 0.5:
            verified["needs_clarification"] = True

            # Generate clarification questions based on low-confidence agents
            for agent_id, result in results.items():
                if result.get("confidence", 1.0) < 0.5:
                    if "geo" in agent_id:
                        verified["clarification_questions"].append(
                            "Can you provide a more specific location or address?"
                        )
                    elif "temporal" in agent_id:
                        verified["clarification_questions"].append(
                            "Can you provide specific dates or times?"
                        )
                    elif "category" in agent_id:
                        verified["clarification_questions"].append(
                            "Can you provide more details about the type of issue?"
                        )

    return verified


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
):
    """
    Save processed results to DynamoDB
    """
    if not incidents_table:
        print("Warning: Incidents table not available, skipping save")
        return

    try:
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
            "status": "completed",
            "processed_at": datetime.utcnow().isoformat(),
            "job_type": job_type,
        }

        # Convert floats to Decimal for DynamoDB
        item = convert_floats_to_decimal(item)

        incidents_table.put_item(Item=item)
        print(f"Results saved for job {job_id}")

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
