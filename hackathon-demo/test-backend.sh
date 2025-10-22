#!/bin/bash

echo "🧪 Testing Backend API"
echo "====================="
echo ""

# Load API URL from .env
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Run deploy-backend.sh first."
    exit 1
fi

if [ -z "$API_URL" ]; then
    echo "❌ API_URL not set in .env"
    exit 1
fi

echo "API URL: $API_URL"
echo ""

# Test 1: Report ingestion
echo "Test 1: Report Ingestion"
echo "------------------------"
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "ingestion",
    "message": "Broken streetlight at 123 Main Street, very dark and dangerous",
    "session_id": "test-session-1"
  }')

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2: List reports
echo "Test 2: List Reports"
echo "-------------------"
RESPONSE=$(curl -s "${API_URL}reports")
echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 3: Query
echo "Test 3: Query Reports"
echo "--------------------"
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "query",
    "message": "Show me all high severity issues",
    "session_id": "test-session-2"
  }')

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

echo "✅ Tests complete!"
