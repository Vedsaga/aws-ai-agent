# Deployment In Progress ✅

## Current Status

Your deployment is running successfully! The IAM policy issue has been fixed.

## What's Happening Now

### Step 1: CDK Bootstrap (Currently Running)
- Creating CDKToolkit CloudFormation stack
- Setting up S3 bucket for CDK assets
- Creating IAM roles for CDK deployments
- **Time:** 2-3 minutes

### Step 2: Building Application (Next)
- Compiling TypeScript to JavaScript
- Packaging Lambda functions
- **Time:** 30 seconds

### Step 3: Deploying Infrastructure (After Build)
- Creating DynamoDB table
- Creating 4 Lambda functions
- Creating API Gateway
- Creating Bedrock Agent
- Creating IAM roles and policies
- **Time:** 5-8 minutes

### Step 4: Populating Database (Final)
- Inserting 7 days of simulation data
- **Time:** 2-3 minutes

## Total Expected Time
**10-15 minutes** for first deployment

---

## What Was Fixed

### The Issue
```
[CommandCenterBackend-Dev/ToolLambdaRole/DefaultPolicy] 
A PolicyStatement used in an identity-based policy cannot specify any IAM principals.
```

### The Fix
Removed the incorrect IAM policy statement from `toolLambdaRole`. The permission for Bedrock to invoke the Lambda function is now correctly added as a resource-based policy on the Lambda function itself (in the `createDatabaseQueryToolLambda` method).

**Changed:**
```typescript
// BEFORE (Incorrect - identity-based policy with principals)
this.toolLambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  principals: [new iam.ServicePrincipal('bedrock.amazonaws.com')],
  actions: ['lambda:InvokeFunction'],
  resources: ['*'],
}));

// AFTER (Correct - resource-based policy on Lambda)
// Permission added in createDatabaseQueryToolLambda():
toolLambda.grantInvoke(new iam.ServicePrincipal('bedrock.amazonaws.com'));
```

---

## Monitoring the Deployment

### Watch the Script Output
The script will show progress through 8 steps:
```
[1/8] Checking AWS credentials... ✓
[2/8] Checking Bedrock model access... ✓
[3/8] Checking CDK bootstrap status... (in progress)
[4/8] Installing dependencies...
[5/8] Building TypeScript...
[6/8] Deploying CDK stack...
[7/8] Retrieving deployment info...
[8/8] Populating database...
```

### Check CloudFormation Console (Optional)
1. Go to: https://console.aws.amazon.com/cloudformation/
2. Look for stacks:
   - `CDKToolkit` (bootstrap stack)
   - `CommandCenterBackendStack` (main stack)

### View Real-Time Progress
```bash
# In another terminal, watch CloudFormation events
watch -n 5 'aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 5 \
  --query "StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]" \
  --output table'
```

---

## What to Expect After Deployment

### Success Output
```
═══════════════════════════════════════════════════════════
                    DEPLOYMENT OUTPUTS
═══════════════════════════════════════════════════════════

API Endpoint:
  https://xxxxx.execute-api.us-east-1.amazonaws.com/prod

API Key ID:
  abc123xyz

API Key Value:
  xxxxxxxxxxxxxxxxxxxxxxxxxx

DynamoDB Table:
  CommandCenterBackend-Dev-MasterEventTimeline

Bedrock Agent ID:
  XXXXXXXXXX

═══════════════════════════════════════════════════════════
            DEPLOYMENT COMPLETED SUCCESSFULLY
═══════════════════════════════════════════════════════════
```

### Files Created
- `.env.local` - Contains API credentials (auto-generated)

### Resources Created in AWS
- ✅ DynamoDB table with 7 days of data
- ✅ 4 Lambda functions
- ✅ API Gateway REST API
- ✅ Bedrock Agent
- ✅ IAM roles and policies
- ✅ CloudWatch log groups
- ✅ Cost monitoring alarms

---

## If Deployment Fails

### Common Issues

#### 1. Bedrock Access Denied
**Error:** `Access denied to model anthropic.claude-3-sonnet`

**Solution:**
1. Go to: https://console.aws.amazon.com/bedrock/
2. Click: Model access → Manage model access
3. Check: Claude 3 Sonnet
4. Click: Request model access
5. Wait for approval (usually instant)
6. Re-run: `bash scripts/full-deploy.sh`

#### 2. Insufficient Permissions
**Error:** `User is not authorized to perform: XXX`

**Solution:**
- Ensure your IAM user has Administrator access or required permissions
- Check with your AWS account administrator

#### 3. Resource Limit Exceeded
**Error:** `LimitExceededException`

**Solution:**
- Check AWS service quotas
- Request limit increase if needed

### View Error Details
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name CommandCenterBackendStack \
  --max-items 20

# Check CDK output
cdk deploy --verbose
```

### Retry Deployment
```bash
# After fixing the issue
bash scripts/full-deploy.sh
```

---

## Next Steps After Successful Deployment

### 1. Test the API
```bash
# Load credentials
source .env.local

# Test updates endpoint
curl -X GET "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: ${API_KEY}"
```

### 2. Configure Frontend
Copy values from `command-center-backend/.env.local` to your frontend:
```bash
# command-center-dashboard/.env.local
NEXT_PUBLIC_API_ENDPOINT=<from backend .env.local>
NEXT_PUBLIC_API_KEY=<from backend .env.local>
```

### 3. Run Integration Tests
```bash
npm run test:integration
```

### 4. View Logs
```bash
aws logs tail /aws/lambda/queryHandlerLambda --follow
```

---

## Deployment Warnings (Safe to Ignore)

You may see these deprecation warnings - they're safe to ignore:

```
[WARNING] aws-cdk-lib.aws_dynamodb.TableOptions#pointInTimeRecovery is deprecated.
[WARNING] aws-cdk-lib.aws_lambda.FunctionOptions#logRetention is deprecated.
```

These are CDK library deprecation notices and don't affect functionality.

---

## Questions?

- **How long will this take?** 10-15 minutes for first deployment
- **Can I stop it?** Press Ctrl+C, but you'll need to clean up with `cdk destroy`
- **What if it fails?** Check error message, fix issue, re-run script
- **Can I watch progress?** Yes, check CloudFormation console or use AWS CLI

---

## Support

- **Pre-deployment:** See `PRE_DEPLOYMENT_CHECKLIST.md`
- **Redeployment:** See `REDEPLOYMENT_GUIDE.md`
- **Full docs:** See `DEPLOYMENT_GUIDE.md`
- **Quick start:** See `START_HERE.md`

---

**Status:** Deployment in progress... ⏳

Let the script complete. It will show success message when done!
