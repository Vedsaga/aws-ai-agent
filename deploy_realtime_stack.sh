#!/bin/bash

# Deploy Realtime Stack (AppSync for real-time status updates)
# This script deploys the AppSync API and status publisher Lambda

set -e

echo "=================================================="
echo "Deploying Realtime Stack (AppSync)"
echo "=================================================="
echo ""

# Configuration
STACK_NAME="MultiAgentOrchestration-dev-Realtime"
REGION=${AWS_REGION:-us-east-1}
PROFILE=${AWS_PROFILE:-default}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
echo_info "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo_error "AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo_error "Node.js not found. Please install it first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo_error "npm not found. Please install it first."
    exit 1
fi

# Check if infrastructure directory exists
if [ ! -d "infrastructure" ]; then
    echo_error "Infrastructure directory not found. Please run from project root."
    exit 1
fi

cd infrastructure

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo_info "Installing CDK dependencies..."
    npm install
fi

# Check if UserSessions table exists
echo_info "Checking for UserSessions table..."
USER_SESSIONS_TABLE="MultiAgentOrchestration-dev-UserSessions"

if aws dynamodb describe-table --table-name "$USER_SESSIONS_TABLE" --region "$REGION" --profile "$PROFILE" &> /dev/null; then
    echo_info "UserSessions table found: $USER_SESSIONS_TABLE"
else
    echo_warn "UserSessions table not found. Creating..."

    aws dynamodb create-table \
        --table-name "$USER_SESSIONS_TABLE" \
        --attribute-definitions \
            AttributeName=user_id,AttributeType=S \
            AttributeName=session_id,AttributeType=S \
        --key-schema \
            AttributeName=user_id,KeyType=HASH \
            AttributeName=session_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --profile "$PROFILE" \
        --tags Key=Environment,Value=dev Key=Project,Value=MultiAgentOrchestration

    echo_info "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "$USER_SESSIONS_TABLE" --region "$REGION" --profile "$PROFILE"
    echo_info "UserSessions table created successfully"
fi

# Create GraphQL schema if it doesn't exist
SCHEMA_PATH="lambda/realtime/schema.graphql"
if [ ! -f "$SCHEMA_PATH" ]; then
    echo_warn "GraphQL schema not found. It should already exist at $SCHEMA_PATH"
    exit 1
fi

echo_info "GraphQL schema found at $SCHEMA_PATH"

# Package status publisher Lambda
echo_info "Packaging status publisher Lambda..."
REALTIME_DIR="lambda/realtime"

if [ ! -d "$REALTIME_DIR" ]; then
    echo_error "Realtime Lambda directory not found: $REALTIME_DIR"
    exit 1
fi

# Check Python files exist
if [ ! -f "$REALTIME_DIR/status_publisher.py" ]; then
    echo_error "status_publisher.py not found in $REALTIME_DIR"
    exit 1
fi

if [ ! -f "$REALTIME_DIR/status_utils.py" ]; then
    echo_error "status_utils.py not found in $REALTIME_DIR"
    exit 1
fi

echo_info "All Lambda files found"

# Deploy using CDK
echo ""
echo_info "Deploying Realtime Stack with CDK..."
echo ""

# Check if CDK is bootstrapped
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region "$REGION" --profile "$PROFILE" &> /dev/null; then
    echo_warn "CDK not bootstrapped. Bootstrapping now..."
    npx cdk bootstrap --profile "$PROFILE" --region "$REGION"
fi

# Deploy the stack
echo_info "Running CDK deploy..."
npx cdk deploy "$STACK_NAME" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --require-approval never \
    --outputs-file cdk-outputs.json

if [ $? -eq 0 ]; then
    echo ""
    echo_info "Realtime Stack deployed successfully!"

    # Extract outputs
    if [ -f "cdk-outputs.json" ]; then
        echo ""
        echo_info "Stack Outputs:"
        echo "---------------------------------------------------"

        APPSYNC_URL=$(cat cdk-outputs.json | grep -o '"AppSyncApiUrl": "[^"]*"' | cut -d'"' -f4)
        APPSYNC_API_KEY=$(cat cdk-outputs.json | grep -o '"AppSyncApiKey": "[^"]*"' | cut -d'"' -f4)
        APPSYNC_API_ID=$(cat cdk-outputs.json | grep -o '"AppSyncApiId": "[^"]*"' | cut -d'"' -f4)
        STATUS_PUBLISHER_ARN=$(cat cdk-outputs.json | grep -o '"StatusPublisherFunctionArn": "[^"]*"' | cut -d'"' -f4)

        if [ ! -z "$APPSYNC_URL" ]; then
            echo_info "AppSync API URL: $APPSYNC_URL"
        fi

        if [ ! -z "$APPSYNC_API_KEY" ]; then
            echo_info "AppSync API Key: $APPSYNC_API_KEY"
        fi

        if [ ! -z "$APPSYNC_API_ID" ]; then
            echo_info "AppSync API ID: $APPSYNC_API_ID"
        fi

        if [ ! -z "$STATUS_PUBLISHER_ARN" ]; then
            echo_info "Status Publisher ARN: $STATUS_PUBLISHER_ARN"
        fi

        echo "---------------------------------------------------"

        # Save to environment file
        ENV_FILE="../.env.appsync"
        echo "# AppSync Configuration" > "$ENV_FILE"
        echo "APPSYNC_API_URL=$APPSYNC_URL" >> "$ENV_FILE"
        echo "APPSYNC_API_KEY=$APPSYNC_API_KEY" >> "$ENV_FILE"
        echo "APPSYNC_API_ID=$APPSYNC_API_ID" >> "$ENV_FILE"
        echo "STATUS_PUBLISHER_FUNCTION=$STATUS_PUBLISHER_ARN" >> "$ENV_FILE"

        echo_info "Environment variables saved to $ENV_FILE"
    fi

    echo ""
    echo_info "Next steps:"
    echo "  1. Update orchestrator Lambda environment variables with STATUS_PUBLISHER_FUNCTION"
    echo "  2. Test real-time subscriptions using the client examples"
    echo "  3. Submit a report/query and monitor status updates in real-time"
    echo ""
    echo_info "Client examples:"
    echo "  - Python: python appsync_client_example.py ingest"
    echo "  - Node.js: node appsync_client_example.js"
    echo ""

else
    echo ""
    echo_error "Realtime Stack deployment failed!"
    exit 1
fi

# Update orchestrator environment variables
echo ""
echo_info "Updating orchestrator Lambda with STATUS_PUBLISHER_FUNCTION..."

ORCHESTRATOR_FUNCTION="MultiAgentOrchestration-dev-Orchestrator"

if aws lambda get-function --function-name "$ORCHESTRATOR_FUNCTION" --region "$REGION" --profile "$PROFILE" &> /dev/null; then
    if [ ! -z "$STATUS_PUBLISHER_ARN" ]; then
        aws lambda update-function-configuration \
            --function-name "$ORCHESTRATOR_FUNCTION" \
            --environment Variables={STATUS_PUBLISHER_FUNCTION="$STATUS_PUBLISHER_ARN"} \
            --region "$REGION" \
            --profile "$PROFILE" &> /dev/null

        echo_info "Orchestrator Lambda updated with status publisher ARN"
    fi
else
    echo_warn "Orchestrator Lambda not found. You'll need to update it manually later."
fi

# Update ingest handler environment variables
INGEST_FUNCTION="MultiAgentOrchestration-dev-IngestHandler"

if aws lambda get-function --function-name "$INGEST_FUNCTION" --region "$REGION" --profile "$PROFILE" &> /dev/null; then
    if [ ! -z "$STATUS_PUBLISHER_ARN" ]; then
        aws lambda update-function-configuration \
            --function-name "$INGEST_FUNCTION" \
            --environment Variables={STATUS_PUBLISHER_FUNCTION="$STATUS_PUBLISHER_ARN"} \
            --region "$REGION" \
            --profile "$PROFILE" &> /dev/null

        echo_info "Ingest Handler Lambda updated with status publisher ARN"
    fi
else
    echo_warn "Ingest Handler Lambda not found. You'll need to update it manually later."
fi

# Update query handler environment variables
QUERY_FUNCTION="MultiAgentOrchestration-dev-QueryHandler"

if aws lambda get-function --function-name "$QUERY_FUNCTION" --region "$REGION" --profile "$PROFILE" &> /dev/null; then
    if [ ! -z "$STATUS_PUBLISHER_ARN" ]; then
        aws lambda update-function-configuration \
            --function-name "$QUERY_FUNCTION" \
            --environment Variables={STATUS_PUBLISHER_FUNCTION="$STATUS_PUBLISHER_ARN"} \
            --region "$REGION" \
            --profile "$PROFILE" &> /dev/null

        echo_info "Query Handler Lambda updated with status publisher ARN"
    fi
else
    echo_warn "Query Handler Lambda not found. You'll need to update it manually later."
fi

echo ""
echo_info "Deployment complete!"
echo ""

cd ..
