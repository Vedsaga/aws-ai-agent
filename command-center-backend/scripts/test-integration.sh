#!/bin/bash

# Integration Test Script for Command Center Backend
# Tests all API endpoints to verify they work correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_ENDPOINT="${API_ENDPOINT:-}"
API_KEY="${API_KEY:-}"

# Check if configuration is provided
if [ -z "$API_ENDPOINT" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API_ENDPOINT and API_KEY must be set${NC}"
    echo "Usage: API_ENDPOINT=https://your-api.com API_KEY=your-key ./test-integration.sh"
    exit 1
fi

echo "========================================="
echo "Command Center Backend Integration Tests"
echo "========================================="
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo "API Key: ${API_KEY:0:10}..."
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test an endpoint
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo -n "Testing: $test_name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X GET \
            -H "x-api-key: $API_KEY" \
            "$API_ENDPOINT$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "x-api-key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_ENDPOINT$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: GET /data/updates - Basic
test_endpoint \
    "GET /data/updates (basic)" \
    "GET" \
    "/data/updates?since=2023-02-06T00:00:00Z" \
    ""

# Test 2: GET /data/updates - With domain filter
test_endpoint \
    "GET /data/updates (with domain)" \
    "GET" \
    "/data/updates?since=2023-02-06T00:00:00Z&domain=MEDICAL" \
    ""

# Test 3: POST /agent/query - Simple query
test_endpoint \
    "POST /agent/query (simple)" \
    "POST" \
    "/agent/query" \
    '{"text":"What are the most urgent needs right now?"}'

# Test 4: POST /agent/query - Medical query
test_endpoint \
    "POST /agent/query (medical)" \
    "POST" \
    "/agent/query" \
    '{"text":"Show me all critical medical incidents"}'

# Test 5: POST /agent/query - Location query
test_endpoint \
    "POST /agent/query (location)" \
    "POST" \
    "/agent/query" \
    '{"text":"What is happening in Nurdağı?"}'

# Test 6: POST /agent/action - Area briefing
test_endpoint \
    "POST /agent/action (area briefing)" \
    "POST" \
    "/agent/action" \
    '{"actionId":"GENERATE_AREA_BRIEFING","payload":{"area":"Nurdağı"}}'

# Test 7: POST /agent/action - Critical incidents
test_endpoint \
    "POST /agent/action (critical incidents)" \
    "POST" \
    "/agent/action" \
    '{"actionId":"SHOW_CRITICAL_INCIDENTS","payload":{"domain":"MEDICAL"}}'

echo ""
echo "========================================="
echo "Test Results"
echo "========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check the output above.${NC}"
    exit 1
fi
