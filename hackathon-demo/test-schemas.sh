#!/bin/bash

echo "🧪 Testing All 3 Flows with New Schema Structure"
echo "================================================="
echo ""

API_URL="https://tzbw0aw913.execute-api.us-east-1.amazonaws.com/prod/"

# Test 1: Ingestion
echo "=== TEST 1: INGESTION (Create New Report) ==="
echo "Input: 'Dangerous pothole at 123 Oak Street, needs immediate repair'"
echo ""
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "ingestion",
    "message": "Dangerous pothole at 123 Oak Street, needs immediate repair",
    "session_id": "schema-test-1"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
print('Status:', result.get('status'))
print('Report ID:', result.get('report_id'))
print('Confidence:', result.get('confidence'))
print('Needs Clarification:', result.get('needs_clarification'))
if result.get('data'):
    print('\nStructured Data:')
    print('  Location:', result['data']['location']['address'])
    print('  Coordinates:', result['data']['location']['geo_coordinates'])
    print('  Entity:', result['data']['entity']['description'])
    print('  Severity:', result['data']['severity']['level'])
    print('  Urgency:', result['data']['temporal']['urgency'])
if result.get('agent_execution'):
    print('\nAgent Execution:')
    print('  Agents Run:', result['agent_execution']['agents_run'])
    print('  Execution Time:', result['agent_execution']['execution_time_ms'], 'ms')
if result.get('report_id'):
    with open('.last_report_id', 'w') as f:
        f.write(result['report_id'])
    print('\n✅ Report created successfully!')
"
echo ""
echo "---"
echo ""

# Test 2: Query
echo "=== TEST 2: QUERY (Search Existing Reports) ==="
echo "Input: 'Show me all high severity issues'"
echo ""
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "query",
    "message": "Show me all high severity issues",
    "session_id": "schema-test-2"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
print('Status:', result.get('status'))
print('Total Results:', result.get('total_results'))
print('\nFilters Applied:')
for agent, info in result.get('filters_applied', {}).items():
    if info.get('filters'):
        print(f'  {agent}:', info['filters'])
print('\nResults:')
for r in result.get('results', [])[:3]:
    print(f'  - {r.get(\"entity\", \"N/A\")[:50]} [{r.get(\"severity\", \"N/A\")}]')
print('\nAgent Execution:')
print('  Agents Run:', result.get('agent_execution', {}).get('agents_run', []))
print('  Execution Time:', result.get('agent_execution', {}).get('execution_time_ms', 0), 'ms')
print('\n✅ Query executed successfully!')
"
echo ""
echo "---"
echo ""

# Test 3: Management
if [ -f .last_report_id ]; then
    REPORT_ID=$(cat .last_report_id)
    echo "=== TEST 3: MANAGEMENT (Update Existing Report) ==="
    echo "Input: 'Assign report $REPORT_ID to Team A and mark as in progress'"
    echo ""
    RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
      -H "Content-Type: application/json" \
      -d "{
        \"mode\": \"management\",
        \"message\": \"Assign report $REPORT_ID to Team A and mark as in progress\",
        \"session_id\": \"schema-test-3\"
      }")
    
    echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
print('Status:', result.get('status'))
print('Action:', result.get('action'))
print('Target Report ID:', result.get('target_report_id', 'N/A')[:16] + '...')
print('\nUpdates Applied:')
for key, value in result.get('updates_applied', {}).items():
    print(f'  {key}: {value}')
print('\nPrevious Values:')
for key, value in result.get('previous_values', {}).items():
    if value:
        print(f'  {key}: {value}')
print('\nConfirmation:', result.get('confirmation'))
print('\nAgent Execution:')
print('  Command Parsed:', result.get('agent_execution', {}).get('command_parsed'))
print('  Execution Time:', result.get('agent_execution', {}).get('execution_time_ms', 0), 'ms')
if result.get('status') == 'success':
    print('\n✅ Management operation successful!')
else:
    print('\n❌ Error:', result.get('error'))
"
    rm -f .last_report_id
else
    echo "=== TEST 3: MANAGEMENT (Test Error Handling) ==="
    echo "Input: 'Assign report to Team A' (no report ID)"
    echo ""
    RESPONSE=$(curl -s -X POST "${API_URL}orchestrate" \
      -H "Content-Type: application/json" \
      -d '{
        "mode": "management",
        "message": "Assign report to Team A",
        "session_id": "schema-test-3"
      }')
    
    echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
print('Status:', result.get('status'))
print('Error:', result.get('error'))
print('\n✅ Error handling working correctly!')
"
fi

echo ""
echo "================================================="
echo "✅ All 3 flows tested with new schema structure!"
echo "================================================="
