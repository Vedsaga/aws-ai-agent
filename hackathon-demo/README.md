# DomainFlow Hackathon Demo

**Clean, minimal setup for 30-minute demo**

No complex infrastructure. No authentication. Just 3 agent classes, DynamoDB, and Lambda.

## What This Is

A stripped-down version of DomainFlow focused on the core concept: **AI agents as the data interface**.

Instead of building custom APIs for every feature, you configure agents with prompts. Same infrastructure, infinite use cases.

## Architecture

```
User Input → Lambda Orchestrator (Nova Pro) → Multiple Agents (Nova Lite) → DynamoDB
                ↓                                      ↓
         EventBridge (real-time status)    Verifier (Nova Pro)
                ↓
         Frontend (dark mode + map + chat)
```

**Components:**
- DynamoDB: Single table `civic-reports`
- Lambda: Single function with orchestrator + multiple agents
- Bedrock: Nova Pro (orchestrator/verifier), Nova Lite (agents)
- API Gateway: No auth (demo only)
- EventBridge: Real-time status events
- Frontend: Dark mode HTML + Mapbox dark-v11

## 3 Meta Agent Classes

### 1. Data-Ingestion (CREATE)
Extracts structured data using multiple specialized agents.

**Input:** "Street light broken near post office"

**Orchestrator (Nova Pro):** Plans execution → Run Geo, Entity, Severity agents

**Agents (Nova Lite):**
- Geo Agent: Extracts "near post office" (confidence: 0.6 - LOW!)
- Entity Agent: Identifies "street light" (confidence: 0.95)
- Severity Agent: Determines "high" (confidence: 0.9)

**Verifier (Nova Pro):** Checks confidence → Geo is too low!

**Agent asks:** "Can you confirm the exact street address?"

**User:** "Yes, 123 Main Street"

**Re-run agents → Verifier approves → Save:** `{location: "123 Main St", geo: [-74, 40.7], entity: "streetlight", severity: "high"}`

### 2. Data-Query (READ)
Answers questions using multiple analysis agents.

**Input:** "Show me all high-priority potholes"

**Orchestrator (Nova Pro):** Plans → Run What, Where, When agents

**Agents (Nova Lite):**
- What Agent: Analyzes "potholes" → entity filter (confidence: 0.92)
- Where Agent: No location specified → no filter (confidence: 0.88)
- When Agent: No time specified → no filter (confidence: 0.85)

**Database:** Queries with combined filters → 5 results

**Verifier (Nova Pro):** Synthesizes answer from all agents

**Output:** "Found 5 high-priority pothole reports across the city. Most are concentrated in downtown area." + map data

### 3. Data-Management (UPDATE)
Updates existing reports based on commands.

**Input:** "Assign this to Team B, due in 48 hours"

**Agent:**
1. Parses action: assign + set due date
2. Extracts: assignee="Team B", due_at=+48h
3. Updates DynamoDB

**Output:** "✅ Assigned to Team B, due October 25, 2025"

## Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.11+
- Bedrock access (Claude 3.5 Sonnet)

### Deploy (10 min)

```bash
cd hackathon-demo
./deploy.sh
```

### Test (5 min)

```bash
# Shell script
./test-api.sh

# Or Python
python3 test-client.py
```

### Frontend (5 min)

1. Get Mapbox token: https://account.mapbox.com/access-tokens/
2. Edit `frontend/index.html`:
   - Replace `YOUR_API_ENDPOINT_HERE`
   - Replace `YOUR_MAPBOX_TOKEN`
3. Open in browser

## Demo Script

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the full 5-minute presentation.

**TL;DR:**
1. Report issue with vague location → agent asks for clarification
2. Confirm location → data saved, appears on map
3. Query "show high-priority issues" → map filters
4. Assign task → data updates in real-time

## File Structure

```
hackathon-demo/
├── README.md                 # This file
├── QUICK_START.md           # Detailed setup guide
├── DEMO_SCRIPT.md           # Presentation script
├── deploy.sh                # One-command deployment
├── test-api.sh              # Shell test script
├── test-client.py           # Python test client
├── agent-definitions.json   # Agent prompts
├── cdk/                     # Infrastructure
│   ├── app.py              # CDK stack
│   ├── cdk.json
│   └── requirements.txt
├── lambda/                  # Backend
│   ├── orchestrator.py     # Main Lambda
│   └── requirements.txt
└── frontend/                # UI
    └── index.html          # Single-page app
```

## Key Differences from Main Project

| Feature | Main Project | Hackathon Demo |
|---------|-------------|----------------|
| Auth | Cognito + JWT | None |
| Database | RDS + DynamoDB | DynamoDB only |
| Agents | 12+ builtin | 3 meta classes |
| Orchestration | Step Functions | Single Lambda |
| Real-time | WebSocket | EventBridge |
| Frontend | Next.js | Vanilla HTML |
| Deployment | Multi-stack CDK | Single stack |

## What's Missing (Intentionally)

- Authentication (would use Cognito)
- Multi-tenancy (would use tenant_id partition)
- Agent chaining (would use Step Functions)
- Verification agents (would validate outputs)
- File uploads (would use S3 presigned URLs)
- Geocoding (would use AWS Location Service)
- Search (would use OpenSearch)
- Caching (would use ElastiCache)

## Why This Works for Demo

**Focus on the concept:** AI agents as data interface

**Not distracted by:** Auth flows, tenant isolation, complex orchestration

**Shows the value:** Same infrastructure, different prompts = different apps

## Extending This

Want to add a new domain? Just change the agent prompts:

**Hospital domain:**
```json
{
  "data-ingestion": {
    "system_prompt": "Extract patient symptoms, severity, department..."
  }
}
```

**Logistics domain:**
```json
{
  "data-ingestion": {
    "system_prompt": "Extract shipment details, destination, priority..."
  }
}
```

Same code. Different prompts. New application.

## Clean Up

```bash
cd cdk
cdk destroy
```

## Questions?

- Architecture: See main project `/diagrams`
- Full system: See main project `/infrastructure`
- API docs: See main project `API_DOCUMENTATION.md`
