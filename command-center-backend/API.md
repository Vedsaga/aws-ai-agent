# API Documentation

Complete API reference for the Command Center Backend with client-side integration examples.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Authentication](#-authentication)
- [Base URL](#-base-url)
- [Endpoints](#-endpoints)
- [Sequence Diagrams](#-sequence-diagrams)
- [Data Models](#-data-models)
- [Error Handling](#-error-handling)
- [Client Integration](#-client-integration)
- [Rate Limits](#-rate-limits)

---

## 🌐 Overview

The Command Center Backend API provides real-time event updates and AI-powered query capabilities for disaster response operations.

**Technology Stack**:
- AWS API Gateway (REST API)
- AWS Lambda (Serverless functions)
- Amazon DynamoDB (Event storage)
- Amazon Bedrock (AI agent with OpenAI GPT-4o)

**Data Source**: 7-day pre-processed earthquake response simulation timeline

---

## 🔐 Authentication

All API requests require an API key in the request header:

```http
x-api-key: your-api-key-here
```

### Getting Your API Key

After deployment, retrieve your API key:

**Option 1: From `.env.local` (auto-generated)**
```bash
cat .env.local
```

**Option 2: AWS Console**
1. Go to API Gateway → API Keys
2. Find your key
3. Click "Show" to reveal value

**Option 3: AWS CLI**
```bash
aws apigateway get-api-keys --include-values
```

### Example Request

```bash
curl -X GET "https://your-api.com/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: your-api-key-here"
```

---

## 🌍 Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
```

Example:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev
```

**Stages**:
- `dev` - Development environment
- `staging` - Staging environment
- `prod` - Production environment

---

## 📡 Endpoints

### Summary

| Method | Endpoint | Description | Response Time |
|--------|----------|-------------|---------------|
| GET | `/data/updates` | Get event updates | < 500ms |
| POST | `/agent/query` | Natural language query | < 3s |
| POST | `/agent/action` | Execute pre-defined action | < 3s |


---

## 🔄 Sequence Diagrams

### 1. GET /data/updates - Event Updates Flow

```
Frontend                API Gateway           Lambda              DynamoDB
   │                         │                   │                    │
   │  GET /data/updates      │                   │                    │
   │  ?since=2023-02-06      │                   │                    │
   │  + x-api-key            │                   │                    │
   ├────────────────────────>│                   │                    │
   │                         │                   │                    │
   │                         │  Validate API Key │                    │
   │                         │───────────────────┤                    │
   │                         │                   │                    │
   │                         │  Invoke Lambda    │                    │
   │                         ├──────────────────>│                    │
   │                         │                   │                    │
   │                         │                   │  Query Events      │
   │                         │                   │  WHERE Day IN      │
   │                         │                   │  (DAY_0...DAY_6)   │
   │                         │                   │  AND Timestamp >   │
   │                         │                   │  since             │
   │                         │                   ├───────────────────>│
   │                         │                   │                    │
   │                         │                   │  Return Events     │
   │                         │                   │<───────────────────┤
   │                         │                   │                    │
   │                         │                   │  Transform to      │
   │                         │                   │  GeoJSON layers    │
   │                         │                   │──────────┐         │
   │                         │                   │          │         │
   │                         │                   │<─────────┘         │
   │                         │                   │                    │
   │                         │  Return Response  │                    │
   │                         │<──────────────────┤                    │
   │                         │                   │                    │
   │  200 OK                 │                   │                    │
   │  {                      │                   │                    │
   │    latestTimestamp,     │                   │                    │
   │    mapUpdates,          │                   │                    │
   │    criticalAlerts       │                   │                    │
   │  }                      │                   │                    │
   │<────────────────────────┤                   │                    │
   │                         │                   │                    │
   │  Update Map             │                   │                    │
   │──────────┐              │                   │                    │
   │          │              │                   │                    │
   │<─────────┘              │                   │                    │
```

### 2. POST /agent/query - AI Query Flow

```
Frontend            API Gateway         Lambda          Bedrock Agent      Database Tool
   │                     │                 │                   │                  │
   │  POST /agent/query  │                 │                   │                  │
   │  {                  │                 │                   │                  │
   │    text: "Show      │                 │                   │                  │
   │    critical         │                 │                   │                  │
   │    medical"         │                 │                   │                  │
   │  }                  │                 │                   │                  │
   │  + x-api-key        │                 │                   │                  │
   ├────────────────────>│                 │                   │                  │
   │                     │                 │                   │                  │
   │                     │  Validate Key   │                   │                  │
   │                     │─────────────────┤                   │                  │
   │                     │                 │                   │                  │
   │                     │  Invoke Lambda  │                   │                  │
   │                     ├────────────────>│                   │                  │
   │                     │                 │                   │                  │
   │                     │                 │  Invoke Agent     │                  │
   │                     │                 │  with query       │                  │
   │                     │                 ├──────────────────>│                  │
   │                     │                 │                   │                  │
   │                     │                 │                   │  Parse query     │
   │                     │                 │                   │  with GPT-4o     │
   │                     │                 │                   │──────────┐       │
   │                     │                 │                   │          │       │
   │                     │                 │                   │<─────────┘       │
   │                     │                 │                   │                  │
   │                     │                 │                   │  Call Database   │
   │                     │                 │                   │  Tool (Lambda)   │
   │                     │                 │                   ├─────────────────>│
   │                     │                 │                   │                  │
   │                     │                 │                   │  Query DynamoDB  │
   │                     │                 │                   │  for medical     │
   │                     │                 │                   │  + critical      │
   │                     │                 │                   │<─────────────────┤
   │                     │                 │                   │                  │
   │                     │                 │                   │  Generate        │
   │                     │                 │                   │  response with   │
   │                     │                 │                   │  GPT-4o          │
   │                     │                 │                   │──────────┐       │
   │                     │                 │                   │          │       │
   │                     │                 │                   │<─────────┘       │
   │                     │                 │                   │                  │
   │                     │                 │  Agent Response   │                  │
   │                     │                 │<──────────────────┤                  │
   │                     │                 │                   │                  │
   │                     │                 │  Transform to     │                  │
   │                     │                 │  map layers       │                  │
   │                     │                 │──────────┐        │                  │
   │                     │                 │          │        │                  │
   │                     │                 │<─────────┘        │                  │
   │                     │                 │                   │                  │
   │                     │  Return Response│                   │                  │
   │                     │<────────────────┤                   │                  │
   │                     │                 │                   │                  │
   │  200 OK             │                 │                   │                  │
   │  {                  │                 │                   │                  │
   │    chatResponse,    │                 │                   │                  │
   │    mapLayers,       │                 │                   │                  │
   │    viewState        │                 │                   │                  │
   │  }                  │                 │                   │                  │
   │<────────────────────┤                 │                   │                  │
   │                     │                 │                   │                  │
   │  Update UI + Map    │                 │                   │                  │
   │──────────┐          │                 │                   │                  │
   │          │          │                 │                   │                  │
   │<─────────┘          │                 │                   │                  │
```

### 3. POST /agent/action - Pre-defined Action Flow

```
Frontend            API Gateway         Lambda          Bedrock Agent
   │                     │                 │                   │
   │  POST /agent/action │                 │                   │
   │  {                  │                 │                   │
   │    actionId:        │                 │                   │
   │    "SHOW_CRITICAL_  │                 │                   │
   │     MEDICAL"        │                 │                   │
   │  }                  │                 │                   │
   │  + x-api-key        │                 │                   │
   ├────────────────────>│                 │                   │
   │                     │                 │                   │
   │                     │  Validate Key   │                   │
   │                     │─────────────────┤                   │
   │                     │                 │                   │
   │                     │  Invoke Lambda  │                   │
   │                     ├────────────────>│                   │
   │                     │                 │                   │
   │                     │                 │  Map actionId to  │
   │                     │                 │  pre-defined      │
   │                     │                 │  prompt           │
   │                     │                 │──────────┐        │
   │                     │                 │          │        │
   │                     │                 │<─────────┘        │
   │                     │                 │                   │
   │                     │                 │  Invoke Agent     │
   │                     │                 │  with prompt      │
   │                     │                 ├──────────────────>│
   │                     │                 │                   │
   │                     │                 │  Process & Query  │
   │                     │                 │  (same as above)  │
   │                     │                 │                   │
   │                     │                 │  Agent Response   │
   │                     │                 │<──────────────────┤
   │                     │                 │                   │
   │                     │  Return Response│                   │
   │                     │<────────────────┤                   │
   │                     │                 │                   │
   │  200 OK             │                 │                   │
   │  {                  │                 │                   │
   │    chatResponse,    │                 │                   │
   │    mapLayers,       │                 │                   │
   │    viewState        │                 │                   │
   │  }                  │                 │                   │
   │<────────────────────┤                 │                   │
   │                     │                 │                   │
```


---

## 📡 Endpoint Details

### 1. GET /data/updates

Retrieve event updates based on time and optional domain filters.

**Purpose**: Incremental updates for real-time dashboard synchronization

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `since` | string | Yes | ISO 8601 timestamp | `2023-02-06T00:00:00Z` |
| `domain` | string | No | Filter by domain | `MEDICAL`, `FIRE`, `STRUCTURAL` |

**Request Example**:

```bash
curl -X GET "https://your-api.com/data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
  -H "x-api-key: your-api-key-here"
```

**Response**: `200 OK`

```json
{
  "latestTimestamp": "2023-02-06T12:30:00Z",
  "mapUpdates": {
    "mapAction": "APPEND",
    "mapLayers": [
      {
        "layerId": "incidents-medical",
        "layerName": "Medical Incidents",
        "geometryType": "Point",
        "style": {
          "icon": "MEDICAL_EMERGENCY",
          "color": "#DC2626",
          "size": 8
        },
        "data": {
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "geometry": {
                "type": "Point",
                "coordinates": [37.0123, 37.4567]
              },
              "properties": {
                "eventId": "evt-123",
                "severity": "CRITICAL",
                "summary": "Multiple casualties reported",
                "timestamp": "2023-02-06T12:15:00Z"
              }
            }
          ]
        }
      }
    ]
  },
  "criticalAlerts": [
    {
      "alertId": "alert-456",
      "timestamp": "2023-02-06T12:15:00Z",
      "severity": "CRITICAL",
      "title": "Medical Emergency",
      "summary": "Multiple casualties reported at collapsed building"
    }
  ]
}
```

**Performance**: < 500ms typical response time


### 2. POST /agent/query

Process natural language queries using AI to retrieve and synthesize information.

**Purpose**: AI-powered natural language query processing

**Request Body**:

```json
{
  "text": "Show me all critical medical incidents in the last 6 hours",
  "sessionId": "session-abc-123",
  "currentMapState": {
    "center": [37.0, 37.5],
    "zoom": 10
  }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Natural language query |
| `sessionId` | string | No | Session ID for conversation continuity |
| `currentMapState` | object | No | Current map view context |

**Request Example**:

```bash
curl -X POST "https://your-api.com/agent/query" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the most urgent needs right now?"
  }'
```

**Response**: `200 OK`

```json
{
  "simulationTime": "Day 1, 12:30",
  "timestamp": "2023-02-06T12:30:00Z",
  "chatResponse": "I found 8 critical medical incidents in the last 6 hours...",
  "mapAction": "REPLACE",
  "viewState": {
    "bounds": {
      "southwest": { "lat": 37.1, "lon": 36.8 },
      "northeast": { "lat": 37.6, "lon": 37.3 }
    }
  },
  "mapLayers": [
    {
      "layerId": "critical-medical",
      "layerName": "Critical Medical Incidents",
      "geometryType": "Point",
      "style": {
        "icon": "MEDICAL_EMERGENCY",
        "color": "#DC2626",
        "size": 10
      },
      "data": {
        "type": "FeatureCollection",
        "features": [...]
      }
    }
  ],
  "uiContext": {
    "suggestedActions": [
      {
        "label": "Show available medical resources",
        "actionId": "SHOW_MEDICAL_RESOURCES"
      }
    ]
  }
}
```

**Performance**: < 3 seconds typical response time


### 3. POST /agent/action

Execute pre-defined actions that map to common queries.

**Purpose**: Quick access to frequently used operations

**Request Body**:

```json
{
  "actionId": "SHOW_CRITICAL_MEDICAL",
  "payload": {
    "includeResources": true
  }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actionId` | string | Yes | Pre-defined action identifier |
| `payload` | object | No | Action-specific parameters |

**Available Action IDs**:

| Action ID | Description | Payload Parameters |
|-----------|-------------|-------------------|
| `SHOW_CRITICAL_MEDICAL` | Show critical medical incidents | None |
| `SHOW_FIRE_INCIDENTS` | Show fire incidents | None |
| `SHOW_STRUCTURAL_DAMAGE` | Show structural damage | None |
| `SHOW_LOGISTICS_STATUS` | Show logistics status | None |
| `SHOW_RESOURCE_GAPS` | Identify resource shortages | `domain` (optional) |
| `GENERATE_AREA_BRIEFING` | Generate area summary | `area` (required) |
| `CALC_ROUTE` | Calculate route | `from`, `to` (coordinates) |
| `HELP` | Show available actions | None |

**Request Example**:

```bash
curl -X POST "https://your-api.com/agent/action" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "actionId": "SHOW_CRITICAL_MEDICAL"
  }'
```

**Response**: Same structure as `/agent/query`

**Performance**: < 3 seconds typical response time

---

## 📊 Data Models

### MapLayer

```typescript
interface MapLayer {
  layerId: string;              // Unique identifier
  layerName: string;            // Display name
  geometryType: "Point" | "Polygon" | "LineString";
  style: {
    icon?: string;              // Icon name for Point layers
    color?: string;             // Hex color code
    size?: number;              // Size for Point layers
    fillColor?: string;         // Fill color for Polygon layers
    fillOpacity?: number;       // Opacity (0-1)
  };
  data: GeoJSON.FeatureCollection;
}
```

### Alert

```typescript
interface Alert {
  alertId: string;
  timestamp: string;            // ISO 8601
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  title: string;
  summary: string;
  location?: {
    lat: number;
    lon: number;
  };
}
```

### ViewState

```typescript
interface ViewState {
  bounds?: {
    southwest: { lat: number; lon: number };
    northeast: { lat: number; lon: number };
  };
  center?: { lat: number; lon: number };
  zoom?: number;
}
```


---

## ❌ Error Handling

### Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additionalInfo": "Optional additional context"
    }
  }
}
```

### HTTP Status Codes

| Status | Error Code | Description | Action |
|--------|------------|-------------|--------|
| 400 | `INVALID_REQUEST` | Malformed request or missing fields | Check request format |
| 401 | `AUTHENTICATION_FAILED` | Invalid or missing API key | Verify API key |
| 403 | `FORBIDDEN` | Valid key but insufficient permissions | Check permissions |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry |
| 500 | `DATABASE_ERROR` | DynamoDB query failed | Check logs, retry |
| 500 | `AGENT_ERROR` | Bedrock Agent invocation failed | Check Bedrock access |
| 500 | `INTERNAL_ERROR` | Unexpected server error | Check logs, contact support |

### Error Examples

**400 Bad Request - Missing Parameter**:
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required parameter: since",
    "details": {
      "parameter": "since",
      "expectedFormat": "ISO 8601 timestamp"
    }
  }
}
```

**401 Unauthorized - Invalid API Key**:
```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid API key"
  }
}
```

**429 Too Many Requests**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "details": {
      "retryAfter": 60
    }
  }
}
```

**500 Internal Server Error**:
```json
{
  "error": {
    "code": "AGENT_ERROR",
    "message": "Failed to process query with AI agent",
    "details": {
      "requestId": "req-abc-123"
    }
  }
}
```

---

## 💻 Client Integration

### React/Next.js Example

**1. Environment Variables**

Create `.env.local`:
```bash
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxx
```

**2. API Client**

```typescript
// lib/api-client.ts
const API_ENDPOINT = process.env.NEXT_PUBLIC_API_ENDPOINT;
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

export async function getUpdates(since: string, domain?: string) {
  const params = new URLSearchParams({ since });
  if (domain) params.append('domain', domain);
  
  const response = await fetch(
    `${API_ENDPOINT}/data/updates?${params}`,
    {
      headers: {
        'x-api-key': API_KEY!,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}

export async function queryAgent(text: string, sessionId?: string) {
  const response = await fetch(
    `${API_ENDPOINT}/agent/query`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY!,
      },
      body: JSON.stringify({ text, sessionId }),
    }
  );
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}

export async function executeAction(actionId: string, payload?: any) {
  const response = await fetch(
    `${API_ENDPOINT}/agent/action`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY!,
      },
      body: JSON.stringify({ actionId, payload }),
    }
  );
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}
```


**3. React Hook Example**

```typescript
// hooks/useEventUpdates.ts
import { useState, useEffect } from 'react';
import { getUpdates } from '@/lib/api-client';

export function useEventUpdates(pollInterval = 5000) {
  const [events, setEvents] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(new Date().toISOString());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUpdates = async () => {
      try {
        setLoading(true);
        const data = await getUpdates(lastUpdate);
        
        if (data.mapUpdates?.mapLayers) {
          // Append new events
          setEvents(prev => [...prev, ...data.mapUpdates.mapLayers]);
        }
        
        if (data.latestTimestamp) {
          setLastUpdate(data.latestTimestamp);
        }
        
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchUpdates();

    // Poll for updates
    const interval = setInterval(fetchUpdates, pollInterval);

    return () => clearInterval(interval);
  }, [lastUpdate, pollInterval]);

  return { events, loading, error };
}
```

**4. Component Example**

```typescript
// components/ChatInterface.tsx
import { useState } from 'react';
import { queryAgent } from '@/lib/api-client';

export function ChatInterface() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = await queryAgent(query);
      setResponse(data);
      
      // Update map with response data
      if (data.mapLayers) {
        // updateMap(data.mapLayers, data.viewState);
      }
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about the situation..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Send'}
        </button>
      </form>
      
      {response && (
        <div>
          <p>{response.chatResponse}</p>
          {response.uiContext?.suggestedActions && (
            <div>
              {response.uiContext.suggestedActions.map(action => (
                <button key={action.actionId}>
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Vanilla JavaScript Example

```javascript
// api.js
const API_ENDPOINT = 'https://your-api.com';
const API_KEY = 'your-api-key';

async function getUpdates(since, domain = null) {
  const params = new URLSearchParams({ since });
  if (domain) params.append('domain', domain);
  
  const response = await fetch(
    `${API_ENDPOINT}/data/updates?${params}`,
    {
      headers: {
        'x-api-key': API_KEY,
      },
    }
  );
  
  return response.json();
}

async function queryAgent(text) {
  const response = await fetch(
    `${API_ENDPOINT}/agent/query`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
      },
      body: JSON.stringify({ text }),
    }
  );
  
  return response.json();
}

// Usage
getUpdates('2023-02-06T00:00:00Z')
  .then(data => console.log(data))
  .catch(error => console.error(error));

queryAgent('Show critical incidents')
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

---

## 🚦 Rate Limits

| Endpoint | Limit | Window | Burst |
|----------|-------|--------|-------|
| `/data/updates` | 100 req/min | Per API key | 200 req/10s |
| `/agent/query` | 20 req/min | Per API key | 30 req/10s |
| `/agent/action` | 20 req/min | Per API key | 30 req/10s |

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

**When Rate Limited**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds."
  }
}
```

**Best Practices**:
- Implement exponential backoff
- Cache responses when possible
- Use `/data/updates` polling instead of frequent queries
- Batch requests when possible

---

## 🔧 CORS Configuration

**Allowed Origins**: Configured during deployment  
**Allowed Methods**: `GET`, `POST`, `OPTIONS`  
**Allowed Headers**: `Content-Type`, `x-api-key`  
**Max Age**: 3600 seconds

---

## 📝 Icon Reference

Available icons for Point layer styling:

| Icon Name | Use Case |
|-----------|----------|
| `BUILDING_COLLAPSE` | Structural damage |
| `MEDICAL_EMERGENCY` | Medical incidents |
| `FIRE` | Fire incidents |
| `FOOD_SUPPLY` | Food distribution |
| `WATER_SUPPLY` | Water distribution |
| `SHELTER` | Emergency shelters |
| `HOSPITAL` | Medical facilities |
| `AMBULANCE` | Medical transport |
| `FIRE_TRUCK` | Fire response |
| `SEARCH_RESCUE` | Search and rescue |

---

## 🆘 Support

**Troubleshooting**:
- Check [DEPLOYMENT.md](./DEPLOYMENT.md#-troubleshooting) for common issues
- View CloudWatch logs for detailed errors
- Verify API key is correct

**Testing**:
```bash
./test-api.sh
```

**Logs**:
```bash
aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow
```

---

**API Version**: v1.0.0  
**Last Updated**: 2025-10-16
