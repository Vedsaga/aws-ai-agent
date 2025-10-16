# 502 Error Fix - Root Cause Analysis

## 🔍 Problem Identified

All Lambda functions returning **502 Internal Server Error**

### Error from CloudWatch Logs:
```
Runtime.ImportModuleError: Error: Cannot find module 'zod'
Require stack:
- /var/task/lib/types/api.js
- /var/task/lib/lambdas/updatesHandler.handler
```

## 🎯 Root Cause

**CDK was deploying Lambda code WITHOUT dependencies**

The Lambda functions were created with:
```typescript
code: lambda.Code.fromAsset('dist')
```

This only uploaded the compiled `.js` files from TypeScript, but **NOT** the `node_modules/` directory containing:
- `zod` (validation library)
- `@aws-sdk/client-dynamodb`
- `@aws-sdk/lib-dynamodb`  
- `@aws-sdk/client-bedrock-agent-runtime`

## ✅ Solution Implemented

### 1. Created Bundle Script
**File:** `scripts/prepare-lambda-bundle.sh`

Bundles Lambda code WITH dependencies:
```bash
lambda-bundle/
├── lib/              # Compiled code
├── node_modules/     # Production dependencies ✅
└── package.json
```

### 2. Updated CDK Stack
**File:** `lib/command-center-backend-stack.ts`

Changed all 4 Lambda functions:
```typescript
// Before
code: lambda.Code.fromAsset('dist')

// After  
code: lambda.Code.fromAsset('lambda-bundle')
```

### 3. Updated Deployment Process
**File:** `package.json`

```json
{
  "scripts": {
    "bundle": "./scripts/prepare-lambda-bundle.sh",
    "deploy": "./scripts/prepare-lambda-bundle.sh && cdk deploy"
  }
}
```

## 🚀 How to Deploy the Fix

```bash
# One command to fix everything
npm run deploy
```

This will:
1. Build TypeScript → `dist/`
2. Create bundle with dependencies → `lambda-bundle/`
3. Deploy to AWS with CDK
4. Update all 4 Lambda functions

## 🧪 Verification

```bash
# Test the API
npm run test:quick

# Expected: All tests pass with 200/400 status codes
# No more 502 errors!
```

## 📊 Impact

**Affected Lambda Functions:**
1. ✅ CommandCenterBackend-Dev-UpdatesHandler
2. ✅ CommandCenterBackend-Dev-QueryHandler
3. ✅ CommandCenterBackend-Dev-ActionHandler
4. ✅ CommandCenterBackend-Dev-DatabaseQueryTool

**API Endpoints Fixed:**
1. ✅ GET /data/updates
2. ✅ POST /agent/query
3. ✅ POST /agent/action

## 🔄 Deployment Status

**Current Status:** Code changes committed, ready to deploy

**Next Action:** Run `npm run deploy` to apply the fix

**ETA:** ~5-10 minutes for deployment to complete

## 📝 Technical Details

### Why This Happened
AWS Lambda needs ALL code and dependencies in the deployment package. When using `lambda.Code.fromAsset()`, CDK uploads exactly what's in that directory. The `dist/` directory only had compiled JavaScript, not `node_modules/`.

### Why It Works Now
The `lambda-bundle/` directory contains:
- Compiled JavaScript code
- All production dependencies from `package.json`
- Optimized (removed test files, docs, source maps)

### Bundle Size Optimization
The script removes unnecessary files:
- `*.md` (documentation)
- `*.ts` (TypeScript source)
- `*.map` (source maps)
- `test/` directories
- `examples/` directories

This keeps the Lambda package small for faster cold starts.

## 🎓 Lessons Learned

1. **Always bundle dependencies** for Lambda functions
2. **Test deployment packages** before going to production
3. **Check CloudWatch Logs** for runtime errors
4. **Use proper bundling tools** (esbuild, webpack, or manual bundling)

## 🔮 Future Improvements

Consider migrating to `NodejsFunction` from `aws-cdk-lib/aws-lambda-nodejs`:
- Automatic dependency bundling with esbuild
- Tree-shaking (removes unused code)
- Minification
- TypeScript compilation built-in
- No manual bundling needed

Example:
```typescript
import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs';

new NodejsFunction(this, 'MyFunction', {
  entry: 'lib/lambdas/handler.ts',
  // Dependencies automatically bundled!
});
```

## ✅ Checklist

- [x] Identified root cause (missing dependencies)
- [x] Created bundling script
- [x] Updated CDK stack configuration
- [x] Updated deployment process
- [x] Added documentation
- [ ] **Deploy the fix** ← YOU ARE HERE
- [ ] Verify with tests
- [ ] Confirm with frontend team

## 🆘 Support

If deployment fails or tests still show 502:

1. Check bundle exists:
   ```bash
   ls -la lambda-bundle/node_modules/zod
   ```

2. Verify CDK diff:
   ```bash
   cdk diff
   ```

3. Check deployment logs:
   ```bash
   cdk deploy --verbose
   ```

4. Inspect Lambda function:
   ```bash
   aws lambda get-function --function-name CommandCenterBackend-Dev-UpdatesHandler
   ```
