# Deployment Guide

Complete guide for deploying the Command Center Backend to AWS.

---

## 🚀 Quick Start (2 Steps)

```bash
# 1. Request Bedrock access (AWS Console - one time only)
# Go to: https://console.aws.amazon.com/bedrock/ → Model access → Request OpenAI GPT-4o

# 2. Deploy everything
./deploy.sh
```

**That's it!** The deployment takes ~10 minutes and handles everything automatically:
- ✅ Prerequisites check
- ✅ CDK bootstrap
- ✅ TypeScript build
- ✅ Lambda bundling with dependencies
- ✅ CDK deployment
- ✅ Database population
- ✅ Credentials saved to `.env.local`

---

## 📋 Prerequisites

### Required Software

| Software | Version | Check Command | Install |
|----------|---------|---------------|---------|
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| npm | Latest | `npm --version` | Comes with Node.js |
| AWS CLI | v2 | `aws --version` | [AWS CLI Install](https://aws.amazon.com/cli/) |
| AWS CDK | Latest | `cdk --version` | `npm install -g aws-cdk` |

### AWS Setup

```bash
# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# Verify configuration
aws sts get-caller-identity
```

### Bedrock Model Access (One-Time)

1. Go to [AWS Console → Bedrock → Model access](https://console.aws.amazon.com/bedrock/)
2. Click **"Manage model access"**
3. Select **"OpenAI GPT-4o"** (openai.gpt-4o-2024-11-20-v1)
4. Click **"Request model access"**
5. Wait for approval (usually instant)

---

## 📦 Installation

```bash
cd command-center-backend
npm install
```

---

## 🚀 Deployment

### First-Time Deployment

```bash
./deploy.sh
```

**What happens:**

```
[1/7] Checking prerequisites...
  ✓ Node.js v20.10.0
  ✓ npm v10.2.3
  ✓ AWS CLI installed
  ✓ AWS credentials configured
  ✓ AWS CDK installed

[2/7] Checking CDK bootstrap...
  ✓ CDK already bootstrapped

[3/7] Installing dependencies...
  ✓ Dependencies already installed

[4/7] Building and bundling Lambda functions...
  ✓ TypeScript compiled
  ✓ Lambda bundle created (45M)

[5/7] Deploying CDK stack...
  ✓ Stack deployed successfully

[6/7] Retrieving deployment information...
  ✓ Stack outputs retrieved
  API Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
  API Key: xxxxxxxxxxxxx
  ✓ Credentials saved to .env.local

[7/7] Populating database...
  ✓ Database populated (847 items)

╔════════════════════════════════════════════════════════════╗
║              DEPLOYMENT COMPLETED SUCCESSFULLY             ║
╚════════════════════════════════════════════════════════════╝
```

### Deployment Options

```bash
# Deploy without populating database
./deploy.sh --skip-populate

# Deploy to production
./deploy.sh --stage prod

# Deploy without CDK bootstrap check
./deploy.sh --skip-bootstrap

# Show help
./deploy.sh --help
```

### What Gets Deployed

| Resource | Description | Name Pattern |
|----------|-------------|--------------|
| DynamoDB Table | Event timeline storage | `CommandCenterBackend-{Stage}-MasterEventTimeline` |
| Lambda Functions | 4 handlers | `CommandCenterBackend-{Stage}-{Handler}` |
| API Gateway | REST API | `CommandCenterBackend-{Stage}-API` |
| Bedrock Agent | AI query processor | `CommandCenterAgent-{Stage}` |
| IAM Roles | Least privilege roles | `CommandCenterBackend-{Stage}-{Role}` |
| CloudWatch Logs | Lambda logs | `/aws/lambda/CommandCenterBackend-{Stage}-*` |
| CloudWatch Alarm | Budget monitoring | `CommandCenterBackend-{Stage}-BudgetAlarm` |

### Deployment Time

- **First deployment**: ~10-15 minutes
- **Updates**: ~2-5 minutes (only changed resources)
- **No changes**: ~30 seconds (verification only)

---

## 🔄 Redeployment (After Code Changes)

```bash
# Full redeployment (recommended)
./deploy.sh

# Quick deploy (skip bundling if only CDK stack changed)
npm run deploy:quick

# Deploy specific stage
./deploy.sh --stage prod
```

**CDK is smart** - it only updates what changed:
- Changed Lambda code? → Updates only that Lambda
- Changed API routes? → Updates only API Gateway
- No changes? → Completes in seconds

---

## 📊 Post-Deployment

### 1. Verify Deployment

```bash
# Test all endpoints
./test-api.sh
```

Expected output:
```
╔════════════════════════════════════════════════════════════╗
║              Command Center API Test Suite                ║
╚════════════════════════════════════════════════════════════╝

[Test 1] GET /data/updates - Valid request
  ✓ PASSED (Status: 200)

[Test 2] POST /agent/query - Valid request
  ✓ PASSED (Status: 200)

...

Total Tests: 10
Passed: 10
Failed: 0

✓ All tests passed!
```

### 2. Check Credentials

Credentials are automatically saved to `.env.local`:

```bash
cat .env.local
```

Output:
```
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
API_KEY=xxxxxxxxxxxxx
TABLE_NAME=CommandCenterBackend-Dev-MasterEventTimeline
AGENT_ID=XXXXXXXXXX
AGENT_ALIAS_ID=XXXXXXXXXX
AWS_REGION=us-east-1
```

### 3. Share with Frontend Team

Copy credentials to frontend `.env.local`:

```bash
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxx
```

### 4. Populate Database (if skipped)

```bash
npm run populate-db
```

This generates 7 days of simulation data (~500-1000 events).

---

## 🧪 Testing

### Quick Test

```bash
# Load credentials
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}" | jq
```

### Full Test Suite

```bash
./test-api.sh
```

Tests 10 scenarios:
1. ✓ GET /data/updates - Valid request
2. ✓ GET /data/updates - With domain filter
3. ✓ GET /data/updates - Missing parameter (400)
4. ✓ POST /agent/query - Valid request
5. ✓ POST /agent/query - Empty text (400)
6. ✓ POST /agent/action - Valid action
7. ✓ POST /agent/action - Invalid action (400)
8. ✓ POST /agent/action - HELP action
9. ✓ Authentication - No API key (403)
10. ✓ Authentication - Invalid API key (403)

---

## 🔍 Troubleshooting

### 502 Errors (Bad Gateway)

**Symptom**: API returns 502 error

**Cause**: Missing dependencies in Lambda package (historical issue, now fixed)

**Solution**: The deployment now automatically bundles dependencies. Just run:
```bash
./deploy.sh
```

**What changed**:
- **Before**: Lambda used `dist/` (no node_modules) ❌
- **After**: Lambda uses `lambda-bundle/` (with node_modules) ✅

**Technical details**:
The `deploy.sh` script now:
1. Builds TypeScript → `dist/`
2. Creates `lambda-bundle/` directory
3. Copies compiled code to `lambda-bundle/`
4. Installs production dependencies in `lambda-bundle/`
5. Optimizes bundle size (removes .md, .ts, .map, tests)
6. CDK deploys from `lambda-bundle/`

### 403 Forbidden

**Symptom**: API returns 403 error

**Causes**:
1. Missing API key in request
2. Invalid API key
3. Wrong header name

**Solution**:
```bash
# Ensure header is correct
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
  
# NOT: -H "Authorization: Bearer ${API_KEY}"
# NOT: -H "api-key: ${API_KEY}"
```

### Bedrock Access Denied

**Symptom**: `/agent/query` returns error about Bedrock access

**Cause**: OpenAI GPT-4o model access not requested

**Solution**:
1. Go to [AWS Console → Bedrock → Model access](https://console.aws.amazon.com/bedrock/)
2. Request access to **OpenAI GPT-4o**
3. Wait for approval (usually instant)
4. Redeploy: `./deploy.sh --skip-populate`

### Deployment Fails

**Symptom**: `cdk deploy` fails with permission error

**Cause**: Insufficient IAM permissions

**Required permissions**:
- CloudFormation (full)
- Lambda (full)
- API Gateway (full)
- DynamoDB (full)
- IAM (create/update roles)
- Bedrock (full)
- CloudWatch (logs, alarms)

**Solution**:
```bash
# Check current permissions
aws iam get-user

# Attach AdministratorAccess (for development)
# Or create custom policy with required permissions
```

### Database Empty

**Symptom**: API returns empty results

**Cause**: Database not populated

**Solution**:
```bash
npm run populate-db
```

**Verify**:
```bash
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --select COUNT
```

### Check Logs

```bash
# View real-time logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow

# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) * 1000 - 600000))

# View specific time range
aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --since 10m
```

### Verify Resources

```bash
# List Lambda functions
aws lambda list-functions \
  --query "Functions[?contains(FunctionName, 'CommandCenter')].[FunctionName,Runtime,LastModified]" \
  --output table

# Check DynamoDB table
aws dynamodb describe-table \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --query "Table.[TableName,TableStatus,ItemCount]"

# Verify API Gateway
aws apigateway get-rest-apis \
  --query "items[?contains(name, 'CommandCenter')].[name,id]" \
  --output table

# Check Bedrock Agent
aws bedrock-agent list-agents \
  --query "agentSummaries[?contains(agentName, 'CommandCenter')]"
```

---

## 💰 Cost Monitoring

### Budget Alarm

- **Threshold**: $50 USD/month
- **Action**: SNS email notification
- **Check**: AWS Console → CloudWatch → Alarms

### Estimated Costs

| Environment | Monthly Cost | Traffic |
|-------------|--------------|---------|
| Development | $5-10 | Low (testing only) |
| Staging | $10-20 | Medium (team testing) |
| Production | $20-50 | High (real users) |

### Cost Breakdown

| Service | Cost Driver | Estimate |
|---------|-------------|----------|
| Bedrock Agent | Per request (~$0.003) | $5-30 |
| Lambda | Invocations + Duration | $0-5 (free tier) |
| DynamoDB | On-demand reads/writes | $1-5 |
| API Gateway | Requests | $0-3 (free tier) |
| CloudWatch | Logs storage | $1-2 |

### Monitor Costs

```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Check budget status
aws budgets describe-budgets \
  --account-id $(aws sts get-caller-identity --query Account --output text)
```

---

## 🗑️ Cleanup

### Remove All Resources

```bash
cdk destroy
```

**Warning**: This deletes:
- ❌ DynamoDB table (all data lost)
- ❌ Lambda functions
- ❌ API Gateway
- ❌ Bedrock Agent
- ❌ IAM roles
- ❌ CloudWatch logs

**Confirmation required**: Type `y` when prompted

### Partial Cleanup

```bash
# Empty database only
aws dynamodb scan \
  --table-name CommandCenterBackend-Dev-MasterEventTimeline \
  --attributes-to-get Day Timestamp \
  --output json | \
jq -r '.Items[] | @json' | \
while read item; do
  aws dynamodb delete-item \
    --table-name CommandCenterBackend-Dev-MasterEventTimeline \
    --key "$item"
done

# Delete specific Lambda
aws lambda delete-function \
  --function-name CommandCenterBackend-Dev-UpdatesHandler
```

---

## 🎯 Quick Commands Reference

```bash
# Deployment
./deploy.sh                      # Full deployment
./deploy.sh --skip-populate      # Deploy without database
./deploy.sh --stage prod         # Deploy to production
npm run deploy:quick             # Deploy without re-bundling

# Testing
./test-api.sh                    # Test all endpoints
npm run test:api                 # Same as above

# Database
npm run populate-db              # Populate database

# Monitoring
aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow

# Verification
cdk diff                         # Preview changes
aws cloudformation describe-stacks --stack-name CommandCenterBackend-Dev

# Cleanup
cdk destroy                      # Remove all resources
```

---

## ✅ Deployment Checklist

### Before First Deployment
- [ ] Node.js 18+ installed
- [ ] AWS CLI configured (`aws sts get-caller-identity`)
- [ ] AWS CDK installed globally (`cdk --version`)
- [ ] Bedrock OpenAI GPT-4o access requested
- [ ] IAM permissions verified

### During Deployment
- [ ] Run `./deploy.sh`
- [ ] Wait ~10-15 minutes
- [ ] Check for errors in output
- [ ] Note API endpoint and key

### After Deployment
- [ ] Credentials saved to `.env.local`
- [ ] Database populated (check count)
- [ ] Tests passing (`./test-api.sh`)
- [ ] Credentials shared with frontend team
- [ ] CloudWatch alarms configured

---

## 🆘 Getting Help

### Check Logs
```bash
# Lambda logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --since 5m

# CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackend-Dev \
  --max-items 10
```

### Common Commands
```bash
# Verify deployment
aws cloudformation describe-stacks --stack-name CommandCenterBackend-Dev

# Test API
source .env.local && curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" -H "x-api-key: ${API_KEY}"

# Check database
aws dynamodb scan --table-name CommandCenterBackend-Dev-MasterEventTimeline --select COUNT
```

---

**Last Updated**: 2025-10-16  
**Version**: 2.0.0 (with dependency bundling fix)
