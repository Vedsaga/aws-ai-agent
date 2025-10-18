# Configuration API

This Lambda function handles CRUD operations for all configuration types in the Multi-Agent Orchestration System.

## Configuration Types

### 1. Agent Configurations
- **Purpose**: Define AI agents with system prompts, tools, and output schemas
- **Validation**: 
  - Max 5 keys in output schema
  - Single-level dependency (one parent only)
  - Valid agent types: ingestion, query, custom
  - Valid interrogatives for query agents

### 2. Playbook Configurations
- **Purpose**: Define which agents to execute for a domain
- **Validation**:
  - All agent_ids must exist
  - Valid playbook types: ingestion, query
  - Must be linked to a domain_id

### 3. Dependency Graph Configurations
- **Purpose**: Define execution order and dependencies between agents
- **Validation**:
  - No circular dependencies
  - Single-level dependencies only (each agent has max 1 parent)
  - All agents must exist in the associated playbook
  - Generates execution levels via topological sort

### 4. Domain Templates
- **Purpose**: Pre-built configurations for common use cases
- **Includes**: Agent configs, playbook configs, dependency graphs, UI templates
- **Built-in Templates**: Civic Complaints, Disaster Response, Agriculture

## API Endpoints

### Create Configuration
```
POST /api/v1/config
{
  "type": "agent|playbook|dependency_graph|domain_template",
  "config": { ... }
}
```

### Get Configuration
```
GET /api/v1/config/{type}/{id}
```

### List Configurations
```
GET /api/v1/config?type={type}
```

### Update Configuration
```
PUT /api/v1/config/{type}/{id}
{
  "config": { ... }
}
```

### Delete Configuration
```
DELETE /api/v1/config/{type}/{id}
```

## Features

### Versioning
- All configurations are versioned
- Version number increments on each update
- Previous versions backed up to S3

### S3 Backup
- Automatic backup to S3 before updates/deletes
- Backup path: `{tenant_id}/{config_type}/{id}_v{version}_{timestamp}_{status}.json`
- Retention: 365 days (configurable via S3 lifecycle policy)

### Validation
- Schema validation before saving
- Cross-reference validation (agents exist in playbooks, etc.)
- Circular dependency detection
- Single-level dependency enforcement

### Tenant Isolation
- All configurations partitioned by tenant_id
- No cross-tenant access
- Tenant_id extracted from JWT token

## Manager Classes

### AgentConfigManager
- Validates output schema (max 5 keys)
- Validates single-level dependencies
- Validates interrogatives for query agents
- Backs up to S3: `{tenant_id}/agents/{agent_id}_v{version}_{timestamp}_{status}.json`

### PlaybookConfigManager
- Validates agent existence
- Validates playbook type
- Links to domain_id
- Backs up to S3: `{tenant_id}/playbooks/{playbook_id}_v{version}_{timestamp}_{status}.json`

### DependencyGraphManager
- Detects circular dependencies using DFS
- Validates single-level dependencies
- Generates execution levels via topological sort
- Validates all agents exist in playbook
- Backs up to S3: `{tenant_id}/dependency_graphs/{graph_id}_v{version}_{timestamp}_{status}.json`

### DomainTemplateManager
- Manages pre-built domain templates
- Instantiates templates for new tenants
- Maps template agent IDs to new agent IDs
- Creates agents, playbooks, and dependency graphs from template
- Backs up to S3: `{tenant_id}/domain_templates/{template_id}_v{version}_{timestamp}_{status}.json`

## Environment Variables

- `CONFIGURATIONS_TABLE`: DynamoDB table name for configurations
- `CONFIG_BACKUP_BUCKET`: S3 bucket name for configuration backups

## DynamoDB Schema

### Configurations Table
```
Partition Key: tenant_id (String)
Sort Key: config_key (String)

config_key format:
- agent#{agent_id}
- playbook#{playbook_id}
- dependency_graph#{graph_id}
- domain_template#{template_id}

Attributes:
- config_type: agent|playbook|dependency_graph|domain_template
- version: Number
- created_at: Number (timestamp)
- updated_at: Number (timestamp)
- created_by: String (user_id)
- updated_by: String (user_id)
- ... (type-specific fields)
```

## Error Handling

### Validation Errors (400)
- Missing required fields
- Invalid field values
- Schema violations
- Circular dependencies
- Multi-level dependencies

### Not Found Errors (404)
- Configuration not found
- Referenced agent/playbook not found

### Authorization Errors (401/403)
- Missing tenant_id
- Tenant mismatch

### Internal Errors (500)
- DynamoDB errors
- S3 backup errors (logged but don't fail operation)

## Example Usage

### Create Agent
```json
POST /api/v1/config
{
  "type": "agent",
  "config": {
    "agent_name": "Severity Classifier",
    "agent_type": "custom",
    "system_prompt": "Classify the severity of incidents on a scale of 1-10",
    "tools": ["bedrock"],
    "output_schema": {
      "severity": "number",
      "reasoning": "string",
      "urgency": "string",
      "recommended_action": "string"
    },
    "dependency_parent": "entity_agent_id"
  }
}
```

### Create Playbook
```json
POST /api/v1/config
{
  "type": "playbook",
  "config": {
    "domain_id": "civic_complaints",
    "playbook_type": "ingestion",
    "agent_ids": ["geo_agent_id", "temporal_agent_id", "entity_agent_id"],
    "description": "Ingestion pipeline for civic complaints"
  }
}
```

### Create Dependency Graph
```json
POST /api/v1/config
{
  "type": "dependency_graph",
  "config": {
    "playbook_id": "playbook_id",
    "edges": [
      {"from": "entity_agent_id", "to": "severity_classifier_id"}
    ]
  }
}
```

### Instantiate Domain Template
```json
POST /api/v1/config
{
  "type": "domain_template",
  "config": {
    "template_name": "Civic Complaints",
    "domain_id": "civic_complaints",
    "agent_configs": [...],
    "playbook_configs": [...],
    "dependency_graph_configs": [...]
  }
}
```

## Testing

### Unit Tests
- Validation logic for each config type
- Circular dependency detection
- Single-level dependency validation
- Topological sort for execution levels

### Integration Tests
- Create/Read/Update/Delete operations
- S3 backup verification
- DynamoDB versioning
- Cross-reference validation

## Performance

- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Cold Start**: ~2 seconds
- **Warm Execution**: ~100-500ms

## Monitoring

- CloudWatch Logs: All operations logged with tenant_id and config_id
- CloudWatch Metrics: Invocation count, duration, errors
- X-Ray Tracing: End-to-end request tracing

## Security

- JWT token validation via API Gateway authorizer
- Tenant isolation via partition key
- S3 encryption at rest (AES256)
- DynamoDB encryption at rest
- IAM role with least privilege access
