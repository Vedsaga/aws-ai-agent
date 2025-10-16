#!/bin/bash

# Full Automated Deployment Script for Command Center Backend
# This script handles everything: CDK bootstrap, deployment, and database population
# Usage: ./scripts/full-deploy.sh [--stage dev|staging|prod] [--skip-populate]

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
SKIP_BOOTSTRAP_CHECK=false
BEDROCK_MODEL=${BEDROCK_MODEL:-"anthropic.claude-3-sonnet-20240229-v1:0"}

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
        --skip-bootstrap-check)
            SKIP_BOOTSTRAP_CHECK=true
            shift
            ;;
        --model)
            BEDROCK_MODEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --stage STAGE           Deployment stage (default: dev)"
            echo "                          Options: dev, staging, prod"
            echo ""
            echo "  --model MODEL           Bedrock model to use (default: claude-3-sonnet)"
            echo "                          Options:"
            echo "                            anthropic.claude-3-sonnet-20240229-v1:0 (default)"
            echo "                            anthropic.claude-3-5-sonnet-20240620-v1:0"
            echo "                            anthropic.claude-3-haiku-20240307-v1:0"
            echo "                            anthropic.claude-3-opus-20240229-v1:0"
            echo ""
            echo "  --skip-populate         Skip database population after deployment"
            echo "  --skip-bootstrap-check  Skip CDK bootstrap check"
            echo "  --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Deploy dev with Claude 3 Sonnet"
            echo "  $0 --stage prod                       # Deploy to production"
            echo "  $0 --model anthropic.claude-3-5-sonnet-20240620-v1:0  # Use Claude 3.5 Sonnet"
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
echo "║   Command Center Backend - Full Automated Deployment      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "Stage: ${YELLOW}${STAGE}${NC}"
echo -e "Model: ${YELLOW}${BEDROCK_MODEL}${NC}"
echo ""

# Step 1: Check AWS credentials
echo -e "${BOLD}${BLUE}[1/8] Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS CLI is not configured or credentials are invalid${NC}"
    echo ""
    echo "Please configure AWS CLI first:"
    echo "  aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
AWS_USER=$(aws sts get-caller-identity --query Arn --output text)

echo -e "${GREEN}✓ AWS credentials verified${NC}"
echo -e "  Account: ${AWS_ACCOUNT}"
echo -e "  Region: ${AWS_REGION}"
echo -e "  User: ${AWS_USER}"
echo ""

# Step 2: Check Bedrock model access
echo -e "${BOLD}${BLUE}[2/8] Checking Bedrock model access...${NC}"
BEDROCK_CHECK=$(aws bedrock list-foundation-models --region ${AWS_REGION} 2>&1 || echo "FAILED")

if [[ "$BEDROCK_CHECK" == *"FAILED"* ]] || [[ "$BEDROCK_CHECK" == *"AccessDenied"* ]]; then
    echo -e "${YELLOW}⚠ Cannot verify Bedrock access (may need permissions)${NC}"
    echo -e "${YELLOW}  Please ensure Bedrock is enabled in your AWS account${NC}"
    echo -e "${YELLOW}  Go to: AWS Console → Bedrock → Model access${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
else
    # Check for Claude 3 Sonnet specifically
    CLAUDE_ACCESS=$(echo "$BEDROCK_CHECK" | grep -i "claude-3-sonnet" || echo "")
    if [ -z "$CLAUDE_ACCESS" ]; then
        echo -e "${YELLOW}⚠ Claude 3 Sonnet model not found${NC}"
        echo -e "${YELLOW}  You may need to request access in AWS Console${NC}"
        echo -e "${YELLOW}  Go to: AWS Console → Bedrock → Model access → Request access${NC}"
        echo ""
    else
        echo -e "${GREEN}✓ Bedrock access verified${NC}"
    fi
fi
echo ""

# Step 3: Check CDK bootstrap
if [ "$SKIP_BOOTSTRAP_CHECK" = false ]; then
    echo -e "${BOLD}${BLUE}[3/8] Checking CDK bootstrap status...${NC}"
    
    BOOTSTRAP_STACK=$(aws cloudformation describe-stacks \
        --stack-name CDKToolkit \
        --region ${AWS_REGION} 2>&1 || echo "NOT_FOUND")
    
    if [[ "$BOOTSTRAP_STACK" == *"NOT_FOUND"* ]] || [[ "$BOOTSTRAP_STACK" == *"does not exist"* ]]; then
        echo -e "${YELLOW}⚠ CDK not bootstrapped in this account/region${NC}"
        echo -e "${BLUE}Bootstrapping CDK...${NC}"
        
        cdk bootstrap aws://${AWS_ACCOUNT}/${AWS_REGION}
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ CDK bootstrap complete${NC}"
        else
            echo -e "${RED}✗ CDK bootstrap failed${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ CDK already bootstrapped${NC}"
    fi
else
    echo -e "${BLUE}[3/8] Skipping CDK bootstrap check${NC}"
fi
echo ""

# Step 4: Install dependencies
echo -e "${BOLD}${BLUE}[4/8] Installing dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi
echo ""

# Step 5: Build TypeScript
echo -e "${BOLD}${BLUE}[5/8] Building TypeScript...${NC}"
npm run build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ TypeScript build successful${NC}"
else
    echo -e "${RED}✗ TypeScript build failed${NC}"
    exit 1
fi
echo ""

# Step 6: Deploy CDK stack
echo -e "${BOLD}${BLUE}[6/8] Deploying CDK stack...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes...${NC}"
echo ""

export CDK_DEFAULT_ACCOUNT=${AWS_ACCOUNT}
export CDK_DEFAULT_REGION=${AWS_REGION}
export STAGE=${STAGE}
export BEDROCK_MODEL=${BEDROCK_MODEL}

# Determine stack name based on stage
if [ "$STAGE" = "dev" ]; then
    CHECK_STACK_NAME="CommandCenterBackend-Dev"
elif [ "$STAGE" = "staging" ]; then
    CHECK_STACK_NAME="CommandCenterBackend-Staging"
elif [ "$STAGE" = "prod" ]; then
    CHECK_STACK_NAME="CommandCenterBackend-Prod"
fi

# Check if stack already exists
STACK_EXISTS=$(aws cloudformation describe-stacks \
    --stack-name ${CHECK_STACK_NAME} \
    --region ${AWS_REGION} 2>&1 || echo "NOT_FOUND")

if [[ "$STACK_EXISTS" != *"NOT_FOUND"* ]]; then
    echo -e "${YELLOW}⚠ Stack already exists. This will update existing resources.${NC}"
    echo -e "${BLUE}Checking for potential conflicts...${NC}"
    
    # Check if stack is in a stable state
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name ${CHECK_STACK_NAME} \
        --region ${AWS_REGION} \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null)
    
    if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
        echo -e "${RED}✗ Stack is currently being updated. Please wait for it to complete.${NC}"
        echo -e "  Current status: ${STACK_STATUS}"
        echo ""
        echo "Monitor progress with:"
        echo "  aws cloudformation describe-stacks --stack-name CommandCenterBackendStack"
        exit 1
    fi
    
    if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" ]] || [[ "$STACK_STATUS" == "ROLLBACK_FAILED"* ]]; then
        echo -e "${RED}✗ Stack is in a failed state: ${STACK_STATUS}${NC}"
        echo -e "${YELLOW}You need to delete the stack first:${NC}"
        echo "  cdk destroy"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Stack is in a stable state: ${STACK_STATUS}${NC}"
fi

# Deploy with progress monitoring
cdk deploy --require-approval never &
CDK_PID=$!

# Wait for deployment to complete
echo ""
echo -e "${BLUE}Monitoring deployment progress...${NC}"
echo -e "${YELLOW}(This may take 5-10 minutes)${NC}"
echo ""

# Monitor CloudFormation stack status
LAST_STATUS=""
DOTS=0
while kill -0 $CDK_PID 2>/dev/null; do
    CURRENT_STATUS=$(aws cloudformation describe-stacks \
        --stack-name ${CHECK_STACK_NAME} \
        --region ${AWS_REGION} \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "CREATING")
    
    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        if [ ! -z "$LAST_STATUS" ]; then
            echo ""
        fi
        echo -e "${CYAN}Status: ${CURRENT_STATUS}${NC}"
        LAST_STATUS=$CURRENT_STATUS
        DOTS=0
    else
        echo -n "."
        DOTS=$((DOTS + 1))
        if [ $DOTS -ge 60 ]; then
            echo ""
            DOTS=0
        fi
    fi
    
    sleep 5
done

# Wait for the CDK process to finish
wait $CDK_PID
CDK_EXIT_CODE=$?

echo ""
if [ $CDK_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Stack deployed successfully${NC}"
else
    echo -e "${RED}✗ Stack deployment failed${NC}"
    echo ""
    echo "Check CloudFormation events for details:"
    echo "  aws cloudformation describe-stack-events --stack-name CommandCenterBackendStack --max-items 10"
    exit 1
fi
echo ""

# Step 7: Retrieve and display stack outputs
echo -e "${BOLD}${BLUE}[7/8] Retrieving deployment information...${NC}"
# Use the actual stack name from config (CommandCenterBackend-Dev, not CommandCenterBackendStack)
STACK_NAME="CommandCenterBackend-${STAGE^}"  # Capitalize first letter of stage
if [ "$STAGE" = "dev" ]; then
    STACK_NAME="CommandCenterBackend-Dev"
elif [ "$STAGE" = "staging" ]; then
    STACK_NAME="CommandCenterBackend-Staging"
elif [ "$STAGE" = "prod" ]; then
    STACK_NAME="CommandCenterBackend-Prod"
fi

OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${AWS_REGION} \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Stack outputs retrieved${NC}"
    echo ""
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    DEPLOYMENT OUTPUTS                      ${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Extract and display key outputs (try both naming conventions)
    API_ENDPOINT=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="APIEndpoint" or .OutputKey=="ApiEndpoint") | .OutputValue // empty')
    API_KEY_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="APIKeyId" or .OutputKey=="ApiKeyId") | .OutputValue // empty')
    TABLE_NAME=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="TableName") | .OutputValue // empty')
    AGENT_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="BedrockAgentId" or .OutputKey=="AgentId") | .OutputValue // empty')
    AGENT_ALIAS_ID=$(echo "${OUTPUTS}" | jq -r '.[] | select(.OutputKey=="BedrockAgentAliasId" or .OutputKey=="AgentAliasId") | .OutputValue // empty')
    
    if [ ! -z "$API_ENDPOINT" ]; then
        echo -e "${YELLOW}API Endpoint:${NC}"
        echo -e "  ${API_ENDPOINT}"
        echo ""
    fi
    
    if [ ! -z "$API_KEY_ID" ]; then
        echo -e "${YELLOW}API Key ID:${NC}"
        echo -e "  ${API_KEY_ID}"
        echo ""
        
        # Try to retrieve the actual API key value
        echo -e "${BLUE}Retrieving API Key value...${NC}"
        API_KEY_VALUE=$(aws apigateway get-api-key \
            --api-key ${API_KEY_ID} \
            --include-value \
            --query 'value' \
            --output text 2>/dev/null || echo "")
        
        if [ ! -z "$API_KEY_VALUE" ]; then
            echo -e "${YELLOW}API Key Value:${NC}"
            echo -e "  ${API_KEY_VALUE}"
            echo ""
            
            # Save to .env.local for easy access
            if [ -f ".env.local" ]; then
                # Update existing file
                if grep -q "^API_KEY=" .env.local; then
                    sed -i.bak "s|^API_KEY=.*|API_KEY=${API_KEY_VALUE}|" .env.local
                else
                    echo "API_KEY=${API_KEY_VALUE}" >> .env.local
                fi
                
                if grep -q "^API_ENDPOINT=" .env.local; then
                    sed -i.bak "s|^API_ENDPOINT=.*|API_ENDPOINT=${API_ENDPOINT}|" .env.local
                else
                    echo "API_ENDPOINT=${API_ENDPOINT}" >> .env.local
                fi
                rm -f .env.local.bak
            else
                # Create new file
                cat > .env.local << EOF
# Auto-generated by deployment script
API_ENDPOINT=${API_ENDPOINT}
API_KEY=${API_KEY_VALUE}
TABLE_NAME=${TABLE_NAME}
AGENT_ID=${AGENT_ID}
AGENT_ALIAS_ID=${AGENT_ALIAS_ID}
AWS_REGION=${AWS_REGION}
EOF
            fi
            echo -e "${GREEN}✓ API credentials saved to .env.local${NC}"
            echo ""
        fi
    fi
    
    if [ ! -z "$TABLE_NAME" ]; then
        echo -e "${YELLOW}DynamoDB Table:${NC}"
        echo -e "  ${TABLE_NAME}"
        echo ""
    fi
    
    if [ ! -z "$AGENT_ID" ]; then
        echo -e "${YELLOW}Bedrock Agent ID:${NC}"
        echo -e "  ${AGENT_ID}"
        echo ""
    fi
    
    if [ ! -z "$AGENT_ALIAS_ID" ]; then
        echo -e "${YELLOW}Bedrock Agent Alias ID:${NC}"
        echo -e "  ${AGENT_ALIAS_ID}"
        echo ""
    fi
    
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Could not retrieve stack outputs${NC}"
    TABLE_NAME="MasterEventTimeline"  # Default fallback
fi
echo ""

# Step 8: Populate database
if [ "$SKIP_POPULATE" = false ]; then
    echo -e "${BOLD}${BLUE}[8/8] Populating database with simulation data...${NC}"
    echo -e "${YELLOW}This may take 2-3 minutes...${NC}"
    echo ""
    
    export TABLE_NAME=${TABLE_NAME}
    
    npm run populate-db
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Database populated successfully${NC}"
        
        # Verify data
        ITEM_COUNT=$(aws dynamodb scan \
            --table-name ${TABLE_NAME} \
            --select COUNT \
            --region ${AWS_REGION} \
            --output json 2>/dev/null | jq -r '.Count // 0')
        
        echo -e "  Total items in database: ${ITEM_COUNT}"
    else
        echo -e "${YELLOW}⚠ Database population had issues (check logs above)${NC}"
    fi
else
    echo -e "${BLUE}[8/8] Skipping database population${NC}"
    echo ""
    echo -e "${YELLOW}To populate the database later, run:${NC}"
    echo -e "  npm run populate-db"
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
if [ ! -z "$API_ENDPOINT" ] && [ ! -z "$API_KEY_VALUE" ]; then
    echo -e "   ${BLUE}curl -X GET \"${API_ENDPOINT}/data/updates?since=2023-02-06T00:00:00Z\" \\${NC}"
    echo -e "   ${BLUE}     -H \"x-api-key: ${API_KEY_VALUE}\"${NC}"
else
    echo -e "   npm run test:integration"
fi
echo ""

echo -e "2. ${CYAN}Configure frontend:${NC}"
echo -e "   Update your frontend .env.local with:"
if [ ! -z "$API_ENDPOINT" ]; then
    echo -e "   ${BLUE}NEXT_PUBLIC_API_ENDPOINT=${API_ENDPOINT}${NC}"
fi
if [ ! -z "$API_KEY_VALUE" ]; then
    echo -e "   ${BLUE}NEXT_PUBLIC_API_KEY=${API_KEY_VALUE}${NC}"
fi
echo ""

echo -e "3. ${CYAN}View CloudWatch logs:${NC}"
echo -e "   aws logs tail /aws/lambda/queryHandlerLambda --follow"
echo ""

echo -e "4. ${CYAN}Monitor costs:${NC}"
echo -e "   AWS Console → CloudWatch → Dashboards"
echo ""

echo -e "${BOLD}${YELLOW}Important Files:${NC}"
echo -e "  ${CYAN}.env.local${NC}         - API credentials (DO NOT commit to git)"
echo -e "  ${CYAN}API_DOCUMENTATION.md${NC} - API usage guide"
echo -e "  ${CYAN}DEPLOYMENT_GUIDE.md${NC}  - Detailed deployment documentation"
echo ""

echo -e "${BOLD}${YELLOW}Useful Commands:${NC}"
echo -e "  ${CYAN}npm run test:integration${NC}  - Run integration tests"
echo -e "  ${CYAN}cdk diff${NC}                  - Preview changes before deploy"
echo -e "  ${CYAN}cdk destroy${NC}               - Remove all resources"
echo ""

echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
