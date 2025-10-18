# Configuration API Examples

Quick reference for using the Configuration API endpoints.

## Authentication

All requests require a JWT token in the Authorization header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The JWT token must contain:
- `tenant_id`: Tenant identifier
- `user_id`: User identifier

## Agent Configuration

### Create Agent
```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Severity Classifier",
      "agent_type": "custom",
      "system_prompt": "Classify the severity of incidents on a scale of 1-10 based on the description and context.",
      "tools": ["bedrock"],
      "output_schema": {
        "severity": "number",
        "reasoning": "string",
        "urgency": "string",
        "recommended_action": "string"
      },
      "dependency_parent": "entity_agent_id"
    }
  }'
```

### Get Agent
```bash
curl -X GET https://api.example.com/api/v1/config/agent/{agent_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### List All Agents
```bash
curl -X GET "https://api.example.com/api/v1/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Update Agent
```bash
curl -X PUT https://api.example.com/api/v1/config/agent/{agent_id} \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agent_name": "Severity Classifier v2",
      "agent_type": "custom",
      "system_prompt": "Updated prompt...",
      "tools": ["bedrock", "comprehend"],
      "output_schema": {
        "severity": "number",
        "reasoning": "string",
        "urgency": "string",
        "recommended_action": "string",
        "confidence": "number"
      }
    }
  }'
```

### Delete Agent
```bash
curl -X DELETE https://api.example.com/api/v1/config/agent/{agent_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Playbook Configuration

### Create Playbook
```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "playbook",
    "config": {
      "domain_id": "civic_complaints",
      "playbook_type": "ingestion",
      "agent_ids": [
        "geo_agent_id",
        "temporal_agent_id",
        "entity_agent_id",
        "severity_classifier_id"
      ],
      "description": "Ingestion pipeline for civic complaints with severity classification"
    }
  }'
```

### Get Playbook
```bash
curl -X GET https://api.example.com/api/v1/config/playbook/{playbook_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### List All Playbooks
```bash
curl -X GET "https://api.example.com/api/v1/config?type=playbook" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Update Playbook
```bash
curl -X PUT https://api.example.com/api/v1/config/playbook/{playbook_id} \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "domain_id": "civic_complaints",
      "playbook_type": "ingestion",
      "agent_ids": [
        "geo_agent_id",
        "temporal_agent_id",
        "entity_agent_id"
      ],
      "description": "Updated playbook"
    }
  }'
```

### Delete Playbook
```bash
curl -X DELETE https://api.example.com/api/v1/config/playbook/{playbook_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Dependency Graph Configuration

### Create Dependency Graph
```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "dependency_graph",
    "config": {
      "playbook_id": "playbook_id",
      "edges": [
        {
          "from": "entity_agent_id",
          "to": "severity_classifier_id"
        },
        {
          "from": "temporal_agent_id",
          "to": "priority_scorer_id"
        }
      ]
    }
  }'
```

**Note**: Each agent can have at most one parent (single-level dependency).

### Get Dependency Graph
```bash
curl -X GET https://api.example.com/api/v1/config/dependency_graph/{graph_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### List All Dependency Graphs
```bash
curl -X GET "https://api.example.com/api/v1/config?type=dependency_graph" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Update Dependency Graph
```bash
curl -X PUT https://api.example.com/api/v1/config/dependency_graph/{graph_id} \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "playbook_id": "playbook_id",
      "edges": [
        {
          "from": "entity_agent_id",
          "to": "severity_classifier_id"
        }
      ]
    }
  }'
```

### Delete Dependency Graph
```bash
curl -X DELETE https://api.example.com/api/v1/config/dependency_graph/{graph_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Domain Template Configuration

### Create Domain Template
```bash
curl -X POST https://api.example.com/api/v1/config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "domain_template",
    "config": {
      "template_name": "Custom Domain",
      "domain_id": "custom_domain",
      "description": "Custom domain template",
      "agent_configs": [
        {
          "agent_name": "Custom Agent",
          "agent_type": "ingestion",
          "system_prompt": "Extract custom information",
          "tools": ["bedrock"],
          "output_schema": {
            "field1": "string",
            "field2": "number"
          }
        }
      ],
      "playbook_configs": [
        {
          "playbook_type": "ingestion",
          "agent_ids": ["custom_agent"],
          "description": "Custom ingestion pipeline"
        }
      ],
      "dependency_graph_configs": [],
      "ui_template": {}
    }
  }'
```

### Get Domain Template
```bash
curl -X GET https://api.example.com/api/v1/config/domain_template/{template_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### List All Domain Templates
```bash
curl -X GET "https://api.example.com/api/v1/config?type=domain_template" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Update Domain Template
```bash
curl -X PUT https://api.example.com/api/v1/config/domain_template/{template_id} \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "template_name": "Updated Template",
      "domain_id": "custom_domain",
      "description": "Updated description",
      "agent_configs": [...],
      "playbook_configs": [...]
    }
  }'
```

### Delete Domain Template
```bash
curl -X DELETE https://api.example.com/api/v1/config/domain_template/{template_id} \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Response Formats

### Success Response (200/201)
```json
{
  "tenant_id": "tenant-123",
  "config_key": "agent#agent-456",
  "config_type": "agent",
  "agent_id": "agent-456",
  "agent_name": "Severity Classifier",
  "version": 1,
  "created_at": 1698765432,
  "updated_at": 1698765432,
  ...
}
```

### List Response (200)
```json
{
  "configs": [
    {
      "tenant_id": "tenant-123",
      "config_key": "agent#agent-456",
      ...
    },
    {
      "tenant_id": "tenant-123",
      "config_key": "agent#agent-789",
      ...
    }
  ],
  "count": 2
}
```

### Error Response (400/404/500)
```json
{
  "error": "Missing required field: agent_name",
  "timestamp": "2024-10-31T12:34:56.789Z"
}
```

## Common Error Messages

### Validation Errors (400)
- `"Missing required field: {field_name}"`
- `"Invalid agent_type: {type}. Must be one of ['ingestion', 'query', 'custom']"`
- `"output_schema cannot have more than 5 keys. Found {count} keys"`
- `"Circular dependency detected"`
- `"Multi-level dependencies detected. Each agent can only depend on one parent agent"`
- `"Agent not found: {agent_id}"`
- `"Playbook not found: {playbook_id}"`

### Not Found Errors (404)
- `"Configuration not found: {type}/{id}"`

### Authorization Errors (401)
- `"Unauthorized: Missing tenant_id"`

## Built-in Domain Templates

The system includes three pre-built domain templates:

### 1. Civic Complaints
```bash
# Get built-in template
curl -X GET "https://api.example.com/api/v1/config?type=domain_template" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

Includes:
- Geo Agent (location extraction)
- Temporal Agent (time extraction)
- Entity Agent (entity and sentiment extraction)

### 2. Disaster Response
Includes:
- Geo Agent (location extraction)
- Severity Agent (severity assessment)

### 3. Agriculture
Includes:
- Crop Agent (crop information extraction)
- Geo Agent (farm location extraction)

## Testing with Postman

1. Import the API endpoints into Postman
2. Set up environment variables:
   - `BASE_URL`: https://api.example.com
   - `JWT_TOKEN`: Your JWT token
3. Use `{{BASE_URL}}` and `{{JWT_TOKEN}}` in requests
4. Test CRUD operations for each config type

## Python SDK Example

```python
import requests
import json

BASE_URL = "https://api.example.com/api/v1"
JWT_TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Create agent
agent_config = {
    "type": "agent",
    "config": {
        "agent_name": "Test Agent",
        "agent_type": "custom",
        "system_prompt": "Test prompt",
        "tools": ["bedrock"],
        "output_schema": {
            "result": "string"
        }
    }
}

response = requests.post(
    f"{BASE_URL}/config",
    headers=headers,
    json=agent_config
)

print(response.json())
```

## Notes

- All timestamps are Unix timestamps (seconds since epoch)
- All IDs are UUIDs (auto-generated if not provided)
- Configurations are versioned automatically on updates
- Previous versions are backed up to S3 before updates/deletes
- All operations are scoped to the tenant_id from the JWT token
