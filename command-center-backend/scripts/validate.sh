#!/bin/bash

# Validation script for Command Center Backend setup

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Validating Command Center Backend Setup ===${NC}"
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js installed: ${NODE_VERSION}${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm installed: ${NPM_VERSION}${NC}"
else
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi

# Check AWS CLI
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version)
    echo -e "${GREEN}✓ AWS CLI installed: ${AWS_VERSION}${NC}"
else
    echo -e "${RED}✗ AWS CLI not found${NC}"
    exit 1
fi

# Check CDK CLI
if command -v cdk &> /dev/null; then
    CDK_VERSION=$(cdk --version)
    echo -e "${GREEN}✓ AWS CDK installed: ${CDK_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠ AWS CDK not found globally. Install with: npm install -g aws-cdk${NC}"
fi

# Check AWS credentials
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✓ AWS credentials configured (Account: ${ACCOUNT_ID})${NC}"
else
    echo -e "${RED}✗ AWS credentials not configured or invalid${NC}"
    exit 1
fi

# Check if dependencies are installed
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✓ Node modules installed${NC}"
else
    echo -e "${YELLOW}⚠ Node modules not installed. Run: npm install${NC}"
fi

# Check TypeScript compilation
if npm run build &> /dev/null; then
    echo -e "${GREEN}✓ TypeScript compilation successful${NC}"
else
    echo -e "${RED}✗ TypeScript compilation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Validation Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Review environment configuration in config/environment.ts"
echo "  2. Set STAGE environment variable (dev/staging/prod)"
echo "  3. Run: npm run deploy"
