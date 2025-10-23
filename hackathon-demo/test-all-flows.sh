
API_URL='https://tzbw0aw913.execute-api.us-east-1.amazonaws.com/prod/'

echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo '🧪 TESTING ALL 3 FLOWS'
echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo ''

# Test 1: Ingestion
echo '1️⃣  INGESTION FLOW'
echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo 'Request: Broken fire hydrant at 789 Park Avenue, water everywhere'
echo ''
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate"   -H 'Content-Type: application/json'   -d '{
    "mode": "ingestion",
    "message": "Broken fire hydrant at 789 Park Avenue, water everywhere",
    "session_id": "demo-ingest"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Status:', data.get('mode'))
result = data.get('result', {})
if result.get('needs_clarification'):
    print('⚠️  Needs Clarification:', result.get('question'))
elif result.get('report_id'):
    print('✅ Report Created!')
    print('   ID:', result['report_id'])
    print('   Location:', result.get('data', {}).get('location'))
    print('   Entity:', result.get('data', {}).get('entity'))
    print('   Severity:', result.get('data', {}).get('severity'))
    print('   Confidence:', result.get('data', {}).get('confidence'))
    
    # Save report ID for management test
    with open('.test_report_id', 'w') as f:
        f.write(result['report_id'])
    
    # Show agent execution
    if result.get('agent_response'):
        import json
        agents = json.loads(result['agent_response'])
        print('')
        print('🤖 Agent Execution:')
        for agent, output in agents.items():
            conf = output.get('confidence', 0)
            print(f'   {agent}: {int(conf*100)}% confidence')
else:
    print(json.dumps(data, indent=2))
" 2>/dev/null || echo "$RESPONSE"

echo ''
echo ''

# Test 2: Query
echo '2️⃣  QUERY FLOW'
echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo 'Request: Show me all reports with high or critical severity'
echo ''
RESPONSE=$(curl -s -X POST "${API_URL}orchestrate"   -H 'Content-Type: application/json'   -d '{
    "mode": "query",
    "message": "Show me all reports with high or critical severity",
    "session_id": "demo-query"
  }')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
results = result.get('results', [])
print(f'✅ Found {len(results)} reports')
print('')
for i, r in enumerate(results[:5], 1):
    print(f'{i}. {r.get("entity", "N/A")[:60]}')
    print(f'   Location: {r.get("location", "N/A")}')
    print(f'   Severity: {r.get("severity", "N/A")}')
    if r.get('status'):
        print(f'   Status: {r["status"]}')
    print('')

if result.get('summary'):
    summary = result['summary'][:200]
    print('📊 AI Summary:')
    print(f'   {summary}...')
    
print('')
print('🗺️  Map Data:')
map_data = result.get('map_data', {})
features = map_data.get('features', [])
print(f'   {len(features)} locations on map')
" 2>/dev/null || echo "$RESPONSE"

echo ''
echo ''

# Test 3: Management
if [ -f .test_report_id ]; then
    REPORT_ID=$(cat .test_report_id)
    echo '3️⃣  MANAGEMENT FLOW'
    echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    echo "Request: Assign report $REPORT_ID to Team C and mark as in progress"
    echo ''
    RESPONSE=$(curl -s -X POST "${API_URL}orchestrate"       -H 'Content-Type: application/json'       -d "{
        \"mode\": \"management\",
        \"message\": \"Assign report $REPORT_ID to Team C and mark as in progress\",
        \"session_id\": \"demo-manage\"
      }")
    
    echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('result', {})
if result.get('confirmation'):
    print('✅', result['confirmation'])
if result.get('updates'):
    print('')
    print('📝 Updates Applied:')
    for key, value in result['updates'].items():
        print(f'   {key}: {value}')
if result.get('error'):
    print('❌ Error:', result['error'])
" 2>/dev/null || echo "$RESPONSE"
    
    rm -f .test_report_id
else
    echo '3️⃣  MANAGEMENT FLOW'
    echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    echo '⚠️  Skipped (no report ID from ingestion test)'
fi

echo ''
echo ''
echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
echo '✅ ALL TESTS COMPLETE'
echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
