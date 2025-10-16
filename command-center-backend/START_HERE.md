# 🚀 START HERE - Command Center Backend Deployment

## Your Current Status

✅ **AWS CLI:** Installed and configured  
✅ **AWS Account:** 847272187168  
✅ **AWS User:** Command-center-hackathon-Administrator-Access  
✅ **Deployment Scripts:** Ready to use  

---

## 🎯 Deploy in 3 Commands

### 1️⃣ Check Prerequisites
```bash
cd command-center-backend
bash check-prerequisites.sh
```

This verifies you have:
- Node.js 18+
- npm
- AWS CLI
- AWS CDK

### 2️⃣ Request Bedrock Access (One-Time Manual Step)

**This is the ONLY manual step required!**

1. Open: https://console.aws.amazon.com/bedrock/
2. Click: **Model access** (left sidebar)
3. Click: **Manage model access**
4. Find: **Claude 3 Sonnet**
5. Check the box and click: **Request model access**
6. Wait for approval (usually instant)

**Why?** The AI agent needs Claude 3 Sonnet model access.

### 3️⃣ Deploy Everything
```bash
# Deploy with default model (Claude 3 Sonnet)
bash scripts/full-deploy.sh

# Or deploy with Claude 3.5 Sonnet (recommended)
bash scripts/full-deploy.sh --model anthropic.claude-3-5-sonnet-20240620-v1:0
```

**Time:** 10-15 minutes (waits for completion)  
**What it does:** Everything! (Bootstrap, build, deploy, populate database)

**See:** `MODEL_SELECTION.md` for other model options

---

## ✅ What You Get

After deployment:

```
API Endpoint: https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
API Key: xxxxxxxxxxxxxxxxxxxxxxxxxx
DynamoDB Table: MasterEventTimeline (with 7 days of data)
Bedrock Agent: Ready for natural language queries
```

All credentials saved to `.env.local`

---

## 🔄 After Making Code Changes

**Question:** If I change Lambda code, API routes, or JSON configs, do I just run the script again?

**Answer:** YES! Just run:
```bash
bash scripts/full-deploy.sh --skip-populate
```

CDK is smart - it only updates what changed:
- Changed Lambda code? → Updates only that Lambda (1-2 min)
- Changed API routes? → Updates only API Gateway (2-3 min)
- No changes? → Completes in 10-30 seconds

**See REDEPLOYMENT_GUIDE.md for all scenarios.**

---

## 📋 Manual Steps Required

### Before First Deployment
1. ✋ **Request Bedrock Claude 3 Sonnet access** (AWS Console - see step 2 above)

### That's It!
Everything else is automated by the script.

---

## 📚 Documentation Files

| File | When to Read |
|------|--------------|
| **START_HERE.md** | ← You are here (read first) |
| **DEPLOYMENT_README.md** | Complete overview |
| **PRE_DEPLOYMENT_CHECKLIST.md** | Prerequisites and installation |
| **REDEPLOYMENT_GUIDE.md** | After making code changes |
| **QUICK_DEPLOY.md** | Quick reference |
| **DEPLOYMENT_GUIDE.md** | Detailed documentation |

---

## 🎬 What Happens During Deployment?

```
Step 1: Verify AWS credentials ✓
Step 2: Check Bedrock access ✓
Step 3: Bootstrap CDK (if needed) ✓
Step 4: Install npm dependencies ✓
Step 5: Build TypeScript ✓
Step 6: Deploy infrastructure ✓
        - DynamoDB table
        - 4 Lambda functions
        - API Gateway
        - Bedrock Agent
        - IAM roles
Step 7: Retrieve API credentials ✓
Step 8: Populate database ✓

DEPLOYMENT COMPLETE! 🎉
```

---

## 🔗 Connect to Frontend

After deployment, copy credentials to your frontend:

### From Backend (auto-generated)
```bash
# command-center-backend/.env.local
API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### To Frontend (you create)
```bash
# command-center-dashboard/.env.local
NEXT_PUBLIC_API_ENDPOINT=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
NEXT_PUBLIC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🧪 Test the Deployment

```bash
# Load credentials
source .env.local

# Test API
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
```

---

## ❓ Common Questions

### Q: Do I need to visit AWS Console?
**A:** Only once, to request Bedrock model access. Everything else is automated.

### Q: What if I change Lambda code?
**A:** Just run `bash scripts/full-deploy.sh --skip-populate` again.

### Q: What if I change API routes?
**A:** Same - just run the script again.

### Q: What if I only change database data?
**A:** No deployment needed! Just run `npm run populate-db`

### Q: How long does redeployment take?
**A:** 1-5 minutes depending on what changed. CDK only updates changed resources.

### Q: Can I preview changes before deploying?
**A:** Yes! Run `cdk diff` to see what will change.

---

## 🚨 Troubleshooting

### "Access Denied" for Bedrock
→ Request Claude 3 Sonnet access (see step 2 above)

### "CDK not bootstrapped"
→ Script handles this automatically

### "npm not found"
→ Install Node.js: https://nodejs.org/

### Deployment failed
→ Check logs:
```bash
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 10
```

---

## 🗑️ Cleanup

Remove everything:
```bash
cdk destroy
```

---

## 💰 Costs

- **Development:** ~$5-10/month
- **Budget alarm:** Set at $50 USD
- **Main costs:** Bedrock Agent, Lambda, DynamoDB

---

## 🎯 Quick Commands

```bash
# Check prerequisites
bash check-prerequisites.sh

# Deploy everything
bash scripts/full-deploy.sh

# Redeploy after changes
bash scripts/full-deploy.sh --skip-populate

# Preview changes
cdk diff

# Test API
npm run test:integration

# View logs
aws logs tail /aws/lambda/queryHandlerLambda --follow

# Cleanup
cdk destroy
```

---

## 🚀 Ready to Deploy?

```bash
cd command-center-backend
bash check-prerequisites.sh
# Then request Bedrock access (AWS Console)
bash scripts/full-deploy.sh
```

**That's it!** The script handles everything else.

---

## 📞 Need More Help?

- **Prerequisites:** See `PRE_DEPLOYMENT_CHECKLIST.md`
- **Redeployment:** See `REDEPLOYMENT_GUIDE.md`
- **Full docs:** See `DEPLOYMENT_GUIDE.md`
- **API docs:** See `API_DOCUMENTATION.md`

---

**Happy deploying! 🎉**
