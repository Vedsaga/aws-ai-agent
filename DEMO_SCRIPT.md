# Multi-Agent Orchestration System - Demo Script

**Version:** 1.0  
**Last Updated:** October 20, 2025  
**Total Demo Time:** ~9 minutes

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Demo Steps](#demo-steps)
  - [Step 1: Authentication (30 seconds)](#step-1-authentication-30-seconds)
  - [Step 2: Create Custom Agent (1 minute)](#step-2-create-custom-agent-1-minute)
  - [Step 3: Create Custom Domain (1 minute)](#step-3-create-custom-domain-1-minute)
  - [Step 4: Submit Report (2 minutes)](#step-4-submit-report-2-minutes)
  - [Step 5: Ask Question (2 minutes)](#step-5-ask-question-2-minutes)
  - [Step 6: Retrieve Data (1 minute)](#step-6-retrieve-data-1-minute)
- [End-to-End Workflow](#end-to-end-workflow)
- [Troubleshooting](#troubleshooting)

---

## Introduction

This demo script provides a step-by-step walkthrough of the Multi-Agent Orchestration System's core capabilities. It demonstrates:

- **Custom Agent Creation**: Define specialized agents with custom prompts and output schemas
- **Domain Configuration**: Create custom domains with agent pipelines
- **Report Ingestion**: Submit incident reports for automated processing
- **Query Processing**: Ask natural language questions and get AI-generated insights
- **Data Retrieval**: Access structured data with powerful filtering

Each step includes curl commands, expected responses, and timing estimates for a smooth demonstration.

---

## Prerequisites

Before starting the demo, ensure you have:

1. **API Access**
   - API Base URL: `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`
   - Valid JWT token from AWS Cognito

2. **Tools Installed**
   - `curl` (for API requests)
   - `jq` (optional, for JSON formatting)

3. **Environment Variables**

```bash
export API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
export JWT_TOKEN="your-jwt-token-here"
```

4. **Test Data Ready**
   - Sample incident report text
   - Sample question for query

---

## Demo Steps

### Step 1: Authentication (30 seconds)

**Objective:** Obtain a valid JWT token from AWS Cognito

**Cognito Configuration:**
- User Pool ID: `us-east-1_7QZ7Y6Gbl`
- Client ID: `6gobbpage9af3nd7ahm3lchkct`
- Region: `us-east-1`

**Option A: Using AWS CLI**

```bash
# Authenticate with username and password
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=your-username,PASSWORD=your-password \
  --region us-east-1
```

**Expected Response:**

```json
{
  "AuthenticationResult": {
    "AccessToken": "eyJraWQiOiJ...",
    "IdToken": "eyJraWQiOiJ...",
    "RefreshToken": "eyJjdHkiOiJ...",
    "TokenType": "Bearer",
    "ExpiresIn": 3600
  }
}
```

**Extract and Set Token:**

```bash
export JWT_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=your-username,PASSWORD=your-password \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo "Token obtained: ${JWT_TOKEN:0:50}..."
```

**Option B: Using Frontend Login**

1. Navigate to the frontend application
2. Log in with your credentials
3. Open browser developer tools (F12)
4. Go to Application > Local Storage
5. Copy the JWT token value
6. Export it: `export JWT_TOKEN="your-token-here"`

**Verification:**

```bash
# Test authentication with a simple API call
curl -X GET "$API_URL/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected:** List of agents (200 OK)

**Timing:** 30 seconds

---

### Step 2: Create Custom Agent (1 minute)

**Objective:** Create a custom agent that classifies incident severity

**curl Command:**

```bash
curl -X POST "$API_URL/config" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Severity Classifier",
      "agent_type": "custom",
      "system_prompt": "Analyze incident reports and classify their severity on a scale of 1-10, where 1 is minor and 10 is critical. Consider factors like public safety impact, urgency, and potential for escalation. Provide a severity score, reasoning, and urgency level.",
      "tools": ["bedrock"],
      "output_schema": {
        "severity_score": "number",
        "reasoning": "string",
        "urgency": "string",
        "estimated_response_time": "string"
      }
    }
  }'
```

**Expected Response (201 Created):**

```json
{
  "tenant_id": "tenant-abc123",
  "config_key": "agent#agent-xyz789",
  "config_type": "agent",
  "agent_id": "agent-xyz789",
  "agent_name": "Severity Classifier",
  "agent_type": "custom",
  "system_prompt": "Analyze incident reports and classify their severity...",
  "tools": ["bedrock"],
  "output_schema": {
    "severity_score": "number",
    "reasoning": "string",
    "urgency": "string",
    "estimated_response_time": "string"
  },
  "version": 1,
  "created_at": 1729425296,
  "updated_at": 1729425296,
  "created_by": "user-123",
  "is_builtin": false
}
```

**Save Agent ID:**

```bash
export CUSTOM_AGENT_ID="agent-xyz789"  # Replace with actual ID from response
echo "Created agent: $CUSTOM_AGENT_ID"
```

**What This Demonstrates:**
- Custom agent creation with specialized prompts
- Flexible output schema definition (4 fields)
- Integration with AWS Bedrock for LLM capabilities

**Timing:** 1 minute

---

### Step 3: Create Custom Domain (1 minute)

**Objective:** Create a custom domain that uses the new severity classifier agent

**curl Command:**

```bash
curl -X POST "$API_URL/config" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"domain_template\",
    \"config\": {
      \"template_name\": \"Priority Incidents\",
      \"domain_id\": \"priority_incidents\",
      \"description\": \"Incident tracking with automated severity classification and priority scoring\",
      \"ingest_agent_ids\": [\"geo_agent\", \"temporal_agent\", \"entity_agent\", \"$CUSTOM_AGENT_ID\"],
      \"query_agent_ids\": [\"when_agent\", \"where_agent\", \"what_agent\", \"why_agent\"]
    }
  }"
```

**Expected Response (201 Created):**

```json
{
  "tenant_id": "tenant-abc123",
  "config_key": "domain_template#template-456",
  "config_type": "domain_template",
  "template_id": "template-456",
  "template_name": "Priority Incidents",
  "domain_id": "priority_incidents",
  "description": "Incident tracking with automated severity classification...",
  "agent_configs": [
    {
      "agent_id": "geo_agent",
      "agent_name": "Geo Agent",
      "is_builtin": true
    },
    {
      "agent_id": "temporal_agent",
      "agent_name": "Temporal Agent",
      "is_builtin": true
    },
    {
      "agent_id": "entity_agent",
      "agent_name": "Entity Agent",
      "is_builtin": true
    },
    {
      "agent_id": "agent-xyz789",
      "agent_name": "Severity Classifier",
      "is_builtin": false
    }
  ],
  "version": 1,
  "created_at": 1729425296,
  "updated_at": 1729425296,
  "created_by": "user-123",
  "is_builtin": false
}
```

**Save Domain ID:**

```bash
export CUSTOM_DOMAIN_ID="priority_incidents"
echo "Created domain: $CUSTOM_DOMAIN_ID"
```

**What This Demonstrates:**
- Custom domain creation with mixed built-in and custom agents
- Agent pipeline configuration (4 ingestion agents, 4 query agents)
- Domain-specific processing workflows

**Timing:** 1 minute

---

### Step 4: Submit Report (2 minutes)

**Objective:** Submit an incident report and observe real-time agent processing

**curl Command:**

```bash
curl -X POST "$API_URL/ingest" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$CUSTOM_DOMAIN_ID\",
    \"text\": \"Major water main break on Oak Street between 5th and 6th Avenue. Water is flooding the street and several basements. Multiple residents are affected and the road is completely impassable. This happened around 3 AM this morning and is getting worse.\",
    \"metadata\": {
      \"source\": \"demo_script\",
      \"priority\": \"critical\"
    }
  }"
```

**Expected Response (202 Accepted):**

```json
{
  "job_id": "job-abc-123-def-456",
  "status": "processing",
  "message": "Report submitted successfully",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "estimated_completion_seconds": 30
}
```

**Save Job ID:**

```bash
export INGEST_JOB_ID="job-abc-123-def-456"  # Replace with actual ID from response
echo "Report submitted with job_id: $INGEST_JOB_ID"
```

**Real-time Status Updates:**

While the report is processing, the system publishes real-time status updates via AppSync WebSocket. The processing flow looks like this:

```
1. loading_agents
   → "Loading agent configuration for domain: priority_incidents"

2. invoking_geo_agent
   → "Invoking geo_agent"
   → "Calling location service for geocoding"
   → "geo_agent completed with confidence: 0.95"

3. invoking_temporal_agent
   → "Invoking temporal_agent"
   → "temporal_agent completed with confidence: 0.92"

4. invoking_entity_agent
   → "Invoking entity_agent"
   → "Calling comprehend for entity extraction"
   → "entity_agent completed with confidence: 0.88"

5. invoking_severity_classifier
   → "Invoking Severity Classifier"
   → "Calling bedrock for severity analysis"
   → "Severity Classifier completed with confidence: 0.94"

6. validating
   → "Validating agent outputs"

7. complete
   → "Processing complete"
```

**Wait for Processing:**

```bash
echo "Waiting 15 seconds for processing to complete..."
sleep 15
```

**What This Demonstrates:**
- Asynchronous report ingestion
- Multi-agent pipeline execution (4 agents in sequence)
- Real-time status updates during processing
- Automatic extraction of location, time, entities, and severity
- Structured data generation from unstructured text

**Timing:** 2 minutes (including wait time)

---

### Step 5: Ask Question (2 minutes)

**Objective:** Submit a natural language query and get AI-generated insights

**curl Command:**

```bash
curl -X POST "$API_URL/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$CUSTOM_DOMAIN_ID\",
    \"question\": \"What are the most critical incidents that need immediate attention? Where are they located and what is their severity?\",
    \"options\": {
      \"include_visualizations\": true,
      \"max_results\": 10
    }
  }"
```

**Expected Response (202 Accepted):**

```json
{
  "job_id": "job-query-789-xyz-012",
  "status": "processing",
  "message": "Query submitted successfully",
  "timestamp": "2025-10-20T12:35:42.123Z",
  "estimated_completion_seconds": 45
}
```

**Save Job ID:**

```bash
export QUERY_JOB_ID="job-query-789-xyz-012"  # Replace with actual ID from response
echo "Query submitted with job_id: $QUERY_JOB_ID"
```

**Real-time Status Updates:**

The query processing flow involves multiple interrogative agents working in parallel:

```
1. loading_agents
   → "Loading query agents for domain: priority_incidents"

2. Parallel Agent Execution:
   - invoking_when_agent
     → "Analyzing temporal patterns"
     → "when_agent completed with confidence: 0.87"
   
   - invoking_where_agent
     → "Analyzing spatial distribution"
     → "where_agent completed with confidence: 0.91"
   
   - invoking_what_agent
     → "Analyzing incident categories and severity"
     → "what_agent completed with confidence: 0.93"
   
   - invoking_why_agent
     → "Analyzing causal factors"
     → "why_agent completed with confidence: 0.85"

3. synthesizing
   → "Synthesizing query results from 4 agents"

4. complete
   → "Query processing complete"
```

**Wait for Processing:**

```bash
echo "Waiting 20 seconds for query processing to complete..."
sleep 20
```

**Expected Query Results Structure:**

```json
{
  "job_id": "job-query-789-xyz-012",
  "status": "complete",
  "question": "What are the most critical incidents that need immediate attention?",
  "domain_id": "priority_incidents",
  "agent_results": {
    "what_agent": {
      "answer": "The most critical incident is a major water main break with severity score 9/10...",
      "confidence": 0.93,
      "data": {
        "critical_incidents": [
          {
            "incident_id": "incident-123",
            "severity_score": 9,
            "category": "infrastructure",
            "urgency": "critical"
          }
        ]
      }
    },
    "where_agent": {
      "answer": "The critical incident is located on Oak Street between 5th and 6th Avenue...",
      "confidence": 0.91,
      "data": {
        "location": {
          "address": "Oak Street",
          "coordinates": {"lat": 40.7128, "lon": -74.0060}
        }
      }
    },
    "when_agent": {
      "answer": "The incident occurred at approximately 3 AM this morning...",
      "confidence": 0.87
    },
    "why_agent": {
      "answer": "The severity is high due to multiple affected residents, road closure, and flooding...",
      "confidence": 0.85
    }
  },
  "summary": "The most critical incident requiring immediate attention is a major water main break on Oak Street (severity: 9/10). It occurred at 3 AM, is causing flooding and road closure, and affects multiple residents. The location is Oak Street between 5th and 6th Avenue. Immediate response is needed due to the escalating nature of the flooding.",
  "confidence_score": 0.89,
  "processing_time_seconds": 18.5
}
```

**What This Demonstrates:**
- Natural language query processing
- Multi-agent interrogative pipeline (4 agents in parallel)
- AI-generated synthesis and summary
- Confidence scoring for each agent
- Structured insights from unstructured questions

**Timing:** 2 minutes (including wait time)

---

### Step 6: Retrieve Data (1 minute)

**Objective:** Retrieve structured incident data with filtering

**curl Command (Basic Retrieval):**

```bash
curl -X GET "$API_URL/data?type=retrieval&filters=%7B%22domain_id%22%3A%22$CUSTOM_DOMAIN_ID%22%2C%22limit%22%3A10%7D" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Or with jq for better formatting:**

```bash
FILTERS=$(echo "{\"domain_id\":\"$CUSTOM_DOMAIN_ID\",\"limit\":10}" | jq -r @uri)
curl -X GET "$API_URL/data?type=retrieval&filters=$FILTERS" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" | jq
```

**Expected Response (200 OK):**

```json
{
  "status": "success",
  "data": [
    {
      "id": "incident-123",
      "tenant_id": "tenant-abc123",
      "domain_id": "priority_incidents",
      "raw_text": "Major water main break on Oak Street between 5th and 6th Avenue...",
      "structured_data": {
        "location": {
          "address": "Oak Street between 5th and 6th Avenue",
          "coordinates": {
            "lat": 40.7128,
            "lon": -74.0060
          },
          "confidence": 0.95
        },
        "timestamp": {
          "extracted_time": "2025-10-20T03:00:00Z",
          "confidence": 0.92,
          "time_reference": "3 AM this morning"
        },
        "entities": {
          "locations": ["Oak Street", "5th Avenue", "6th Avenue"],
          "affected_parties": ["residents"],
          "sentiment": "urgent",
          "confidence": 0.88
        },
        "severity_score": 9,
        "reasoning": "Critical infrastructure failure affecting multiple residents with escalating flooding",
        "urgency": "critical",
        "estimated_response_time": "immediate - within 1 hour"
      },
      "confidence_scores": {
        "geo_agent": 0.95,
        "temporal_agent": 0.92,
        "entity_agent": 0.88,
        "severity_classifier": 0.94
      },
      "created_at": "2025-10-20T12:34:56.789Z",
      "updated_at": "2025-10-20T12:35:12.456Z",
      "created_by": "user-123"
    }
  ],
  "count": 1,
  "limit": 10,
  "offset": 0
}
```

**Advanced Filtering Examples:**

```bash
# Filter by severity (high priority incidents)
FILTERS='{"domain_id":"'$CUSTOM_DOMAIN_ID'","custom_filters":{"severity_score":{"$gte":7}},"limit":5}'
curl -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq

# Filter by date range
FILTERS='{"domain_id":"'$CUSTOM_DOMAIN_ID'","date_from":"2025-10-20T00:00:00Z","date_to":"2025-10-20T23:59:59Z"}'
curl -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq

# Filter by location
FILTERS='{"domain_id":"'$CUSTOM_DOMAIN_ID'","location":"Oak Street"}'
curl -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq
```

**What This Demonstrates:**
- Structured data retrieval with filtering
- Rich metadata from multi-agent processing
- Confidence scores for each agent's output
- Flexible query parameters for different use cases
- Complete incident lifecycle (submission → processing → retrieval)

**Timing:** 1 minute

---

## End-to-End Workflow

This section combines all steps into a complete workflow that demonstrates the full system capabilities.

**Complete Demo Script (9 minutes):**

```bash
#!/bin/bash

# Configuration
export API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
export JWT_TOKEN="your-jwt-token-here"

echo "========================================="
echo "Multi-Agent Orchestration System Demo"
echo "========================================="
echo ""

# Step 1: Verify Authentication (30 seconds)
echo "Step 1: Verifying authentication..."
AUTH_TEST=$(curl -s -X GET "$API_URL/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json")

if echo "$AUTH_TEST" | grep -q "configs"; then
  echo "✓ Authentication successful"
else
  echo "✗ Authentication failed"
  exit 1
fi
echo ""

# Step 2: Create Custom Agent (1 minute)
echo "Step 2: Creating custom Severity Classifier agent..."
AGENT_RESPONSE=$(curl -s -X POST "$API_URL/config" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Severity Classifier",
      "agent_type": "custom",
      "system_prompt": "Analyze incident reports and classify their severity on a scale of 1-10. Consider public safety impact, urgency, and escalation potential. Provide severity score, reasoning, urgency level, and estimated response time.",
      "tools": ["bedrock"],
      "output_schema": {
        "severity_score": "number",
        "reasoning": "string",
        "urgency": "string",
        "estimated_response_time": "string"
      }
    }
  }')

CUSTOM_AGENT_ID=$(echo "$AGENT_RESPONSE" | jq -r '.agent_id')
echo "✓ Created agent: $CUSTOM_AGENT_ID"
echo ""

# Step 3: Create Custom Domain (1 minute)
echo "Step 3: Creating custom Priority Incidents domain..."
DOMAIN_RESPONSE=$(curl -s -X POST "$API_URL/config" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"domain_template\",
    \"config\": {
      \"template_name\": \"Priority Incidents\",
      \"domain_id\": \"priority_incidents\",
      \"description\": \"Incident tracking with automated severity classification\",
      \"ingest_agent_ids\": [\"geo_agent\", \"temporal_agent\", \"entity_agent\", \"$CUSTOM_AGENT_ID\"],
      \"query_agent_ids\": [\"when_agent\", \"where_agent\", \"what_agent\", \"why_agent\"]
    }
  }")

CUSTOM_DOMAIN_ID=$(echo "$DOMAIN_RESPONSE" | jq -r '.domain_id')
echo "✓ Created domain: $CUSTOM_DOMAIN_ID"
echo ""

# Step 4: Submit Report (2 minutes)
echo "Step 4: Submitting incident report..."
INGEST_RESPONSE=$(curl -s -X POST "$API_URL/ingest" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$CUSTOM_DOMAIN_ID\",
    \"text\": \"Major water main break on Oak Street between 5th and 6th Avenue. Water is flooding the street and several basements. Multiple residents are affected and the road is completely impassable. This happened around 3 AM this morning and is getting worse.\",
    \"metadata\": {
      \"source\": \"demo_script\",
      \"priority\": \"critical\"
    }
  }")

INGEST_JOB_ID=$(echo "$INGEST_RESPONSE" | jq -r '.job_id')
echo "✓ Report submitted with job_id: $INGEST_JOB_ID"
echo "  Waiting 15 seconds for processing..."
sleep 15
echo ""

# Step 5: Ask Question (2 minutes)
echo "Step 5: Submitting query..."
QUERY_RESPONSE=$(curl -s -X POST "$API_URL/query" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"domain_id\": \"$CUSTOM_DOMAIN_ID\",
    \"question\": \"What are the most critical incidents that need immediate attention? Where are they located and what is their severity?\",
    \"options\": {
      \"include_visualizations\": true,
      \"max_results\": 10
    }
  }")

QUERY_JOB_ID=$(echo "$QUERY_RESPONSE" | jq -r '.job_id')
echo "✓ Query submitted with job_id: $QUERY_JOB_ID"
echo "  Waiting 20 seconds for query processing..."
sleep 20
echo ""

# Step 6: Retrieve Data (1 minute)
echo "Step 6: Retrieving incident data..."
FILTERS="{\"domain_id\":\"$CUSTOM_DOMAIN_ID\",\"limit\":10}"
DATA_RESPONSE=$(curl -s -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json")

INCIDENT_COUNT=$(echo "$DATA_RESPONSE" | jq -r '.count')
echo "✓ Retrieved $INCIDENT_COUNT incident(s)"

if [ "$INCIDENT_COUNT" -gt 0 ]; then
  echo ""
  echo "Sample Incident Data:"
  echo "$DATA_RESPONSE" | jq '.data[0] | {
    id: .id,
    text: .raw_text,
    location: .structured_data.location.address,
    severity: .structured_data.severity_score,
    urgency: .structured_data.urgency,
    confidence_scores: .confidence_scores
  }'
fi
echo ""

echo "========================================="
echo "Demo Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "- Created custom agent: $CUSTOM_AGENT_ID"
echo "- Created custom domain: $CUSTOM_DOMAIN_ID"
echo "- Submitted report: $INGEST_JOB_ID"
echo "- Submitted query: $QUERY_JOB_ID"
echo "- Retrieved $INCIDENT_COUNT incident(s)"
echo ""
echo "Key Capabilities Demonstrated:"
echo "✓ Custom agent creation with specialized prompts"
echo "✓ Domain configuration with agent pipelines"
echo "✓ Asynchronous report ingestion"
echo "✓ Multi-agent processing (4 ingestion agents)"
echo "✓ Natural language query processing"
echo "✓ AI-generated insights and summaries"
echo "✓ Structured data extraction and retrieval"
echo ""
```

**Save and Run:**

```bash
# Save the script
cat > demo.sh << 'EOF'
[paste the script above]
EOF

# Make it executable
chmod +x demo.sh

# Run the demo
./demo.sh
```

**What the Complete Workflow Demonstrates:**

1. **Extensibility**: Custom agents can be created with specialized capabilities
2. **Flexibility**: Domains can mix built-in and custom agents
3. **Automation**: Multi-agent pipelines process data automatically
4. **Intelligence**: AI-powered extraction, classification, and analysis
5. **Real-time**: Asynchronous processing with status updates
6. **Scalability**: Handles complex workflows with multiple agents
7. **Usability**: Simple REST API for all operations

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Invalid JWT Token

**Symptoms:**
```json
{
  "error": "Unauthorized: Invalid JWT token",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "UNAUTHORIZED"
}
```

**Solutions:**

1. **Token Expired**: JWT tokens expire after 1 hour. Get a new token:
   ```bash
   export JWT_TOKEN=$(aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id 6gobbpage9af3nd7ahm3lchkct \
     --auth-parameters USERNAME=your-username,PASSWORD=your-password \
     --region us-east-1 \
     --query 'AuthenticationResult.IdToken' \
     --output text)
   ```

2. **Wrong Token Type**: Make sure you're using the `IdToken`, not `AccessToken`:
   ```bash
   # Correct
   export JWT_TOKEN="eyJraWQiOiJ..."  # IdToken
   
   # Incorrect
   export JWT_TOKEN="eyJraWQiOiJ..."  # AccessToken
   ```

3. **Missing Authorization Header**: Ensure the header is included:
   ```bash
   curl -X GET "$API_URL/config?type=agent" \
     -H "Authorization: Bearer $JWT_TOKEN"  # Don't forget this!
   ```

#### Issue 2: Domain Not Found

**Symptoms:**
```json
{
  "error": "Domain not found: priority_incidents",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "NOT_FOUND"
}
```

**Solutions:**

1. **Domain Not Created Yet**: Make sure you completed Step 3 (Create Domain)

2. **Wrong Domain ID**: Verify the domain ID matches what you created:
   ```bash
   # List all domains
   curl -X GET "$API_URL/config?type=domain_template" \
     -H "Authorization: Bearer $JWT_TOKEN" | jq '.configs[] | {domain_id, template_name}'
   ```

3. **Tenant Isolation**: Domains are tenant-specific. Make sure you're using the same JWT token (tenant) that created the domain.

#### Issue 3: Agent Not Found

**Symptoms:**
```json
{
  "error": "Agent not found: agent-xyz789",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "NOT_FOUND"
}
```

**Solutions:**

1. **Agent Not Created Yet**: Make sure you completed Step 2 (Create Agent)

2. **Wrong Agent ID**: Verify the agent ID from the creation response:
   ```bash
   # List all agents
   curl -X GET "$API_URL/config?type=agent" \
     -H "Authorization: Bearer $JWT_TOKEN" | jq '.configs[] | {agent_id, agent_name}'
   ```

3. **Copy-Paste Error**: Double-check that you saved the correct agent ID:
   ```bash
   echo "Agent ID: $CUSTOM_AGENT_ID"
   ```

#### Issue 4: Network Timeout

**Symptoms:**
```
curl: (28) Operation timed out after 30000 milliseconds
```

**Solutions:**

1. **Increase Timeout**: Add timeout parameter to curl:
   ```bash
   curl --max-time 60 -X POST "$API_URL/ingest" ...
   ```

2. **Check API Availability**: Verify the API endpoint is accessible:
   ```bash
   curl -I "$API_URL/config?type=agent" \
     -H "Authorization: Bearer $JWT_TOKEN"
   ```

3. **Network Issues**: Check your internet connection and firewall settings

#### Issue 5: Processing Takes Too Long

**Symptoms:**
- Report or query submitted but no results after waiting

**Solutions:**

1. **Check Job Status**: The system is asynchronous. Processing can take 15-45 seconds:
   ```bash
   # For production, use WebSocket subscription to get real-time updates
   # For demo, wait 15-20 seconds and then retrieve data
   sleep 20
   ```

2. **Verify Processing Completed**: Check if data was saved:
   ```bash
   FILTERS="{\"domain_id\":\"$CUSTOM_DOMAIN_ID\",\"limit\":1}"
   curl -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
     -H "Authorization: Bearer $JWT_TOKEN" | jq '.count'
   ```

3. **Check CloudWatch Logs**: For detailed debugging, check AWS CloudWatch logs:
   - Log Group: `/aws/lambda/orchestration-*`
   - Look for errors or exceptions during processing

#### Issue 6: Validation Errors

**Symptoms:**
```json
{
  "error": "output_schema cannot have more than 5 keys. Found 7 keys",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "TOO_MANY"
}
```

**Solutions:**

1. **Review Validation Rules**: Check the [API Reference](API_REFERENCE.md#validation-rules) for field constraints

2. **Common Validation Issues**:
   - Agent name: 1-100 characters, alphanumeric + spaces
   - System prompt: 1-2000 characters
   - Output schema: Maximum 5 keys
   - Domain ID: Lowercase alphanumeric + underscores only
   - Report text: 1-10,000 characters
   - Images: Maximum 5 images, 5MB each

3. **Fix and Retry**: Adjust your request to meet the validation rules

#### Issue 7: Rate Limit Exceeded

**Symptoms:**
```json
{
  "error": "Rate limit exceeded",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "error_code": "RATE_LIMIT"
}
```

**Solutions:**

1. **Wait and Retry**: Rate limits reset every minute:
   ```bash
   echo "Rate limit exceeded. Waiting 60 seconds..."
   sleep 60
   ```

2. **Rate Limits**:
   - Config API: 100 requests/minute
   - Data API: 200 requests/minute
   - Ingest API: 50 requests/minute
   - Query API: 50 requests/minute

3. **Batch Operations**: If you need to submit multiple reports, add delays:
   ```bash
   for i in {1..10}; do
     curl -X POST "$API_URL/ingest" ...
     sleep 2  # 2 second delay between requests
   done
   ```

### Verification Steps

**1. Verify Deployment:**

```bash
# Check API is accessible
curl -I "$API_URL/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected: HTTP/1.1 200 OK
```

**2. Verify Authentication:**

```bash
# Decode JWT token to check claims
echo "$JWT_TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq

# Should include: tenant_id, user_id, exp
```

**3. Verify Agent Creation:**

```bash
# List all agents including custom ones
curl -X GET "$API_URL/config?type=agent" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.configs[] | select(.is_builtin == false)'
```

**4. Verify Domain Creation:**

```bash
# List all domains including custom ones
curl -X GET "$API_URL/config?type=domain_template" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.configs[] | select(.is_builtin == false)'
```

**5. Verify Data Ingestion:**

```bash
# Check if incidents were created
FILTERS='{"limit":1}'
curl -X GET "$API_URL/data?type=retrieval&filters=$(echo $FILTERS | jq -r @uri)" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.count'

# Should return count > 0 if reports were processed
```

### Getting Help

If you encounter issues not covered here:

1. **Check CloudWatch Logs**: 
   - Navigate to AWS CloudWatch Console
   - Look for log groups: `/aws/lambda/*`
   - Search for error messages or stack traces

2. **Review API Reference**: 
   - See [API_REFERENCE.md](API_REFERENCE.md) for detailed endpoint documentation
   - Check validation rules and error codes

3. **Check System Status**:
   - Verify all AWS services are operational
   - Check RDS database is running
   - Verify Lambda functions are deployed

4. **Contact Support**:
   - Email: api-support@example.com
   - Include: JWT token (first 20 chars), request details, error messages

---

**End of Demo Script**
