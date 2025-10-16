#!/bin/bash

# Prepare Lambda deployment bundle with all dependencies

set -e

echo "🔧 Preparing Lambda deployment bundle..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist lambda-bundle

# Build TypeScript
echo "📦 Building TypeScript..."
npm run build

# Create bundle directory with compiled code
echo "📦 Creating bundle directory..."
mkdir -p lambda-bundle
cp -r dist/* lambda-bundle/

# Copy package files
cp package.json lambda-bundle/
cp package-lock.json lambda-bundle/ 2>/dev/null || true

# Install production dependencies in bundle
echo "📦 Installing production dependencies..."
cd lambda-bundle
npm install --production --no-optional --ignore-scripts

# Clean up unnecessary files to reduce size
echo "🧹 Optimizing bundle size..."
find node_modules -name "*.md" -type f -delete 2>/dev/null || true
find node_modules -name "*.ts" -type f -delete 2>/dev/null || true
find node_modules -name "*.map" -type f -delete 2>/dev/null || true
find node_modules -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "*.test.js" -type f -delete 2>/dev/null || true
find node_modules -name "*.spec.js" -type f -delete 2>/dev/null || true
find node_modules -name "examples" -type d -exec rm -rf {} + 2>/dev/null || true
find node_modules -name "docs" -type d -exec rm -rf {} + 2>/dev/null || true

cd ..

echo "✅ Bundle prepared successfully!"
echo "📊 Bundle size:"
du -sh lambda-bundle

echo ""
echo "✅ Ready for deployment!"
echo "Run: npm run deploy"
