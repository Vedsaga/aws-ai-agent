# Pre-Deployment Checklist

## Manual Steps Required BEFORE Running Deployment Script

### 1. AWS Bedrock Model Access (REQUIRED)

**This is the ONLY manual step that requires AWS Console access.**

#### Why?
The Bedrock Agent uses Claude 3 Sonnet model, which requires explicit access approval.

#### Steps:
1. Go to AWS Console: https://console.aws.amazon.com/bedrock/
2. Navigate to: **Bedrock** → **Model access** (left sidebar)
3. Click **"Manage model access"** or **"Request model access"**
4. Find **"Claude 3 Sonnet"** in the list
5. Check the box next to it
6. Click **"Request model access"** or **"Save changes"**
7. Wait for approval (usually instant, status changes to "Access granted")

#### Verification:
```bash
aws bedrock list-foundation-models --region us-east-1 | grep -i claude-3-sonnet
```

If you see output, you have access. If not, complete the steps above.

---

## Automated Steps (Handled by Script)

The deployment script automatically handles:

✅ AWS credentials verification  
✅ CDK bootstrap (first-time setup)  
✅ npm dependencies installation  
✅ TypeScript compilation  
✅ Infrastructure deployment (DynamoDB, Lambda, API Gateway, Bedrock Agent)  
✅ IAM roles and policies creation  
✅ API key generation  
✅ Database population  

---

## Prerequisites Verification

Before running the deployment script, verify these are installed:

### 1. Node.js (v18+)
```bash
node --version
# Should show v18.x or higher
```

**If not installed:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node@18

# Or download from: https://nodejs.org/
```

### 2. AWS CLI (v2)
```bash
aws --version
# Should show aws-cli/2.x.x
```

**If not installed:**
```bash
# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# macOS
brew install awscli

# Or follow: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
```

### 3. AWS Credentials Configured
```bash
aws sts get-caller-identity
# Should show your account details
```

**If not configured:**
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### 4. AWS CDK CLI
```bash
cdk --version
# Should show 2.x.x
```

**If not installed:**
```bash
npm install -g aws-cdk
```

---

## Quick Verification Script

Run this to check all prerequisites:

```bash
#!/bin/bash

echo "Checking prerequisites..."
echo ""

# Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js: $(node --version)"
else
    echo "✗ Node.js: NOT INSTALLED"
fi

# npm
if command -v npm &> /dev/null; then
    echo "✓ npm: $(npm --version)"
else
    echo "✗ npm: NOT INSTALLED"
fi

# AWS CLI
if command -v aws &> /dev/null; then
    echo "✓ AWS CLI: $(aws --version 2>&1 | head -n1)"
else
    echo "✗ AWS CLI: NOT INSTALLED"
fi

# AWS Credentials
if aws sts get-caller-identity &> /dev/null; then
    echo "✓ AWS Credentials: CONFIGURED"
    aws sts get-caller-identity
else
    echo "✗ AWS Credentials: NOT CONFIGURED"
fi

# CDK
if command -v cdk &> /dev/null; then
    echo "✓ AWS CDK: $(cdk --version)"
else
    echo "✗ AWS CDK: NOT INSTALLED"
fi

echo ""
echo "If all items show ✓, you're ready to deploy!"
```

Save this as `check-prerequisites.sh` and run:
```bash
bash check-prerequisites.sh
```

---

## Summary

### Manual Steps (Do Once):
1. ✋ **Request Bedrock Claude 3 Sonnet access** (AWS Console)

### Automated Steps (Script Handles):
- Everything else!

### Ready to Deploy?
Once Bedrock access is granted, run:
```bash
bash scripts/full-deploy.sh
```

---

## Troubleshooting

### "Access Denied" for Bedrock
→ Complete the Bedrock model access request (step 1 above)

### "CDK bootstrap required"
→ Script handles this automatically, or run manually:
```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

### "Insufficient permissions"
→ Ensure your IAM user has these permissions:
- CloudFormation (full)
- Lambda (full)
- API Gateway (full)
- DynamoDB (full)
- Bedrock (full)
- IAM (create roles)
- S3 (CDK bucket access)

### "npm not found"
→ Install Node.js (includes npm)

---

## Next Steps After Deployment

See `QUICK_DEPLOY.md` for post-deployment steps and frontend integration.
