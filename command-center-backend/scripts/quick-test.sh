#!/bin/bash

# Quick API Test Script
# Simple tests for all endpoints

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Quick API Test                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Load credentials
if [ ! -f ".env.local" ]; then
    echo -e "${RED}Error: .env.local not found${NC}"
    exit 1
fi

source .env.local

if [ -z "$API_ENDPOINT" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API_ENDPOINT or API_KEY not set${NC}"
    exit 1
fi

echo -e "API Endpoint: ${BLUE}${API_ENDPOINT}${NC}"
echo -e "API Key: ${BLUE}${API_KEY:0:10}...${NC}"
echo ""

# Test 1: Updates endpoint
echo -e "${YELLOW}[1/3] Testing GET /data/updates${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" \
    -H "x-api-key: ${API_KEY}")
STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    EVENT_COUNT=$(echo "$BODY" | jq -r '.events | length' 2>/dev/null || echo "0")
    echo -e "  Events returned: ${EVENT_COUNT}"
else
    echo -e "${RED}✗ Status: ${STATUS}${NC}"
    echo "  Response: ${BODY}"
fi
echo ""

# Test 2: Query endpoint
echo -e "${YELLOW}[2/3] Testing POST /agent/query${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}agent/query" \
    -H "x-api-key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"text": "Show critical incidents"}')
STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    echo "  Response preview: ${BODY:0:100}..."
else
    echo -e "${RED}✗ Status: ${STATUS}${NC}"
    echo "  Response: ${BODY}"
fi
echo ""

# Test 3: Action endpoint
echo -e "${YELLOW}[3/3] Testing POST /agent/action${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}agent/action" \
    -H "x-api-key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"actionId": "SHOW_CRITICAL_INCIDENTS"}')
STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Status: 200 OK${NC}"
    echo "  Response preview: ${BODY:0:100}..."
else
    echo -e "${RED}✗ Status: ${STATUS}${NC}"
    echo "  Response: ${BODY}"
fi
echo ""

echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Quick test complete!${NC}"
echo ""
echo "For detailed testing, run: bash scripts/test-api.sh"
echo "For logs, run: aws logs tail /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler --follow"
