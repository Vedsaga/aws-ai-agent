# Frontend Integration Summary

## Quick Start for Dashboard Team

This document provides everything the frontend team needs to integrate with the Command Center Backend API.

---

## 🚀 What You Need

### 1. API Configuration

```bash
# Add to command-center-dashboard/.env.local
NEXT_PUBLIC_API_BASE_URL=https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_API_KEY=your-api-key-here
```

**Get these values from the backend team** after deployment.

### 2. New API Service File

We've created `command-center-dashboard/services/apiService.ts` for you. This replaces the mock API service.

### 3. Update Your Imports

Change this:
```typescript
import { mockApiService } from '../services/mockApiService';
```

To this:
```typescript
import { apiService } from '../services/apiService';
```

---

## 📋 API Methods

The real API service has the same interface as the mock:

### Get Initial Load
```typescript
const data = await apiService.getInitialLoad();
```

### Post Query
```typescript
const response = await apiService.postQuery(
  'Show me critical medical incidents',
  sessionId,        // optional: for conversation continuity
  currentMapState   // optional: current map view
);
```

### Execute Action
```typescript
const response = await apiService.executeAction(
  'GENERATE_AREA_BRIEFING',
  { area: 'Nurdağı' }
);
```

### Get Updates
```typescript
const updates = await apiService.getUpdates(
  lastTimestamp,
  activeDomainFilter  // optional: MEDICAL, FIRE, etc.
);
```

---

## 🔧 Required Code Changes

### 1. Update Component Imports

Files to update:
- `app/page.tsx`
- `components/ChatPanel.tsx`
- `components/InteractionPanel.tsx`

### 2. Add Error Handling

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
    switch (error.code) {
      case 'RATE_LIMIT_EXCEEDED':
        showError('Too many requests. Please wait a moment.');
        break;
      case 'AUTHENTICATION_FAILED':
        showError('API authentication failed. Check configuration.');
        break;
      default:
        showError('Failed to process request. Please try again.');
    }
  } else {
    // Network error
    showError('Failed to connect to backend.');
  }
}
```

### 3. Add Health Check (Optional)

```typescript
useEffect(() => {
  async function checkApi() {
    const isHealthy = await apiService.healthCheck();
    if (!isHealthy) {
      console.warn('Backend API not available');
      // Show warning banner
    }
  }
  checkApi();
}, []);
```

---

## 📊 Response Formats

### Updates Response

```typescript
{
  latestTimestamp: "2023-02-06T12:30:00Z",
  mapUpdates?: {
    mapAction: "APPEND" | "REPLACE",
    mapLayers: [
      {
        layerId: "incidents-medical",
        layerName: "Medical Incidents",
        geometryType: "Point",
        style: {
          icon: "MEDICAL_EMERGENCY",
          color: "#DC2626",
          size: 8
        },
        data: {
          type: "FeatureCollection",
          features: [...]
        }
      }
    ]
  },
  criticalAlerts?: [
    {
      alertId: "alert-123",
      timestamp: "2023-02-06T12:15:00Z",
      severity: "CRITICAL",
      title: "Medical Emergency",
      summary: "Multiple casualties reported",
      location: { lat: 37.4567, lon: 37.0123 }
    }
  ]
}
```

### Query/Action Response

```typescript
{
  simulationTime: "Day 1, 12:30",
  timestamp: "2023-02-06T12:30:00Z",
  chatResponse: "I found 8 critical medical incidents...",
  mapAction: "REPLACE" | "APPEND",
  viewState?: {
    bounds?: {
      southwest: { lat: 37.1, lon: 36.8 },
      northeast: { lat: 37.6, lon: 37.3 }
    },
    center?: { lat: 37.4, lon: 37.0 },
    zoom?: 10
  },
  mapLayers: [...],
  uiContext?: {
    suggestedActions: [
      {
        label: "Show available medical resources",
        actionId: "SHOW_MEDICAL_RESOURCES",
        payload: { domain: "MEDICAL" }
      }
    ]
  }
}
```

---

## ✅ Testing Checklist

### Basic Tests
- [ ] Dashboard loads with real data
- [ ] Can send query: "What are the most urgent needs?"
- [ ] AI responds with real data
- [ ] Map updates with query results
- [ ] Critical alerts appear

### Query Tests
- [ ] "Show me medical incidents"
- [ ] "What's happening in Nurdağı?"
- [ ] "Show me incidents from the last 6 hours"

### Action Tests
- [ ] Click "Generate Area Briefing"
- [ ] Click suggested actions from AI

### Map Tests
- [ ] Map layers render correctly
- [ ] Map zooms to relevant areas
- [ ] REPLACE action clears previous layers
- [ ] APPEND action adds to existing layers

### Error Tests
- [ ] Test with invalid API key (should show error)
- [ ] Test with network disconnected (should handle gracefully)

---

## 🐛 Common Issues

### CORS Error
**Problem**: `Access to fetch blocked by CORS policy`

**Solution**: Contact backend team to add your dashboard URL to allowed origins.

### 401 Unauthorized
**Problem**: `Invalid API key`

**Solution**: 
1. Verify API key in `.env.local` is correct
2. Ensure `.env.local` is not in `.gitignore`
3. Restart dev server after changing `.env.local`

### Slow Responses
**Problem**: Queries take > 5 seconds

**Solution**: 
1. Add loading indicators
2. Implement request timeout
3. Contact backend team if persistent

### Map Not Updating
**Problem**: Map doesn't show query results

**Solution**:
1. Check browser console for errors
2. Verify `mapLayers` data structure
3. Check GeoJSON coordinates are [lon, lat] not [lat, lon]

---

## 📞 Getting Help

### Documentation
- **API Reference**: `API_DOCUMENTATION.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Integration Checklist**: `INTEGRATION_CHECKLIST.md`

### Testing
- **Test Script**: `scripts/test-integration.sh`
- **Postman Collection**: `postman_collection.json`
- **OpenAPI Spec**: `openapi.yaml`

### Support
- Backend team contact: [Contact info]
- Check backend logs: CloudWatch
- Check frontend errors: Browser console

---

## 🎯 Next Steps

1. **Get API credentials** from backend team
2. **Update `.env.local`** with API endpoint and key
3. **Copy `apiService.ts`** to your services directory
4. **Update imports** in your components
5. **Add error handling** to API calls
6. **Test basic functionality**
7. **Run through testing checklist**
8. **Report any issues** to backend team

---

## 📝 Example Integration

Here's a complete example of updating a component:

### Before (Mock API)
```typescript
import { mockApiService } from '../services/mockApiService';

export default function ChatPanel() {
  const handleQuery = async (query: string) => {
    const response = await mockApiService.postQuery(query, timestamp);
    // Handle response
  };
  
  return <div>...</div>;
}
```

### After (Real API)
```typescript
import { apiService, ApiServiceError } from '../services/apiService';

export default function ChatPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleQuery = async (query: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.postQuery(
        query,
        sessionId,
        currentMapState
      );
      // Handle response
    } catch (err) {
      if (err instanceof ApiServiceError) {
        setError(err.message);
      } else {
        setError('Failed to connect to backend');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      {loading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} />}
      {/* ... rest of component */}
    </div>
  );
}
```

---

## 🎉 You're Ready!

Once you've completed the integration:

1. ✅ Dashboard loads with real backend data
2. ✅ AI queries work and return intelligent responses
3. ✅ Map updates dynamically based on queries
4. ✅ Actions execute correctly
5. ✅ Error handling works gracefully

**Welcome to the integrated Command Center!** 🚀

---

**Questions?** Contact the backend team or refer to the detailed documentation.

**Last Updated**: [Current Date]
