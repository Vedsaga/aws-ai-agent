#!/bin/bash
set -e

echo "🚀 Deploying Hackathon Demo Backend"
echo "===================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required"
    exit 1
fi

if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is required. Install with: npm install -g aws-cdk"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo "✓ Prerequisites OK"
echo "  Account: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo ""

# Navigate to CDK directory
cd "$(dirname "$0")/cdk"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

# Bootstrap CDK (if needed)
echo "Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://${AWS_ACCOUNT}/${AWS_REGION}
    echo "✓ CDK bootstrapped"
else
    echo "✓ CDK already bootstrapped"
fi
echo ""

# Deploy stack
echo "Deploying stack..."
echo "This will take 2-3 minutes..."
echo ""
cdk deploy --require-approval never --outputs-file outputs.json

echo ""
echo "===================================="
echo "✅ Backend Deployed Successfully!"
echo "===================================="
echo ""

# Extract API URL
if [ -f outputs.json ]; then
    API_URL=$(python3 -c "import json; data=json.load(open('outputs.json')); print(list(data.values())[0]['ApiEndpoint'])" 2>/dev/null || echo "")
    
    if [ -n "$API_URL" ]; then
        echo "API Endpoint: $API_URL"
        echo ""
        
        # Update frontend .env.local
        FRONTEND_ENV="../frontend-react/.env.local"
        if [ -f "$FRONTEND_ENV" ]; then
            sed -i.bak "s|YOUR_API_URL_HERE|${API_URL}|g" "$FRONTEND_ENV"
            rm -f "${FRONTEND_ENV}.bak"
            echo "✓ Frontend .env.local updated"
        fi
        
        # Save to parent .env
        echo "API_URL=$API_URL" > ../.env
        echo "AWS_REGION=$AWS_REGION" >> ../.env
        echo "✓ Configuration saved to .env"
    fi
fi

echo ""
echo "Next steps:"
echo "1. Test the API:"
echo "   curl -X POST ${API_URL}orchestrate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"mode\":\"ingestion\",\"message\":\"Broken streetlight at 123 Main St\"}'"
echo ""
echo "2. Start the frontend:"
echo "   cd frontend-react"
echo "   npm install"
echo "   npm run dev"
echo ""
