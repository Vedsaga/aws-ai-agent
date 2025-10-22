# API Integration Guide - Multi-Agent Orchestration System

## Overview

This guide documents all backend APIs, client-side integration, and solutions to common issues including the network error on startup.

## Table of Contents

1. [Quick Fix: Network Error](#quick-fix-network-error)
2. [API Architecture](#api-architecture)
3. [Available APIs](#available-apis)
4. [Client-Side Integration](#client-side-integration)
5. [Status Polling](#status-polling)
6. [Form Integration](#form-integration)
7. [Map Integration](#map-integration)
8. [Real-Time Updates](#real-time-updates)
9. [Error Handling](#error-handling)
10. [Examples](#examples)

---

## Quick Fix: Network Error

### Problem
Network errors appear on page load due to API calls being made before configuration is ready.

### Solution
The application now uses an **initialization guard** that:
- Validates configuration before making API calls
- Prevents network requests if API URL is not configured
- Gracefully falls back to default data
- Shows appropriate error messages only when necessary

### Environment Setup
Ensure your `.env.local` file has valid configuration:

```bash
# Required
NEXT_PUBLIC_API_URL=https://your-api-url.execute-api.us-east-1.amazonaws.com/v1

# Required for Auth
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_REGION=us-east-1

# Optional - for real-time features
NEXT_PUBLIC_APPSYNC_URL=https://xxxxx.appsync-api.us-east-1.amazonaws.com/graphql
NEXT_PUBLIC_APPSYNC_REGION=us-east-1

# Optional - for maps
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## API Architecture

### Base URL
```
https://{api-gateway-id}.execute-api.us-east-1.amazonaws.com/v1/api/v1
```

### Authentication
All endpoints require JWT token from AWS Cognito:
```
Authorization: Bearer {jwt-token}
```

### Response Format
```typescript
// Success Response
{
  "data": {...},
  "status": 200
}

// Error Response
{
  "error": "Error message",
  "error_code": "ERR_XXX",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Available APIs

### 1. Ingest API - Submit Reports

**Endpoint:** `POST /api/v1/ingest`

**Request:**
```typescript
{
  "domain_id": "civic_complaints",
  "text": "There is a large pothole on Main St near 5th Avenue",
  "images": ["base64-image-data"],           // Optional, max 5 images
  "source": "web",                           // Optional: web, mobile, api
  "priority": "normal",                      // Optional: low, normal, high, urgent
  "reporter_contact": "user@example.com"     // Optional
}
```

**Response:**
```typescript
{
  "job_id": "job_abc123def456",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "2024-01-01T12:00:00Z",
  "estimated_completion_seconds": 30
}
```

**Client Usage:**
```typescript
import { submitReport } from '@/lib/api-client';

const result = await submitReport({
  domain_id: "civic_complaints",
  text: "Pothole on Main St",
  priority: "high"
});

if (result.data) {
  console.log("Job ID:", result.data.job_id);
}
```

---

### 2. Query API - Ask Questions

**Endpoint:** `POST /api/v1/query`

**Request:**
```typescript
{
  "domain_id": "civic_complaints",
  "question": "How many potholes were reported this month?",
  "filters": {                               // Optional
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    },
    "category": ["potholes", "road_damage"],
    "priority": ["high", "urgent"]
  },
  "include_visualizations": true             // Optional
}
```

**Response:**
```typescript
{
  "job_id": "query_abc123def456",
  "status": "accepted",
  "message": "Question submitted for processing",
  "timestamp": "2024-01-01T12:00:00Z",
  "estimated_completion_seconds": 10
}
```

**Client Usage:**
```typescript
import { submitQuery } from '@/lib/api-client';

const result = await submitQuery({
  domain_id: "civic_complaints",
  question: "Show me all potholes in downtown",
  filters: {
    location: {
      latitude: 40.7128,
      longitude: -74.0060,
      radius_km: 5
    }
  }
});
```

---

### 3. Status Polling API

**Endpoint:** `GET /api/v1/status/{job_id}`

**Response:**
```typescript
{
  "job_id": "job_abc123def456",
  "status": "processing",                    // pending, processing, completed, failed
  "progress": 65,                            // 0-100
  "message": "Processing with geo agent...",
  "timestamp": "2024-01-01T12:00:30Z",
  "current_step": "geo_extraction",
  "agent_updates": [
    {
      "agent_name": "GeoAgent",
      "status": "completed",
      "progress": 100,
      "message": "Location extracted successfully",
      "output": "123 Main St, City, State"
    }
  ],
  "result": {...},                           // Only present when completed
  "error": "Error message"                   // Only present when failed
}
```

**Client Usage with Polling:**
```typescript
import { useJobPolling } from '@/hooks/use-job-polling';

function MyComponent() {
  const { status, isPolling, progress } = useJobPolling({
    jobId: "job_abc123",
    intervalMs: 2500,
    onComplete: (finalStatus) => {
      console.log("Job completed:", finalStatus);
    }
  });

  return (
    <div>
      {isPolling && <p>Progress: {progress}%</p>}
      {status?.message}
    </div>
  );
}
```

---

### 4. Config API - Manage Domains & Agents

#### List Configurations
**Endpoint:** `GET /api/v1/config?type={domain|agent|playbook|template}`

**Response:**
```typescript
{
  "configs": [
    {
      "config_id": "cfg_123",
      "tenant_id": "tenant_001",
      "config_type": "domain",
      "name": "Civic Complaints",
      "description": "Report civic issues",
      "config": {
        "domain_id": "civic_complaints",
        "ingest_agents": ["geo_agent", "temporal_agent"],
        "query_agents": ["what_agent", "where_agent"]
      },
      "version": 1,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": "user_123"
    }
  ],
  "count": 1
}
```

#### Create Configuration
**Endpoint:** `POST /api/v1/config`

**Request:**
```typescript
{
  "type": "domain",
  "config": {
    "domain_id": "custom_domain",
    "name": "Custom Domain",
    "description": "My custom domain",
    "ingest_agents": ["geo_agent"],
    "query_agents": ["what_agent"]
  }
}
```

#### Update Configuration
**Endpoint:** `PUT /api/v1/config/{type}/{id}`

#### Delete Configuration
**Endpoint:** `DELETE /api/v1/config/{type}/{id}`

**Client Usage:**
```typescript
import { listDomains, createDomain } from '@/lib/api-client';

// List domains
const response = await listDomains();
const domains = response.data;

// Create domain
await createDomain({
  domain_id: "my_domain",
  name: "My Domain",
  description: "Custom domain",
  ingest_agents: ["geo_agent"],
  query_agents: ["what_agent"]
});
```

---

### 5. Data API - Retrieve Incidents & Queries

**Endpoint:** `GET /api/v1/data?type={incidents|queries}&filters={json}`

**Response:**
```typescript
{
  "data": [
    {
      "incident_id": "inc_12345678",
      "job_id": "job_abc123",
      "domain_id": "civic_complaints",
      "raw_text": "Pothole on Main St",
      "status": "completed",
      "location": {
        "type": "Point",
        "coordinates": [-74.0060, 40.7128]
      },
      "category": "potholes",
      "priority": "high",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "has_more": false
}
```

**Client Usage:**
```typescript
import { fetchIncidents } from '@/lib/api-client';

const response = await fetchIncidents("civic_complaints", {
  status: ["completed"],
  date_range: {
    start: "2024-01-01",
    end: "2024-01-31"
  }
});

const incidents = response.data?.data || [];
```

---

### 6. Tools API - Tool Registry

**Endpoint:** `GET /api/v1/tools`

**Response:**
```typescript
{
  "tools": [
    {
      "tool_id": "bedrock",
      "name": "AWS Bedrock",
      "description": "LLM inference via AWS Bedrock",
      "tool_type": "api",
      "parameters": [...]
    }
  ]
}
```

---

## Client-Side Integration

### Using the Unified API Service

```typescript
import { apiService } from '@/lib/api-service';

// Submit report with auto-polling
const handleSubmit = async () => {
  const status = await apiService.submitReportWithPolling(
    "civic_complaints",
    "Pothole on Main St",
    (update) => {
      console.log("Progress:", update.progress);
      console.log("Message:", update.message);
    },
    {
      images: [],
      priority: "high",
      pollingIntervalMs: 2500
    }
  );

  if (status?.status === "completed") {
    console.log("Success:", status.result);
  }
};

// Query with auto-polling
const handleQuery = async () => {
  const status = await apiService.submitQueryWithPolling(
    "civic_complaints",
    "Show all potholes",
    (update) => {
      console.log("Progress:", update.progress);
    }
  );

  if (status?.status === "completed") {
    console.log("Results:", status.result);
  }
};
```

---

## Status Polling

### Using the Polling Hook

```typescript
import { useJobPolling } from '@/hooks/use-job-polling';
import { useState } from 'react';

function ReportForm() {
  const [jobId, setJobId] = useState<string | null>(null);
  
  const { status, isPolling, progress, error } = useJobPolling({
    jobId,
    enabled: jobId !== null,
    intervalMs: 2500,
    maxAttempts: 60,
    onComplete: (finalStatus) => {
      console.log("Completed:", finalStatus);
      if (finalStatus.result) {
        // Show results on map, in chat, etc.
      }
    },
    onError: (err) => {
      console.error("Error:", err);
    }
  });

  const handleSubmit = async () => {
    const result = await submitReport({...});
    if (result.data) {
      setJobId(result.data.job_id);
    }
  };

  return (
    <div>
      {isPolling && (
        <div>
          <progress value={progress} max={100} />
          <p>{status?.message}</p>
        </div>
      )}
    </div>
  );
}
```

### Manual Polling Control

```typescript
import { apiService } from '@/lib/api-service';

// Start polling
apiService.startPolling(
  "job_abc123",
  (status) => {
    console.log("Update:", status);
  },
  2500  // interval in ms
);

// Stop polling
apiService.stopPolling("job_abc123");

// Stop all polling
apiService.stopAllPolling();

// Cleanup on unmount
useEffect(() => {
  return () => {
    apiService.cleanup();
  };
}, []);
```

---

## Form Integration

### Report Submission Form

```typescript
import { useState } from 'react';
import { apiService } from '@/lib/api-service';
import { useJobPolling } from '@/hooks/use-job-polling';

export function SubmitReportForm({ domainId }: { domainId: string }) {
  const [text, setText] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { status, isPolling, progress } = useJobPolling({
    jobId,
    intervalMs: 2500,
    onComplete: (result) => {
      console.log("Report processed:", result);
      // Reset form or show success
      setText('');
      setJobId(null);
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const result = await apiService.submitReport(domainId, text, {
        priority: 'normal',
        source: 'web'
      });

      if (result.success && result.jobId) {
        setJobId(result.jobId);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Describe the issue..."
        disabled={submitting || isPolling}
      />
      
      {isPolling && (
        <div>
          <progress value={progress} max={100} />
          <p>{status?.message}</p>
        </div>
      )}
      
      <button type="submit" disabled={submitting || isPolling}>
        {submitting ? 'Submitting...' : 'Submit Report'}
      </button>
    </form>
  );
}
```

### Query Form

```typescript
export function QueryForm({ domainId }: { domainId: string }) {
  const [question, setQuestion] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const { status, isPolling } = useJobPolling({
    jobId,
    intervalMs: 2000,
    onComplete: (result) => {
      // Display results in chat or map
      if (result.result?.data) {
        // Show data on map
      }
      if (result.result?.answer) {
        // Add to chat history
      }
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await apiService.submitQuery(domainId, question);
    if (result.success && result.jobId) {
      setJobId(result.jobId);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question..."
      />
      <button type="submit" disabled={isPolling}>
        {isPolling ? 'Processing...' : 'Ask'}
      </button>
    </form>
  );
}
```

---

## Map Integration

### Display Incidents on Map

```typescript
import { useEffect, useState } from 'react';
import { apiService } from '@/lib/api-service';
import type { IncidentRecord, GeoJSONFeature } from '@/lib/api-types';

export function IncidentMap({ domainId }: { domainId: string }) {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);

  useEffect(() => {
    loadIncidents();
  }, [domainId]);

  const loadIncidents = async () => {
    const data = await apiService.fetchIncidents(domainId, {
      status: ['completed'],
      has_location: true
    });
    setIncidents(data);
  };

  const toGeoJSON = (): GeoJSONFeature[] => {
    return incidents
      .filter(inc => inc.location)
      .map(inc => ({
        type: 'Feature',
        geometry: inc.location!,
        properties: {
          id: inc.incident_id,
          title: inc.category || 'Incident',
          description: inc.raw_text,
          status: inc.status,
          priority: inc.priority,
          created_at: inc.created_at
        }
      }));
  };

  return (
    <Map>
      {toGeoJSON().map(feature => (
        <Marker
          key={feature.properties.id}
          coordinates={feature.geometry.coordinates}
          onClick={() => {
            // Show popup with incident details
          }}
        />
      ))}
    </Map>
  );
}
```

### Update Map on New Data

```typescript
const { status } = useJobPolling({
  jobId,
  onComplete: (result) => {
    if (result.result?.location) {
      // Zoom to new incident location
      map.flyTo({
        center: result.result.location.coordinates,
        zoom: 15
      });
      
      // Add marker
      addMarker(result.result.location);
    }
  }
});
```

---

## Real-Time Updates

### AppSync Integration (When Deployed)

```typescript
import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/api';

const client = generateClient();

// Subscribe to status updates
const subscription = client.graphql({
  query: `
    subscription OnStatusUpdate($job_id: String!) {
      onStatusUpdate(job_id: $job_id) {
        job_id
        status
        progress
        message
        timestamp
      }
    }
  `,
  variables: { job_id: "job_abc123" }
}).subscribe({
  next: (data) => {
    console.log("Real-time update:", data);
  },
  error: (error) => {
    console.error("Subscription error:", error);
  }
});

// Cleanup
subscription.unsubscribe();
```

---

## Error Handling

### Network Error Prevention

```typescript
import { initGuard } from '@/lib/init-guard';

// Check if API is ready before making calls
useEffect(() => {
  const checkReady = async () => {
    const ready = await initGuard.ensureReady({ skipIfInvalid: true });
    if (ready) {
      // Safe to make API calls
      loadData();
    } else {
      // Use fallback data
      setData(DEFAULT_DATA);
    }
  };
  checkReady();
}, []);
```

### Handle API Errors

```typescript
const result = await apiService.submitReport(domainId, text);

if (!result.success) {
  // Show error to user
  showErrorToast("Submission failed", result.error || "Unknown error");
  return;
}

// Continue with success flow
```

---

## Examples

### Complete Submit → Poll → Display Flow

```typescript
export function CompleteReportFlow() {
  const [text, setText] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const { status, isPolling, progress } = useJobPolling({
    jobId,
    intervalMs: 2500,
    onComplete: (finalStatus) => {
      setResult(finalStatus.result);
    }
  });

  const handleSubmit = async () => {
    const response = await apiService.submitReport(
      'civic_complaints',
      text,
      { priority: 'high' }
    );

    if (response.success && response.jobId) {
      setJobId(response.jobId);
    }
  };

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button onClick={handleSubmit} disabled={isPolling}>
        Submit
      </button>

      {isPolling && (
        <div>
          <p>Progress: {progress}%</p>
          <p>{status?.message}</p>
        </div>
      )}

      {result && (
        <div>
          <h3>Processing Complete!</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
```

---

## Troubleshooting

### Issue: Network Error on Load
**Solution:** Ensure `.env.local` has valid `NEXT_PUBLIC_API_URL` or the app will use fallback data.

### Issue: Polling Never Completes
**Solution:** Check that the backend orchestrator is running and job is being processed.

### Issue: Map Not Showing Incidents
**Solution:** Ensure incidents have `location` field with `coordinates` in `[longitude, latitude]` format.

### Issue: Auth Token Expired
**Solution:** The API client automatically refreshes tokens. If issues persist, log out and log back in.

---

## Summary

This integration provides:
- ✅ Type-safe API client with all endpoints
- ✅ Automatic status polling with configurable intervals
- ✅ Network error prevention with initialization guard
- ✅ Fallback to default data when API unavailable
- ✅ React hooks for easy polling integration
- ✅ Unified API service for common operations
- ✅ Map integration support
- ✅ Real-time updates (when AppSync deployed)
- ✅ Comprehensive error handling

All APIs are ready to use. Focus on building UI components that consume these services.