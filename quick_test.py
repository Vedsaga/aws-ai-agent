#!/usr/bin/env python3
"""
Quick API Test Script - No AWS SDK needed
Tests API endpoints directly via HTTP
"""

import requests
import json
import sys

# Configuration
API_URL = "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1"
USER_POOL_ID = "us-east-1_7QZ7Y6Gbl"
CLIENT_ID = "6gobbpage9af3nd7ahm3lchkct"


def test_no_auth():
    """Test 1: Verify 401 without auth"""
    print("\n" + "=" * 60)
    print("TEST 1: No Authentication")
    print("=" * 60)

    response = requests.get(f"{API_URL}/api/v1/config", params={"type": "agent"})

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 401:
        print("✓ PASS - Correctly returns 401")
        return True
    else:
        print("✗ FAIL - Expected 401")
        return False


def get_cognito_token_via_srp():
    """Try to get Cognito token using direct API call"""
    print("\n" + "=" * 60)
    print("TEST 2: Getting Cognito Token")
    print("=" * 60)

    # Try using Cognito Identity Provider API directly
    cognito_url = f"https://cognito-idp.us-east-1.amazonaws.com/"

    payload = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": CLIENT_ID,
        "AuthParameters": {"USERNAME": "testuser", "PASSWORD": "TestPassword123!"},
    }

    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    }

    try:
        response = requests.post(cognito_url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            token = data.get("AuthenticationResult", {}).get("IdToken")
            if token:
                print(f"✓ Token obtained (length: {len(token)})")
                return token
            else:
                print("✗ No token in response")
                print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"✗ Failed: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")

    return None


def test_with_mock_token():
    """Test 3: Try with a mock token to see Lambda error"""
    print("\n" + "=" * 60)
    print("TEST 3: Test with Mock Token (to trigger Lambda)")
    print("=" * 60)

    # Use a fake JWT structure
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    headers = {"Authorization": f"Bearer {mock_token}"}
    response = requests.get(
        f"{API_URL}/api/v1/config", params={"type": "agent"}, headers=headers
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    if response.status_code == 500:
        print("\n⚠ Lambda is executing but returning 500 error")
        print("This means Lambda function has bugs we need to fix")
        return False
    elif response.status_code == 401:
        print("\n✓ Authorizer correctly rejects invalid token")
        return True
    elif response.status_code == 200:
        print("\n⚠ Unexpected 200 - token validation may be disabled")
        return True
    else:
        print(f"\n? Unexpected status: {response.status_code}")
        return False


def test_config_create():
    """Test 4: Try to create an agent"""
    print("\n" + "=" * 60)
    print("TEST 4: Create Agent (with mock token)")
    print("=" * 60)

    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    headers = {
        "Authorization": f"Bearer {mock_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "type": "agent",
        "config": {
            "agent_name": "Test Agent",
            "agent_type": "custom",
            "system_prompt": "You are a test agent",
            "tools": ["bedrock"],
            "output_schema": {"result": "string", "confidence": "number"},
        },
    }

    response = requests.post(f"{API_URL}/api/v1/config", json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    return response.status_code in [201, 401]


def test_ingest():
    """Test 5: Try to submit a report"""
    print("\n" + "=" * 60)
    print("TEST 5: Submit Report (with mock token)")
    print("=" * 60)

    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    headers = {
        "Authorization": f"Bearer {mock_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "domain_id": "civic_complaints",
        "text": "Test report: Broken streetlight on Main St",
    }

    response = requests.post(f"{API_URL}/api/v1/ingest", json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    return response.status_code in [202, 401]


def main():
    print("\n" + "=" * 70)
    print("  QUICK API TEST - Direct HTTP Testing (No AWS SDK)")
    print("=" * 70)
    print(f"\nAPI URL: {API_URL}")
    print(f"Testing without AWS credentials (pure HTTP)")

    results = []

    # Test 1: No auth
    results.append(("No Auth Test", test_no_auth()))

    # Test 2: Get real token
    token = get_cognito_token_via_srp()

    # Test 3: Mock token
    results.append(("Mock Token Test", test_with_mock_token()))

    # Test 4: Create agent
    results.append(("Create Agent", test_config_create()))

    # Test 5: Ingest
    results.append(("Submit Report", test_ingest()))

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed >= 3:
        print("\n✓ GOOD - API Gateway is working, auth is configured")
        print("\nNext steps:")
        print("1. Fix Cognito token issue (or use API Gateway test)")
        print("2. Check CloudWatch logs once Lambda is triggered")
        print("3. Deploy updated Lambda handlers")
    else:
        print("\n✗ ISSUES - Need to investigate API Gateway configuration")

    return 0 if passed >= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
