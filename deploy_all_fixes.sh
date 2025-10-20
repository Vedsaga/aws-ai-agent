#!/bin/bash

# Comprehensive API Fix Deployment Script
# Deploys all simplified Lambda handlers to fix 500 errors
# Run this when AWS services are back online

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "Multi-Agent Orchestration System"
echo "Complete API Fix Deployment"
echo "=========================================="
echo ""

# Configuration
REGION="us-east-1"
USER_POOL_CLIENT="6gobbpage9af3nd7ahm3lchkct"
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

# Lambda function names
CONFIG_LAMBDA="MultiAgentOrchestration-dev-Api-ConfigHandler"
INGEST_LAMBDA="MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY_LAMBDA="MultiAgentOrchestration-dev-Api-QueryHandler"

DEPLOY_DIR="/tmp/lambda_fixes"
mkdir -p $DEPLOY_DIR

# ============================================================================
# Step 1: Check AWS Availability
# ============================================================================

echo -e "${BLUE}Step 1: Checking AWS service availability...${NC}"

if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to AWS${NC}"
    echo "Please check your AWS credentials and try again"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: $ACCOUNT_ID${NC}"

# Test Lambda API
if ! aws lambda list-functions --region $REGION --max-items 1 &> /dev/null; then
    echo -e "${RED}ERROR: AWS Lambda API is not available${NC}"
    echo "AWS may still be experiencing issues. Please try again in a few minutes."
    exit 1
fi
echo -e "${GREEN}✓ AWS Lambda API is available${NC}"

# Test Cognito
if ! aws cognito-idp describe-user-pool --user-pool-id us-east-1_7QZ7Y6Gbl --region $REGION &> /dev/null; then
    echo -e "${YELLOW}⚠ AWS Cognito API is not available${NC}"
    echo "Will proceed but authentication testing may fail"
fi

echo ""

# ============================================================================
# Step 2: Package Lambda Functions
# ============================================================================

echo -e "${BLUE}Step 2: Packaging Lambda functions...${NC}"

# Package Config API
echo -e "${CYAN}Packaging Config API...${NC}"
python3 << 'PYEOF'
import zipfile
import os
import shutil

deploy_dir = "/tmp/lambda_fixes"
source_file = "infrastructure/lambda/config-api/config_handler_simple.py"
dest_file = os.path.join(deploy_dir, "config_handler.py")
zip_path = os.path.join(deploy_dir, "config_deploy.zip")

if os.path.exists(source_file):
    shutil.copy(source_file, dest_file)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dest_file, "config_handler.py")
    print(f"✓ Config API packaged: {os.path.getsize(zip_path):,} bytes")
else:
    print(f"✗ ERROR: {source_file} not found")
    exit(1)
PYEOF

# Package Ingest API
echo -e "${CYAN}Packaging Ingest API...${NC}"
python3 << 'PYEOF'
import zipfile
import os
import shutil

deploy_dir = "/tmp/lambda_fixes"
source_file = "infrastructure/lambda/orchestration/ingest_handler_simple.py"
dest_file = os.path.join(deploy_dir, "ingest_handler.py")
zip_path = os.path.join(deploy_dir, "ingest_deploy.zip")

if os.path.exists(source_file):
    shutil.copy(source_file, dest_file)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dest_file, "ingest_handler.py")
    print(f"✓ Ingest API packaged: {os.path.getsize(zip_path):,} bytes")
else:
    print(f"✗ ERROR: {source_file} not found")
    exit(1)
PYEOF

# Package Query API
echo -e "${CYAN}Packaging Query API...${NC}"
python3 << 'PYEOF'
import zipfile
import os
import shutil

deploy_dir = "/tmp/lambda_fixes"
source_file = "infrastructure/lambda/orchestration/query_handler_simple.py"
dest_file = os.path.join(deploy_dir, "query_handler.py")
zip_path = os.path.join(deploy_dir, "query_deploy.zip")

if os.path.exists(source_file):
    shutil.copy(source_file, dest_file)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(dest_file, "query_handler.py")
    print(f"✓ Query API packaged: {os.path.getsize(zip_path):,} bytes")
else:
    print(f"✗ ERROR: {source_file} not found")
    exit(1)
PYEOF

echo ""

# ============================================================================
# Step 3: Deploy Lambda Functions
# ============================================================================

echo -e "${BLUE}Step 3: Deploying Lambda functions...${NC}"

# Deploy Config API
echo -e "${CYAN}Deploying Config API...${NC}"
aws lambda update-function-code \
    --function-name $CONFIG_LAMBDA \
    --zip-file fileb://$DEPLOY_DIR/config_deploy.zip \
    --region $REGION \
    --no-cli-pager > /dev/null

echo "Waiting for Config API update to complete..."
aws lambda wait function-updated \
    --function-name $CONFIG_LAMBDA \
    --region $REGION

echo -e "${GREEN}✓ Config API deployed${NC}"

# Deploy Ingest API
echo -e "${CYAN}Deploying Ingest API...${NC}"
aws lambda update-function-code \
    --function-name $INGEST_LAMBDA \
    --zip-file fileb://$DEPLOY_DIR/ingest_deploy.zip \
    --region $REGION \
    --no-cli-pager > /dev/null

echo "Waiting for Ingest API update to complete..."
aws lambda wait function-updated \
    --function-name $INGEST_LAMBDA \
    --region $REGION

echo -e "${GREEN}✓ Ingest API deployed${NC}"

# Deploy Query API
echo -e "${CYAN}Deploying Query API...${NC}"
aws lambda update-function-code \
    --function-name $QUERY_LAMBDA \
    --zip-file fileb://$DEPLOY_DIR/query_deploy.zip \
    --region $REGION \
    --no-cli-pager > /dev/null

echo "Waiting for Query API update to complete..."
aws lambda wait function-updated \
    --function-name $QUERY_LAMBDA \
    --region $REGION

echo -e "${GREEN}✓ Query API deployed${NC}"
echo ""

# ============================================================================
# Step 4: Test APIs
# ============================================================================

echo -e "${BLUE}Step 4: Testing APIs...${NC}"

# Get JWT token
echo -e "${CYAN}Getting authentication token...${NC}"
TOKEN_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id $USER_POOL_CLIENT \
    --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
    --region $REGION \
    2>&1)

if echo "$TOKEN_RESPONSE" | grep -q "IdToken"; then
    JWT_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")
    echo -e "${GREEN}✓ JWT token obtained${NC}"
else
    echo -e "${YELLOW}⚠ Could not get JWT token${NC}"
    echo "Authentication may not be working yet"
    JWT_TOKEN=""
fi

echo ""

# Test Config API
echo -e "${CYAN}Testing Config API (GET /api/v1/config?type=agent)...${NC}"
if [ -n "$JWT_TOKEN" ]; then
    CONFIG_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X GET "$API_URL/api/v1/config?type=agent" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json")

    CONFIG_HTTP_CODE=$(echo "$CONFIG_RESPONSE" | tail -n1)
    CONFIG_BODY=$(echo "$CONFIG_RESPONSE" | head -n-1)

    if [ "$CONFIG_HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Config API working! (HTTP 200)${NC}"
        echo "$CONFIG_BODY" | python3 -m json.tool 2>/dev/null | head -10
    else
        echo -e "${RED}✗ Config API returned HTTP $CONFIG_HTTP_CODE (expected 200)${NC}"
        echo "$CONFIG_BODY"
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no JWT token)${NC}"
fi

echo ""

# Test Ingest API
echo -e "${CYAN}Testing Ingest API (POST /api/v1/ingest)...${NC}"
if [ -n "$JWT_TOKEN" ]; then
    INGEST_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_URL/api/v1/ingest" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "domain_id": "civic_complaints",
            "text": "Test report: Pothole on Main Street needs repair."
        }')

    INGEST_HTTP_CODE=$(echo "$INGEST_RESPONSE" | tail -n1)
    INGEST_BODY=$(echo "$INGEST_RESPONSE" | head -n-1)

    if [ "$INGEST_HTTP_CODE" = "202" ]; then
        echo -e "${GREEN}✓ Ingest API working! (HTTP 202)${NC}"
        echo "$INGEST_BODY" | python3 -m json.tool 2>/dev/null
    else
        echo -e "${RED}✗ Ingest API returned HTTP $INGEST_HTTP_CODE (expected 202)${NC}"
        echo "$INGEST_BODY"
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no JWT token)${NC}"
fi

echo ""

# Test Query API
echo -e "${CYAN}Testing Query API (POST /api/v1/query)...${NC}"
if [ -n "$JWT_TOKEN" ]; then
    QUERY_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$API_URL/api/v1/query" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "domain_id": "civic_complaints",
            "question": "What are the most common complaints?"
        }')

    QUERY_HTTP_CODE=$(echo "$QUERY_RESPONSE" | tail -n1)
    QUERY_BODY=$(echo "$QUERY_RESPONSE" | head -n-1)

    if [ "$QUERY_HTTP_CODE" = "202" ]; then
        echo -e "${GREEN}✓ Query API working! (HTTP 202)${NC}"
        echo "$QUERY_BODY" | python3 -m json.tool 2>/dev/null
    else
        echo -e "${RED}✗ Query API returned HTTP $QUERY_HTTP_CODE (expected 202)${NC}"
        echo "$QUERY_BODY"
    fi
else
    echo -e "${YELLOW}⊘ Skipped (no JWT token)${NC}"
fi

echo ""

# ============================================================================
# Step 5: Generate Summary
# ============================================================================

echo -e "${BLUE}Step 5: Deployment Summary${NC}"
echo ""

TOTAL_APIS=3
WORKING_APIS=0

if [ -n "$JWT_TOKEN" ]; then
    [ "$CONFIG_HTTP_CODE" = "200" ] && WORKING_APIS=$((WORKING_APIS + 1))
    [ "$INGEST_HTTP_CODE" = "202" ] && WORKING_APIS=$((WORKING_APIS + 1))
    [ "$QUERY_HTTP_CODE" = "202" ] && WORKING_APIS=$((WORKING_APIS + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "API Status: ${WORKING_APIS}/${TOTAL_APIS} working"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    [ "$CONFIG_HTTP_CODE" = "200" ] && echo -e "✓ Config API:  ${GREEN}Working${NC}" || echo -e "✗ Config API:  ${RED}Not Working${NC}"
    [ "$INGEST_HTTP_CODE" = "202" ] && echo -e "✓ Ingest API:  ${GREEN}Working${NC}" || echo -e "✗ Ingest API:  ${RED}Not Working${NC}"
    [ "$QUERY_HTTP_CODE" = "202" ] && echo -e "✓ Query API:   ${GREEN}Working${NC}" || echo -e "✗ Query API:   ${RED}Not Working${NC}"
    echo ""

    if [ $WORKING_APIS -eq $TOTAL_APIS ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✓✓✓ SUCCESS! All APIs are working! ✓✓✓${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    elif [ $WORKING_APIS -gt 0 ]; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}⚠ PARTIAL SUCCESS: Some APIs working${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}✗ FAILURE: No APIs working${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not test APIs (authentication failed)${NC}"
    echo "Lambda functions deployed but testing incomplete"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ============================================================================
# Next Steps
# ============================================================================

echo ""
echo -e "${MAGENTA}NEXT STEPS:${NC}"
echo ""

if [ -n "$JWT_TOKEN" ] && [ $WORKING_APIS -gt 0 ]; then
    echo "1. Record demo video showing working APIs"
    echo "2. Create architecture diagram"
    echo "3. Update README with deployment status"
    echo "4. Run full test suite: ./run_tests.sh"
    echo "5. Submit to DevPost!"
    echo ""
    echo "To test APIs manually:"
    echo ""
    echo "  export API_URL=\"$API_URL\""
    echo "  export JWT_TOKEN=\"\$TOKEN\""
    echo ""
    echo "  # List agents"
    echo "  curl -X GET \"\$API_URL/api/v1/config?type=agent\" \\"
    echo "    -H \"Authorization: Bearer \$JWT_TOKEN\""
    echo ""
else
    echo "1. Check CloudWatch Logs for errors:"
    echo "   aws logs tail /aws/lambda/$CONFIG_LAMBDA --follow --region $REGION"
    echo ""
    echo "2. Verify environment variables:"
    echo "   aws lambda get-function-configuration --function-name $CONFIG_LAMBDA --region $REGION"
    echo ""
    echo "3. Check DynamoDB tables exist:"
    echo "   aws dynamodb list-tables --region $REGION"
    echo ""
fi

echo ""
echo "=========================================="
echo "Deployment Complete"
echo "=========================================="
echo ""

# Exit with appropriate code
if [ -n "$JWT_TOKEN" ] && [ $WORKING_APIS -gt 0 ]; then
    exit 0
else
    exit 1
fi
