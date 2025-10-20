"""
Status API Handler - Poll for job completion status
Allows clients to check if orchestrator has finished processing
"""

import json
import os
import boto3
from datetime import datetime
import traceback

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables
INCIDENTS_TABLE = os.environ.get(
    "INCIDENTS_TABLE", "MultiAgentOrchestration-dev-Data-Incidents"
)
QUERIES_TABLE = os.environ.get(
    "QUERIES_TABLE", "MultiAgentOrchestration-dev-Data-Queries"
)

# Initialize DynamoDB tables
incidents_table = dynamodb.Table(INCIDENTS_TABLE)
queries_table = dynamodb.Table(QUERIES_TABLE)


def handler(event, context):
    """
    Main Lambda handler for status API
    GET /api/v1/status/{job_id}
    """
    print(f"Event: {json.dumps(event, default=str)}")

    try:
        # Extract job_id from path parameters
        path_params = event.get("pathParameters", {})
        job_id = path_params.get("job_id")

        if not job_id:
            return error_response(400, "Missing job_id in path")

        print(f"Checking status for job_id: {job_id}")

        # Determine if it's an ingest or query job
        if job_id.startswith("query_"):
            result = check_query_status(job_id)
        elif job_id.startswith("job_"):
            result = check_ingest_status(job_id)
        else:
            return error_response(400, "Invalid job_id format")

        if not result:
            return error_response(404, "Job not found")

        return success_response(result)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


def check_ingest_status(job_id: str) -> dict:
    """
    Check status of an ingestion job
    Returns unified response structure
    """
    try:
        # Scan for records with this job_id
        response = incidents_table.scan(
            FilterExpression="job_id = :jid",
            ExpressionAttributeValues={":jid": job_id},
        )

        items = response.get("Items", [])

        if not items:
            return None

        # Look for the orchestrator-processed record (has structured_data with agents)
        processed_record = None
        for item in items:
            structured_data = item.get("structured_data", {})
            if "geo_agent" in structured_data or "temporal_agent" in structured_data:
                processed_record = item
                break

        if not processed_record:
            # Still processing
            return {
                "status": "processing",
                "action": "WAIT",
                "job_id": job_id,
                "message": "Report is being processed by agents",
                "estimated_completion_seconds": 10,
            }

        # Processing complete - build response
        status = processed_record.get("status", "completed")
        needs_clarification = processed_record.get("needs_clarification", False)
        confidence = processed_record.get("overall_confidence", 1.0)
        clarification_questions = processed_record.get("clarification_questions", [])
        summary = processed_record.get("summary", "")

        structured_data = processed_record.get("structured_data", {})
        geo_data = structured_data.get("geo_agent", {})
        temporal_data = structured_data.get("temporal_agent", {})
        category_data = structured_data.get("category_agent", {})

        # Extract location
        location = geo_data.get("location", {})

        # Build ingested data
        ingested_data = {
            "reportId": processed_record.get("incident_id", ""),
            "jobId": job_id,
            "type": category_data.get("category", "unknown"),
            "details": processed_record.get("raw_text", ""),
            "location_text": location.get("address", "Unknown location"),
            "latitude": location.get("lat"),
            "longitude": location.get("lon"),
            "city": location.get("city"),
            "country": location.get("country"),
            "status": status,
            "timestamp": temporal_data.get("timestamp", datetime.utcnow().isoformat()),
            "duration": temporal_data.get("duration"),
            "confidence": float(confidence) if confidence else 0.5,
            "submittedBy": processed_record.get("tenant_id", ""),
        }

        if needs_clarification:
            # Return clarification needed
            return {
                "status": "needs_clarification",
                "action": "ASK_QUESTION",
                "sessionId": job_id,
                "data": {
                    "ui": {
                        "type": "chat_message",
                        "message": clarification_questions[0]
                        if clarification_questions
                        else "Could you provide more details?",
                    },
                    "conversationContext": {
                        "state": "pending_ingestion",
                        "jobId": job_id,
                        "pendingData": ingested_data,
                        "lastAgentQuestion": clarification_questions[0]
                        if clarification_questions
                        else "Could you provide more details?",
                    },
                    "summary": summary,
                },
            }
        else:
            # Return success with data
            return {
                "status": "success",
                "action": "SHOW_MESSAGE",
                "sessionId": job_id,
                "data": {
                    "ui": {
                        "type": "toast",
                        "message": f"Report {ingested_data['reportId']} created successfully!",
                    },
                    "ingestedData": ingested_data,
                    "conversationContext": None,
                    "summary": summary,
                    "map": {
                        "action": "ZOOM_TO",
                        "data": [
                            {
                                "type": "point",
                                "geometry": {
                                    "lat": ingested_data["latitude"],
                                    "lon": ingested_data["longitude"],
                                },
                                "icon": ingested_data.get("type", "marker"),
                                "fullReport": ingested_data,
                            }
                        ]
                        if ingested_data.get("latitude")
                        and ingested_data.get("longitude")
                        else [],
                    },
                },
            }

    except Exception as e:
        print(f"Error checking ingest status: {e}")
        return None


def check_query_status(job_id: str) -> dict:
    """
    Check status of a query job
    Returns unified response structure
    """
    try:
        # Get query record
        response = queries_table.get_item(Key={"job_id": job_id})

        item = response.get("Item")
        if not item:
            return None

        status = item.get("status", "processing")
        agent_results = item.get("agent_results", {})
        summary = item.get("summary", "")
        question = item.get("question", "")

        # Check if processing is complete
        if status == "processing" or not agent_results:
            return {
                "status": "processing",
                "action": "WAIT",
                "job_id": job_id,
                "message": "Query is being processed by agents",
                "estimated_completion_seconds": 5,
            }

        # Build query response
        # This is simplified - you'd query incidents table for actual map data
        return {
            "status": "success",
            "action": "UPDATE_MAP_AND_CHAT",
            "sessionId": job_id,
            "data": {
                "ui": {
                    "type": "chat_message",
                    "message": summary
                    or "I've analyzed your query. Here are the results.",
                },
                "map": {
                    "action": "FIT_BOUNDS",
                    "data": [],  # Would populate from actual incidents
                },
                "conversationContext": None,
            },
        }

    except Exception as e:
        print(f"Error checking query status: {e}")
        return None


def success_response(data, status_code=200):
    """Return successful response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(data, default=str),
    }


def error_response(status_code, message):
    """Return error response"""
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(
            {
                "error": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ),
    }


def cors_headers():
    """Return CORS headers"""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Tenant-ID",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }
