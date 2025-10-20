import json
import requests

url = "https://cognito-idp.us-east-1.amazonaws.com/"

headers = {
    "Content-Type": "application/x-amz-json-1.1",
    "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
}

data = {
    "AuthFlow": "USER_PASSWORD_AUTH",
    "ClientId": "6gobbpage9af3nd7ahm3lchkct",
    "AuthParameters": {
        "USERNAME": "testuser",
        "PASSWORD": "TestPassword123!",
    },
}

response = requests.post(url, headers=headers, data=json.dumps(data))

if response.status_code == 200:
    print(response.json()["AuthenticationResult"]["IdToken"])
else:
    print(f"Authentication failed: {response.text}")
    exit(1)
