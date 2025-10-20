#!/bin/bash

echo "TESTING CURRENT DEPLOYED STATE"
echo "==============================="
echo ""

TIMESTAMP=$(date +%s)
JOB_ID="verify_${TIMESTAMP}"

cat > /tmp/test_current.json << EOF
{
    "job_id": "${JOB_ID}",
    "job_type": "ingest",
    "domain_id": "civic_complaints",
    "text": "Pothole on Main Street needs fixing",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}
EOF

echo "Invoking orchestrator..."
aws lambda invoke \
    --function-name MultiAgentOrchestration-dev-Orchestrator \
    --cli-binary-format raw-in-base64-out \
    --payload file:///tmp/test_current.json \
    --region us-east-1 \
    /tmp/response_current.json > /dev/null 2>&1

echo "Response:"
cat /tmp/response_current.json
echo ""
echo ""

sleep 5

echo "CHECKING FOR STATUS PUBLISHING IN LOGS:"
echo "========================================"
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 2>/dev/null | grep "${JOB_ID}"

echo ""
echo ""
echo "CHECKING FOR 'publish' CALLS:"
echo "=============================="
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 2>/dev/null | grep -i "publish"

echo ""
echo "CHECKING FOR 'status' CALLS:"
echo "============================="
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Orchestrator \
    --since 1m \
    --region us-east-1 2>/dev/null | grep -i "status.*publish"
