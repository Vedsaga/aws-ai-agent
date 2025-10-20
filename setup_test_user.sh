#!/bin/bash
# Setup test user with known password for API testing

USER_POOL_ID="us-east-1_7QZ7Y6Gbl"
USERNAME="testuser"
PASSWORD="TestPassword123!"

echo "Setting password for test user..."
echo "User Pool: $USER_POOL_ID"
echo "Username: $USERNAME"
echo ""

# Set permanent password
aws cognito-idp admin-set-user-password \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --permanent

if [ $? -eq 0 ]; then
    echo "✅ Password set successfully!"
    echo ""
    echo "Test user credentials:"
    echo "  Username: $USERNAME"
    echo "  Password: $PASSWORD"
    echo ""
    echo "Get JWT token with:"
    echo "  COGNITO_USERNAME=$USERNAME COGNITO_PASSWORD=$PASSWORD ./get_jwt_token.sh"
else
    echo "❌ Failed to set password"
    exit 1
fi
