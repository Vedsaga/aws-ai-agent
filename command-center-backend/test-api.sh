#!/bin/bash

# Command Center Backend - API Test Script
# Tests all API endpoints with comprehensive validation
# Usage: ./test-api.sh

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Load environment variables
if [ ! -f "$SCRIPT_DIR/.env.local" ]; then
    echo -e "${RED}Error: .env.local file not found${NC}"
    echo "Run deployment first: ./deploy.sh"
    exit 1
fi

source "$SCRIPT_DIR/.env.local"

# Check required variables
if [ -z "$API_ENDPOINT" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API_ENDPOINT or API_KEY not set in .env.local${NC}"
    exit 1
fi

echo -e "${BOLD}${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Command Center API Test Suite                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "API Endpoint: ${YELLOW}${API_ENDPOINT}${NC}"
echo -e "API Key: ${YELLOW}${API_KEY:0:10}...${NC}"
echo ""

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "${BLUE}[Test $TOTAL_TESTS] ${test_name}${NC}"
    
    if [ "$method" = "GET" ]; then
        RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}${endpoint}" \
            -H "x-api-key: ${API_KEY}" 2>&1)
    else
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}${endpoint}" \
            -H "x-api-key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "${data}" 2>&1)
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (Status: ${HTTP_CODE})"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Validate JSON response
        if echo "$BODY" | jq empty 2>/dev/null; then
            # Show full response (pretty-printed if possible)
            echo -e "  Response:"
            echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
        fi
    else
        echo -e "  ${RED}✗ FAILED${NC} (Expected: ${expected_status}, Got: ${HTTP_CODE})"
        echo -e "  Response:"
        echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    echo ""
}

# Start tests
echo -e "${BOLD}${CYAN}Running Tests...${NC}"
echo ""

# Test 1: GET /data/updates - Valid request
test_endpoint \
    "GET /data/updates - Valid request" \
    "GET" \
    "data/updates?since=2023-02-06T00:00:00Z" \
    "" \
    "200"

# Test 2: GET /data/updates - With domain filter
test_endpoint \
    "GET /data/updates - With MEDICAL domain filter" \
    "GET" \
    "data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
    "" \
    "200"

# Test 3: GET /data/updates - Missing required parameter
test_endpoint \
    "GET /data/updates - Missing 'since' parameter (should fail)" \
    "GET" \
    "data/updates" \
    "" \
    "400"

# Test 4: POST /agent/query - Valid request
test_endpoint \
    "POST /agent/query - Valid natural language query" \
    "POST" \
    "agent/query" \
    '{"text": "Show me critical medical incidents"}' \
    "200"

# Test 5: POST /agent/query - Empty text
test_endpoint \
    "POST /agent/query - Empty text (should fail)" \
    "POST" \
    "agent/query" \
    '{"text": ""}' \
    "400"

# Test 6: POST /agent/action - Valid action
test_endpoint \
    "POST /agent/action - SHOW_CRITICAL_MEDICAL action" \
    "POST" \
    "agent/action" \
    '{"actionId": "SHOW_CRITICAL_MEDICAL"}' \
    "200"

# Test 7: POST /agent/action - Invalid action
test_endpoint \
    "POST /agent/action - Invalid action ID (should fail)" \
    "POST" \
    "agent/action" \
    '{"actionId": "INVALID_ACTION"}' \
    "400"

# Test 8: POST /agent/action - HELP action
test_endpoint \
    "POST /agent/action - HELP action" \
    "POST" \
    "agent/action" \
    '{"actionId": "HELP"}' \
    "200"

# Test 9: Authentication - No API key
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))] Authentication - No API key (should fail)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "  ${GREEN}✓ PASSED${NC} (Status: ${HTTP_CODE})"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}✗ FAILED${NC} (Expected: 403, Got: ${HTTP_CODE})"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Test 10: Authentication - Invalid API key
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))] Authentication - Invalid API key (should fail)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
    -H "x-api-key: invalid-key-12345" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "  ${GREEN}✓ PASSED${NC} (Status: ${HTTP_CODE})"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}✗ FAILED${NC} (Expected: 403, Got: ${HTTP_CODE})"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Summary
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}                    Test Summary                           ${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Total Tests: ${BOLD}${TOTAL_TESTS}${NC}"
echo -e "Passed: ${GREEN}${BOLD}${PASSED_TESTS}${NC}"
echo -e "Failed: ${RED}${BOLD}${FAILED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ All tests passed!${NC}"
    echo ""
    echo -e "${CYAN}Your API is working correctly! 🎉${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}${BOLD}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Lambda logs:"
    echo "     aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow"
    echo ""
    echo "  2. Verify Bedrock model access:"
    echo "     AWS Console → Bedrock → Model access"
    echo ""
    echo "  3. Check CloudFormation stack status:"
    echo "     aws cloudformation describe-stacks --stack-name CommandCenterBackend-Dev"
    echo ""
    exit 1
fi
