# Lambda Functions

This directory contains the Lambda function handlers for the Command Center Backend API.

## updatesHandler.ts

**Endpoint**: `GET /data/updates`

**Purpose**: Retrieves event updates based on time and optional domain filters. Returns lean JSON structure with map layers and critical alerts.

**Query Parameters**:
- `since` (required): ISO 8601 timestamp - returns all events after this timestamp
- `domain` (optional): Domain filter - one of `MEDICAL`, `FIRE`, `STRUCTURAL`, `LOGISTICS`, `COMMUNICATION`

**Response Structure**:
```typescript
{
  latestTimestamp: string;
  mapUpdates?: {
    mapAction: "APPEND";
    mapLayers: MapLayer[];
  };
  criticalAlerts?: Alert[];
}
```

**Features**:
- ✅ Query parameter parsing and validation using Zod
- ✅ Efficient DynamoDB queries using GSI for domain filtering
- ✅ Transforms database results to map layers grouped by domain and layer type
- ✅ Extracts critical alerts from high-severity events
- ✅ Comprehensive error handling with appropriate HTTP status codes
- ✅ Structured logging to CloudWatch
- ✅ CORS headers for cross-origin requests
- ✅ Performance monitoring (query duration, transformation duration)

**Error Codes**:
- `INVALID_REQUEST` (400): Malformed query parameters
- `DATABASE_ERROR` (500): DynamoDB query failed
- `CONFIGURATION_ERROR` (500): Missing environment variables
- `TIMEOUT_ERROR` (504): Request timed out
- `INTERNAL_ERROR` (500): Unexpected server error

**Environment Variables**:
- `TABLE_NAME`: DynamoDB table name
- `LOG_LEVEL`: Logging verbosity (INFO or DEBUG)

**Performance**:
- Target: <500ms response time for 95% of requests
- Memory: 512 MB
- Timeout: 30 seconds

## databaseQueryTool.ts

**Endpoint**: Bedrock Agent Action Group Tool (not directly accessible via API Gateway)

**Purpose**: Provides database query capabilities to the Bedrock Agent for natural language query processing. This Lambda is invoked by the Bedrock Agent when it needs to retrieve data from the simulation database.

**Input Parameters** (from Bedrock Agent):
```typescript
{
  domain?: string;           // MEDICAL | FIRE | STRUCTURAL | LOGISTICS | COMMUNICATION
  severity?: string;         // CRITICAL | HIGH | MEDIUM | LOW
  startTime?: string;        // ISO 8601 timestamp
  endTime?: string;          // ISO 8601 timestamp
  location?: {
    lat: number;
    lon: number;
    radiusKm?: number;       // Default: 10km
  };
  limit?: number;            // Default: 100
}
```

**Response Structure**:
```typescript
{
  events: RawEvent[];
  count: number;
}
```

**Features**:
- ✅ Input validation using Zod schema
- ✅ Efficient DynamoDB querying with GSI support for domain filtering
- ✅ Multi-day querying when no domain is specified
- ✅ Geospatial filtering using Haversine distance calculation
- ✅ Supports Point, Polygon, and LineString geometries
- ✅ Structured error responses for agent interpretation
- ✅ Comprehensive logging for debugging tool invocations
- ✅ Automatic limit enforcement to prevent large responses

**Geospatial Filtering**:
The tool implements location-based filtering using the Haversine formula to calculate distances between coordinates. It:
1. Extracts coordinates from GeoJSON geometries (Point, Polygon, LineString)
2. Calculates distance from target location to each event
3. Filters events within the specified radius (default 10km)

**Error Responses**:
- `INVALID_PARAMETERS`: Invalid or missing required parameters
- `TOOL_EXECUTION_ERROR`: Unexpected error during execution

**Environment Variables**:
- `TABLE_NAME`: DynamoDB table name
- `LOG_LEVEL`: Logging verbosity (INFO or DEBUG)

**Performance**:
- Memory: 512 MB
- Timeout: 30 seconds
- Default limit: 100 events to prevent large responses

## Building

Lambda functions are compiled with the rest of the project:

```bash
npm run build
```

This compiles TypeScript to JavaScript in the `dist/` directory.

## Deployment

Lambda functions are deployed as part of the CDK stack:

```bash
npm run deploy
```

The CDK stack automatically:
1. Creates the Lambda function with appropriate IAM role
2. Configures environment variables
3. Sets up CloudWatch logging
4. Grants DynamoDB read permissions
