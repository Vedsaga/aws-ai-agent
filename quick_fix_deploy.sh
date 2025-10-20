#!/bin/bash

# Quick Fix Deployment Script
# Deploys simplified Lambda handler to fix 500 errors

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "Quick Fix Deployment Script"
echo "=========================================="
echo ""

# Configuration
REGION="us-east-1"
LAMBDA_NAME="MultiAgentOrchestration-dev-Api-ConfigApiHandler"
LAMBDA_DIR="infrastructure/lambda/config-api"

echo -e "${BLUE}Step 1: Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: $ACCOUNT_ID${NC}"
echo ""

echo -e "${BLUE}Step 2: Checking Lambda function exists...${NC}"
if ! aws lambda get-function --function-name $LAMBDA_NAME --region $REGION &> /dev/null; then
    echo -e "${RED}ERROR: Lambda function $LAMBDA_NAME not found${NC}"
    echo "Available functions:"
    aws lambda list-functions --query 'Functions[?contains(FunctionName, `MultiAgent`)].FunctionName' --output table --region $REGION
    exit 1
fi

echo -e "${GREEN}✓ Lambda function exists${NC}"
echo ""

echo -e "${BLUE}Step 3: Creating deployment package...${NC}"

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "Temp directory: $TEMP_DIR"

# Copy simplified handler
cp $LAMBDA_DIR/config_handler_simple.py $TEMP_DIR/config_handler.py

# Create zip file
cd $TEMP_DIR
zip -q deployment.zip config_handler.py

PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
echo -e "${GREEN}✓ Package created: $PACKAGE_SIZE${NC}"
echo ""

echo -e "${BLUE}Step 4: Updating Lambda function code...${NC}"
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://deployment.zip \
    --region $REGION \
    --no-cli-pager > /dev/null

echo -e "${GREEN}✓ Lambda code updated${NC}"
echo ""

echo -e "${BLUE}Step 5: Waiting for update to complete...${NC}"
aws lambda wait function-updated \
    --function-name $LAMBDA_NAME \
    --region $REGION

echo -e "${GREEN}✓ Update complete${NC}"
echo ""

# Cleanup
cd - > /dev/null
rm -rf $TEMP_DIR

echo -e "${BLUE}Step 6: Testing Lambda function...${NC}"

# Get JWT token
echo "Getting JWT token..."
TOKEN_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id 6gobbpage9af3nd7ahm3lchkct \
    --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
    --region $REGION \
    2>&1)

if echo "$TOKEN_RESPONSE" | grep -q "IdToken"; then
    JWT_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"IdToken":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ JWT token obtained${NC}"
else
    echo -e "${YELLOW}⚠ Could not get JWT token (may need to create user)${NC}"
    JWT_TOKEN=""
fi

# Test API endpoint
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
echo ""
echo "Testing API endpoint: $API_URL/api/v1/config?type=agent"

if [ -n "$JWT_TOKEN" ]; then
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X GET "$API_URL/api/v1/config?type=agent" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json")

    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

    echo ""
    echo "Response Code: $HTTP_CODE"
    echo "Response Body:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

    if [ "$HTTP_CODE" = "200" ]; then
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ SUCCESS! API is working!"
        echo "==========================================${NC}"
    elif [ "$HTTP_CODE" = "500" ]; then
        echo ""
        echo -e "${RED}=========================================="
        echo "❌ Still getting 500 errors"
        echo "==========================================${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Check CloudWatch Logs:"
        echo "   aws logs tail /aws/lambda/$LAMBDA_NAME --follow --region $REGION"
        echo ""
        echo "2. Check Lambda environment variables:"
        echo "   aws lambda get-function-configuration --function-name $LAMBDA_NAME --region $REGION"
    else
        echo ""
        echo -e "${YELLOW}=========================================="
        echo "⚠ Unexpected response code: $HTTP_CODE"
        echo "==========================================${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping API test (no JWT token)${NC}"
    echo ""
    echo "To test manually:"
    echo "1. Get JWT token:"
    echo "   TOKEN=\$(aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id 6gobbpage9af3nd7ahm3lchkct --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! --region $REGION --query 'AuthenticationResult.IdToken' --output text)"
    echo ""
    echo "2. Test API:"
    echo "   curl -X GET \"$API_URL/api/v1/config?type=agent\" -H \"Authorization: Bearer \$TOKEN\""
fi

echo ""
echo "=========================================="
echo "Deployment Complete"
echo "=========================================="
echo ""
