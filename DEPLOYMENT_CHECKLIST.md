# Deployment Checklist for Orchestrator Fix

## Pre-Deployment Verification

### 1. Check Database Seeding
```bash
# Verify agents are seeded in RDS
python3 check_agents_seeded.py
```

**Expected output:**
- ✓ Found 12 builtin agents
- ✓ 3 ingestion agents
- ✓ 6 query agents
- ✓ 3 management agents
- ✓ Found civic_complaints domain

### 2. Review Code Changes
- [x] `orchestrator_handler.py` - Uses RDS instead of DynamoDB
- [x] `rds_utils.py` - Enhanced with system tenant fallback
- [x] Removed legacy incidents tables from schema
- [x] Updated fallback agent IDs to match database

### 3. Check Dependencies
```bash
# Verify rds_utils.py has required functions
grep -n "def get_domain_by_id" infrastructure/lambda/orchestration/rds_utils.py
grep -n "def get_playbook" infrastructure/lambda/orchestration/rds_utils.py
grep -n "def get_agents_by_ids" infrastructure/lambda/orchestration/rds_utils.py
```

## Deployment Steps

### 1. Deploy Database Changes
```bash
cd infrastructure

# Deploy data stack (if schema changed)
cdk deploy MultiAgentOrchestration-dev-Data

# Verify database initialization
aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Data-DbInit \
  --payload '{"seed_builtin_data": true}' \
  response.json

cat response.json
```

### 2. Deploy Orchestration Stack
```bash
# Deploy orchestration stack with updated handler
cdk deploy MultiAgentOrchestration-dev-Orchestration

# Verify deployment
aws lambda get-function \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --query 'Configuration.LastModified'
```

### 3. Verify Lambda Layers
```bash
# Check that orchestrator has access to rds_utils
aws lambda get-function \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --query 'Configuration.Layers'
```

## Post-Deployment Testing

### 1. Test Domain Loading
```bash
# Invoke orchestrator with test payload
cat > test_payload.json << EOF
{
  "job_id": "test_001",
  "job_type": "ingest",
  "domain_id": "civic_complaints",
  "text": "Pothole on Main Street",
  "tenant_id": "system",
  "user_id": "test-user"
}
EOF

aws lambda invoke \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --payload file://test_payload.json \
  response.json

cat response.json
```

**Expected in CloudWatch Logs:**
```
Loading domain from RDS: civic_complaints, tenant: system
Loaded domain civic_complaints: Civic Complaints (tenant: system)
Loading ingestion playbook for domain: civic_complaints
Loaded agent IDs from playbook: ['builtin-ingestion-geo', 'builtin-ingestion-temporal', 'builtin-ingestion-entity']
Agent pipeline: ['builtin-ingestion-geo', 'builtin-ingestion-temporal', 'builtin-ingestion-entity']
Loading 3 agents from RDS
Loaded agent from RDS: builtin-ingestion-geo
Loaded agent from RDS: builtin-ingestion-temporal
Loaded agent from RDS: builtin-ingestion-entity
```

### 2. Check CloudWatch Logs
```bash
# Get recent logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --follow \
  --format short
```

**Look for:**
- ✓ "RDS utils loaded successfully"
- ✓ "Loading domain from RDS"
- ✓ "Loaded agent IDs from playbook"
- ✓ "Loaded agent from RDS: builtin-ingestion-geo"
- ❌ "Domain not found in RDS" (should NOT appear)
- ❌ "Agent not found in RDS" (should NOT appear)

### 3. Run E2E Tests
```bash
# Set environment variables
export API_BASE_URL="https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1"
export COGNITO_CLIENT_ID="6gobbpage9af3nd7ahm3lchkct"
export TEST_USERNAME="testuser"
export TEST_PASSWORD="TestPassword123!"
export AWS_REGION="us-east-1"

# Run E2E test
python3 test_e2e_flows.py
```

**Expected output:**
```
================================================================================
                        END-TO-END FLOW TESTS
================================================================================

TEST 1: DATA INGESTION FLOW
────────────────────────────────────────────────────────────────────────────────
Step 1: Create Domain with Ingestion Playbook (Using Builtin Agents)
✓ Domain created: test_domain_1234567890

Step 2: Submit Report for Ingestion (Triggers 3 Agents)
  Expected agents to execute:
    - builtin-ingestion-geo: Extract location (123 Main Street)
    - builtin-ingestion-temporal: Extract time (2:30 PM) and urgency
    - builtin-ingestion-entity: Extract entities (John Doe, Jane Smith)
✓ Report submitted: inc_abc12345

Step 3: Wait for Ingestion Processing & Verify Agent Execution
✓ Ingestion completed! Verifying agent outputs...

Agent Execution Results:
  ✓ Geo Agent: location=123 Main Street, confidence=0.85
  ✓ Temporal Agent: urgency=urgent, timestamp=2024-10-22T14:30:00Z
  ✓ Entity Agent: entities=2, sentiment=NEGATIVE

TEST 2: DATA QUERY FLOW
[Similar success output]

TEST 3: DATA MANAGEMENT FLOW
[Similar success output]

================================================================================
                            TEST SUMMARY
================================================================================
  Ingestion Flow: ✓ PASS
  Query Flow: ✓ PASS
  Management Flow: ✓ PASS

✓ All end-to-end flows passed!
```

## Rollback Plan

If issues occur:

### 1. Revert Code Changes
```bash
cd infrastructure
git revert HEAD
cdk deploy MultiAgentOrchestration-dev-Orchestration
```

### 2. Check Previous Version
```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler

# Rollback to previous version
aws lambda update-alias \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --name PROD \
  --function-version <previous-version>
```

## Monitoring

### Key Metrics to Watch:
1. **Lambda Errors** - Should remain at 0
2. **Lambda Duration** - May increase slightly (RDS queries)
3. **RDS Connections** - Monitor connection pool
4. **Agent Execution Success Rate** - Should be >95%

### CloudWatch Alarms:
```bash
# Create alarm for orchestrator errors
aws cloudwatch put-metric-alarm \
  --alarm-name orchestrator-errors \
  --alarm-description "Alert on orchestrator errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler
```

## Success Criteria

- [x] Code changes deployed successfully
- [ ] CloudWatch logs show RDS loading
- [ ] Agents loaded with correct IDs
- [ ] E2E tests pass (all 3 flows)
- [ ] No increase in error rate
- [ ] Response times acceptable (<5s for ingestion)

## Troubleshooting

### Issue: "Domain not found in RDS"
**Solution:** Check that domain exists in database
```sql
SELECT domain_id, domain_name, tenant_id 
FROM domain_configurations 
WHERE domain_id = 'civic_complaints';
```

### Issue: "Agent not found in RDS"
**Solution:** Check that agents are seeded
```sql
SELECT agent_id, agent_name, tenant_id, is_inbuilt 
FROM agent_definitions 
WHERE is_inbuilt = true;
```

### Issue: "RDS connection timeout"
**Solution:** Check VPC security groups and Lambda VPC config
```bash
aws lambda get-function-configuration \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --query 'VpcConfig'
```

### Issue: "Module 'rds_utils' not found"
**Solution:** Ensure rds_utils.py is in Lambda package
```bash
# Check Lambda package contents
aws lambda get-function \
  --function-name MultiAgentOrchestration-dev-Orchestration-OrchestratorHandler \
  --query 'Code.Location' \
  --output text | xargs curl -o lambda.zip

unzip -l lambda.zip | grep rds_utils
```

## Sign-Off

- [ ] Code reviewed and approved
- [ ] Database verified and seeded
- [ ] Deployment successful
- [ ] Tests passing
- [ ] Monitoring in place
- [ ] Documentation updated

**Deployed by:** _________________
**Date:** _________________
**Verified by:** _________________
