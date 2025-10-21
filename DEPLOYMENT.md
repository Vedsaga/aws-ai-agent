# Deployment Guide

**Deployment Time:** ~5 minutes  
**Status:** ✅ Production Ready

---

## Quick Start

### One-Command Deployment

```bash
chmod +x DEPLOY.sh
./DEPLOY.sh
```

This script will:
1. Check prerequisites (AWS CLI, Python, credentials)
2. Deploy/update all Lambda functions
3. Verify infrastructure status
4. Test all API endpoints
5. Display deployment summary

---

## Prerequisites

### Required Software
- AWS CLI (configured with credentials)
- Python 3.11+
- Node.js 18+ (for frontend)
- Git

### AWS Account Setup
```bash
# Configure AWS credentials
aws configure

# Verify credentials
aws sts get-caller-identity
```

---

## Infrastructure Overview

### Deployed Resources

**API Gateway:**
- API ID: `vluqfpl2zi`
- Base URL: `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`

**Lambda Functions:**
- ConfigHandler - Agent/domain management
- IngestHandler - Report processing
- QueryHandler - Question processing
- Orchestrator - Multi-agent coordination
- Authorizer - JWT validation

**Data Storage:**
- DynamoDB - Configuration storage (6 tables)
- RDS PostgreSQL - Incident and query data
- S3 - File storage

**Authentication:**
- Cognito User Pool ID: `us-east-1_7QZ7Y6Gbl`
- Client ID: `6gobbpage9af3nd7ahm3lchkct`
- Test User: `testuser` / `TestPassword123!`

---

## Deployment Steps

### 1. Deploy Backend

```bash
./DEPLOY.sh
```

**What it does:**
- Updates Lambda function code
- Verifies all services are running
- Tests API endpoints
- Creates test user if needed

**Expected output:**
```
✓ Deployment Complete!

API Endpoint:
  https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1

Test Credentials:
  Username: testuser
  Password: TestPassword123!
```

### 2. Setup Frontend

```bash
cd infrastructure/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend URL:** `http://localhost:3000`

### 3. Verify Deployment

```bash
# Test APIs
cd infrastructure
python3 TEST.py

# Expected: 11/11 tests passed
```

---

## Environment Configuration

### Frontend Environment Variables

File: `infrastructure/frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_7QZ7Y6Gbl
NEXT_PUBLIC_COGNITO_CLIENT_ID=6gobbpage9af3nd7ahm3lchkct
NEXT_PUBLIC_COGNITO_REGION=us-east-1
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

---

## Troubleshooting

### Issue: DEPLOY.sh fails

**Check AWS credentials:**
```bash
aws sts get-caller-identity
```

**Check if infrastructure exists:**
```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `MultiAgent`)].StackName'
```

**If stacks don't exist, deploy infrastructure first:**
```bash
cd infrastructure
npm install
npm run build
cdk deploy --all
```

### Issue: Frontend won't start

**Solution:**
```bash
cd infrastructure/frontend
rm -rf .next node_modules
npm install
npm run dev
```

### Issue: Login fails

**Reset test user password:**
```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_7QZ7Y6Gbl \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1
```

### Issue: API returns 500 error

**Check Lambda logs:**
```bash
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler \
  --follow --region us-east-1
```

**Redeploy:**
```bash
./DEPLOY.sh
```

---

## Initial Infrastructure Deployment

If this is your first deployment and infrastructure doesn't exist:

### 1. Install CDK Dependencies

```bash
cd infrastructure
npm install
```

### 2. Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://ACCOUNT_ID/us-east-1
```

Replace `ACCOUNT_ID` with your AWS account ID.

### 3. Deploy All Stacks

```bash
cdk deploy --all --require-approval never
```

This will create:
- Auth Stack (Cognito)
- Storage Stack (S3)
- Data Stack (DynamoDB, RDS)
- API Stack (API Gateway, Lambda)

**Deployment time:** ~25-30 minutes

### 4. Create Test User

```bash
# Get User Pool ID from stack outputs
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPassword123! \
  --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1
```

### 5. Run Deployment Script

```bash
cd ..
./DEPLOY.sh
```

---

## Monitoring

### View Lambda Logs

```bash
# Config Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler --follow

# Ingest Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-IngestHandler --follow

# Query Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-QueryHandler --follow

# Orchestrator
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator --follow
```

### Check API Gateway Metrics

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=MultiAgentOrchestration-dev-Api-RestApi \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## Cost Management

### Stop RDS When Not in Use

```bash
# Stop RDS
./infrastructure/scripts/stop-rds.sh

# Start RDS
./infrastructure/scripts/start-rds.sh
```

### Estimated Costs

- **Development:** $35-40/month
- **Production (low traffic):** $50-75/month
- **Production (high traffic):** $150-300/month

---

## Cleanup

### Remove All Resources

```bash
cd infrastructure
cdk destroy --all
```

**Warning:** This deletes all data permanently!

---

## Production Deployment

### Differences from Development

1. **Multi-AZ RDS** - Enable for high availability
2. **WAF** - Add Web Application Firewall
3. **Custom Domain** - Use Route53 and ACM certificate
4. **Enhanced Monitoring** - CloudWatch dashboards and alarms
5. **Automated Backups** - RDS and DynamoDB backups
6. **Secrets Manager** - Store all credentials securely
7. **VPC Configuration** - Private subnets with NAT Gateway

### Production Checklist

- [ ] Enable CloudTrail logging
- [ ] Configure CloudWatch alarms
- [ ] Set up SNS notifications
- [ ] Enable AWS Config rules
- [ ] Configure backup policies
- [ ] Set up disaster recovery
- [ ] Enable encryption at rest
- [ ] Configure VPC endpoints
- [ ] Set up CI/CD pipeline
- [ ] Document runbooks

---

## Common Commands

```bash
# Deploy system
./DEPLOY.sh

# Test APIs
cd infrastructure && python3 TEST.py

# Start frontend
cd infrastructure/frontend && npm run dev

# View logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler --follow

# Reset password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_7QZ7Y6Gbl \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1

# Get JWT token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1
```

---

## Success Criteria

### Deployment Successful When:
- ✅ `./DEPLOY.sh` completes without errors
- ✅ All API tests pass (11/11) - run `cd infrastructure && python3 TEST.py`
- ✅ Frontend starts on localhost:3000
- ✅ Can login with test credentials
- ✅ Can submit reports
- ✅ Can ask questions
- ✅ Can create custom agents

---

## Support

**Scripts:**
- `./DEPLOY.sh` - Deploy/update system
- `infrastructure/TEST.py` - Test all APIs

**Documentation:**
- `README.md` - Project overview
- `infrastructure/API_DOCUMENTATION.md` - API reference and testing
- `DEPLOYMENT.md` - This file

---

**Status:** ✅ Ready for Deployment  
**Last Updated:** October 21, 2025
