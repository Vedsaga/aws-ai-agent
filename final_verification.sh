#!/bin/bash

# Final Verification Script for Hackathon Demo
# Run this before the demo to ensure everything is ready

echo "=========================================="
echo "  FINAL HACKATHON VERIFICATION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Function to check status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC} - $1"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - $1"
        ((FAILED++))
    fi
}

echo "1. Checking AWS Credentials..."
aws sts get-caller-identity > /dev/null 2>&1
check_status "AWS credentials configured"

echo ""
echo "2. Checking API Gateway..."
aws apigateway get-rest-api --rest-api-id vluqfpl2zi --region us-east-1 > /dev/null 2>&1
check_status "API Gateway accessible"

echo ""
echo "3. Checking Lambda Functions..."
aws lambda get-function --function-name MultiAgentOrchestration-dev-Api-ConfigHandler --region us-east-1 > /dev/null 2>&1
check_status "Config Lambda exists"

aws lambda get-function --function-name MultiAgentOrchestration-dev-Api-IngestHandler --region us-east-1 > /dev/null 2>&1
check_status "Ingest Lambda exists"

aws lambda get-function --function-name MultiAgentOrchestration-dev-Api-QueryHandler --region us-east-1 > /dev/null 2>&1
check_status "Query Lambda exists"

echo ""
echo "4. Checking DynamoDB Tables..."
aws dynamodb describe-table --table-name MultiAgentOrchestration-dev-Data-Configurations --region us-east-1 > /dev/null 2>&1
check_status "Configurations table exists"

aws dynamodb describe-table --table-name MultiAgentOrchestration-dev-Data-Incidents --region us-east-1 > /dev/null 2>&1
check_status "Incidents table exists"

echo ""
echo "5. Checking RDS Database..."
aws rds describe-db-instances --region us-east-1 --query 'DBInstances[?contains(DBInstanceIdentifier, `multiagent`)].DBInstanceStatus' --output text | grep -q "available"
check_status "RDS database available"

echo ""
echo "6. Checking Cognito User Pool..."
aws cognito-idp describe-user-pool --user-pool-id us-east-1_7QZ7Y6Gbl --region us-east-1 > /dev/null 2>&1
check_status "Cognito user pool exists"

echo ""
echo "7. Checking Frontend Files..."
if [ -f "infrastructure/frontend/.env.local" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Frontend .env.local exists"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Frontend .env.local missing"
    ((FAILED++))
fi

if [ -f "infrastructure/frontend/lib/api-client.ts" ]; then
    echo -e "${GREEN}✓ PASS${NC} - API client exists"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - API client missing"
    ((FAILED++))
fi

if [ -d "infrastructure/frontend/node_modules" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Node modules installed"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARN${NC} - Node modules not installed (run: cd infrastructure/frontend && npm install)"
fi

echo ""
echo "8. Testing API Endpoint..."
API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/config?type=agent")

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - API endpoint responding (HTTP $HTTP_CODE)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - API endpoint not responding correctly (HTTP $HTTP_CODE)"
    ((FAILED++))
fi

echo ""
echo "=========================================="
echo "  VERIFICATION SUMMARY"
echo "=========================================="
echo ""
echo "Total Checks: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}${GREEN}✓✓✓ ALL SYSTEMS GO! READY FOR DEMO! ✓✓✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. cd infrastructure/frontend"
    echo "2. npm run dev"
    echo "3. Open http://localhost:3000"
    echo "4. Login with testuser / TestPassword123!"
    echo "5. WIN THE HACKATHON! 🏆"
    exit 0
else
    echo -e "${RED}✗✗✗ SOME CHECKS FAILED ✗✗✗${NC}"
    echo ""
    echo "Please fix the failed checks before demo."
    echo "See documentation for troubleshooting."
    exit 1
fi
