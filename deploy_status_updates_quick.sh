#!/bin/bash
set -e

REGION="us-east-1"
ORCHESTRATOR="MultiAgentOrchestration-dev-Orchestrator"
INGEST="MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY="MultiAgentOrchestration-dev-Api-QueryHandler"
STATUS_PUBLISHER="MultiAgentOrchestration-dev-StatusPublisher"

echo "Deploying Status Updates Integration..."

# 1. Update orchestrator
echo "[1/3] Updating Orchestrator..."
cd /tmp && rm -rf orch_deploy && mkdir orch_deploy && cd orch_deploy
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/orchestrator_handler.py handler.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py .
zip -q deployment.zip handler.py status_utils.py

aws lambda update-function-code --function-name $ORCHESTRATOR --zip-file fileb://deployment.zip --region $REGION --no-cli-pager > /dev/null
aws lambda wait function-updated --function-name $ORCHESTRATOR --region $REGION
echo "✓ Orchestrator updated"

# 2. Update ingest handler
echo "[2/3] Updating Ingest Handler..."
cd /tmp && rm -rf ingest_deploy && mkdir ingest_deploy && cd ingest_deploy
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/ingest_handler_with_orchestrator.py handler.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py .
zip -q deployment.zip handler.py status_utils.py

aws lambda update-function-code --function-name $INGEST --zip-file fileb://deployment.zip --region $REGION --no-cli-pager > /dev/null
aws lambda wait function-updated --function-name $INGEST --region $REGION
echo "✓ Ingest handler updated"

# 3. Update query handler
echo "[3/3] Updating Query Handler..."
cd /tmp && rm -rf query_deploy && mkdir query_deploy && cd query_deploy
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/query_index.py handler.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py .
zip -q deployment.zip handler.py status_utils.py

aws lambda update-function-code --function-name $QUERY --zip-file fileb://deployment.zip --region $REGION --no-cli-pager > /dev/null
aws lambda wait function-updated --function-name $QUERY --region $REGION
echo "✓ Query handler updated"

# 4. Update env variables with status publisher ARN
if aws lambda get-function --function-name $STATUS_PUBLISHER --region $REGION > /dev/null 2>&1; then
    ARN=$(aws lambda get-function --function-name $STATUS_PUBLISHER --region $REGION --query 'Configuration.FunctionArn' --output text)
    echo "Status Publisher ARN: $ARN"
    
    # Update orchestrator env
    aws lambda update-function-configuration --function-name $ORCHESTRATOR \
        --environment "Variables={CONFIGURATIONS_TABLE=MultiAgentOrchestration-dev-Data-Configurations,INCIDENTS_TABLE=MultiAgentOrchestration-dev-Data-Incidents,BEDROCK_REGION=us-east-1,STATUS_PUBLISHER_FUNCTION=$ARN}" \
        --region $REGION --no-cli-pager > /dev/null 2>&1 || echo "Note: Orchestrator env update skipped"
fi

echo ""
echo "✅ All deployments complete!"
echo ""
echo "Test with:"
echo "  python3 test_appsync_realtime.py"
