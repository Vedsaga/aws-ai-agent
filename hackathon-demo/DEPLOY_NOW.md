# Deploy Now - 15 Minute Checklist

## Prerequisites (2 min)
- [ ] AWS CLI configured (`aws sts get-caller-identity`)
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js installed (for CDK) (`node --version`)
- [ ] Mapbox account created (free tier)

## Deploy Backend (8 min)

### Step 1: Run Quick Deploy
```bash
cd hackathon-demo
./quick-deploy.sh
```

**What it does:**
1. Installs CDK dependencies
2. Bootstraps CDK (if needed)
3. Deploys stack
4. Outputs API endpoint

**Expected output:**
```
✅ Deployment Complete!
API Endpoint: https://abc123.execute-api.us-east-1.amazonaws.com/prod/
```

### Step 2: Save API URL
```bash
# Copy the API endpoint URL
export API_URL="<your-api-url>"
```

## Setup Frontend (3 min)

### Step 1: Get Mapbox Token
1. Go to https://account.mapbox.com/access-tokens/
2. Create new token (or use default)
3. Copy token

### Step 2: Edit Frontend
```bash
cd frontend
# Edit index.html
```

Replace these two lines:
```javascript
const API_URL = 'YOUR_API_ENDPOINT_HERE'; // Line ~238
const MAPBOX_TOKEN = 'YOUR_MAPBOX_TOKEN'; // Line ~239
```

With:
```javascript
const API_URL = 'https://abc123.execute-api.us-east-1.amazonaws.com/prod/';
const MAPBOX_TOKEN = 'pk.eyJ1...'; // Your token
```

### Step 3: Open in Browser
```bash
# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

## Test (2 min)

### Test 1: Ingestion
1. Type: "Street light broken near post office"
2. Watch agent status panel
3. See clarification request
4. Type: "Yes, 123 Main Street"
5. See report saved + marker on map

### Test 2: Query
1. Switch to Query mode
2. Type: "Show me all high-priority issues"
3. Watch agents execute
4. See results + map update

### Test 3: Management
1. Switch to Management mode
2. Type: "Assign this to Team B"
3. Watch agents execute
4. See confirmation

## Troubleshooting

### CDK Bootstrap Fails
```bash
# Manually bootstrap
cd cdk
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Lambda Timeout
```bash
# Increase timeout in cdk/app.py
timeout=Duration.seconds(120)  # Change from 60 to 120
cdk deploy
```

### Bedrock Access Denied
1. Go to AWS Console → Bedrock
2. Enable model access for:
   - Amazon Nova Pro
   - Amazon Nova Lite
3. Wait 2-3 minutes
4. Redeploy: `cdk deploy`

### Map Not Loading
- Check Mapbox token is correct
- Check browser console for errors
- Verify token has correct permissions

### API Not Responding
```bash
# Check Lambda logs
aws logs tail /aws/lambda/domainflow-orchestrator --follow
```

## Demo Checklist

### Before Demo:
- [ ] Backend deployed
- [ ] Frontend configured
- [ ] Test all 3 modes
- [ ] Map displays correctly
- [ ] Agent status panel works
- [ ] Confidence scores visible
- [ ] Dark mode looks good

### During Demo:
- [ ] Show mode badge in header
- [ ] Highlight agent status panel
- [ ] Point out confidence scores
- [ ] Explain orchestrator/verifier
- [ ] Show real-time updates
- [ ] Demonstrate clarification flow

### After Demo:
- [ ] Answer questions
- [ ] Share GitHub repo
- [ ] Collect feedback

## Quick Commands

### Redeploy Backend
```bash
cd hackathon-demo/cdk
cdk deploy
```

### View Logs
```bash
aws logs tail /aws/lambda/domainflow-orchestrator --follow
```

### Test API
```bash
curl -X POST $API_URL/orchestrate \
  -H 'Content-Type: application/json' \
  -d '{"mode":"ingestion","message":"test"}'
```

### List Reports
```bash
curl $API_URL/reports
```

### Destroy Stack
```bash
cd hackathon-demo/cdk
cdk destroy
```

## Cost Estimate

**Demo usage (100 requests):**
- Lambda: $0.20
- DynamoDB: $0.25
- Bedrock (Nova): $0.50
- API Gateway: $0.01
- EventBridge: $0.00

**Total: ~$1.00 per day**

## Success Criteria

✅ All 3 modes work
✅ Agent status panel displays
✅ Confidence scores visible
✅ Map updates in real-time
✅ Dark mode looks professional
✅ Clarification flow works
✅ No errors in console

## Emergency Backup

If deployment fails, use pre-recorded demo:
1. Show screenshots
2. Walk through code
3. Explain architecture
4. Show VISUAL_FLOW.md diagrams

## Time Breakdown

- Prerequisites: 2 min
- Backend deploy: 8 min
- Frontend setup: 3 min
- Testing: 2 min

**Total: 15 minutes**

---

**Ready? Let's deploy!**

```bash
cd hackathon-demo
./quick-deploy.sh
```

🚀
