#!/bin/bash

# Get API URL
API_URL=$(grep ApiEndpoint cdk/outputs.json 2>/dev/null | cut -d'"' -f4)

if [ -z "$API_URL" ]; then
    echo "❌ No deployment found. Run ./DEPLOY_FAST.sh first"
    exit 1
fi

echo "Testing API: $API_URL"
echo ""

# Test 1: Ingestion
echo "Test 1: Ingestion"
curl -s -X POST "$API_URL/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{"mode":"ingestion","message":"Street light broken at 123 Main St","session_id":"test-123"}' | jq .

echo ""
echo ""

# Test 2: List reports
echo "Test 2: List reports"
curl -s "$API_URL/reports" | jq .

echo ""
echo "✅ Tests complete"
