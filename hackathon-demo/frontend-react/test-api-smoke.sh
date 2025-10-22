#!/bin/bash

# API Smoke Test Script
# Tests basic connectivity to the backend API

# Load API URL from environment
API_URL="${API_BASE_URL}"

if [ -z "$API_URL" ]; then
    echo "❌ ERROR: API_BASE_URL environment variable not set"
    echo "Please set it in your .env file or export it"
    exit 1
fi

echo "========================================="
echo "API Smoke Test"
echo "========================================="
echo ""
echo "API URL: $API_URL"
echo ""

# Test 1: Health check (if available)
echo "Test 1: API Connectivity"
echo "-------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/config?type=agent" 2>&1)
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "200" ]; then
    echo "✅ PASS - API is reachable (HTTP $response)"
else
    echo "❌ FAIL - API returned HTTP $response"
fi
echo ""

# Test 2: Check if config endpoint exists
echo "Test 2: Config Endpoint"
echo "-------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/config?type=agent" 2>&1)
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "200" ]; then
    echo "✅ PASS - Config endpoint exists (HTTP $response)"
    echo "   Note: 401/403 expected without authentication"
else
    echo "❌ FAIL - Config endpoint returned HTTP $response"
fi
echo ""

# Test 3: Check if ingest endpoint exists
echo "Test 3: Ingest Endpoint"
echo "-------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/ingest" 2>&1)
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "405" ]; then
    echo "✅ PASS - Ingest endpoint exists (HTTP $response)"
    echo "   Note: 401/403/405 expected without authentication or wrong method"
else
    echo "❌ FAIL - Ingest endpoint returned HTTP $response"
fi
echo ""

# Test 4: Check if query endpoint exists
echo "Test 4: Query Endpoint"
echo "-------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/query" 2>&1)
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "405" ]; then
    echo "✅ PASS - Query endpoint exists (HTTP $response)"
    echo "   Note: 401/403/405 expected without authentication or wrong method"
else
    echo "❌ FAIL - Query endpoint returned HTTP $response"
fi
echo ""

# Test 5: Check if data endpoint exists
echo "Test 5: Data Endpoint"
echo "-------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/data?type=retrieval" 2>&1)
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "200" ]; then
    echo "✅ PASS - Data endpoint exists (HTTP $response)"
    echo "   Note: 401/403 expected without authentication"
else
    echo "❌ FAIL - Data endpoint returned HTTP $response"
fi
echo ""

echo "========================================="
echo "Smoke Test Complete"
echo "========================================="
echo ""
echo "Note: All endpoints should return 401/403 without authentication."
echo "This is expected behavior and indicates the API is working correctly."
echo ""
echo "To test with authentication:"
echo "1. Log in to the frontend at http://localhost:3000"
echo "2. Use the browser's developer tools to inspect API calls"
echo "3. Run the manual test checklist in MANUAL_TEST_CHECKLIST.md"
