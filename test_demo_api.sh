#!/bin/bash

# Test script for local demo API

echo "=========================================="
echo "Testing Local Demo API"
echo "=========================================="
echo ""

API_URL="http://localhost:8000"

# Check if server is running
echo "1. Health Check..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

# Test Config API - List Agents
echo "2. List Agents..."
curl -s "$API_URL/api/v1/config?type=agent" | python3 -m json.tool | head -30
echo ""

# Test Config API - Create Agent
echo "3. Create Custom Agent..."
curl -s -X POST "$API_URL/api/v1/config" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "agent",
    "config": {
      "agent_name": "Test Custom Agent",
      "agent_type": "custom",
      "system_prompt": "You are a test agent for demo",
      "tools": ["bedrock"],
      "output_schema": {
        "result": "string",
        "confidence": "number"
      }
    }
  }' | python3 -m json.tool
echo ""

# Test Ingest API
echo "4. Submit Report..."
curl -s -X POST "$API_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "text": "There is a broken streetlight on Main Street near the library"
  }' | python3 -m json.tool
echo ""

# Test Query API
echo "5. Ask Question..."
curl -s -X POST "$API_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "civic_complaints",
    "question": "What are the most common complaints this month?"
  }' | python3 -m json.tool
echo ""

# Test Data API
echo "6. Retrieve Incidents..."
curl -s "$API_URL/api/v1/data?type=retrieval" | python3 -m json.tool
echo ""

# Test Tools API
echo "7. List Tools..."
curl -s "$API_URL/api/v1/tools" | python3 -m json.tool
echo ""

echo "=========================================="
echo "✓ All tests complete!"
echo "=========================================="
