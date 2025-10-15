# Deployment and Testing Guide

This document provides comprehensive instructions for deploying and testing the Command Center Backend API.

## Table of Contents

1. [Deployment Scripts](#deployment-scripts)
2. [Data Population Scripts](#data-population-scripts)
3. [Testing Scripts](#testing-scripts)
4. [Quick Start](#quick-start)
5. [Troubleshooting](#troubleshooting)

---

## Deployment Scripts

### deploy.sh

Enhanced CDK deployment script with environment configuration and post-deployment validation.

**Location:** `./scripts/deploy.sh`

**Usage:**
```bash
./scripts/deploy.sh [--stage dev|staging|prod] [--skip-validation]
```

**Options:**
- `--stage`: Deployment stage (default: dev)
- `--skip-validation`: Skip post-deployment validation checks
- `--help`: Show help message

**Features:**
- ✅ Validates AWS credentials
- ✅ Loads environment variables from `.env.local`
- ✅ Builds TypeScript code
- ✅ Synthesizes CloudFormation template
- ✅ Deploys stack to AWS
- ✅ Retrieves and displays stack outputs
- ✅ Post-deployment validation:
  - DynamoDB table accessibility
  - API Gateway endpoint health
  - Bedrock Agent status

**Example:**
```bash
# Deploy to dev environment
./scripts/deploy.sh

# Deploy to production with validation
./scripts/deploy.sh --stage prod

# Deploy without validation
./scripts/deploy.sh --stage staging --skip-validation
```

**Post-Deployment:**
After successful deployment, the script displays:
- API endpoint URL
- DynamoDB table name
- Bedrock Agent ID
- Next steps for data population and testing

---

## Data Population Scripts

### populate-db.sh

Database population script with validation and rollback capability.

**Location:** `./scripts/populate-db.sh`

**Usage:**
```bash
./scripts/populate-db.sh [--table-name TABLE_NAME] [--backup] [--rollback BACKUP_ID]
```

**Options:**
- `--table-name`: DynamoDB table name (auto-detected if not provided)
- `--backup`: Create backup before populating
- `--rollback`: Rollback to specified backup ID
- `--help`: Show help message

**Features:**
- ✅ Auto-detects table name from CloudFormation stack
- ✅ Creates backups before population
- ✅ Validates data insertion
- ✅ Checks data distribution across days and domains
- ✅ Verifies required fields in sample items
- ✅ Rollback capability to previous state

**Example:**
```bash
# Populate database (auto-detect table)
./scripts/populate-db.sh

# Populate with backup
./scripts/populate-db.sh --backup

# Rollback to previous state
./scripts/populate-db.sh --rollback 20231215_143022

# Specify table name explicitly
./scripts/populate-db.sh --table-name MasterEventTimeline
```

**Validation Checks:**
1. Item count verification
2. Data distribution across 7 days (DAY_0 to DAY_6)
3. Data distribution across 5 domains (MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION)
4. Required field presence (Day, Timestamp, eventId, domain, severity, geojson, summary)

**Backup Management:**
- Backups are stored in `./backups/` directory
- Backup filename format: `YYYYMMDD_HHMMSS.json`
- Use `--rollback` with backup ID to restore

---

## Testing Scripts

### Integration Tests

Tests each API endpoint with various parameters and validates response formats.

**Location:** `./scripts/run-integration-tests.sh`

**Usage:**
```bash
./scripts/run-integration-tests.sh [--endpoint URL] [--api-key KEY]
```

**Options:**
- `--endpoint`: API endpoint URL (auto-detected if not provided)
- `--api-key`: API key for authentication (optional)
- `--help`: Show help message

**Test Coverage:**
- ✅ GET /data/updates endpoint
  - Basic requests with since parameter
  - Domain filtering
  - All valid domains
  - Error cases (missing parameters, invalid domain)
  - Response structure validation
- ✅ POST /agent/query endpoint
  - Natural language queries
  - Session continuity
  - Map state context
  - Full response structure
  - Error cases
- ✅ POST /agent/action endpoint
  - Pre-defined actions
  - Action payloads
  - Response structure
  - Error cases
- ✅ CORS configuration

**Example:**
```bash
# Run integration tests (auto-detect endpoint)
npm run test:integration

# Or use script directly
./scripts/run-integration-tests.sh

# Specify endpoint and API key
./scripts/run-integration-tests.sh \
  --endpoint https://abc123.execute-api.us-east-1.amazonaws.com/prod \
  --api-key your-api-key-here
```

**Output:**
- ✓/✗ for each test
- Summary with pass/fail counts
- Failed test details with error messages

### End-to-End Tests

Tests complete flows including agent tool invocation, performance, and concurrency.

**Location:** `./scripts/run-e2e-tests.sh`

**Usage:**
```bash
./scripts/run-e2e-tests.sh [--endpoint URL] [--api-key KEY]
```

**Options:**
- `--endpoint`: API endpoint URL (auto-detected if not provided)
- `--api-key`: API key for authentication (optional)
- `--help`: Show help message

**Test Coverage:**
- ✅ Complete data flow (API Gateway → Lambda → DynamoDB)
- ✅ Agent tool invocation flow
  - Single tool calls
  - Multiple tool calls
  - Location-based queries
- ✅ Response time validation
  - Updates endpoint: P95 < 500ms
  - Agent endpoint: P95 < 3s
- ✅ Concurrent request handling
  - 10 concurrent updates requests
  - 10 concurrent agent requests
  - Mixed concurrent requests
- ✅ Error recovery

**Example:**
```bash
# Run E2E tests (auto-detect endpoint)
npm run test:e2e

# Or use script directly
./scripts/run-e2e-tests.sh

# Specify endpoint
./scripts/run-e2e-tests.sh --endpoint https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

**Performance Metrics:**
The E2E tests measure and report:
- Min, Max, Average response times
- P50, P95, P99 percentiles
- Validation against SLA thresholds

---

## Quick Start

### Complete Deployment and Setup

```bash
# 1. Deploy the stack
./scripts/deploy.sh --stage dev

# 2. Populate the database with backup
./scripts/populate-db.sh --backup

# 3. Run integration tests
npm run test:integration

# 4. Run E2E tests
npm run test:e2e
```

### Using npm Scripts

The following npm scripts are available:

```bash
# Build TypeScript
npm run build

# Deploy stack
npm run deploy

# Populate database
npm run populate-db

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e

# Destroy stack
npm run destroy
```

---

## Troubleshooting

### Deployment Issues

**Problem:** AWS credentials not configured
```
Error: AWS CLI is not configured or credentials are invalid
```
**Solution:**
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1
```

**Problem:** CDK bootstrap required
```
Error: This stack uses assets, so the toolkit stack must be deployed
```
**Solution:**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

**Problem:** TypeScript build fails
```
Error: TypeScript build failed
```
**Solution:**
```bash
# Check for syntax errors
npm run build

# Install dependencies
npm install
```

### Data Population Issues

**Problem:** Table not found
```
Error: Could not auto-detect table name
```
**Solution:**
```bash
# Specify table name explicitly
./scripts/populate-db.sh --table-name MasterEventTimeline

# Or check CloudFormation outputs
aws cloudformation describe-stacks --stack-name CommandCenterBackendStack
```

**Problem:** No items inserted
```
Validation failed: No items were inserted
```
**Solution:**
- Check DynamoDB write permissions
- Verify table exists and is active
- Check for throttling in CloudWatch logs

**Problem:** Need to rollback
```bash
# List available backups
ls -la ./backups/

# Rollback to specific backup
./scripts/populate-db.sh --rollback 20231215_143022
```

### Testing Issues

**Problem:** API endpoint not found
```
Error: Could not auto-detect API endpoint
```
**Solution:**
```bash
# Get endpoint from CloudFormation
aws cloudformation describe-stacks \
  --stack-name CommandCenterBackendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Use endpoint explicitly
./scripts/run-integration-tests.sh --endpoint https://your-endpoint.amazonaws.com
```

**Problem:** Tests fail with 403 Forbidden
```
Error: Request failed with status code 403
```
**Solution:**
- Provide API key: `--api-key your-key`
- Check API Gateway authentication settings
- Verify CORS configuration

**Problem:** Agent tests timeout
```
Error: timeout of 30000ms exceeded
```
**Solution:**
- Bedrock Agent may be slow on first invocation (cold start)
- Check Bedrock Agent status in AWS console
- Verify Action Group Lambda is deployed
- Check CloudWatch logs for errors

**Problem:** Performance tests fail
```
P95 response time (650ms) should be under 500ms
```
**Solution:**
- Run tests multiple times (first run may be slower due to cold starts)
- Check DynamoDB provisioned capacity
- Review Lambda memory allocation
- Check for throttling in CloudWatch

### General Tips

1. **Check CloudWatch Logs:**
   ```bash
   # View Lambda logs
   aws logs tail /aws/lambda/UpdatesHandlerLambda --follow
   ```

2. **Verify Stack Status:**
   ```bash
   aws cloudformation describe-stacks --stack-name CommandCenterBackendStack
   ```

3. **Test Individual Endpoints:**
   ```bash
   # Test updates endpoint
   curl "${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z"
   
   # Test query endpoint
   curl -X POST "${API_ENDPOINT}/agent/query" \
     -H "Content-Type: application/json" \
     -d '{"text":"Show me incidents"}'
   ```

4. **Monitor DynamoDB:**
   ```bash
   # Check item count
   aws dynamodb scan --table-name MasterEventTimeline --select COUNT
   
   # Sample items
   aws dynamodb scan --table-name MasterEventTimeline --limit 5
   ```

---

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)

---

## Support

For issues or questions:
1. Check CloudWatch logs for detailed error messages
2. Review the troubleshooting section above
3. Verify all prerequisites are met
4. Check AWS service quotas and limits
