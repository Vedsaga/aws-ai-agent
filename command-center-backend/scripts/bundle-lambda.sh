#!/bin/bash

# Bundle Lambda functions with dependencies for deployment

set -e

echo "🔧 Bundling Lambda functions with dependencies..."

# Create bundle directory
BUNDLE_DIR="lambda-bundle"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Copy compiled Lambda code
echo "📦 Copying compiled code..."
cp -r lib "$BUNDLE_DIR/"

# Install production dependencies only
echo "📦 Installing production dependencies..."
cd "$BUNDLE_DIR"
cp ../package.json .
cp ../package-lock.json . 2>/dev/null || true

# Install only production dependencies
npm install --production --no-optional

# Remove unnecessary files to reduce package size
echo "🧹 Cleaning up..."
find node_modules -name "*.md" -delete
find node_modules -name "*.ts" -delete
find node_modules -name "*.map" -delete
find node_modules -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "*.test.js" -delete
find node_modules -name "*.spec.js" -delete

cd ..

echo "✅ Bundle created in $BUNDLE_DIR/"
echo "📊 Bundle size:"
du -sh "$BUNDLE_DIR"

echo ""
echo "Next steps:"
echo "1. Update CDK stack to use lambda-bundle directory"
echo "2. Run: npm run deploy"
