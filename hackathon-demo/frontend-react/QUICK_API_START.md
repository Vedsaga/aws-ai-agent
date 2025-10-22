# Quick Start - API Integration

## 🚀 Get Started in 5 Minutes

### Step 1: Check Environment Variables

Create or update `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_REGION=us-east-1
```

### Step 2: Submit a Report with Auto-Polling

```typescript
import { apiService } from '@/lib/api-service';
import { useJobPolling } from '@/hooks/use-job-polling';
import { useState } from 'react';

function MyReportForm() {
  const [text, setText] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  // Auto-polling hook (2.5 second intervals)
  const { status, isPolling, progress } = useJobPolling({
    jobId,
    intervalMs: 2500,
    onComplete: (result) => {
      console.log('Done!', result);
      // Add to chat, update map, etc.
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await apiService.submitReport(
      'civic_complaints',
      text,
      { priority: 'normal' }
    );

    if (result.success) {
      setJobId(result.jobId!);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea 
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={isPolling}
      />
      
      {isPolling && (
        <div>
          <progress value={progress} max={100} />
          <p>{status?.message}</p>
        </div>
      )}
      
      <button disabled={isPolling}>Submit</button>
    </form>
  );
}
```

### Step 3: Submit a Query

```typescript
function MyQueryForm() {
  const [question, setQuestion] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const { status, isPolling } = useJobPolling({
    jobId,
    intervalMs: 2500,
    onComplete: (result) => {
      // Show answer in chat
      console.log('Answer:', result.result?.answer);
      
      // Show data on map
      if (result.result?.data) {
        updateMap(result.result.data);
      }
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await apiService.submitQuery(
      'civic_complaints',
      question
    );

    if (result.success) {
      setJobId(result.jobId!);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isPolling}
      />
      <button disabled={isPolling}>Ask</button>
    </form>
  );
}
```

### Step 4: Load and Display Incidents on Map

```typescript
import { useEffect, useState } from 'react';
import { apiService } from '@/lib/api-service';
import type { IncidentRecord } from '@/lib/api-types';

function IncidentMap() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    const data = await apiService.fetchIncidents('civic_complaints', {
      status: ['completed']
    });
    setIncidents(data);
  };

  return (
    <Map>
      {incidents.map(incident => (
        incident.location && (
          <Marker
            key={incident.incident_id}
            coordinates={incident.location.coordinates}
            onClick={() => {
              // Show popup
              alert(`${incident.category}: ${incident.raw_text}`);
            }}
          />
        )
      ))}
    </Map>
  );
}
```

### Step 5: Manage Domains

```typescript
import { useEffect, useState } from 'react';
import { apiService } from '@/lib/api-service';
import type { DomainConfig } from '@/lib/api-types';

function DomainManager() {
  const [domains, setDomains] = useState<DomainConfig[]>([]);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    const data = await apiService.listDomains();
    setDomains(data);
  };

  const createNewDomain = async () => {
    const success = await apiService.createDomain({
      domain_id: 'my_domain',
      name: 'My Domain',
      description: 'Custom domain',
      ingest_agents: ['geo_agent', 'temporal_agent'],
      query_agents: ['what_agent', 'where_agent']
    });

    if (success) {
      loadDomains(); // Reload
    }
  };

  return (
    <div>
      {domains.map(domain => (
        <div key={domain.domain_id}>
          {domain.icon} {domain.name}
        </div>
      ))}
      <button onClick={createNewDomain}>Create Domain</button>
    </div>
  );
}
```

---

## 🔧 Common Patterns

### Pattern 1: Submit → Poll → Display

```typescript
const [jobId, setJobId] = useState<string | null>(null);
const [result, setResult] = useState<any>(null);

const { isPolling } = useJobPolling({
  jobId,
  intervalMs: 2500,
  onComplete: (status) => {
    setResult(status.result);
    // Display in UI
  }
});

// Submit
const submit = async () => {
  const res = await apiService.submitReport(...);
  if (res.success) setJobId(res.jobId!);
};
```

### Pattern 2: Load Data with Fallback

```typescript
import { initGuard } from '@/lib/init-guard';
import { DEFAULT_DOMAINS } from '@/lib/domains-config';

useEffect(() => {
  const load = async () => {
    const ready = await initGuard.ensureReady({ skipIfInvalid: true });
    
    if (ready) {
      // API is ready
      const data = await apiService.listDomains();
      setDomains(data);
    } else {
      // Use fallback
      setDomains(DEFAULT_DOMAINS);
    }
  };
  load();
}, []);
```

### Pattern 3: Update Map on New Data

```typescript
const { status } = useJobPolling({
  jobId,
  onComplete: (result) => {
    if (result.result?.location) {
      // Add marker
      addMarker(result.result.location);
      
      // Zoom to location
      map.flyTo({
        center: result.result.location.coordinates,
        zoom: 15
      });
    }
  }
});
```

---

## 📋 API Quick Reference

### Submit Report
```typescript
await apiService.submitReport(domainId, text, {
  images: [],
  priority: 'high',
  source: 'web'
});
```

### Submit Query
```typescript
await apiService.submitQuery(domainId, question, {
  filters: { date_range: {...} }
});
```

### Poll Status (Manual)
```typescript
apiService.startPolling(jobId, (status) => {
  console.log(status.progress);
}, 2500);
```

### Load Data
```typescript
const incidents = await apiService.fetchIncidents(domainId);
const queries = await apiService.fetchQueries(domainId);
const domains = await apiService.listDomains();
const agents = await apiService.listAgents();
```

### CRUD Operations
```typescript
// Domains
await apiService.createDomain(config);
await apiService.updateDomain(id, config);
await apiService.deleteDomain(id);

// Agents
await apiService.createAgent(config);
await apiService.updateAgent(id, config);
await apiService.deleteAgent(id);
```

---

## 🐛 Troubleshooting

### Network Error on Load
✅ **FIXED** - The app now checks if API is configured before making calls.

If you still see issues:
1. Check `.env.local` has valid `NEXT_PUBLIC_API_URL`
2. Restart dev server: `npm run dev`
3. Clear browser cache

### Polling Never Completes
- Check backend is running
- Check job_id is correct
- Increase `maxAttempts` in polling hook

### No Data on Map
- Ensure incidents have `location` field
- Check coordinates format: `[longitude, latitude]`
- Verify `fetchIncidents` filter includes completed items

---

## ✅ Checklist

Before integrating:
- [ ] `.env.local` configured with valid API URL
- [ ] Cognito credentials set (for auth)
- [ ] Backend APIs deployed
- [ ] Test API with: `curl $NEXT_PUBLIC_API_URL/api/v1/config?type=domain`

For each form:
- [ ] Import `apiService` or `useJobPolling`
- [ ] Submit request → get job_id
- [ ] Start polling with 2-3 second interval
- [ ] Display progress/status during polling
- [ ] Handle completion (show in chat/map)
- [ ] Handle errors gracefully

---

## 🎯 Next Steps

1. **Update existing forms** to use `apiService` and `useJobPolling`
2. **Add progress indicators** during polling
3. **Implement map popups** on marker click
4. **Add auto-zoom** when new data appears
5. **Test all flows** end-to-end

---

## 📚 Full Documentation

- `API_INTEGRATION_GUIDE.md` - Complete API documentation
- `INTEGRATION_COMPLETE.md` - Implementation summary
- `lib/api-types.ts` - All TypeScript types
- `lib/api-client.ts` - API client functions
- `lib/api-service.ts` - High-level service
- `hooks/use-job-polling.ts` - Polling hooks

---

## 💡 Pro Tips

1. **Always use the polling hook** instead of manual polling for cleaner code
2. **Set `skipIfInvalid: true`** when loading data to prevent errors
3. **Use `apiService`** for common operations, it handles errors better
4. **Poll at 2500ms (2.5s)** for reports, 2000ms for queries
5. **Always cleanup** polling on component unmount (hook does this automatically)

---

**You're ready to integrate!** 🚀

Start with one form, test it end-to-end, then apply the same pattern to other components.