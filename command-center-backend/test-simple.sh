#!/bin/bash

# Load environment variables
source .env.local

echo "Testing POST /agent/query..."
curl -X POST "${API_ENDPOINT}agent/query" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{"text":"Hello"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  2>&1

echo ""
echo "Done!"
