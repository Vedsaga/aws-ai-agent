# Command Center Backend API Documentation

## Overview

The Command Center Backend API provides real-time event updates and AI-powered query capabilities for disaster response operations. The API is built on AWS serverless infrastructure and serves data from a 7-day pre-processed earthquake response simulation timeline.

**Base URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

**Authentication**: API Key (passed in `x-api-key` header)

**Content Type**: `application/json`

---

## Authentication

All API requests require an API key to be included in the request headers:

```http
x-api-key: your-api-key-here
```

### Getting Your API Key

After deployment, the API key is available in:
- AWS Console: API Gateway → API Keys
- CDK Output: Check the deployment output for `ApiKeyId`
- AWS CLI: `aws apigateway get-api-keys --include-values`

### Example Request with Authentication

```bash
curl -X GET "https://your-api-url.com/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: your-api-key-here"
```

---

## Endpoints

### 1. GET /data/updates

Retrieve event updates based on time and optional domain filters. This endpoint provides incremental updates for real-time dashboard synchronization.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `since` | string | Yes | ISO 8601 timestamp. Returns events after this time. |
| `domain` | string | No | Filter by domain: `MEDICAL`, `FIRE`, `STRUCTURAL`, `LOGISTICS`, `COMMUNICATION` |

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
      "summary": "Multiple casualties reported at collapsed building",
      "location": {
        "lat": 37.4567,
        "lon": 37.0123
      }
    }
  ]
}
```

**Example Requests**:

```bash
# Get all updates since a specific time
curl -X GET "https://your-api-url.com/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: your-api-key-here"

# Get medical domain updates only
curl -X GET "https://your-api-url.com/data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
  -H "x-api-key: your-api-key-here"
```

**Performance**: Typical response time < 500ms

---

### 2. POST /agent/query

Process natural language queries using AI to retrieve and synthesize information from the simulation database.

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

**Response**: `200 OK`

```json
{
  "simulationTime": "Day 1, 12:30",
  "timestamp": "2023-02-06T12:30:00Z",
  "chatResponse": "I found 8 critical medical incidents in the last 6 hours. The most severe are concentrated in Nurdağı district with 5 building collapses requiring immediate medical attention. 3 additional incidents are in İslahiye.",
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
        "features": [
          {
            "type": "Feature",
            "geometry": {
              "type": "Point",
              "coordinates": [37.0123, 37.4567]
            },
            "properties": {
              "eventId": "evt-789",
              "severity": "CRITICAL",
              "summary": "Building collapse - 15 trapped",
              "timestamp": "2023-02-06T10:45:00Z",
              "resourcesNeeded": ["MEDICAL_TEAM", "SEARCH_RESCUE"]
            }
          }
        ]
      }
    }
  ],
  "uiContext": {
    "suggestedActions": [
      {
        "label": "Show available medical resources",
        "actionId": "SHOW_MEDICAL_RESOURCES",
        "payload": { "domain": "MEDICAL" }
      },
      {
        "label": "Generate area briefing",
        "actionId": "GENERATE_AREA_BRIEFING",
        "payload": { "area": "Nurdağı" }
      }
    ]
  }
}
```

**Example Requests**:

```bash
# Simple query
curl -X POST "https://your-api-url.com/agent/query" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the most urgent needs right now?"
  }'

# Query with session continuity
curl -X POST "https://your-api-url.com/agent/query" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Show me the medical incidents",
    "sessionId": "session-123"
  }'
```

**Performance**: Typical response time < 3 seconds

---

### 3. POST /agent/action

Execute pre-defined actions that map to common queries. This provides quick access to frequently used operations.

**Request Body**:

```json
{
  "actionId": "GENERATE_AREA_BRIEFING",
  "payload": {
    "area": "Nurdağı",
    "includeResources": true
  }
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actionId` | string | Yes | Pre-defined action identifier |
| `payload` | object | No | Action-specific parameters |

**Common Action IDs**:

| Action ID | Description | Payload Parameters |
|-----------|-------------|-------------------|
| `GENERATE_AREA_BRIEFING` | Generate summary for specific area | `area` (string), `includeResources` (boolean) |
| `SHOW_CRITICAL_INCIDENTS` | Show all critical severity incidents | `domain` (string, optional) |
| `CALC_ROUTE` | Calculate route between locations | `from` (coordinates), `to` (coordinates) |
| `SHOW_MEDICAL_RESOURCES` | Display available medical resources | `radius` (number, optional) |
| `SHOW_SUPPLY_GAPS` | Identify areas with supply shortages | `supplyType` (string) |

**Response**: Same structure as `/agent/query`

**Example Requests**:

```bash
# Generate area briefing
curl -X POST "https://your-api-url.com/agent/action" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "actionId": "GENERATE_AREA_BRIEFING",
    "payload": {
      "area": "Nurdağı"
    }
  }'

# Show critical incidents
curl -X POST "https://your-api-url.com/agent/action" \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "actionId": "SHOW_CRITICAL_INCIDENTS",
    "payload": {
      "domain": "MEDICAL"
    }
  }'
```

---

## Error Responses

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

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request or missing required fields |
| 401 | `AUTHENTICATION_FAILED` | Invalid or missing API key |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `DATABASE_ERROR` | DynamoDB query failed |
| 500 | `AGENT_ERROR` | Bedrock Agent invocation failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

### Example Error Responses

**400 Bad Request - Missing Required Parameter**:
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

## Data Models

### MapLayer

Represents a layer of geographic data to be displayed on the map.

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
    fillOpacity?: number;       // Opacity (0-1) for Polygon layers
  };
  data: GeoJSON.FeatureCollection;
}
```

### Alert

Represents a critical alert that requires attention.

```typescript
interface Alert {
  alertId: string;
  timestamp: string;            // ISO 8601
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  title: string;
  summary: string;
  location: {
    lat: number;
    lon: number;
  };
}
```

### ViewState

Controls the map viewport.

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

## Icon Reference

Available icons for Point layer styling:

| Icon Name | Use Case |
|-----------|----------|
| `BUILDING_COLLAPSE` | Structural damage |
| `MEDICAL_EMERGENCY` | Medical incidents |
| `FIRE` | Fire incidents |
| `FOOD_SUPPLY` | Food distribution points |
| `WATER_SUPPLY` | Water distribution points |
| `DONATION_POINT` | Donation collection centers |
| `SHELTER` | Emergency shelters |
| `HOSPITAL` | Medical facilities |
| `AMBULANCE` | Medical transport |
| `FIRE_TRUCK` | Fire response vehicles |
| `SEARCH_RESCUE` | Search and rescue teams |
| `COMMUNICATION_TOWER` | Communication infrastructure |

---

## Rate Limits

- **Default**: 100 requests per minute per API key
- **Burst**: Up to 200 requests in a 10-second window
- **Agent endpoints**: 20 requests per minute (due to AI processing costs)

When rate limited, the API returns HTTP 429 with a `Retry-After` header.

---

## CORS Configuration

The API supports cross-origin requests from approved dashboard origins:

**Allowed Origins**: Configured during deployment
**Allowed Methods**: `GET`, `POST`, `OPTIONS`
**Allowed Headers**: `Content-Type`, `x-api-key`
**Max Age**: 3600 seconds

---

## Versioning

Current API version: **v1**

The API version is included in the base URL path. Future versions will be released as `/v2`, `/v3`, etc., with backward compatibility maintained for at least 6 months.

---

## Support and Contact

For API issues or questions:
- Check the troubleshooting guide in `DEPLOYMENT_GUIDE.md`
- Review CloudWatch logs for detailed error information
- Contact: [Your team contact information]

---

## Changelog

### v1.0.0 (Initial Release)
- GET /data/updates endpoint
- POST /agent/query endpoint
- POST /agent/action endpoint
- API key authentication
- 7-day simulation timeline data
