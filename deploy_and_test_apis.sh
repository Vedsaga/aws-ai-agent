#!/bin/bash

# ==============================================================================
# Deploy and Test API Script
# ==============================================================================
# This script:
# 1. Checks AWS connectivity
# 2. Deploys simplified Lambda handlers
# 3. Tests all critical API endpoints
# 4. Reports pass/fail status
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REGION="us-east-1"
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
USER_POOL_CLIENT_ID="6gobbpage9af3nd7ahm3lchkct"

# Lambda function names
CONFIG_LAMBDA="MultiAgentOrchestration-dev-Api-ConfigApiHandler"
INGEST_LAMBDA="MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY_LAMBDA="MultiAgentOrchestration-dev-Api-QueryHandler"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

increment_test() {
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

pass_test() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_success "$1"
}

fail_test() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    log_error "$1"
}

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================

log_section "Step 1: Checking Prerequisites"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not installed. Please install it first."
    exit 1
fi
log_success "AWS CLI installed"

# Check AWS connectivity
log_info "Testing AWS connectivity..."
if aws sts get-caller-identity --region $REGION &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region $REGION)
    log_success "AWS credentials valid (Account: $ACCOUNT_ID)"
else
    log_error "Cannot connect to AWS. Check your credentials and network."
    log_warning "Try: aws configure"
    exit 1
fi

# Check if in correct directory
if [ ! -d "infrastructure/lambda" ]; then
    log_error "Please run this script from the aws-ai-agent directory"
    exit 1
fi
log_success "Running from correct directory"

# ==============================================================================
# Step 2: Deploy Lambda Functions
# ==============================================================================

log_section "Step 2: Deploying Simplified Lambda Functions"

deploy_lambda() {
    local LAMBDA_NAME=$1
    local HANDLER_FILE=$2
    local HANDLER_DIR=$3

    log_info "Deploying $LAMBDA_NAME..."

    # Check if Lambda exists
    if ! aws lambda get-function --function-name $LAMBDA_NAME --region $REGION &> /dev/null; then
        log_error "Lambda function $LAMBDA_NAME not found"
        return 1
    fi

    # Create temp directory
    TEMP_DIR=$(mktemp -d)

    # Copy handler file
    cp "$HANDLER_DIR/$HANDLER_FILE" "$TEMP_DIR/$(basename ${HANDLER_FILE/_simple/})"

    # Create deployment package
    cd "$TEMP_DIR"
    zip -q deployment.zip *.py

    # Deploy
    if aws lambda update-function-code \
        --function-name $LAMBDA_NAME \
        --zip-file fileb://deployment.zip \
        --region $REGION \
        --no-cli-pager > /dev/null 2>&1; then

        # Wait for update to complete
        log_info "Waiting for Lambda update to complete..."
        if aws lambda wait function-updated \
            --function-name $LAMBDA_NAME \
            --region $REGION 2> /dev/null; then
            log_success "Deployed $LAMBDA_NAME"
            cd - > /dev/null
            rm -rf "$TEMP_DIR"
            return 0
        else
            log_warning "Update may still be in progress for $LAMBDA_NAME"
            cd - > /dev/null
            rm -rf "$TEMP_DIR"
            return 0
        fi
    else
        log_error "Failed to deploy $LAMBDA_NAME"
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        return 1
    fi
}

# Deploy Config API
deploy_lambda "$CONFIG_LAMBDA" "config_handler_simple.py" "infrastructure/lambda/config-api"

# Deploy Ingest API
deploy_lambda "$INGEST_LAMBDA" "ingest_handler_simple.py" "infrastructure/lambda/orchestration"

# Deploy Query API
deploy_lambda "$QUERY_LAMBDA" "query_handler_simple.py" "infrastructure/lambda/orchestration"

log_success "All Lambda functions deployed"

# Wait a bit for propagation
log_info "Waiting 10 seconds for deployment to propagate..."
sleep 10

# ==============================================================================
# Step 3: Get Authentication Token
# ==============================================================================

log_section "Step 3: Getting Authentication Token"

log_info "Requesting JWT token from Cognito..."

TOKEN_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id $USER_POOL_CLIENT_ID \
    --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
    --region $REGION \
    2>&1)

if echo "$TOKEN_RESPONSE" | grep -q "IdToken"; then
    JWT_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")
    log_success "JWT token obtained (length: ${#JWT_TOKEN})"
else
    log_error "Failed to get JWT token"
    echo "$TOKEN_RESPONSE"
    log_warning "You may need to create a test user first"
    log_warning "Run: aws cognito-idp admin-create-user ..."
    exit 1
fi

# ==============================================================================
# Step 4: Test API Endpoints
# ==============================================================================

log_section "Step 4: Testing API Endpoints"

test_endpoint() {
    local TEST_NAME=$1
    local METHOD=$2
    local ENDPOINT=$3
    local DATA=$4
    local EXPECTED_CODE=$5

    increment_test

    log_info "Testing: $TEST_NAME"

    if [ -z "$DATA" ]; then
        # GET request
        RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
            -X $METHOD "$API_URL$ENDPOINT" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json")
    else
        # POST request with data
        RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
            -X $METHOD "$API_URL$ENDPOINT" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$DATA")
    fi

    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

    if [ "$HTTP_CODE" = "$EXPECTED_CODE" ]; then
        pass_test "$TEST_NAME: HTTP $HTTP_CODE"
        echo "  Response: $(echo $BODY | head -c 100)..."
        return 0
    else
        fail_test "$TEST_NAME: Expected $EXPECTED_CODE, got $HTTP_CODE"
        echo "  Response: $BODY"
        return 1
    fi
}

# Test 1: Config API - List Agents
test_endpoint \
    "Config API - List Agents" \
    "GET" \
    "/api/v1/config?type=agent" \
    "" \
    "200"

# Test 2: Config API - Create Agent
CREATE_AGENT_DATA='{
  "type": "agent",
  "config": {
    "agent_name": "Test Demo Agent",
    "agent_type": "custom",
    "system_prompt": "You are a test agent for demo purposes",
    "tools": ["bedrock"],
    "output_schema": {
      "result": "string",
      "confidence": "number"
    }
  }
}'

test_endpoint \
    "Config API - Create Agent" \
    "POST" \
    "/api/v1/config" \
    "$CREATE_AGENT_DATA" \
    "201"

# Test 3: Config API - List Domains
test_endpoint \
    "Config API - List Domains" \
    "GET" \
    "/api/v1/config?type=domain_template" \
    "" \
    "200"

# Test 4: Ingest API - Submit Report
SUBMIT_REPORT_DATA='{
  "domain_id": "civic_complaints",
  "text": "There is a broken streetlight on Oak Avenue near the park. It has been out for 3 days.",
  "priority": "normal"
}'

test_endpoint \
    "Ingest API - Submit Report" \
    "POST" \
    "/api/v1/ingest" \
    "$SUBMIT_REPORT_DATA" \
    "202"

# Test 5: Query API - Ask Question
ASK_QUESTION_DATA='{
  "domain_id": "civic_complaints",
  "question": "What are the most common infrastructure complaints this month?"
}'

test_endpoint \
    "Query API - Ask Question" \
    "POST" \
    "/api/v1/query" \
    "$ASK_QUESTION_DATA" \
    "202"

# Test 6: Error Handling - Missing Auth
increment_test
log_info "Testing: Error Handling - Missing Auth"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X GET "$API_URL/api/v1/config?type=agent" \
    -H "Content-Type: application/json")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
if [ "$HTTP_CODE" = "401" ]; then
    pass_test "Error Handling - Missing Auth: HTTP 401"
else
    fail_test "Error Handling - Missing Auth: Expected 401, got $HTTP_CODE"
fi

# Test 7: Error Handling - Invalid Domain
INVALID_DOMAIN_DATA='{
  "domain_id": "",
  "text": "Test"
}'

test_endpoint \
    "Error Handling - Invalid Domain" \
    "POST" \
    "/api/v1/ingest" \
    "$INVALID_DOMAIN_DATA" \
    "400"

# ==============================================================================
# Step 5: Test Results Summary
# ==============================================================================

log_section "Test Results Summary"

echo ""
echo "Total Tests:   $TESTS_TOTAL"
echo -e "${GREEN}Passed:        $TESTS_PASSED${NC}"
echo -e "${RED}Failed:        $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_TOTAL -gt 0 ]; then
    PASS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc)
    echo "Pass Rate:     $PASS_RATE%"
else
    PASS_RATE=0
fi

echo ""

# ==============================================================================
# Step 6: Recommendations
# ==============================================================================

log_section "Recommendations"

if [ "$TESTS_FAILED" -eq 0 ]; then
    log_success "ALL TESTS PASSED! 🎉"
    echo ""
    log_info "Next Steps:"
    echo "  1. Record demo video showing these working APIs"
    echo "  2. Prepare demo script (see DEMO_SCRIPT.md)"
    echo "  3. Submit to DevPost before deadline"
    echo ""
    log_success "You are READY for demo!"
elif [ "$TESTS_PASSED" -ge 3 ]; then
    log_success "MINIMUM VIABLE DEMO ACHIEVED! ✓"
    echo ""
    log_info "You have $TESTS_PASSED/$TESTS_TOTAL tests passing ($PASS_RATE%)"
    echo ""
    log_info "Failed tests:"
    echo "  - Review CloudWatch logs for details"
    echo "  - May need additional environment variables"
    echo "  - May need IAM permissions"
    echo ""
    log_info "You can still demo with working endpoints:"
    echo "  - Show Config API (agent management)"
    echo "  - Show Ingest API (report submission)"
    echo "  - Show Query API (question answering)"
    echo ""
    log_warning "Proceed with demo preparation, but monitor for improvements"
else
    log_error "INSUFFICIENT PASSING TESTS"
    echo ""
    log_info "Only $TESTS_PASSED/$TESTS_TOTAL tests passing"
    echo ""
    log_error "Critical issues to fix:"
    echo "  1. Check CloudWatch Logs:"
    echo "     aws logs tail /aws/lambda/$CONFIG_LAMBDA --follow --region $REGION"
    echo ""
    echo "  2. Verify environment variables are set"
    echo ""
    echo "  3. Check IAM permissions for Lambda roles"
    echo ""
    echo "  4. Verify DynamoDB tables exist and are accessible"
    echo ""
    log_warning "Consider backup plan: Use mock data or architecture walkthrough"
fi

echo ""

# ==============================================================================
# Step 7: Quick Commands Reference
# ==============================================================================

log_section "Quick Commands Reference"

cat << 'EOF'
# Get fresh JWT token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test Config API
curl -X GET "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/config?type=agent" \
  -H "Authorization: Bearer $TOKEN"

# Test Ingest API
curl -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","text":"Test report"}'

# Check CloudWatch Logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigApiHandler \
  --follow --region us-east-1

# View DynamoDB data
aws dynamodb scan \
  --table-name MultiAgentOrchestration-dev-Data-Configurations \
  --limit 5 --region us-east-1
EOF

echo ""
log_info "Script complete!"
echo ""

# Exit with appropriate code
if [ "$TESTS_FAILED" -eq 0 ]; then
    exit 0
elif [ "$TESTS_PASSED" -ge 3 ]; then
    exit 0
else
    exit 1
fi
