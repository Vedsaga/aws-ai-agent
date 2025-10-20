#!/bin/bash
# Script to get JWT token from Cognito for API testing

USER_POOL_ID="us-east-1_7QZ7Y6Gbl"
CLIENT_ID="6gobbpage9af3nd7ahm3lchkct"
REGION="us-east-1"

# Check if username and password are provided
if [ -z "$COGNITO_USERNAME" ] || [ -z "$COGNITO_PASSWORD" ]; then
    echo "ERROR: COGNITO_USERNAME and COGNITO_PASSWORD environment variables are required"
    echo ""
    echo "Usage:"
    echo "  COGNITO_USERNAME=your_email COGNITO_PASSWORD=your_password ./get_jwt_token.sh"
    echo ""
    echo "Or create a test user first:"
    echo "  aws cognito-idp admin-create-user \\"
    echo "    --user-pool-id $USER_POOL_ID \\"
    echo "    --username test@example.com \\"
    echo "    --temporary-password TempPass123! \\"
    echo "    --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true \\"
    echo "    --message-action SUPPRESS"
    exit 1
fi

echo "Authenticating with Cognito..."
echo "User Pool: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo "Username: $COGNITO_USERNAME"
echo ""

# Authenticate and get tokens
RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$CLIENT_ID" \
    --auth-parameters "USERNAME=$COGNITO_USERNAME,PASSWORD=$COGNITO_PASSWORD" \
    --region "$REGION" \
    2>&1)

# Check if authentication was successful
if echo "$RESPONSE" | grep -q "IdToken"; then
    # Extract ID token (JWT)
    JWT_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.IdToken')
    
    echo "✅ Authentication successful!"
    echo ""
    echo "JWT Token (first 50 chars): ${JWT_TOKEN:0:50}..."
    echo ""
    echo "Export this token for testing:"
    echo "export JWT_TOKEN='$JWT_TOKEN'"
    echo ""
    echo "Or run tests directly:"
    echo "API_URL=https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1 JWT_TOKEN='$JWT_TOKEN' python3 test_api.py"
    
else
    echo "❌ Authentication failed!"
    echo ""
    echo "Response:"
    echo "$RESPONSE"
    echo ""
    
    # Check if it's a password reset required error
    if echo "$RESPONSE" | grep -q "NEW_PASSWORD_REQUIRED"; then
        echo "⚠️  New password required. The user needs to change their temporary password."
        echo ""
        echo "To set a permanent password:"
        echo "  aws cognito-idp admin-set-user-password \\"
        echo "    --user-pool-id $USER_POOL_ID \\"
        echo "    --username $COGNITO_USERNAME \\"
        echo "    --password YourNewPassword123! \\"
        echo "    --permanent"
    fi
    
    exit 1
fi
