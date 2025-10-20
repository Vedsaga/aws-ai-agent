#!/bin/bash

# Deploy Orchestrator Lambda with Realtime Status Updates
# This script packages and deploys the orchestrator with status publishing integration

set -e

echo "=========================================="
echo "Orchestrator + Realtime Deployment"
echo "=========================================="

# Configuration
REGION="us-east-1"
ORCHESTRATOR_FUNCTION="MultiAgentOrchestration-dev-Orchestrator"
INGEST_FUNCTION="MultiAgentOrchestration-dev-Api-IngestHandler"
QUERY_FUNCTION="MultiAgentOrchestration-dev-Api-QueryHandler"
STATUS_PUBLISHER_FUNCTION="MultiAgentOrchestration-dev-StatusPublisher"
TEMP_DIR="/tmp/orchestrator_realtime_deploy_$$"

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

# Step 2: Copy orchestrator handler and realtime utilities
log_info "Copying orchestrator handler with realtime integration..."
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/orchestrator_handler.py orchestrator_handler.py

# Copy realtime utilities
mkdir -p realtime
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py realtime/
touch realtime/__init__.py

log_info "Files copied:"
ls -lh orchestrator_handler.py
ls -lh realtime/

# Step 3: Create requirements.txt
log_info "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
boto3>=1.28.0
EOF

# Step 4: Create deployment package
log_info "Creating deployment package..."
zip -r9 deployment.zip orchestrator_handler.py realtime/ -x "*.pyc" "__pycache__/*" > /dev/null

PACKAGE_SIZE=$(du -h deployment.zip | cut -f1)
log_info "Package size: $PACKAGE_SIZE"

# Step 5: Check if orchestrator function exists
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
            BEDROCK_REGION=$REGION,
            STATUS_PUBLISHER_FUNCTION=$STATUS_PUBLISHER_FUNCTION
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
        --handler orchestrator_handler.handler \
        --zip-file fileb://deployment.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={
            CONFIGURATIONS_TABLE=MultiAgentOrchestration-dev-Data-Configurations,
            INCIDENTS_TABLE=MultiAgentOrchestration-dev-Incidents,
            BEDROCK_REGION=$REGION,
            STATUS_PUBLISHER_FUNCTION=$STATUS_PUBLISHER_FUNCTION
        }" \
        --region $REGION > /dev/null

    log_info "✓ Orchestrator function created"
fi

# Step 6: Grant Bedrock and Location Service permissions
log_info "Adding Bedrock and Location Service permissions..."

ROLE_NAME=$(aws lambda get-function \
    --function-name $ORCHESTRATOR_FUNCTION \
    --region $REGION \
    --query 'Configuration.Role' \
    --output text | awk -F'/' '{print $NF}')

aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess \
    --region $REGION 2>/dev/null || log_warning "Bedrock policy may already be attached"

# Add Location Service permissions
cat > /tmp/location-policy.json << 'EOFPOLICY'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "geo:SearchPlaceIndexForText",
                "geo:SearchPlaceIndexForPosition",
                "geo:GetPlace"
            ],
            "Resource": "*"
        }
    ]
}
EOFPOLICY

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name LocationServicePolicy \
    --policy-document file:///tmp/location-policy.json \
    --region $REGION

log_info "✓ Bedrock and Location Service permissions configured"

# Step 7: Grant permission to invoke Status Publisher
log_info "Granting permission to invoke Status Publisher..."

if aws lambda get-function --function-name $STATUS_PUBLISHER_FUNCTION --region $REGION > /dev/null 2>&1; then
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name StatusPublisherInvokePolicy \
        --policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [{
                \"Effect\": \"Allow\",
                \"Action\": [\"lambda:InvokeFunction\"],
                \"Resource\": \"arn:aws:lambda:$REGION:*:function:$STATUS_PUBLISHER_FUNCTION\"
            }]
        }" \
        --region $REGION
    
    log_info "✓ Status Publisher invoke permission granted"
else
    log_warning "Status Publisher function not found, skipping permission grant"
fi

# Step 8: Update IngestHandler with realtime integration
log_info "Updating IngestHandler with realtime integration..."

cd $TEMP_DIR
rm -rf *
mkdir -p realtime

cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/ingest_handler_with_orchestrator.py ingest_handler_simple.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py realtime/
touch realtime/__init__.py

zip -r9 deployment.zip ingest_handler_simple.py realtime/ -x "*.pyc" "__pycache__/*" > /dev/null

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
        STATUS_PUBLISHER_FUNCTION=$STATUS_PUBLISHER_FUNCTION,
        BEDROCK_REGION=$REGION
    }" \
    --region $REGION > /dev/null

log_info "✓ IngestHandler updated"

# Step 9: Update QueryHandler with realtime integration
log_info "Updating QueryHandler with realtime integration..."

cd $TEMP_DIR
rm -rf *
mkdir -p realtime

cp ~/hackathon/aws-ai-agent/infrastructure/lambda/orchestration/query_index.py query_handler_simple.py
cp ~/hackathon/aws-ai-agent/infrastructure/lambda/realtime/status_utils.py realtime/
touch realtime/__init__.py

zip -r9 deployment.zip query_handler_simple.py realtime/ -x "*.pyc" "__pycache__/*" > /dev/null

aws lambda update-function-code \
    --function-name $QUERY_FUNCTION \
    --zip-file fileb://deployment.zip \
    --region $REGION > /dev/null

log_info "Waiting for QueryHandler update..."
aws lambda wait function-updated \
    --function-name $QUERY_FUNCTION \
    --region $REGION

# Update environment variables
aws lambda update-function-configuration \
    --function-name $QUERY_FUNCTION \
    --environment "Variables={
        DATA_QUERIES_TABLE=MultiAgentOrchestration-dev-DataQueries,
        ORCHESTRATOR_FUNCTION=$ORCHESTRATOR_FUNCTION,
        STATUS_PUBLISHER_FUNCTION=$STATUS_PUBLISHER_FUNCTION,
        BEDROCK_REGION=$REGION
    }" \
    --region $REGION > /dev/null

log_info "✓ QueryHandler updated"

# Step 10: Grant IngestHandler and QueryHandler permission to invoke Orchestrator
log_info "Granting invoke permissions..."

for HANDLER_FUNCTION in $INGEST_FUNCTION $QUERY_FUNCTION; do
    HANDLER_ROLE=$(aws lambda get-function \
        --function-name $HANDLER_FUNCTION \
        --region $REGION \
        --query 'Configuration.Role' \
        --output text | awk -F'/' '{print $NF}')

    # Grant Lambda invocation permission
    aws iam put-role-policy \
        --role-name $HANDLER_ROLE \
        --policy-name OrchestratorInvokePolicy \
        --policy-document "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [{
                \"Effect\": \"Allow\",
                \"Action\": [\"lambda:InvokeFunction\", \"lambda:InvokeAsync\"],
                \"Resource\": \"arn:aws:lambda:$REGION:*:function:$ORCHESTRATOR_FUNCTION\"
            }]
        }" \
        --region $REGION
    
    # Grant Status Publisher invocation permission
    if aws lambda get-function --function-name $STATUS_PUBLISHER_FUNCTION --region $REGION > /dev/null 2>&1; then
        aws iam put-role-policy \
            --role-name $HANDLER_ROLE \
            --policy-name StatusPublisherInvokePolicy \
            --policy-document "{
                \"Version\": \"2012-10-17\",
                \"Statement\": [{
                    \"Effect\": \"Allow\",
                    \"Action\": [\"lambda:InvokeFunction\"],
                    \"Resource\": \"arn:aws:lambda:$REGION:*:function:$STATUS_PUBLISHER_FUNCTION\"
                }]
            }" \
            --region $REGION
    fi
    
    log_info "✓ Permissions granted for $HANDLER_FUNCTION"
done

# Step 11: Test orchestrator
log_info "Testing orchestrator with sample payload..."

TIMESTAMP=$(date +%s)
cat > /tmp/test_payload.json << EOFTEST
{
    "job_id": "test_${TIMESTAMP}",
    "job_type": "ingest",
    "domain_id": "civic_complaints",
    "text": "TEST: There is a pothole on Main Street near Central Park causing traffic issues",
    "tenant_id": "default-tenant",
    "user_id": "test-user"
}
EOFTEST

aws lambda invoke \
    --function-name $ORCHESTRATOR_FUNCTION \
    --payload file:///tmp/test_payload.json \
    --region $REGION \
    /tmp/orchestrator_test_response.json > /dev/null

if [ -f /tmp/orchestrator_test_response.json ]; then
    log_info "Test response:"
    cat /tmp/orchestrator_test_response.json | jq '.' 2>/dev/null || cat /tmp/orchestrator_test_response.json
    echo ""
fi

# Step 12: Cleanup
log_info "Cleaning up temporary files..."
cd ~
rm -rf $TEMP_DIR
rm -f /tmp/location-policy.json
rm -f /tmp/orchestrator_test_response.json
rm -f /tmp/test_payload.json

# Step 13: Get function details
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
log_info "✓ Orchestrator with realtime status updates"
log_info "✓ IngestHandler updated with status publishing"
log_info "✓ QueryHandler updated with status publishing"
log_info "✓ Bedrock and Location Service permissions configured"
log_info "✓ Status Publisher integration enabled"
log_info ""
log_info "=========================================="
log_info "✓ Deployment Complete!"
log_info "=========================================="
log_info ""
log_info "Next steps:"
log_info "1. Submit a test report via API"
log_info "2. Monitor realtime status updates via AppSync"
log_info "3. Check CloudWatch logs for agent execution"
log_info "4. Verify structured data in DynamoDB"
log_info ""
log_info "Monitor logs:"
log_info "  aws logs tail /aws/lambda/$ORCHESTRATOR_FUNCTION --follow --region $REGION"
log_info ""

echo "Done!"
