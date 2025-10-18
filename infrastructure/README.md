# Multi-Agent Orchestration System - Infrastructure

This directory contains the AWS CDK infrastructure code for the Multi-Agent Orchestration System.

## 📚 Documentation

- **[Quick Start](#quick-start-deployment)** - Fast automated deployment
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Comprehensive deployment guide with troubleshooting
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Detailed manual deployment steps

## Prerequisites

- Node.js 18+ and npm
- AWS CLI configured with appropriate credentials
- AWS CDK CLI (`npm install -g aws-cdk`)
- Python 3.11+ (for Lambda functions)
- An AWS account with appropriate permissions

## Project Structure

```
infrastructure/
├── bin/
│   └── app.ts                 # CDK app entry point
├── lib/
│   └── stacks/
│       ├── auth-stack.ts      # Cognito authentication
│       ├── api-stack.ts       # API Gateway
│       ├── data-stack.ts      # RDS, DynamoDB, OpenSearch
│       └── storage-stack.ts   # S3 buckets
├── lambda/
│   ├── authorizer/            # JWT authorizer
│   ├── db-init/               # Database initialization
│   └── opensearch-init/       # OpenSearch index setup
├── package.json
├── tsconfig.json
└── cdk.json
```

## Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and set your AWS account details:
```bash
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
STAGE=dev
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Build TypeScript:
```bash
npm run build
```

3. Bootstrap CDK (first time only):
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

## Quick Start Deployment

### Option 1: Automated Deployment (Recommended)

The fastest way to deploy the entire system:

```bash
# 1. Check if your environment is ready
npm run check-readiness

# 2. Run the automated deployment script
npm run deploy:full

# 3. Load sample data and configurations
npm run seed-data

# 4. Verify deployment
npm run smoke-test
```

This automated approach will:
1. ✓ Check all prerequisites
2. ✓ Install dependencies
3. ✓ Bootstrap CDK (if needed)
4. ✓ Deploy all stacks in correct order
5. ✓ Initialize database schema
6. ✓ Initialize OpenSearch indices
7. ✓ Create test user (testuser/TestPassword123!)
8. ✓ Display all stack outputs

**Estimated time: 25-30 minutes**

### Option 2: Step-by-Step Deployment

For more control over the deployment process:

```bash
# 1. Check prerequisites
npm run check-readiness

# 2. Install and build
npm install
npm run build

# 3. Bootstrap CDK (first time only)
cdk bootstrap

# 4. Deploy all stacks
npm run deploy

# 5. Wait for deployment to complete, then seed data
npm run seed-data

# 6. Run smoke tests
npm run smoke-test
```

### Available NPM Scripts

| Script | Description |
|--------|-------------|
| `npm run check-readiness` | Verify prerequisites before deployment |
| `npm run build` | Compile TypeScript to JavaScript |
| `npm run deploy:full` | Automated full deployment (recommended) |
| `npm run deploy` | Deploy all CDK stacks |
| `npm run seed-data` | Load sample configurations and data |
| `npm run smoke-test` | Verify deployment is working |
| `npm run synth` | Generate CloudFormation templates |
| `npm run diff` | Show changes before deployment |
| `npm run destroy` | Delete all resources |

## Deployment Scripts

The project includes four deployment scripts in the `scripts/` directory:

### 1. check-readiness.sh

Verifies your environment is ready for deployment:

```bash
npm run check-readiness
```

**Checks:**
- ✓ Node.js 18+ installed
- ✓ Python 3.11+ installed
- ✓ AWS CLI v2 installed
- ✓ AWS CDK CLI installed
- ✓ AWS credentials configured
- ✓ .env file exists and configured
- ✓ Dependencies installed
- ✓ CDK bootstrapped
- ✓ Scripts are executable

**Exit codes:**
- 0: Ready to deploy
- 1: Issues found (see output for details)

### 2. deploy.sh

Automated deployment script that handles the entire deployment process:

```bash
npm run deploy:full
```

**What it does:**
1. Checks prerequisites
2. Loads environment configuration
3. Installs dependencies
4. Bootstraps CDK (if needed)
5. Deploys all stacks
6. Initializes database schema
7. Initializes OpenSearch indices
8. Creates test user
9. Displays stack outputs

**Duration:** ~25-30 minutes

**Outputs:**
- API URL
- User Pool ID and Client ID
- Database endpoint
- OpenSearch endpoint
- S3 bucket names

### 3. seed-data.sh

Loads sample configurations and test data:

```bash
npm run seed-data
```

**What it loads:**
1. Tool registry entries (Bedrock, Comprehend, Location Service, etc.)
2. Agent configurations (Geo, Temporal, Entity agents)
3. Query agents (When, Where, Why, How, What, etc.)
4. Playbooks (Civic Complaints domain)
5. Dependency graphs
6. Sample incident data (3 civic complaints)

**Prerequisites:**
- Stacks must be deployed
- Test user must exist
- Database and OpenSearch must be initialized

**Duration:** ~2-3 minutes

### 4. smoke-test.sh

Comprehensive verification of the deployment:

```bash
npm run smoke-test
```

**Tests performed:**
- ✓ All CloudFormation stacks exist and are healthy
- ✓ Cognito User Pool is enabled
- ✓ Test user exists
- ✓ S3 buckets are accessible
- ✓ DynamoDB tables are active
- ✓ RDS database is available
- ✓ OpenSearch domain is active
- ✓ Authentication works (JWT token generation)
- ✓ API Gateway is reachable
- ✓ Lambda functions are deployed
- ✓ Config API endpoint responds
- ✓ Ingest API endpoint accepts requests

**Duration:** ~1-2 minutes

**Exit codes:**
- 0: All tests passed
- 1: Some tests failed (see output for details)

## Manual Deployment

If you prefer step-by-step deployment:

### Deploy All Stacks

```bash
npm run deploy
```

This will deploy all stacks in the correct order:
1. Auth Stack (Cognito)
2. Storage Stack (S3)
3. Data Stack (RDS, DynamoDB, OpenSearch)
4. API Stack (API Gateway)
5. Orchestration Stack (Step Functions)
6. Realtime Stack (AppSync)

### Deploy Individual Stacks

```bash
cdk deploy MultiAgentOrchestration-dev-Auth
cdk deploy MultiAgentOrchestration-dev-Storage
cdk deploy MultiAgentOrchestration-dev-Data
cdk deploy MultiAgentOrchestration-dev-Api
cdk deploy MultiAgentOrchestration-dev-Orchestration
cdk deploy MultiAgentOrchestration-dev-Realtime
```

### View Deployment Plan

```bash
npm run synth
```

### View Differences

```bash
npm run diff
```

## Seeding Data

After deployment, load sample configurations and data:

```bash
npm run seed-data
```

This will:
- Load tool registry entries
- Create sample agent configurations
- Set up playbooks and dependency graphs
- Create sample incident data for testing

## Verification

Run smoke tests to verify deployment:

```bash
npm run smoke-test
```

This will test:
- All CloudFormation stacks
- Cognito authentication
- S3 buckets
- DynamoDB tables
- RDS database
- OpenSearch domain
- API Gateway endpoints
- Lambda functions

## Post-Deployment Steps

### 1. Initialize Database Schema

After the Data Stack is deployed, invoke the database initialization Lambda:

```bash
aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Data-DbInit \
  --region us-east-1 \
  response.json

cat response.json
```

### 2. Initialize OpenSearch Index

Invoke the OpenSearch initialization Lambda:

```bash
aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Data-OpenSearchInit \
  --region us-east-1 \
  response.json

cat response.json
```

### 3. Create Test User

Create a test user in Cognito:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username testuser \
  --user-attributes Name=email,Value=test@example.com Name=custom:tenant_id,Value=test-tenant-123 \
  --temporary-password TempPassword123! \
  --region us-east-1
```

## Stack Outputs

After deployment, important values are exported:

- **Auth Stack**:
  - UserPoolId
  - UserPoolClientId
  - AuthorizerFunctionArn

- **Storage Stack**:
  - EvidenceBucketName
  - ConfigBackupBucketName

- **Data Stack**:
  - DatabaseEndpoint
  - DatabaseSecretArn
  - ConfigurationsTableName
  - OpenSearchEndpoint

- **API Stack**:
  - ApiUrl
  - ApiId

View outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Api \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

## SSM Parameters

Configuration values are stored in SSM Parameter Store:

```bash
# View all parameters
aws ssm get-parameters-by-path \
  --path /app \
  --recursive \
  --region us-east-1

# Get specific parameter
aws ssm get-parameter \
  --name /app/api/url \
  --region us-east-1
```

## Testing the API

### Get JWT Token

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <USER_POOL_CLIENT_ID> \
  --auth-parameters USERNAME=testuser,PASSWORD=<password> \
  --region us-east-1
```

### Test API Endpoint

```bash
curl -X POST https://<API_URL>/api/v1/ingest \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic-complaints",
    "text": "There is a pothole on Main Street",
    "images": []
  }'
```

## Cleanup

To destroy all resources:

```bash
npm run destroy
```

**Warning**: This will delete all resources including databases and S3 buckets (if removal policy allows).

## Troubleshooting

### Common Deployment Issues

#### 1. Prerequisites Check Fails

**Problem:** `check-readiness.sh` reports missing software

**Solution:**
```bash
# Install Node.js 18+
# Visit: https://nodejs.org/

# Install Python 3.11+
# Visit: https://www.python.org/

# Install AWS CLI v2
# Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Install AWS CDK CLI
npm install -g aws-cdk

# Configure AWS credentials
aws configure
```

#### 2. CDK Bootstrap Issues

**Problem:** "Unable to resolve AWS account to use"

**Solution:**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Set explicit credentials
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_REGION=us-east-1

# Force re-bootstrap
cdk bootstrap --force
```

#### 3. Stack Deployment Timeout

**Problem:** "Resource creation cancelled" or timeout

**Solution:**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name MultiAgentOrchestration-dev-Data \
  --max-items 20 \
  --region us-east-1

# Common causes:
# - RDS creation takes 15-20 minutes (normal, wait)
# - OpenSearch domain creation takes 10-15 minutes (normal, wait)
# - VPC resource limits (check service quotas)

# Check service quotas
aws service-quotas list-service-quotas \
  --service-code rds \
  --region us-east-1
```

#### 4. Database Initialization Fails

**Problem:** Lambda timeout or connection error

**Solution:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Data-DbInit --follow

# Common causes:
# - Security group not allowing Lambda access
# - Database not fully ready (wait 5 minutes, retry)
# - Incorrect database credentials

# Retry initialization
DB_INIT_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs[?OutputKey==`DbInitFunctionName`].OutputValue' \
  --output text)

aws lambda invoke \
  --function-name ${DB_INIT_FUNCTION} \
  --region us-east-1 \
  response.json

cat response.json
```

#### 5. OpenSearch Initialization Fails

**Problem:** "Unable to connect to OpenSearch"

**Solution:**
```bash
# Check OpenSearch domain status
aws opensearch describe-domain \
  --domain-name multiagentorchestration-dev-opensearch \
  --region us-east-1 \
  --query 'DomainStatus.Processing'

# Wait for Processing=false, then retry
OS_INIT_FUNCTION=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchInitFunctionName`].OutputValue' \
  --output text)

aws lambda invoke \
  --function-name ${OS_INIT_FUNCTION} \
  --region us-east-1 \
  response.json
```

#### 6. Authentication Fails

**Problem:** "User does not exist" or "Incorrect username or password"

**Solution:**
```bash
# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

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

#### 7. Seed Data Script Fails

**Problem:** "Failed to seed agent" or API errors

**Solution:**
```bash
# Verify API is accessible
API_URL=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

curl -I ${API_URL}

# Check if JWT token is valid
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Auth \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id ${CLIENT_ID} \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1

# Retry seed data
npm run seed-data
```

#### 8. Smoke Tests Fail

**Problem:** Some tests fail during verification

**Solution:**
```bash
# Wait for resources to stabilize (5-10 minutes after deployment)
sleep 300

# Check specific resource status
aws cloudformation describe-stacks \
  --stack-name MultiAgentOrchestration-dev-Data \
  --query 'Stacks[0].StackStatus' \
  --region us-east-1

# Re-run smoke tests
npm run smoke-test

# Check CloudWatch logs for specific failures
aws logs tail /aws/lambda/<function-name> --follow
```

### Viewing Logs

```bash
# Lambda function logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-<function-name> --follow

# API Gateway logs
aws logs tail /aws/apigateway/MultiAgentOrchestration-dev-Api --follow

# RDS logs
aws rds describe-db-log-files \
  --db-instance-identifier multiagentorchestration-dev-postgres \
  --region us-east-1

# OpenSearch logs
aws opensearch describe-domain \
  --domain-name multiagentorchestration-dev-opensearch \
  --region us-east-1 \
  --query 'DomainStatus.LogPublishingOptions'

# CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name MultiAgentOrchestration-dev-Data \
  --max-items 50 \
  --region us-east-1
```

### Getting Help

If issues persist:

1. **Check CloudWatch Logs**: Most errors are logged in CloudWatch
2. **Review Stack Events**: CloudFormation events show resource creation issues
3. **Verify Prerequisites**: Run `npm run check-readiness` again
4. **Check Service Quotas**: Ensure you have sufficient AWS service limits
5. **Review Documentation**: See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed steps
6. **Clean and Retry**: Sometimes a fresh deployment helps:
   ```bash
   npm run destroy
   npm run deploy:full
   ```

## Cost Estimation

Approximate monthly costs (us-east-1):
- RDS PostgreSQL (t3.medium, Multi-AZ): ~$120
- OpenSearch (2x t3.medium): ~$150
- DynamoDB (on-demand): ~$5-50 (usage dependent)
- S3: ~$5-20 (storage dependent)
- Lambda: ~$5-20 (invocations dependent)
- API Gateway: ~$3.50 per million requests

**Total**: ~$300-400/month for development environment

## Deployment Best Practices

### For Development

1. **Use the automated script**: `npm run deploy:full` handles everything
2. **Check readiness first**: Run `npm run check-readiness` before deploying
3. **Monitor deployment**: Watch CloudFormation console for progress
4. **Verify with smoke tests**: Always run `npm run smoke-test` after deployment
5. **Keep .env file secure**: Never commit credentials to git

### For Production

1. **Use separate AWS accounts**: Dev, staging, and production
2. **Enable Multi-AZ**: For RDS and OpenSearch high availability
3. **Configure backups**: Enable automated backups for RDS
4. **Set up monitoring**: Create CloudWatch dashboards and alarms
5. **Use larger instances**: Scale up RDS and OpenSearch for production load
6. **Enable WAF**: Protect API Gateway with AWS WAF
7. **Configure VPC**: Use private subnets for databases
8. **Implement CI/CD**: Automate deployments with GitHub Actions or CodePipeline

### Deployment Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Deployment Workflow                       │
└─────────────────────────────────────────────────────────────┘

1. Prerequisites Check
   ├─ Node.js 18+
   ├─ Python 3.11+
   ├─ AWS CLI v2
   ├─ AWS CDK CLI
   └─ AWS Credentials
        ↓
2. Environment Setup
   ├─ Create .env file
   ├─ Set AWS_REGION
   ├─ Set STAGE
   └─ Set AWS_ACCOUNT_ID
        ↓
3. CDK Bootstrap (first time only)
   └─ cdk bootstrap
        ↓
4. Deploy Infrastructure
   ├─ Auth Stack (Cognito)
   ├─ Storage Stack (S3)
   ├─ Data Stack (RDS, DynamoDB, OpenSearch)
   ├─ API Stack (API Gateway, Lambda)
   ├─ Orchestration Stack (Step Functions)
   └─ Realtime Stack (AppSync)
        ↓
5. Initialize Services
   ├─ Database schema
   ├─ OpenSearch indices
   └─ Test user
        ↓
6. Load Seed Data
   ├─ Tool registry
   ├─ Agent configurations
   ├─ Playbooks
   └─ Sample data
        ↓
7. Verify Deployment
   └─ Run smoke tests
        ↓
8. Ready for Use! 🎉
```

### Estimated Deployment Times

| Phase | Duration | Notes |
|-------|----------|-------|
| Prerequisites check | 1 min | Instant if already installed |
| CDK bootstrap | 2-3 min | Only needed once per account/region |
| Auth Stack | 2-3 min | Cognito User Pool creation |
| Storage Stack | 1-2 min | S3 bucket creation |
| Data Stack | 15-20 min | RDS and OpenSearch take longest |
| API Stack | 3-5 min | API Gateway and Lambda functions |
| Orchestration Stack | 2-3 min | Step Functions state machines |
| Realtime Stack | 2-3 min | AppSync API |
| Service initialization | 2-3 min | Database and OpenSearch setup |
| Seed data | 2-3 min | Loading configurations |
| Smoke tests | 1-2 min | Verification |
| **Total** | **25-35 min** | End-to-end automated deployment |

### Resource Naming Convention

All resources follow this naming pattern:

```
MultiAgentOrchestration-{STAGE}-{STACK}-{RESOURCE}

Examples:
- MultiAgentOrchestration-dev-Auth-UserPool
- MultiAgentOrchestration-dev-Data-PostgresDB
- MultiAgentOrchestration-prod-Api-IngestFunction
```

This makes it easy to:
- Identify resources by environment
- Filter CloudWatch logs
- Track costs by stage
- Clean up resources

## Support

For issues or questions, refer to:
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Comprehensive deployment guide
- [Project Requirements](../.kiro/specs/multi-agent-orchestration-system/requirements.md)
- [Design Document](../.kiro/specs/multi-agent-orchestration-system/design.md)
- [Troubleshooting](#troubleshooting) - Common issues and solutions
