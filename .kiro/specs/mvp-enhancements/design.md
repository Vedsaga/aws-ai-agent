# Design Document

## Overview

This design document outlines the frontend enhancements needed to complete the MVP for the Multi-Agent Orchestration System. The backend is fully deployed and functional with all APIs operational. The focus is on implementing dark mode UI, error handling, domain management, data table views, and polishing the user experience for hackathon demonstration.

The implementation will use Shadcn UI components for consistent dark mode styling, integrate with existing backend APIs, and enhance the current dashboard layout (80% map, 20% chat) with additional features for domain creators and users.

## Architecture

### Current State (Deployed)

**Backend (100% Complete):**
- ✅ All APIs deployed and functional
- ✅ 14 built-in agents (3 ingestion, 11 query)
- ✅ 3 built-in domains (Civic Complaints, Disaster Response, Agriculture)
- ✅ Configuration API for agents, playbooks, dependency graphs
- ✅ Data APIs (retrieval, aggregation, spatial, analytics)
- ✅ Real-time status via AppSync WebSocket
- ✅ Authentication via Cognito

**Frontend (60% Complete):**
- ✅ Dashboard layout (80% map, 20% chat)
- ✅ Login page
- ✅ Agent creation form
- ✅ Dependency graph editor
- ✅ Map view with markers
- ✅ Ingestion panel
- ✅ Query panel
- ❌ Dark mode styling
- ❌ Error toast notifications
- ❌ Domain selector
- ❌ Data table view
- ❌ Role switching (Use vs Manage)

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Dark Mode Theme (Shadcn UI + Tailwind)              │  │
│  │  - Dark background colors                             │  │
│  │  - High contrast text                                 │  │
│  │  - Dark Mapbox style (dark-v11)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  View Mode Selector                                   │  │
│  │  ┌─────────────┐  ┌──────────────┐                  │  │
│  │  │ Use Domain  │  │ Manage Domain │                  │  │
│  │  └─────────────┘  └──────────────┘                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Use Domain Mode (Current Dashboard)                  │  │
│  │  ┌────────────────────┬──────────────────────────┐  │  │
│  │  │                    │  Domain Selector         │  │  │
│  │  │                    │  ┌────────────────────┐  │  │  │
│  │  │                    │  │ Civic Complaints ▼ │  │  │  │
│  │  │                    │  └────────────────────┘  │  │  │
│  │  │                    │                          │  │  │
│  │  │   Map View (80%)   │  Submit Report Tab      │  │  │
│  │  │   - Dark style     │  - Text input           │  │  │
│  │  │   - Markers        │  - Image upload         │  │  │
│  │  │   - Popups         │  - Real-time status     │  │  │
│  │  │                    │                          │  │  │
│  │  │                    │  Ask Question Tab       │  │  │
│  │  │                    │  - Query input          │  │  │
│  │  │                    │  - Bullet points        │  │  │
│  │  │                    │  - Summary              │  │  │
│  │  │                    │  (20%)                  │  │  │
│  │  └────────────────────┴──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Manage Domain Mode (New)                             │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Domain Selector + Data Table View             │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │ Filters: Date | Location | Category     │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │ ID | Location | Time | Category | ...   │  │  │  │
│  │  │  │ 1  | Main St  | 2h ago | Pothole | ...  │  │  │  │
│  │  │  │ 2  | Park Ave | 5h ago | Light   | ...  │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  │                                                │  │  │
│  │  │  Chat with Domain Data                        │  │  │
│  │  │  - Ask questions about data                   │  │  │
│  │  │  - View query results                         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Error Handling (Toast Notifications)                 │  │
│  │  - API errors                                          │  │
│  │  - Validation errors                                   │  │
│  │  - Agent execution failures                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS + JWT
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend APIs (Deployed)                     │
├─────────────────────────────────────────────────────────────┤
│  GET  /config?type=domain_template  - List domains          │
│  GET  /config?type=agent            - List agents           │
│  POST /config                       - Create agent/domain   │
│  POST /ingest                       - Submit report         │
│  POST /query                        - Ask question          │
│  GET  /data?type=retrieval          - Fetch incidents       │
│  WebSocket (AppSync)                - Real-time status      │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Dark Mode Theme System

**Technology:** Shadcn UI + Tailwind CSS

**Implementation:**
- Install Shadcn UI components with dark mode preset
- Configure Tailwind with dark mode class strategy
- Update all existing components to use Shadcn components
- Apply dark color palette consistently

**Color Palette:**
```css
:root {
  --background: 222.2 84% 4.9%;        /* Dark background */
  --foreground: 210 40% 98%;           /* Light text */
  --card: 222.2 84% 4.9%;              /* Card background */
  --card-foreground: 210 40% 98%;      /* Card text */
  --primary: 217.2 91.2% 59.8%;        /* Indigo accent */
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;      /* Secondary accent */
  --muted: 217.2 32.6% 17.5%;          /* Muted elements */
  --accent: 217.2 32.6% 17.5%;         /* Accent elements */
  --destructive: 0 62.8% 30.6%;        /* Error red */
  --border: 217.2 32.6% 17.5%;         /* Borders */
  --input: 217.2 32.6% 17.5%;          /* Input fields */
  --ring: 224.3 76.3% 48%;             /* Focus rings */
}
```

**Mapbox Dark Style:**
```typescript
mapboxgl.Map({
  style: 'mapbox://styles/mapbox/dark-v11',  // Dark map style
  // ... other config
})
```

### 2. Error Toast System

**Technology:** Shadcn Toast component

**Interface:**
```typescript
interface ToastOptions {
  title: string;
  description?: string;
  variant: 'default' | 'destructive' | 'success';
  duration?: number;
}

function showToast(options: ToastOptions): void;
```

**Usage Examples:**
```typescript
// API error
showToast({
  title: 'Failed to submit report',
  description: 'Network error. Please try again.',
  variant: 'destructive',
  duration: 5000
});

// Success
showToast({
  title: 'Report submitted successfully',
  variant: 'success',
  duration: 3000
});

// Validation error
showToast({
  title: 'Validation error',
  description: 'Please select a domain before submitting',
  variant: 'destructive'
});
```

**Integration Points:**
- API client error responses
- Form validation failures
- Agent execution failures (from AppSync)
- Network connectivity issues

### 3. Domain Selector Component

**Component:** `DomainSelector.tsx`

**Interface:**
```typescript
interface Domain {
  domain_id: string;
  template_name: string;
  description: string;
  ingestion_agents: number;
  query_agents: number;
}

interface DomainSelectorProps {
  selectedDomain: string | null;
  onDomainChange: (domainId: string) => void;
  className?: string;
}
```

**API Integration:**
```typescript
// Fetch domains on mount
const { data } = await apiRequest('/config?type=domain_template');
const domains = data.configs;

// Store selected domain in state
const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

// Pass to ingestion/query panels
<IngestionPanel domainId={selectedDomain} />
<QueryPanel domainId={selectedDomain} />
```

**UI Design:**
```tsx
<Select value={selectedDomain} onValueChange={onDomainChange}>
  <SelectTrigger className="w-full">
    <SelectValue placeholder="Select a domain" />
  </SelectTrigger>
  <SelectContent>
    {domains.map(domain => (
      <SelectItem key={domain.domain_id} value={domain.domain_id}>
        <div>
          <div className="font-medium">{domain.template_name}</div>
          <div className="text-xs text-muted-foreground">
            {domain.description}
          </div>
        </div>
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

### 4. View Mode Switcher

**Component:** `ViewModeSwitcher.tsx`

**Interface:**
```typescript
type ViewMode = 'use' | 'manage';

interface ViewModeSwitcherProps {
  mode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
}
```

**UI Design:**
```tsx
<Tabs value={mode} onValueChange={onModeChange}>
  <TabsList className="grid w-full grid-cols-2">
    <TabsTrigger value="use">Use Domain</TabsTrigger>
    <TabsTrigger value="manage">Manage Domain</TabsTrigger>
  </TabsList>
</Tabs>
```

**Routing:**
- Use Domain mode: `/dashboard` (current)
- Manage Domain mode: `/manage` (new full-screen page)

**Manage Mode Screen:**
When user selects "Manage Domain", navigate to `/manage` page showing:

```tsx
<div className="p-6 space-y-6">
  {/* Header */}
  <div className="flex justify-between items-center">
    <h1 className="text-2xl font-bold">Manage Domains</h1>
    <Button onClick={() => router.push('/config')}>
      Create New Domain
    </Button>
  </div>

  {/* Domain Grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {domains.map(domain => (
      <Card key={domain.domain_id} className="cursor-pointer hover:border-primary">
        <CardHeader>
          <div className="flex justify-between items-start">
            <CardTitle>{domain.template_name}</CardTitle>
            {domain.created_by === user.id && (
              <Badge variant="secondary">Created by me</Badge>
            )}
          </div>
          <CardDescription>{domain.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Ingestion Agents:</span>
              <span className="font-medium">{domain.ingestion_agents.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Query Agents:</span>
              <span className="font-medium">{domain.query_agents.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Incidents:</span>
              <span className="font-medium">{domain.incident_count}</span>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => router.push(`/manage/${domain.domain_id}`)}
          >
            View Data
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => router.push(`/config/domain/${domain.domain_id}`)}
          >
            Edit
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>
</div>
```

### 5. Data Table View

**Component:** `DataTableView.tsx`

**Interface:**
```typescript
interface Incident {
  id: string;
  domain_id: string;
  raw_text: string;
  structured_data: Record<string, any>;
  location?: { latitude: number; longitude: number };
  created_at: string;
  images?: string[];
}

interface DataTableViewProps {
  domainId: string;
}
```

**Features:**
- Pagination (20 rows per page)
- Sorting by column
- Filtering by date range, location, category
- Row click to view details
- Export to CSV

**API Integration:**
```typescript
const fetchIncidents = async (filters: any) => {
  const response = await apiRequest('/data?type=retrieval&filters=' + JSON.stringify(filters));
  return response.data.data;
};
```

**Column Configuration:**
```typescript
const columns = [
  { key: 'id', label: 'ID', width: '100px' },
  { key: 'created_at', label: 'Time', width: '150px', sortable: true },
  { key: 'location', label: 'Location', width: '200px' },
  { key: 'category', label: 'Category', width: '150px', filterable: true },
  // Dynamic columns from agent output schemas
  ...agentOutputColumns
];
```

**UI Design:**
```tsx
<div className="space-y-4">
  {/* Filters */}
  <div className="flex gap-4">
    <DateRangePicker onChange={setDateRange} />
    <Input placeholder="Search location..." />
    <Select placeholder="Category">
      {categories.map(cat => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}
    </Select>
  </div>

  {/* Table */}
  <Table>
    <TableHeader>
      <TableRow>
        {columns.map(col => (
          <TableHead key={col.key} onClick={() => handleSort(col.key)}>
            {col.label} {sortColumn === col.key && <SortIcon />}
          </TableHead>
        ))}
      </TableRow>
    </TableHeader>
    <TableBody>
      {incidents.map(incident => (
        <TableRow key={incident.id} onClick={() => handleRowClick(incident)}>
          {columns.map(col => (
            <TableCell key={col.key}>{renderCell(incident, col)}</TableCell>
          ))}
        </TableRow>
      ))}
    </TableBody>
  </Table>

  {/* Pagination */}
  <Pagination
    currentPage={page}
    totalPages={totalPages}
    onPageChange={setPage}
  />
</div>
```

### 6. Incident Detail Modal

**Component:** `IncidentDetailModal.tsx`

**Interface:**
```typescript
interface IncidentDetailModalProps {
  incident: Incident;
  isOpen: boolean;
  onClose: () => void;
}
```

**UI Design:**
```tsx
<Dialog open={isOpen} onOpenChange={onClose}>
  <DialogContent className="max-w-3xl">
    <DialogHeader>
      <DialogTitle>Incident Details</DialogTitle>
    </DialogHeader>
    
    <div className="space-y-4">
      {/* Raw text */}
      <div>
        <h3 className="font-semibold">Original Report</h3>
        <p className="text-sm text-muted-foreground">{incident.raw_text}</p>
      </div>

      {/* Structured data */}
      <div>
        <h3 className="font-semibold">Extracted Data</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(incident.structured_data).map(([key, value]) => (
            <div key={key}>
              <span className="text-xs text-muted-foreground">{key}</span>
              <p className="text-sm">{JSON.stringify(value)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Images */}
      {incident.images && incident.images.length > 0 && (
        <div>
          <h3 className="font-semibold">Images</h3>
          <div className="grid grid-cols-3 gap-2">
            {incident.images.map((img, i) => (
              <img key={i} src={img} alt={`Evidence ${i+1}`} className="rounded" />
            ))}
          </div>
        </div>
      )}

      {/* Map */}
      {incident.location && (
        <div>
          <h3 className="font-semibold">Location</h3>
          <div className="h-48 rounded border">
            {/* Mini map showing incident location */}
          </div>
        </div>
      )}
    </div>
  </DialogContent>
</Dialog>
```

### 7. Enhanced Real-Time Status Display

**Component:** `StatusPanel.tsx`

**Interface:**
```typescript
interface StatusUpdate {
  jobId: string;
  agentName: string;
  status: 'loading' | 'invoking' | 'calling_tool' | 'complete' | 'error';
  message: string;
  timestamp: string;
}

interface StatusPanelProps {
  jobId: string;
}
```

**UI Design:**
```tsx
<div className="space-y-2 p-4 bg-card rounded-lg">
  <h3 className="text-sm font-semibold">Processing Status</h3>
  
  <div className="space-y-1">
    {statusUpdates.map((update, i) => (
      <div key={i} className="flex items-center gap-2 text-xs">
        {update.status === 'complete' && <CheckIcon className="text-green-500" />}
        {update.status === 'error' && <XIcon className="text-red-500" />}
        {update.status === 'invoking' && <Spinner className="text-blue-500" />}
        
        <span className="text-muted-foreground">{update.agentName}</span>
        <span>{update.message}</span>
      </div>
    ))}
  </div>
</div>
```

**AppSync Integration:**
```typescript
const subscription = client.subscribe({
  query: gql`
    subscription OnStatusUpdate($userId: ID!) {
      onStatusUpdate(userId: $userId) {
        jobId
        agentName
        status
        message
        timestamp
      }
    }
  `,
  variables: { userId: user.id }
});

subscription.subscribe({
  next: ({ data }) => {
    setStatusUpdates(prev => [...prev, data.onStatusUpdate]);
  },
  error: (err) => {
    showToast({
      title: 'Connection error',
      description: 'Lost connection to status updates',
      variant: 'destructive'
    });
  }
});
```

## Geometry Support

### Supported Geometry Types

The system supports three geometry types for spatial data:

**1. Point (Default)**
```json
{
  "geometry_type": "Point",
  "coordinates": [longitude, latitude]
}
```
- Used for: Single location incidents (pothole, street light)
- Map rendering: Single marker

**2. LineString**
```json
{
  "geometry_type": "LineString",
  "coordinates": [
    [lon1, lat1],
    [lon2, lat2],
    [lon3, lat3]
  ]
}
```
- Used for: Linear features (road damage, pipeline issues)
- Map rendering: Line overlay

**3. Polygon**
```json
{
  "geometry_type": "Polygon",
  "coordinates": [[
    [lon1, lat1],
    [lon2, lat2],
    [lon3, lat3],
    [lon4, lat4],
    [lon1, lat1]  // Close the polygon
  ]]
}
```
- Used for: Area features (flood zones, affected neighborhoods)
- Map rendering: Filled polygon with border

### Geometry Detection

**GeoAgent Output Enhancement:**
```json
{
  "location": "string",
  "coordinates": "array",
  "address": "string",
  "confidence": "number",
  "geometry_type": "Point|LineString|Polygon"  // NEW FIELD
}
```

**Detection Logic:**
- If text mentions "from X to Y" or "along X street" → LineString
- If text mentions "area", "zone", "neighborhood", "block" → Polygon
- Otherwise → Point (default)

**Map Rendering:**
```typescript
const renderGeometry = (incident: Incident) => {
  const geom = incident.structured_data.geo_agent;
  
  switch (geom.geometry_type) {
    case 'Point':
      return new mapboxgl.Marker()
        .setLngLat(geom.coordinates)
        .addTo(map);
    
    case 'LineString':
      map.addSource(`line-${incident.id}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: geom.coordinates
          }
        }
      });
      map.addLayer({
        id: `line-${incident.id}`,
        type: 'line',
        source: `line-${incident.id}`,
        paint: {
          'line-color': '#FF5733',
          'line-width': 3
        }
      });
      break;
    
    case 'Polygon':
      map.addSource(`polygon-${incident.id}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: geom.coordinates
          }
        }
      });
      map.addLayer({
        id: `polygon-${incident.id}`,
        type: 'fill',
        source: `polygon-${incident.id}`,
        paint: {
          'fill-color': '#FF5733',
          'fill-opacity': 0.3
        }
      });
      map.addLayer({
        id: `polygon-border-${incident.id}`,
        type: 'line',
        source: `polygon-${incident.id}`,
        paint: {
          'line-color': '#FF5733',
          'line-width': 2
        }
      });
      break;
  }
};
```

## Query Clarification System

### Problem: Ambiguous Queries

Users may ask vague questions like:
- "Show me the complaints" (no boundary, no category)
- "What's happening?" (no context)
- "How many?" (no subject)

### Solution: Query Clarification Agent

**New Component:** `QueryClarificationPanel.tsx`

**Flow:**
```
User Query → Clarification Check → Follow-up Questions → Refined Query → Execute
```

**Implementation:**

**1. Clarification Detection (Client-side)**
```typescript
const needsClarification = (query: string): boolean => {
  const ambiguousPatterns = [
    /^show me/i,
    /^what('s| is)/i,
    /^how many$/i,
    /^where$/i,
    /complaints?$/i,  // Ends with "complaint(s)" only
  ];
  
  return ambiguousPatterns.some(pattern => pattern.test(query));
};
```

**2. Clarification Questions**
```typescript
interface ClarificationQuestion {
  field: string;
  question: string;
  options?: string[];
  required: boolean;
}

const getClarificationQuestions = (query: string): ClarificationQuestion[] => {
  const questions: ClarificationQuestion[] = [];
  
  // Check for missing category
  if (!query.match(/pothole|street light|sidewalk|trash/i)) {
    questions.push({
      field: 'category',
      question: 'What type of complaints?',
      options: ['All', 'Potholes', 'Street Lights', 'Sidewalks', 'Trash'],
      required: false
    });
  }
  
  // Check for missing location
  if (!query.match(/in|at|near|downtown|neighborhood/i)) {
    questions.push({
      field: 'location',
      question: 'Which area?',
      options: ['All', 'Downtown', 'North Side', 'South Side', 'East End', 'West End'],
      required: false
    });
  }
  
  // Check for missing time range
  if (!query.match(/today|yesterday|week|month|year/i)) {
    questions.push({
      field: 'time_range',
      question: 'What time period?',
      options: ['All time', 'Today', 'This week', 'This month', 'This year'],
      required: false
    });
  }
  
  return questions;
};
```

**3. Clarification UI**
```tsx
const QueryClarificationPanel = ({ query, onSubmit }) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const questions = getClarificationQuestions(query);
  
  if (questions.length === 0) {
    // No clarification needed, submit directly
    onSubmit(query);
    return null;
  }
  
  return (
    <Card className="p-4 space-y-4">
      <div>
        <h3 className="font-semibold">Your question:</h3>
        <p className="text-sm text-muted-foreground">{query}</p>
      </div>
      
      <div className="space-y-3">
        <p className="text-sm">Please clarify:</p>
        
        {questions.map(q => (
          <div key={q.field}>
            <label className="text-sm font-medium">{q.question}</label>
            {q.options ? (
              <Select 
                value={answers[q.field]} 
                onValueChange={(val) => setAnswers({...answers, [q.field]: val})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select..." />
                </SelectTrigger>
                <SelectContent>
                  {q.options.map(opt => (
                    <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input 
                value={answers[q.field] || ''} 
                onChange={(e) => setAnswers({...answers, [q.field]: e.target.value})}
                placeholder="Enter..."
              />
            )}
          </div>
        ))}
      </div>
      
      <div className="flex gap-2">
        <Button onClick={() => onSubmit(buildRefinedQuery(query, answers))}>
          Submit Query
        </Button>
        <Button variant="outline" onClick={() => onSubmit(query)}>
          Skip (use as-is)
        </Button>
      </div>
    </Card>
  );
};
```

**4. Query Refinement**
```typescript
const buildRefinedQuery = (originalQuery: string, answers: Record<string, string>): string => {
  let refined = originalQuery;
  
  // Add category filter
  if (answers.category && answers.category !== 'All') {
    refined += ` about ${answers.category.toLowerCase()}`;
  }
  
  // Add location filter
  if (answers.location && answers.location !== 'All') {
    refined += ` in ${answers.location}`;
  }
  
  // Add time range
  if (answers.time_range && answers.time_range !== 'All time') {
    refined += ` from ${answers.time_range.toLowerCase()}`;
  }
  
  return refined;
};

// Example:
// Original: "Show me the complaints"
// Refined: "Show me the complaints about potholes in Downtown from this week"
```

**5. Integration with Query Panel**
```tsx
const QueryPanel = () => {
  const [query, setQuery] = useState('');
  const [showClarification, setShowClarification] = useState(false);
  
  const handleQuerySubmit = (q: string) => {
    if (needsClarification(q)) {
      setShowClarification(true);
    } else {
      submitQuery(q);
    }
  };
  
  const submitQuery = async (refinedQuery: string) => {
    setShowClarification(false);
    // Submit to backend
    await apiRequest('/query', {
      method: 'POST',
      body: JSON.stringify({
        domain_id: selectedDomain,
        question: refinedQuery
      })
    });
  };
  
  return (
    <div className="space-y-4">
      <Textarea 
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question about the data..."
      />
      
      {showClarification ? (
        <QueryClarificationPanel 
          query={query}
          onSubmit={submitQuery}
        />
      ) : (
        <Button onClick={() => handleQuerySubmit(query)}>
          Ask Question
        </Button>
      )}
    </div>
  );
};
```

## Data Models

### Frontend State Management

**Global State (Context API):**
```typescript
interface AppState {
  user: User | null;
  selectedDomain: string | null;
  viewMode: 'use' | 'manage';
  theme: 'dark';  // Always dark for MVP
  chatHistory: Record<string, ChatMessage[]>;  // NEW: Per-domain chat history
}

interface AppActions {
  setUser: (user: User) => void;
  setSelectedDomain: (domainId: string) => void;
  setViewMode: (mode: 'use' | 'manage') => void;
  addChatMessage: (domainId: string, message: ChatMessage) => void;
  clearChatHistory: (domainId: string) => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'system' | 'agent';
  content: string;
  timestamp: string;
  metadata?: {
    jobId?: string;
    agentName?: string;
    status?: string;
  };
}
```

**Chat History Persistence:**
```typescript
// Save to localStorage on change
useEffect(() => {
  localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}, [chatHistory]);

// Load on mount
useEffect(() => {
  const saved = localStorage.getItem('chatHistory');
  if (saved) {
    setChatHistory(JSON.parse(saved));
  }
}, []);

// Restore chat when switching domains
useEffect(() => {
  if (selectedDomain && chatHistory[selectedDomain]) {
    setMessages(chatHistory[selectedDomain]);
  } else {
    setMessages([]);
  }
}, [selectedDomain]);
```

**Local State (Component):**
```typescript
// Dashboard
const [incidents, setIncidents] = useState<Incident[]>([]);
const [statusUpdates, setStatusUpdates] = useState<StatusUpdate[]>([]);
const [loading, setLoading] = useState(false);
const [messages, setMessages] = useState<ChatMessage[]>([]);  // Current domain chat

// Data Table
const [filters, setFilters] = useState<Filters>({
  dateRange: null,
  location: null,
  category: null
});
const [page, setPage] = useState(1);
const [sortColumn, setSortColumn] = useState<string | null>(null);
const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
```

## Visual Design System

### Color Coding by Category

**Category Colors:**
```typescript
const CATEGORY_COLORS: Record<string, { bg: string; border: string; icon: string }> = {
  'pothole': {
    bg: '#EF4444',      // Red
    border: '#DC2626',
    icon: '🕳️'
  },
  'street_light': {
    bg: '#F59E0B',      // Amber
    border: '#D97706',
    icon: '💡'
  },
  'sidewalk': {
    bg: '#8B5CF6',      // Purple
    border: '#7C3AED',
    icon: '🚶'
  },
  'trash': {
    bg: '#10B981',      // Green
    border: '#059669',
    icon: '🗑️'
  },
  'flooding': {
    bg: '#3B82F6',      // Blue
    border: '#2563EB',
    icon: '🌊'
  },
  'fire': {
    bg: '#DC2626',      // Dark Red
    border: '#991B1B',
    icon: '🔥'
  },
  'default': {
    bg: '#6B7280',      // Gray
    border: '#4B5563',
    icon: '📍'
  }
};
```

**Severity Colors:**
```typescript
const SEVERITY_COLORS: Record<string, string> = {
  'critical': '#DC2626',  // Red
  'high': '#F59E0B',      // Amber
  'medium': '#F59E0B',    // Yellow
  'low': '#10B981',       // Green
};
```

### Map Marker Customization

**Custom Marker with Icon and Color:**
```typescript
const createCustomMarker = (incident: Incident): HTMLElement => {
  const category = incident.structured_data.entity_agent?.category || 'default';
  const severity = incident.structured_data.severity_classifier?.severity_level || 'medium';
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
  
  const el = document.createElement('div');
  el.className = 'custom-marker';
  el.innerHTML = `
    <div style="
      width: 40px;
      height: 40px;
      background: ${colors.bg};
      border: 3px solid ${colors.border};
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      position: relative;
    ">
      ${colors.icon}
      ${severity === 'critical' ? '<div style="position: absolute; top: -5px; right: -5px; width: 12px; height: 12px; background: #DC2626; border: 2px solid white; border-radius: 50%;"></div>' : ''}
    </div>
  `;
  
  return el;
};

// Usage
const marker = new mapboxgl.Marker(createCustomMarker(incident))
  .setLngLat(incident.location.coordinates)
  .setPopup(createDetailedPopup(incident))
  .addTo(map);
```

### Enhanced Popup with Full Details

**Detailed Popup Component:**
```typescript
const createDetailedPopup = (incident: Incident): mapboxgl.Popup => {
  const category = incident.structured_data.entity_agent?.category || 'Unknown';
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
  
  const popupContent = document.createElement('div');
  popupContent.className = 'incident-popup';
  popupContent.style.cssText = 'max-width: 400px; max-height: 500px; overflow-y: auto;';
  
  // Header with category badge
  const header = document.createElement('div');
  header.style.cssText = `
    background: ${colors.bg};
    color: white;
    padding: 12px;
    margin: -12px -12px 12px -12px;
    border-radius: 8px 8px 0 0;
  `;
  header.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="font-size: 24px;">${colors.icon}</span>
      <div>
        <h3 style="margin: 0; font-size: 16px; font-weight: bold;">${category}</h3>
        <p style="margin: 0; font-size: 12px; opacity: 0.9;">
          ${new Date(incident.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  `;
  popupContent.appendChild(header);
  
  // Original report text
  const reportSection = document.createElement('div');
  reportSection.style.cssText = 'margin-bottom: 12px;';
  reportSection.innerHTML = `
    <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">Report</h4>
    <p style="margin: 0; font-size: 13px; color: #6B7280;">
      ${incident.raw_text}
    </p>
  `;
  popupContent.appendChild(reportSection);
  
  // Structured data from agents
  const dataSection = document.createElement('div');
  dataSection.style.cssText = 'margin-bottom: 12px;';
  dataSection.innerHTML = '<h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">Extracted Data</h4>';
  
  Object.entries(incident.structured_data).forEach(([agentName, agentData]) => {
    const agentDiv = document.createElement('div');
    agentDiv.style.cssText = 'margin-bottom: 8px; padding: 8px; background: #F3F4F6; border-radius: 4px;';
    
    const agentTitle = document.createElement('div');
    agentTitle.style.cssText = 'font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 4px;';
    agentTitle.textContent = agentName.replace(/_/g, ' ').toUpperCase();
    agentDiv.appendChild(agentTitle);
    
    Object.entries(agentData as Record<string, any>).forEach(([key, value]) => {
      const field = document.createElement('div');
      field.style.cssText = 'font-size: 11px; color: #6B7280; margin-left: 8px;';
      field.innerHTML = `<strong>${key}:</strong> ${JSON.stringify(value)}`;
      agentDiv.appendChild(field);
    });
    
    dataSection.appendChild(agentDiv);
  });
  popupContent.appendChild(dataSection);
  
  // Images
  if (incident.images && incident.images.length > 0) {
    const imagesSection = document.createElement('div');
    imagesSection.style.cssText = 'margin-bottom: 12px;';
    imagesSection.innerHTML = '<h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">Evidence</h4>';
    
    const imageGrid = document.createElement('div');
    imageGrid.style.cssText = 'display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px;';
    
    incident.images.forEach((imageUrl, i) => {
      const imgWrapper = document.createElement('div');
      imgWrapper.style.cssText = 'position: relative; padding-top: 100%; cursor: pointer;';
      imgWrapper.onclick = () => window.open(imageUrl, '_blank');
      
      const img = document.createElement('img');
      img.src = imageUrl;
      img.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 4px;';
      img.alt = `Evidence ${i + 1}`;
      
      imgWrapper.appendChild(img);
      imageGrid.appendChild(imgWrapper);
    });
    
    imagesSection.appendChild(imageGrid);
    popupContent.appendChild(imagesSection);
  }
  
  // Action buttons
  const actions = document.createElement('div');
  actions.style.cssText = 'display: flex; gap: 8px; margin-top: 12px;';
  actions.innerHTML = `
    <button 
      onclick="window.open('/manage/${incident.domain_id}?incident=${incident.id}', '_blank')"
      style="
        flex: 1;
        padding: 8px;
        background: #4F46E5;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
      "
    >
      View Full Details
    </button>
  `;
  popupContent.appendChild(actions);
  
  return new mapboxgl.Popup({
    offset: 25,
    maxWidth: '400px',
    className: 'dark-popup'
  }).setDOMContent(popupContent);
};
```

### LineString and Polygon Popups

**Interactive Geometry Popups:**
```typescript
// For LineString
map.on('click', `line-${incident.id}`, (e) => {
  new mapboxgl.Popup()
    .setLngLat(e.lngLat)
    .setDOMContent(createDetailedPopup(incident).getElement())
    .addTo(map);
});

// For Polygon
map.on('click', `polygon-${incident.id}`, (e) => {
  new mapboxgl.Popup()
    .setLngLat(e.lngLat)
    .setDOMContent(createDetailedPopup(incident).getElement())
    .addTo(map);
});

// Hover effects
map.on('mouseenter', `line-${incident.id}`, () => {
  map.getCanvas().style.cursor = 'pointer';
});

map.on('mouseleave', `line-${incident.id}`, () => {
  map.getCanvas().style.cursor = '';
});
```

## Error Handling

### Error Categories and Responses

**1. API Errors (Network/Server)**
```typescript
try {
  const response = await apiRequest('/ingest', { method: 'POST', body });
  if (response.error) {
    showToast({
      title: 'Submission failed',
      description: response.error,
      variant: 'destructive'
    });
  }
} catch (error) {
  showToast({
    title: 'Network error',
    description: 'Please check your connection and try again',
    variant: 'destructive'
  });
}
```

**2. Validation Errors (Client-side)**
```typescript
const validateForm = () => {
  const errors: string[] = [];
  
  if (!selectedDomain) {
    errors.push('Please select a domain');
  }
  
  if (!reportText.trim()) {
    errors.push('Report text is required');
  }
  
  if (errors.length > 0) {
    showToast({
      title: 'Validation error',
      description: errors.join(', '),
      variant: 'destructive'
    });
    return false;
  }
  
  return true;
};
```

**3. Agent Execution Errors (Real-time)**
```typescript
subscription.subscribe({
  next: ({ data }) => {
    if (data.onStatusUpdate.status === 'error') {
      showToast({
        title: `${data.onStatusUpdate.agentName} failed`,
        description: data.onStatusUpdate.message,
        variant: 'destructive',
        duration: 10000  // Longer duration for errors
      });
    }
  }
});
```

**4. Authentication Errors**
```typescript
if (response.status === 401) {
  showToast({
    title: 'Session expired',
    description: 'Please log in again',
    variant: 'destructive'
  });
  router.push('/login');
}
```

## Testing Strategy

### Component Testing
- Test dark mode theme application
- Test domain selector with mock data
- Test data table sorting and filtering
- Test error toast display
- Test view mode switching

### Integration Testing
- Test API integration with error handling
- Test AppSync WebSocket connection
- Test real-time status updates
- Test end-to-end report submission
- Test end-to-end query flow

### User Acceptance Testing
- Test civic complaint submission flow
- Test query with map visualization
- Test data table view and filtering
- Test error scenarios (network failure, validation)
- Test role switching (use vs manage)

## Deployment

### Installation Steps

**1. Install Shadcn UI:**
```bash
cd infrastructure/frontend
npx shadcn-ui@latest init
```

**2. Install Required Components:**
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add card
```

**3. Configure Tailwind for Dark Mode:**
```javascript
// tailwind.config.ts
module.exports = {
  darkMode: 'class',
  // ... rest of config
}
```

**4. Update Root Layout:**
```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="dark:bg-background dark:text-foreground">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

### Environment Variables

No new environment variables needed. Existing:
```
NEXT_PUBLIC_API_URL=https://api.example.com/api/v1
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxx
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_USER_POOL_ID=us-east-1_xxx
NEXT_PUBLIC_USER_POOL_CLIENT_ID=xxx
NEXT_PUBLIC_APPSYNC_URL=wss://xxx.appsync-api.us-east-1.amazonaws.com/graphql
```

## API Validation and Corrections

### Required API Endpoints

**All endpoints verified to exist in deployed backend:**

✅ **GET /config?type=domain_template** - List domains
✅ **GET /config?type=agent** - List agents  
✅ **GET /config?type=dependency_graph** - Get dependency graphs
✅ **POST /config** - Create agent/domain/playbook
✅ **PUT /config/{type}/{id}** - Update configuration
✅ **DELETE /config/{type}/{id}** - Delete configuration
✅ **POST /ingest** - Submit report
✅ **POST /query** - Ask question
✅ **GET /data?type=retrieval** - Fetch incidents
✅ **GET /data?type=aggregation** - Get statistics
✅ **GET /data?type=spatial** - Spatial queries
✅ **GET /data?type=analytics** - Analytics data
✅ **WebSocket (AppSync)** - Real-time status updates

### API Response Validation

**Expected vs Actual Response Formats:**

**1. Domain List Response:**
```typescript
// Expected format (from design)
interface DomainResponse {
  configs: Array<{
    domain_id: string;
    template_name: string;
    description: string;
    agent_configs: any[];
    playbook_configs: any[];
    created_by: string;
    created_at: string;
  }>;
  count: number;
}

// Validation in frontend
const validateDomainResponse = (data: any): boolean => {
  if (!data.configs || !Array.isArray(data.configs)) {
    console.error('Invalid domain response: missing configs array');
    return false;
  }
  
  for (const domain of data.configs) {
    if (!domain.domain_id || !domain.template_name) {
      console.error('Invalid domain: missing required fields', domain);
      return false;
    }
  }
  
  return true;
};
```

**2. Incident List Response:**
```typescript
// Expected format
interface IncidentResponse {
  data: Array<{
    id: string;
    domain_id: string;
    raw_text: string;
    structured_data: Record<string, any>;
    location?: { latitude: number; longitude: number };
    created_at: string;
    images?: string[];
  }>;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

// Validation
const validateIncidentResponse = (data: any): boolean => {
  if (!data.data || !Array.isArray(data.data)) {
    console.error('Invalid incident response: missing data array');
    return false;
  }
  
  if (!data.pagination) {
    console.warn('Missing pagination data, using defaults');
    data.pagination = { page: 1, per_page: 20, total: data.data.length, total_pages: 1 };
  }
  
  return true;
};
```

**3. Query Response:**
```typescript
// Expected format
interface QueryResponse {
  job_id: string;
  status: 'processing' | 'complete' | 'error';
  results?: {
    agent_responses: Record<string, any>;
    summary: string;
    bullet_points: string[];
    visualization?: any;
  };
}

// Real-time updates via AppSync
interface StatusUpdate {
  jobId: string;
  agentName: string;
  status: 'loading' | 'invoking' | 'complete' | 'error';
  message: string;
  timestamp: string;
  output?: any;
}
```

### Error Handling for API Mismatches

**Graceful Degradation:**
```typescript
const fetchWithValidation = async <T>(
  endpoint: string,
  validator: (data: any) => boolean,
  fallback: T
): Promise<T> => {
  try {
    const response = await apiRequest(endpoint);
    
    if (response.error) {
      showToast({
        title: 'API Error',
        description: response.error,
        variant: 'destructive'
      });
      return fallback;
    }
    
    if (!validator(response.data)) {
      showToast({
        title: 'Data Validation Error',
        description: 'Received unexpected data format from server',
        variant: 'destructive'
      });
      return fallback;
    }
    
    return response.data as T;
  } catch (error) {
    console.error('API request failed:', error);
    showToast({
      title: 'Network Error',
      description: 'Failed to connect to server',
      variant: 'destructive'
    });
    return fallback;
  }
};

// Usage
const domains = await fetchWithValidation(
  '/config?type=domain_template',
  validateDomainResponse,
  { configs: [], count: 0 }
);
```

### Missing API Endpoints (To Be Created)

**None identified** - All required endpoints exist in the deployed backend.

However, if during implementation we discover missing endpoints, we will:
1. Document the missing endpoint
2. Create a mock implementation in the frontend for demo
3. Note it as a post-MVP enhancement

## Implementation Timeline

**Total: 10-14 hours** (updated with new features)

### Phase 1: Dark Mode (2-3 hours)
- Install Shadcn UI
- Configure Tailwind dark mode
- Update all components to use Shadcn
- Apply dark Mapbox style (dark-v11)
- Test contrast and accessibility

### Phase 2: Error Handling (1-2 hours)
- Implement toast system
- Add error handling to API client
- Add validation error display
- Add API response validation
- Test error scenarios

### Phase 3: Domain Selector & Chat History (2-3 hours)
- Create DomainSelector component
- Integrate with API
- Add to ingestion/query panels
- Implement chat history persistence (localStorage)
- Restore chat on domain switch
- Test domain switching

### Phase 4: View Mode & Manage Screen (2-3 hours)
- Create ViewModeSwitcher component
- Create Manage Domain page with grid view
- Add "Created by me" badges
- Implement routing
- Test mode switching

### Phase 5: Visual Design System (2-3 hours)
- Implement category colors and icons
- Create custom map markers with icons
- Add severity indicators
- Implement geometry rendering (Point, LineString, Polygon)
- Add hover effects and cursor changes
- Test visual consistency

### Phase 6: Enhanced Popups (1-2 hours)
- Create detailed popup component
- Add category header with color
- Display all agent outputs
- Add image gallery
- Add action buttons
- Make popups work for all geometry types

### Phase 7: Query Clarification (1-2 hours)
- Implement clarification detection
- Create clarification UI
- Add follow-up questions
- Implement query refinement
- Test with ambiguous queries

### Phase 8: Data Table View (2-3 hours)
- Create DataTableView component
- Implement filtering and sorting
- Create IncidentDetailModal
- Integrate with Retrieval API
- Test with real data

### Phase 9: Polish and Testing (1-2 hours)
- Fix UI bugs
- Test end-to-end flows
- Validate all API integrations
- Optimize performance
- Prepare demo script

## Success Criteria

1. ✅ Dark mode applied consistently across all pages
2. ✅ Error toasts display for all error scenarios
3. ✅ Domain selector works with all 3 built-in domains
4. ✅ View mode switcher toggles between Use and Manage
5. ✅ Data table displays incidents with filtering
6. ✅ Civic complaint flow works end-to-end
7. ✅ Query flow works with map visualization
8. ✅ Real-time status updates display correctly
9. ✅ All APIs integrate successfully
10. ✅ Demo-ready for hackathon presentation
