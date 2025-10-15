#!/bin/bash

# Deployment script for Command Center Backend
# Usage: ./scripts/deploy.sh [--stage dev|staging|prod] [--skip-validation]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
STAGE=${STAGE:-dev}
SKIP_VALIDATION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stage)
            STAGE="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--stage dev|staging|prod] [--skip-validation]"
            echo ""
            echo "Options:"
            echo "  --stage           Deployment stage (default: dev)"
            echo "  --skip-validation Skip post-deployment validation"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate stage
if [[ ! "$STAGE" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid stage '$STAGE'. Must be dev, staging, or prod${NC}"
    exit 1
fi

echo -e "${GREEN}=== Command Center Backend Deployment ===${NC}"
echo -e "Stage: ${YELLOW}${STAGE}${NC}"
echo ""

# Check if AWS CLI is configured
echo -e "${BLUE}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not configured or credentials are invalid${NC}"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo -e "${GREEN}✓ AWS credentials verified${NC}"
echo -e "  Account: ${AWS_ACCOUNT}"
echo -e "  Region: ${AWS_REGION}"
echo ""

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    echo -e "${BLUE}Loading environment variables from .env.local...${NC}"
    export $(grep -v '^#' .env.local | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${YELLOW}⚠ No .env.local file found, using defaults${NC}"
fi

# Set CDK environment variables
export CDK_DEFAULT_ACCOUNT=${AWS_ACCOUNT}
export CDK_DEFAULT_REGION=${AWS_REGION}
export STAGE=${STAGE}

echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Build TypeScript
echo -e "${BLUE}Building TypeScript...${NC}"
npm run build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ TypeScript build successful${NC}"
else
    echo -e "${RED}✗ TypeScript build failed${NC}"
    exit 1
fi

# Synthesize CloudFormation template
echo -e "${BLUE}Synthesizing CloudFormation template...${NC}"
npm run synth
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CloudFormation template synthesized${NC}"
else
    echo -e "${RED}✗ CloudFormation synthesis failed${NC}"
    exit 1
fi

# Deploy
echo ""
echo -e "${BLUE}Deploying stack to AWS...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"
npm run deploy -- --require-approval never

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deployed successfully${NC}"
else
    echo -e "${RED}✗ Stack deployment failed${NC}"
    exit 1
fi

# Get stack outputs
STACK_NAME="CommandCenterBackendStack"
echo ""
echo -e "${BLUE}Retrieving stack outputs...${NC}"
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack outputs retrieved${NC}"
    echo ""
    echo -e "${YELLOW}Stack Outputs:${NC}"
    echo "${OUTPUTS}" | jq -r '.[] | "  \(.OutputKey): \(.OutputValue)"'
    
    # Extract key outputs for validation
    API_ENDPOINT=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue')
    TABLE_NAME=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="TableName") | .OutputValue')
    AGENT_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="AgentId") | .OutputValue')
else
    echo -e "${YELLOW}⚠ Could not retrieve stack outputs${NC}"
    SKIP_VALIDATION=true
fi

# Post-deployment validation
if [ "$SKIP_VALIDATION" = false ]; then
    echo ""
    echo -e "${BLUE}Running post-deployment validation...${NC}"
    
    # Validate DynamoDB table exists
    if [ ! -z "$TABLE_NAME" ]; then
        echo -e "${BLUE}Checking DynamoDB table...${NC}"
        aws dynamodb describe-table --table-name ${TABLE_NAME} &> /dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ DynamoDB table exists and is accessible${NC}"
        else
            echo -e "${RED}✗ DynamoDB table validation failed${NC}"
            exit 1
        fi
    fi
    
    # Validate API Gateway endpoint
    if [ ! -z "$API_ENDPOINT" ]; then
        echo -e "${BLUE}Checking API Gateway endpoint...${NC}"
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${API_ENDPOINT}/data/updates?since=2023-01-01T00:00:00Z || echo "000")
        if [[ "$HTTP_CODE" =~ ^(200|400|401|403)$ ]]; then
            echo -e "${GREEN}✓ API Gateway endpoint is accessible (HTTP ${HTTP_CODE})${NC}"
        else
            echo -e "${YELLOW}⚠ API Gateway endpoint returned unexpected status: ${HTTP_CODE}${NC}"
        fi
    fi
    
    # Validate Bedrock Agent
    if [ ! -z "$AGENT_ID" ]; then
        echo -e "${BLUE}Checking Bedrock Agent...${NC}"
        aws bedrock-agent get-agent --agent-id ${AGENT_ID} &> /dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Bedrock Agent exists and is accessible${NC}"
        else
            echo -e "${YELLOW}⚠ Bedrock Agent validation failed (may need permissions)${NC}"
        fi
    fi
    
    echo -e "${GREEN}✓ Post-deployment validation complete${NC}"
fi

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Populate the database: npm run populate-db"
echo "  2. Test the API endpoints: npm run test:integration"
echo ""
if [ ! -z "$API_ENDPOINT" ]; then
    echo -e "${YELLOW}API Endpoint:${NC} ${API_ENDPOINT}"
fi
echo ""
echo "To view full stack details:"
echo "  aws cloudformation describe-stacks --stack-name ${STACK_NAME}"
