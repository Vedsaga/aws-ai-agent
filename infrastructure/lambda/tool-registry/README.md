# Tool Registry Management System

This directory contains the Lambda functions for managing the tool registry and access control in the Multi-Agent Orchestration System.

## Components

### 1. Tool Registry (`tool_registry.py`)
Manages CRUD operations for the tool catalog in DynamoDB.

**Features:**
- Create, read, update, delete tools
- Support for built-in and custom tools
- Tool metadata validation
- Tool type categorization (aws_service, external_api, custom, data_api)

**API Endpoints:**
- `POST /tools` - Create new tool
- `GET /tools/{tool_name}` - Get tool details
- `PUT /tools/{tool_name}` - Update tool
- `DELETE /tools/{tool_name}` - Delete tool (custom only)
- `GET /tools?type={type}` - List tools by type

### 2. Tool Access Control (`tool-acl/tool_acl.py`)
Verifies agent permissions and returns tool metadata with credentials.

**Features:**
- Permission verification against DynamoDB
- In-memory caching (5-minute TTL)
- Credential retrieval from Secrets Manager
- Grant/revoke permissions

**API Endpoints:**
- `POST /tool-access/verify` - Verify tool access
- `POST /tool-access/grant` - Grant permission
- `DELETE /tool-access/revoke` - Revoke permission
- `GET /tool-access/list?agent_id={id}` - List agent permissions

### 3. Tool Proxies (`tool-proxies/`)
Proxy functions for accessing various tools with proper authentication.

**Proxies:**
- `bedrock_proxy.py` - AWS Bedrock (IAM auth)
- `comprehend_proxy.py` - AWS Comprehend (IAM auth)
- `location_proxy.py` - Amazon Location Service (IAM auth)
- `websearch_proxy.py` - Web Search API (API key from Secrets Manager)
- `custom_api_proxy.py` - Custom APIs (user credentials from Secrets Manager)

### 4. Data API Proxies (`data-api-proxies/`)
Proxy functions for internal data access APIs.

**Proxies:**
- `retrieval_proxy.py` - Incident retrieval with filters
- `aggregation_proxy.py` - Statistics and summaries
- `spatial_proxy.py` - Geospatial queries (PostGIS)
- `analytics_proxy.py` - Trend detection and pattern recognition
- `vector_search_proxy.py` - Semantic similarity search (OpenSearch)

## Built-in Tools

The system includes 9 built-in tools (see `seed_tools.json`):

1. **bedrock** - AWS Bedrock for LLM capabilities
2. **comprehend** - AWS Comprehend for NLP
3. **location_service** - Amazon Location Service for geocoding
4. **web_search** - External web search API
5. **retrieval_api** - Internal data retrieval
6. **aggregation_api** - Internal data aggregation
7. **spatial_api** - Internal spatial queries
8. **analytics_api** - Internal analytics
9. **vector_search** - Internal vector search

## Database Schema

### DynamoDB: tool_catalog
```
Partition Key: tool_name (String)

Attributes:
- tool_type (String): aws_service|external_api|custom|data_api
- endpoint (String): Service endpoint or identifier
- auth_method (String): iam|api_key|oauth|custom|none
- description (String): Tool description
- parameters_schema (Map): Expected parameters
- is_builtin (Boolean): Whether tool is built-in
- created_at (Number): Creation timestamp
- updated_at (Number): Last update timestamp
```

### DynamoDB: tool_permissions
```
Partition Key: tenant_agent_id (String) - Format: "{tenant_id}#{agent_id}"
Sort Key: tool_name (String)

Attributes:
- tenant_id (String): Tenant identifier
- agent_id (String): Agent identifier
- allowed (Boolean): Permission status
- granted_at (Number): Grant timestamp
```

## Usage Examples

### Register a Custom Tool
```python
import boto3
import json

lambda_client = boto3.client('lambda')

tool_data = {
    "tool_name": "weather_api",
    "tool_type": "external_api",
    "endpoint": "https://api.weather.com/v1",
    "auth_method": "api_key",
    "description": "Weather data API",
    "parameters_schema": {
        "location": "string (required)",
        "units": "string (optional: metric|imperial)"
    }
}

response = lambda_client.invoke(
    FunctionName='tool-registry',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'httpMethod': 'POST',
        'path': '/tools',
        'body': json.dumps(tool_data)
    })
)
```

### Grant Tool Permission to Agent
```python
permission_data = {
    "tenant_id": "tenant-123",
    "agent_id": "geo-agent",
    "tool_name": "location_service"
}

response = lambda_client.invoke(
    FunctionName='tool-acl',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'httpMethod': 'POST',
        'path': '/tool-access/grant',
        'body': json.dumps(permission_data)
    })
)
```

### Verify Tool Access
```python
verify_data = {
    "tenant_id": "tenant-123",
    "agent_id": "geo-agent",
    "tool_name": "location_service",
    "include_credentials": True
}

response = lambda_client.invoke(
    FunctionName='tool-acl',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'httpMethod': 'POST',
        'path': '/tool-access/verify',
        'body': json.dumps(verify_data)
    })
)
```

## Environment Variables

### Tool Registry
- `TOOL_CATALOG_TABLE` - DynamoDB table name for tool catalog

### Tool ACL
- `TOOL_CATALOG_TABLE` - DynamoDB table name for tool catalog
- `TOOL_PERMISSIONS_TABLE` - DynamoDB table name for permissions

### Tool Proxies
- `BEDROCK_MODEL_ID` - Default Bedrock model ID
- `PLACE_INDEX_NAME` - Location Service place index name
- `ROUTE_CALCULATOR_NAME` - Location Service route calculator name
- `SEARCH_API_SECRET_NAME` - Secrets Manager secret for web search API

### Data API Proxies
- `DB_HOST` - PostgreSQL host
- `DB_PORT` - PostgreSQL port
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `OPENSEARCH_ENDPOINT` - OpenSearch endpoint
- `OPENSEARCH_INDEX` - OpenSearch index name
- `EMBEDDING_MODEL_ID` - Bedrock embedding model ID

## Security Considerations

1. **IAM Roles**: All Lambda functions use IAM roles for AWS service access
2. **Secrets Manager**: External API credentials stored in Secrets Manager
3. **Tenant Isolation**: All operations enforce tenant_id filtering
4. **Permission Checks**: Tool access verified before every invocation
5. **Caching**: 5-minute TTL on permission cache to balance performance and security

## Deployment

These Lambda functions are deployed via AWS CDK as part of the infrastructure stack. See `infrastructure/lib/stacks/` for CDK definitions.

## Testing

Test the tool registry locally:
```bash
cd infrastructure/lambda/tool-registry
python -c "
import json
from tool_registry import create_tool, get_tool, list_tools

# Test create
tool = create_tool({
    'tool_name': 'test_tool',
    'tool_type': 'custom',
    'endpoint': 'https://example.com',
    'auth_method': 'api_key',
    'description': 'Test tool'
})
print('Created:', json.dumps(tool, indent=2))

# Test get
tool = get_tool('test_tool')
print('Retrieved:', json.dumps(tool, indent=2))

# Test list
tools = list_tools()
print('All tools:', len(tools))
"
```

## Requirements

See `requirements.txt` in each directory for Python dependencies.
