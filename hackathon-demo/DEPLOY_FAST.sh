#!/bin/bash
set -e

echo "🚀 Fast Deploy - 5 Minutes"
echo "=========================="

# 1. Deploy backend
echo "1️⃣ Deploying backend..."
cd cdk
pip3 install -r requirements.txt -q
cdk bootstrap --require-approval never 2>/dev/null || true
cdk deploy --require-approval never --outputs-file outputs.json

API_URL=$(grep ApiEndpoint outputs.json | cut -d'"' -f4)
echo "✓ Backend deployed: $API_URL"

# 2. Setup frontend
echo ""
echo "2️⃣ Setting up frontend..."
cd ../frontend-react

# Update .env.local
sed -i "s|YOUR_API_URL_HERE|$API_URL|g" .env.local

echo "✓ Frontend configured"
echo ""
echo "=========================="
echo "✅ Backend Ready!"
echo "=========================="
echo ""
echo "API URL: $API_URL"
echo ""
echo "Next steps:"
echo "1. Get Mapbox token: https://account.mapbox.com/access-tokens/"
echo "2. Edit frontend-react/.env.local"
echo "3. Add your MAPBOX_TOKEN"
echo "4. Run: cd frontend-react && npm install && npm run dev"
echo ""
