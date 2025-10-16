# Command Center Backend - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Command Center Backend API to AWS. The deployment uses AWS CDK (Cloud Development Kit) to provision all necessary infrastructure including Lambda functions, DynamoDB tables, API Gateway, and Amazon Bedrock Agent.

---

## Prerequisites

### Required Software

1. **Node.js** (v18 or later)
   ```bash
   node --version  # Should be v18.x or higher
   ```

2. **npm** (comes with Node.js)
   ```bash
   npm --version
   ```

3. **AWS CLI** (v2)
   ```bash
   aws --version
   ```
   Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

4. **AWS CDK CLI**
   ```bash
   npm install -g aws-cdk
   cdk --version
   ```

### AWS Account Setup

1. **AWS Account**: You need an active AWS account with appropriate permissions

2. **AWS Credentials**: Configure AWS CLI with your credentials
   ```bash
   aws configure
   ```
   You'll need:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., `us-east-1`)
   - Default output format (e.g., `json`)

3. **Verify AWS Configuration**
   ```bash
   aws sts get-caller-identity
   ```
   This should return your AWS account details.

---

## Required AWS Permissions

The deploying IAM user/role needs the following permissions:

### Core Services
- **CloudFormation**: Full access (for CDK deployments)
- **IAM**: Create and manage roles and policies
- **Lambda**: Create and manage functions
- **API Gateway**: Create and manage REST APIs
- **DynamoDB**: Create and manage tables
- **Bedrock**: Create and manage agents and action groups
- **CloudWatch**: Create log groups and metrics
- **S3**: Access to CDK bootstrap bucket

### Recommended IAM Policy

For production deployments, use a custom policy. For development/testing, you can use:
- `AdministratorAccess` (full access - use with caution)

Or create a custom policy with these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "iam:*",
        "lambda:*",
        "apigateway:*",
        "dynamodb:*",
        "bedrock:*",
        "logs:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Bedrock Model Access

Ensure your AWS account has access to Amazon Bedrock and the Claude 3 Sonnet model:

1. Go to AWS Console → Bedrock → Model access
2. Request access to "Claude 3 Sonnet" if not already enabled
3. Wait for approval (usually instant for most accounts)

---

## Installation Steps

### 1. Clone and Install Dependencies

```bash
cd command-center-backend
npm install
```

This installs all required dependencies including AWS CDK libraries.

### 2. Bootstrap CDK (First-Time Only)

If this is your first time using CDK in this AWS account/region:

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

Example:
```bash
cdk bootstrap aws://123456789012/us-east-1
```

This creates an S3 bucket and other resources needed for CDK deployments.

### 3. Configure Environment Variables

Create a `.env.local` file in the `command-center-backend` directory:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Application Configuration
ENVIRONMENT=dev
TABLE_NAME=MasterEventTimeline

# Cost Control
BUDGET_LIMIT_USD=50
ALERT_EMAIL=your-email@example.com
```

**Important**: Replace placeholder values with your actual configuration.

### 4. Review CDK Stack Configuration

Open `lib/command-center-backend-stack.ts` and verify:
- Region settings
- Resource naming conventions
- Cost control settings (budget alarms)

---

## Deployment Process

### Step 1: Synthesize CloudFormation Template

Preview what will be deployed:

```bash
cdk synth
```

This generates a CloudFormation template. Review it to ensure everything looks correct.

### Step 2: Deploy Infrastructure

Deploy the full stack:

```bash
cdk deploy
```

You'll see a summary of changes. Type `y` to confirm.

**Deployment time**: Approximately 5-10 minutes

The deployment will create:
- DynamoDB table (MasterEventTimeline)
- 4 Lambda functions (updates, query, action, tool handlers)
- API Gateway REST API
- Bedrock Agent with Action Group
- IAM roles and policies
- CloudWatch log groups
- Cost monitoring alarms

### Step 3: Note Deployment Outputs

After successful deployment, CDK will output important values:

```
Outputs:
CommandCenterBackendStack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com/prod
CommandCenterBackendStack.ApiKeyId = xyz789
CommandCenterBackendStack.TableName = MasterEventTimeline
CommandCenterBackendStack.AgentId = AGENT123
```

**Save these values** - you'll need them for configuration and testing.

### Step 4: Retrieve API Key

Get your API key value:

```bash
aws apigateway get-api-key --api-key YOUR_API_KEY_ID --include-value
```

Or use the AWS Console:
1. Go to API Gateway → API Keys
2. Find your key
3. Click "Show" to reveal the value

---

## Post-Deployment Configuration

### 1. Populate Database with Simulation Data

Run the data population script:

```bash
npm run populate-db
```

Or manually:

```bash
cd scripts
ts-node populate-database.ts
```

This will:
- Generate 7 days of simulation data
- Insert events into DynamoDB
- Verify data integrity

**Expected time**: 2-3 minutes

### 2. Verify Database Population

Check that data was inserted:

```bash
aws dynamodb scan \
  --table-name MasterEventTimeline \
  --select COUNT
```

You should see a count of events (typically 500-1000 events).

### 3. Configure Bedrock Agent

The Bedrock Agent is created automatically, but you may want to verify its configuration:

1. Go to AWS Console → Bedrock → Agents
2. Find your agent (CommandCenterAgent)
3. Verify:
   - Model: Claude 3 Sonnet
   - Action Group: databaseQueryTool is configured
   - Lambda association: Points to databaseQueryToolLambda

### 4. Test Agent in Bedrock Console

Before testing via API, test the agent directly:

1. In Bedrock Console, open your agent
2. Click "Test" in the right panel
3. Try queries like:
   - "What are the most urgent needs?"
   - "Show me medical incidents"
4. Verify the agent can invoke the tool and return results

---

## Verification and Testing

### 1. Test API Endpoints

#### Test Updates Endpoint

```bash
curl -X GET "https://YOUR_API_ENDPOINT/data/updates?since=2023-02-06T00:00:00Z" \
  -H "x-api-key: YOUR_API_KEY"
```

Expected: JSON response with event updates

#### Test Query Endpoint

```bash
curl -X POST "https://YOUR_API_ENDPOINT/agent/query" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the most urgent needs right now?"
  }'
```

Expected: JSON response with AI-generated answer and map data

#### Test Action Endpoint

```bash
curl -X POST "https://YOUR_API_ENDPOINT/agent/action" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "actionId": "SHOW_CRITICAL_INCIDENTS"
  }'
```

Expected: JSON response with critical incidents

### 2. Run Integration Tests

```bash
npm run test:integration
```

This runs the full integration test suite against your deployed API.

### 3. Run End-to-End Tests

```bash
npm run test:e2e
```

This tests complete workflows including agent interactions.

### 4. Monitor CloudWatch Logs

Check logs for any errors:

```bash
# View logs for updates handler
aws logs tail /aws/lambda/updatesHandlerLambda --follow

# View logs for query handler
aws logs tail /aws/lambda/queryHandlerLambda --follow
```

---

## Configuration Reference

### Environment Variables

Lambda functions receive these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TABLE_NAME` | DynamoDB table name | `MasterEventTimeline` |
| `AGENT_ID` | Bedrock Agent ID | `AGENT123ABC` |
| `AGENT_ALIAS_ID` | Bedrock Agent Alias ID | `TSTALIASID` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `AWS_REGION` | AWS region | `us-east-1` |

### DynamoDB Configuration

- **Table Name**: MasterEventTimeline
- **Partition Key**: Day (String)
- **Sort Key**: Timestamp (String)
- **GSI**: domain-timestamp-index
- **Billing Mode**: PAY_PER_REQUEST (on-demand)
- **Encryption**: AWS managed keys

### API Gateway Configuration

- **Type**: REST API
- **Stage**: prod
- **Authentication**: API Key
- **CORS**: Enabled for dashboard origins
- **Throttling**: 100 requests/minute (default)

### Cost Controls

The deployment includes automatic cost monitoring:

- **Budget Alarm**: Triggers at $50 USD
- **SNS Notification**: Sends email alert
- **Auto-Shutdown**: Optional (configure in stack)

---

## Updating the Deployment

### Update Application Code

After making code changes:

```bash
# 1. Build TypeScript
npm run build

# 2. Deploy changes
cdk deploy
```

CDK will only update changed resources.

### Update Agent Instructions

To update the Bedrock Agent's instruction prompt:

1. Edit the prompt in `lib/command-center-backend-stack.ts`
2. Deploy: `cdk deploy`
3. Test changes in Bedrock Console

### Update Database Schema

**Warning**: Schema changes require careful migration planning.

For adding attributes:
1. Update TypeScript interfaces in `lib/types/`
2. Update Lambda code to handle new fields
3. Deploy: `cdk deploy`
4. Backfill data if needed

---

## Rollback Procedures

### Rollback to Previous Version

If deployment fails or causes issues:

```bash
# List previous versions
aws cloudformation describe-stacks --stack-name CommandCenterBackendStack

# Rollback via CDK (if possible)
cdk deploy --rollback

# Or via CloudFormation Console
# Go to CloudFormation → Stacks → Select stack → Stack actions → Roll back
```

### Emergency Shutdown

To quickly shut down all resources:

```bash
cdk destroy
```

**Warning**: This deletes all resources including data. Use with caution.

---

## Troubleshooting

### Issue: CDK Bootstrap Fails

**Error**: `Need to perform AWS calls for account XXX, but no credentials configured`

**Solution**:
```bash
aws configure
# Enter your credentials
cdk bootstrap
```

### Issue: Deployment Fails - Insufficient Permissions

**Error**: `User: arn:aws:iam::XXX:user/YYY is not authorized to perform: XXX`

**Solution**:
- Verify IAM permissions (see Required AWS Permissions section)
- Ensure you have CloudFormation, Lambda, API Gateway, DynamoDB, and Bedrock permissions

### Issue: Bedrock Model Access Denied

**Error**: `Access denied to model anthropic.claude-3-sonnet`

**Solution**:
1. Go to AWS Console → Bedrock → Model access
2. Request access to Claude 3 Sonnet
3. Wait for approval (usually instant)
4. Redeploy: `cdk deploy`

### Issue: API Returns 403 Forbidden

**Error**: `{"message":"Forbidden"}`

**Solution**:
- Verify you're including the API key in the `x-api-key` header
- Check that the API key is valid: `aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value`
- Ensure the API key is associated with the usage plan

### Issue: Agent Queries Timeout

**Error**: Agent queries take too long or timeout

**Solution**:
- Check CloudWatch logs for the queryHandlerLambda
- Verify the Bedrock Agent can invoke the tool Lambda
- Check tool Lambda logs for errors
- Increase Lambda timeout in CDK stack (default: 30s)

### Issue: Database Queries Slow

**Error**: Updates endpoint takes > 1 second

**Solution**:
- Verify GSI is created: `aws dynamodb describe-table --table-name MasterEventTimeline`
- Check DynamoDB metrics in CloudWatch
- Consider switching to provisioned capacity if on-demand is throttling

### Issue: High Costs

**Error**: AWS bill higher than expected

**Solution**:
- Check CloudWatch dashboard for usage metrics
- Verify budget alarm is configured
- Review Bedrock Agent invocation count (most expensive component)
- Consider reducing test query frequency
- Use `cdk destroy` to tear down when not in use

### Issue: Lambda Cold Starts

**Error**: First request after idle period is slow

**Solution**:
- This is normal for serverless
- Consider provisioned concurrency for production (increases cost)
- Implement warming strategy if needed

---

## Monitoring and Maintenance

### CloudWatch Dashboard

Access the auto-created dashboard:

1. Go to CloudWatch → Dashboards
2. Find "CommandCenterBackend-Dashboard"
3. Monitor:
   - API request count and latency
   - Lambda invocations and errors
   - DynamoDB read/write capacity
   - Bedrock Agent invocations

### Log Analysis

View logs for debugging:

```bash
# Recent errors across all functions
aws logs filter-log-events \
  --log-group-name /aws/lambda/queryHandlerLambda \
  --filter-pattern "ERROR"

# Tail live logs
aws logs tail /aws/lambda/queryHandlerLambda --follow
```

### Cost Monitoring

Check current costs:

```bash
# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

Or use AWS Cost Explorer in the console.

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Review and adjust budget limits
- [ ] Configure production API keys (separate from dev)
- [ ] Set up proper CORS origins for production dashboard
- [ ] Enable API Gateway access logging
- [ ] Configure CloudWatch alarms for errors and latency
- [ ] Set up SNS notifications for critical alerts
- [ ] Review IAM roles for least privilege
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Document API endpoint and key for frontend team
- [ ] Run full integration and e2e test suite
- [ ] Perform load testing
- [ ] Set up backup and disaster recovery procedures
- [ ] Configure proper log retention policies
- [ ] Review and optimize Lambda memory allocation
- [ ] Enable AWS X-Ray for distributed tracing (optional)

---

## Cleanup and Teardown

### Remove All Resources

To completely remove the deployment:

```bash
cdk destroy
```

This will:
- Delete all Lambda functions
- Delete API Gateway
- Delete DynamoDB table (and all data)
- Delete Bedrock Agent
- Delete IAM roles
- Delete CloudWatch log groups (after retention period)

**Warning**: This is irreversible. All data will be lost.

### Partial Cleanup

To keep some resources:

1. Manually delete specific resources in AWS Console
2. Or modify the CDK stack to remove specific constructs
3. Deploy: `cdk deploy`

---

## Support and Resources

### AWS Documentation
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)

### Project Documentation
- API Documentation: `API_DOCUMENTATION.md`
- Requirements: `.kiro/specs/command-center-backend/requirements.md`
- Design: `.kiro/specs/command-center-backend/design.md`

### Getting Help
- Check CloudWatch logs for detailed error messages
- Review the Troubleshooting section above
- Contact: [Your team contact information]

---

## Appendix: Deployment Scripts

### Quick Deploy Script

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "Building application..."
npm run build

echo "Running tests..."
npm test

echo "Deploying to AWS..."
cdk deploy --require-approval never

echo "Deployment complete!"
echo "Run 'npm run populate-db' to populate the database."
```

Make it executable:
```bash
chmod +x scripts/deploy.sh
```

### Complete Setup Script

Create `scripts/setup.sh`:

```bash
#!/bin/bash
set -e

echo "=== Command Center Backend Setup ==="

echo "1. Installing dependencies..."
npm install

echo "2. Building application..."
npm run build

echo "3. Deploying infrastructure..."
cdk deploy

echo "4. Populating database..."
npm run populate-db

echo "5. Running tests..."
npm run test:integration

echo "=== Setup Complete ==="
echo "Your API is ready to use!"
```

---

**Last Updated**: [Current Date]
**Version**: 1.0.0
