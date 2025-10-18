# Multi-Agent Orchestration System - Deployment Documentation

## Overview

This document provides a complete reference for deploying the Multi-Agent Orchestration System using AWS CDK and the provided automation scripts.

## Quick Reference

### One-Command Deployment

```bash
cd infrastructure
npm run deploy:full
```

**Duration:** 25-30 minutes  
**What it does:** Complete automated deployment from prerequisites check to smoke tests

### Deployment Commands

| Command | Purpose | Duration |
|---------|---------|----------|
| `npm run check-readiness` | Verify prerequisites | 1 min |
| `npm run deploy:full` | Full automated deployment | 25-30 min |
| `npm run deploy` | Deploy CDK stacks only | 20-25 min |
| `npm run seed-data` | Load sample data | 2-3 min |
| `npm run smoke-test` | Verify deployment | 1-2 min |
| `npm run destroy` | Delete all resources | 10-15 min |

## Prerequisites

### Required Software

- **Node.js 18+**: JavaScript runtime for CDK
- **Python 3.11+**: Runtime for Lambda functions
- **AWS CLI v2**: AWS command-line interface
- **AWS CDK CLI**: Infrastructure as Code tool (`npm install -g aws-cdk`)

### AWS Account Requirements

- Active AWS account with admin access
- Configured AWS credentials (`aws configure`)
- Sufficient service quotas:
  - RDS instances: 1+
  - OpenSearch domains: 1+
  - Lambda concurrent executions: 20+
  - VPC resources: 1 VPC with subnets

### Verify Prerequisites

```bash
cd infrastructure
npm run check-readiness
```

This will check all prerequisites and report any issues.

## Deployment Scripts

### 1. check-readiness.sh

**Purpose:** Verify environment is ready for deployment

**Usage:**
```bash
npm run check-readiness
```

**Checks:**
- ✓ Node.js version (18+)
- ✓ Python version (3.11+)
- ✓ AWS CLI installed
- ✓ AWS CDK CLI installed
- ✓ AWS credentials configured
- ✓ .env file exists
- ✓ Dependencies installed
- ✓ CDK bootstrapped

**Exit Codes:**
- 0: Ready to deploy
- 1: Issues found (see output)

### 2. deploy.sh

**Purpose:** Automated full deployment

**Usage:**
```bash
npm run deploy:full
```

**Steps:**
1. Check prerequisites
2. Load environment configuration
3. Install dependencies
4. Bootstrap CDK (if needed)
5. Deploy all stacks:
   - Auth Stack (Cognito)
   - Storage Stack (S3)
   - Data Stack (RDS, DynamoDB, OpenSearch)
   - API Stack (API Gateway, Lambda)
   - Orchestration Stack (Step Functions)
   - Realtime Stack (AppSync)
6. Initialize database schema
7. Initialize OpenSearch indices
8. Create test user (testuser/TestPassword123!)
9. Display stack outputs

**Duration:** 25-30 minutes

**Outputs:**
- API URL
- User Pool ID and Client ID
- Database endpoint
- OpenSearch endpoint
- S3 bucket names

### 3. seed-data.sh

**Purpose:** Load sample configurations and test data

**Usage:**
```bash
npm run seed-data
```

**Prerequisites:**
- Stacks must be deployed
- Database and OpenSearch initialized
- Test user must exist

**What it loads:**
1. **Tool Registry:**
   - Amazon Bedrock
   - AWS Comprehend
   - Amazon Location Service
   - Web Search API
   - Data Query APIs
   - Vector Search

2. **Agent Configurations:**
   - Geo Agent (location extraction)
   - Temporal Agent (time/date extraction)
   - Entity Agent (entity recognition)
   - Severity Classifier (custom agent)

3. **Query Agents:**
   - When Agent (temporal analysis)
   - Where Agent (spatial analysis)
   - Why Agent (causal analysis)
   - How Agent (method analysis)
   - What Agent (entity analysis)
   - Who Agent (person analysis)
   - Which Agent (selection analysis)
   - How Many Agent (count analysis)
   - How Much Agent (quantity analysis)
   - From Where Agent (origin analysis)
   - What Kind Agent (type analysis)

4. **Playbooks:**
   - Civic Complaints ingestion playbook
   - Civic Complaints query playbook

5. **Dependency Graphs:**
   - Ingestion pipeline dependencies
   - Query pipeline dependencies

6. **Sample Data:**
   - 3 civic complaint incidents

**Duration:** 2-3 minutes

### 4. smoke-test.sh

**Purpose:** Comprehensive deployment verification

**Usage:**
```bash
npm run smoke-test
```

**Tests:**
- ✓ CloudFormation stacks exist and healthy
- ✓ Cognito User Pool enabled
- ✓ Test user exists
- ✓ S3 buckets accessible
- ✓ DynamoDB tables active
- ✓ RDS database available
- ✓ OpenSearch domain active
- ✓ Authentication works (JWT generation)
- ✓ API Gateway reachable
- ✓ Lambda functions deployed
- ✓ Config API responds
- ✓ Ingest API accepts requests

**Duration:** 1-2 minutes

**Exit Codes:**
- 0: All tests passed
- 1: Some tests failed

## Deployment Workflow

### Automated Deployment (Recommended)

```bash
# Step 1: Check prerequisites
npm run check-readiness

# Step 2: Deploy everything
npm run deploy:full

# Step 3: Load sample data
npm run seed-data

# Step 4: Verify deployment
npm run smoke-test
```

### Manual Deployment

```bash
# Step 1: Check prerequisites
npm run check-readiness

# Step 2: Install dependencies
npm install
npm run build

# Step 3: Bootstrap CDK (first time only)
cdk bootstrap

# Step 4: Deploy stacks
npm run deploy

# Step 5: Initialize services
# (Handled automatically by deploy.sh, or manually invoke Lambda functions)

# Step 6: Load seed data
npm run seed-data

# Step 7: Verify
npm run smoke-test
```

## Environment Configuration

### .env File

Create `.env` file in the `infrastructure/` directory:

```bash
# AWS Configuration
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
STAGE=dev

# Optional: Custom configuration
# PROJECT_NAME=MultiAgentOrchestration
# DB_INSTANCE_CLASS=db.t3.medium
# OPENSEARCH_INSTANCE_TYPE=t3.medium.search
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| AWS_ACCOUNT_ID | AWS account ID | Auto-detected | No |
| AWS_REGION | Deployment region | us-east-1 | No |
| STAGE | Environment stage | dev | No |
| PROJECT_NAME | Project name prefix | MultiAgentOrchestration | No |

## Stack Architecture

### Deployment Order

```
1. Auth Stack
   └─ Cognito User Pool
   └─ Lambda Authorizer

2. Storage Stack
   └─ S3 Evidence Bucket
   └─ S3 Config Backup Bucket

3. Data Stack
   └─ RDS PostgreSQL (Multi-AZ)
   └─ DynamoDB Tables (4 tables)
   └─ OpenSearch Domain (2 nodes)
   └─ Database Init Lambda
   └─ OpenSearch Init Lambda

4. API Stack
   └─ API Gateway (REST)
   └─ Lambda Functions (20+ functions)
   └─ Tool Proxies
   └─ Data API Proxies

5. Orchestration Stack
   └─ Step Functions (2 state machines)
   └─ Orchestration Lambdas

6. Realtime Stack
   └─ AppSync API (GraphQL + WebSocket)
   └─ Status Publisher Lambda
```

### Stack Dependencies

```
Auth Stack (no dependencies)
  ↓
Storage Stack (no dependencies)
  ↓
Data Stack (depends on Storage)
  ↓
API Stack (depends on Auth, Data)
  ↓
Orchestration Stack (depends on API, Data)
  ↓
Realtime Stack (depends on Data)
```

## Stack Outputs

After deployment, retrieve important values:

### Auth Stack

```bash
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

**Outputs:**
- UserPoolId
- UserPoolClientId
- AuthorizerFunctionArn

### API Stack

```bash
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Api \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

**Outputs:**
- ApiUrl (e.g., https://abc123.execute-api.us-east-1.amazonaws.com/)
- ApiId

### Data Stack

```bash
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

**Outputs:**
- DatabaseEndpoint
- DatabaseSecretArn
- ConfigurationsTableName
- OpenSearchEndpoint

### Storage Stack

```bash
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Storage \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

**Outputs:**
- EvidenceBucketName
- ConfigBackupBucketName

## Testing the Deployment

### Get JWT Token

```bash
# Set variables
USER_POOL_CLIENT_ID=<from-auth-stack-outputs>
AWS_REGION=us-east-1

# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id ${USER_POOL_CLIENT_ID} \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region ${AWS_REGION} \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo $TOKEN
```

### Test Ingest API

```bash
API_URL=<from-api-stack-outputs>

curl -X POST ${API_URL}api/v1/ingest \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic-complaints",
    "text": "There is a large pothole on Main Street near Oak Avenue",
    "images": []
  }'
```

### Test Query API

```bash
curl -X POST ${API_URL}api/v1/query \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic-complaints",
    "question": "What are the recent pothole complaints?"
  }'
```

### Test Config API

```bash
curl -X GET ${API_URL}api/v1/config/agents \
  -H "Authorization: Bearer ${TOKEN}"
```

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Fails

**Error:** "Unable to resolve AWS account"

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Force re-bootstrap
cdk bootstrap --force
```

#### 2. Stack Deployment Timeout

**Error:** "Resource creation cancelled"

**Solution:**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name MultiAgentOrchestration-dev-Data \
  --max-items 20

# RDS and OpenSearch take 15-20 minutes (normal)
# Wait and monitor CloudFormation console
```

#### 3. Database Initialization Fails

**Error:** Lambda timeout or connection error

**Solution:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Data-DbInit --follow

# Wait 5 minutes for database to be ready, then retry
DB_INIT_FUNCTION=<from-stack-outputs>
aws lambda invoke \
  --function-name ${DB_INIT_FUNCTION} \
  --region us-east-1 \
  response.json
```

#### 4. Smoke Tests Fail

**Error:** Some tests fail

**Solution:**
```bash
# Wait for resources to stabilize
sleep 300

# Re-run smoke tests
npm run smoke-test

# Check specific resource status
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].StackStatus'
```

### Viewing Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/<function-name> --follow

# API Gateway logs
aws logs tail /aws/apigateway/MultiAgentOrchestration-dev-Api --follow

# CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name <stack-name> \
  --max-items 50
```

## Cost Estimation

### Development Environment (us-east-1)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| RDS PostgreSQL | t3.medium, Multi-AZ, 20GB | $120 |
| OpenSearch | 2x t3.medium, 20GB EBS | $150 |
| DynamoDB | On-demand, 1GB storage | $5-20 |
| S3 | 10GB storage | $5 |
| Lambda | 1M invocations, 512MB | $10-20 |
| API Gateway | 1M requests | $3.50 |
| Cognito | 1000 MAU | Free |
| CloudWatch | Logs and metrics | $10 |
| **Total** | | **$300-350** |

### Production Environment

For production with high availability:
- RDS: t3.large Multi-AZ: ~$250/month
- OpenSearch: 3x m5.large: ~$500/month
- Lambda: 10M invocations: ~$100/month
- **Total: ~$1000-1500/month**

### Cost Optimization

For development/testing:
1. Use smaller instances (t3.micro)
2. Single-AZ RDS (not recommended for production)
3. Single-node OpenSearch
4. Delete resources when not in use: `npm run destroy`

## Cleanup

### Delete All Resources

```bash
npm run destroy
```

This will delete all CloudFormation stacks in reverse order.

### Manual Cleanup

Some resources may have RETAIN policy:

```bash
# Delete S3 buckets
aws s3 rb s3://<bucket-name> --force

# Delete RDS snapshots
aws rds delete-db-snapshot --db-snapshot-identifier <snapshot-id>

# Delete CloudWatch log groups
aws logs delete-log-group --log-group-name /aws/lambda/<function-name>
```

### Verify Cleanup

```bash
# Check for remaining stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `MultiAgentOrchestration`)].StackName'

# Check for Lambda functions
aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `MultiAgentOrchestration`)].FunctionName'
```

## Best Practices

### For Development

1. Use automated deployment: `npm run deploy:full`
2. Check readiness first: `npm run check-readiness`
3. Monitor CloudFormation console during deployment
4. Always run smoke tests after deployment
5. Keep .env file secure (never commit to git)

### For Production

1. Use separate AWS accounts (dev, staging, prod)
2. Enable Multi-AZ for RDS and OpenSearch
3. Configure automated backups
4. Set up CloudWatch dashboards and alarms
5. Use larger instances for production load
6. Enable AWS WAF for API Gateway
7. Use private subnets for databases
8. Implement CI/CD pipeline

## Support

For issues or questions:
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Comprehensive guide
- [README.md](./README.md) - Quick reference
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Project Requirements](../.kiro/specs/multi-agent-orchestration-system/requirements.md)
- [Design Document](../.kiro/specs/multi-agent-orchestration-system/design.md)

## Appendix

### Resource Naming Convention

All resources follow this pattern:
```
MultiAgentOrchestration-{STAGE}-{STACK}-{RESOURCE}
```

Examples:
- `MultiAgentOrchestration-dev-Auth-UserPool`
- `MultiAgentOrchestration-dev-Data-PostgresDB`
- `MultiAgentOrchestration-prod-Api-IngestFunction`

### Port Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| RDS PostgreSQL | 5432 | TCP | Database |
| OpenSearch | 443 | HTTPS | Search API |
| API Gateway | 443 | HTTPS | REST API |
| AppSync | 443 | WSS | WebSocket |

### Deployment Timeline

```
0:00  - Start deployment
0:01  - Prerequisites check
0:02  - CDK bootstrap (if needed)
0:05  - Auth Stack deployed
0:07  - Storage Stack deployed
0:25  - Data Stack deployed (RDS + OpenSearch)
0:30  - API Stack deployed
0:33  - Orchestration Stack deployed
0:35  - Realtime Stack deployed
0:37  - Database initialized
0:38  - OpenSearch initialized
0:39  - Test user created
0:40  - Deployment complete ✓
```

### Next Steps

After successful deployment:

1. **Explore the API**: Test endpoints with curl or Postman
2. **Deploy Frontend**: Set up Next.js frontend application
3. **Create Custom Agents**: Use config API for domain-specific agents
4. **Load Real Data**: Replace sample data with actual use case data
5. **Monitor Performance**: Set up CloudWatch dashboards
6. **Scale Resources**: Adjust instance sizes based on load testing
