# Multi-Agent Orchestration System - Complete Deployment Guide

This guide provides comprehensive instructions for deploying the Multi-Agent Orchestration System to AWS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Cost Estimation](#cost-estimation)
8. [Cleanup](#cleanup)

## Prerequisites

### Required Software

- **Node.js 18+**: [Download](https://nodejs.org/)
- **Python 3.11+**: [Download](https://www.python.org/)
- **AWS CLI v2**: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS CDK CLI**: Install with `npm install -g aws-cdk`
- **Git**: For cloning the repository

### AWS Account Requirements

- Active AWS account with administrative access
- AWS credentials configured locally
- Sufficient service limits for:
  - RDS instances (1x t3.medium or larger)
  - OpenSearch domains (2x t3.medium nodes)
  - Lambda functions (20+ concurrent executions)
  - API Gateway (1 REST API)
  - Cognito User Pools (1 pool)

### Verify Prerequisites

```bash
# Check Node.js version
node --version  # Should be v18.0.0 or higher

# Check Python version
python3 --version  # Should be 3.11 or higher

# Check AWS CLI
aws --version  # Should be aws-cli/2.x.x

# Check CDK CLI
cdk --version  # Should be 2.100.0 or higher

# Verify AWS credentials
aws sts get-caller-identity
```

## Quick Start

For the fastest deployment experience:

```bash
# 1. Clone the repository
git clone <repository-url>
cd infrastructure

# 2. Configure environment
cp .env.example .env
# Edit .env with your AWS account details

# 3. Run automated deployment
npm run deploy:full
```

**Total time: ~30 minutes**

The automated script will handle everything including:
- Dependency installation
- CDK bootstrapping
- Stack deployment
- Database initialization
- Test user creation

## Detailed Deployment Steps

### Step 1: Environment Configuration

```bash
cd infrastructure

# Copy environment template
cp .env.example .env
```

Edit `.env` file:

```bash
# AWS Configuration
AWS_ACCOUNT_ID=123456789012  # Your AWS account ID
AWS_REGION=us-east-1         # Deployment region
STAGE=dev                    # Environment stage (dev/staging/prod)

# Optional: Custom configuration
# PROJECT_NAME=MultiAgentOrchestration
# DB_INSTANCE_CLASS=db.t3.medium
# OPENSEARCH_INSTANCE_TYPE=t3.medium.search
```

### Step 2: Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Build TypeScript
npm run build
```

### Step 3: Bootstrap CDK

First-time setup for your AWS account:

```bash
# Set environment variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Bootstrap CDK
cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION}
```

**Note**: Bootstrapping only needs to be done once per account/region combination.

### Step 4: Review Infrastructure

Before deploying, review what will be created:

```bash
# Generate CloudFormation templates
npm run synth

# View differences (if updating existing deployment)
npm run diff
```

### Step 5: Deploy Stacks

Deploy all stacks:

```bash
npm run deploy
```

Or deploy individually in order:

```bash
# 1. Authentication (Cognito)
cdk deploy MultiAgentOrchestration-dev-Auth

# 2. Storage (S3 buckets)
cdk deploy MultiAgentOrchestration-dev-Storage

# 3. Data layer (RDS, DynamoDB, OpenSearch)
cdk deploy MultiAgentOrchestration-dev-Data

# 4. API layer (API Gateway, Lambda)
cdk deploy MultiAgentOrchestration-dev-Api
```

**Deployment time**: 25-30 minutes total

### Step 6: Initialize Database

After stacks are deployed, initialize the database schema:

```bash
# Get function name
DB_INIT_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs[?OutputKey==`DbInitFunctionName`].OutputValue' \
  --output text)

# Invoke initialization
aws lambda invoke \
  --function-name ${DB_INIT_FUNCTION} \
  --region us-east-1 \
  db-init-response.json

# Check result
cat db-init-response.json
```

### Step 7: Initialize OpenSearch

Initialize OpenSearch indices:

```bash
# Get function name
OS_INIT_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchInitFunctionName`].OutputValue' \
  --output text)

# Invoke initialization
aws lambda invoke \
  --function-name ${OS_INIT_FUNCTION} \
  --region us-east-1 \
  os-init-response.json

# Check result
cat os-init-response.json
```

### Step 8: Create Test User

Create a test user for API access:

```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser \
  --user-attributes \
    Name=email,Value=test@example.com \
    Name=custom:tenant_id,Value=test-tenant-123 \
  --temporary-password TempPassword123! \
  --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1
```

## Post-Deployment Configuration

### Load Seed Data

Load sample configurations and test data:

```bash
npm run seed-data
```

This will:
1. Populate tool registry with built-in tools
2. Create sample agent configurations (Geo, Temporal, Entity agents)
3. Set up playbooks for civic complaints domain
4. Create dependency graphs
5. Insert sample incident data

### Retrieve Stack Outputs

Get important deployment values:

```bash
# API URL
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# User Pool ID
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Database Endpoint
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text
```

### Configure Frontend (Optional)

If deploying the frontend application:

```bash
cd frontend

# Copy environment template
cp .env.example .env.local

# Edit with your stack outputs
# NEXT_PUBLIC_API_URL=<API_URL>
# NEXT_PUBLIC_USER_POOL_ID=<USER_POOL_ID>
# NEXT_PUBLIC_USER_POOL_CLIENT_ID=<CLIENT_ID>
# NEXT_PUBLIC_REGION=us-east-1

# Install and run
npm install
npm run dev
```

## Verification

### Run Smoke Tests

Verify all components are working:

```bash
npm run smoke-test
```

The smoke test will verify:
- ✓ All CloudFormation stacks are deployed
- ✓ Cognito User Pool is active
- ✓ S3 buckets are accessible
- ✓ DynamoDB tables are active
- ✓ RDS database is available
- ✓ OpenSearch domain is active
- ✓ Authentication is working
- ✓ API Gateway is reachable
- ✓ Lambda functions are deployed
- ✓ Config API endpoint responds
- ✓ Ingest API endpoint responds

### Manual API Testing

Test the API manually:

```bash
# Get JWT token
API_URL=<your-api-url>
CLIENT_ID=<your-client-id>

TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id ${CLIENT_ID} \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test ingest endpoint
curl -X POST ${API_URL}api/v1/ingest \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic-complaints",
    "text": "There is a pothole on Main Street",
    "images": []
  }'

# Test query endpoint
curl -X POST ${API_URL}api/v1/query \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic-complaints",
    "question": "What are the recent complaints?"
  }'

# Test config endpoint
curl -X GET ${API_URL}api/v1/config/agents \
  -H "Authorization: Bearer ${TOKEN}"
```

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Fails

**Error**: "Unable to resolve AWS account to use"

**Solution**:
```bash
# Explicitly set credentials
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_REGION=us-east-1

# Force re-bootstrap
cdk bootstrap --force
```

#### 2. Stack Deployment Timeout

**Error**: "Resource creation cancelled"

**Solution**:
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name MultiAgentOrchestration-dev-Data \
  --max-items 20

# Common causes:
# - RDS taking longer than expected (normal, wait)
# - OpenSearch domain creation (normal, wait)
# - VPC resource limits (check service quotas)
```

#### 3. Database Initialization Fails

**Error**: Lambda timeout or connection error

**Solution**:
```bash
# Check Lambda logs
aws logs tail /aws/lambda/${DB_INIT_FUNCTION} --follow

# Common causes:
# - Security group not allowing Lambda access
# - Database not fully ready (wait 5 minutes, retry)
# - Incorrect database credentials

# Retry initialization
aws lambda invoke \
  --function-name ${DB_INIT_FUNCTION} \
  --region us-east-1 \
  response.json
```

#### 4. Authentication Fails

**Error**: "User does not exist" or "Incorrect username or password"

**Solution**:
```bash
# Verify user exists
aws cognito-idp admin-get-user \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser \
  --region us-east-1

# Reset password if needed
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1
```

#### 5. API Returns 403 Forbidden

**Error**: "User is not authorized to access this resource"

**Solution**:
```bash
# Check JWT token is valid
echo $TOKEN | cut -d'.' -f2 | base64 -d

# Verify tenant_id in token matches request
# Ensure Lambda authorizer is attached to API Gateway
# Check CloudWatch logs for authorizer function
```

### Viewing Logs

```bash
# Lambda function logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-<function-name> --follow

# API Gateway logs
aws logs tail /aws/apigateway/MultiAgentOrchestration-dev-Api --follow

# RDS logs
aws rds describe-db-log-files \
  --db-instance-identifier multiagentorchestration-dev-postgres

# OpenSearch logs
aws opensearch describe-domain \
  --domain-name multiagentorchestration-dev-opensearch \
  --query 'DomainStatus.LogPublishingOptions'
```

## Cost Estimation

### Monthly Costs (us-east-1, Development Environment)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| RDS PostgreSQL | t3.medium, Multi-AZ, 20GB | $120 |
| OpenSearch | 2x t3.medium, 20GB EBS | $150 |
| DynamoDB | On-demand, 1GB storage | $5-20 |
| S3 | 10GB storage, 1000 requests | $5 |
| Lambda | 1M invocations, 512MB avg | $10-20 |
| API Gateway | 1M requests | $3.50 |
| Cognito | 1000 MAU | Free |
| CloudWatch | Logs and metrics | $10 |
| Data Transfer | 10GB out | $1 |

**Total: ~$300-350/month**

### Cost Optimization Tips

For development/testing:

1. **Use smaller instances**:
   ```typescript
   // In data-stack.ts
   instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO)
   ```

2. **Single-AZ RDS**:
   ```typescript
   multiAz: false  // Not recommended for production
   ```

3. **Single-node OpenSearch**:
   ```typescript
   capacity: { dataNodes: 1 }
   ```

4. **Delete when not in use**:
   ```bash
   npm run destroy
   ```

### Production Costs

For production with high availability:
- RDS: t3.large Multi-AZ: ~$250/month
- OpenSearch: 3x m5.large: ~$500/month
- Lambda: 10M invocations: ~$100/month
- **Total: ~$1000-1500/month**

## Cleanup

### Destroy All Resources

```bash
# Destroy all stacks
npm run destroy

# Or destroy individually (reverse order)
cdk destroy MultiAgentOrchestration-dev-Api
cdk destroy MultiAgentOrchestration-dev-Data
cdk destroy MultiAgentOrchestration-dev-Storage
cdk destroy MultiAgentOrchestration-dev-Auth
```

### Manual Cleanup

Some resources may have `RETAIN` removal policy:

```bash
# Delete S3 buckets (if not empty)
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

# Check for S3 buckets
aws s3 ls | grep multiagentorchestration
```

## Next Steps

After successful deployment:

1. **Explore the API**: Use the provided Postman collection or curl commands
2. **Deploy Frontend**: Set up the Next.js frontend application
3. **Create Custom Agents**: Use the config API to create domain-specific agents
4. **Load Real Data**: Replace sample data with actual use case data
5. **Monitor Performance**: Set up CloudWatch dashboards and alarms
6. **Scale Resources**: Adjust instance sizes based on load testing

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review CloudWatch logs
- Consult [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- Review [Requirements](../.kiro/specs/multi-agent-orchestration-system/requirements.md)
- Review [Design Document](../.kiro/specs/multi-agent-orchestration-system/design.md)

## Appendix

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| AWS_ACCOUNT_ID | AWS account ID | Auto-detected | No |
| AWS_REGION | Deployment region | us-east-1 | No |
| STAGE | Environment stage | dev | No |
| PROJECT_NAME | Project name prefix | MultiAgentOrchestration | No |
| DB_INSTANCE_CLASS | RDS instance type | db.t3.medium | No |
| OPENSEARCH_INSTANCE_TYPE | OpenSearch instance | t3.medium.search | No |

### Stack Dependencies

```
Auth Stack (no dependencies)
  ↓
Storage Stack (no dependencies)
  ↓
Data Stack (depends on Storage)
  ↓
API Stack (depends on Auth)
```

### Port Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| RDS PostgreSQL | 5432 | TCP | Database connections |
| OpenSearch | 443 | HTTPS | Search API |
| API Gateway | 443 | HTTPS | REST API |
| AppSync | 443 | WSS | WebSocket |

### IAM Permissions Required

Minimum IAM permissions for deployment:

- CloudFormation: Full access
- Lambda: Full access
- API Gateway: Full access
- RDS: Full access
- OpenSearch: Full access
- DynamoDB: Full access
- S3: Full access
- Cognito: Full access
- IAM: Create/update roles and policies
- VPC: Create/update networking resources
- CloudWatch: Create log groups and metrics
- SSM: Put/get parameters
- Secrets Manager: Create/update secrets
