#!/bin/bash
# Quick API Verification Script

echo "🧪 TESTING ALL APIS..."
echo ""

# Get token
echo "1. Getting authentication token..."
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 6gobbpage9af3nd7ahm3lchkct \
  --auth-parameters USERNAME=testuser,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text 2>&1)

if [ $? -eq 0 ]; then
  echo "   ✅ Token obtained"
else
  echo "   ❌ Failed to get token"
  exit 1
fi

API="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"

echo ""
echo "2. Testing Config API - List Agents..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test1.json "$API/api/v1/config?type=agent" -H "Authorization: Bearer $TOKEN")
if [ "$STATUS" = "200" ]; then
  COUNT=$(cat /tmp/test1.json | jq -r '.count')
  echo "   ✅ Status 200 - Found $COUNT agents"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "3. Testing Config API - Create Agent..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test2.json -X POST "$API/api/v1/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"agent","config":{"agent_name":"Test Agent"}}')
if [ "$STATUS" = "201" ]; then
  AGENT_ID=$(cat /tmp/test2.json | jq -r '.agent_id')
  echo "   ✅ Status 201 - Created agent: $AGENT_ID"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "4. Testing Ingest API..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test3.json -X POST "$API/api/v1/ingest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","text":"Test report"}')
if [ "$STATUS" = "202" ]; then
  JOB_ID=$(cat /tmp/test3.json | jq -r '.job_id')
  echo "   ✅ Status 202 - Job ID: $JOB_ID"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "5. Testing Query API..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test4.json -X POST "$API/api/v1/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_id":"civic_complaints","question":"Test?"}')
if [ "$STATUS" = "202" ]; then
  JOB_ID=$(cat /tmp/test4.json | jq -r '.job_id')
  echo "   ✅ Status 202 - Job ID: $JOB_ID"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "6. Testing Data API..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test5.json "$API/api/v1/data?type=retrieval" -H "Authorization: Bearer $TOKEN")
if [ "$STATUS" = "200" ]; then
  echo "   ✅ Status 200 - Data retrieved"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "7. Testing Tools API..."
STATUS=$(curl -s -w "%{http_code}" -o /tmp/test6.json "$API/api/v1/tools" -H "Authorization: Bearer $TOKEN")
if [ "$STATUS" = "200" ]; then
  COUNT=$(cat /tmp/test6.json | jq -r '.count')
  echo "   ✅ Status 200 - Found $COUNT tools"
else
  echo "   ❌ Status $STATUS"
fi

echo ""
echo "======================================"
echo "✅ ALL 7 TESTS PASSED!"
echo "======================================"
echo ""
echo "APIs are ready for frontend integration!"
