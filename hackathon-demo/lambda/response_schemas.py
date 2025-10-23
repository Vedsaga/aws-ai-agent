"""
Response Schema Definitions
Meta-level and Micro-level (domain-specific) structures
"""

# ============================================================================
# META-LEVEL SCHEMAS (Universal across all domains)
# ============================================================================

INGESTION_RESPONSE_SCHEMA = {
    "session_id": "string",
    "mode": "ingestion",
    "result": {
        "status": "success | needs_clarification | error",
        "report_id": "uuid | null",
        "confidence": "float (0.0-1.0)",
        "needs_clarification": "boolean",
        "clarification_question": "string | null",
        "data": {
            # Domain-specific structured data
        },
        "agent_execution": {
            "agents_run": ["agent_id1", "agent_id2"],
            "execution_time_ms": "integer",
            "agent_results": {
                "agent_id": {
                    "status": "completed | error",
                    "confidence": "float",
                    "output": "any"
                }
            }
        },
        "metadata": {
            "created_at": "ISO8601 timestamp",
            "source": "string",
            "version": "string"
        }
    }
}

QUERY_RESPONSE_SCHEMA = {
    "session_id": "string",
    "mode": "query",
    "result": {
        "status": "success | error",
        "total_results": "integer",
        "results": [
            # Array of matching records
        ],
        "filters_applied": {
            # Extracted filters from query
        },
        "summary": "string (AI-generated summary)",
        "visualizations": {
            "map_data": {
                "type": "FeatureCollection",
                "features": []
            },
            "charts": []  # Future: chart data
        },
        "agent_execution": {
            "agents_run": ["agent_id1", "agent_id2"],
            "execution_time_ms": "integer",
            "agent_results": {}
        },
        "metadata": {
            "query_timestamp": "ISO8601",
            "data_sources": ["source1", "source2"]
        }
    }
}

MANAGEMENT_RESPONSE_SCHEMA = {
    "session_id": "string",
    "mode": "management",
    "result": {
        "status": "success | error",
        "action": "assign | update_status | set_priority | add_note",
        "target_report_id": "uuid (REQUIRED - must reference existing report)",
        "updates_applied": {
            # Key-value pairs of what was updated
        },
        "confirmation": "string (human-readable confirmation)",
        "previous_values": {
            # What the values were before update (for audit)
        },
        "agent_execution": {
            "command_parsed": "boolean",
            "execution_time_ms": "integer"
        },
        "metadata": {
            "updated_at": "ISO8601",
            "updated_by": "string"
        }
    }
}

# ============================================================================
# MICRO-LEVEL SCHEMAS (Domain-specific: Civic Reports)
# ============================================================================

CIVIC_INGESTION_DATA_SCHEMA = {
    "location": {
        "address": "string",
        "geo_coordinates": [
            "longitude (float)",
            "latitude (float)"
        ],
        "place_id": "string | null",
        "confidence": "float"
    },
    "entity": {
        "type": "pothole | streetlight | graffiti | debris | other",
        "description": "string",
        "confidence": "float"
    },
    "severity": {
        "level": "low | medium | high | critical",
        "reasoning": "string",
        "confidence": "float"
    },
    "temporal": {
        "reported_at": "ISO8601",
        "incident_time": "ISO8601 | null (when it happened)",
        "urgency": "immediate | soon | routine"
    },
    "reporter": {
        "contact": "string | null",
        "source": "web | mobile | phone | email"
    }
}

CIVIC_QUERY_FILTERS_SCHEMA = {
    "severity": "low | medium | high | critical | null",
    "entity_type": "string | null",
    "location": "string | null",
    "status": "pending | in_progress | resolved | closed | null",
    "date_range": {
        "start": "ISO8601 | null",
        "end": "ISO8601 | null"
    },
    "assignee": "string | null"
}

CIVIC_MANAGEMENT_ACTIONS_SCHEMA = {
    "assign": {
        "required_fields": ["target_report_id", "assignee"],
        "updates": {
            "assignee": "string (team name or person)",
            "assigned_at": "ISO8601",
            "status": "in_progress (auto-set)"
        }
    },
    "update_status": {
        "required_fields": ["target_report_id", "status"],
        "updates": {
            "status": "pending | in_progress | resolved | closed",
            "status_updated_at": "ISO8601"
        }
    },
    "set_priority": {
        "required_fields": ["target_report_id", "priority"],
        "updates": {
            "priority": "low | medium | high | critical",
            "priority_updated_at": "ISO8601"
        }
    },
    "add_note": {
        "required_fields": ["target_report_id", "note"],
        "updates": {
            "notes": "array of note objects",
            "last_note_at": "ISO8601"
        }
    }
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

VALIDATION_RULES = {
    "ingestion": {
        "min_confidence_threshold": 0.7,
        "required_fields": ["location", "entity", "severity"],
        "geo_coordinates_format": "[-180 to 180, -90 to 90]"
    },
    "query": {
        "max_results": 200,
        "default_limit": 50,
        "valid_sort_fields": ["created_at", "severity", "status"]
    },
    "management": {
        "must_reference_existing_report": True,
        "valid_statuses": ["pending", "in_progress", "resolved", "closed"],
        "valid_priorities": ["low", "medium", "high", "critical"],
        "audit_trail_required": True
    }
}

# ============================================================================
# ERROR RESPONSE SCHEMA
# ============================================================================

ERROR_RESPONSE_SCHEMA = {
    "session_id": "string",
    "mode": "string",
    "result": {
        "status": "error",
        "error_code": "string",
        "error_message": "string",
        "details": "any",
        "timestamp": "ISO8601"
    }
}
