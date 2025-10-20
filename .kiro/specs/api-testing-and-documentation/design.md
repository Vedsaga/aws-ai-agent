# Design Document

## Overview

This design document outlines the approach for comprehensive API testing, documentation, and validation of the Multi-Agent Orchestration System. With less than 6 hours remaining before hackathon submission, the focus is on creating a complete API reference, automated test suite, and gap analysis to maximize Technical Execution (50%) and Functionality (10%) scores.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Testing System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API Docs   │  │  Test Suite  │  │ Gap Analysis │      │
│  │   Generator  │  │   Runner     │  │   Tool       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│              ┌──────────────────────────┐                    │
│              │   API Reference Doc      │                    │
│              │   + Test Report          │                    │
│              │   + Gap Analysis Report  │                    │
│              └──────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend APIs (Existing)                     │
├─────────────────────────────────────────────────────────────┤
│  Config API  │  Data API  │  Ingest API  │  Query API       │
└─────────────────────────────────────────────────────────────┘
```

### Testing Strategy

1. **API Documentation Generator**: Analyze existing Lambda handlers to extract endpoint definitions
2. **Automated Test Suite**: Execute comprehensive tests against all endpoints
3. **Gap Analysis Tool**: Compare expected vs. actual functionality
4. **Demo Script Generator**: Create step-by-step demo with curl commands


## Components and Interfaces

### 1. API Documentation Generator

**Purpose**: Generate comprehensive API reference from existing code

**Input**:
- Lambda handler Python files
- Existing API_EXAMPLES.md files
- OpenAPI/Swagger definitions (if available)

**Output**:
- `API_REFERENCE.md`: Complete API documentation
- Organized by endpoint category
- Includes request/response schemas
- Includes authentication requirements
- Includes error codes and examples

**Key Functions**:
```python
def extract_endpoints(handler_file: str) -> List[Endpoint]:
    """Parse Lambda handler to extract endpoint definitions"""
    
def generate_request_schema(endpoint: Endpoint) -> Dict:
    """Generate JSON schema for request body"""
    
def generate_response_schema(endpoint: Endpoint) -> Dict:
    """Generate JSON schema for response body"""
    
def generate_markdown_doc(endpoints: List[Endpoint]) -> str:
    """Generate formatted Markdown documentation"""
```

### 2. Automated Test Suite

**Purpose**: Execute comprehensive tests against all API endpoints

**Test Categories**:
- **Smoke Tests**: Basic connectivity and authentication
- **CRUD Tests**: Create, Read, Update, Delete operations
- **Validation Tests**: Input validation and error handling
- **Edge Case Tests**: Boundary conditions and special cases
- **Performance Tests**: Response time measurements

**Test Framework**: Python with `requests` library

**Key Functions**:
```python
def test_config_api_create_agent():
    """Test creating a custom agent"""
    
def test_config_api_list_agents():
    """Test listing all agents"""
    
def test_data_api_retrieval():
    """Test retrieving incidents"""
    
def test_ingest_api_submit_report():
    """Test submitting a report"""
    
def test_query_api_ask_question():
    """Test asking a question"""
```


### 3. Gap Analysis Tool

**Purpose**: Identify missing or incomplete API functionality

**Analysis Areas**:
- Missing endpoints
- Incomplete implementations
- Missing error handling
- Missing validation
- Missing documentation

**Output**: `GAP_ANALYSIS.md` with prioritized action items

**Key Functions**:
```python
def analyze_endpoint_coverage() -> Dict:
    """Compare expected vs. actual endpoints"""
    
def analyze_error_handling() -> List[Issue]:
    """Check error handling completeness"""
    
def analyze_validation() -> List[Issue]:
    """Check input validation completeness"""
    
def prioritize_gaps(gaps: List[Gap]) -> List[Gap]:
    """Prioritize by severity and demo impact"""
```

### 4. Demo Script Generator

**Purpose**: Create step-by-step demo script for judges

**Output**: `DEMO_SCRIPT.md` with curl commands and expected responses

**Demo Flow**:
1. Authentication (get JWT token)
2. Create custom agent
3. Create custom domain
4. Submit report
5. Ask question
6. Retrieve data

**Key Functions**:
```python
def generate_demo_step(step: DemoStep) -> str:
    """Generate Markdown for demo step with curl command"""
    
def generate_expected_response(endpoint: Endpoint) -> str:
    """Generate example response for demo"""
```


## Data Models

### Endpoint Definition

```python
@dataclass
class Endpoint:
    method: str  # GET, POST, PUT, DELETE
    path: str  # /api/v1/config
    description: str
    auth_required: bool
    request_schema: Dict
    response_schema: Dict
    error_codes: List[int]
    examples: List[Example]
```

### Test Result

```python
@dataclass
class TestResult:
    test_name: str
    endpoint: str
    status: str  # PASS, FAIL, SKIP
    response_time_ms: int
    error_message: Optional[str]
    request: Dict
    response: Dict
```

### Gap

```python
@dataclass
class Gap:
    category: str  # missing_endpoint, incomplete_impl, missing_validation
    severity: str  # critical, high, medium, low
    description: str
    affected_endpoint: str
    estimated_fix_time_hours: float
    demo_blocking: bool
```

### Demo Step

```python
@dataclass
class DemoStep:
    step_number: int
    title: str
    description: str
    curl_command: str
    expected_response: str
    timing_estimate_seconds: int
```


## API Endpoint Inventory

### Config API (`/api/v1/config`)

**Handler**: `infrastructure/lambda/config-api/config_handler.py`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/v1/config` | Create configuration | Yes | ✅ Implemented |
| GET | `/api/v1/config/{type}/{id}` | Get configuration | Yes | ✅ Implemented |
| GET | `/api/v1/config?type={type}` | List configurations | Yes | ✅ Implemented |
| PUT | `/api/v1/config/{type}/{id}` | Update configuration | Yes | ✅ Implemented |
| DELETE | `/api/v1/config/{type}/{id}` | Delete configuration | Yes | ✅ Implemented |

**Configuration Types**:
- `agent`: Agent configurations
- `playbook`: Playbook configurations
- `dependency_graph`: Dependency graph configurations
- `domain_template`: Domain template configurations

### Data API (`/api/v1/data`)

**Handlers**: `infrastructure/lambda/data-api-proxies/*.py`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/data?type=retrieval` | Retrieve incidents | Yes | ✅ Implemented |
| GET | `/api/v1/data?type=spatial` | Spatial queries | Yes | ✅ Implemented |
| GET | `/api/v1/data?type=analytics` | Analytics queries | Yes | ✅ Implemented |
| GET | `/api/v1/data?type=aggregation` | Aggregation queries | Yes | ✅ Implemented |
| GET | `/api/v1/data?type=vector_search` | Vector search | Yes | ✅ Implemented |

### Ingest API (`/api/v1/ingest`)

**Handler**: `infrastructure/lambda/orchestration/` (Step Functions)

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/v1/ingest` | Submit report | Yes | ✅ Implemented |

### Query API (`/api/v1/query`)

**Handler**: `infrastructure/lambda/orchestration/` (Step Functions)

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/v1/query` | Ask question | Yes | ✅ Implemented |

### Tool Registry API (`/api/v1/tools`)

**Handler**: `infrastructure/lambda/tool-registry/tool_registry.py`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/tools` | List all tools | Yes | ✅ Implemented |
| GET | `/api/v1/tools/{tool_id}` | Get tool details | Yes | ✅ Implemented |

### Real-time API (AppSync GraphQL)

**Handler**: `infrastructure/lambda/realtime/status_publisher.py`

| Type | Operation | Description | Auth | Status |
|------|-----------|-------------|------|--------|
| Subscription | `onStatusUpdate` | Real-time status updates | Yes | ✅ Implemented |
| Mutation | `publishStatus` | Publish status update | Yes | ✅ Implemented |


## Request/Response Schemas

### Config API - Create Agent

**Request**:
```json
{
  "type": "agent",
  "config": {
    "agent_name": "string (required, max 100 chars)",
    "agent_type": "string (required, enum: ingestion|query|custom)",
    "system_prompt": "string (required, max 2000 chars)",
    "tools": ["string"] (required, array of tool IDs),
    "output_schema": {
      "field1": "type",
      "field2": "type"
    } (required, max 5 keys),
    "dependency_parent": "string (optional, agent ID)",
    "api_endpoint": "string (optional, URL)",
    "example_output": "object (optional)"
  }
}
```

**Response (201)**:
```json
{
  "tenant_id": "string",
  "config_key": "string",
  "config_type": "agent",
  "agent_id": "string (UUID)",
  "agent_name": "string",
  "agent_type": "string",
  "version": 1,
  "created_at": 1698765432,
  "updated_at": 1698765432,
  "created_by": "string (user_id)",
  "is_builtin": false,
  ...
}
```

**Error Responses**:
- `400`: Missing required fields, invalid data types, validation errors
- `401`: Missing or invalid JWT token
- `500`: Internal server error

### Config API - List Agents

**Request**:
```
GET /api/v1/config?type=agent
Authorization: Bearer {JWT_TOKEN}
```

**Response (200)**:
```json
{
  "configs": [
    {
      "agent_id": "string",
      "agent_name": "string",
      "agent_type": "string",
      "is_builtin": boolean,
      "created_by_me": boolean,
      ...
    }
  ],
  "count": number
}
```


### Ingest API - Submit Report

**Request**:
```json
{
  "domain_id": "string (required)",
  "text": "string (required, max 10000 chars)",
  "images": ["string (base64)"] (optional, max 5 images, 5MB each),
  "metadata": {
    "source": "string (optional)",
    "priority": "string (optional)"
  } (optional)
}
```

**Response (202)**:
```json
{
  "job_id": "string (UUID)",
  "status": "processing",
  "message": "Report submitted successfully",
  "timestamp": "2024-10-31T12:34:56.789Z"
}
```

**Error Responses**:
- `400`: Missing domain_id, invalid text length, too many images
- `401`: Missing or invalid JWT token
- `404`: Domain not found
- `500`: Internal server error

### Query API - Ask Question

**Request**:
```json
{
  "domain_id": "string (required)",
  "question": "string (required, max 1000 chars)",
  "filters": {
    "date_range": {
      "start": "ISO8601 date",
      "end": "ISO8601 date"
    },
    "location": {
      "bbox": [lon_min, lat_min, lon_max, lat_max]
    },
    "category": "string"
  } (optional)
}
```

**Response (202)**:
```json
{
  "job_id": "string (UUID)",
  "status": "processing",
  "message": "Query submitted successfully",
  "timestamp": "2024-10-31T12:34:56.789Z"
}
```

**Error Responses**:
- `400`: Missing domain_id, invalid question length
- `401`: Missing or invalid JWT token
- `404`: Domain not found
- `500`: Internal server error


### Data API - Retrieve Incidents

**Request**:
```
GET /api/v1/data?type=retrieval&filters={...}
Authorization: Bearer {JWT_TOKEN}
```

**Query Parameters**:
- `type`: "retrieval" (required)
- `filters`: JSON string with filter criteria (optional)
  - `date_range`: `{"start": "ISO8601", "end": "ISO8601"}`
  - `location`: `{"bbox": [lon_min, lat_min, lon_max, lat_max]}`
  - `category`: string
  - `custom_fields`: object with field filters

**Response (200)**:
```json
{
  "incidents": [
    {
      "incident_id": "string (UUID)",
      "domain_id": "string",
      "text": "string",
      "structured_data": {
        "location": {...},
        "timestamp": {...},
        "category": {...},
        ...
      },
      "confidence_scores": {
        "geo_agent": 0.95,
        "temporal_agent": 0.87,
        ...
      },
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "count": number,
  "pagination": {
    "page": number,
    "page_size": number,
    "total_pages": number,
    "total_count": number
  }
}
```

### Real-time API - Status Update Subscription

**GraphQL Subscription**:
```graphql
subscription OnStatusUpdate($jobId: ID!) {
  onStatusUpdate(jobId: $jobId) {
    jobId
    agentName
    status
    message
    confidence
    timestamp
  }
}
```

**Status Messages**:
- `loading_agents`: Loading playbook configuration
- `invoking_{agent_name}`: Agent starting execution
- `calling_{tool_name}`: Tool invocation in progress
- `agent_complete_{agent_name}`: Agent finished with confidence score
- `validating`: Validation in progress
- `synthesizing`: Synthesis in progress
- `complete`: Job complete
- `error`: Error occurred with details


## Error Handling

### Error Response Format

All error responses follow this structure:

```json
{
  "error": "string (human-readable error message)",
  "timestamp": "ISO8601 timestamp",
  "error_code": "string (optional, machine-readable code)",
  "details": {
    "field": "string (optional, field that caused error)",
    "constraint": "string (optional, constraint violated)"
  } (optional)
}
```

### HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Async operation started (Ingest, Query) |
| 400 | Bad Request | Invalid input, validation errors |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists, version conflict |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Temporary service outage |

### Common Error Codes

```python
ERROR_CODES = {
    "MISSING_FIELD": "Required field is missing",
    "INVALID_TYPE": "Field has invalid data type",
    "INVALID_VALUE": "Field value is not allowed",
    "TOO_LONG": "Field exceeds maximum length",
    "TOO_SHORT": "Field is below minimum length",
    "TOO_MANY": "Too many items in array",
    "NOT_FOUND": "Resource not found",
    "ALREADY_EXISTS": "Resource already exists",
    "CIRCULAR_DEPENDENCY": "Circular dependency detected",
    "MULTI_LEVEL_DEPENDENCY": "Multi-level dependencies not allowed",
    "INVALID_PARENT": "Parent agent not found or invalid",
    "INVALID_TOOL": "Tool not found or not available",
    "INVALID_DOMAIN": "Domain not found",
    "UNAUTHORIZED": "Authentication required",
    "FORBIDDEN": "Insufficient permissions",
    "RATE_LIMIT": "Rate limit exceeded",
    "INTERNAL_ERROR": "Internal server error"
}
```


## Testing Strategy

### Test Execution Flow

```
1. Setup
   ├── Load environment variables (API_URL, JWT_TOKEN)
   ├── Initialize test database state
   └── Create test fixtures

2. Smoke Tests (2 min)
   ├── Test API connectivity
   ├── Test authentication
   └── Test basic GET requests

3. Config API Tests (10 min)
   ├── Test agent CRUD operations
   ├── Test domain CRUD operations
   ├── Test playbook CRUD operations
   └── Test dependency graph CRUD operations

4. Data API Tests (5 min)
   ├── Test retrieval endpoint
   ├── Test spatial queries
   ├── Test analytics queries
   └── Test pagination

5. Ingest API Tests (5 min)
   ├── Test text-only report
   ├── Test report with images
   ├── Test invalid inputs
   └── Test real-time status updates

6. Query API Tests (5 min)
   ├── Test simple question
   ├── Test complex question
   ├── Test invalid inputs
   └── Test real-time status updates

7. Edge Case Tests (5 min)
   ├── Test missing required fields
   ├── Test invalid data types
   ├── Test boundary values
   └── Test special characters

8. Performance Tests (3 min)
   ├── Measure response times
   ├── Test concurrent requests
   └── Test pagination performance

9. Teardown
   ├── Clean up test data
   └── Generate test report

Total: ~35 minutes
```

### Test Data Fixtures

```python
# Test agent configuration
TEST_AGENT = {
    "agent_name": "Test Agent",
    "agent_type": "custom",
    "system_prompt": "Test prompt",
    "tools": ["bedrock"],
    "output_schema": {
        "result": "string",
        "confidence": "number"
    }
}

# Test domain configuration
TEST_DOMAIN = {
    "template_name": "Test Domain",
    "domain_id": "test_domain",
    "ingest_agent_ids": ["geo_agent", "temporal_agent"],
    "query_agent_ids": ["when_agent", "where_agent"],
    "description": "Test domain for automated testing"
}

# Test report
TEST_REPORT = {
    "domain_id": "civic_complaints",
    "text": "There is a pothole on Main Street near the library",
    "images": []
}

# Test query
TEST_QUERY = {
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints this month?"
}
```


## Validation Rules

### Client-Side Validation

These validations should be performed in the frontend before API calls:

**Agent Configuration**:
- `agent_name`: Required, 1-100 characters, alphanumeric + spaces
- `agent_type`: Required, must be "ingestion", "query", or "custom"
- `system_prompt`: Required, 1-2000 characters
- `tools`: Required, array with at least 1 tool
- `output_schema`: Required, object with 1-5 keys
- `dependency_parent`: Optional, must be valid agent ID if provided

**Domain Configuration**:
- `template_name`: Required, 1-100 characters
- `domain_id`: Required, 1-50 characters, lowercase alphanumeric + underscores
- `ingest_agent_ids`: Required, array with at least 1 agent ID
- `query_agent_ids`: Required, array with at least 1 agent ID
- `description`: Optional, max 500 characters

**Report Submission**:
- `domain_id`: Required, must exist
- `text`: Required, 1-10000 characters
- `images`: Optional, max 5 images, each max 5MB, base64 encoded

**Query Submission**:
- `domain_id`: Required, must exist
- `question`: Required, 1-1000 characters

### Server-Side Validation

These validations are performed by the backend:

**Agent Configuration**:
- Validate agent_type is one of allowed values
- Validate tools exist in tool registry
- Validate output_schema has max 5 keys
- Validate dependency_parent exists and doesn't create circular dependency
- Validate no multi-level dependencies

**Domain Configuration**:
- Validate domain_id is unique
- Validate all agent IDs exist
- Validate at least one ingestion agent
- Validate at least one query agent

**Report Submission**:
- Validate domain exists
- Validate text length
- Validate image count and size
- Validate image format (base64)

**Query Submission**:
- Validate domain exists
- Validate question length
- Validate filter parameters if provided


## Implementation Plan

### Phase 1: API Documentation (1.5 hours)

**Goal**: Create comprehensive API reference document

**Tasks**:
1. Create `API_REFERENCE.md` with table of contents
2. Document Config API endpoints with schemas
3. Document Data API endpoints with schemas
4. Document Ingest API endpoint with schema
5. Document Query API endpoint with schema
6. Document Tool Registry API endpoints
7. Document Real-time API subscriptions
8. Add authentication section
9. Add error codes reference
10. Add code examples (curl, JavaScript, Python)

**Output**: `API_REFERENCE.md` (complete API documentation)

### Phase 2: Automated Test Suite (2 hours)

**Goal**: Create comprehensive automated tests

**Tasks**:
1. Create `test_api.py` test runner
2. Implement Config API tests (agent CRUD)
3. Implement Config API tests (domain CRUD)
4. Implement Data API tests (retrieval, spatial, analytics)
5. Implement Ingest API tests (submit report)
6. Implement Query API tests (ask question)
7. Implement authentication tests
8. Implement error handling tests
9. Implement edge case tests
10. Implement performance tests
11. Add test report generation

**Output**: `test_api.py` (automated test suite)

### Phase 3: Gap Analysis (1 hour)

**Goal**: Identify and prioritize gaps

**Tasks**:
1. Run automated test suite
2. Analyze test results
3. Identify missing endpoints
4. Identify incomplete implementations
5. Identify missing error handling
6. Identify missing validation
7. Prioritize gaps by severity
8. Estimate fix times
9. Create action plan
10. Generate `GAP_ANALYSIS.md`

**Output**: `GAP_ANALYSIS.md` (prioritized gap analysis)

### Phase 4: Demo Script (0.5 hours)

**Goal**: Create demo script for judges

**Tasks**:
1. Create `DEMO_SCRIPT.md`
2. Add authentication step
3. Add create agent step
4. Add create domain step
5. Add submit report step
6. Add ask question step
7. Add retrieve data step
8. Add timing estimates
9. Add expected responses
10. Add troubleshooting tips

**Output**: `DEMO_SCRIPT.md` (demo script)

### Phase 5: Quick Fixes (1 hour)

**Goal**: Fix critical gaps identified in Phase 3

**Tasks**:
1. Fix demo-blocking issues first
2. Fix critical validation issues
3. Fix critical error handling issues
4. Re-run tests to verify fixes
5. Update documentation

**Output**: Fixed critical issues

**Total Time**: 6 hours
