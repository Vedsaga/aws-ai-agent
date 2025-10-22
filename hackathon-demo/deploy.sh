#!/bin/bash
set -e

echo "🚀 Deploying DomainFlow Hackathon Demo..."

# Install CDK dependencies
cd cdk
pip install -r requirements.txt

# Bootstrap CDK (if needed)
cdk bootstrap

# Deploy stack
cdk deploy --require-approval never

# Get API endpoint
API_URL=$(aws cloudformation describe-stacks \
  --stack-name DomainFlowDemo \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "API Endpoint: $API_URL"
echo ""
echo "Test ingestion:"
echo "curl -X POST $API_URL/orchestrate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"mode\": \"ingestion\", \"message\": \"Street light broken near post office\"}'"
echo ""
