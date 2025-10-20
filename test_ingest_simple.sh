#!/bin/bash

API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
REGION="us-east-1"

echo "Testing Ingest with Status Updates..."
echo ""

# Submit a report
RESPONSE=$(curl -s -X POST "$API_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: default-tenant" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "Large pothole at Main Street and 5th Avenue causing traffic issues",
    "source": "test"
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')

if [ ! -z "$JOB_ID" ] && [ "$JOB_ID" != "null" ]; then
    echo ""
    echo "Job ID: $JOB_ID"
    echo ""
    echo "Waiting 5 seconds for processing..."
    sleep 5
    
    echo ""
    echo "Checking Orchestrator logs for status updates..."
    aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator --since 2m --region $REGION | grep -i "status\|publish" | tail -10 || echo "No status logs found yet"
    
    echo ""
    echo "Checking Status Publisher logs..."
    aws logs tail /aws/lambda/MultiAgentOrchestration-dev-StatusPublisher --since 2m --region $REGION | tail -10 || echo "No publisher logs found yet"
fi
