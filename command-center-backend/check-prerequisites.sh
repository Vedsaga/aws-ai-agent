#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Command Center - Prerequisites Check              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

ALL_GOOD=true

# Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ $NODE_VERSION"
else
    echo "✗ NOT INSTALLED"
    ALL_GOOD=false
fi

# npm
echo -n "Checking npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ v$NPM_VERSION"
else
    echo "✗ NOT INSTALLED"
    ALL_GOOD=false
fi

# AWS CLI
echo -n "Checking AWS CLI... "
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
    echo "✓ $AWS_VERSION"
else
    echo "✗ NOT INSTALLED"
    ALL_GOOD=false
fi

# AWS Credentials
echo -n "Checking AWS Credentials... "
if aws sts get-caller-identity &> /dev/null; then
    echo "✓ CONFIGURED"
    echo ""
    echo "AWS Account Details:"
    aws sts get-caller-identity | grep -E "UserId|Account|Arn" | sed 's/^/  /'
else
    echo "✗ NOT CONFIGURED"
    ALL_GOOD=false
fi

echo ""

# CDK
echo -n "Checking AWS CDK... "
if command -v cdk &> /dev/null; then
    CDK_VERSION=$(cdk --version 2>&1)
    echo "✓ $CDK_VERSION"
else
    echo "✗ NOT INSTALLED"
    echo ""
    echo "Install with: npm install -g aws-cdk"
    ALL_GOOD=false
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

if [ "$ALL_GOOD" = true ]; then
    echo "✓ All prerequisites met! You're ready to deploy."
    echo ""
    echo "Next steps:"
    echo "  1. Request Bedrock Claude 3 Sonnet access (AWS Console)"
    echo "     → https://console.aws.amazon.com/bedrock/"
    echo "     → Model access → Request access to Claude 3 Sonnet"
    echo ""
    echo "  2. Run deployment:"
    echo "     bash scripts/full-deploy.sh"
else
    echo "✗ Some prerequisites are missing."
    echo ""
    echo "Please install missing components and run this script again."
    echo "See PRE_DEPLOYMENT_CHECKLIST.md for installation instructions."
fi

echo ""
