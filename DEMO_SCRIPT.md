# Hackathon Demo Script

## Overview

This script outlines the steps for a compelling 3-minute demo of the Multi-Agent Orchestration System. Due to a backend authentication issue, this script uses `curl` commands with a placeholder `JWT_TOKEN` and simulated JSON responses to showcase the intended end-to-end workflow.

**Presenter:** [Your Name]
**Time Limit:** 3 minutes

---

### Step 1: Introduction (30 seconds)

**Presenter:** "Our project is a multi-agent orchestration system that allows users to create custom AI agents for data ingestion and querying. Today, we'll demonstrate how a city official can use our platform to process and analyze a citizen's report about a pothole."

**(Show the web application's main dashboard)**

---

### Step 2: Creating a Custom Agent (45 seconds)

**Presenter:** "First, let's create a custom agent to extract the priority level from a citizen's report. We'll define the agent's name, system prompt, and the expected output schema."

**(Show the 'Create Agent' form in the web app, pre-filled with the following data)**

**Simulated API Call:**

```bash
# DEMO: Create a custom agent to determine the priority of a citizen's report.
curl -X POST https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Priority Assessment Agent",
      "agent_type": "ingestion",
      "system_prompt": "You are an AI assistant for a city's public works department. Your task is to analyze citizen reports and determine the priority level. The priority should be one of: Low, Medium, High, or Critical.",
      "tools": ["bedrock"],
      "output_schema": {
        "priority": "string",
        "reasoning": "string"
      }
    }
  }'
```

**Presenter:** "When we submit this, our system creates a new, reusable agent that can be added to any of our data processing workflows."

**Simulated API Response (display in a terminal or a mock-up):**
```json
{
  "status": "success",
  "agent_id": "agent-123-priority-assessment",
  "message": "Agent 'Priority Assessment Agent' created successfully."
}
```
---

### Step 3: Submitting a Report for Ingestion (60 seconds)

**Presenter:** "Now, let's see this in action. A citizen submits a report: 'There's a massive pothole on Main Street, right in front of the hospital entrance. It's been there for a week and is causing traffic delays.' Our system will use a chain of agents, including our new Priority Agent, to process this unstructured text."

**(Show the 'Submit Report' form in the web app)**

**Simulated API Call:**
```bash
# DEMO: Submit a citizen's report for processing.
curl -X POST https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "There''s a massive pothole on Main Street, right in front of the hospital entrance. It''s been there for a week and is causing traffic delays."
  }'
```
**Presenter:** "Our orchestration engine now processes this report through a series of agents: one to identify the location, another to extract the timeline, and our custom agent to assess the priority. Here is the structured data that our system generates:"

**Simulated Final Data (display in the web app or a mock-up):**
```json
{
  "incident_id": "incident-987",
  "original_report": "There's a massive pothole on Main Street...",
  "structured_data": {
    "location": {
      "address": "Main Street",
      "landmark": "Hospital Entrance",
      "geo_coordinates": {
        "latitude": 34.0522,
        "longitude": -118.2437
      }
    },
    "timeline": {
      "reported_on": "2025-10-20",
      "duration": "1 week"
    },
    "priority_assessment": {
      "priority": "Critical",
      "reasoning": "The pothole is large, located at a hospital entrance, and is causing traffic disruptions."
    }
  }
}
```
---

### Step 4: Querying the Data (30 seconds)

**Presenter:** "Finally, a city manager can ask natural language questions to analyze this structured data. For example, 'How many critical issues were reported this week?'"

**(Show the 'Query' interface in the web app)**

**Simulated API Call:**
```bash
# DEMO: Ask a question about the processed data.
curl -X POST https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/query \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "How many critical issues were reported this week?"
  }'
```

**Presenter:** "Our query agent understands the question and provides a direct answer, empowering city officials to make data-driven decisions."

**Simulated API Response (display in the web app):**
```json
{
  "summary": "There have been 14 critical issues reported this week.",
  "data_points": [
    { "incident_id": "incident-987", "priority": "Critical", "location": "Main Street" },
    { "...": "..." }
  ]
}
```
---

### Step 5: Conclusion (15 seconds)

**Presenter:** "Our multi-agent system transforms unstructured data into actionable insights, improving efficiency and responsiveness for any organization. Thank you."

---

## Technical Notes for the Presenter

*   Have the `curl` commands and simulated JSON responses ready in a text editor.
*   Practice the timing to ensure you stay within the 3-minute limit.
*   Be prepared to answer questions about the architecture and the technical challenges you faced (and have a plan to overcome them, as outlined in the `GAP_ANALYSIS.md`).
