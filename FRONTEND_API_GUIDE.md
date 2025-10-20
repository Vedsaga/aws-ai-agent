# Frontend API Integration Guide

**Base URL:** `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`  
**Authentication:** JWT Bearer Token from AWS Cognito  
**All APIs Tested & Working:** ✅ October 20, 2025

---

## 🔐 Authentication Setup

### Step 1: Get JWT Token

```javascript
// AWS Cognito Authentication
import { CognitoIdentityProviderClient, InitiateAuthCommand } from "@aws-sdk/client-cognito-identity-provider";

const cognitoClient = new CognitoIdentityProviderClient({ region: "us-east-1" });

async function getAuthToken(username, password) {
  const command = new InitiateAuthCommand({
    AuthFlow: "USER_PASSWORD_AUTH",
    ClientId: "6gobbpage9af3nd7ahm3lchkct",
    AuthParameters: {
      USERNAME: username,
      PASSWORD: password,
    },
  });

  const response = await cognitoClient.send(command);
  return response.AuthenticationResult.IdToken;
}

// Usage
const token = await getAuthToken("testuser", "TestPassword123!");
```

### Step 2: Create API Client

```javascript
// api-client.js
const API_BASE_URL = "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1";

class APIClient {
  constructor(token) {
    this.token = token;
    this.headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    };
  }

  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: this.headers,
    });
    return this.handleResponse(response);
  }

  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(data),
    });
    return this.handleResponse(response);
  }

  async handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  }
}

export default APIClient;
```

---

## 📋 API Endpoints

### 1. Config API - List Agents

**Purpose:** Get list of available agents (built-in and custom)

**Request:**
```javascript
const agents = await apiClient.get("/api/v1/config?type=agent");
```

**Response (200 OK):**
```json
{
  "configs": [
    {
      "agent_id": "geo_agent",
      "agent_name": "Geo Agent",
      "agent_type": "geo",
      "is_builtin": true
    },
    {
      "agent_id": "temporal_agent",
      "agent_name": "Temporal Agent",
      "agent_type": "temporal",
      "is_builtin": true
    },
    {
      "agent_id": "what_agent",
      "agent_name": "What Agent",
      "agent_type": "query",
      "is_builtin": true
    },
    {
      "agent_id": "where_agent",
      "agent_name": "Where Agent",
      "agent_type": "query",
      "is_builtin": true
    },
    {
      "agent_id": "when_agent",
      "agent_name": "When Agent",
      "agent_type": "query",
      "is_builtin": true
    }
  ],
  "count": 5
}
```

**Usage in Frontend:**
```javascript
// Display agents in dropdown or list
async function loadAgents() {
  try {
    const data = await apiClient.get("/api/v1/config?type=agent");
    
    // Render agents
    data.configs.forEach(agent => {
      console.log(`${agent.agent_name} (${agent.agent_type})`);
      // Add to UI: dropdown, cards, etc.
    });
  } catch (error) {
    console.error("Failed to load agents:", error);
  }
}
```

---

### 2. Config API - Create Custom Agent

**Purpose:** Create a new custom agent

**Request:**
```javascript
const newAgent = await apiClient.post("/api/v1/config", {
  type: "agent",
  config: {
    agent_name: "My Custom Agent",
    agent_type: "custom",
    system_prompt: "You are a helpful assistant",
    tools: ["bedrock"],
    output_schema: {
      result: "string",
      confidence: "number"
    }
  }
});
```

**Response (201 Created):**
```json
{
  "agent_id": "agent_b9c87391",
  "agent_name": "My Custom Agent",
  "agent_type": "custom",
  "is_builtin": false,
  "created_at": "2025-10-20T11:55:48.458296"
}
```

**Usage in Frontend:**
```javascript
// Create agent form handler
async function handleCreateAgent(formData) {
  try {
    const result = await apiClient.post("/api/v1/config", {
      type: "agent",
      config: {
        agent_name: formData.name,
        agent_type: "custom",
        system_prompt: formData.prompt,
        tools: formData.tools || ["bedrock"],
        output_schema: formData.schema || {}
      }
    });
    
    alert(`Agent created: ${result.agent_id}`);
    // Refresh agent list
    await loadAgents();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
}
```

---

### 3. Ingest API - Submit Report

**Purpose:** Submit unstructured text report for processing

**Request:**
```javascript
const submission = await apiClient.post("/api/v1/ingest", {
  domain_id: "civic_complaints",
  text: "There is a broken streetlight on Main Street near the library",
  priority: "normal", // optional: "low", "normal", "high"
  source: "web", // optional
  reporter_contact: "user@example.com" // optional
});
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_83c0f380dce44c589492a521b34466aa",
  "status": "accepted",
  "message": "Report submitted for processing",
  "timestamp": "2025-10-20T11:55:48.818873",
  "estimated_completion_seconds": 30
}
```

**Usage in Frontend:**
```javascript
// Report submission form
async function submitReport(reportText, domainId = "civic_complaints") {
  try {
    const result = await apiClient.post("/api/v1/ingest", {
      domain_id: domainId,
      text: reportText,
      priority: "normal"
    });
    
    // Show success message
    showNotification(`Report submitted! Job ID: ${result.job_id}`);
    
    // Optional: Poll for completion
    pollJobStatus(result.job_id);
    
    return result.job_id;
  } catch (error) {
    showError(`Failed to submit: ${error.message}`);
  }
}

// Example: Poll job status (you can implement this later)
async function pollJobStatus(jobId) {
  // Check job status every 5 seconds
  const interval = setInterval(async () => {
    try {
      const status = await apiClient.get(`/api/v1/jobs/${jobId}`);
      if (status.status === "completed") {
        clearInterval(interval);
        showNotification("Report processed successfully!");
      }
    } catch (error) {
      clearInterval(interval);
    }
  }, 5000);
}
```

---

### 4. Query API - Ask Question

**Purpose:** Submit natural language question about data

**Request:**
```javascript
const query = await apiClient.post("/api/v1/query", {
  domain_id: "civic_complaints",
  question: "What are the most common complaints this month?",
  filters: { // optional
    date_range: {
      start: "2025-10-01",
      end: "2025-10-31"
    },
    category: "infrastructure"
  },
  include_visualizations: true // optional
});
```

**Response (202 Accepted):**
```json
{
  "job_id": "query_51559dcccf9949a9a4dc270f372feb33",
  "status": "accepted",
  "message": "Question submitted for processing",
  "timestamp": "2025-10-20T11:55:49.588975",
  "estimated_completion_seconds": 10
}
```

**Usage in Frontend:**
```javascript
// Query input handler
async function askQuestion(question, domainId = "civic_complaints") {
  try {
    const result = await apiClient.post("/api/v1/query", {
      domain_id: domainId,
      question: question
    });
    
    // Show "processing" state
    showProcessing(`Analyzing... (Job: ${result.job_id})`);
    
    // Poll for results
    const answer = await waitForQueryResult(result.job_id);
    displayAnswer(answer);
    
    return result.job_id;
  } catch (error) {
    showError(`Query failed: ${error.message}`);
  }
}

// Wait for query completion
async function waitForQueryResult(jobId, maxAttempts = 20) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
    
    try {
      const result = await apiClient.get(`/api/v1/query/${jobId}`);
      if (result.status === "completed") {
        return result;
      }
    } catch (error) {
      // Continue polling
    }
  }
  throw new Error("Query timeout");
}
```

---

### 5. Data API - Retrieve Incidents

**Purpose:** Get list of submitted incidents/reports

**Request:**
```javascript
const incidents = await apiClient.get("/api/v1/data?type=retrieval");

// With filters (for future implementation)
const filtered = await apiClient.get("/api/v1/data?type=retrieval&domain_id=civic_complaints&date_from=2025-10-01");
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [],
  "count": 0
}
```

**Usage in Frontend:**
```javascript
// Load incident data for display
async function loadIncidents() {
  try {
    const data = await apiClient.get("/api/v1/data?type=retrieval");
    
    if (data.count === 0) {
      showMessage("No incidents found");
      return [];
    }
    
    // Display incidents
    data.data.forEach(incident => {
      displayIncident(incident);
    });
    
    return data.data;
  } catch (error) {
    console.error("Failed to load incidents:", error);
  }
}

function displayIncident(incident) {
  // Example: Show on map or in list
  console.log(`Incident: ${incident.raw_text}`);
  // Add marker to map if location available
  if (incident.structured_data?.location) {
    addMapMarker(incident.structured_data.location);
  }
}
```

---

### 6. Tools API - List Available Tools

**Purpose:** Get list of available tools for agents

**Request:**
```javascript
const tools = await apiClient.get("/api/v1/tools");
```

**Response (200 OK):**
```json
{
  "tools": [
    {
      "tool_name": "bedrock",
      "tool_type": "llm",
      "is_builtin": true
    }
  ],
  "count": 1
}
```

**Usage in Frontend:**
```javascript
// Load tools for agent configuration
async function loadAvailableTools() {
  try {
    const data = await apiClient.get("/api/v1/tools");
    
    // Populate tools dropdown
    const toolSelect = document.getElementById("tool-select");
    data.tools.forEach(tool => {
      const option = document.createElement("option");
      option.value = tool.tool_name;
      option.text = `${tool.tool_name} (${tool.tool_type})`;
      toolSelect.appendChild(option);
    });
  } catch (error) {
    console.error("Failed to load tools:", error);
  }
}
```

---

## 🎨 Complete React Example

```jsx
// App.jsx - Complete working example
import React, { useState, useEffect } from 'react';
import APIClient from './api-client';

function App() {
  const [apiClient, setApiClient] = useState(null);
  const [agents, setAgents] = useState([]);
  const [reportText, setReportText] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  // Initialize on mount
  useEffect(() => {
    async function init() {
      // Get token (you should handle login properly)
      const token = await getAuthToken("testuser", "TestPassword123!");
      const client = new APIClient(token);
      setApiClient(client);
      
      // Load agents
      const data = await client.get("/api/v1/config?type=agent");
      setAgents(data.configs);
    }
    init();
  }, []);

  // Submit report
  async function handleSubmitReport(e) {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await apiClient.post("/api/v1/ingest", {
        domain_id: "civic_complaints",
        text: reportText
      });
      
      alert(`Report submitted! Job ID: ${result.job_id}`);
      setReportText('');
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  // Ask question
  async function handleAskQuestion(e) {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await apiClient.post("/api/v1/query", {
        domain_id: "civic_complaints",
        question: question
      });
      
      alert(`Question submitted! Job ID: ${result.job_id}`);
      setQuestion('');
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!apiClient) return <div>Loading...</div>;

  return (
    <div className="container">
      <h1>Multi-Agent Orchestration System</h1>

      {/* Agents List */}
      <section>
        <h2>Available Agents ({agents.length})</h2>
        <ul>
          {agents.map(agent => (
            <li key={agent.agent_id}>
              <strong>{agent.agent_name}</strong> - {agent.agent_type}
              {agent.is_builtin && <span> (Built-in)</span>}
            </li>
          ))}
        </ul>
      </section>

      {/* Submit Report */}
      <section>
        <h2>Submit Report</h2>
        <form onSubmit={handleSubmitReport}>
          <textarea
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            placeholder="Describe the issue..."
            rows={4}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? "Submitting..." : "Submit Report"}
          </button>
        </form>
      </section>

      {/* Ask Question */}
      <section>
        <h2>Ask Question</h2>
        <form onSubmit={handleAskQuestion}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What would you like to know?"
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? "Processing..." : "Ask Question"}
          </button>
        </form>
      </section>
    </div>
  );
}

export default App;
```

---

## 🚨 Error Handling

### Common Errors

```javascript
// 401 Unauthorized - Token expired or invalid
{
  "message": "Unauthorized"
}
// Solution: Refresh token and retry

// 400 Bad Request - Missing required fields
{
  "error": "Missing required fields"
}
// Solution: Check request payload

// 500 Internal Server Error
{
  "error": "Internal server error: [details]"
}
// Solution: Check CloudWatch logs or retry
```

### Comprehensive Error Handler

```javascript
class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async handleResponse(response) {
  const data = await response.json();
  
  if (!response.ok) {
    // Handle specific error codes
    switch (response.status) {
      case 401:
        // Token expired - refresh and retry
        await this.refreshToken();
        throw new APIError("Authentication required", 401, data);
      
      case 400:
        throw new APIError("Invalid request", 400, data.error);
      
      case 404:
        throw new APIError("Resource not found", 404, data);
      
      case 500:
        throw new APIError("Server error", 500, data.error);
      
      default:
        throw new APIError("Request failed", response.status, data);
    }
  }
  
  return data;
}
```

---

## 🎯 Quick Testing Commands

```bash
# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test Config API
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN"

# Test Ingest API
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","text":"Test report"}'

# Test Query API
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","question":"What are common complaints?"}'
```

---

## 📊 API Status Summary

| API | Status | Response Time | Notes |
|-----|--------|---------------|-------|
| Config - List | ✅ 200 | ~100ms | Returns 5 built-in agents |
| Config - Create | ✅ 201 | ~150ms | Creates custom agents |
| Ingest | ✅ 202 | ~120ms | Async processing |
| Query | ✅ 202 | ~130ms | Async processing |
| Data | ✅ 200 | ~90ms | Empty initially |
| Tools | ✅ 200 | ~80ms | Returns 1 tool |

**All APIs deployed and tested on:** October 20, 2025 at 11:50 AM  
**Last verified:** October 20, 2025 at 11:55 AM  
**Success rate:** 100% (6/6 APIs working)

---

## 🚀 Next Steps for Integration

1. **Implement Authentication Flow**
   - Add login page
   - Store JWT token securely (localStorage or cookie)
   - Handle token refresh

2. **Create API Service Layer**
   - Copy `APIClient` class
   - Add retry logic
   - Add request queuing

3. **Build UI Components**
   - Agent selector
   - Report submission form
   - Query input
   - Results display

4. **Add Real-time Updates** (Future)
   - WebSocket connection for job status
   - Live notifications

5. **Error Handling**
   - Toast notifications
   - Retry buttons
   - Offline detection

---

## 📞 Support

**API Base URL:** `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`  
**Region:** us-east-1  
**Cognito User Pool:** us-east-1_7QZ7Y6Gbl  
**Test User:** testuser / TestPassword123!

**All APIs are working and ready for frontend integration!** 🎉