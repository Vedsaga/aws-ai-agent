#!/bin/bash

# Deploy Orchestrator Lambda with Agent Execution
# This script packages and deploys the orchestrator that actually runs agents

set -e

echo "=========================================="
echo "Orchestrator Lambda Deployment"
echo "=========================================="

# Configuration
REGION="us-east-1"
ORCHESTRATOR_FUNCTION="MultiAgentOrchestration-dev-Orchestrator"
INGEST_FUNCTION="MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY_FUNCTION="MultiAgentOrchestration-dev-Api-QueryHandler"
TEMP_DIR="/tmp/orchestrator_deploy_$$"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create temporary directory
log_info "Creating temporary directory..."
mkdir -p $TEMP_DIR
cd $TEMP_DIR

# Step 2: Copy orchestrator handler
log_info "Copying orchestrator handler..."
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/orchestrator_handler.py handler.py

# Step 3: Create requirements.txt
log_info "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
boto3>=1.28.0
EOF

# Step 4: Install dependencies (if any additional needed)
log_info "Installing dependencies..."
pip3 install -r requirements.txt -t . --quiet || log_warning "Some dependencies may already exist"

# Step 5: Create deployment package
log_info "Creating deployment package..."
zip -r9 deployment.zip . -x "*.pyc" "__pycache__/*" > /dev/null

PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
log_info "Package size: $PACKAGE_SIZE"

# Step 6: Check if orchestrator function exists
log_info "Checking if orchestrator function exists..."

if aws lambda get-function --function-name $ORCHESTRATOR_FUNCTION --region $REGION > /dev/null 2>&1; then
    log_info "Function exists, updating code..."

    aws lambda update-function-code \
        --function-name $ORCHESTRATOR_FUNCTION \
        --zip-file fileb://deployment.zip \
        --region $REGION > /dev/null

    log_info "Waiting for update to complete..."
    aws lambda wait function-updated \
        --function-name $ORCHESTRATOR_FUNCTION \
        --region $REGION

    log_info "Updating configuration..."
    aws lambda update-function-configuration \
        --function-name $ORCHESTRATOR_FUNCTION \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={
            CONFIGURATIONS_TABLE=MultiAgentOrchestration-dev-Data-Configurations,
            INCIDENTS_TABLE=MultiAgentOrchestration-dev-Incidents,
            AWS_REGION=$REGION
        }" \
        --region $REGION > /dev/null

    log_info "✓ Orchestrator function updated"
else
    log_warning "Orchestrator function does not exist, creating..."

    # Get execution role (use existing role from IngestHandler)
    ROLE_ARN=$(aws lambda get-function \
        --function-name $INGEST_FUNCTION \
        --region $REGION \
        --query 'Configuration.Role' \
        --output text)

    if [ -z "$ROLE_ARN" ]; then
        log_error "Could not find execution role"
        exit 1
    fi

    log_info "Using role: $ROLE_ARN"

    aws lambda create-function \
        --function-name $ORCHESTRATOR_FUNCTION \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler handler.handler \
        --zip-file fileb://deployment.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={
            CONFIGURATIONS_TABLE=MultiAgentOrchestration-dev-Data-Configurations,
            INCIDENTS_TABLE=MultiAgentOrchestration-dev-Incidents,
            AWS_REGION=$REGION
        }" \
        --region $REGION > /dev/null

    log_info "✓ Orchestrator function created"
fi

# Step 7: Grant Bedrock permissions
log_info "Adding Bedrock permissions to execution role..."

ROLE_NAME=$(aws lambda get-function \
    --function-name $ORCHESTRATOR_FUNCTION \
    --region $REGION \
    --query 'Configuration.Role' \
    --output text | awk -F'/' '{print $NF}')

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
    --region $REGION 2>/dev/null || log_warning "Bedrock policy may already be attached"

log_info "✓ Bedrock permissions configured"

# Step 8: Update IngestHandler to use new code
log_info "Updating IngestHandler with orchestrator integration..."

cd ~/hackathon/aws-ai-agent
cp infrastructure/lambda/orchestration/ingest_handler_with_orchestrator.py $TEMP_DIR/ingest_handler.py

cd $TEMP_DIR
rm -f deployment.zip
zip -r9 deployment.zip ingest_handler.py > /dev/null

aws lambda update-function-code \
    --function-name $INGEST_FUNCTION \
    --zip-file fileb://deployment.zip \
    --region $REGION > /dev/null

log_info "Waiting for IngestHandler update..."
aws lambda wait function-updated \
    --function-name $INGEST_FUNCTION \
    --region $REGION

# Update environment variables
aws lambda update-function-configuration \
    --function-name $INGEST_FUNCTION \
    --environment "Variables={
        INCIDENTS_TABLE=MultiAgentOrchestration-dev-Incidents,
        ORCHESTRATOR_FUNCTION=$ORCHESTRATOR_FUNCTION,
        AWS_REGION=$REGION
    }" \
    --region $REGION > /dev/null

log_info "✓ IngestHandler updated"

# Step 9: Grant IngestHandler permission to invoke Orchestrator
log_info "Granting invoke permissions..."

INGEST_ROLE=$(aws lambda get-function \
    --function-name $INGEST_FUNCTION \
    --region $REGION \
    --query 'Configuration.Role' \
    --output text | awk -F'/' '{print $NF}')

# Create inline policy for Lambda invocation
cat > /tmp/lambda-invoke-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:InvokeAsync"
            ],
            "Resource": "arn:aws:lambda:$REGION:*:function:$ORCHESTRATOR_FUNCTION"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name $INGEST_ROLE \
    --policy-name OrchestratorInvokePolicy \
    --policy-document file:///tmp/lambda-invoke-policy.json \
    --region $REGION

log_info "✓ Invoke permissions granted"

# Step 10: Test orchestrator
log_info "Testing orchestrator with sample payload..."

TEST_PAYLOAD='{
    "job_id": "test_'$(date +%s)'",
    "job_type": "ingest",
    "domain_id": "civic_complaints",
    "text": "TEST: There is a pothole on Main Street causing traffic issues",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}'

aws lambda invoke \
    --function-name $ORCHESTRATOR_FUNCTION \
    --payload "$TEST_PAYLOAD" \
    --region $REGION \
    /tmp/orchestrator_test_response.json > /dev/null

if [ -f /tmp/orchestrator_test_response.json ]; then
    log_info "Test response:"
    cat /tmp/orchestrator_test_response.json | jq '.' 2>/dev/null || cat /tmp/orchestrator_test_response.json
    echo ""
fi

# Step 11: Cleanup
log_info "Cleaning up temporary files..."
cd ~
rm -rf $TEMP_DIR
rm -f /tmp/lambda-invoke-policy.json

# Step 12: Get function details
log_info "=========================================="
log_info "Deployment Summary"
log_info "=========================================="

ORCHESTRATOR_ARN=$(aws lambda get-function \
    --function-name $ORCHESTRATOR_FUNCTION \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

log_info "Orchestrator Function: $ORCHESTRATOR_FUNCTION"
log_info "ARN: $ORCHESTRATOR_ARN"
log_info "Region: $REGION"
log_info ""
log_info "IngestHandler updated to trigger orchestrator"
log_info "Bedrock permissions configured"
log_info ""
log_info "=========================================="
log_info "✓ Deployment Complete!"
log_info "=========================================="
log_info ""
log_info "Next steps:"
log_info "1. Submit a test report via API"
log_info "2. Check CloudWatch logs for agent execution"
log_info "3. Verify structured data in DynamoDB"
log_info ""
log_info "Monitor logs:"
log_info "  aws logs tail /aws/lambda/$ORCHESTRATOR_FUNCTION --follow --region $REGION"
log_info ""

echo "Done!"
