# Deployment Fix Guide

**Quick Reference**: How to fix the deployment issues identified in Task 31

---

## Issue #1: Missing psycopg Module in Lambda Functions

### Problem
Lambda functions fail with: `Runtime.ImportModuleError: Unable to import module 'agent_handler': No module named 'psycopg'`

### Solution: Use PythonFunction Construct

#### Step 1: Install CDK Python Alpha Module

```bash
cd infrastructure
npm install @aws-cdk/aws-lambda-python-alpha
```

#### Step 2: Update api-stack.ts

Replace the current Lambda function definitions with PythonFunction:

```typescript
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

// Agent Handler
const agentHandler = new PythonFunction(this, 'AgentHandler', {
  functionName: `${this.stackName}-AgentHandler`,
  entry: path.join(__dirname, '../../lambda/agent-api'),
  runtime: lambda.Runtime.PYTHON_3_11,
  index: 'agent_handler.py',
  handler: 'handler',
  timeout: cdk.Duration.seconds(30),
  memorySize: 512,
  environment: {
    RDS_CLUSTER_ARN: rdsClusterArn,
    DB_SECRET_ARN: dbSecretArn,
    TENANT_ID: 'default',
  },
  bundling: {
    assetExcludes: ['.venv', '__pycache__', '*.pyc', 'test_*', '.pytest_cache', '.coverage'],
  },
});

// Domain Handler
const domainHandler = new PythonFunction(this, 'DomainHandler', {
  functionName: `${this.stackName}-DomainHandler`,
  entry: path.join(__dirname, '../../lambda/domain-api'),
  runtime: lambda.Runtime.PYTHON_3_11,
  index: 'domain_handler.py',
  handler: 'handler',
  timeout: cdk.Duration.seconds(30),
  memorySize: 512,
  environment: {
    RDS_CLUSTER_ARN: rdsClusterArn,
    DB_SECRET_ARN: dbSecretArn,
    TENANT_ID: 'default',
  },
  bundling: {
    assetExcludes: ['.venv', '__pycache__', '*.pyc', 'test_*'],
  },
});

// Session Handler
const sessionHandler = new PythonFunction(this, 'SessionHandler', {
  functionName: `${this.stackName}-SessionHandler`,
  entry: path.join(__dirname, '../../lambda/session-api'),
  runtime: lambda.Runtime.PYTHON_3_11,
  index: 'session_handler.py',
  handler: 'handler',
  timeout: cdk.Duration.seconds(15),
  memorySize: 256,
  environment: {
    SESSIONS_TABLE: sessionsTableName,
    MESSAGES_TABLE: messagesTableName,
  },
  bundling: {
    assetExcludes: ['.venv', '__pycache__', '*.pyc', 'test_*'],
  },
});
```

#### Step 3: Redeploy

```bash
cd infrastructure
export $(grep -v '^#' .env | xargs)
cdk deploy MultiAgentOrchestration-dev-Api --require-approval never
```

---

## Issue #2: DB-Init Lambda Timeout

### Problem
Database initialization Lambda times out after 300 seconds

### Solution: Check VPC Configuration

#### Step 1: Verify Lambda is in VPC

```bash
aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Data-DbInit \
  --region us-east-1 \
  --query 'VpcConfig'
```

Expected output should show VPC ID and subnet IDs. If empty, Lambda is not in VPC.

#### Step 2: Update data-stack.ts

Ensure db-init Lambda is in the same VPC as RDS:

```typescript
const dbInitFunction = new lambda.Function(this, 'DbInit', {
  // ... other config
  vpc: vpc,  // Same VPC as RDS
  vpcSubnets: {
    subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
  },
  securityGroups: [dbSecurityGroup],  // Allow access to RDS
});
```

#### Step 3: Verify Security Groups

```bash
# Get RDS security group
aws rds describe-db-clusters \
  --db-cluster-identifier multiagentorchestration-dev-data-databaseb269d8bb \
  --region us-east-1 \
  --query 'DBClusters[0].VpcSecurityGroups'

# Ensure Lambda security group can access RDS on port 5432
```

#### Step 4: Increase Timeout (if needed)

```typescript
const dbInitFunction = new lambda.Function(this, 'DbInit', {
  // ... other config
  timeout: cdk.Duration.minutes(10),  // Increase from 5 to 10 minutes
});
```

---

## Issue #3: Report API Authorization Error

### Problem
Report submission returns 403 with authorization header error

### Solution: Check IngestHandler Authorization

#### Step 1: Review IngestHandler Code

Check if IngestHandler expects a different auth format:

```bash
grep -n "Authorization" infrastructure/lambda/orchestration/ingest_handler_simple.py
```

#### Step 2: Verify API Gateway Integration

Ensure IngestHandler uses the same authorizer as other endpoints:

```typescript
const reportsResource = apiV1.addResource('reports');
reportsResource.addMethod('POST', new apigateway.LambdaIntegration(ingestHandler), {
  authorizer: this.authorizer,  // Must use the same authorizer
  authorizationType: apigateway.AuthorizationType.CUSTOM,
});
```

#### Step 3: Test Authorization Header

```bash
# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test endpoint
curl -X POST https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","text":"Test report"}'
```

---

## Issue #4: Database Seeding

### Problem
Cannot seed database from local machine (VPC access)

### Solution: Use Lambda Function for Seeding

#### Option A: Invoke db-init with Seed Data

Update db-init Lambda to accept seed data as event:

```python
def handler(event, context):
    # Initialize schema
    initialize_schema()
    
    # Seed builtin data if requested
    if event.get('seed_builtin_data', False):
        seed_builtin_agents()
        seed_sample_domain()
    
    return {'statusCode': 200, 'body': 'Database initialized'}
```

Invoke with seed flag:

```bash
aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Data-DbInit \
  --region us-east-1 \
  --payload '{"seed_builtin_data": true}' \
  --cli-read-timeout 600 \
  response.json
```

#### Option B: Create Separate Seed Lambda

Create a new Lambda function specifically for seeding:

```typescript
const seedFunction = new lambda.Function(this, 'SeedData', {
  functionName: `${this.stackName}-SeedData`,
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'seed_data.handler',
  code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/db-init')),
  vpc: vpc,
  timeout: cdk.Duration.minutes(5),
  environment: {
    RDS_CLUSTER_ARN: rdsClusterArn,
    DB_SECRET_ARN: dbSecretArn,
  },
});
```

---

## Quick Deployment Checklist

### Before Redeploying

- [ ] Install @aws-cdk/aws-lambda-python-alpha
- [ ] Update api-stack.ts to use PythonFunction
- [ ] Update data-stack.ts to put db-init in VPC
- [ ] Verify security group rules
- [ ] Build TypeScript: `npm run build`

### Deploy

```bash
cd infrastructure
export $(grep -v '^#' .env | xargs)

# Deploy Data stack first (if updated)
cdk deploy MultiAgentOrchestration-dev-Data --require-approval never

# Wait for completion, then deploy API stack
cdk deploy MultiAgentOrchestration-dev-Api --require-approval never
```

### After Deployment

```bash
# Initialize database
aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Data-DbInit \
  --region us-east-1 \
  --payload '{"seed_builtin_data": true}' \
  --cli-read-timeout 600 \
  response.json

# Wait 2 minutes, then run tests
cd infrastructure
python3 TEST.py --mode deployed
```

### Expected Results

```
Total Tests: 24
Passed: 24 (100%)
Failed: 0 (0%)
Skipped: 0 (0%)

✓ READY FOR DEMO
All critical endpoints are working!
```

---

## Troubleshooting

### Lambda Still Can't Import psycopg

**Check**: Verify PythonFunction bundled dependencies

```bash
# Download Lambda function code
aws lambda get-function \
  --function-name MultiAgentOrchestration-dev-Api-AgentHandler \
  --region us-east-1 \
  --query 'Code.Location' \
  --output text | xargs curl -o function.zip

# Extract and check
unzip function.zip
ls -la | grep psycopg
```

### DB-Init Still Timing Out

**Check**: CloudWatch logs for detailed error

```bash
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Data-DbInit \
  --region us-east-1 \
  --follow
```

**Check**: VPC endpoints for Secrets Manager

```bash
aws ec2 describe-vpc-endpoints \
  --region us-east-1 \
  --filters "Name=service-name,Values=com.amazonaws.us-east-1.secretsmanager"
```

### Tests Still Failing

**Check**: API Gateway logs

```bash
aws logs tail /aws/apigateway/MultiAgentOrchestration-dev-Api-RestApi \
  --region us-east-1 \
  --follow
```

**Check**: Individual Lambda logs

```bash
# Agent Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-AgentHandler --region us-east-1 --follow

# Domain Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-DomainHandler --region us-east-1 --follow

# Session Handler
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-SessionHandler --region us-east-1 --follow
```

---

## Contact & Support

For issues or questions:
1. Check CloudWatch logs first
2. Review the detailed verification report: `TASK_31_DEPLOYMENT_VERIFICATION_REPORT.md`
3. Verify all prerequisites are met
4. Ensure AWS credentials have necessary permissions

---

**Last Updated**: October 22, 2025  
**Version**: 1.0
