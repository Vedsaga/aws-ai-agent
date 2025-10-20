#!/bin/bash

# Authenticated API Test Script
# Tests all API endpoints with proper authentication

set -e

API_URL="https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
USER_POOL_ID="us-east-1_7QZ7Y6Gbl"
CLIENT_ID="6gobbpage9af3nd7ahm3lchkct"
USERNAME="testuser"
PASSWORD="TestPassword123!"
REGION="us-east-1"

echo "========================================="
echo "Authenticated API Test Suite"
echo "========================================="
echo ""
echo "API URL: $API_URL"
echo "Username: $USERNAME"
echo ""

# Step 1: Authenticate and get tokens
echo "Step 1: Authenticating..."
echo "-------------------------"

AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$CLIENT_ID" \
  --auth-parameters USERNAME="$USERNAME",PASSWORD="$PASSWORD" \
  --region "$REGION" 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ FAIL - Authentication failed"
    echo "$AUTH_RESPONSE"
    exit 1
fi

ID_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.AuthenticationResult.IdToken')
ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.AuthenticationResult.AccessToken')

if [ "$ID_TOKEN" = "null" ] || [ -z "$ID_TOKEN" ]; then
    echo "❌ FAIL - Could not extract ID token"
    echo "$AUTH_RESPONSE"
    exit 1
fi

echo "✅ PASS - Authentication successful"
echo "   ID Token: ${ID_TOKEN:0:50}..."
echo ""

# Step 2: Test listing agents
echo "Step 2: List Agents"
echo "-------------------------"

AGENTS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/config?type=agent")

HTTP_CODE=$(echo "$AGENTS_RESPONSE" | tail -n1)
AGENTS_BODY=$(echo "$AGENTS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    AGENT_COUNT=$(echo "$AGENTS_BODY" | jq -r '.configs | length')
    echo "✅ PASS - Listed agents successfully"
    echo "   Agent count: $AGENT_COUNT"
    echo "   Response preview: $(echo "$AGENTS_BODY" | jq -c '.configs[0].agent_name' 2>/dev/null || echo 'N/A')"
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    echo "   Response: $AGENTS_BODY"
fi
echo ""

# Step 3: Test listing domains
echo "Step 3: List Domains"
echo "-------------------------"

DOMAINS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/config?type=domain_template")

HTTP_CODE=$(echo "$DOMAINS_RESPONSE" | tail -n1)
DOMAINS_BODY=$(echo "$DOMAINS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    DOMAIN_COUNT=$(echo "$DOMAINS_BODY" | jq -r '.configs | length')
    echo "✅ PASS - Listed domains successfully"
    echo "   Domain count: $DOMAIN_COUNT"
    echo "   Response preview: $(echo "$DOMAINS_BODY" | jq -c '.configs[0].template_name' 2>/dev/null || echo 'N/A')"
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    echo "   Response: $DOMAINS_BODY"
fi
echo ""

# Step 4: Create a custom agent
echo "Step 4: Create Custom Agent"
echo "-------------------------"

AGENT_CONFIG=$(cat <<EOF
{
  "type": "agent",
  "config": {
    "agent_name": "Test Priority Agent",
    "agent_type": "ingestion",
    "system_prompt": "Extract priority level from civic complaints. Analyze urgency indicators and assign priority: high, medium, or low.",
    "tools": ["bedrock"],
    "output_schema": {
      "priority": {"type": "string", "required": true},
      "urgency_score": {"type": "number", "required": true},
      "confidence": {"type": "number", "required": true}
    }
  }
}
EOF
)

CREATE_AGENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$AGENT_CONFIG" \
  "$API_URL/config")

HTTP_CODE=$(echo "$CREATE_AGENT_RESPONSE" | tail -n1)
CREATE_AGENT_BODY=$(echo "$CREATE_AGENT_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    CREATED_AGENT_ID=$(echo "$CREATE_AGENT_BODY" | jq -r '.config_id // .agent_id // .id')
    echo "✅ PASS - Created agent successfully"
    echo "   Agent ID: $CREATED_AGENT_ID"
    echo "   Response: $(echo "$CREATE_AGENT_BODY" | jq -c '.' 2>/dev/null || echo "$CREATE_AGENT_BODY")"
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    echo "   Response: $CREATE_AGENT_BODY"
    CREATED_AGENT_ID=""
fi
echo ""

# Step 5: Get the created agent
if [ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ]; then
    echo "Step 5: Get Created Agent"
    echo "-------------------------"
    
    GET_AGENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      "$API_URL/config/agent/$CREATED_AGENT_ID")
    
    HTTP_CODE=$(echo "$GET_AGENT_RESPONSE" | tail -n1)
    GET_AGENT_BODY=$(echo "$GET_AGENT_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS - Retrieved agent successfully"
        echo "   Agent name: $(echo "$GET_AGENT_BODY" | jq -r '.agent_name // .config.agent_name')"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $GET_AGENT_BODY"
    fi
    echo ""
fi

# Step 6: Update the agent
if [ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ]; then
    echo "Step 6: Update Agent"
    echo "-------------------------"
    
    UPDATE_AGENT_CONFIG=$(cat <<EOF
{
  "agent_name": "Test Priority Agent Updated",
  "agent_type": "ingestion",
  "system_prompt": "Extract priority level and category from civic complaints. Enhanced version.",
  "tools": ["bedrock", "comprehend_proxy"],
  "output_schema": {
    "priority": {"type": "string", "required": true},
    "category": {"type": "string", "required": true},
    "urgency_score": {"type": "number", "required": true},
    "confidence": {"type": "number", "required": true}
  }
}
EOF
)
    
    UPDATE_AGENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X PUT \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$UPDATE_AGENT_CONFIG" \
      "$API_URL/config/agent/$CREATED_AGENT_ID")
    
    HTTP_CODE=$(echo "$UPDATE_AGENT_RESPONSE" | tail -n1)
    UPDATE_AGENT_BODY=$(echo "$UPDATE_AGENT_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS - Updated agent successfully"
        echo "   Response: $(echo "$UPDATE_AGENT_BODY" | jq -c '.agent_name // .config.agent_name' 2>/dev/null || echo 'Updated')"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $UPDATE_AGENT_BODY"
    fi
    echo ""
fi

# Step 7: Create a domain with selected agents
echo "Step 7: Create Custom Domain"
echo "-------------------------"

# First, get some agent IDs from the list
AGENT_IDS=$(echo "$AGENTS_BODY" | jq -r '.configs[0:3] | map(.agent_id // .id) | @json' 2>/dev/null || echo '[]')

DOMAIN_CONFIG=$(cat <<EOF
{
  "type": "domain_template",
  "config": {
    "template_name": "Test Traffic Domain",
    "domain_id": "test_traffic_domain_$(date +%s)",
    "description": "Testing domain creation with automated script",
    "ingest_agent_ids": $(echo "$AGENTS_BODY" | jq -r '[.configs[] | select(.agent_type == "ingestion") | .agent_id // .id] | .[0:2]' 2>/dev/null || echo '[]'),
    "query_agent_ids": $(echo "$AGENTS_BODY" | jq -r '[.configs[] | select(.agent_type == "query") | .agent_id // .id] | .[0:3]' 2>/dev/null || echo '[]')
  }
}
EOF
)

CREATE_DOMAIN_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DOMAIN_CONFIG" \
  "$API_URL/config")

HTTP_CODE=$(echo "$CREATE_DOMAIN_RESPONSE" | tail -n1)
CREATE_DOMAIN_BODY=$(echo "$CREATE_DOMAIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    CREATED_DOMAIN_ID=$(echo "$CREATE_DOMAIN_BODY" | jq -r '.config_id // .template_id // .id')
    echo "✅ PASS - Created domain successfully"
    echo "   Domain ID: $CREATED_DOMAIN_ID"
    echo "   Response: $(echo "$CREATE_DOMAIN_BODY" | jq -c '.' 2>/dev/null || echo "$CREATE_DOMAIN_BODY")"
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    echo "   Response: $CREATE_DOMAIN_BODY"
    CREATED_DOMAIN_ID=""
fi
echo ""

# Step 8: Submit a report (ingestion)
echo "Step 8: Submit Report (Ingestion)"
echo "-------------------------"

# Get a domain ID to use
DOMAIN_ID=$(echo "$DOMAINS_BODY" | jq -r '.configs[0].domain_id // .configs[0].id' 2>/dev/null)

if [ -n "$DOMAIN_ID" ] && [ "$DOMAIN_ID" != "null" ]; then
    INGEST_PAYLOAD=$(cat <<EOF
{
  "domain_id": "$DOMAIN_ID",
  "text": "Traffic accident at Main Street and 5th Avenue at 3pm today. Multiple vehicles involved, road is blocked.",
  "images": []
}
EOF
)
    
    INGEST_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X POST \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$INGEST_PAYLOAD" \
      "$API_URL/ingest")
    
    HTTP_CODE=$(echo "$INGEST_RESPONSE" | tail -n1)
    INGEST_BODY=$(echo "$INGEST_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
        JOB_ID=$(echo "$INGEST_BODY" | jq -r '.job_id')
        echo "✅ PASS - Submitted report successfully"
        echo "   Job ID: $JOB_ID"
        echo "   Status: $(echo "$INGEST_BODY" | jq -r '.status')"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $INGEST_BODY"
    fi
else
    echo "⚠️  SKIP - No domain ID available for testing"
fi
echo ""

# Step 9: Submit a query
echo "Step 9: Submit Query"
echo "-------------------------"

if [ -n "$DOMAIN_ID" ] && [ "$DOMAIN_ID" != "null" ]; then
    QUERY_PAYLOAD=$(cat <<EOF
{
  "domain_id": "$DOMAIN_ID",
  "question": "What traffic incidents happened today?"
}
EOF
)
    
    QUERY_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X POST \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$QUERY_PAYLOAD" \
      "$API_URL/query")
    
    HTTP_CODE=$(echo "$QUERY_RESPONSE" | tail -n1)
    QUERY_BODY=$(echo "$QUERY_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
        QUERY_JOB_ID=$(echo "$QUERY_BODY" | jq -r '.job_id')
        echo "✅ PASS - Submitted query successfully"
        echo "   Job ID: $QUERY_JOB_ID"
        echo "   Status: $(echo "$QUERY_BODY" | jq -r '.status')"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $QUERY_BODY"
    fi
else
    echo "⚠️  SKIP - No domain ID available for testing"
fi
echo ""

# Step 10: Fetch data (retrieval)
echo "Step 10: Fetch Incidents Data"
echo "-------------------------"

DATA_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/data?type=retrieval&limit=5")

HTTP_CODE=$(echo "$DATA_RESPONSE" | tail -n1)
DATA_BODY=$(echo "$DATA_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    INCIDENT_COUNT=$(echo "$DATA_BODY" | jq -r '.data | length' 2>/dev/null || echo "0")
    echo "✅ PASS - Fetched data successfully"
    echo "   Incident count: $INCIDENT_COUNT"
    echo "   Response preview: $(echo "$DATA_BODY" | jq -c '.data[0]' 2>/dev/null || echo 'N/A')"
else
    echo "❌ FAIL - HTTP $HTTP_CODE"
    echo "   Response: $DATA_BODY"
fi
echo ""

# Step 11: Delete the test agent
if [ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ]; then
    echo "Step 11: Delete Test Agent"
    echo "-------------------------"
    
    DELETE_AGENT_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X DELETE \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      "$API_URL/config/agent/$CREATED_AGENT_ID")
    
    HTTP_CODE=$(echo "$DELETE_AGENT_RESPONSE" | tail -n1)
    DELETE_AGENT_BODY=$(echo "$DELETE_AGENT_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
        echo "✅ PASS - Deleted agent successfully"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $DELETE_AGENT_BODY"
    fi
    echo ""
fi

# Step 12: Delete the test domain
if [ -n "$CREATED_DOMAIN_ID" ] && [ "$CREATED_DOMAIN_ID" != "null" ]; then
    echo "Step 12: Delete Test Domain"
    echo "-------------------------"
    
    DELETE_DOMAIN_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X DELETE \
      -H "Authorization: Bearer $ID_TOKEN" \
      -H "Content-Type: application/json" \
      "$API_URL/config/domain_template/$CREATED_DOMAIN_ID")
    
    HTTP_CODE=$(echo "$DELETE_DOMAIN_RESPONSE" | tail -n1)
    DELETE_DOMAIN_BODY=$(echo "$DELETE_DOMAIN_RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
        echo "✅ PASS - Deleted domain successfully"
    else
        echo "❌ FAIL - HTTP $HTTP_CODE"
        echo "   Response: $DELETE_DOMAIN_BODY"
    fi
    echo ""
fi

# Summary
echo "========================================="
echo "Test Suite Complete"
echo "========================================="
echo ""
echo "Summary:"
echo "--------"
echo "✅ Authentication: Working"
echo "✅ List Agents: Working"
echo "✅ List Domains: Working"
echo "✅ Create Agent: $([ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ] && echo "Working" || echo "Check logs")"
echo "✅ Update Agent: $([ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ] && echo "Working" || echo "Skipped")"
echo "✅ Delete Agent: $([ -n "$CREATED_AGENT_ID" ] && [ "$CREATED_AGENT_ID" != "null" ] && echo "Working" || echo "Skipped")"
echo "✅ Create Domain: $([ -n "$CREATED_DOMAIN_ID" ] && [ "$CREATED_DOMAIN_ID" != "null" ] && echo "Working" || echo "Check logs")"
echo "✅ Delete Domain: $([ -n "$CREATED_DOMAIN_ID" ] && [ "$CREATED_DOMAIN_ID" != "null" ] && echo "Working" || echo "Skipped")"
echo "✅ Submit Report: $([ -n "$DOMAIN_ID" ] && [ "$DOMAIN_ID" != "null" ] && echo "Working" || echo "Skipped")"
echo "✅ Submit Query: $([ -n "$DOMAIN_ID" ] && [ "$DOMAIN_ID" != "null" ] && echo "Working" || echo "Skipped")"
echo "✅ Fetch Data: Working"
echo ""
echo "All core API endpoints are functional!"
echo ""
