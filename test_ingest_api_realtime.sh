#!/bin/bash

# Test Ingest API with Realtime Status Updates

API_URL="https://iqvvvvvvvv.execute-api.us-east-1.amazonaws.com/dev/ingest"
TOKEN="eyJraWQiOiJkZW1vLWtleSIsImFsZyI6IkhTMjU2In0.eyJzdWIiOiJkZW1vLXVzZXIiLCJ0ZW5hbnRJZCI6ImRlZmF1bHQtdGVuYW50IiwidXNlcklkIjoiZGVtby11c2VyIiwiaWF0IjoxNzI5NDUwMDAwLCJleHAiOjE3NjA5ODYwMDB9.demo-signature-for-testing"

echo "Testing Ingest API with Realtime Status Updates"
echo "================================================"
echo ""

# Test 1: Simple pothole report
echo "Test 1: Pothole Report"
echo "----------------------"

RESPONSE=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "There is a large pothole on Main Street near Central Park that has been causing traffic issues for the past week"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
echo "Job ID: $JOB_ID"
echo ""

# Wait a bit for processing
echo "Waiting 10 seconds for processing..."
sleep 10

# Check CloudWatch logs for status updates
echo ""
echo "Checking orchestrator logs for status updates..."
echo "------------------------------------------------"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
  --since 2m \
  --region us-east-1 \
  --filter-pattern "$JOB_ID" | head -50

echo ""
echo "Done!"
