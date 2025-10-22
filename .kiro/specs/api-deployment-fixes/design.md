# Design Document

## Overview

This design addresses critical deployment issues preventing Lambda functions from executing due to missing Python dependencies. The solution involves updating CDK stack configurations to use the PythonFunction construct for automatic dependency bundling, ensuring proper VPC configuration for database access, and implementing comprehensive deployment verification.

The current deployment successfully creates all AWS infrastructure (100% resource creation) but fails at runtime with only 4.2% test pass rate. The root causes are:
1. Lambda functions missing psycopg module (Runtime.ImportModuleError)
2. db-init Lambda timing out due to VPC/security group misconfiguration
3. No automated verification of deployment success

This design provides a systematic approach to fix these issues and achieve 100% API functionality.

## Architecture

### Current State Issues

```
┌─────────────────────────────────────────────────────────────┐
│                    Current Deployment                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CDK Stack (api-stack.ts)                                   │
│  ┌──────────────────────────────────────────┐              │
│  │ lambda.Function()                         │              │
│  │ - Uses Code.fromAsset()                   │              │
│  │ - Does NOT bundle dependencies            │              │
│  │ - requirements.txt ignored                │              │
│  └──────────────────────────────────────────┘              │
│                    ↓                                         │
│  Lambda Deployment Package                                   │
│  ┌──────────────────────────────────────────┐              │
│  │ ✓ agent_handler.py                        │              │
│  │ ✓ domain_handler.py                       │              │
│  │ ✗ psycopg module (MISSING)                │              │
│  │ ✗ boto3 dependencies (MISSING)            │              │
│  └──────────────────────────────────────────┘              │
│                    ↓                                         │
│  Runtime Execution                                           │
│  ┌──────────────────────────────────────────┐              │
│  │ ✗ ImportModuleError: No module 'psycopg' │              │
│  │ ✗ 502 Bad Gateway                         │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Target State Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Fixed Deployment                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CDK Stack (api-stack.ts)                                   │
│  ┌──────────────────────────────────────────┐              │
│  │ PythonFunction()                          │              │
│  │ - entry: lambda/agent-api                 │              │
│  │ - Reads requirements.txt                  │              │
│  │ - Bundles dependencies via Docker         │              │
│  │ - Excludes test files                     │              │
│  └──────────────────────────────────────────┘              │
│                    ↓                                         │
│  Lambda Deployment Package                                   │
│  ┌──────────────────────────────────────────┐              │
│  │ ✓ agent_handler.py                        │              │
│  │ ✓ domain_handler.py                       │              │
│  │ ✓ psycopg/ (bundled)                      │              │
│  │ ✓ boto3/ (bundled)                        │              │
│  │ ✓ All dependencies from requirements.txt  │              │
│  └──────────────────────────────────────────┘              │
│                    ↓                                         │
│  Runtime Execution                                           │
│  ┌──────────────────────────────────────────┐              │
│  │ ✓ All imports successful                  │              │
│  │ ✓ 200/201 responses                       │              │
│  │ ✓ Database connectivity                   │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### VPC and Database Access

```
┌────────────────────────────────────────────────────────────┐
│                         VPC                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                  Public Subnet                        │ │
│  │                                                        │ │
│  │  ┌─────────────────┐      ┌──────────────────────┐  │ │
│  │  │  db-init Lambda │─────▶│  RDS Aurora Cluster  │  │ │
│  │  │  - In VPC       │      │  - PostgreSQL 15.4   │  │ │
│  │  │  - Public subnet│      │  - Serverless v2     │  │ │
│  │  │  - Has SG       │      │  - Port 5432         │  │ │
│  │  └─────────────────┘      └──────────────────────┘  │ │
│  │         │                           ▲                 │ │
│  │         │                           │                 │ │
│  │         └───────Security Group──────┘                │ │
│  │              (Allows TCP 5432)                        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Secrets Manager                          │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │  Database Credentials                           │  │ │
│  │  │  - username: postgres                           │  │ │
│  │  │  - password: <generated>                        │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. CDK Stack Updates

#### api-stack.ts Modifications

**Component**: Lambda Function Definitions  
**Current Implementation**: Uses `lambda.Function` with `Code.fromAsset()`  
**New Implementation**: Uses `PythonFunction` construct

**Interface Changes**:

```typescript
// OLD - Does not bundle dependencies
const agentHandler = new lambda.Function(this, 'AgentHandler', {
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'agent_handler.handler',
  code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/agent-api')),
  // ... other config
});

// NEW - Automatically bundles dependencies
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

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
    assetExcludes: [
      '.venv',
      '__pycache__',
      '*.pyc',
      'test_*',
      '.pytest_cache',
      '.coverage',
    ],
  },
});
```

**Functions Requiring Update**:
- AgentHandler (agent-api)
- DomainHandler (domain-api)
- SessionHandler (session-api)
- ConfigHandler (config-api)
- IngestHandler (orchestration)
- QueryHandler (orchestration)
- Orchestrator (orchestration)

### 2. Database Initialization Component

#### db-init Lambda Configuration

**Current Issue**: Lambda times out after 300 seconds  
**Root Cause**: VPC configuration already correct, but timeout too short for schema + seed operations

**Solution**: Increase timeout and add seed data support

```typescript
const dbInitFunction = new lambda.Function(this, 'DbInitFunction', {
  functionName: `${id}-DbInit`,
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'db_init.handler',
  code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/db-init')),
  layers: [psycopg2Layer],
  timeout: cdk.Duration.minutes(10),  // Increased from 5 to 10
  memorySize: 512,
  vpc: this.vpc,
  vpcSubnets: {
    subnetType: ec2.SubnetType.PUBLIC,
  },
  allowPublicSubnet: true,
  environment: {
    DB_SECRET_ARN: this.databaseSecret.secretArn,
    DB_HOST: (this.database as any).clusterEndpoint.hostname,
    DB_PORT: '5432',
    DB_NAME: 'multi_agent_orchestration',
  },
});
```

#### db_init.py Handler Enhancement

**Current**: Only creates schema  
**New**: Creates schema AND loads seed data

```python
def handler(event, context):
    """
    Initialize database schema and optionally seed data.
    
    Event parameters:
    - seed_builtin_data: bool - Load builtin agents and sample domain
    """
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Create schema
        create_schema(conn)
        
        # Seed data if requested
        if event.get('seed_builtin_data', False):
            seed_builtin_agents(conn)
            seed_sample_domain(conn)
        
        conn.commit()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database initialized successfully',
                'schema_created': True,
                'data_seeded': event.get('seed_builtin_data', False)
            })
        }
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### 3. Deployment Verification Script

**Component**: deploy-and-verify.sh  
**Purpose**: Automated deployment with verification checkpoints

**Script Flow**:

```bash
#!/bin/bash
set -e

# 1. Pre-deployment checks
check_prerequisites() {
  # Verify AWS credentials
  # Verify CDK installed
  # Verify environment variables
}

# 2. Install dependencies
install_dependencies() {
  cd infrastructure
  npm install
  npm install @aws-cdk/aws-lambda-python-alpha
}

# 3. Build and deploy
deploy_stacks() {
  npm run build
  cdk deploy MultiAgentOrchestration-dev-Data --require-approval never
  cdk deploy MultiAgentOrchestration-dev-Api --require-approval never
}

# 4. Verify deployment
verify_deployment() {
  # Check stack status
  # Verify Lambda functions are Active
  # Check CloudWatch logs for errors
}

# 5. Initialize database
initialize_database() {
  aws lambda invoke \
    --function-name MultiAgentOrchestration-dev-Data-DbInit \
    --payload '{"seed_builtin_data": true}' \
    --cli-read-timeout 600 \
    response.json
  
  # Verify response
  cat response.json | jq '.statusCode'
}

# 6. Run tests
run_tests() {
  python3 TEST.py --mode deployed
}

# 7. Generate report
generate_report() {
  # Parse test results
  # Check CloudWatch logs
  # Create deployment report
}
```

### 4. Test Suite Integration

**Component**: TEST.py enhancements  
**Purpose**: Better error reporting and CloudWatch log capture

**Enhancements**:

```python
class DeploymentTester:
    def __init__(self, mode='deployed'):
        self.mode = mode
        self.results = []
        self.cloudwatch_client = boto3.client('logs')
    
    def run_test(self, test_name, test_func):
        """Run test and capture CloudWatch logs on failure"""
        try:
            result = test_func()
            self.results.append({
                'test': test_name,
                'status': 'PASS' if result else 'FAIL',
                'logs': None
            })
        except Exception as e:
            # Capture CloudWatch logs
            logs = self.get_recent_logs(test_name)
            self.results.append({
                'test': test_name,
                'status': 'FAIL',
                'error': str(e),
                'logs': logs
            })
    
    def get_recent_logs(self, function_name):
        """Fetch recent CloudWatch logs for Lambda function"""
        log_group = f'/aws/lambda/MultiAgentOrchestration-dev-Api-{function_name}'
        # Fetch last 50 lines
        return self.cloudwatch_client.filter_log_events(
            logGroupName=log_group,
            limit=50
        )
    
    def generate_report(self):
        """Generate comprehensive test report"""
        pass_count = sum(1 for r in self.results if r['status'] == 'PASS')
        total_count = len(self.results)
        pass_rate = (pass_count / total_count) * 100
        
        return {
            'total': total_count,
            'passed': pass_count,
            'failed': total_count - pass_count,
            'pass_rate': pass_rate,
            'ready_for_demo': pass_rate == 100.0,
            'results': self.results
        }
```

## Data Models

### Deployment Verification Report

```json
{
  "deployment_id": "20251022-v1",
  "timestamp": "2025-10-22T10:30:00Z",
  "stacks": [
    {
      "name": "MultiAgentOrchestration-dev-Data",
      "status": "UPDATE_COMPLETE",
      "resources": 15
    },
    {
      "name": "MultiAgentOrchestration-dev-Api",
      "status": "UPDATE_COMPLETE",
      "resources": 12
    }
  ],
  "lambda_functions": [
    {
      "name": "MultiAgentOrchestration-dev-Api-AgentHandler",
      "state": "Active",
      "runtime": "python3.11",
      "code_size": 15728640,
      "has_dependencies": true
    }
  ],
  "database": {
    "initialized": true,
    "schema_version": "1.0",
    "seed_data_loaded": true,
    "builtin_agents": 5,
    "sample_domains": 1
  },
  "tests": {
    "total": 24,
    "passed": 24,
    "failed": 0,
    "pass_rate": 100.0,
    "ready_for_demo": true
  },
  "issues": []
}
```

### Lambda Function Configuration

```typescript
interface LambdaConfig {
  functionName: string;
  entry: string;              // Path to Lambda code directory
  index: string;              // Python file name (e.g., 'agent_handler.py')
  handler: string;            // Handler function name (e.g., 'handler')
  runtime: lambda.Runtime;
  timeout: cdk.Duration;
  memorySize: number;
  environment: Record<string, string>;
  bundling: {
    assetExcludes: string[];  // Files to exclude from bundle
  };
}
```

## Error Handling

### Lambda Import Errors

**Detection**: CloudWatch logs show `Runtime.ImportModuleError`  
**Prevention**: PythonFunction construct bundles all dependencies  
**Logging**: Enhanced error messages with module name and traceback

```python
try:
    import psycopg
except ImportError as e:
    logger.error(f"Failed to import required module: {e}")
    logger.error(f"Python path: {sys.path}")
    logger.error(f"Available modules: {os.listdir('/var/task')}")
    raise
```

### Database Connection Errors

**Detection**: Connection timeout or authentication failure  
**Prevention**: Proper VPC configuration and security groups  
**Logging**: Connection details (host, port, timeout duration)

```python
try:
    conn = psycopg.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password,
        connect_timeout=30
    )
except psycopg.OperationalError as e:
    logger.error(f"Database connection failed: {e}")
    logger.error(f"Host: {db_host}, Port: {db_port}, Database: {db_name}")
    logger.error(f"VPC: {os.environ.get('AWS_LAMBDA_VPC_ID')}")
    raise
```

### Deployment Verification Errors

**Detection**: Stack status not CREATE_COMPLETE/UPDATE_COMPLETE  
**Prevention**: Pre-deployment validation checks  
**Logging**: CloudFormation events and error messages

```bash
verify_stack_status() {
  local stack_name=$1
  local status=$(aws cloudformation describe-stacks \
    --stack-name "$stack_name" \
    --query 'Stacks[0].StackStatus' \
    --output text)
  
  if [[ "$status" != "CREATE_COMPLETE" && "$status" != "UPDATE_COMPLETE" ]]; then
    echo "ERROR: Stack $stack_name is in $status state"
    aws cloudformation describe-stack-events \
      --stack-name "$stack_name" \
      --max-items 10
    return 1
  fi
  
  echo "✓ Stack $stack_name is $status"
  return 0
}
```

## Testing Strategy

### Unit Tests

**Scope**: Individual Lambda function handlers  
**Location**: `infrastructure/lambda/*/test_*.py`  
**Execution**: Local development environment

```bash
# Test agent handler
cd infrastructure/lambda/agent-api
python -m pytest test_agent_handler.py -v

# Test domain handler
cd infrastructure/lambda/domain-api
python -m pytest test_domain_handler.py -v
```

### Integration Tests

**Scope**: Full API endpoints against deployed infrastructure  
**Location**: `infrastructure/TEST.py`  
**Execution**: After deployment

```bash
cd infrastructure
python3 TEST.py --mode deployed
```

**Test Categories**:
1. Authentication (1 test)
2. Agent CRUD (6 tests)
3. Domain CRUD (6 tests)
4. Report submission (4 tests)
5. Session management (4 tests)
6. Query execution (3 tests)

### Deployment Verification Tests

**Scope**: Infrastructure and configuration validation  
**Execution**: Automated in deployment script

```bash
# 1. Stack status verification
verify_stack_status "MultiAgentOrchestration-dev-Data"
verify_stack_status "MultiAgentOrchestration-dev-Api"

# 2. Lambda function verification
verify_lambda_active "MultiAgentOrchestration-dev-Api-AgentHandler"
verify_lambda_active "MultiAgentOrchestration-dev-Api-DomainHandler"

# 3. Database verification
verify_database_initialized

# 4. API Gateway verification
verify_api_gateway_deployed
```

### CloudWatch Log Monitoring

**Scope**: Runtime error detection  
**Execution**: Continuous during testing

```bash
# Monitor all Lambda functions
for func in AgentHandler DomainHandler SessionHandler; do
  aws logs tail "/aws/lambda/MultiAgentOrchestration-dev-Api-$func" \
    --region us-east-1 \
    --follow &
done
```

## Implementation Phases

### Phase 1: CDK Stack Updates (Requirements 1, 2)

1. Install @aws-cdk/aws-lambda-python-alpha package
2. Update api-stack.ts to use PythonFunction for all handlers
3. Update data-stack.ts to increase db-init timeout
4. Build and validate TypeScript compilation

**Validation**: `npm run build` succeeds without errors

### Phase 2: Database Initialization Enhancement (Requirement 4)

1. Update db_init.py to accept seed_builtin_data parameter
2. Add seed_builtin_agents() function
3. Add seed_sample_domain() function
4. Test locally with mock database

**Validation**: Unit tests pass for db_init.py

### Phase 3: Deployment (Requirement 3)

1. Deploy Data stack with updated db-init Lambda
2. Deploy API stack with PythonFunction constructs
3. Verify all stacks show UPDATE_COMPLETE status
4. Verify all Lambda functions are Active

**Validation**: CloudFormation stacks deployed successfully

### Phase 4: Database Initialization (Requirement 4)

1. Invoke db-init Lambda with seed_builtin_data=true
2. Wait for completion (up to 10 minutes)
3. Verify response shows statusCode 200
4. Query database to confirm tables and data exist

**Validation**: Database contains schema and seed data

### Phase 5: Testing and Verification (Requirements 5, 6)

1. Run TEST.py in deployed mode
2. Capture test results and CloudWatch logs
3. Generate deployment verification report
4. Confirm 100% pass rate

**Validation**: All 24 tests pass, ready for demo

## Dependencies

### NPM Packages

```json
{
  "dependencies": {
    "@aws-cdk/aws-lambda-python-alpha": "^2.x.x"
  }
}
```

### Python Packages (Lambda)

Already defined in requirements.txt files:
- psycopg[binary]==3.2.3
- boto3==1.34.0
- pytest==7.4.3 (dev only)

### AWS Services

- AWS CDK v2
- CloudFormation
- Lambda
- RDS Aurora Serverless v2
- DynamoDB
- API Gateway
- Cognito
- Secrets Manager
- CloudWatch Logs
- IAM

### Tools

- Node.js 18+
- Python 3.11
- AWS CLI v2
- Docker (for PythonFunction bundling)
- jq (for JSON parsing in scripts)

## Security Considerations

### IAM Permissions

Lambda functions require:
- RDS Data API access (rds-data:ExecuteStatement)
- Secrets Manager read (secretsmanager:GetSecretValue)
- DynamoDB read/write (dynamodb:GetItem, PutItem, Query, etc.)
- CloudWatch Logs write (logs:CreateLogStream, PutLogEvents)

### VPC Security

- Lambda functions in public subnet with allowPublicSubnet=true
- Security group allows outbound to RDS on port 5432
- RDS security group allows inbound from Lambda security group
- No inbound internet access to RDS (public subnet but security group restricted)

### Secrets Management

- Database credentials stored in Secrets Manager
- Automatic password generation (32 characters, no punctuation)
- Lambda functions access via DB_SECRET_ARN environment variable
- Secrets encrypted at rest with AWS managed keys

### API Security

- All endpoints protected by Cognito authorizer
- Authorization header required (Bearer token)
- CORS configured for specific origins
- API Gateway logging enabled for audit trail

## Performance Considerations

### Lambda Cold Start

PythonFunction bundling increases deployment package size:
- Current: ~50 MB (code only)
- With dependencies: ~15 MB (psycopg + boto3)
- Cold start impact: +200-500ms

**Mitigation**: Acceptable for demo, can add provisioned concurrency for production

### Database Connection Pooling

Lambda functions create new database connections per invocation:
- Connection time: ~100-200ms
- Query time: ~50-100ms
- Total: ~150-300ms per request

**Mitigation**: Acceptable for demo, can implement connection pooling for production

### Deployment Time

PythonFunction bundling uses Docker:
- First deployment: ~5-10 minutes (Docker image pull + dependency install)
- Subsequent deployments: ~2-3 minutes (cached dependencies)

**Mitigation**: Acceptable for development workflow

## Monitoring and Observability

### CloudWatch Metrics

- Lambda invocation count
- Lambda error count
- Lambda duration (p50, p99)
- API Gateway 4xx/5xx errors
- API Gateway latency

### CloudWatch Logs

- Lambda function logs (all invocations)
- API Gateway access logs (all requests)
- CloudFormation deployment logs

### Alarms (Future Enhancement)

- Lambda error rate > 5%
- API Gateway 5xx rate > 1%
- Database connection failures
- Lambda timeout rate > 1%

## Rollback Strategy

### Failed Deployment

CDK automatically rolls back on failure:
1. CloudFormation detects resource creation failure
2. Automatically deletes newly created resources
3. Restores previous stack state
4. Logs error in CloudFormation events

### Failed Database Initialization

Manual rollback required:
1. Connect to RDS via bastion or Lambda
2. Drop all tables: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
3. Re-run db-init Lambda

### Failed Tests

No rollback needed:
1. Infrastructure remains deployed
2. Fix code issues
3. Redeploy only affected Lambda functions
4. Re-run tests

## Success Criteria

### Deployment Success

- ✓ All CloudFormation stacks show UPDATE_COMPLETE
- ✓ All Lambda functions in Active state
- ✓ No import errors in CloudWatch logs
- ✓ Database initialized with schema and seed data

### Functional Success

- ✓ TEST.py shows 100% pass rate (24/24 tests)
- ✓ All API endpoints return valid responses
- ✓ No 502 Bad Gateway errors
- ✓ No timeout errors
- ✓ "READY FOR DEMO" status displayed

### Integration Readiness

- ✓ API Gateway URL accessible
- ✓ Cognito authentication working
- ✓ All CRUD operations functional
- ✓ Frontend can integrate without API changes
