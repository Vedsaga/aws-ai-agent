# Command Center Backend - Complete Deployment Guide

## 🚀 Quick Start (3 Steps)

```bash
# 1. Check prerequisites
bash check-prerequisites.sh

# 2. Request Bedrock access (AWS Console - one time only)
# Go to: https://console.aws.amazon.com/bedrock/ → Model access → Request Claude 3 Sonnet

# 3. Deploy everything
npm run deploy
```

**That's it!** The deployment takes ~10 minutes and handles everything automatically.

---

## 📋 Prerequisites

### Required Software
- **Node.js 18+**: `node --version`
- **npm**: `npm --version`
- **AWS CLI v2**: `aws --version`
- **AWS CDK**: `npm install -g aws-cdk`

### AWS Setup
```bash
# Configure AWS credentials
aws configure

# Verify configuration
aws sts get-caller-identity
```

### Bedrock Model Access (One-Time)
1. Go to AWS Console → Bedrock → Model access
2. Request access to **Claude 3 Sonnet**
3. Wait for approval (usually instant)

---

## 🔧 502 Error Fix (If Deploying for First Time)

### Problem
Lambda functions fail with `Error: Cannot find module 'zod'` because dependencies weren't bundled.

### Solution (Already Applied)
The deployment now automatically bundles all dependencies. Just run:

```bash
npm run deploy
```

This command:
1. Builds TypeScript → `dist/`
2. Creates bundle with dependencies → `lambda-bundle/`
3. Deploys to AWS with CDK

### What Changed
- **Before**: Lambda used `dist/` (no node_modules) ❌
- **After**: Lambda uses `lambda-bundle/` (with node_modules) ✅

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
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy everything
npm run deploy
```

### What Gets Deployed
- ✅ DynamoDB table (MasterEventTimeline)
- ✅ 4 Lambda functions (with dependencies bundled)
- ✅ API Gateway REST API
- ✅ Bedrock Agent with Action Group
- ✅ IAM roles and policies
- ✅ CloudWatch log groups
- ✅ Cost monitoring alarms

### Deployment Time
- **First deployment**: ~10-15 minutes
- **Updates**: ~2-5 minutes (only changed resources)

---

## 🔄 Redeployment (After Code Changes)

```bash
# Redeploy everything
npm run deploy

# Or deploy without re-bundling (if only CDK stack changed)
npm run deploy:quick
```

CDK is smart - it only updates what changed:
- Changed Lambda code? → Updates only that Lambda
- Changed API routes? → Updates only API Gateway
- No changes? → Completes in seconds

---

## 📊 Post-Deployment

### 1. Save Outputs

After deployment, save these values:

```
API Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
API Key ID: xxxxx
Table Name: CommandCenterBackend-Dev-MasterEventTimeline
Agent ID: xxxxx
```

### 2. Retrieve API Key

```bash
aws apigateway get-api-key --api-key YOUR_API_KEY_ID --include-value
```

Or check `.env.local` (auto-generated).

### 3. Populate Database

```bash
npm run populate-db
```

This generates 7 days of simulation data (~500-1000 events).

### 4. Verify Deployment

```bash
# Quick test
npm run test:quick

# Full test suite
npm run test:api
```

---

## 🧪 Testing

### Test Individual Endpoints

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

### Run Test Suites

```bash
# Quick API test
npm run test:quick

# Full API test suite
npm run test:api

# Integration tests
npm run test:integration
```

---

## 🔍 Troubleshooting

### 502 Errors
**Cause**: Missing dependencies in Lambda package  
**Fix**: Already applied! Just run `npm run deploy`

### 403 Forbidden
**Cause**: Missing or invalid API key  
**Fix**: Include `x-api-key` header with valid key

### Bedrock Access Denied
**Cause**: Model access not requested  
**Fix**: Request Claude 3 Sonnet access in AWS Console

### Deployment Fails
**Cause**: Insufficient permissions  
**Fix**: Ensure IAM user has CloudFormation, Lambda, API Gateway, DynamoDB, Bedrock permissions

### Check Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow
aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow
aws logs tail /aws/lambda/CommandCenterBackend-Dev-ActionHandler --follow
```

---

## 📁 Project Structure

```
command-center-backend/
├── lib/
│   ├── command-center-backend-stack.ts  # CDK stack definition
│   ├── lambdas/                         # Lambda function code
│   ├── types/                           # TypeScript types
│   └── agent/                           # Bedrock Agent config
├── scripts/
│   ├── prepare-lambda-bundle.sh         # Bundle dependencies
│   ├── populate-database.ts             # Generate simulation data
│   └── test-api.sh                      # API test script
├── dist/                                # Compiled TypeScript
├── lambda-bundle/                       # Lambda deployment package
├── package.json                         # Dependencies
└── .env.local                           # API credentials (auto-generated)
```

---

## 🔐 Environment Variables

### Lambda Functions Receive:
- `TABLE_NAME`: DynamoDB table name
- `AGENT_ID`: Bedrock Agent ID
- `AGENT_ALIAS_ID`: Bedrock Agent Alias ID
- `LOG_LEVEL`: DEBUG (dev) or INFO (prod)

### Frontend Needs (copy from `.env.local`):
```bash
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxx
```

---

## 💰 Cost Monitoring

- **Budget Alarm**: Triggers at $50 USD
- **SNS Notification**: Sends email alert
- **Estimated Monthly Cost**: $5-10 (dev), $20-50 (prod with traffic)

### Main Cost Drivers:
1. Bedrock Agent invocations (~$0.003 per request)
2. Lambda invocations (free tier: 1M requests/month)
3. DynamoDB (on-demand pricing)
4. API Gateway (free tier: 1M requests/month)

---

## 🗑️ Cleanup

### Remove Everything
```bash
cdk destroy
```

**Warning**: This deletes all resources including data!

---

## 📚 Additional Documentation

- **API_DOCUMENTATION.md** - API endpoint reference
- **TESTING_GUIDE.md** - Testing strategies
- **README.md** - Project overview

---

## 🎯 Quick Commands Reference

```bash
# Check prerequisites
bash check-prerequisites.sh

# Deploy (bundles + deploys)
npm run deploy

# Deploy without bundling
npm run deploy:quick

# Bundle only
npm run bundle

# Populate database
npm run populate-db

# Test API
npm run test:quick
npm run test:api

# View logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow

# Preview changes
cdk diff

# Cleanup
cdk destroy
```

---

## ✅ Deployment Checklist

### Before First Deployment
- [ ] Node.js 18+ installed
- [ ] AWS CLI configured
- [ ] AWS CDK installed globally
- [ ] Bedrock Claude 3 Sonnet access requested
- [ ] IAM permissions verified

### After Deployment
- [ ] API endpoint saved
- [ ] API key retrieved
- [ ] Database populated
- [ ] Tests passing
- [ ] Credentials shared with frontend team

---

## 🆘 Getting Help

### Check Logs
```bash
# Lambda logs
aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --since 5m

# CloudFormation events
aws cloudformation describe-stack-events --stack-name CommandCenterBackend-Dev --max-items 10
```

### Verify Resources
```bash
# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'CommandCenter')]"

# Check DynamoDB table
aws dynamodb describe-table --table-name CommandCenterBackend-Dev-MasterEventTimeline

# Verify API Gateway
aws apigateway get-rest-apis --query "items[?contains(name, 'CommandCenter')]"
```

---

**Last Updated**: 2025-10-16  
**Version**: 2.0.0 (with 502 fix)
