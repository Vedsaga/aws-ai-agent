# DomainFlow Hackathon Demo - Quick Start

## 30-Minute Setup

### Prerequisites
- AWS CLI configured
- Python 3.11+
- Node.js (for CDK)
- Mapbox account (free tier)

### Step 1: Deploy Backend (10 min)

```bash
cd hackathon-demo
./deploy.sh
```

This creates:
- DynamoDB table: `civic-reports`
- Lambda: `domainflow-orchestrator`
- API Gateway endpoint (no auth)
- EventBridge bus for real-time status

### Step 2: Get API Endpoint (1 min)

```bash
aws cloudformation describe-stacks \
  --stack-name DomainFlowDemo \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### Step 3: Test API (5 min)

```bash
./test-api.sh
```

### Step 4: Setup Frontend (5 min)

1. Get Mapbox token: https://account.mapbox.com/access-tokens/
2. Edit `frontend/index.html`:
   - Replace `YOUR_API_ENDPOINT_HERE` with your API URL
   - Replace `YOUR_MAPBOX_TOKEN` with your Mapbox token
3. Open `frontend/index.html` in browser

**New UI Features:**
- Dark mode interface with Mapbox dark-v11
- Mode badge in top-right showing current mode
- Real-time agent execution panel showing:
  - Orchestrator planning
  - Individual agent status (Geo, Entity, Severity, etc.)
  - Confidence scores for each agent
  - Verifier validation
- Report counter on map overlay

### Step 5: Demo Script (9 min)

#### Scene 1: Data Ingestion (3 min)

**User:** "Street light broken near the post office"

**Agent:** "Can you confirm the exact street address or intersection?"

**User:** "Yes, 123 Main Street"

**Agent:** "✅ Report saved! ID: abc-123"

*Map updates with new marker*

#### Scene 2: Data Query (3 min)

Switch to Query mode

**User:** "Show me all high-priority issues"

**Agent:** "Found 5 high-priority reports"

*Map shows filtered markers*

**User:** "What's broken on Main Street?"

**Agent:** "Found 3 reports: 2 streetlights, 1 pothole"

#### Scene 3: Data Management (3 min)

Switch to Management mode

**User:** "Assign this report to Team B and make it due in 48 hours"

**Agent:** "✅ Assigned to Team B, due October 25, 2025"

*Map marker updates with assignment info*

## Architecture Highlights

### 3 Meta Agent Classes

1. **Data-Ingestion** (CREATE)
   - Extracts: location, entity, severity
   - Validates: confidence, precision
   - Clarifies: vague inputs

2. **Data-Query** (READ)
   - Parses: natural language queries
   - Filters: by location, entity, severity, date
   - Visualizes: GeoJSON for maps

3. **Data-Management** (UPDATE)
   - Assigns: tasks to teams
   - Updates: status, priority, due dates
   - Tracks: change history

### Real-Time Status

EventBridge events emitted during agent execution:
- `running`: Agent started
- `clarification`: Needs user input
- `completed`: Task finished
- `error`: Something failed

### No Auth (Demo Only)

API is open for quick testing. In production:
- Add Cognito authorizer
- Implement tenant isolation
- Add rate limiting

## Troubleshooting

### Lambda timeout
Increase timeout in `cdk/app.py` (currently 60s)

### Bedrock access denied
Ensure your AWS account has Bedrock enabled in us-east-1

### Map not loading
Check Mapbox token and browser console

### No reports showing
Run `./test-api.sh` to seed some data

## Clean Up

```bash
cd cdk
cdk destroy
```

## Next Steps

- Add authentication (Cognito)
- Implement WebSocket for real-time updates
- Add more agent types (verification, routing)
- Integrate with AWS Location Service for geocoding
- Add file upload for images
- Implement agent chaining for complex workflows
