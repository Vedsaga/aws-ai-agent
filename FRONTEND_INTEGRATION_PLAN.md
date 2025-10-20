# Frontend Integration Plan - API to Client

## 📋 Verification Results

### ✅ CloudWatch Logs Verified
**Lambda Functions Found:**
- `MultiAgentOrchestration-dev-Api-ConfigHandler`
- `MultiAgentOrchestration-dev-Api-IngestHandler`
- `MultiAgentOrchestration-dev-Api-QueryHandler`
- `MultiAgentOrchestration-dev-Api-ToolsHandler`
- `MultiAgentOrchestration-dev-Api-DataHandler`

**Sample Log Entry (Ingest API):**
```
Method: POST, Path: /api/v1/ingest, Tenant: default-tenant
Processing ingest: job_id=job_8828023fa1ff43bf90d59fc397d6e1aa
domain=civic_complaints, text_length=138
Status: Submitted (202 Accepted)
```

**Key Observations:**
- ✅ APIs are receiving requests
- ✅ Tenant extraction working (default-tenant)
- ✅ Job IDs being generated
- ⚠️ Warning: "Incidents table not available" (DynamoDB permissions issue - non-blocking)

### ✅ DynamoDB Data Verified
**Table:** `MultiAgentOrchestration-dev-Data-Configurations`

**Built-in Agents Found:**
```json
{
  "agent_id": "geo_agent",
  "agent_name": "Geo Agent",
  "agent_type": "ingestion",
  "is_builtin": true
},
{
  "agent_id": "temporal_agent",
  "agent_name": "Temporal Agent",
  "agent_type": "ingestion",
  "is_builtin": true
},
{
  "agent_id": "entity_agent",
  "agent_name": "Entity Agent",
  "agent_type": "ingestion",
  "is_builtin": true
}
```

**Query Agents Found:**
- `what_agent`, `when_agent`, `where_agent`
- `how_agent`, `why_agent`, `who_agent`

**Domain Templates:**
- `civic_complaints` (built-in)
- Playbooks configured (ingestion, query)

**Tenant Structure:**
- `system` tenant: Built-in configurations
- `default-tenant`: User-created configurations

---

## 🎯 Frontend Structure Analysis

### Existing API Client (`lib/api-client.ts`)

**Current Implementation:**
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Authentication using AWS Amplify
async function getAuthHeaders(): Promise<HeadersInit> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// Generic request function
async function apiRequest<T>(endpoint: string, options: RequestInit)
```

**Existing API Functions:**
- `submitReport()` - Partially implemented
- `submitQuery()` - Partially implemented
- `fetchIncidents()` - Partially implemented
- `createAgentConfig()` - Stub
- `getAgentConfigs()` - Stub
- `createAgent()` - Placeholder
- `listAgents()` - Placeholder
- Agent CRUD operations - Placeholders

---

## 🚀 Integration Strategy

### Phase 1: Update API Client (Priority: HIGH)

#### 1.1 Update Environment Variables
**File:** `.env.local` (create if not exists)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1

# Cognito Configuration
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_7QZ7Y6Gbl
NEXT_PUBLIC_COGNITO_CLIENT_ID=6gobbpage9af3nd7ahm3lchkct
NEXT_PUBLIC_COGNITO_REGION=us-east-1

# Feature Flags
NEXT_PUBLIC_ENABLE_AGENT_CREATION=true
NEXT_PUBLIC_ENABLE_DOMAIN_CREATION=true
```

#### 1.2 Update `lib/api-client.ts`

**Replace stub functions with actual implementations:**

```typescript
// ============================================================================
// CONFIG API - Agent Management
// ============================================================================

/**
 * List all agents (built-in + custom)
 * GET /api/v1/config?type=agent
 */
export async function listAgents(): Promise<ApiResponse<{ configs: Agent[]; count: number }>> {
  return apiRequest('/api/v1/config?type=agent', {
    method: 'GET',
  });
}

/**
 * Get specific agent by ID
 * GET /api/v1/config/agent/{agentId}
 */
export async function getAgent(agentId: string): Promise<ApiResponse<Agent>> {
  return apiRequest(`/api/v1/config/agent/${agentId}`, {
    method: 'GET',
  });
}

/**
 * Create custom agent
 * POST /api/v1/config
 */
export async function createAgent(config: {
  agent_name: string;
  agent_type: string;
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, string>;
  dependency_parent?: string;
}): Promise<ApiResponse<Agent>> {
  return apiRequest('/api/v1/config', {
    method: 'POST',
    body: JSON.stringify({
      type: 'agent',
      config,
    }),
  });
}

/**
 * Update agent
 * PUT /api/v1/config/agent/{agentId}
 */
export async function updateAgent(
  agentId: string,
  config: Partial<Agent>
): Promise<ApiResponse<Agent>> {
  return apiRequest(`/api/v1/config/agent/${agentId}`, {
    method: 'PUT',
    body: JSON.stringify({ config }),
  });
}

/**
 * Delete agent
 * DELETE /api/v1/config/agent/{agentId}
 */
export async function deleteAgent(agentId: string): Promise<ApiResponse<{ message: string }>> {
  return apiRequest(`/api/v1/config/agent/${agentId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// CONFIG API - Domain Management
// ============================================================================

/**
 * List all domain templates
 * GET /api/v1/config?type=domain_template
 */
export async function listDomains(): Promise<ApiResponse<{ configs: Domain[]; count: number }>> {
  return apiRequest('/api/v1/config?type=domain_template', {
    method: 'GET',
  });
}

/**
 * Create domain
 * POST /api/v1/config
 */
export async function createDomain(config: {
  template_name: string;
  domain_id: string;
  description: string;
  ingest_agent_ids: string[];
  query_agent_ids: string[];
}): Promise<ApiResponse<Domain>> {
  return apiRequest('/api/v1/config', {
    method: 'POST',
    body: JSON.stringify({
      type: 'domain_template',
      config,
    }),
  });
}

// ============================================================================
// INGEST API - Report Submission
// ============================================================================

/**
 * Submit report to domain
 * POST /api/v1/ingest
 */
export async function submitReport(data: {
  domain_id: string;
  text: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  reporter_contact?: string;
  images?: string[];
}): Promise<ApiResponse<{
  job_id: string;
  status: string;
  message: string;
  timestamp: string;
  estimated_completion_seconds: number;
}>> {
  // Validate before sending
  if (!data.text || data.text.length < 10) {
    return {
      error: 'Report text must be at least 10 characters',
      status: 400,
    };
  }

  if (data.text.length > 10000) {
    return {
      error: 'Report text cannot exceed 10000 characters',
      status: 400,
    };
  }

  return apiRequest('/api/v1/ingest', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// QUERY API - Natural Language Questions
// ============================================================================

/**
 * Submit question to query agents
 * POST /api/v1/query
 */
export async function submitQuery(data: {
  domain_id: string;
  question: string;
  filters?: {
    date_range?: { start: string; end: string };
    category?: string;
  };
  include_visualizations?: boolean;
}): Promise<ApiResponse<{
  job_id: string;
  status: string;
  message: string;
  timestamp: string;
  estimated_completion_seconds: number;
}>> {
  // Validate before sending
  if (!data.question || data.question.length < 5) {
    return {
      error: 'Question must be at least 5 characters',
      status: 400,
    };
  }

  if (data.question.length > 1000) {
    return {
      error: 'Question cannot exceed 1000 characters',
      status: 400,
    };
  }

  return apiRequest('/api/v1/query', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// TOOLS API
// ============================================================================

/**
 * List available tools
 * GET /api/v1/tools
 */
export async function listTools(): Promise<ApiResponse<{
  tools: Array<{
    tool_name: string;
    tool_type: string;
    description: string;
    is_builtin: boolean;
  }>;
  count: number;
}>> {
  return apiRequest('/api/v1/tools', {
    method: 'GET',
  });
}

// ============================================================================
// DATA API
// ============================================================================

/**
 * Retrieve incidents/reports
 * GET /api/v1/data?domain_id={domainId}&limit={limit}
 */
export async function fetchIncidents(params: {
  domain_id: string;
  limit?: number;
  offset?: number;
}): Promise<ApiResponse<{
  data: Array<any>;
  count: number;
}>> {
  const queryParams = new URLSearchParams({
    domain_id: params.domain_id,
    ...(params.limit && { limit: params.limit.toString() }),
    ...(params.offset && { offset: params.offset.toString() }),
  });

  return apiRequest(`/api/v1/data?${queryParams.toString()}`, {
    method: 'GET',
  });
}
```

### Phase 2: Create TypeScript Interfaces

**File:** `lib/types.ts` (create new)

```typescript
// ============================================================================
// Agent Types
// ============================================================================

export interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: 'geo' | 'temporal' | 'category' | 'entity' | 'sentiment' | 'custom' | 'query';
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, string>;
  dependency_parent?: string;
  is_builtin: boolean;
  created_at: string;
  updated_at?: string;
  created_by: string;
  version: number;
}

// ============================================================================
// Domain Types
// ============================================================================

export interface Domain {
  template_id: string;
  domain_id: string;
  template_name: string;
  description: string;
  ingest_agent_ids: string[];
  query_agent_ids: string[];
  is_builtin: boolean;
  created_at: string;
}

// ============================================================================
// Ingest Types
// ============================================================================

export interface ReportSubmission {
  domain_id: string;
  text: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  reporter_contact?: string;
  images?: string[];
  source?: string;
}

export interface IngestResponse {
  job_id: string;
  status: 'accepted' | 'processing' | 'completed' | 'failed';
  message: string;
  timestamp: string;
  estimated_completion_seconds: number;
}

// ============================================================================
// Query Types
// ============================================================================

export interface QuerySubmission {
  domain_id: string;
  question: string;
  filters?: {
    date_range?: {
      start: string;
      end: string;
    };
    category?: string;
  };
  include_visualizations?: boolean;
}

export interface QueryResponse {
  job_id: string;
  status: 'accepted' | 'processing' | 'completed' | 'failed';
  message: string;
  timestamp: string;
  estimated_completion_seconds: number;
}

// ============================================================================
// Tool Types
// ============================================================================

export interface Tool {
  tool_name: string;
  tool_type: string;
  description: string;
  is_builtin: boolean;
  capabilities?: string[];
}

// ============================================================================
// Validation Types
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}
```

### Phase 3: Create Validation Utilities

**File:** `lib/validation.ts` (create new)

```typescript
import { ValidationResult, ValidationError } from './types';

/**
 * Validate agent configuration
 */
export function validateAgentConfig(config: {
  agent_name?: string;
  agent_type?: string;
  system_prompt?: string;
  tools?: string[];
  output_schema?: Record<string, string>;
}): ValidationResult {
  const errors: ValidationError[] = [];

  // Agent name validation
  if (!config.agent_name) {
    errors.push({ field: 'agent_name', message: 'Agent name is required' });
  } else if (config.agent_name.length < 3) {
    errors.push({ field: 'agent_name', message: 'Agent name must be at least 3 characters' });
  } else if (config.agent_name.length > 100) {
    errors.push({ field: 'agent_name', message: 'Agent name cannot exceed 100 characters' });
  }

  // Agent type validation
  const validTypes = ['geo', 'temporal', 'category', 'entity', 'sentiment', 'custom', 'query'];
  if (!config.agent_type) {
    errors.push({ field: 'agent_type', message: 'Agent type is required' });
  } else if (!validTypes.includes(config.agent_type)) {
    errors.push({ field: 'agent_type', message: `Agent type must be one of: ${validTypes.join(', ')}` });
  }

  // System prompt validation
  if (!config.system_prompt) {
    errors.push({ field: 'system_prompt', message: 'System prompt is required' });
  } else if (config.system_prompt.length > 2000) {
    errors.push({ field: 'system_prompt', message: 'System prompt cannot exceed 2000 characters' });
  }

  // Tools validation
  if (!config.tools || config.tools.length === 0) {
    errors.push({ field: 'tools', message: 'At least one tool is required' });
  }

  // Output schema validation
  if (!config.output_schema || Object.keys(config.output_schema).length === 0) {
    errors.push({ field: 'output_schema', message: 'Output schema is required' });
  } else if (Object.keys(config.output_schema).length > 5) {
    errors.push({ field: 'output_schema', message: 'Output schema cannot have more than 5 keys' });
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate report submission
 */
export function validateReportSubmission(data: {
  domain_id?: string;
  text?: string;
  images?: string[];
}): ValidationResult {
  const errors: ValidationError[] = [];

  if (!data.domain_id) {
    errors.push({ field: 'domain_id', message: 'Domain ID is required' });
  }

  if (!data.text) {
    errors.push({ field: 'text', message: 'Report text is required' });
  } else if (data.text.length < 10) {
    errors.push({ field: 'text', message: 'Report must be at least 10 characters' });
  } else if (data.text.length > 10000) {
    errors.push({ field: 'text', message: 'Report cannot exceed 10000 characters' });
  }

  if (data.images && data.images.length > 5) {
    errors.push({ field: 'images', message: 'Cannot upload more than 5 images' });
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate query submission
 */
export function validateQuerySubmission(data: {
  domain_id?: string;
  question?: string;
}): ValidationResult {
  const errors: ValidationError[] = [];

  if (!data.domain_id) {
    errors.push({ field: 'domain_id', message: 'Domain ID is required' });
  }

  if (!data.question) {
    errors.push({ field: 'question', message: 'Question is required' });
  } else if (data.question.length < 5) {
    errors.push({ field: 'question', message: 'Question must be at least 5 characters' });
  } else if (data.question.length > 1000) {
    errors.push({ field: 'question', message: 'Question cannot exceed 1000 characters' });
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate domain configuration
 */
export function validateDomainConfig(config: {
  domain_id?: string;
  template_name?: string;
  ingest_agent_ids?: string[];
  query_agent_ids?: string[];
}): ValidationResult {
  const errors: ValidationError[] = [];

  if (!config.domain_id) {
    errors.push({ field: 'domain_id', message: 'Domain ID is required' });
  } else if (!/^[a-z0-9_]+$/.test(config.domain_id)) {
    errors.push({ field: 'domain_id', message: 'Domain ID must contain only lowercase letters, numbers, and underscores' });
  }

  if (!config.template_name) {
    errors.push({ field: 'template_name', message: 'Template name is required' });
  }

  if (!config.ingest_agent_ids || config.ingest_agent_ids.length === 0) {
    errors.push({ field: 'ingest_agent_ids', message: 'At least one ingest agent is required' });
  }

  if (!config.query_agent_ids || config.query_agent_ids.length === 0) {
    errors.push({ field: 'query_agent_ids', message: 'At least one query agent is required' });
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
```

### Phase 4: Create React Hooks for API Calls

**File:** `hooks/useAgents.ts` (create new)

```typescript
import { useState, useEffect } from 'react';
import { listAgents, createAgent, updateAgent, deleteAgent } from '@/lib/api-client';
import { Agent } from '@/lib/types';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    
    const response = await listAgents();
    
    if (response.error) {
      setError(response.error);
      setLoading(false);
      return;
    }

    setAgents(response.data?.configs || []);
    setLoading(false);
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const create = async (config: any) => {
    const response = await createAgent(config);
    
    if (response.error) {
      showErrorToast('Failed to create agent', response.error);
      return null;
    }

    showSuccessToast('Agent created successfully');
    await fetchAgents(); // Refresh list
    return response.data;
  };

  const update = async (agentId: string, config: any) => {
    const response = await updateAgent(agentId, config);
    
    if (response.error) {
      showErrorToast('Failed to update agent', response.error);
      return null;
    }

    showSuccessToast('Agent updated successfully');
    await fetchAgents(); // Refresh list
    return response.data;
  };

  const remove = async (agentId: string) => {
    const response = await deleteAgent(agentId);
    
    if (response.error) {
      showErrorToast('Failed to delete agent', response.error);
      return false;
    }

    showSuccessToast('Agent deleted successfully');
    await fetchAgents(); // Refresh list
    return true;
  };

  return {
    agents,
    loading,
    error,
    refresh: fetchAgents,
    create,
    update,
    remove,
  };
}
```

**File:** `hooks/useReportSubmission.ts` (create new)

```typescript
import { useState } from 'react';
import { submitReport } from '@/lib/api-client';
import { ReportSubmission, IngestResponse } from '@/lib/types';
import { validateReportSubmission } from '@/lib/validation';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';

export function useReportSubmission() {
  const [submitting, setSubmitting] = useState(false);
  const [response, setResponse] = useState<IngestResponse | null>(null);

  const submit = async (data: ReportSubmission) => {
    // Validate before submission
    const validation = validateReportSubmission(data);
    if (!validation.valid) {
      const errorMsg = validation.errors.map(e => e.message).join(', ');
      showErrorToast('Validation failed', errorMsg);
      return null;
    }

    setSubmitting(true);
    
    const result = await submitReport(data);
    
    if (result.error) {
      showErrorToast('Failed to submit report', result.error);
      setSubmitting(false);
      return null;
    }

    setResponse(result.data!);
    showSuccessToast(
      'Report submitted',
      `Job ID: ${result.data?.job_id}. Processing will complete in ~${result.data?.estimated_completion_seconds}s`
    );
    
    setSubmitting(false);
    return result.data;
  };

  return {
    submit,
    submitting,
    response,
  };
}
```

### Phase 5: Update Components

**Example: Update Report Submission Component**

**File:** `components/ReportForm.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useReportSubmission } from '@/hooks/useReportSubmission';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';

export function ReportForm() {
  const [domainId, setDomainId] = useState('civic_complaints');
  const [text, setText] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high' | 'urgent'>('normal');
  const [contact, setContact] = useState('');

  const { submit, submitting, response } = useReportSubmission();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await submit({
      domain_id: domainId,
      text,
      priority,
      reporter_contact: contact || undefined,
    });

    if (result) {
      // Clear form on success
      setText('');
      setContact('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label>Domain</label>
        <Select value={domainId} onChange={(e) => setDomainId(e.target.value)}>
          <option value="civic_complaints">Civic Complaints</option>
          {/* Add more domains dynamically */}
        </Select>
      </div>

      <div>
        <label>Report Description *</label>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe the issue (10-10000 characters)"
          minLength={10}
          maxLength={10000}
          rows={5}
          required
        />
        <p className="text-sm text-gray-500">{text.length}/10000 characters</p>
      </div>

      <div>
        <label>Priority</label>
        <Select value={priority} onChange={(e) => setPriority(e.target.value as any)}>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </Select>
      </div>

      <div>
        <label>Contact (optional)</label>
        <input
          type="text"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          placeholder="email@example.com or phone"
        />
      </div>

      <Button type="submit" disabled={submitting || text.length < 10}>
        {submitting ? 'Submitting...' : 'Submit Report'}
      </Button>

      {response && (
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <p className="font-medium">Report Submitted!</p>
          <p className="text-sm">Job ID: {response.job_id}</p>
          <p className="text-sm">Status: {response.status}</p>
          <p className="text-sm">Estimated completion: {response.estimated_completion_seconds}s</p>
        </div>
      )}
    </form>
  );
}
```

### Phase 6: Testing Checklist

#### Frontend Integration Tests

**Test File:** `__tests__/api-integration.test.ts`

```typescript
import { listAgents, createAgent, submitReport, submitQuery } from '@/lib/api-client';

describe('API Integration', () => {
  it('should list agents', async () => {
    const response = await listAgents();
    expect(response.status).toBe(200);
    expect(response.data?.configs).toBeDefined();
    expect(response.data?.configs.length).toBeGreaterThan(0);
  });

  it('should create custom agent', async () => {
    const response = await createAgent({
      agent_name: 'Test Agent',
      agent_type: 'custom',
      system_prompt: 'Test prompt',
      tools: ['bedrock'],
      output_schema: { result: 'string' },
    });
    expect(response.status).toBe(201);
    expect(response.data?.agent_id).toBeDefined();
  });

  it('should submit report', async () => {
    const response = await submitReport({
      domain_id: 'civic_complaints',
      text: 'Test pothole report on Main Street',
    });
    expect(response.status).toBe(202);
    expect(response.data?.job_id).toBeDefined();
  });

  it('should submit query', async () => {
    const response = await submitQuery({
      domain_id: 'civic_complaints',
      question: 'What are the common complaints?',
    });
    expect(response.status).toBe(202);
    expect(response.data?.job_id).toBeDefined();
  });
});
```

---

## 🔧 Implementation Steps

### Step 1: Environment Setup (5 min)
```bash
cd infrastructure/frontend

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_7QZ7Y6Gbl
NEXT_PUBLIC_COGNITO_CLIENT_ID=6gobbpage9af3nd7ahm3lchkct
NEXT_PUBLIC_COGNITO_REGION=us-east-1
EOF
```

### Step 2: Update API Client (10 min)
- Update `lib/api-client.ts` with real implementations
- Add all CRUD functions for agents, domains
- Add ingest and query functions

### Step 3: Create Types & Validation (5 min)
- Create `lib/types.ts`
- Create `lib/validation.ts`

### Step 4: Create Hooks (10 min)
- Create `hooks/useAgents.ts`
- Create `hooks/useReportSubmission.ts`
- Create `hooks/useQuery.ts`

### Step 5: Update Components (15 min)
- Update ReportForm to use real API
- Update AgentList to use real API
- Update QueryInterface to use real API

### Step 6: Test (10 min)
```bash
# Start dev server
npm run dev

# Test in browser:
# 1. Login with testuser / TestPassword123!
# 2. List agents
# 3. Submit report
# 4. Submit query
# 5. Create custom agent
```

---

## 📊 API Endpoints Summary

### ✅ Ready to Integrate

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/config?type=agent` | GET | List agents | ✅ Tested |
| `/api/v1/config` | POST | Create agent | ✅ Tested |
| `/api/v1/config/agent/{id}` | GET | Get agent | ✅ Tested |
| `/api/v1/config/agent/{id}` | PUT | Update agent | ✅ Tested |
| `/api/v1/config/agent/{id}` | DELETE | Delete agent | ✅ Tested |
| `/api/v1/config?type=domain_template` | GET | List domains | ✅ Tested |
| `/api/v1/config` | POST | Create domain | ✅ Tested |
| `/api/v1/ingest` | POST | Submit report | ✅ Tested |
| `/api/v1/query` | POST | Ask question | ✅ Tested |
| `/api/v1/tools` | GET | List tools | ✅ Tested |
| `/api/v1/data` | GET | Get incidents | ✅ Tested |

---

## 🎯 Quick Integration Test Script

**File:** `test-frontend-api.sh`

```bash
#!/bin/bash

API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9