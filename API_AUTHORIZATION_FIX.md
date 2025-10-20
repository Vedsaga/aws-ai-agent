# API Authorization Issue - Fix Guide

## Issue Summary

**Problem:** API Gateway is returning 403 errors with the message:
```
"Invalid key=value pair (missing equal-sign) in Authorization header"
```

**Root Cause:** The API Gateway appears to be configured with AWS_IAM authorization type instead of or in addition to the CUSTOM authorizer (Lambda authorizer).

**Impact:** API calls with Bearer tokens are being rejected, preventing automated testing and potentially affecting frontend functionality.

## Diagnosis

### Symptoms
1. Authentication with Cognito succeeds (ID token is generated)
2. API endpoints return HTTP 403 when called with `Authorization: Bearer <token>`
3. Error message mentions "key=value pair" which is specific to AWS Signature V4 format
4. All endpoints affected: /config, /ingest, /query, /data

### Expected Behavior
- API Gateway should accept `Authorization: Bearer <JWT_TOKEN>` header
- Lambda authorizer should validate the JWT token
- Authorized requests should proceed to backend Lambda functions

### Actual Behavior
- API Gateway is trying to parse the Authorization header as AWS Signature V4
- This suggests IAM authorization is enabled instead of CUSTOM authorization

## Solution

### Step 1: Verify API Gateway Configuration

Check the deployed API Gateway configuration:

```bash
# Get API ID
API_ID=$(aws apigateway get-rest-apis \
  --region us-east-1 \
  --query "items[?name=='MultiAgentOrchestrationAPI'].id" \
  --output text)

echo "API ID: $API_ID"

# Get resources
aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region us-east-1

# Check authorization type for a specific method (e.g., GET /config)
aws apigateway get-method \
  --rest-api-id $API_ID \
  --resource-id <RESOURCE_ID> \
  --http-method GET \
  --region us-east-1 \
  --query 'authorizationType'
```

### Step 2: Check CDK Stack Configuration

Review the API stack configuration in `infrastructure/lib/stacks/api-stack.ts`:

```typescript
// Verify this configuration exists for all methods:
configResource.addMethod('GET', new apigateway.LambdaIntegration(configHandler), {
  authorizer: this.authorizer,
  authorizationType: apigateway.AuthorizationType.CUSTOM,  // Should be CUSTOM, not AWS_IAM
});
```

### Step 3: Verify Lambda Authorizer

Check if the Lambda authorizer is properly configured:

```bash
# List authorizers
aws apigateway get-authorizers \
  --rest-api-id $API_ID \
  --region us-east-1

# Get authorizer details
aws apigateway get-authorizer \
  --rest-api-id $API_ID \
  --authorizer-id <AUTHORIZER_ID> \
  --region us-east-1
```

Expected authorizer configuration:
- Type: TOKEN
- Identity Source: method.request.header.Authorization
- Lambda Function: CognitoAuthorizer

### Step 4: Fix the Configuration

If the issue is in the CDK code:

1. **Update api-stack.ts** (if needed):
   ```typescript
   // Ensure all methods use CUSTOM authorization
   resource.addMethod('GET', integration, {
     authorizer: this.authorizer,
     authorizationType: apigateway.AuthorizationType.CUSTOM,
     // NOT: authorizationType: apigateway.AuthorizationType.IAM,
   });
   ```

2. **Redeploy the stack:**
   ```bash
   cd infrastructure
   npm run cdk deploy MultiAgentOrchestrationStack
   ```

3. **Verify the fix:**
   ```bash
   # Test with authenticated request
   bash infrastructure/frontend/test-api-authenticated.sh
   ```

### Step 5: Alternative - Manual API Gateway Fix

If you need to fix it directly in AWS Console:

1. Open AWS Console → API Gateway
2. Select "MultiAgentOrchestrationAPI"
3. For each resource and method:
   - Click on the method (e.g., GET)
   - Click "Method Request"
   - Check "Authorization" setting
   - Should be: "CognitoAuthorizer" (or your custom authorizer name)
   - Should NOT be: "AWS_IAM"
4. Deploy the API:
   - Click "Actions" → "Deploy API"
   - Select stage: "v1"
   - Click "Deploy"

## Verification

After applying the fix, verify it works:

### Test 1: API Smoke Test
```bash
bash infrastructure/frontend/test-api-smoke.sh
```

Expected: All endpoints return 403 (auth required)

### Test 2: Authenticated API Test
```bash
bash infrastructure/frontend/test-api-authenticated.sh
```

Expected: All tests pass with HTTP 200/201 responses

### Test 3: Browser Test
1. Open `infrastructure/frontend/test-browser-api.html`
2. Authenticate with test credentials
3. Run all tests
4. All should pass

### Test 4: Frontend Application
1. Start frontend: `npm run dev`
2. Navigate to http://localhost:3000
3. Log in with test credentials
4. Navigate to `/agents`
5. Verify agents list loads successfully

## Common Issues

### Issue 1: Authorizer Not Found

**Symptom:** API Gateway can't find the authorizer

**Fix:**
1. Check if Lambda authorizer function exists
2. Verify IAM permissions for API Gateway to invoke Lambda
3. Redeploy the auth stack first, then API stack

### Issue 2: Token Validation Fails

**Symptom:** 401 Unauthorized even with valid token

**Fix:**
1. Check Lambda authorizer logs in CloudWatch
2. Verify Cognito User Pool ID and Client ID in authorizer environment variables
3. Ensure JWKS URL is correct

### Issue 3: CORS Errors

**Symptom:** Browser shows CORS errors

**Fix:**
1. Ensure API Gateway has CORS enabled
2. Check OPTIONS method is configured
3. Verify CORS headers in Lambda responses

## Rollback Plan

If the fix causes issues:

1. **Revert CDK changes:**
   ```bash
   git revert <commit-hash>
   npm run cdk deploy MultiAgentOrchestrationStack
   ```

2. **Restore previous API Gateway configuration:**
   - Use AWS Console to manually restore settings
   - Or restore from CloudFormation stack

3. **Verify rollback:**
   ```bash
   bash infrastructure/frontend/test-api-smoke.sh
   ```

## Testing After Fix

Once the authorization issue is fixed, run the complete test suite:

1. **Automated Tests:**
   ```bash
   # API smoke test
   bash infrastructure/frontend/test-api-smoke.sh
   
   # Authenticated API test
   bash infrastructure/frontend/test-api-authenticated.sh
   
   # Node.js API test
   cd infrastructure/frontend
   node test-frontend-api.js
   ```

2. **Manual Tests:**
   - Follow `MANUAL_TEST_CHECKLIST.md`
   - Test all 40+ test cases
   - Document results

3. **Frontend Tests:**
   - Test agent CRUD operations
   - Test domain creation flow
   - Test report submission
   - Test query submission
   - Test real-time status updates

## Additional Resources

- **API Stack Code:** `infrastructure/lib/stacks/api-stack.ts`
- **Lambda Authorizer:** `infrastructure/lambda/authorizer/authorizer.py`
- **Testing Guide:** `infrastructure/frontend/TESTING_GUIDE.md`
- **Test Checklist:** `infrastructure/frontend/MANUAL_TEST_CHECKLIST.md`
- **Test Summary:** `infrastructure/frontend/TESTING_SUMMARY.md`

## Support

If you need help:
1. Check CloudWatch logs for Lambda authorizer
2. Review API Gateway execution logs
3. Test with AWS CLI to isolate the issue
4. Contact AWS support if needed

## Success Criteria

The fix is successful when:
- ✅ API smoke test passes (all endpoints return 403 without auth)
- ✅ Authenticated API test passes (all endpoints return 200 with auth)
- ✅ Browser test tool works correctly
- ✅ Frontend application can list agents and domains
- ✅ All CRUD operations work through the frontend
- ✅ No CORS errors in browser console
- ✅ No authorization errors in CloudWatch logs

---

**Status:** Issue identified, fix documented, awaiting implementation
**Priority:** HIGH
**Impact:** Blocks automated testing and may affect frontend functionality
**Estimated Fix Time:** 30-60 minutes
