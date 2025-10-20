#!/bin/bash

# AppSync Real-time Status Broadcasting - Quick Start Guide
# This script helps you deploy and test AppSync real-time status updates

set -e

echo "=========================================="
echo "AppSync Real-time Status - Quick Start"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from project root
if [ ! -f "APPSYNC_IMPLEMENTATION.py" ]; then
    echo_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check prerequisites
echo_step "1. Checking prerequisites..."
echo ""

MISSING_DEPS=0

if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 not found. Please install Python 3.8+"
    MISSING_DEPS=1
fi

if ! command -v node &> /dev/null; then
    echo_error "Node.js not found. Please install Node.js 16+"
    MISSING_DEPS=1
fi

if ! command -v npm &> /dev/null; then
    echo_error "npm not found. Please install npm"
    MISSING_DEPS=1
fi

if ! command -v aws &> /dev/null; then
    echo_error "AWS CLI not found. Please install AWS CLI"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo_error "Missing prerequisites. Please install the required tools."
    exit 1
fi

echo_info "✅ All prerequisites found"
echo ""

# Step 2: Install Python dependencies
echo_step "2. Installing Python dependencies..."
echo ""

if [ ! -d "venv" ]; then
    echo_info "Creating virtual environment..."
    python3 -m venv venv
fi

echo_info "Activating virtual environment..."
source venv/bin/activate

echo_info "Installing dependencies..."
pip install -q websockets requests boto3

echo_info "✅ Python dependencies installed"
echo ""

# Step 3: Check AWS credentials
echo_step "3. Checking AWS credentials..."
echo ""

if ! aws sts get-caller-identity &> /dev/null; then
    echo_error "AWS credentials not configured"
    echo ""
    echo "Configure AWS credentials using one of these methods:"
    echo "  1. aws configure"
    echo "  2. export AWS_PROFILE=your-profile"
    echo "  3. export AWS_ACCESS_KEY_ID=xxx AWS_SECRET_ACCESS_KEY=xxx"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}

echo_info "✅ AWS credentials configured"
echo_info "Account: $ACCOUNT_ID"
echo_info "Region: $REGION"
echo ""

# Step 4: Check if infrastructure exists
echo_step "4. Checking existing infrastructure..."
echo ""

# Check for UserSessions table
USER_SESSIONS_TABLE="MultiAgentOrchestration-dev-UserSessions"
if aws dynamodb describe-table --table-name "$USER_SESSIONS_TABLE" --region "$REGION" &> /dev/null; then
    echo_info "✅ UserSessions table exists"
else
    echo_warn "UserSessions table not found - will be created during deployment"
fi

# Check for orchestrator Lambda
ORCHESTRATOR_FUNCTION="MultiAgentOrchestration-dev-Orchestrator"
if aws lambda get-function --function-name "$ORCHESTRATOR_FUNCTION" --region "$REGION" &> /dev/null; then
    echo_info "✅ Orchestrator Lambda exists"
else
    echo_warn "Orchestrator Lambda not found - AppSync will work but won't receive updates"
fi

echo ""

# Step 5: Deploy AppSync stack
echo_step "5. Deploy AppSync Real-time Stack"
echo ""
echo "This will deploy:"
echo "  - AppSync GraphQL API"
echo "  - Status Publisher Lambda"
echo "  - UserSessions DynamoDB table (if needed)"
echo ""

read -p "Deploy AppSync stack? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Deploying AppSync stack..."

    if [ -f "deploy_realtime_stack.sh" ]; then
        bash deploy_realtime_stack.sh
    else
        echo_error "deploy_realtime_stack.sh not found"
        exit 1
    fi

    echo_info "✅ AppSync stack deployed"
else
    echo_warn "Skipping deployment. Using existing stack."
fi

echo ""

# Step 6: Get AppSync configuration
echo_step "6. Getting AppSync configuration..."
echo ""

# Try to load from environment file
if [ -f ".env.appsync" ]; then
    source .env.appsync
    echo_info "Loaded configuration from .env.appsync"
else
    # Try to get from AWS
    echo_info "Querying AWS for AppSync configuration..."

    STACK_NAME="MultiAgentOrchestration-dev-Realtime"

    # Get AppSync API details
    APPSYNC_API_ID=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`AppSyncApiId`].OutputValue' \
        --output text 2>/dev/null || echo "")

    if [ -z "$APPSYNC_API_ID" ]; then
        echo_error "Could not find AppSync API. Please deploy the stack first."
        exit 1
    fi

    APPSYNC_API_URL="https://${APPSYNC_API_ID}.appsync-api.${REGION}.amazonaws.com/graphql"

    # Get API Key
    APPSYNC_API_KEY=$(aws appsync list-api-keys \
        --api-id "$APPSYNC_API_ID" \
        --region "$REGION" \
        --query 'apiKeys[0].id' \
        --output text 2>/dev/null || echo "")

    # Save to .env file
    cat > .env.appsync << EOF
# AppSync Configuration
APPSYNC_API_URL=$APPSYNC_API_URL
APPSYNC_API_KEY=$APPSYNC_API_KEY
APPSYNC_API_ID=$APPSYNC_API_ID
EOF

    echo_info "Configuration saved to .env.appsync"
fi

if [ -z "$APPSYNC_API_URL" ] || [ -z "$APPSYNC_API_KEY" ]; then
    echo_error "Could not get AppSync configuration"
    exit 1
fi

echo ""
echo_info "AppSync Configuration:"
echo "  API URL: $APPSYNC_API_URL"
echo "  API Key: ${APPSYNC_API_KEY:0:10}..."
echo ""

# Step 7: Get API Gateway URL
echo_step "7. Getting API Gateway URL..."
echo ""

API_STACK_NAME="MultiAgentOrchestration-dev-API"
API_BASE_URL=$(aws cloudformation describe-stacks \
    --stack-name "$API_STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$API_BASE_URL" ]; then
    echo_warn "Could not find API Gateway URL automatically"
    echo ""
    read -p "Enter API Gateway URL (e.g., https://xxx.execute-api.us-east-1.amazonaws.com/dev): " API_BASE_URL
fi

echo_info "API URL: $API_BASE_URL"
echo ""

# Export environment variables
export APPSYNC_API_URL
export APPSYNC_API_KEY
export API_BASE_URL
export USER_ID="demo-user"
export TENANT_ID="default-tenant"

# Step 8: Test subscription
echo_step "8. Testing AppSync subscription..."
echo ""
echo "Choose a test to run:"
echo "  1. Test subscription connection only"
echo "  2. Submit report and monitor real-time status"
echo "  3. Submit query and monitor real-time status"
echo "  4. Run full test suite"
echo "  5. Skip testing"
echo ""

read -p "Enter choice (1-5): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        echo_info "Testing subscription connection..."
        python3 -c "
import asyncio
from appsync_client_example import AppSyncStatusSubscriber

async def test():
    sub = AppSyncStatusSubscriber('$APPSYNC_API_URL', '$APPSYNC_API_KEY', '$USER_ID')
    task = asyncio.create_task(sub.subscribe())
    await asyncio.sleep(5)
    await sub.unsubscribe()
    task.cancel()
    print('✅ Connection test passed')

asyncio.run(test())
"
        ;;
    2)
        echo_info "Submitting report and monitoring status..."
        python3 appsync_client_example.py ingest
        ;;
    3)
        echo_info "Submitting query and monitoring status..."
        python3 appsync_client_example.py query
        ;;
    4)
        echo_info "Running full test suite..."
        python3 test_appsync_realtime.py
        ;;
    5)
        echo_warn "Skipping tests"
        ;;
    *)
        echo_warn "Invalid choice. Skipping tests."
        ;;
esac

echo ""

# Step 9: Summary
echo "=========================================="
echo "Quick Start Complete!"
echo "=========================================="
echo ""
echo_info "✅ AppSync is deployed and ready to use"
echo ""
echo "Configuration:"
echo "  AppSync URL: $APPSYNC_API_URL"
echo "  API Gateway: $API_BASE_URL"
echo ""
echo "Next Steps:"
echo ""
echo "1. Monitor real-time status updates:"
echo "   python appsync_client_example.py monitor"
echo ""
echo "2. Test ingest with real-time monitoring:"
echo "   python appsync_client_example.py ingest"
echo ""
echo "3. Test query with real-time monitoring:"
echo "   python appsync_client_example.py query"
echo ""
echo "4. Run comprehensive tests:"
echo "   python test_appsync_realtime.py"
echo ""
echo "5. View client examples:"
echo "   - Python: appsync_client_example.py"
echo "   - JavaScript: appsync_client_example.js"
echo ""
echo "6. Check implementation details:"
echo "   cat APPSYNC_IMPLEMENTATION.py"
echo ""
echo "Troubleshooting:"
echo "  - Check AppSync logs: aws logs tail /aws/appsync/apis/$APPSYNC_API_ID --follow"
echo "  - Check Lambda logs: aws logs tail /aws/lambda/$ORCHESTRATOR_FUNCTION --follow"
echo "  - Review configuration: cat .env.appsync"
echo ""
echo "=========================================="
echo ""

# Save session info
cat > .quickstart_session << EOF
# Quick Start Session Info
# Generated: $(date)

export APPSYNC_API_URL="$APPSYNC_API_URL"
export APPSYNC_API_KEY="$APPSYNC_API_KEY"
export API_BASE_URL="$API_BASE_URL"
export USER_ID="$USER_ID"
export TENANT_ID="$TENANT_ID"
export AWS_REGION="$REGION"

# To restore this session, run:
# source .quickstart_session
EOF

echo_info "Session saved to .quickstart_session"
echo_info "To restore: source .quickstart_session"
echo ""
