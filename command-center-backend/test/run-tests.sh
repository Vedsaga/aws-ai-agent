#!/bin/bash

# Command Center Backend - Test Runner
# Runs unit tests and optionally E2E tests

set -e

echo "========================================"
echo "Command Center Backend - Test Suite"
echo "========================================"
echo ""

# Colors
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Must run from command-center-backend directory${NC}"
    exit 1
fi

# Build the project first
echo "Building project..."
npm run build
if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}Build successful${NC}"
echo ""

# Run unit tests
echo "Running unit tests..."
ts-node test/unit.test.ts
UNIT_TEST_RESULT=$?

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Unit tests passed${NC}"
else
    echo -e "${RED}Unit tests failed${NC}"
fi
echo ""

# Check if E2E tests should be run
if [ "$1" == "--e2e" ] || [ "$1" == "-e" ]; then
    echo "Running E2E tests..."
    
    # Check for required environment variables
    if [ -z "$API_ENDPOINT" ]; then
        echo -e "${YELLOW}Warning: API_ENDPOINT not set${NC}"
        echo "Usage: API_ENDPOINT=https://xxx.execute-api.region.amazonaws.com/prod API_KEY=xxx ./test/run-tests.sh --e2e"
        echo "Skipping E2E tests"
    elif [ -z "$API_KEY" ]; then
        echo -e "${YELLOW}Warning: API_KEY not set${NC}"
        echo "Usage: API_ENDPOINT=https://xxx.execute-api.region.amazonaws.com/prod API_KEY=xxx ./test/run-tests.sh --e2e"
        echo "Skipping E2E tests"
    else
        ts-node test/e2e.test.ts
        E2E_TEST_RESULT=$?
        
        if [ $E2E_TEST_RESULT -eq 0 ]; then
            echo -e "${GREEN}E2E tests passed${NC}"
        else
            echo -e "${RED}E2E tests failed${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}Skipping E2E tests (use --e2e flag to run)${NC}"
fi

echo ""
echo "========================================"
echo "Test Suite Complete"
echo "========================================"

exit $UNIT_TEST_RESULT
