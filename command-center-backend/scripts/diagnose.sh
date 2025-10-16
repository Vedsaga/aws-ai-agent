#!/bin/bash

echo "=== Diagnostic Script ==="
echo ""

# 1. Check database
echo "[1] Checking database..."
COUNT=$(aws dynamodb scan --table-name CommandCenterBackend-Dev-MasterEventTimeline --select COUNT --output json 2>/dev/null | jq -r '.Count // 0')
echo "Database items: $COUNT"
if [ "$COUNT" = "0" ]; then
    echo "❌ Database is empty! Run: npm run populate-db"
fi
echo ""

# 2. Check Lambda function
echo "[2] Checking Lambda function..."
aws lambda get-function --function-name CommandCenterBackend-Dev-UpdatesHandler --query 'Configuration.[FunctionName,State,LastUpdateStatus]' --output table 2>/dev/null || echo "❌ Lambda not found"
echo ""

# 3. Check recent logs
echo "[3] Checking recent Lambda logs..."
aws logs filter-log-events \
  --log-group-name /aws/lambda/CommandCenterBackend-Dev-UpdatesHandler \
  --start-time $(($(date +%s) * 1000 - 600000)) \
  --filter-pattern "ERROR" \
  --query 'events[*].message' \
  --output text 2>/dev/null | head -10 || echo "No recent errors"
echo ""

# 4. Test API
echo "[4] Testing API..."
source .env.local 2>/dev/null
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${API_ENDPOINT}data/updates?since=2023-02-06T00:00:00Z" -H "x-api-key: ${API_KEY}" 2>&1)
STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')
echo "Status: $STATUS"
echo "Response: ${BODY:0:200}"
echo ""

# 5. Check API Gateway
echo "[5] Checking API Gateway..."
aws apigateway get-rest-apis --query "items[?name=='CommandCenterBackend-Dev-API'].id" --output text 2>/dev/null || echo "❌ API Gateway not found"
echo ""

echo "=== Diagnostic Complete ==="
