# Builtin Agents Summary

## Overview
The system has **12 builtin agents** across 3 classes that are seeded in the database:

## Ingestion Agents (3)
These agents extract structured data from unstructured text during report submission:

1. **builtin-ingestion-geo** (Geo Locator)
   - Extracts location information (addresses, landmarks, coordinates)
   - Uses Amazon Location Service for geocoding
   - Detects geometry types (Point, LineString, Polygon)
   - Output: location_name, coordinates, geometry_type, confidence, address

2. **builtin-ingestion-temporal** (Temporal Analyzer)
   - Extracts time and date information
   - Parses relative time expressions ("today", "yesterday", "this morning")
   - Determines urgency level (immediate, urgent, moderate, low)
   - Output: timestamp, time_reference, urgency

3. **builtin-ingestion-entity** (Entity Extractor)
   - Extracts named entities (people, organizations, locations)
   - Analyzes sentiment (positive, negative, neutral, mixed)
   - Extracts key phrases
   - Categorizes complaint type
   - Output: entities, sentiment, key_phrases, category, confidence

## Query Agents (6)
These agents answer questions by analyzing data from different perspectives:

4. **builtin-query-who** (Who Agent)
   - Answers "who" questions about entities and actors
   - Identifies who reported, who was affected
   - Output: entities, reporters, affected, answer

5. **builtin-query-what** (What Agent)
   - Answers "what" questions about incident types
   - Identifies common issues and patterns
   - Output: incident_types, common_issues, summary, answer

6. **builtin-query-where** (Where Agent)
   - Answers "where" questions about locations
   - Identifies geographic clusters and hotspots
   - Generates map data for visualization
   - Output: locations, hotspots, map_data, answer

7. **builtin-query-when** (When Agent)
   - Answers "when" questions about temporal patterns
   - Analyzes time trends and frequency
   - Output: time_pattern, frequency, trend, answer

8. **builtin-query-why** (Why Agent)
   - Answers "why" questions about causes
   - Identifies root causes and contributing factors
   - Output: causes, factors, analysis, answer

9. **builtin-query-how** (How Agent)
   - Answers "how" questions about methods
   - Analyzes processes and mechanisms
   - Output: methods, process, insights, answer

## Management Agents (3)
These agents update and manage existing reports:

10. **builtin-management-task-assigner** (Task Assigner)
    - Assigns tasks to teams or individuals
    - Extracts assignee information from commands
    - Output: assignee_id, assignee_type, assigned_at, reason

11. **builtin-management-status-updater** (Status Updater)
    - Updates report status (pending, in_progress, resolved, closed)
    - Adds history entries with timestamps
    - Output: status, updated_at, updated_by, notes

12. **builtin-management-task-details-editor** (Task Details Editor)
    - Edits task details (priority, due date, metadata)
    - Tracks changes with timestamps
    - Output: field, value, updated_at, reason

## Sample Domain
A **civic_complaints** domain is also seeded with playbooks that use these agents:

- **Ingestion Playbook**: Uses all 3 ingestion agents (geo, temporal, entity)
- **Query Playbook**: Uses all 6 query agents (who, what, where, when, why, how)
- **Management Playbook**: Uses all 3 management agents (task-assigner, status-updater, task-details-editor)

## E2E Testing
The `test_e2e_flows.py` script tests all three flows:

1. **Ingestion Flow**: Submits a report → 3 ingestion agents extract data
2. **Query Flow**: Asks a question → 4 query agents analyze and answer
3. **Management Flow**: Updates a report → 3 management agents process changes

Each flow verifies that the correct agents are invoked and produce expected outputs.
