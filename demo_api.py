#!/usr/bin/env python3
"""
Local Mock API for Demo - Works Without AWS
Simulates the Multi-Agent Orchestration System APIs
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Mock data storage
agents = {
    "geo_agent": {
        "agent_id": "geo_agent",
        "agent_name": "Geo Agent",
        "agent_type": "geo",
        "system_prompt": "Extract location information from text",
        "tools": ["bedrock", "location_service"],
        "output_schema": {
            "address": "string",
            "coordinates": "object",
            "confidence": "number",
        },
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    },
    "temporal_agent": {
        "agent_id": "temporal_agent",
        "agent_name": "Temporal Agent",
        "agent_type": "temporal",
        "system_prompt": "Extract time information from text",
        "tools": ["bedrock", "comprehend"],
        "output_schema": {"timestamp": "string", "confidence": "number"},
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    },
    "what_agent": {
        "agent_id": "what_agent",
        "agent_name": "What Agent",
        "agent_type": "query",
        "system_prompt": "Answer 'what' questions about data",
        "tools": ["bedrock"],
        "output_schema": {"answer": "string", "data": "object"},
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    },
    "where_agent": {
        "agent_id": "where_agent",
        "agent_name": "Where Agent",
        "agent_type": "query",
        "system_prompt": "Answer 'where' questions about data",
        "tools": ["bedrock"],
        "output_schema": {"answer": "string", "locations": "array"},
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    },
    "when_agent": {
        "agent_id": "when_agent",
        "agent_name": "When Agent",
        "agent_type": "query",
        "system_prompt": "Answer 'when' questions about data",
        "tools": ["bedrock"],
        "output_schema": {"answer": "string", "timeframes": "array"},
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    },
}

domains = {
    "civic_complaints": {
        "template_id": "civic_complaints",
        "template_name": "Civic Complaints",
        "domain_id": "civic_complaints",
        "description": "Municipal infrastructure and service complaints",
        "ingest_agent_ids": ["geo_agent", "temporal_agent"],
        "query_agent_ids": ["what_agent", "where_agent", "when_agent"],
        "is_builtin": True,
        "created_at": "2025-01-15T10:00:00Z",
    }
}

incidents = []
queries = []


@app.route("/")
def home():
    return jsonify(
        {
            "service": "Multi-Agent Orchestration System - Demo API",
            "status": "running",
            "version": "1.0.0-demo",
            "note": "This is a local mock API for demonstration purposes",
            "endpoints": {
                "config": "/api/v1/config",
                "ingest": "/api/v1/ingest",
                "query": "/api/v1/query",
            },
        }
    )


@app.route("/api/v1/config", methods=["GET", "POST"])
def config():
    """Config API - Agent and Domain Management"""

    if request.method == "GET":
        # List configurations
        config_type = request.args.get("type", "agent")

        if config_type == "agent":
            return jsonify({"configs": list(agents.values()), "count": len(agents)})
        elif config_type == "domain_template":
            return jsonify({"configs": list(domains.values()), "count": len(domains)})
        else:
            return jsonify({"error": "Invalid type"}), 400

    elif request.method == "POST":
        # Create configuration
        data = request.json
        config_type = data.get("type")
        config_data = data.get("config", {})

        if config_type == "agent":
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
            new_agent = {
                "agent_id": agent_id,
                "agent_name": config_data.get("agent_name", "Unnamed Agent"),
                "agent_type": config_data.get("agent_type", "custom"),
                "system_prompt": config_data.get("system_prompt", ""),
                "tools": config_data.get("tools", []),
                "output_schema": config_data.get("output_schema", {}),
                "is_builtin": False,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            agents[agent_id] = new_agent
            return jsonify(new_agent), 201

        elif config_type == "domain_template":
            domain_id = config_data.get("domain_id", f"domain_{uuid.uuid4().hex[:8]}")
            new_domain = {
                "template_id": domain_id,
                "template_name": config_data.get("template_name", "Unnamed Domain"),
                "domain_id": domain_id,
                "description": config_data.get("description", ""),
                "ingest_agent_ids": config_data.get("ingest_agent_ids", []),
                "query_agent_ids": config_data.get("query_agent_ids", []),
                "is_builtin": False,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            domains[domain_id] = new_domain
            return jsonify(new_domain), 201

        return jsonify({"error": "Invalid type"}), 400


@app.route("/api/v1/config/<config_type>/<config_id>", methods=["GET", "PUT", "DELETE"])
def config_item(config_type, config_id):
    """Config API - Individual Item Operations"""

    if config_type == "agent":
        collection = agents
    elif config_type == "domain_template":
        collection = domains
    else:
        return jsonify({"error": "Invalid type"}), 400

    if request.method == "GET":
        if config_id in collection:
            return jsonify(collection[config_id])
        return jsonify({"error": "Not found"}), 404

    elif request.method == "PUT":
        if config_id not in collection:
            return jsonify({"error": "Not found"}), 404

        data = request.json
        config_data = data.get("config", {})
        collection[config_id].update(config_data)
        collection[config_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        return jsonify(collection[config_id])

    elif request.method == "DELETE":
        if config_id not in collection:
            return jsonify({"error": "Not found"}), 404

        if collection[config_id].get("is_builtin", False):
            return jsonify({"error": "Cannot delete built-in configuration"}), 403

        del collection[config_id]
        return jsonify({"message": f"{config_type} deleted successfully"})


@app.route("/api/v1/ingest", methods=["POST"])
def ingest():
    """Ingest API - Submit Reports"""

    data = request.json
    domain_id = data.get("domain_id")
    text = data.get("text")

    # Validation
    if not domain_id:
        return jsonify({"error": "Missing required field: domain_id"}), 400
    if not text:
        return jsonify({"error": "Missing required field: text"}), 400
    if len(text) > 10000:
        return jsonify({"error": "Text exceeds maximum length"}), 400

    # Create incident
    job_id = f"job_{uuid.uuid4().hex}"
    incident_id = f"inc_{uuid.uuid4().hex[:8]}"

    incident = {
        "job_id": job_id,
        "incident_id": incident_id,
        "domain_id": domain_id,
        "raw_text": text,
        "status": "processing",
        "priority": data.get("priority", "normal"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "structured_data": {
            "location": {
                "address": "123 Main Street",
                "coordinates": {"lat": 37.7749, "lon": -122.4194},
                "confidence": 0.85,
            },
            "timestamp": {
                "extracted_time": datetime.utcnow().isoformat() + "Z",
                "confidence": 0.78,
            },
        },
    }

    incidents.append(incident)

    return jsonify(
        {
            "job_id": job_id,
            "status": "accepted",
            "message": "Report submitted for processing",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "estimated_completion_seconds": 30,
        }
    ), 202


@app.route("/api/v1/query", methods=["POST"])
def query():
    """Query API - Ask Questions"""

    data = request.json
    domain_id = data.get("domain_id")
    question = data.get("question")

    # Validation
    if not domain_id:
        return jsonify({"error": "Missing required field: domain_id"}), 400
    if not question:
        return jsonify({"error": "Missing required field: question"}), 400
    if len(question) > 1000:
        return jsonify({"error": "Question exceeds maximum length"}), 400

    # Create query job
    job_id = f"query_{uuid.uuid4().hex}"

    query_result = {
        "job_id": job_id,
        "status": "completed",
        "question": question,
        "domain_id": domain_id,
        "agent_results": {
            "what_agent": {
                "answer": "The most common complaints are infrastructure issues (45%) and public safety concerns (30%).",
                "confidence": 0.85,
                "data": {
                    "top_categories": [
                        {"category": "infrastructure", "count": 245},
                        {"category": "public_safety", "count": 163},
                        {"category": "environmental", "count": 98},
                    ]
                },
            },
            "when_agent": {
                "answer": "Peak complaint times are Monday mornings (8-10 AM) and Friday afternoons (3-5 PM).",
                "confidence": 0.78,
                "data": {"peak_times": ["Monday 8-10 AM", "Friday 3-5 PM"]},
            },
            "where_agent": {
                "answer": "Most complaints come from downtown area (40%) and residential zones (35%).",
                "confidence": 0.82,
                "data": {
                    "locations": [
                        {"area": "downtown", "percentage": 40},
                        {"area": "residential", "percentage": 35},
                    ]
                },
            },
        },
        "summary": "Analysis shows infrastructure and public safety are primary concerns with clear temporal patterns. Most issues occur in downtown and residential areas during weekday peak hours.",
        "confidence_score": 0.82,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "processing_time_seconds": random.uniform(2.5, 4.8),
    }

    queries.append(query_result)

    return jsonify(query_result), 200


@app.route("/api/v1/data", methods=["GET"])
def data():
    """Data API - Retrieve Incidents"""

    query_type = request.args.get("type", "retrieval")

    if query_type == "retrieval":
        # Return stored incidents
        return jsonify(
            {
                "status": "success",
                "data": incidents[-10:],  # Last 10 incidents
                "count": len(incidents[-10:]),
                "total_count": len(incidents),
            }
        )

    return jsonify({"error": "Query type not implemented"}), 400


@app.route("/api/v1/tools", methods=["GET"])
def tools():
    """Tool Registry API - List Available Tools"""

    tools_list = [
        {
            "tool_name": "bedrock",
            "tool_type": "llm",
            "description": "AWS Bedrock - Claude 3 Sonnet",
            "is_builtin": True,
        },
        {
            "tool_name": "comprehend",
            "tool_type": "nlp",
            "description": "AWS Comprehend - NLP analysis",
            "is_builtin": True,
        },
        {
            "tool_name": "location_service",
            "tool_type": "geo",
            "description": "AWS Location Service - Geocoding",
            "is_builtin": True,
        },
    ]

    return jsonify({"tools": tools_list, "count": len(tools_list)})


@app.route("/health")
def health():
    """Health Check"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "stats": {
                "agents": len(agents),
                "domains": len(domains),
                "incidents": len(incidents),
                "queries": len(queries),
            },
        }
    )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Multi-Agent Orchestration System - Local Demo API")
    print("=" * 70)
    print("\n✓ Starting server on http://localhost:8000")
    print("\n📋 Available Endpoints:")
    print("  - GET  /api/v1/config?type=agent")
    print("  - POST /api/v1/config")
    print("  - POST /api/v1/ingest")
    print("  - POST /api/v1/query")
    print("  - GET  /api/v1/data?type=retrieval")
    print("  - GET  /api/v1/tools")
    print("  - GET  /health")
    print("\n💡 Test with:")
    print("  curl http://localhost:8000/api/v1/config?type=agent")
    print("\n⚠️  Note: This is a DEMO API - no authentication required")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=8000, debug=True)
