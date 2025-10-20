# Design Document

## Overview

This design document outlines the technical approach for integrating backend APIs with frontend components, implementing CRUD operations for custom agents and domains, fixing critical bugs, and adding advanced features like confidence-based clarification, geometry type support, and real-time execution visualization.

The implementation focuses on:
1. **API Integration**: Connect all frontend components to backend APIs
2. **Agent & Domain Management**: Enable CRUD operations with two-stage creation flow
3. **Bug Fixes**: Resolve network errors and resource loading issues
4. **Advanced Features**: Confidence validation, geometry rendering, real-time status, clarification dialogs

## Architecture

### Current State

**Backend (Deployed):**
- ✅ Configuration API with full CRUD for agents and domains
- ✅ Real-time status publishing via AppSync WebSocket
- ✅ Confidence score validation in orchestrator
- ✅ 17 built-in agents (6 ingestion + 11 query)
- ❌ Geometry type support (needs enhancement)
- ❌ Simplified domain creation endpoint (needs enhancement)

**Frontend (Needs Work):**
- ❌ API integration incomplete
- ❌ Agent CRUD UI missing
- ❌ Domain creation flow complex
- ❌ Real-time status visualization basic
- ❌ Confidence-based clarification missing
- ❌ Geometry rendering limited to Points

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  API Client Layer (Enhanced)                              │ │
│  │  - Agent CRUD operations                                  │ │
│  │  - Domain CRUD operations                                 │ │
│  │  - Confidence validation                                  │ │
│  │  - Error handling with retry                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Agent Management                                          │ │
│  │  ┌─────────────────┐  ┌──────────────────┐              │ │
│  │  │ Agent List      │  │ Agent Form       │              │ │
│  │  │ - Built-in (17) │  │ - Type toggle    │              │ │
│  │  │ - Custom        │  │ - Parent select  │              │ │
│  │  │ - Tags          │  │ - Tool select    │              │ │
│  │  └─────────────────┘  └──────────────────┘              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Two-Stage Domain Creation                                 │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Stage 1: Select Ingest Agents (Required)             │ │ │
│  │  │ [✓] Geo Agent    [✓] Temporal Agent                  │ │ │
│  │  │ [ ] Entity Agent [ ] Custom Agent 1                  │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Stage 2: Select Query Agents (Required)              │ │ │
│  │  │ [✓] When Agent   [✓] Where Agent                     │ │ │
│  │  │ [ ] Why Agent    [ ] Custom Query Agent              │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Dependency Graph Visualization                       │ │ │
│  │  │  Geo Agent ──┐                                       │ │ │
│  │  │  Temporal ───┼──→ Parallel Execution                │ │ │
│  │  │  Entity ─────┘                                       │ │ │
│  │  │                                                       │ │ │
│  │  │  When Agent ──→ Sequential                           │ │ │
│  │  │  Where Agent ──→ Sequential                          │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Real-Time Execution Visualization                         │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Job: abc-123                                         │ │ │
│  │  │ ● Geo Agent: complete (confidence: 0.95)            │ │ │
│  │  │ ● Temporal Agent: invoking...                       │ │ │
│  │  │ ○ Entity Agent: waiting                             │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Confidence-Based Clarification Dialog                    │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Low Confidence Detected (0.65)                       │ │ │
│  │  │                                                       │ │ │
│  │  │ Location: "Main Street" (confidence: 0.60)          │ │ │
│  │  │ ❓ Which Main Street? Please provide more details:  │ │ │
│  │  │ [ City, cross streets, or landmarks ]               │ │ │
│  │  │                                                       │ │ │
│  │  │ [Submit Clarification] [Skip]                       │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Geometry Rendering (Point, LineString, Polygon)          │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │ Map View                                             │ │ │
│  │  │  📍 Point: Single location marker                   │ │ │
│  │  │  ━━━ LineString: Road/route line                    │ │ │
│  │  │  ▭ Polygon: Area/zone fill                          │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS + JWT + WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend APIs (Enhanced)                         │
├─────────────────────────────────────────────────────────────────┤
│  POST   /api/v1/config                  - Create agent/domain   │
│  GET    /api/v1/config?type=agent       - List agents           │
│  GET    /api/v1/config?type=domain_template - List domains      │
│  PUT    /api/v1/config/{type}/{id}      - Update config         │
│  DELETE /api/v1/config/{type}/{id}      - Delete config         │
│  POST   /api/v1/ingest                  - Submit report         │
│  POST   /api/v1/query                   - Ask question          │
│  GET    /api/v1/data?type=retrieval     - Fetch incidents       │
│  WebSocket (AppSync)                    - Real-time status      │
│                                                                   │
│  NEW ENHANCEMENTS:                                               │
│  - Geometry type detection in Geo Agent                         │
│  - Simplified domain creation with agent_ids                    │
│  - Confidence-based clarification trigger                       │
│  - Enhanced metadata in list responses                          │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Enhanced API Client

**File:** `infrastructure/frontend/lib/api-client.ts`

**New Functions:**

```typescript
// Agent CRUD
export async function createAgent(config: AgentConfig): Promise<ApiResponse<Agent>>
export async function listAgents(): Promise<ApiResponse<{ agents: Agent[] }>>
export async function getAgent(agentId: string): Promise<ApiResponse<Agent>>
export async function updateAgent(agentId: string, config: AgentConfig): Promise<ApiResponse<Agent>>
export async function deleteAgent(agentId: string): Promise<ApiResponse<void>>

// Domain CRUD
export async function createDomain(config: DomainConfig): Promise<ApiResponse<Domain>>
export async function listDomains(): Promise<ApiResponse<{ domains: Domain[] }>>
export async function getDomain(domainId: string): Promise<ApiResponse<Domain>>
export async function updateDomain(domainId: string, config: DomainConfig): Promise<ApiResponse<Domain>>
export async function deleteDomain(domainId: string): Promise<ApiResponse<void>>
```

**Interfaces:**

```typescript
interface AgentConfig {
  agent_name: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, any>;
  dependency_parent?: string;
  interrogative?: string;
}

interface Agent extends AgentConfig {
  agent_id: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  updated_at: number;
}

interface DomainConfig {
  template_name: string;
  domain_id: string;
  description: string;
  ingest_agent_ids: string[];  // Simplified!
  query_agent_ids: string[];   // Simplified!
}

interface Domain extends DomainConfig {
  template_id: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  agent_count: number;
  incident_count: number;
}
```

### 2. Agent Management Components

**Component:** `AgentListView.tsx`

```typescript
interface AgentListViewProps {
  onCreateAgent: () => void;
  onEditAgent: (agent: Agent) => void;
}

const AgentListView: React.FC<AgentListViewProps> = ({ onCreateAgent, onEditAgent }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filter, setFilter] = useState<'all' | 'builtin' | 'custom'>('all');
  
  useEffect(() => {
    loadAgents();
  }, []);
  
  const loadAgents = async () => {
    const response = await listAgents();
    if (response.data) {
      setAgents(response.data.agents);
    }
  };
  
  const filteredAgents = agents.filter(agent => {
    if (filter === 'builtin') return agent.is_builtin;
    if (filter === 'custom') return !agent.is_builtin;
    return true;
  });
  
  return (
    <div>
      <div className="flex justify-between mb-4">
        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList>
            <TabsTrigger value="all">All ({agents.length})</TabsTrigger>
            <TabsTrigger value="builtin">Built-in</TabsTrigger>
            <TabsTrigger value="custom">Custom</TabsTrigger>
          </TabsList>
        </Tabs>
        <Button onClick={onCreateAgent}>Create Agent</Button>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        {filteredAgents.map(agent => (
          <AgentCard key={agent.agent_id} agent={agent} onEdit={onEditAgent} />
        ))}
      </div>
    </div>
  );
};
```

**Component:** `AgentFormDialog.tsx`

```typescript
interface AgentFormDialogProps {
  agent?: Agent;  // undefined for create, defined for edit
  isOpen: boolean;
  onClose: () => void;
  onSave: (agent: Agent) => void;
}

const AgentFormDialog: React.FC<AgentFormDialogProps> = ({ agent, isOpen, onClose, onSave }) => {
  const [agentType, setAgentType] = useState<'ingestion' | 'query'>('ingestion');
  const [formData, setFormData] = useState<AgentConfig>({
    agent_name: '',
    agent_type: 'ingestion',
    system_prompt: '',
    tools: [],
    output_schema: {},
  });
  
  const handleSubmit = async () => {
    if (agent) {
      // Update existing
      const response = await updateAgent(agent.agent_id, formData);
      if (response.data) onSave(response.data);
    } else {
      // Create new
      const response = await createAgent(formData);
      if (response.data) onSave(response.data);
    }
    onClose();
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{agent ? 'Edit Agent' : 'Create Agent'}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Agent Type Toggle */}
          <div>
            <Label>Agent Type</Label>
            <Tabs value={agentType} onValueChange={setAgentType}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="ingestion">Data Ingest Agent</TabsTrigger>
                <TabsTrigger value="query">Data Query Agent</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          
          {/* Agent Name */}
          <div>
            <Label>Agent Name</Label>
            <Input value={formData.agent_name} onChange={e => setFormData({...formData, agent_name: e.target.value})} />
          </div>
          
          {/* Parent Agent Selection (for chaining) */}
          {agentType === 'query' && (
            <div>
              <Label>Parent Agent (Optional)</Label>
              <Select value={formData.dependency_parent} onValueChange={val => setFormData({...formData, dependency_parent: val})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select parent agent" />
                </SelectTrigger>
                <SelectContent>
                  {/* List of built-in query agents */}
                  <SelectItem value="when_agent">When Agent</SelectItem>
                  <SelectItem value="where_agent">Where Agent</SelectItem>
                  {/* ... other agents */}
                </SelectContent>
              </Select>
            </div>
          )}
          
          {/* Tool Selection */}
          <div>
            <Label>Tools</Label>
            <MultiSelect options={availableTools} value={formData.tools} onChange={tools => setFormData({...formData, tools})} />
          </div>
          
          {/* System Prompt */}
          <div>
            <Label>System Prompt</Label>
            <Textarea value={formData.system_prompt} onChange={e => setFormData({...formData, system_prompt: e.target.value})} rows={5} />
          </div>
          
          {/* Output Schema (Key-Value Pairs) */}
          <div>
            <Label>Output Schema (Max 5 keys)</Label>
            <KeyValueEditor value={formData.output_schema} onChange={schema => setFormData({...formData, output_schema: schema})} maxKeys={5} />
          </div>
          
          {/* Example JSON (for ingest agents) */}
          {agentType === 'ingestion' && (
            <div>
              <Label>Example Output JSON</Label>
              <Textarea placeholder='{"location": "string", "confidence": 0.95}' rows={4} />
            </div>
          )}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Save Agent</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

### 3. Two-Stage Domain Creation

**Component:** `DomainCreationWizard.tsx`

```typescript
interface DomainCreationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (domain: Domain) => void;
}

const DomainCreationWizard: React.FC<DomainCreationWizardProps> = ({ isOpen, onClose, onComplete }) => {
  const [stage, setStage] = useState<1 | 2>(1);
  const [selectedIngestAgents, setSelectedIngestAgents] = useState<string[]>([]);
  const [selectedQueryAgents, setSelectedQueryAgents] = useState<string[]>([]);
  const [domainName, setDomainName] = useState('');
  const [domainDescription, setDomainDescription] = useState('');
  
  const [allAgents, setAllAgents] = useState<Agent[]>([]);
  
  useEffect(() => {
    loadAgents();
  }, []);
  
  const loadAgents = async () => {
    const response = await listAgents();
    if (response.data) {
      setAllAgents(response.data.agents);
    }
  };
  
  const ingestAgents = allAgents.filter(a => a.agent_type === 'ingestion');
  const queryAgents = allAgents.filter(a => a.agent_type === 'query');
  
  const canProceedToStage2 = selectedIngestAgents.length > 0;
  const canCreate = selectedIngestAgents.length > 0 && selectedQueryAgents.length > 0 && domainName;
  
  const handleCreate = async () => {
    const config: DomainConfig = {
      template_name: domainName,
      domain_id: domainName.toLowerCase().replace(/\s+/g, '_'),
      description: domainDescription,
      ingest_agent_ids: selectedIngestAgents,
      query_agent_ids: selectedQueryAgents,
    };
    
    const response = await createDomain(config);
    if (response.data) {
      onComplete(response.data);
      onClose();
    }
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Domain - Stage {stage} of 2</DialogTitle>
        </DialogHeader>
        
        {/* Domain Info */}
        <div className="space-y-4 mb-6">
          <div>
            <Label>Domain Name</Label>
            <Input value={domainName} onChange={e => setDomainName(e.target.value)} placeholder="e.g., Traffic Management" />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea value={domainDescription} onChange={e => setDomainDescription(e.target.value)} placeholder="Describe the domain purpose" />
          </div>
        </div>
        
        {/* Stage 1: Select Ingest Agents */}
        {stage === 1 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Select Data Ingest Agents (Required)</h3>
              <Badge>{selectedIngestAgents.length} selected</Badge>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {ingestAgents.map(agent => (
                <AgentSelectionCard
                  key={agent.agent_id}
                  agent={agent}
                  selected={selectedIngestAgents.includes(agent.agent_id)}
                  onToggle={() => {
                    if (selectedIngestAgents.includes(agent.agent_id)) {
                      setSelectedIngestAgents(selectedIngestAgents.filter(id => id !== agent.agent_id));
                    } else {
                      setSelectedIngestAgents([...selectedIngestAgents, agent.agent_id]);
                    }
                  }}
                />
              ))}
            </div>
            
            <Button onClick={() => setStage(2)} disabled={!canProceedToStage2} className="w-full">
              Next: Select Query Agents
            </Button>
          </div>
        )}
        
        {/* Stage 2: Select Query Agents */}
        {stage === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Select Data Query Agents (Required)</h3>
              <Badge>{selectedQueryAgents.length} selected</Badge>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {queryAgents.map(agent => (
                <AgentSelectionCard
                  key={agent.agent_id}
                  agent={agent}
                  selected={selectedQueryAgents.includes(agent.agent_id)}
                  onToggle={() => {
                    if (selectedQueryAgents.includes(agent.agent_id)) {
                      setSelectedQueryAgents(selectedQueryAgents.filter(id => id !== agent.agent_id));
                    } else {
                      setSelectedQueryAgents([...selectedQueryAgents, agent.agent_id]);
                    }
                  }}
                />
              ))}
            </div>
            
            {/* Dependency Graph Visualization */}
            <div className="mt-6">
              <h4 className="text-sm font-semibold mb-2">Execution Flow</h4>
              <DependencyGraphVisualization
                ingestAgents={allAgents.filter(a => selectedIngestAgents.includes(a.agent_id))}
                queryAgents={allAgents.filter(a => selectedQueryAgents.includes(a.agent_id))}
              />
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStage(1)} className="flex-1">
                Back
              </Button>
              <Button onClick={handleCreate} disabled={!canCreate} className="flex-1">
                Create Domain
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
```

### 4. Dependency Graph Visualization

**Component:** `DependencyGraphVisualization.tsx`

```typescript
interface DependencyGraphVisualizationProps {
  ingestAgents: Agent[];
  queryAgents: Agent[];
}

const DependencyGraphVisualization: React.FC<DependencyGraphVisualizationProps> = ({ ingestAgents, queryAgents }) => {
  // Determine execution levels
  const parallelIngestAgents = ingestAgents.filter(a => !a.dependency_parent);
  const sequentialIngestAgents = ingestAgents.filter(a => a.dependency_parent);
  
  const parallelQueryAgents = queryAgents.filter(a => !a.dependency_parent);
  const sequentialQueryAgents = queryAgents.filter(a => a.dependency_parent);
  
  return (
    <div className="border rounded-lg p-4 bg-card">
      {/* Ingestion Layer */}
      <div className="mb-4">
        <div className="text-xs text-muted-foreground mb-2">Ingestion Layer</div>
        
        {/* Parallel Execution */}
        {parallelIngestAgents.length > 0 && (
          <div className="flex items-center gap-2 mb-2">
            <div className="text-xs text-muted-foreground">Parallel:</div>
            <div className="flex gap-2">
              {parallelIngestAgents.map(agent => (
                <Badge key={agent.agent_id} variant="secondary">
                  {agent.agent_name}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {/* Sequential Execution */}
        {sequentialIngestAgents.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="text-xs text-muted-foreground">Sequential:</div>
            <div className="flex items-center gap-1">
              {sequentialIngestAgents.map((agent, idx) => (
                <React.Fragment key={agent.agent_id}>
                  <Badge variant="outline">{agent.agent_name}</Badge>
                  {idx < sequentialIngestAgents.length - 1 && <span>→</span>}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Query Layer */}
      <div>
        <div className="text-xs text-muted-foreground mb-2">Query Layer</div>
        
        {/* Parallel Execution */}
        {parallelQueryAgents.length > 0 && (
          <div className="flex items-center gap-2 mb-2">
            <div className="text-xs text-muted-foreground">Parallel:</div>
            <div className="flex gap-2">
              {parallelQueryAgents.map(agent => (
                <Badge key={agent.agent_id} variant="secondary">
                  {agent.agent_name}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {/* Sequential Execution */}
        {sequentialQueryAgents.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="text-xs text-muted-foreground">Sequential:</div>
            <div className="flex items-center gap-1">
              {sequentialQueryAgents.map((agent, idx) => (
                <React.Fragment key={agent.agent_id}>
                  <Badge variant="outline">{agent.agent_name}</Badge>
                  {idx < sequentialQueryAgents.length - 1 && <span>→</span>}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 5. Real-Time Execution Status

**Component:** `ExecutionStatusPanel.tsx`

```typescript
interface ExecutionStatusPanelProps {
  jobId: string;
  agents: Agent[];
}

interface StatusUpdate {
  jobId: string;
  agentName: string;
  status: 'waiting' | 'invoking' | 'calling_tool' | 'complete' | 'error';
  message: string;
  confidence?: number;
  timestamp: string;
}

const ExecutionStatusPanel: React.FC<ExecutionStatusPanelProps> = ({ jobId, agents }) => {
  const [statusUpdates, setStatusUpdates] = useState<Record<string, StatusUpdate>>({});
  
  useEffect(() => {
    // Subscribe to AppSync WebSocket
    const subscription = subscribeToStatusUpdates(jobId, (update: StatusUpdate) => {
      setStatusUpdates(prev => ({
        ...prev,
        [update.agentName]: update
      }));
    });
    
    return () => subscription.unsubscribe();
  }, [jobId]);
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle className="text-green-500" />;
      case 'error': return <XCircle className="text-red-500" />;
      case 'invoking': return <Loader2 className="text-blue-500 animate-spin" />;
      case 'calling_tool': return <Wrench className="text-yellow-500" />;
      default: return <Circle className="text-gray-400" />;
    }
  };
  
  return (
    <Card className="p-4">
      <h3 className="text-sm font-semibold mb-3">Execution Status</h3>
      
      <div className="space-y-2">
        {agents.map(agent => {
          const status = statusUpdates[agent.agent_name];
          
          return (
            <div key={agent.agent_id} className="flex items-center gap-2 text-sm">
              {getStatusIcon(status?.status || 'waiting')}
              
              <div className="flex-1">
                <div className="font-medium">{agent.agent_name}</div>
                <div className="text-xs text-muted-foreground">
                  {status?.message || 'Waiting...'}
                </div>
              </div>
              
              {status?.confidence && (
                <Badge variant={status.confidence >= 0.9 ? 'default' : 'destructive'}>
                  {(status.confidence * 100).toFixed(0)}%
                </Badge>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// WebSocket subscription helper
function subscribeToStatusUpdates(jobId: string, onUpdate: (update: StatusUpdate) => void) {
  const client = getAppSyncClient();
  
  const subscription = client.subscribe({
    query: gql`
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
    `,
    variables: { jobId }
  });
  
  return subscription.subscribe({
    next: ({ data }) => onUpdate(data.onStatusUpdate),
    error: (err) => console.error('Subscription error:', err)
  });
}
```

### 6. Confidence-Based Clarification Dialog

**Component:** `ClarificationDialog.tsx`

```typescript
interface ClarificationDialogProps {
  isOpen: boolean;
  jobId: string;
  lowConfidenceFields: LowConfidenceField[];
  onSubmit: (clarifications: Record<string, string>) => void;
  onSkip: () => void;
}

interface LowConfidenceField {
  agentName: string;
  fieldName: string;
  currentValue: any;
  confidence: number;
  question: string;
}

const ClarificationDialog: React.FC<ClarificationDialogProps> = ({
  isOpen,
  jobId,
  lowConfidenceFields,
  onSubmit,
  onSkip
}) => {
  const [clarifications, setClarifications] = useState<Record<string, string>>({});
  
  const handleSubmit = () => {
    onSubmit(clarifications);
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Additional Information Needed</DialogTitle>
          <DialogDescription>
            Some fields have low confidence. Please provide additional details to improve accuracy.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {lowConfidenceFields.map((field, idx) => (
            <div key={idx} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">{field.agentName}</div>
                <Badge variant="destructive">
                  {(field.confidence * 100).toFixed(0)}% confidence
                </Badge>
              </div>
              
              <div className="text-sm text-muted-foreground mb-2">
                Current value: <span className="font-mono">{JSON.stringify(field.currentValue)}</span>
              </div>
              
              <div className="mb-2">
                <Label>{field.question}</Label>
              </div>
              
              <Textarea
                value={clarifications[field.fieldName] || ''}
                onChange={e => setClarifications({
                  ...clarifications,
                  [field.fieldName]: e.target.value
                })}
                placeholder="Provide more details..."
                rows={3}
              />
            </div>
          ))}
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onSkip}>
            Skip (Proceed with low confidence)
          </Button>
          <Button onClick={handleSubmit}>
            Submit Clarification
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

**Integration with Ingestion/Query Flow:**

```typescript
// In IngestionPanel.tsx
const handleSubmit = async () => {
  const response = await submitReport(domainId, text, images);
  
  if (response.data) {
    const jobId = response.data.job_id;
    
    // Wait for completion
    const result = await waitForJobCompletion(jobId);
    
    // Check confidence scores
    const lowConfidenceFields = extractLowConfidenceFields(result, 0.9);
    
    if (lowConfidenceFields.length > 0) {
      // Show clarification dialog
      setShowClarification(true);
      setLowConfidenceFields(lowConfidenceFields);
    } else {
      // Success!
      showSuccessToast('Report submitted successfully');
    }
  }
};

const handleClarificationSubmit = async (clarifications: Record<string, string>) => {
  // Re-submit with additional context
  const enhancedText = `${text}\n\nAdditional details:\n${Object.entries(clarifications).map(([k, v]) => `${k}: ${v}`).join('\n')}`;
  
  const response = await submitReport(domainId, enhancedText, images);
  // ... repeat process
};

function extractLowConfidenceFields(result: any, threshold: number): LowConfidenceField[] {
  const fields: LowConfidenceField[] = [];
  
  for (const agentResult of result.agent_outputs) {
    const confidence = agentResult.output.confidence;
    
    if (confidence < threshold) {
      // Generate clarification question based on agent type
      const question = generateClarificationQuestion(agentResult.agent_name, agentResult.output);
      
      fields.push({
        agentName: agentResult.agent_name,
        fieldName: agentResult.agent_name.toLowerCase().replace(' ', '_'),
        currentValue: agentResult.output,
        confidence,
        question
      });
    }
  }
  
  return fields;
}

function generateClarificationQuestion(agentName: string, output: any): string {
  if (agentName.includes('Geo')) {
    return `Which "${output.location_name}" are you referring to? Please provide city, cross streets, or nearby landmarks.`;
  } else if (agentName.includes('Temporal')) {
    return `When exactly did this occur? Please provide a specific date and time.`;
  } else if (agentName.includes('Entity')) {
    return `Can you provide more details about the ${output.category}? What specific type or characteristics?`;
  }
  return 'Please provide more details about this information.';
}
```

### 7. Geometry Type Support

**Backend Enhancement:** `infrastructure/lambda/agents/geo_agent.py`

```python
# Enhanced output schema
config['output_schema'] = {
    'location_name': {'type': 'string', 'required': True},
    'coordinates': {'type': 'array', 'required': False},
    'geometry_type': {'type': 'string', 'required': True},  # NEW
    'confidence': {'type': 'number', 'required': True},
    'address': {'type': 'string', 'required': False}
}

def detect_geometry_type(text: str) -> str:
    """Detect geometry type from text patterns"""
    text_lower = text.lower()
    
    # LineString patterns
    linestring_patterns = [
        'from .+ to .+',
        'along .+ street',
        'between .+ and .+',
        'route',
        'road',
        'path'
    ]
    
    for pattern in linestring_patterns:
        if re.search(pattern, text_lower):
            return 'LineString'
    
    # Polygon patterns
    polygon_patterns = [
        'area',
        'zone',
        'neighborhood',
        'block',
        'region',
        'district',
        'entire .+'
    ]
    
    for pattern in polygon_patterns:
        if re.search(pattern, text_lower):
            return 'Polygon'
    
    # Default to Point
    return 'Point'

def execute(self, raw_text: str, parent_output: Optional[Dict] = None) -> Dict[str, Any]:
    # ... existing extraction logic ...
    
    # Detect geometry type
    geometry_type = detect_geometry_type(raw_text)
    
    # Extract coordinates based on geometry type
    if geometry_type == 'LineString':
        coordinates = extract_linestring_coordinates(raw_text)
    elif geometry_type == 'Polygon':
        coordinates = extract_polygon_coordinates(raw_text)
    else:
        coordinates = extract_point_coordinates(raw_text)
    
    output = {
        'location_name': location_name,
        'coordinates': coordinates,
        'geometry_type': geometry_type,
        'confidence': confidence,
        'address': address
    }
    
    return output
```

**Frontend Enhancement:** `infrastructure/frontend/lib/map-utils.ts`

```typescript
export function renderGeometry(map: mapboxgl.Map, incident: Incident) {
  const geoData = incident.structured_data.geo_agent;
  
  if (!geoData || !geoData.coordinates) return;
  
  const geometryType = geoData.geometry_type || 'Point';
  const category = incident.structured_data.entity_agent?.category || 'default';
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
  
  switch (geometryType) {
    case 'Point':
      renderPoint(map, incident, geoData, colors);
      break;
    
    case 'LineString':
      renderLineString(map, incident, geoData, colors);
      break;
    
    case 'Polygon':
      renderPolygon(map, incident, geoData, colors);
      break;
  }
}

function renderPoint(map: mapboxgl.Map, incident: Incident, geoData: any, colors: any) {
  const marker = new mapboxgl.Marker({
    color: colors.bg,
    element: createCustomMarker(incident, colors)
  })
    .setLngLat(geoData.coordinates)
    .setPopup(createDetailedPopup(incident))
    .addTo(map);
}

function renderLineString(map: mapboxgl.Map, incident: Incident, geoData: any, colors: any) {
  const sourceId = `line-${incident.id}`;
  const layerId = `line-layer-${incident.id}`;
  
  map.addSource(sourceId, {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: geoData.coordinates
      },
      properties: { incidentId: incident.id }
    }
  });
  
  map.addLayer({
    id: layerId,
    type: 'line',
    source: sourceId,
    paint: {
      'line-color': colors.bg,
      'line-width': 4,
      'line-opacity': 0.8
    }
  });
  
  // Add click handler
  map.on('click', layerId, (e) => {
    new mapboxgl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(createDetailedPopup(incident).getHTML())
      .addTo(map);
  });
  
  // Add hover effect
  map.on('mouseenter', layerId, () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  
  map.on('mouseleave', layerId, () => {
    map.getCanvas().style.cursor = '';
  });
}

function renderPolygon(map: mapboxgl.Map, incident: Incident, geoData: any, colors: any) {
  const sourceId = `polygon-${incident.id}`;
  const fillLayerId = `polygon-fill-${incident.id}`;
  const borderLayerId = `polygon-border-${incident.id}`;
  
  map.addSource(sourceId, {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: geoData.coordinates
      },
      properties: { incidentId: incident.id }
    }
  });
  
  // Fill layer
  map.addLayer({
    id: fillLayerId,
    type: 'fill',
    source: sourceId,
    paint: {
      'fill-color': colors.bg,
      'fill-opacity': 0.3
    }
  });
  
  // Border layer
  map.addLayer({
    id: borderLayerId,
    type: 'line',
    source: sourceId,
    paint: {
      'line-color': colors.border,
      'line-width': 2
    }
  });
  
  // Add click handler
  map.on('click', fillLayerId, (e) => {
    new mapboxgl.Popup()
      .setLngLat(e.lngLat)
      .setHTML(createDetailedPopup(incident).getHTML())
      .addTo(map);
  });
  
  // Add hover effect
  map.on('mouseenter', fillLayerId, () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  
  map.on('mouseleave', fillLayerId, () => {
    map.getCanvas().style.cursor = '';
  });
}
```

## Data Models

### Frontend State Management

```typescript
// Global App Context
interface AppContextState {
  user: User | null;
  selectedDomain: Domain | null;
  agents: Agent[];
  domains: Domain[];
  isLoading: boolean;
}

interface AppContextActions {
  setUser: (user: User) => void;
  setSelectedDomain: (domain: Domain) => void;
  loadAgents: () => Promise<void>;
  loadDomains: () => Promise<void>;
  createAgent: (config: AgentConfig) => Promise<Agent>;
  updateAgent: (id: string, config: AgentConfig) => Promise<Agent>;
  deleteAgent: (id: string) => Promise<void>;
  createDomain: (config: DomainConfig) => Promise<Domain>;
}

// Agent Model
interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, SchemaField>;
  dependency_parent?: string;
  interrogative?: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  updated_at: number;
}

interface SchemaField {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required: boolean;
  description?: string;
}

// Domain Model
interface Domain {
  template_id: string;
  template_name: string;
  domain_id: string;
  description: string;
  ingest_agent_ids: string[];
  query_agent_ids: string[];
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  updated_at: number;
  agent_count: number;
  incident_count: number;
}

// Execution Status Model
interface ExecutionStatus {
  jobId: string;
  agentStatuses: Record<string, AgentStatus>;
  overallStatus: 'running' | 'complete' | 'error';
  startTime: number;
  endTime?: number;
}

interface AgentStatus {
  agentName: string;
  status: 'waiting' | 'invoking' | 'calling_tool' | 'complete' | 'error';
  message: string;
  confidence?: number;
  output?: any;
  error?: string;
  timestamp: number;
}

// Clarification Model
interface ClarificationRequest {
  jobId: string;
  fields: LowConfidenceField[];
  originalInput: string;
  round: number;
}

interface LowConfidenceField {
  agentName: string;
  fieldName: string;
  currentValue: any;
  confidence: number;
  question: string;
}
```

## Error Handling

### Network Error Resolution

**Problem:** "NetworkError when attempting to fetch resource" on page refresh

**Root Cause:** API client not properly initialized with authentication before making requests

**Solution:**

```typescript
// lib/api-client.ts

let isInitialized = false;
let initPromise: Promise<void> | null = null;

async function ensureInitialized(): Promise<void> {
  if (isInitialized) return;
  
  if (initPromise) {
    await initPromise;
    return;
  }
  
  initPromise = (async () => {
    try {
      // Wait for auth session to be ready
      await fetchAuthSession();
      isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize API client:', error);
      throw error;
    } finally {
      initPromise = null;
    }
  })();
  
  await initPromise;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {},
  showToast: boolean = true
): Promise<ApiResponse<T>> {
  try {
    // Ensure initialized before making request
    await ensureInitialized();
    
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });
    
    // ... rest of implementation
  } catch (error) {
    // Only show network error if it's a real network issue
    if (error instanceof TypeError && error.message.includes('fetch')) {
      if (showToast) {
        showNetworkErrorToast();
      }
    }
    
    return {
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 500,
    };
  }
}
```

### Retry Logic with Exponential Backoff

```typescript
async function apiRequestWithRetry<T = any>(
  endpoint: string,
  options: RequestInit = {},
  maxRetries: number = 3
): Promise<ApiResponse<T>> {
  let lastError: any;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await apiRequest<T>(endpoint, options, attempt === maxRetries - 1);
      
      // Success or non-retryable error
      if (response.status < 500 || response.data) {
        return response;
      }
      
      lastError = response.error;
    } catch (error) {
      lastError = error;
    }
    
    // Wait before retry (exponential backoff)
    if (attempt < maxRetries - 1) {
      const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  return {
    error: lastError || 'Request failed after retries',
    status: 500,
  };
}
```

## Backend Enhancements

### 1. Simplified Domain Creation Endpoint

**File:** `infrastructure/lambda/config-api/domain_template_manager.py`

Add new method for simplified creation:

```python
def create_from_agent_ids(
    self,
    tenant_id: str,
    user_id: str,
    template_name: str,
    domain_id: str,
    description: str,
    ingest_agent_ids: List[str],
    query_agent_ids: List[str]
) -> Dict[str, Any]:
    """
    Create domain template from agent IDs (simplified).
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        template_name: Domain name
        domain_id: Domain identifier
        description: Domain description
        ingest_agent_ids: List of ingestion agent IDs
        query_agent_ids: List of query agent IDs
    
    Returns:
        Created domain template
    """
    # Fetch agent configs
    agent_configs = []
    all_agent_ids = ingest_agent_ids + query_agent_ids
    
    for agent_id in all_agent_ids:
        agent = self._get_agent_config(tenant_id, agent_id)
        if agent:
            agent_configs.append(agent)
    
    # Create playbook configs
    playbook_configs = [
        {
            'playbook_type': 'ingestion',
            'agent_ids': ingest_agent_ids,
            'description': f'Ingestion pipeline for {template_name}'
        },
        {
            'playbook_type': 'query',
            'agent_ids': query_agent_ids,
            'description': f'Query pipeline for {template_name}'
        }
    ]
    
    # Build dependency graph from agent relationships
    dependency_graph_configs = self._build_dependency_graph(agent_configs)
    
    # Create full template
    template_config = {
        'template_name': template_name,
        'domain_id': domain_id,
        'description': description,
        'agent_configs': agent_configs,
        'playbook_configs': playbook_configs,
        'dependency_graph_configs': dependency_graph_configs
    }
    
    return self.create(tenant_id, user_id, template_config)

def _build_dependency_graph(self, agent_configs: List[Dict]) -> List[Dict]:
    """Build dependency graph from agent parent relationships"""
    edges = []
    
    for agent in agent_configs:
        if agent.get('dependency_parent'):
            edges.append({
                'from': agent['dependency_parent'],
                'to': agent['agent_id']
            })
    
    if not edges:
        return []
    
    return [{
        'edges': edges,
        'execution_levels': self._calculate_execution_levels(edges)
    }]
```

### 2. Enhanced List Endpoints with Metadata

**File:** `infrastructure/lambda/config-api/config_handler.py`

```python
def list_configs(tenant_id: str, config_type: str) -> Dict[str, Any]:
    """List all configurations with enhanced metadata"""
    try:
        if config_type == 'agent':
            results = agent_manager.list(tenant_id)
            # Add metadata
            for agent in results:
                agent['is_builtin'] = agent.get('is_builtin', False)
                agent['created_by_me'] = agent.get('created_by') == user_id
        
        elif config_type == 'domain_template':
            results = template_manager.list(tenant_id)
            # Add metadata
            for domain in results:
                domain['is_builtin'] = domain.get('is_builtin', False)
                domain['created_by_me'] = domain.get('created_by') == user_id
                domain['agent_count'] = len(domain.get('agent_configs', []))
                # Get incident count from data API
                domain['incident_count'] = get_incident_count(tenant_id, domain['domain_id'])
        
        else:
            return error_response(400, f'Invalid config type: {config_type}')
        
        return success_response(200, {'configs': results, 'count': len(results)})
    
    except Exception as e:
        logger.error(f"Error listing configs: {str(e)}", exc_info=True)
        return error_response(500, f"Failed to list configurations: {str(e)}")
```

### 3. Add Missing Query Agents

**File:** `infrastructure/lambda/config-api/seed_configs.json`

Add 5 more query agents to reach 11 total:

```json
{
  "agent_name": "Which Agent",
  "agent_type": "query",
  "interrogative": "which",
  "system_prompt": "Analyze selection and categorization patterns...",
  "tools": ["bedrock", "retrieval_api", "aggregation_api"],
  "output_schema": {
    "selections": "array",
    "categories": "array",
    "insight": "string"
  },
  "is_builtin": true
},
{
  "agent_name": "How Many Agent",
  "agent_type": "query",
  "interrogative": "how_many",
  "system_prompt": "Analyze counts and discrete quantities...",
  "tools": ["bedrock", "aggregation_api"],
  "output_schema": {
    "count": "number",
    "breakdown": "array",
    "insight": "string"
  },
  "is_builtin": true
},
{
  "agent_name": "How Much Agent",
  "agent_type": "query",
  "interrogative": "how_much",
  "system_prompt": "Analyze magnitudes and continuous quantities...",
  "tools": ["bedrock", "analytics_api"],
  "output_schema": {
    "magnitude": "number",
    "scale": "string",
    "insight": "string"
  },
  "is_builtin": true
},
{
  "agent_name": "From Where Agent",
  "agent_type": "query",
  "interrogative": "from_where",
  "system_prompt": "Analyze origins and source locations...",
  "tools": ["bedrock", "spatial_api", "retrieval_api"],
  "output_schema": {
    "origins": "array",
    "sources": "array",
    "insight": "string"
  },
  "is_builtin": true
},
{
  "agent_name": "What Kind Agent",
  "agent_type": "query",
  "interrogative": "what_kind",
  "system_prompt": "Analyze types and classifications...",
  "tools": ["bedrock", "retrieval_api"],
  "output_schema": {
    "types": "array",
    "classifications": "array",
    "insight": "string"
  },
  "is_builtin": true
}
```

## Testing Strategy

### Unit Tests

1. **API Client Tests** (`lib/__tests__/api-client.test.ts`)
   - Test initialization logic
   - Test retry mechanism
   - Test error handling
   - Test authentication flow

2. **Component Tests**
   - AgentFormDialog validation
   - DomainCreationWizard stage transitions
   - ClarificationDialog submission
   - ExecutionStatusPanel updates

### Integration Tests

1. **Agent CRUD Flow**
   - Create custom agent
   - List agents (built-in + custom)
   - Update agent configuration
   - Delete agent

2. **Domain Creation Flow**
   - Stage 1: Select ingest agents
   - Stage 2: Select query agents
   - View dependency graph
   - Create domain

3. **Execution Flow**
   - Submit report
   - Monitor real-time status
   - Handle low confidence
   - Submit clarification
   - View final results

4. **Geometry Rendering**
   - Render Point markers
   - Render LineString routes
   - Render Polygon areas
   - Test click interactions

### End-to-End Tests

1. **Complete Ingestion Flow**
   - User submits civic complaint
   - System processes with agents
   - Low confidence detected
   - User provides clarification
   - System re-processes
   - High confidence achieved
   - Results displayed on map

2. **Complete Query Flow**
   - User asks question
   - System executes query agents
   - Real-time status shown
   - Results aggregated
   - Map updated with highlights

## Performance Considerations

### Frontend Optimizations

1. **Lazy Loading**
   - Load agent list on demand
   - Load domain details on selection
   - Lazy load map layers

2. **Caching**
   - Cache agent list (5 min TTL)
   - Cache domain list (5 min TTL)
   - Cache built-in agent configs

3. **Debouncing**
   - Debounce search inputs
   - Debounce form validation
   - Throttle map updates

### Backend Optimizations

1. **Database Queries**
   - Add GSI for is_builtin filtering
   - Add GSI for created_by filtering
   - Batch get operations

2. **API Response Size**
   - Paginate agent/domain lists
   - Limit incident retrieval
   - Compress large responses

## Security Considerations

1. **Authorization**
   - Users can only delete their own custom agents
   - Users can only update their own custom agents
   - Built-in agents are read-only

2. **Input Validation**
   - Validate agent output schema (max 5 keys)
   - Validate system prompt length
   - Sanitize user inputs

3. **Rate Limiting**
   - Limit agent creation (10/hour per user)
   - Limit domain creation (5/hour per user)
   - Limit clarification rounds (3 max)
