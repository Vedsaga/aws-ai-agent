#!/bin/bash

# End-to-end test runner script
# Usage: ./scripts/run-e2e-tests.sh [--endpoint URL] [--api-key KEY]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_ENDPOINT=""
API_KEY=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --endpoint)
            API_ENDPOINT="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--endpoint URL] [--api-key KEY]"
            echo ""
            echo "Options:"
            echo "  --endpoint    API endpoint URL (auto-detected if not provided)"
            echo "  --api-key     API key for authentication (optional)"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== End-to-End Test Runner ===${NC}"
echo ""

# Auto-detect API endpoint if not provided
if [ -z "$API_ENDPOINT" ]; then
    echo -e "${BLUE}Auto-detecting API endpoint from CloudFormation stack...${NC}"
    STACK_NAME="CommandCenterBackendStack"
    API_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -z "$API_ENDPOINT" ]; then
        echo -e "${RED}Error: Could not auto-detect API endpoint${NC}"
        echo "Please specify endpoint with --endpoint option"
        exit 1
    fi
    echo -e "${GREEN}✓ Detected endpoint: ${API_ENDPOINT}${NC}"
fi

# Export environment variables
export API_ENDPOINT
export API_KEY

echo ""
echo -e "${BLUE}Building TypeScript...${NC}"
npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: TypeScript build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo ""

# Check if axios is installed
if ! npm list axios &> /dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    npm install --save-dev axios @types/axios
fi

echo -e "${BLUE}Running end-to-end tests...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"
echo ""

# Run the test suite
node dist/test/e2e.test.js

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== All E2E Tests Passed ===${NC}"
else
    echo ""
    echo -e "${RED}=== Some E2E Tests Failed ===${NC}"
fi

exit $TEST_EXIT_CODE
