#!/bin/bash
set -e

echo "🚀 Quick Deploy - DomainFlow Hackathon Demo"
echo "============================================"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

echo "✓ AWS CLI configured"

# Install CDK if not present
if ! command -v cdk &> /dev/null; then
    echo "Installing AWS CDK..."
    npm install -g aws-cdk
fi

echo "✓ CDK available"

# Navigate to CDK directory
cd cdk

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt -q

# Bootstrap (if needed)
echo "Bootstrapping CDK..."
cdk bootstrap --require-approval never 2>/dev/null || true

# Deploy
echo ""
echo "Deploying stack..."
cdk deploy --require-approval never --outputs-file outputs.json

# Extract API URL
API_URL=$(cat outputs.json | grep -o '"ApiEndpoint": "[^"]*' | cut -d'"' -f4)

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "API Endpoint: $API_URL"
echo ""
echo "Next steps:"
echo "1. Edit frontend/index.html"
echo "2. Replace YOUR_API_ENDPOINT_HERE with: $API_URL"
echo "3. Replace YOUR_MAPBOX_TOKEN with your token"
echo "4. Open frontend/index.html in browser"
echo ""
echo "Test API:"
echo "curl -X POST $API_URL/orchestrate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"mode\": \"ingestion\", \"message\": \"Street light broken\"}'"
echo ""
