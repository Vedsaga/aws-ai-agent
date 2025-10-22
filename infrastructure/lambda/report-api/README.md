# Report API Handler

This Lambda function handles CRUD operations for Reports in the DomainFlow system.

## Overview

The Report Handler manages the lifecycle of report documents stored in DynamoDB. Reports are the core data documents in the system, representing incidents, cases, or data records that are processed by ingestion agents and updated by management agents.

## API Endpoints

### POST /api/v1/reports
Create a new report and trigger ingestion playbook.

**Request Body:**
```json
{
  "domain_id": "civic_complaints",
  "text": "There is a pothole on Main Street",
  "images": ["https://example.com/image.jpg"],
  "source": "mobile-app"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_abc123",
  "incident_id": "inc_xyz789",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "2025-10-21T16:00:00Z"
}
```

### GET /api/v1/reports/{incident_id}
Get a report by incident_id with full document structure.

**Response (200 OK):**
```json
{
  "incident_id": "inc_xyz789",
  "tenant_id": "tenant-uuid",
  "domain_id": "civic_complaints",
  "raw_text": "There is a pothole on Main Street",
  "status": "completed",
  "ingestion_data": {
    "complaint_type": "pothole",
    "location_text": "Main Street",
    "urgency": "high",
    "geo_location": {
      "type": "Point",
      "coordinates": [-122.4194, 37.7749]
    }
  },
  "management_data": {
    "task_details": {
      "assignee_id": "team-roads",
      "priority": "high",
      "due_at": "2025-10-23T16:00:00Z"
    },
    "history": [
      {
        "status": "pending",
        "timestamp": "2025-10-21T16:00:00Z",
        "by": "agent"
      }
    ]
  },
  "id": "report-uuid",
  "created_at": "2025-10-21T16:00:00Z",
  "updated_at": "2025-10-21T16:05:00Z",
  "created_by": "user-uuid",
  "source": "mobile-app"
}
```

### GET /api/v1/reports
List reports with filtering and pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `domain_id`: Filter by domain
- `status`: Filter by status

**Response (200 OK):**
```json
{
  "reports": [
    {
      "incident_id": "inc_xyz789",
      "domain_id": "civic_complaints",
      "raw_text": "There is a pothole...",
      "status": "completed",
      "created_at": "2025-10-21T16:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

### PUT /api/v1/reports/{incident_id}
Update a report (merge management_data).

**Request Body:**
```json
{
  "status": "in_progress",
  "management_data": {
    "task_details": {
      "assignee_id": "team-roads",
      "priority": "high"
    }
  }
}
```

**Response (200 OK):**
Returns the updated report document.

### DELETE /api/v1/reports/{incident_id}
Delete a report.

**Response (200 OK):**
```json
{
  "message": "Report deleted successfully",
  "incident_id": "inc_xyz789"
}
```

## Data Model

### Report Document Structure

```python
{
    "incident_id": str,           # Primary key (e.g., "inc_abc12345")
    "tenant_id": str,             # Tenant identifier
    "domain_id": str,             # Domain identifier
    "raw_text": str,              # Original unstructured text
    "status": str,                # processing | completed | failed
    "ingestion_data": dict,       # Populated by ingestion agents
    "management_data": dict,      # Populated by management agents
    "id": str,                    # UUID for standard metadata
    "created_at": str,            # ISO8601 timestamp
    "updated_at": str,            # ISO8601 timestamp
    "created_by": str,            # User ID
    "source": str,                # web | mobile-app | api
    "images": list[str],          # Optional image URLs (max 5)
}
```

## DynamoDB Table

**Table Name:** `Reports`

**Primary Key:**
- Partition Key: `incident_id` (String)

**Global Secondary Indexes:**
1. `tenant-domain-index`
   - Partition Key: `tenant_id`
   - Sort Key: `domain_id`

2. `domain-created-index`
   - Partition Key: `domain_id`
   - Sort Key: `created_at`

## Features

### 1. Report Creation
- Validates required fields (domain_id, text)
- Generates unique incident_id and job_id
- Stores report with empty ingestion_data and management_data
- Triggers orchestrator Lambda asynchronously with ingestion playbook
- Returns 202 Accepted immediately

### 2. Report Retrieval
- Fetches report by incident_id
- Verifies tenant access
- Returns full document with ingestion_data and management_data

### 3. Report Listing
- Supports pagination (page, limit)
- Filters by domain_id and status
- Uses GSI for efficient queries
- Returns simplified list view

### 4. Report Updates
- Supports status updates
- Deep merges management_data (preserves existing fields)
- Updates updated_at timestamp automatically
- Verifies tenant access

### 5. Report Deletion
- Verifies tenant access before deletion
- Removes report from DynamoDB
- Returns confirmation message

## Security

- **Tenant Isolation:** All operations verify tenant_id from JWT token
- **Access Control:** Users can only access reports in their tenant
- **Input Validation:** Validates required fields and data types
- **Error Handling:** Returns appropriate HTTP status codes

## Environment Variables

- `REPORTS_TABLE`: DynamoDB table name for reports
- `ORCHESTRATOR_FUNCTION`: Lambda function name for orchestrator

## Error Responses

All errors follow a standardized format:

```json
{
  "error": "Error message",
  "timestamp": "2025-10-21T16:00:00Z",
  "error_code": "ERR_400"
}
```

**Status Codes:**
- 200: Success
- 202: Accepted (async processing)
- 400: Bad Request (validation error)
- 403: Forbidden (access denied)
- 404: Not Found
- 500: Internal Server Error

## Integration with Orchestrator

When a report is created:
1. Report Handler stores the report in DynamoDB
2. Triggers Orchestrator Lambda asynchronously
3. Orchestrator loads the domain's ingestion_playbook
4. Executes ingestion agents in dependency order
5. Updates report with ingestion_data
6. Publishes status updates via AppSync

## Testing

Run unit tests:
```bash
pytest test_report_handler.py -v
```

## Requirements

See `requirements.txt` for dependencies.
