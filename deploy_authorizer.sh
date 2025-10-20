#!/bin/bash
# Deploy authorizer with dependencies

set -e

echo "Deploying authorizer Lambda..."

# Create temp directory
TEMP_DIR="/tmp/authorizer_deploy"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy authorizer code
cp infrastructure/lambda/authorizer/authorizer.py "$TEMP_DIR/"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r infrastructure/lambda/authorizer/requirements.txt -t "$TEMP_DIR" --quiet

# Create zip
cd "$TEMP_DIR"
zip -r deployment.zip . > /dev/null

# Deploy
echo "Uploading to Lambda..."
aws lambda update-function-code \
    --function-name MultiAgentOrchestration-dev-Auth-Authorizer \
    --zip-file fileb://deployment.zip \
    --no-cli-pager

echo "✅ Authorizer deployed successfully!"
