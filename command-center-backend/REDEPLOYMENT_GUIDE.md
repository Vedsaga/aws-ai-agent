# Redeployment Guide

## When to Redeploy

You need to redeploy when you make changes to:

### ✅ Always Requires Redeployment

1. **Lambda function code** (any `.ts` files in `lambda/` directory)
2. **CDK infrastructure** (changes to `lib/command-center-backend-stack.ts`)
3. **API Gateway configuration** (routes, methods, CORS)
4. **IAM roles and policies**
5. **DynamoDB table schema** (GSI, attributes)
6. **Bedrock Agent configuration** (instructions, action groups)
7. **Environment variables** for Lambda functions

### ❌ Does NOT Require Redeployment

1. **Database data** (DynamoDB items) - just run `npm run populate-db`
2. **Documentation files** (`.md` files)
3. **Test files** (files in `test/` directory)
4. **Scripts** (files in `scripts/` directory)
5. **Configuration files** (`.env.local`, `tsconfig.json`) - unless they affect build output

---

## How to Redeploy

### Quick Redeploy (After Code Changes)

```bash
# From command-center-backend directory

# Option 1: Full automated redeploy
bash scripts/full-deploy.sh

# Option 2: Manual steps
npm run build          # Compile TypeScript
cdk deploy            # Deploy changes
```

### What Gets Updated?

CDK is smart - it only updates what changed:

- **Lambda code changed?** → Only Lambda functions are updated
- **API routes changed?** → Only API Gateway is updated
- **Infrastructure unchanged?** → Deployment completes in seconds

### Deployment Time

- **First deployment**: 5-10 minutes (creates everything)
- **Code-only changes**: 1-2 minutes (updates Lambda)
- **Infrastructure changes**: 3-5 minutes (updates specific resources)
- **No changes**: 10-30 seconds (CDK detects no changes)

---

## Common Redeployment Scenarios

### Scenario 1: Changed Lambda Function Code

**Example:** Modified `lambda/queryHandler.ts`

```bash
# Quick redeploy
npm run build
cdk deploy

# Or use the full script
bash scripts/full-deploy.sh --skip-populate
```

**What happens:**
- TypeScript compiles to JavaScript
- CDK packages Lambda code
- Only affected Lambda function is updated
- API Gateway remains unchanged
- Database remains unchanged

**Time:** ~1-2 minutes

---

### Scenario 2: Changed API Routes

**Example:** Added new endpoint in `lib/command-center-backend-stack.ts`

```bash
npm run build
cdk deploy
```

**What happens:**
- API Gateway configuration updates
- New routes are added
- Existing routes remain active
- Lambda functions may be updated if referenced

**Time:** ~2-3 minutes

---

### Scenario 3: Changed Bedrock Agent Instructions

**Example:** Modified agent prompt in stack definition

```bash
npm run build
cdk deploy
```

**What happens:**
- Bedrock Agent configuration updates
- Agent is redeployed with new instructions
- May require agent alias update

**Time:** ~3-5 minutes

**Note:** Test changes in Bedrock Console before deploying to production

---

### Scenario 4: Changed Environment Variables

**Example:** Added new env var to Lambda

```bash
npm run build
cdk deploy
```

**What happens:**
- Lambda function configuration updates
- Function code may be redeployed
- Environment variables are updated

**Time:** ~1-2 minutes

---

### Scenario 5: Database Schema Change

**Example:** Added new GSI to DynamoDB table

```bash
npm run build
cdk deploy
```

**What happens:**
- DynamoDB table is updated
- GSI is created (can take several minutes)
- Existing data remains intact

**Time:** ~5-10 minutes (GSI creation is slow)

**⚠️ Warning:** Some schema changes require table recreation (data loss)

---

### Scenario 6: Only Data Changed

**Example:** Want to refresh simulation data

```bash
# No deployment needed!
npm run populate-db
```

**What happens:**
- Script connects to existing DynamoDB table
- Inserts new data
- No infrastructure changes

**Time:** ~2-3 minutes

---

## Redeployment Best Practices

### 1. Always Build Before Deploy

```bash
npm run build  # Catches TypeScript errors early
cdk deploy
```

### 2. Preview Changes First

```bash
cdk diff  # Shows what will change
```

Example output:
```
Stack CommandCenterBackendStack
Resources
[~] AWS::Lambda::Function queryHandlerLambda
 └─ [~] Code
     └─ [~] .S3Key:
         ├─ [-] old-hash.zip
         └─ [+] new-hash.zip
```

### 3. Test Locally First

```bash
npm run build  # Ensure no TypeScript errors
npm test       # Run unit tests (if available)
```

### 4. Use Staging Environment

```bash
# Deploy to staging first
STAGE=staging cdk deploy

# Test in staging
# Then deploy to production
STAGE=prod cdk deploy
```

### 5. Monitor Deployment

```bash
# Watch CloudFormation events in real-time
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 10
```

### 6. Verify After Deployment

```bash
# Test API endpoint
curl -X GET "https://YOUR_API/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: YOUR_KEY"

# Check Lambda logs
aws logs tail /aws/lambda/queryHandlerLambda --follow
```

---

## Rollback Procedures

### If Deployment Fails

CDK automatically rolls back failed deployments.

**Manual rollback:**
```bash
# Via CloudFormation Console
# Go to CloudFormation → Stacks → Select stack → Stack actions → Roll back

# Or redeploy previous version
git checkout previous-commit
npm run build
cdk deploy
```

### If Deployment Succeeds But Has Issues

```bash
# Option 1: Quick fix and redeploy
# Fix the code
npm run build
cdk deploy

# Option 2: Rollback to previous version
git revert HEAD
npm run build
cdk deploy

# Option 3: Complete teardown and redeploy
cdk destroy
bash scripts/full-deploy.sh
```

---

## Deployment Checklist

Before redeploying:

- [ ] Code changes tested locally
- [ ] TypeScript compiles without errors (`npm run build`)
- [ ] Reviewed changes with `cdk diff`
- [ ] Backed up important data (if schema changes)
- [ ] Notified team (if production deployment)
- [ ] Ready to monitor logs after deployment

After redeploying:

- [ ] Deployment completed successfully
- [ ] API endpoints responding
- [ ] Lambda functions executing without errors
- [ ] CloudWatch logs show no errors
- [ ] Frontend integration still works
- [ ] Database queries returning expected results

---

## Quick Reference Commands

```bash
# Preview changes
cdk diff

# Build TypeScript
npm run build

# Deploy changes
cdk deploy

# Deploy without confirmation
cdk deploy --require-approval never

# Deploy to specific stage
STAGE=prod cdk deploy

# Full automated redeploy
bash scripts/full-deploy.sh --skip-populate

# Refresh database only (no deploy)
npm run populate-db

# View deployment status
aws cloudformation describe-stacks --stack-name CommandCenterBackendStack

# Rollback (destroy and redeploy)
cdk destroy
bash scripts/full-deploy.sh
```

---

## Continuous Deployment

For automated deployments, consider:

### GitHub Actions Example

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'command-center-backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd command-center-backend
          npm install
      
      - name: Build
        run: |
          cd command-center-backend
          npm run build
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy
        run: |
          cd command-center-backend
          cdk deploy --require-approval never
```

---

## Cost Considerations

Each deployment incurs minimal costs:

- **CloudFormation**: Free
- **Lambda deployments**: Free (just updates code)
- **API Gateway**: No additional cost for updates
- **DynamoDB**: No cost for schema updates (unless recreating table)

**Estimated cost per deployment:** $0.00 - $0.01

---

## Troubleshooting Redeployment Issues

### "No changes detected"

This is normal! CDK detected no infrastructure changes.

```bash
# Force Lambda code update
cdk deploy --force
```

### "Resource already exists"

Usually means a previous deployment failed partially.

```bash
# Complete the deployment
cdk deploy

# Or start fresh
cdk destroy
bash scripts/full-deploy.sh
```

### "Insufficient permissions"

Your IAM user needs update permissions for the resources being changed.

```bash
# Check your permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### "Lambda function too large"

Lambda deployment package exceeds 50MB limit.

```bash
# Check package size
cd lambda
du -sh node_modules

# Solution: Use Lambda layers or reduce dependencies
```

---

## Summary

### Simple Rule:
**Changed code or infrastructure? → Run `cdk deploy`**  
**Changed data only? → Run `npm run populate-db`**

### Quick Redeploy:
```bash
npm run build && cdk deploy
```

### Full Redeploy:
```bash
bash scripts/full-deploy.sh --skip-populate
```

That's it! CDK handles the complexity for you.
