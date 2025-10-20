#!/bin/bash

# Multi-Agent Orchestration System - API Test Runner
# This script runs the comprehensive API test suite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "Multi-Agent Orchestration System"
echo "API Test Suite Runner"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi

# Check if requests library is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}WARNING: 'requests' library not found${NC}"
    echo "Installing requests..."
    pip3 install requests
fi

# Check environment variables
if [ -z "$API_URL" ]; then
    echo -e "${RED}ERROR: API_URL environment variable is not set${NC}"
    echo ""
    echo "Usage:"
    echo "  export API_URL=https://your-api-url.com/"
    echo "  export JWT_TOKEN=your-jwt-token"
    echo "  ./run_tests.sh"
    echo ""
    exit 1
fi

if [ -z "$JWT_TOKEN" ]; then
    echo -e "${YELLOW}WARNING: JWT_TOKEN not set. Authentication tests will be skipped.${NC}"
    echo ""
fi

echo -e "${BLUE}API URL:${NC} $API_URL"
if [ -n "$JWT_TOKEN" ]; then
    echo -e "${BLUE}JWT Token:${NC} ${JWT_TOKEN:0:20}..."
fi
echo ""

# Run the test suite
echo -e "${GREEN}Running test suite...${NC}"
echo ""

python3 test_api.py

# Check exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✅ All tests passed!"
    echo "==========================================${NC}"
    echo ""
    echo "Test report saved to: TEST_REPORT.md"
else
    echo -e "${RED}=========================================="
    echo "❌ Some tests failed"
    echo "==========================================${NC}"
    echo ""
    echo "Check TEST_REPORT.md for details"
fi

echo ""
exit $EXIT_CODE
