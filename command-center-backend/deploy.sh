#!/bin/bash

# Command Center Backend - Full Deployment Script
# This script handles everything: prerequisites check, CDK bootstrap, build, deployment, and database population
# Usage: ./deploy.sh [--stage dev|staging|prod] [--skip-populate] [--skip-bootstrap]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default values
STAGE=${STAGE:-dev}
SKIP_POPULATE=false
SKIP_BOOTSTRAP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stage)
            STAGE="$2"
            shift 2
            ;;
        --skip-populate)
            SKIP_POPULATE=true
            shift
            ;;
        --skip-bootstrap)
            SKIP_BOOTSTRAP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --stage STAGE        Deployment stage (default: dev)"
            echo "                       Options: dev, staging, prod"
            echo "  --skip-populate      Skip database population after deployment"
            echo "  --skip-bootstrap     Skip CDK bootstrap check"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Deploy dev environment"
            echo "  $0 --stage prod              # Deploy to production"
            echo "  $0 --skip-populate           # Deploy without populating database"
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

echo -e "${BOLD}${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Command Center Backend - Full Deployment                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "Stage: ${YELLOW}${STAGE}${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BOLD}${BLUE}[1/7] Checking prerequisites...${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm v$(npm --version)${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo -e "${GREEN}✓ AWS credentials configured${NC}"
echo -e "  Account: ${AWS_ACCOUNT}"
echo -e "  Region: ${AWS_REGION}"

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}✗ AWS CDK not installed${NC}"
    echo "Run: npm install -g aws-cdk"
    exit 1
fi
echo -e "${GREEN}✓ AWS CDK installed${NC}"
echo ""

# Step 2: Check CDK bootstrap
if [ "$SKIP_BOOTSTRAP" = false ]; then
    echo -e "${BOLD}${BLUE}[2/7] Checking CDK bootstrap...${NC}"
    
    BOOTSTRAP_STACK=$(aws cloudformation describe-stacks \
        --stack-name CDKToolkit \
        --region ${AWS_REGION} 2>&1 || echo "NOT_FOUND")
    
    if [[ "$BOOTSTRAP_STACK" == *"NOT_FOUND"* ]] || [[ "$BOOTSTRAP_STACK" == *"does not exist"* ]]; then
        echo -e "${YELLOW}⚠ CDK not bootstrapped${NC}"
        echo -e "${BLUE}Bootstrapping CDK...${NC}"
        cdk bootstrap aws://${AWS_ACCOUNT}/${AWS_REGION}
        echo -e "${GREEN}✓ CDK bootstrap complete${NC}"
    else
        echo -e "${GREEN}✓ CDK already bootstrapped${NC}"
    fi
else
    echo -e "${BLUE}[2/7] Skipping CDK bootstrap check${NC}"
fi
echo ""

# Step 3: Install dependencies
echo -e "${BOLD}${BLUE}[3/7] Installing dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
echo ""

# Step 4: Build and bundle
echo -e "${BOLD}${BLUE}[4/7] Building and bundling Lambda functions...${NC}"

# Clean previous builds
rm -rf dist lambda-bundle

# Build TypeScript
npm run build
echo -e "${GREEN}✓ TypeScript compiled${NC}"

# Create bundle with dependencies
mkdir -p lambda-bundle
cp -r dist/* lambda-bundle/
cp package.json lambda-bundle/
cp package-lock.json lambda-bundle/ 2>/dev/null || true

cd lambda-bundle
npm install --production --no-optional --ignore-scripts --silent

# Optimize bundle size
find node_modules -name "*.md" -type f -delete 2>/dev/null || true
find node_modules -name "*.ts" -type f -delete 2>/dev/null || true
find node_modules -name "*.map" -type f -delete 2>/dev/null || true
find node_modules -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true

cd ..
echo -e "${GREEN}✓ Lambda bundle created ($(du -sh lambda-bundle | cut -f1))${NC}"
echo ""

# Step 5: Deploy CDK stack
echo -e "${BOLD}${BLUE}[5/7] Deploying CDK stack...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes...${NC}"
echo ""

export CDK_DEFAULT_ACCOUNT=${AWS_ACCOUNT}
export CDK_DEFAULT_REGION=${AWS_REGION}
export STAGE=${STAGE}

STACK_NAME="CommandCenterBackend-${STAGE^}"
if [ "$STAGE" = "dev" ]; then
    STACK_NAME="CommandCenterBackend-Dev"
fi

cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deployed successfully${NC}"
else
    echo -e "${RED}✗ Stack deployment failed${NC}"
    exit 1
fi
echo ""

# Step 6: Retrieve outputs
echo -e "${BOLD}${BLUE}[6/7] Retrieving deployment information...${NC}"

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${AWS_REGION} \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    API_ENDPOINT=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="APIEndpoint" or .OutputKey=="ApiEndpoint") | .OutputValue // empty')
    API_KEY_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="APIKeyId" or .OutputKey=="ApiKeyId") | .OutputValue // empty')
    TABLE_NAME=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="TableName") | .OutputValue // empty')
    AGENT_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="BedrockAgentId" or .OutputKey=="AgentId") | .OutputValue // empty')
    AGENT_ALIAS_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="BedrockAgentAliasId" or .OutputKey=="AgentAliasId") | .OutputValue // empty')
    
    echo -e "${GREEN}✓ Stack outputs retrieved${NC}"
    echo ""
    echo -e "${BOLD}${CYAN}Deployment Outputs:${NC}"
    echo -e "${YELLOW}API Endpoint:${NC} ${API_ENDPOINT}"
    
    if [ ! -z "$API_KEY_ID" ]; then
        API_KEY_VALUE=$(aws apigateway get-api-key \
            --api-key ${API_KEY_ID} \
            --include-value \
            --query 'value' \
            --output text 2>/dev/null || echo "")
        
        if [ ! -z "$API_KEY_VALUE" ]; then
            echo -e "${YELLOW}API Key:${NC} ${API_KEY_VALUE}"
            
            # Save to .env.local
            cat > .env.local << EOF
# Auto-generated by deployment script
API_ENDPOINT=${API_ENDPOINT}
API_KEY=${API_KEY_VALUE}
TABLE_NAME=${TABLE_NAME}
AGENT_ID=${AGENT_ID}
AGENT_ALIAS_ID=${AGENT_ALIAS_ID}
AWS_REGION=${AWS_REGION}
EOF
            echo -e "${GREEN}✓ Credentials saved to .env.local${NC}"
        fi
    fi
    
    [ ! -z "$TABLE_NAME" ] && echo -e "${YELLOW}DynamoDB Table:${NC} ${TABLE_NAME}"
    [ ! -z "$AGENT_ID" ] && echo -e "${YELLOW}Bedrock Agent ID:${NC} ${AGENT_ID}"
else
    echo -e "${YELLOW}⚠ Could not retrieve stack outputs${NC}"
    TABLE_NAME="CommandCenterBackend-${STAGE}-MasterEventTimeline"
fi
echo ""

# Step 7: Populate database
if [ "$SKIP_POPULATE" = false ]; then
    echo -e "${BOLD}${BLUE}[7/7] Populating database...${NC}"
    echo -e "${YELLOW}This may take 2-3 minutes...${NC}"
    
    export TABLE_NAME=${TABLE_NAME}
    npm run populate-db
    
    if [ $? -eq 0 ]; then
        ITEM_COUNT=$(aws dynamodb scan \
            --table-name ${TABLE_NAME} \
            --select COUNT \
            --region ${AWS_REGION} \
            --output json 2>/dev/null | jq -r '.Count // 0')
        
        echo -e "${GREEN}✓ Database populated (${ITEM_COUNT} items)${NC}"
    else
        echo -e "${YELLOW}⚠ Database population had issues${NC}"
    fi
else
    echo -e "${BLUE}[7/7] Skipping database population${NC}"
    echo -e "${YELLOW}To populate later: npm run populate-db${NC}"
fi
echo ""

# Final summary
echo -e "${BOLD}${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT COMPLETED SUCCESSFULLY             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BOLD}${YELLOW}Next Steps:${NC}"
echo ""
echo -e "1. ${CYAN}Test the API:${NC}"
echo -e "   ./test-api.sh"
echo ""
echo -e "2. ${CYAN}Configure frontend:${NC}"
echo -e "   Copy credentials from .env.local to your frontend"
echo ""
echo -e "3. ${CYAN}View logs:${NC}"
echo -e "   aws logs tail /aws/lambda/${STACK_NAME}-QueryHandler --follow"
echo ""
echo -e "${GREEN}Deployment complete! 🚀${NC}"
echo ""
