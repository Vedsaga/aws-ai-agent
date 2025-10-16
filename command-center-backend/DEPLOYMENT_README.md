# Command Center Backend - Complete Deployment Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Check Prerequisites
```bash
bash check-prerequisites.sh
```

### Step 2: Request Bedrock Access (One-Time, Manual)
1. Go to: https://console.aws.amazon.com/bedrock/
2. Click: **Model access** (left sidebar)
3. Click: **Manage model access** or **Request model access**
4. Find and check: **Claude 3 Sonnet**
5. Click: **Request model access**
6. Wait for approval (usually instant)

### Step 3: Deploy Everything
```bash
bash scripts/full-deploy.sh
```

**That's it!** ☕ Grab coffee while it deploys (5-10 minutes).

---

## 📋 What You Need

### Already Have ✓
- AWS CLI installed
- AWS credentials configured
- Account: `847272187168`
- User: `Command-center-hackathon-Administrator-Access`

### Need to Install (If Missing)
- Node.js 18+ (`node --version`)
- AWS CDK (`npm install -g aws-cdk`)

### Need to Do Once (Manual)
- Request Bedrock Claude 3 Sonnet access (see Step 2 above)

---

## 📁 Documentation Files

| File | Purpose |
|------|---------|
| **DEPLOYMENT_README.md** | ← You are here (start here) |
| **PRE_DEPLOYMENT_CHECKLIST.md** | Prerequisites and manual steps |
| **REDEPLOYMENT_GUIDE.md** | How to redeploy after code changes |
| **QUICK_DEPLOY.md** | Quick reference guide |
| **DEPLOYMENT_GUIDE.md** | Comprehensive deployment documentation |
| **API_DOCUMENTATION.md** | API usage and endpoints |

---

## 🎯 Deployment Scripts

### Full Automated Deployment
```bash
bash scripts/full-deploy.sh
```
**Does everything:** Bootstrap, build, deploy, populate database

### Simple Deployment
```bash
bash deploy-now.sh
```
**Quick version:** Build and deploy only

### Check Prerequisites
```bash
bash check-prerequisites.sh
```
**Verifies:** All required tools are installed

---

## 🔄 After Making Code Changes

### Quick Answer
**Yes!** Just run the deployment script again:
```bash
bash scripts/full-deploy.sh --skip-populate
```

### What Gets Updated?
CDK is smart - it only updates what changed:

| Change Type | What Updates | Time |
|-------------|--------------|------|
| Lambda code | Only Lambda functions | 1-2 min |
| API routes | Only API Gateway | 2-3 min |
| Infrastructure | Specific resources | 3-5 min |
| No changes | Nothing (CDK detects) | 10-30 sec |

### Detailed Guide
See **REDEPLOYMENT_GUIDE.md** for all scenarios.

---

## 📦 What Gets Deployed

### Infrastructure (Automated)
- ✅ DynamoDB table (MasterEventTimeline)
- ✅ 4 Lambda functions (updates, query, action, tool handlers)
- ✅ API Gateway REST API
- ✅ Bedrock Agent with Claude 3 Sonnet
- ✅ IAM roles and policies
- ✅ CloudWatch logs and monitoring
- ✅ Cost monitoring alarms

### Data (Automated)
- ✅ 7 days of simulation data
- ✅ Multiple domains (Medical, Fire, Structural, etc.)
- ✅ GeoJSON location data
- ✅ ~500-1000 events

### Configuration (Automated)
- ✅ API key generation
- ✅ Credentials saved to `.env.local`
- ✅ CORS configuration
- ✅ Environment variables

---

## 🎬 Deployment Process

### What Happens When You Run the Script?

```
[1/8] Checking AWS credentials... ✓
      Account: 847272187168
      Region: us-east-1

[2/8] Checking Bedrock model access... ✓
      Claude 3 Sonnet: Available

[3/8] Checking CDK bootstrap... ✓
      Already bootstrapped

[4/8] Installing dependencies... ✓
      npm packages installed

[5/8] Building TypeScript... ✓
      Compiled successfully

[6/8] Deploying CDK stack... ⏳
      Creating DynamoDB table...
      Creating Lambda functions...
      Creating API Gateway...
      Creating Bedrock Agent...
      ✓ Deployment complete!

[7/8] Retrieving deployment info... ✓
      API Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
      API Key: xxxxxxxxxxxxxxxxxxxxxxxxxx
      Saved to .env.local

[8/8] Populating database... ✓
      Inserted 847 events
      Database ready!

═══════════════════════════════════════
    DEPLOYMENT COMPLETED SUCCESSFULLY
═══════════════════════════════════════
```

---

## 🔗 Frontend Integration

After deployment, copy credentials to your frontend:

### Backend `.env.local` (auto-generated)
```bash
# command-center-backend/.env.local
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
TABLE_NAME=MasterEventTimeline
AGENT_ID=XXXXXXXXXX
```

### Frontend `.env.local` (you create)
```bash
# command-center-dashboard/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy the values** from backend to frontend.

---

## ✅ Testing the Deployment

### Quick API Test
```bash
# Load credentials
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"

# Test query endpoint
curl -X POST "${API_ENDPOINT}/agent/query" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the most urgent needs?"}'
```

### Run Integration Tests
```bash
npm run test:integration
```

---

## 🔧 Common Issues

### Issue: "Access Denied" for Bedrock
**Solution:** Request Claude 3 Sonnet access in AWS Console (see Step 2)

### Issue: "CDK not bootstrapped"
**Solution:** Script handles this automatically, or run:
```bash
cdk bootstrap aws://847272187168/us-east-1
```

### Issue: "npm not found"
**Solution:** Install Node.js (includes npm)
```bash
# Check installation guide in PRE_DEPLOYMENT_CHECKLIST.md
```

### Issue: Deployment failed
**Solution:** Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 10
```

---

## 🗑️ Cleanup

Remove all resources:
```bash
cdk destroy
```

**Warning:** This deletes everything including data!

---

## 💰 Cost Monitoring

### Included Monitoring
- Budget alarm at $50 USD
- CloudWatch dashboard
- Email alerts (if configured)

### Estimated Costs
- **Development/Testing:** $5-10/month
- **Production (light use):** $20-30/month
- **Main costs:** Bedrock Agent invocations, Lambda, DynamoDB

### View Current Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## 📞 Need Help?

### Check These First
1. **PRE_DEPLOYMENT_CHECKLIST.md** - Prerequisites and setup
2. **REDEPLOYMENT_GUIDE.md** - Redeployment scenarios
3. **DEPLOYMENT_GUIDE.md** - Comprehensive guide
4. **CloudWatch Logs** - Error details

### View Logs
```bash
# Query handler logs
aws logs tail /aws/lambda/queryHandlerLambda --follow

# Updates handler logs
aws logs tail /aws/lambda/updatesHandlerLambda --follow
```

### Stack Status
```bash
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackendStack
```

---

## 🎯 Summary

### Manual Steps (Do Once)
1. ✋ Request Bedrock Claude 3 Sonnet access (AWS Console)

### Automated Steps (Script Handles)
- ✅ Everything else!

### Redeployment (After Code Changes)
```bash
bash scripts/full-deploy.sh --skip-populate
```

### Ready to Deploy?
```bash
bash check-prerequisites.sh  # Verify prerequisites
bash scripts/full-deploy.sh  # Deploy everything
```

---

## 📚 Quick Command Reference

```bash
# Check prerequisites
bash check-prerequisites.sh

# Full deployment
bash scripts/full-deploy.sh

# Redeploy after changes
bash scripts/full-deploy.sh --skip-populate

# Preview changes
cdk diff

# Build only
npm run build

# Deploy only
cdk deploy

# Populate database only
npm run populate-db

# Test API
npm run test:integration

# View logs
aws logs tail /aws/lambda/queryHandlerLambda --follow

# Cleanup
cdk destroy
```

---

**Ready to deploy? Run:** `bash scripts/full-deploy.sh` 🚀
