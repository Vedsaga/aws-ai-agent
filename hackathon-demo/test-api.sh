#!/bin/bash

# Get API endpoint from CloudFormation
API_URL=$(aws cloudformation describe-stacks \
  --stack-name DomainFlowDemo \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo "Testing DomainFlow API: $API_URL"
echo ""

# Test 1: Ingestion with vague location
echo "=== Test 1: Report with vague location ==="
curl -X POST "$API_URL/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "ingestion",
    "message": "Street light broken near the post office"
  }' | jq .

echo ""
echo ""

# Test 2: Clarification response
echo "=== Test 2: Provide clarification ==="
SESSION_ID=$(uuidgen)
curl -X POST "$API_URL/orchestrate" \
  -H "Content-Type: application/json" \
  -d "{
    \"mode\": \"ingestion\",
    \"message\": \"Yes, it's at 123 Main Street\",
    \"session_id\": \"$SESSION_ID\",
    \"conversation_history\": [
      {\"role\": \"user\", \"content\": \"Street light broken near the post office\"},
      {\"role\": \"assistant\", \"content\": \"Can you confirm the exact street address?\"}
    ]
  }" | jq .

echo ""
echo ""

# Test 3: Query reports
echo "=== Test 3: Query high-priority reports ==="
curl -X POST "$API_URL/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "query",
    "message": "Show me all high-priority issues"
  }' | jq .

echo ""
echo ""

# Test 4: List all reports
echo "=== Test 4: List all reports ==="
curl -X GET "$API_URL/reports" | jq .

echo ""
echo ""

# Test 5: Management - assign task
echo "=== Test 5: Assign task to Team B ==="
REPORT_ID=$(curl -s "$API_URL/reports" | jq -r '.reports[0].report_id')
curl -X POST "$API_URL/orchestrate" \
  -H "Content-Type: application/json" \
  -d "{
    \"mode\": \"management\",
    \"message\": \"Assign this to Team B and make it due in 48 hours\",
    \"report_id\": \"$REPORT_ID\"
  }" | jq .

echo ""
