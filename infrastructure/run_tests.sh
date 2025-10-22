#!/bin/bash
export API_BASE_URL=https://u4ytm9eyng.execute-api.us-east-1.amazonaws.com/v1
export COGNITO_CLIENT_ID=6gobbpage9af3nd7ahm3lchkct
export TEST_USERNAME=testuser
export TEST_PASSWORD="TestPassword123!"
export AWS_REGION=us-east-1

python3 TEST.py --mode deployed
