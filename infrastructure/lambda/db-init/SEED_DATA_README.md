# Seed Data Documentation

This document describes the builtin agents and sample domain that are automatically seeded during database initialization.

## Overview

The seed data includes:
- **12 Builtin Agents**: 3 ingestion, 6 query, 3 management
- **1 Sample Domain**: civic_complaints with all three playbooks configured

All builtin agents are marked with `is_inbuilt=true` to prevent deletion and indicate they are system-provided.

## Builtin Ingestion Agents

These agents process unstructured input and extract structured data.

### 1. Geo Locator (`builtin-ingestion-geo`)
- **Purpose**: Extract geographic location from text
- **Tools**: location_service, web_search
- **Output**: location_text, geo_location (GeoJSON Point), address, confidence
- **Use Case**: "There's a pothole on Main Street" → extracts coordinates

### 2. Temporal Analyzer (`builtin-ingestion-temporal`)
- **Purpose**: Extract time/date information and determine urgency
- **Tools**: None (LLM-based)
- **Output**: timestamp (ISO 8601), time_reference, urgency (immediate/urgent/moderate/low)
- **Use Case**: "Yesterday morning" → converts to ISO timestamp

### 3. Entity Extractor (`builtin-ingestion-entity`)
- **Purpose**: Extract entities, sentiment, and categorize content
- **Tools**: comprehend
- **Output**: entities, sentiment, key_phrases, complaint_type
- **Use Case**: Identifies people, organizations, sentiment, and complaint category

## Builtin Query Agents

These agents answer natural language questions by analyzing stored data.

### 4. Who Agent (`builtin-query-who`)
- **Purpose**: Answer "who" questions about entities and actors
- **Tools**: retrieval_api, aggregation_api
- **Output**: entities, reporters, affected, answer
- **Example**: "Who reported the most complaints?"

### 5. What Agent (`builtin-query-what`)
- **Purpose**: Answer "what" questions about incident types
- **Tools**: retrieval_api, aggregation_api
- **Output**: incident_types, common_issues, summary, answer
- **Example**: "What are the most common complaints?"

### 6. Where Agent (`builtin-query-where`)
- **Purpose**: Answer "where" questions about locations
- **Tools**: spatial_api, retrieval_api
- **Output**: locations, hotspots, map_data (GeoJSON), answer
- **Example**: "Where are the potholes concentrated?"

### 7. When Agent (`builtin-query-when`)
- **Purpose**: Answer "when" questions about temporal patterns
- **Tools**: analytics_api, retrieval_api
- **Output**: time_pattern, frequency, trend, answer
- **Example**: "When do most complaints occur?"

### 8. Why Agent (`builtin-query-why`)
- **Purpose**: Answer "why" questions about causes
- **Tools**: analytics_api, retrieval_api
- **Output**: causes, factors, analysis, answer
- **Example**: "Why are there more complaints in winter?"

### 9. How Agent (`builtin-query-how`)
- **Purpose**: Answer "how" questions about methods/processes
- **Tools**: retrieval_api, analytics_api
- **Output**: methods, process, insights, answer
- **Example**: "How are complaints typically resolved?"

## Builtin Management Agents

These agents update existing data based on natural language commands.

### 10. Task Assigner (`builtin-management-task-assigner`)
- **Purpose**: Assign tasks to teams or users
- **Tools**: retrieval_api
- **Output**: assignee_id, assignee_type, assigned_at, reason
- **Example**: "Assign this to the roads team"

### 11. Status Updater (`builtin-management-status-updater`)
- **Purpose**: Update report status
- **Tools**: retrieval_api
- **Output**: status, updated_at, updated_by, notes
- **Example**: "Mark this as resolved"

### 12. Task Details Editor (`builtin-management-task-details-editor`)
- **Purpose**: Edit task details (priority, due date, etc)
- **Tools**: retrieval_api
- **Output**: field, value, updated_at, reason
- **Example**: "Set priority to high"

## Sample Domain: civic_complaints

A pre-configured domain for civic complaint management.

### Configuration

**Domain ID**: `civic_complaints`
**Domain Name**: Civic Complaints
**Description**: Citizen-reported infrastructure and service issues

### Playbooks

**Ingestion Playbook**:
- Agents: geo, temporal, entity (all run in parallel)
- Purpose: Extract location, time, and entities from complaint text

**Query Playbook**:
- Agents: who, what, where, when, why, how (all run in parallel)
- Purpose: Answer questions about complaints

**Management Playbook**:
- Agents: task_assigner, status_updater, task_details_editor (all run in parallel)
- Purpose: Update complaint status and assignments

### Example Usage

1. **Submit Report**: "There's a pothole on Main Street that appeared yesterday"
   - Geo agent extracts location
   - Temporal agent extracts timestamp
   - Entity agent categorizes as infrastructure complaint

2. **Query Data**: "Where are the most potholes?"
   - Where agent analyzes spatial patterns
   - Returns map with hotspots

3. **Manage Tasks**: "Assign this to the roads team"
   - Task assigner updates management_data
   - Sets assignee_id to roads team

## Seeding Methods

### Automatic (Recommended)
Builtin data is automatically seeded when `db_init.py` Lambda runs during stack deployment.

### Manual
Run the standalone seed script:
```bash
cd infrastructure
./scripts/seed-builtin-data.sh
```

### Programmatic
Import and call the seed function:
```python
from db_init import seed_builtin_data
seed_builtin_data(cursor, tenant_id, user_id)
```

## Verification

After seeding, verify with SQL:

```sql
-- Count builtin agents by class
SELECT agent_class, COUNT(*) 
FROM agent_definitions 
WHERE is_inbuilt = true 
GROUP BY agent_class;

-- Expected output:
-- ingestion  | 3
-- query      | 6
-- management | 3

-- Verify domain exists
SELECT domain_id, domain_name 
FROM domain_configurations 
WHERE domain_id = 'civic_complaints';
```

## Notes

- All builtin agents use `tenant_id` and `created_by` from the system tenant/user
- Builtin agents cannot be deleted through the API (protected by `is_inbuilt=true`)
- The seed operation is idempotent (uses `ON CONFLICT DO NOTHING`)
- Agents have no dependencies (all run in parallel within their playbooks)
- Output schemas are limited to 5 keys maximum (enforced by `max_output_keys=5`)

## Customization

To add custom agents:
1. Create agents through the Agent Management API
2. Set `is_inbuilt=false` (default)
3. Add to domain playbooks as needed

To modify builtin agents:
1. Update the seed data in `db_init.py` or `seed_builtin_data.json`
2. Re-run the seed script
3. Use `ON CONFLICT DO UPDATE` to overwrite existing agents
