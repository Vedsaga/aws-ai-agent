# Backend-Dashboard Integration Guide

## Overview

This guide explains how to integrate the Command Center Backend API with the Command Center Dashboard frontend application.

---

## Prerequisites

Before integration:

1. ✅ Backend API deployed to AWS
2. ✅ API endpoint URL available
3. ✅ API key retrieved
4. ✅ Database populated with simulation data
5. ✅ Backend API tested and verified working

---

## Step 1: Configure Dashboard Environment

### 1.1 Update Dashboard Environment Variables

In the `command-center-dashboard` directory, update `.env.local`:

```bash
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_API_KEY=your-api-key-here

# Optional: Enable/disable mock mode
NEXT_PUBLIC_USE_MOCK_API=false
```

**Important**: Replace the placeholder values with your actual API endpoint and key from the backend deployment.

### 1.2 Get Your API Configuration

From your backend deployment outputs:

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Get API key ID
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text

# Get API key value
aws apigateway get-api-key \
  --api-key YOUR_API_KEY_ID \
  --include-value \
  --query 'value' \
  --output text
```

---

## Step 2: Update Dashboard Code

### 2.1 Replace Mock API Service

The dashboard currently uses `mockApiService.ts`. We've created a real `apiService.ts` that you can use.

**Option A: Direct Replacement (Recommended)**

Update all imports in your dashboard components:

```typescript
// Before
import { mockApiService } from '../services/mockApiService';

// After
import { apiService } from '../services/apiService';
```

Files to update:
- `app/page.tsx`
- `components/ChatPanel.tsx`
- `components/InteractionPanel.tsx`
- Any other files using the API service

**Option B: Conditional API Service**

Create a wrapper that switches between mock and real API:

```typescript
// services/index.ts
import { mockApiService } from './mockApiService';
import { apiService } from './apiService';

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === 'true';

export const api = USE_MOCK ? mockApiService : apiService;
```

Then import from the wrapper:
```typescript
import { api } from '../services';
```

### 2.2 Update API Call Sites

The real API service has the same interface as the mock, but with some enhancements:

```typescript
// Get initial load
const data = await apiService.getInitialLoad();

// Post query with optional session ID
const response = await apiService.postQuery(
  'Show me critical medical incidents',
  sessionId,  // optional
  currentMapState  // optional
);

// Execute action
const response = await apiService.executeAction(
  'GENERATE_AREA_BRIEFING',
  { area: 'Nurdağı' }
);

// Get updates
const updates = await apiService.getUpdates(
  lastTimestamp,
  activeDomainFilter  // optional
);
```

### 2.3 Add Error Handling

The real API can throw errors. Update your components to handle them:

```typescript
import { apiService, ApiServiceError } from '../services/apiService';

try {
  const response = await apiService.postQuery(query);
  // Handle success
} catch (error) {
  if (error instanceof ApiServiceError) {
    // Handle API error
    console.error(`API Error [${error.code}]:`, error.message);
    
    // Show user-friendly message
    if (error.code === 'RATE_LIMIT_EXCEEDED') {
      alert('Too many requests. Please wait a moment.');
    } else if (error.code === 'AUTHENTICATION_FAILED') {
      alert('API authentication failed. Check your API key.');
    } else {
      alert('Failed to process request. Please try again.');
    }
  } else {
    // Handle network error
    console.error('Network error:', error);
    alert('Failed to connect to backend. Check your connection.');
  }
}
```

---

## Step 3: Verify Integration

### 3.1 Health Check

Add a health check on dashboard startup:

```typescript
// In your main page component
useEffect(() => {
  async function checkApi() {
    const isHealthy = await apiService.healthCheck();
    if (!isHealthy) {
      console.warn('Backend API is not available. Check configuration.');
      // Optionally show a warning banner
    }
  }
  checkApi();
}, []);
```

### 3.2 Test Basic Functionality

1. **Start the dashboard**:
   ```bash
   cd command-center-dashboard
   npm run dev
   ```

2. **Test initial load**:
   - Dashboard should load with real data from backend
   - Map should show incidents from the simulation

3. **Test queries**:
   - Type a query in the chat: "Show me medical incidents"
   - Verify AI responds with real data
   - Check that map updates with query results

4. **Test updates**:
   - Let the dashboard run for a minute
   - Verify it polls for updates
   - Check that new events appear on the map

5. **Test actions**:
   - Click any suggested action button
   - Verify the action executes and returns results

### 3.3 Check Browser Console

Open browser DevTools and check for:
- ✅ No API errors
- ✅ Successful API responses
- ✅ Proper data structure in responses
- ❌ No CORS errors
- ❌ No authentication errors

---

## Step 4: Data Contract Verification

### 4.1 Verify Response Structures

The backend returns data in specific formats. Verify your dashboard handles them correctly:

**Updates Response**:
```typescript
{
  latestTimestamp: string;
  mapUpdates?: {
    mapAction: "APPEND" | "REPLACE";
    mapLayers: MapLayer[];
  };
  criticalAlerts?: Alert[];
}
```

**Query/Action Response**:
```typescript
{
  simulationTime: string;
  timestamp: string;
  chatResponse: string;
  mapAction: "REPLACE" | "APPEND";
  viewState?: ViewState;
  mapLayers: MapLayer[];
  tabularData?: any;
  uiContext?: {
    suggestedActions?: Action[];
  };
  clientStateHint?: {
    activeDomainFilter?: string;
  };
}
```

### 4.2 Update Type Definitions

Ensure your TypeScript types match the backend contracts:

```typescript
// types/api.ts
export interface MapLayer {
  layerId: string;
  layerName: string;
  geometryType: 'Point' | 'Polygon' | 'LineString';
  style: {
    icon?: string;
    color?: string;
    size?: number;
    fillColor?: string;
    fillOpacity?: number;
  };
  data: GeoJSON.FeatureCollection;
}

export interface Alert {
  alertId: string;
  timestamp: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  summary: string;
  location: {
    lat: number;
    lon: number;
  };
}

// ... other types
```

---

## Step 5: End-to-End Testing

### 5.1 Manual Testing Checklist

Test these scenarios:

- [ ] **Initial Load**: Dashboard loads with real simulation data
- [ ] **Simple Query**: "What are the most urgent needs?"
- [ ] **Domain Query**: "Show me all medical incidents"
- [ ] **Location Query**: "What's happening in Nurdağı?"
- [ ] **Time Query**: "Show me incidents from the last 6 hours"
- [ ] **Action Execution**: Click "Generate Area Briefing"
- [ ] **Map Updates**: Verify map layers update correctly
- [ ] **Map Actions**: Test both REPLACE and APPEND actions
- [ ] **View State**: Verify map zooms/pans to relevant areas
- [ ] **Suggested Actions**: Click suggested action buttons
- [ ] **Session Continuity**: Ask follow-up questions
- [ ] **Polling Updates**: Let dashboard run, verify updates appear
- [ ] **Domain Filtering**: Filter by domain, verify updates respect filter
- [ ] **Critical Alerts**: Verify alerts appear in alerts panel
- [ ] **Error Handling**: Test with invalid API key (should show error)
- [ ] **Network Error**: Disconnect network, verify graceful handling

### 5.2 Automated Testing

Create integration tests:

```typescript
// __tests__/integration/api.test.ts
import { apiService } from '@/services/apiService';

describe('Backend API Integration', () => {
  it('should get initial load', async () => {
    const data = await apiService.getInitialLoad();
    expect(data).toHaveProperty('chatResponse');
    expect(data).toHaveProperty('mapLayers');
  });

  it('should post query', async () => {
    const response = await apiService.postQuery('Show me medical incidents');
    expect(response.chatResponse).toBeTruthy();
    expect(Array.isArray(response.mapLayers)).toBe(true);
  });

  it('should get updates', async () => {
    const updates = await apiService.getUpdates('2023-02-06T00:00:00Z');
    expect(updates).toHaveProperty('latestTimestamp');
  });
});
```

Run tests:
```bash
npm test
```

---

## Step 6: Performance Optimization

### 6.1 Implement Request Caching

Cache responses to reduce API calls:

```typescript
// Simple cache implementation
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 30000; // 30 seconds

async function cachedFetch(key: string, fetcher: () => Promise<any>) {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  const data = await fetcher();
  cache.set(key, { data, timestamp: Date.now() });
  return data;
}
```

### 6.2 Debounce Queries

Prevent excessive queries while user is typing:

```typescript
import { debounce } from 'lodash';

const debouncedQuery = debounce(async (query: string) => {
  const response = await apiService.postQuery(query);
  // Handle response
}, 500);
```

### 6.3 Optimize Polling

Adjust polling frequency based on activity:

```typescript
// Poll more frequently when active, less when idle
const ACTIVE_POLL_INTERVAL = 10000;  // 10 seconds
const IDLE_POLL_INTERVAL = 30000;    // 30 seconds

let pollInterval = ACTIVE_POLL_INTERVAL;

// Increase interval after period of inactivity
// Decrease when user interacts
```

---

## Step 7: Production Deployment

### 7.1 Update CORS Configuration

Ensure backend allows requests from your production dashboard URL:

In `command-center-backend/lib/command-center-backend-stack.ts`:

```typescript
// Add your production dashboard URL
const allowedOrigins = [
  'http://localhost:3000',  // Development
  'https://your-dashboard-domain.com',  // Production
];
```

Redeploy backend:
```bash
cd command-center-backend
cdk deploy
```

### 7.2 Secure API Key

For production:

1. **Never commit API keys** to version control
2. Use environment variables
3. Consider using AWS Secrets Manager for key rotation
4. Set up separate API keys for dev/staging/prod

### 7.3 Enable Monitoring

Add monitoring to track API usage:

```typescript
// Track API calls
const trackApiCall = (endpoint: string, duration: number, success: boolean) => {
  // Send to analytics service
  console.log(`API Call: ${endpoint}, Duration: ${duration}ms, Success: ${success}`);
};
```

---

## Troubleshooting

### Issue: CORS Error

**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution**:
1. Check backend CORS configuration
2. Ensure your dashboard URL is in allowed origins
3. Redeploy backend after updating CORS settings

### Issue: 401 Unauthorized

**Error**: `{"error": {"code": "AUTHENTICATION_FAILED", "message": "Invalid API key"}}`

**Solution**:
1. Verify API key in `.env.local` is correct
2. Check API key is not expired
3. Ensure `x-api-key` header is being sent

### Issue: Slow Response Times

**Error**: Queries take > 5 seconds

**Solution**:
1. Check backend CloudWatch logs for Lambda cold starts
2. Verify Bedrock Agent is responding quickly
3. Consider implementing loading states in UI
4. Add request timeout handling

### Issue: Map Not Updating

**Error**: Map doesn't show query results

**Solution**:
1. Check browser console for errors
2. Verify `mapLayers` data structure matches expected format
3. Check that `mapAction` is being handled correctly
4. Verify GeoJSON coordinates are valid

### Issue: Session Not Persisting

**Error**: Agent doesn't remember previous queries

**Solution**:
1. Ensure `sessionId` is being passed in subsequent queries
2. Generate and store session ID on first query
3. Check backend logs to verify session is being used

---

## Monitoring Integration Health

### Dashboard Metrics to Track

1. **API Response Times**
   - Initial load time
   - Query response time
   - Update polling time

2. **Error Rates**
   - Failed API calls
   - Authentication errors
   - Network errors

3. **User Experience**
   - Time to first meaningful paint
   - Time to interactive
   - Query success rate

### Backend Metrics to Monitor

1. **API Gateway**
   - Request count
   - Error rate (4xx, 5xx)
   - Latency (p50, p95, p99)

2. **Lambda Functions**
   - Invocation count
   - Error count
   - Duration
   - Cold starts

3. **DynamoDB**
   - Read capacity usage
   - Query latency
   - Throttled requests

4. **Bedrock Agent**
   - Invocation count
   - Success rate
   - Average response time
   - Cost per invocation

---

## Next Steps

After successful integration:

1. ✅ Conduct user acceptance testing
2. ✅ Gather feedback on AI responses
3. ✅ Optimize query patterns based on usage
4. ✅ Refine Bedrock Agent instructions
5. ✅ Add more pre-defined actions
6. ✅ Implement advanced features (session history, bookmarks, etc.)
7. ✅ Set up production monitoring and alerting
8. ✅ Document common queries and best practices
9. ✅ Train users on effective query formulation

---

## Support

For integration issues:

1. Check backend logs: `aws logs tail /aws/lambda/queryHandlerLambda --follow`
2. Check browser console for frontend errors
3. Review API documentation: `API_DOCUMENTATION.md`
4. Review deployment guide: `DEPLOYMENT_GUIDE.md`
5. Contact backend team: [Your contact info]

---

**Last Updated**: [Current Date]
**Version**: 1.0.0
