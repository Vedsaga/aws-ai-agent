# Client Integration Guide

## Deployment Outputs for Frontend Integration

After running `bash scripts/full-deploy.sh`, you'll receive all necessary information for client-side integration.

---

## Stage 7: Retrieve Deployment Information

### What It Does

Stage 7 retrieves all deployment outputs from CloudFormation and:
1. ✅ Extracts API endpoint URL
2. ✅ Retrieves API key ID
3. ✅ Gets actual API key value (secret)
4. ✅ Saves credentials to `.env.local`
5. ✅ Displays all outputs in formatted view

### Outputs Provided

```
═══════════════════════════════════════════════════════════
                    DEPLOYMENT OUTPUTS
═══════════════════════════════════════════════════════════

API Endpoint:
  https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/

API Key ID:
  yz7txbqii5

API Key Value:
  xxxxxxxxxxxxxxxxxxxxxxxxxx

DynamoDB Table:
  CommandCenterBackend-Dev-MasterEventTimeline

Bedrock Agent ID:
  2SCAO1Z7OP

Bedrock Agent Alias ID:
  RFQMVJPVCE

═══════════════════════════════════════════════════════════
```

### What Gets Saved

All credentials are automatically saved to `.env.local`:

```bash
# command-center-backend/.env.local (auto-generated)
API_ENDPOINT=https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
TABLE_NAME=CommandCenterBackend-Dev-MasterEventTimeline
AGENT_ID=2SCAO1Z7OP
AGENT_ALIAS_ID=RFQMVJPVCE
AWS_REGION=us-east-1
```

---

## Stage 8: Populate Database

### What It Does

Stage 8 populates the DynamoDB table with simulation data:
1. ✅ Generates 7 days of earthquake response events
2. ✅ Inserts ~500-1000 events
3. ✅ Verifies data insertion
4. ✅ Reports item count

### Output

```
[8/8] Populating database with simulation data...
This may take 2-3 minutes...

Generating simulation data...
✓ Generated 847 events

Inserting events into DynamoDB...
✓ Inserted 847 events

✓ Database populated successfully
  Total items in database: 847
```

### Can Be Skipped

If you already have data or want to populate later:

```bash
bash scripts/full-deploy.sh --skip-populate
```

Then populate manually:
```bash
npm run populate-db
```

---

## Complete Deployment Outputs

### From Your Deployment

Based on your output, here's what was deployed:

| Output | Value | Purpose |
|--------|-------|---------|
| **API Endpoint** | `https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/` | Base URL for all API calls |
| **API Key ID** | `yz7txbqii5` | Reference ID (not the secret) |
| **API Key Value** | (retrieved in Stage 7) | Secret key for authentication |
| **Table Name** | `CommandCenterBackend-Dev-MasterEventTimeline` | DynamoDB table name |
| **Agent ID** | `2SCAO1Z7OP` | Bedrock Agent identifier |
| **Agent Alias ID** | `RFQMVJPVCE` | Agent alias for stable endpoint |

### Additional Outputs

Your deployment also created:

- **Lambda Functions:**
  - `CommandCenterBackend-Dev-UpdatesHandler`
  - `CommandCenterBackend-Dev-QueryHandler`
  - `CommandCenterBackend-Dev-ActionHandler`
  - `CommandCenterBackend-Dev-DatabaseQueryTool`

- **IAM Roles:**
  - `CommandCenterBackend-Dev-UpdatesLambdaRole`
  - `CommandCenterBackend-Dev-QueryLambdaRole`
  - `CommandCenterBackend-Dev-ActionLambdaRole`
  - `CommandCenterBackend-Dev-ToolLambdaRole`

- **Monitoring:**
  - CloudWatch Dashboard: `CommandCenterBackend-Dev-Monitoring`
  - SNS Topic: `CommandCenterBackend-Dev-CostAlert`
  - Cost Threshold: $50 USD

---

## Frontend Integration

### Step 1: Copy Credentials

From `command-center-backend/.env.local`:

```bash
API_ENDPOINT=https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 2: Create Frontend .env.local

In your `command-center-dashboard` directory:

```bash
# command-center-dashboard/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note:** Use `NEXT_PUBLIC_` prefix for Next.js environment variables that need to be accessible in the browser.

### Step 3: Test API Connection

```bash
# From command-center-backend directory
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"

# Test query endpoint
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the most urgent needs?"}'
```

---

## API Endpoints

### 1. GET /data/updates

**Purpose:** Get real-time event updates

**URL:** `${API_ENDPOINT}data/updates`

**Query Parameters:**
- `since` (required): ISO 8601 timestamp (e.g., `2023-02-06T00:00:00Z`)
- `domain` (optional): Filter by domain (MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION)

**Headers:**
```
x-api-key: YOUR_API_KEY
```

**Example:**
```javascript
const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z`,
  {
    headers: {
      'x-api-key': process.env.NEXT_PUBLIC_API_KEY
    }
  }
);
const data = await response.json();
```

**Response:**
```json
{
  "events": [
    {
      "eventId": "evt_001",
      "timestamp": "2023-02-06T08:15:00Z",
      "domain": "MEDICAL",
      "severity": "CRITICAL",
      "summary": "Building collapse with 15 people trapped",
      "geojson": {
        "type": "Point",
        "coordinates": [37.12, 37.15]
      }
    }
  ],
  "count": 1,
  "lastUpdate": "2023-02-06T08:15:00Z"
}
```

---

### 2. POST /agent/query

**Purpose:** Natural language queries to AI agent

**URL:** `${API_ENDPOINT}agent/query`

**Headers:**
```
x-api-key: YOUR_API_KEY
Content-Type: application/json
```

**Body:**
```json
{
  "text": "What are the most urgent needs right now?"
}
```

**Example:**
```javascript
const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_ENDPOINT}agent/query`,
  {
    method: 'POST',
    headers: {
      'x-api-key': process.env.NEXT_PUBLIC_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: 'What are the most urgent needs?'
    })
  }
);
const data = await response.json();
```

**Response:**
```json
{
  "chatResponse": "There are 12 critical medical incidents...",
  "mapAction": "REPLACE",
  "mapLayers": [
    {
      "type": "FeatureCollection",
      "features": [...]
    }
  ],
  "viewState": {
    "latitude": 37.15,
    "longitude": 37.12,
    "zoom": 12
  },
  "uiContext": {
    "suggestedActions": ["View medical facilities", "Check supply status"]
  }
}
```

---

### 3. POST /agent/action

**Purpose:** Execute pre-defined actions

**URL:** `${API_ENDPOINT}agent/action`

**Headers:**
```
x-api-key: YOUR_API_KEY
Content-Type: application/json
```

**Body:**
```json
{
  "actionId": "SHOW_CRITICAL_INCIDENTS"
}
```

**Available Actions:**
- `SHOW_CRITICAL_INCIDENTS`
- `SHOW_MEDICAL_FACILITIES`
- `SHOW_SUPPLY_POINTS`
- `SHOW_FIRE_INCIDENTS`
- `SHOW_STRUCTURAL_DAMAGE`

**Example:**
```javascript
const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_ENDPOINT}agent/action`,
  {
    method: 'POST',
    headers: {
      'x-api-key': process.env.NEXT_PUBLIC_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      actionId: 'SHOW_CRITICAL_INCIDENTS'
    })
  }
);
const data = await response.json();
```

---

## Environment Variables Summary

### Backend (.env.local)
```bash
API_ENDPOINT=https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
TABLE_NAME=CommandCenterBackend-Dev-MasterEventTimeline
AGENT_ID=2SCAO1Z7OP
AGENT_ALIAS_ID=RFQMVJPVCE
AWS_REGION=us-east-1
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_ENDPOINT=https://aw1xewbtj7.execute-api.us-east-1.amazonaws.com/dev/
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Idempotency & Safety

### Safe to Run Multiple Times

The deployment script is idempotent and safe to run multiple times:

#### ✅ Harmless Operations (Always Execute)
- Checking AWS credentials
- Checking Bedrock access
- Installing npm dependencies (if missing)
- Building TypeScript
- Retrieving deployment outputs

#### ⚠️ Potentially Harmful Operations (With Checks)
- **CDK Bootstrap:** Only runs if not already bootstrapped
- **Stack Deployment:** Checks for conflicts before deploying
  - ✅ Proceeds if stack is stable
  - ❌ Fails if stack is being updated
  - ❌ Fails if stack is in failed state
- **Database Population:** Can be skipped with `--skip-populate`

### Conflict Detection

```bash
# If you run deployment while another is in progress:
✗ Stack is currently being updated. Please wait for it to complete.
  Current status: UPDATE_IN_PROGRESS

# If stack is in failed state:
✗ Stack is in a failed state: ROLLBACK_COMPLETE
You need to delete the stack first:
  cdk destroy
```

### Redeployment Scenarios

#### Scenario 1: No Changes
```bash
bash scripts/full-deploy.sh --skip-populate
# Result: Completes in 10-30 seconds, no resources updated
```

#### Scenario 2: Code Changes
```bash
# Changed Lambda code
bash scripts/full-deploy.sh --skip-populate
# Result: Updates only Lambda functions (1-2 minutes)
```

#### Scenario 3: Infrastructure Changes
```bash
# Changed API routes or DynamoDB schema
bash scripts/full-deploy.sh --skip-populate
# Result: Updates affected resources (3-5 minutes)
```

#### Scenario 4: Data Refresh Only
```bash
# No deployment needed
npm run populate-db
# Result: Refreshes database data (2-3 minutes)
```

---

## Verification

### Check Deployment Status

```bash
# View stack status
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackend-Dev \
  --query 'Stacks[0].StackStatus'

# View all outputs
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackend-Dev \
  --query 'Stacks[0].Outputs'
```

### Test API Endpoints

```bash
# Load credentials
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}" | jq

# Test query endpoint
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "Show critical incidents"}' | jq
```

### Check Database

```bash
# Count items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --select COUNT

# Sample items
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --limit 5
```

---

## Summary

### Stage 7: Retrieve Deployment Information
- ✅ Extracts all CloudFormation outputs
- ✅ Retrieves API key secret
- ✅ Saves to `.env.local`
- ✅ Displays formatted output

### Stage 8: Populate Database
- ✅ Generates simulation data
- ✅ Inserts into DynamoDB
- ✅ Verifies insertion
- ✅ Can be skipped with `--skip-populate`

### Client Integration
- ✅ All necessary outputs provided
- ✅ API endpoint URL
- ✅ API key for authentication
- ✅ Three endpoints: updates, query, action
- ✅ Complete API documentation

### Safety
- ✅ Idempotent script
- ✅ Conflict detection
- ✅ Safe to run multiple times
- ✅ Harmless operations always execute
- ✅ Harmful operations have checks

---

## Next Steps

1. ✅ Copy credentials from `.env.local` to frontend
2. ✅ Test API endpoints
3. ✅ Integrate with dashboard
4. ✅ Deploy frontend

**Your backend is ready for integration!** 🚀
