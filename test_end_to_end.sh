#!/bin/bash

echo "=========================================="
echo "END-TO-END ORCHESTRATOR TEST"
echo "=========================================="
echo ""

# Test 1: Simple Ingest
echo "TEST 1: SIMPLE INGEST - Pothole Report"
echo "=========================================="

cat > /tmp/test1_payload.json << 'EOF'
{
    "job_id": "test_simple_001",
    "job_type": "ingest",
    "domain_id": "civic_complaints",
    "text": "There is a pothole on Main Street",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}
EOF

echo "Payload:"
cat /tmp/test1_payload.json | jq .
echo ""

echo "Invoking orchestrator..."
aws lambda invoke \
    --function-name MultiAgentOrchestration-dev-Orchestrator \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test1_payload.json \
    --region us-east-1 \
    /tmp/test1_response.json > /dev/null 2>&1

echo "Response:"
cat /tmp/test1_response.json | jq .
echo ""

echo "Waiting 3 seconds for processing..."
sleep 3

echo "CloudWatch Logs (last 30 lines):"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 \
    --filter-pattern "test_simple_001" 2>/dev/null | tail -30

echo ""
echo "=========================================="
echo ""

# Test 2: Complex Ingest
echo "TEST 2: COMPLEX INGEST - Detailed Report"
echo "=========================================="

cat > /tmp/test2_payload.json << 'EOF'
{
    "job_id": "test_complex_002",
    "job_type": "ingest",
    "domain_id": "civic_complaints",
    "text": "There is a large pothole on Main Street near Central Park that has been causing severe traffic issues for the past 2 weeks. Multiple cars have been damaged. The pothole is approximately 3 feet wide and 6 inches deep. It's located right in front of building number 123.",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}
EOF

echo "Payload:"
cat /tmp/test2_payload.json | jq .
echo ""

echo "Invoking orchestrator..."
aws lambda invoke \
    --function-name MultiAgentOrchestration-dev-Orchestrator \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test2_payload.json \
    --region us-east-1 \
    /tmp/test2_response.json > /dev/null 2>&1

echo "Response:"
cat /tmp/test2_response.json | jq .
echo ""

echo "Waiting 8 seconds for processing..."
sleep 8

echo "CloudWatch Logs (showing agent execution):"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 \
    --filter-pattern "test_complex_002" 2>/dev/null | grep -E "(Processing|Agent|executed|confidence|Orchestrator invoked)" | tail -20

echo ""
echo "=========================================="
echo ""

# Test 3: Query
echo "TEST 3: DATA QUERY - Search Reports"
echo "=========================================="

cat > /tmp/test3_payload.json << 'EOF'
{
    "job_id": "test_query_003",
    "job_type": "query",
    "domain_id": "civic_complaints",
    "question": "Show me all pothole reports on Main Street",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}
EOF

echo "Payload:"
cat /tmp/test3_payload.json | jq .
echo ""

echo "Invoking orchestrator..."
aws lambda invoke \
    --function-name MultiAgentOrchestration-dev-Orchestrator \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test3_payload.json \
    --region us-east-1 \
    /tmp/test3_response.json > /dev/null 2>&1

echo "Response:"
cat /tmp/test3_response.json | jq .
echo ""

echo "Waiting 5 seconds for processing..."
sleep 5

echo "CloudWatch Logs (showing query execution):"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 \
    --filter-pattern "test_query_003" 2>/dev/null | grep -E "(Processing|Agent|executed|query)" | tail -20

echo ""
echo "=========================================="
echo "DETAILED LOG ANALYSIS"
echo "=========================================="
echo ""

echo "Full execution log for Test 2 (Complex):"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 2m \
    --region us-east-1 \
    --filter-pattern "test_complex_002" 2>/dev/null

echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "=========================================="
