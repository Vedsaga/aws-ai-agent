#!/bin/bash
set -e
REGION="us-east-1"
ORCH="MultiAgentOrchestration-dev-Orchestrator"

echo "Redeploying orchestrator with proper status_utils..."

cd /tmp && rm -rf orch_new && mkdir orch_new && cd orch_new

# Copy files
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/orchestrator_handler.py handler.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py .

# Fix the import in handler.py to import directly
sed -i 's/from realtime.status_utils import/from status_utils import/g' handler.py

# Package
zip -q deployment.zip handler.py status_utils.py

# Deploy
aws lambda update-function-code --function-name $ORCH --zip-file fileb://deployment.zip --region $REGION --no-cli-pager > /dev/null
aws lambda wait function-updated --function-name $ORCH --region $REGION

echo "✅ Done! Testing..."

# Test immediately
curl -s -X POST "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"domain_id":"civic_complaints","text":"TEST 3: Status updates test - pothole on Elm Street","source":"test"}' | jq '.job_id'

echo ""
echo "Waiting 8 seconds..."
sleep 8

echo ""
echo "Checking for status publishing logs..."
aws logs tail /aws/lambda/$ORCH --since 1m --region $REGION | grep -E "Publishing status|STATUS_PUBLISHER_FUNCTION"
