#!/bin/bash
set -e

echo "=== Command Center Backend Deployment ==="
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
aws sts get-caller-identity

echo ""
echo "Installing dependencies..."
npm install

echo ""
echo "Building TypeScript..."
npm run build

echo ""
echo "Deploying to AWS..."
npm run deploy -- --require-approval never

echo ""
echo "Deployment complete!"
echo ""
echo "Next: Populate database with 'npm run populate-db'"
