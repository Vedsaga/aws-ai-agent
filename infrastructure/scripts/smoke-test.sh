#!/bin/bash

# Multi-Agent Orchestration System - Smoke Test Script
# This script verifies that the deployment is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

# Load environment
load_environment() {
    if [ ! -f .env ]; then
        log_error ".env file not found"
        exit 1
    fi
    
    export $(grep -v '^#' .env | xargs)
    export AWS_REGION=${AWS_REGION:-us-east-1}
    export STAGE=${STAGE:-dev}
}

# Get stack outputs
get_stack_outputs() {
    log_info "Retrieving stack outputs..."
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Api \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    CLIENT_ID=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Auth \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    OS_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Data \
        --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchEndpoint`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
    
    EVIDENCE_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name MultiAgentOrchestration-${STAGE}-Storage \
        --query 'Stacks[0].Outputs[?OutputKey==`EvidenceBucketName`].OutputValue' \
        --output text \
        --region $AWS_REGION 2>/dev/null || echo "")
}

# Test 1: Verify all stacks exist
test_stacks_exist() {
    log_test "Verifying CloudFormation stacks..."
    
    STACKS=("Auth" "Storage" "Data" "Api")
    
    for stack in "${STACKS[@]}"; do
        STACK_NAME="MultiAgentOrchestration-${STAGE}-${stack}"
        STATUS=$(aws cloudformation describe-stacks \
            --stack-name $STACK_NAME \
            --query 'Stacks[0].StackStatus' \
            --output text \
            --region $AWS_REGION 2>/dev/null || echo "NOT_FOUND")
        
        if [[ "$STATUS" == "CREATE_COMPLETE" || "$STATUS" == "UPDATE_COMPLETE" ]]; then
            log_success "Stack $stack exists and is healthy"
        else
            log_error "Stack $stack status: $STATUS"
        fi
    done
}

# Test 2: Verify Cognito user pool
test_cognito() {
    log_test "Verifying Cognito User Pool..."
    
    if [ -z "$USER_POOL_ID" ]; then
        log_error "User Pool ID not found"
        return
    fi
    
    POOL_STATUS=$(aws cognito-idp describe-user-pool \
        --user-pool-id $USER_POOL_ID \
        --region $AWS_REGION \
        --query 'UserPool.Status' \
        --output text 2>/dev/null || echo "ERROR")
    
    if [ "$POOL_STATUS" == "Enabled" ]; then
        log_success "Cognito User Pool is enabled"
    else
        log_error "Cognito User Pool status: $POOL_STATUS"
    fi
    
    # Check test user exists
    if aws cognito-idp admin-get-user \
        --user-pool-id $USER_POOL_ID \
        --username testuser \
        --region $AWS_REGION &> /dev/null; then
        log_success "Test user 'testuser' exists"
    else
        log_error "Test user 'testuser' not found"
    fi
}

# Test 3: Verify S3 buckets
test_s3() {
    log_test "Verifying S3 buckets..."
    
    if [ -z "$EVIDENCE_BUCKET" ]; then
        log_error "Evidence bucket name not found"
        return
    fi
    
    if aws s3 ls s3://$EVIDENCE_BUCKET --region $AWS_REGION &> /dev/null; then
        log_success "Evidence bucket exists and is accessible"
    else
        log_error "Evidence bucket not accessible"
    fi
}

# Test 4: Verify DynamoDB tables
test_dynamodb() {
    log_test "Verifying DynamoDB tables..."
    
    TABLES=("configurations" "user_sessions" "tool_catalog" "tool_permissions")
    
    for table in "${TABLES[@]}"; do
        TABLE_NAME="multiagentorchestration-${STAGE}-${table}"
        STATUS=$(aws dynamodb describe-table \
            --table-name $TABLE_NAME \
            --region $AWS_REGION \
            --query 'Table.TableStatus' \
            --output text 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$STATUS" == "ACTIVE" ]; then
            log_success "DynamoDB table $table is active"
        else
            log_error "DynamoDB table $table status: $STATUS"
        fi
    done
}

# Test 5: Verify RDS database
test_rds() {
    log_test "Verifying RDS database..."
    
    if [ -z "$DB_ENDPOINT" ]; then
        log_error "Database endpoint not found"
        return
    fi
    
    DB_INSTANCE="multiagentorchestration-${STAGE}-postgres"
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier $DB_INSTANCE \
        --region $AWS_REGION \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$STATUS" == "available" ]; then
        log_success "RDS database is available"
    else
        log_error "RDS database status: $STATUS"
    fi
}

# Test 6: Verify OpenSearch domain
test_opensearch() {
    log_test "Verifying OpenSearch domain..."
    
    if [ -z "$OS_ENDPOINT" ]; then
        log_error "OpenSearch endpoint not found"
        return
    fi
    
    DOMAIN_NAME="multiagentorchestration-${STAGE}-opensearch"
    STATUS=$(aws opensearch describe-domain \
        --domain-name $DOMAIN_NAME \
        --region $AWS_REGION \
        --query 'DomainStatus.Processing' \
        --output text 2>/dev/null || echo "ERROR")
    
    if [ "$STATUS" == "False" ]; then
        log_success "OpenSearch domain is active"
    else
        log_error "OpenSearch domain is processing or unavailable"
    fi
}

# Test 7: Test authentication
test_authentication() {
    log_test "Testing authentication..."
    
    if [ -z "$CLIENT_ID" ]; then
        log_error "Client ID not found"
        return
    fi
    
    # Get credentials from environment
    TEST_USERNAME="${TEST_USERNAME:-testuser}"
    TEST_PASSWORD="${TEST_PASSWORD}"
    
    if [ -z "$TEST_PASSWORD" ]; then
        log_error "TEST_PASSWORD not set in .env file"
        return
    fi
    
    TOKEN=$(aws cognito-idp initiate-auth \
        --auth-flow USER_PASSWORD_AUTH \
        --client-id $CLIENT_ID \
        --auth-parameters USERNAME=$TEST_USERNAME,PASSWORD="$TEST_PASSWORD" \
        --region $AWS_REGION \
        --query 'AuthenticationResult.IdToken' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$TOKEN" ]; then
        log_success "Authentication successful"
        export JWT_TOKEN=$TOKEN
    else
        log_error "Authentication failed"
    fi
}

# Test 8: Test API Gateway
test_api_gateway() {
    log_test "Testing API Gateway..."
    
    if [ -z "$API_URL" ]; then
        log_error "API URL not found"
        return
    fi
    
    # Test health endpoint (if exists) or just check API is reachable
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_CODE" != "000" ]]; then
        log_success "API Gateway is reachable (HTTP $HTTP_CODE)"
    else
        log_error "API Gateway is not reachable"
    fi
}

# Test 9: Test config API endpoint
test_config_api() {
    log_test "Testing config API endpoint..."
    
    if [ -z "$API_URL" ] || [ -z "$JWT_TOKEN" ]; then
        log_error "API URL or JWT token not available"
        return
    fi
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        "${API_URL}api/v1/config/agents" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "404" ]]; then
        log_success "Config API endpoint is accessible"
    else
        log_error "Config API endpoint returned HTTP $HTTP_CODE"
    fi
}

# Test 10: Test ingest endpoint
test_ingest_api() {
    log_test "Testing ingest API endpoint..."
    
    if [ -z "$API_URL" ] || [ -z "$JWT_TOKEN" ]; then
        log_error "API URL or JWT token not available"
        return
    fi
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"domain_id":"civic-complaints","text":"Test smoke test incident","images":[]}' \
        "${API_URL}api/v1/ingest" 2>/dev/null || echo "000")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "202" ]]; then
        log_success "Ingest API endpoint is working"
    else
        log_error "Ingest API endpoint returned HTTP $HTTP_CODE"
    fi
}

# Test 11: Verify Lambda functions
test_lambda_functions() {
    log_test "Verifying Lambda functions..."
    
    # Count Lambda functions with our prefix
    FUNCTION_COUNT=$(aws lambda list-functions \
        --region $AWS_REGION \
        --query "Functions[?starts_with(FunctionName, 'MultiAgentOrchestration-${STAGE}')].FunctionName" \
        --output text 2>/dev/null | wc -w)
    
    if [ "$FUNCTION_COUNT" -gt 0 ]; then
        log_success "Found $FUNCTION_COUNT Lambda functions"
    else
        log_error "No Lambda functions found"
    fi
}

# Display summary
display_summary() {
    echo ""
    echo "=========================================="
    echo "SMOKE TEST SUMMARY"
    echo "=========================================="
    echo ""
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All smoke tests passed! ✓"
        echo ""
        log_info "Your deployment is ready to use!"
        echo ""
        echo "API URL: $API_URL"
        echo "Test User: ${TEST_USERNAME:-testuser}"
        echo "Password: (set in .env file)"
        echo ""
        return 0
    else
        log_error "Some smoke tests failed. Please review the output above."
        echo ""
        log_info "Common issues:"
        echo "  - Resources still being created (wait a few minutes)"
        echo "  - Permissions issues (check IAM roles)"
        echo "  - Network connectivity (check VPC/security groups)"
        echo ""
        return 1
    fi
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "Multi-Agent Orchestration System"
    echo "Smoke Test Script"
    echo "=========================================="
    echo ""
    
    # Change to infrastructure directory
    cd "$(dirname "$0")/.."
    
    load_environment
    get_stack_outputs
    
    echo ""
    log_info "Running smoke tests..."
    echo ""
    
    test_stacks_exist
    test_cognito
    test_s3
    test_dynamodb
    test_rds
    test_opensearch
    test_authentication
    test_api_gateway
    test_lambda_functions
    test_config_api
    test_ingest_api
    
    display_summary
}

main "$@"
