#!/bin/bash

echo "🧪 Testing Backend API - All 3 Flows"
echo "====================================="
echo ""

# Load API URL from .env
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found. Run deploy-backend.sh first."
    exit 1
fi

if [ -z "$API_URL" ]; then
    echo "❌ API_URL not set in .env"
    exit 1
fi

echo "API URL: $API_URL"
echo ""

# Test 1: Report ingestion
echo "=== Test 1: Ingestion ==="
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "ingestion",
    "message": "Graffiti on Main Street wall, needs cleanup",
    "session_id": "test-1"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data, indent=2))
if 'result' in data and 'report_id' in data['result']:
    print('\n✅ Report created:', data['result']['report_id'])
    with open('.last_report_id', 'w') as f:
        f.write(data['result']['report_id'])
" 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 2: Query
echo "=== Test 2: Query ==="
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "query",
    "message": "Show me all reports",
    "session_id": "test-2"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'result' in data and 'results' in data['result']:
    print(f\"Found {len(data['result']['results'])} reports\")
    for r in data['result']['results'][:3]:
        print(f\"  - {r.get('entity', 'N/A')[:50]} [{r.get('severity', 'N/A')}]\")
    if 'summary' in data['result']:
        print(f'\nSummary: {data['result']['summary'][:200]}...')
else:
    print(json.dumps(data, indent=2))
" 2>/dev/null || echo "$RESPONSE"
echo ""

# Test 3: Management
if [ -f .last_report_id ]; then
    REPORT_ID=$(cat .last_report_id)
    echo "=== Test 3: Management ==="
    RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
      -H "Content-Type: application/json" \
      -d "{
        \"mode\": \"management\",
        \"message\": \"Assign report $REPORT_ID to Team A\",
        \"session_id\": \"test-3\"
      }")
    
    echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'result' in data:
    result = data['result']
    if 'confirmation' in result:
        print('✅', result['confirmation'])
    if 'updates' in result:
        print('Updates applied:', json.dumps(result['updates'], indent=2))
    if 'error' in result:
        print('❌ Error:', result['error'])
else:
    print(json.dumps(data, indent=2))
" 2>/dev/null || echo "$RESPONSE"
    rm -f .last_report_id
else
    echo "=== Test 3: Management ==="
    echo "⚠️  Skipped (no report ID from Test 1)"
fi

echo ""
echo "✅ All tests complete!"
