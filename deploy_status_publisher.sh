#!/bin/bash

# Deploy Status Publisher Lambda Function
# This creates/updates the Lambda function that publishes status to AppSync

set -e

echo "=================================================="
echo "Deploying Status Publisher Lambda"
echo "=================================================="
echo ""

# Configuration
FUNCTION_NAME="MultiAgentOrchestration-dev-StatusPublisher"
REGION=${AWS_REGION:-us-east-1}
RUNTIME="python3.11"
HANDLER="status_publisher.lambda_handler"
TIMEOUT=30
MEMORY=256

# Table names
USER_SESSIONS_TABLE="MultiAgentOrchestration-dev-Data-UserSessions"
APPSYNC_API_URL=${APPSYNC_API_URL:-""}
APPSYNC_API_ID=${APPSYNC_API_ID:-""}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "infrastructure/lambda/realtime" ]; then
    echo_error "Please run from project root directory"
    exit 1
fi

cd infrastructure/lambda/realtime

echo_info "Packaging Lambda function..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy Lambda files
cp status_publisher.py $TEMP_DIR/
cp status_utils.py $TEMP_DIR/

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo_info "Installing dependencies..."
    pip install -q -r requirements.txt -t $TEMP_DIR/
fi

# Create ZIP package
cd $TEMP_DIR
zip -q -r ../lambda.zip .
cd - > /dev/null

PACKAGE_PATH="$TEMP_DIR/../lambda.zip"
PACKAGE_SIZE=$(ls -lh "$PACKAGE_PATH" | awk '{print $5}')
echo_info "Package created: $PACKAGE_SIZE"

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
    echo_info "Function exists. Updating code..."

    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$PACKAGE_PATH" \
        --region "$REGION" \
        --no-cli-pager > /dev/null

    echo_info "Waiting for update to complete..."
    aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"

    # Update environment if provided
    if [ ! -z "$APPSYNC_API_URL" ] && [ ! -z "$APPSYNC_API_ID" ]; then
        echo_info "Updating environment variables..."
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --environment "Variables={USER_SESSIONS_TABLE=$USER_SESSIONS_TABLE,APPSYNC_API_URL=$APPSYNC_API_URL,APPSYNC_API_ID=$APPSYNC_API_ID}" \
            --region "$REGION" \
            --no-cli-pager > /dev/null
    fi

    echo_info "✅ Function updated successfully"
else
    echo_info "Function does not exist. Creating..."

    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

    # Create execution role if needed
    ROLE_NAME="MultiAgentOrchestration-StatusPublisher-Role"
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"

    if ! aws iam get-role --role-name "$ROLE_NAME" --region "$REGION" &> /dev/null; then
        echo_info "Creating IAM role..."

        # Create trust policy
        cat > /tmp/trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        aws iam create-role \
            --role-name "$ROLE_NAME" \
            --assume-role-policy-document file:///tmp/trust-policy.json \
            --region "$REGION" > /dev/null

        # Attach basic execution policy
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
            --region "$REGION"

        # Create inline policy for DynamoDB and AppSync
        cat > /tmp/inline-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$USER_SESSIONS_TABLE*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "appsync:GraphQL"
      ],
      "Resource": "arn:aws:appsync:$REGION:$ACCOUNT_ID:apis/*/types/Mutation/fields/publishStatus"
    }
  ]
}
EOF

        aws iam put-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "StatusPublisherPolicy" \
            --policy-document file:///tmp/inline-policy.json \
            --region "$REGION"

        echo_info "Waiting for IAM role to propagate..."
        sleep 10
    fi

    # Create Lambda function
    ENV_VARS="Variables={USER_SESSIONS_TABLE=$USER_SESSIONS_TABLE"
    if [ ! -z "$APPSYNC_API_URL" ]; then
        ENV_VARS="$ENV_VARS,APPSYNC_API_URL=$APPSYNC_API_URL"
    fi
    if [ ! -z "$APPSYNC_API_ID" ]; then
        ENV_VARS="$ENV_VARS,APPSYNC_API_ID=$APPSYNC_API_ID"
    fi
    ENV_VARS="$ENV_VARS}"

    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://$PACKAGE_PATH" \
        --timeout "$TIMEOUT" \
        --memory-size "$MEMORY" \
        --environment "$ENV_VARS" \
        --region "$REGION" \
        --no-cli-pager > /dev/null

    echo_info "✅ Function created successfully"
fi

# Get function ARN
FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)

echo ""
echo_info "Status Publisher Lambda deployed!"
echo_info "Function ARN: $FUNCTION_ARN"
echo ""

# Update orchestrator environment
ORCHESTRATOR_FUNCTION="MultiAgentOrchestration-dev-Orchestrator"
if aws lambda get-function --function-name "$ORCHESTRATOR_FUNCTION" --region "$REGION" &> /dev/null; then
    echo_info "Updating orchestrator with status publisher ARN..."

    # Get current environment
    CURRENT_ENV=$(aws lambda get-function-configuration --function-name "$ORCHESTRATOR_FUNCTION" --region "$REGION" --query 'Environment.Variables' --output json)

    # Add STATUS_PUBLISHER_FUNCTION
    UPDATED_ENV=$(echo "$CURRENT_ENV" | jq -c --arg arn "$FUNCTION_ARN" '. + {STATUS_PUBLISHER_FUNCTION: $arn}')

    aws lambda update-function-configuration \
        --function-name "$ORCHESTRATOR_FUNCTION" \
        --environment Variables="$UPDATED_ENV" \
        --region "$REGION" \
        --no-cli-pager > /dev/null

    echo_info "✅ Orchestrator updated"
fi

# Update ingest handler
INGEST_FUNCTION="MultiAgentOrchestration-dev-Api-IngestHandler"
if aws lambda get-function --function-name "$INGEST_FUNCTION" --region "$REGION" &> /dev/null; then
    echo_info "Updating ingest handler with status publisher ARN..."

    CURRENT_ENV=$(aws lambda get-function-configuration --function-name "$INGEST_FUNCTION" --region "$REGION" --query 'Environment.Variables' --output json)
    UPDATED_ENV=$(echo "$CURRENT_ENV" | jq -c --arg arn "$FUNCTION_ARN" '. + {STATUS_PUBLISHER_FUNCTION: $arn}')

    aws lambda update-function-configuration \
        --function-name "$INGEST_FUNCTION" \
        --environment Variables="$UPDATED_ENV" \
        --region "$REGION" \
        --no-cli-pager > /dev/null

    echo_info "✅ Ingest handler updated"
fi

# Update query handler
QUERY_FUNCTION="MultiAgentOrchestration-dev-Api-QueryHandler"
if aws lambda get-function --function-name "$QUERY_FUNCTION" --region "$REGION" &> /dev/null; then
    echo_info "Updating query handler with status publisher ARN..."

    CURRENT_ENV=$(aws lambda get-function-configuration --function-name "$QUERY_FUNCTION" --region "$REGION" --query 'Environment.Variables' --output json)
    UPDATED_ENV=$(echo "$CURRENT_ENV" | jq -c --arg arn "$FUNCTION_ARN" '. + {STATUS_PUBLISHER_FUNCTION: $arn}')

    aws lambda update-function-configuration \
        --function-name "$QUERY_FUNCTION" \
        --environment Variables="$UPDATED_ENV" \
        --region "$REGION" \
        --no-cli-pager > /dev/null

    echo_info "✅ Query handler updated"
fi

echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "Function: $FUNCTION_NAME"
echo "ARN: $FUNCTION_ARN"
echo ""
echo "Next steps:"
echo "  1. Deploy updated orchestrator/handlers with status publishing code"
echo "  2. Test status updates"
echo ""

cd ../../..
