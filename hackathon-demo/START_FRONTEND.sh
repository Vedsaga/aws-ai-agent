#!/bin/bash

echo "🚀 Starting Frontend"
echo "===================="
echo ""

cd "$(dirname "$0")/frontend-react"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Check if Mapbox token is set
if grep -q "YOUR_MAPBOX_TOKEN_HERE" .env.local; then
    echo "⚠️  WARNING: Mapbox token not configured!"
    echo ""
    echo "To enable the map:"
    echo "1. Get a free token at https://account.mapbox.com/access-tokens/"
    echo "2. Edit frontend-react/.env.local"
    echo "3. Replace YOUR_MAPBOX_TOKEN_HERE with your token"
    echo ""
    echo "The app will work without it, but the map won't display."
    echo ""
fi

echo "Starting development server..."
echo "Open http://localhost:3000 in your browser"
echo ""

npm run dev
