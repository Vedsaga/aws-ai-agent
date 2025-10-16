#!/bin/bash

# API Testing Script
# Tests all API endpoints with request/response validation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Load environment variables
if [ ! -f ".env.local" ]; then
    echo -e "${RED}Error: .env.local file not found${NC}"
    echo "Run deployment first: bash scripts/full-deploy.sh"
    exit 1
fi

source .env.local

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
echo -e "Testing with API Key: ${YELLOW}${API_KEY:0:10}...${NC}"
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
    echo -e "  Method: ${method}"
    echo -e "  Endpoint: ${endpoint}"
    
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
    
    echo -e "  Status: ${HTTP_CODE}"
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Validate JSON response
        if echo "$BODY" | jq empty 2>/dev/null; then
            echo -e "  ${GREEN}✓ Valid JSON response${NC}"
        else
            echo -e "  ${YELLOW}⚠ Response is not valid JSON${NC}"
        fi
        
        # Show sample response
        if [ ${#BODY} -gt 200 ]; then
            echo -e "  Response: ${BODY:0:200}..."
        else
            echo -e "  Response: ${BODY}"
        fi
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        echo -e "  Expected: ${expected_status}, Got: ${HTTP_CODE}"
        echo -e "  Response: ${BODY}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    echo ""
}

# Start tests
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${CYAN}                    Running Tests                          ${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
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
    "GET /data/updates - With domain filter" \
    "GET" \
    "data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
    "" \
    "200"

# Test 3: GET /data/updates - Missing required parameter
test_endpoint \
    "GET /data/updates - Missing 'since' parameter" \
    "GET" \
    "data/updates" \
    "" \
    "400"

# Test 4: GET /data/updates - Invalid date format
test_endpoint \
    "GET /data/updates - Invalid date format" \
    "GET" \
    "data/updates?since=invalid-date" \
    "" \
    "400"

# Test 5: POST /agent/query - Valid request
test_endpoint \
    "POST /agent/query - Valid request" \
    "POST" \
    "agent/query" \
    '{"text": "What are the most urgent needs?"}' \
    "200"

# Test 6: POST /agent/query - Empty text
test_endpoint \
    "POST /agent/query - Empty text" \
    "POST" \
    "agent/query" \
    '{"text": ""}' \
    "400"

# Test 7: POST /agent/query - Missing text field
test_endpoint \
    "POST /agent/query - Missing text field" \
    "POST" \
    "agent/query" \
    '{}' \
    "400"

# Test 8: POST /agent/action - Valid action
test_endpoint \
    "POST /agent/action - Valid action" \
    "POST" \
    "agent/action" \
    '{"actionId": "SHOW_CRITICAL_INCIDENTS"}' \
    "200"

# Test 9: POST /agent/action - Invalid action
test_endpoint \
    "POST /agent/action - Invalid action ID" \
    "POST" \
    "agent/action" \
    '{"actionId": "INVALID_ACTION"}' \
    "400"

# Test 10: POST /agent/action - Missing actionId
test_endpoint \
    "POST /agent/action - Missing actionId" \
    "POST" \
    "agent/action" \
    '{}' \
    "400"

# Test 11: GET /data/updates - No API key (should fail)
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))] GET /data/updates - No API key${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
echo -e "  Status: ${HTTP_CODE}"
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "  ${GREEN}✓ PASSED (correctly rejected)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}✗ FAILED (should return 403)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Test 12: GET /data/updates - Invalid API key
echo -e "${BLUE}[Test $((TOTAL_TESTS + 1))] GET /data/updates - Invalid API key${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
    -H "x-api-key: invalid-key-12345" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
echo -e "  Status: ${HTTP_CODE}"
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "  ${GREEN}✓ PASSED (correctly rejected)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "  ${RED}✗ FAILED (should return 403)${NC}"
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
    exit 0
else
    echo -e "${RED}${BOLD}✗ Some tests failed${NC}"
    echo ""
    echo "Check Lambda logs for details:"
    echo "  aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow"
    echo "  aws logs tail /aws/lambda/CommandCenterBackend-Dev-QueryHandler --follow"
    echo "  aws logs tail /aws/lambda/CommandCenterBackend-Dev-ActionHandler --follow"
    echo ""
    exit 1
fi
