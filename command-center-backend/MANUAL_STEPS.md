# Manual Steps Required for Deployment

## Summary

**NO manual steps required!** 🎉

As of AWS's new guidelines, Bedrock model access is automatically enabled. Everything is fully automated by the deployment script.

---

## ✅ No Manual Steps Required!

### AWS Update (October 2024)

**Model access page has been retired**

Access to all serverless foundation models are now automatically enabled for your AWS account. You no longer need to manually request or enable model access.

### What Changed?

**Before:**
- Manual model access request required
- Wait for approval
- Enable each model individually

**Now:**
- ✅ Automatic access to all models
- ✅ No approval needed
- ✅ Use IAM policies to restrict if needed

### Only Requirement

**IAM User with AdministratorAccess** - That's it!

Your user already has this: `Command-center-hackathon-Administrator-Access`

### Old Steps (No Longer Needed):

#### 1. Open AWS Bedrock Console
Go to: https://console.aws.amazon.com/bedrock/

Or:
- AWS Console → Search "Bedrock" → Click "Amazon Bedrock"

#### 2. Navigate to Model Access
- Look at the left sidebar
- Click **"Model access"**

#### 3. Request Access
- Click **"Manage model access"** or **"Request model access"** button (top right)
- You'll see a list of available models

#### 4. Select Claude 3 Sonnet
- Scroll down to find **"Claude 3 Sonnet"** by Anthropic
- Check the box next to it
- You may also want to check other Claude models while you're here

#### 5. Submit Request
- Click **"Request model access"** button at the bottom
- Or click **"Save changes"** if you already have some models enabled

#### 6. Wait for Approval
- Status will change from "Available" → "In progress" → "Access granted"
- **Usually instant** (takes 1-10 seconds)
- Refresh the page if needed

#### 7. Verify Access
Run this command to verify:
```bash
aws bedrock list-foundation-models --region us-east-1 | grep -i "claude-3-sonnet"
```

If you see output, you have access! ✓

---

## Visual Guide

```
AWS Console
    ↓
Search "Bedrock"
    ↓
Click "Amazon Bedrock"
    ↓
Left Sidebar → "Model access"
    ↓
Click "Manage model access"
    ↓
Find "Claude 3 Sonnet"
    ↓
Check the box
    ↓
Click "Request model access"
    ↓
Wait 1-10 seconds
    ↓
Status: "Access granted" ✓
```

---

## Screenshot Locations

### Step 1: Bedrock Console
```
URL: https://console.aws.amazon.com/bedrock/
Look for: Orange "Bedrock" logo at top
```

### Step 2: Model Access Page
```
Left sidebar: "Model access" (with a key icon)
Main area: List of foundation models
```

### Step 3: Claude 3 Sonnet
```
Provider: Anthropic
Model name: Claude 3 Sonnet
Status: "Available" (before request)
        "Access granted" (after approval)
```

---

## What If I Skip This Step?

If you try to deploy without Bedrock access, you'll see:

```
Error: Access denied to model anthropic.claude-3-sonnet
```

The deployment will fail when creating the Bedrock Agent.

**Solution:** Complete the manual step above, then redeploy.

---

## Alternative: Request via AWS CLI

If you prefer command line:

```bash
# This may not work for all accounts
aws bedrock put-model-invocation-logging-configuration \
  --region us-east-1
```

**Note:** Model access requests are typically done via Console for first-time setup.

---

## After Requesting Access

Once approved, you can:

1. ✅ Run the deployment script
2. ✅ Deploy as many times as you want
3. ✅ No need to request access again

The access is permanent for your AWS account.

---

## Other Models (Optional)

While you're requesting access, consider enabling:

- **Claude 3.5 Sonnet** (newer, better performance)
- **Claude 3 Haiku** (faster, cheaper)
- **Claude 3 Opus** (most capable)

These can be useful for future projects or testing.

---

## Troubleshooting

### "Model access" not visible in sidebar
→ Ensure you're in a region that supports Bedrock (us-east-1, us-west-2, etc.)

### Request button is grayed out
→ Your IAM user may lack permissions. Contact your AWS administrator.

### Access request denied
→ Rare, but may happen for new AWS accounts. Contact AWS Support.

### Can't find Claude 3 Sonnet
→ Ensure you're in the right region. Try us-east-1.

---

## Verification Checklist

After requesting access:

- [ ] Opened AWS Bedrock Console
- [ ] Navigated to "Model access"
- [ ] Found "Claude 3 Sonnet"
- [ ] Checked the box
- [ ] Clicked "Request model access"
- [ ] Status shows "Access granted"
- [ ] Verified with AWS CLI (optional)

---

## Ready to Deploy?

Once Bedrock access is granted:

```bash
cd command-center-backend
bash scripts/full-deploy.sh
```

The script will verify Bedrock access and proceed with deployment.

---

## Summary

**Manual Steps:**
1. ✋ Request Bedrock Claude 3 Sonnet access (AWS Console) - **2-3 minutes**

**Automated Steps:**
- ✅ Everything else! - **5-10 minutes**

**Total Time:**
- **First deployment:** ~10-15 minutes
- **Redeployments:** ~1-5 minutes

---

## Questions?

- **What if I already have Bedrock access?** → Skip to deployment!
- **Do I need to do this for every deployment?** → No, only once
- **Can I automate this?** → Not easily, AWS requires manual approval
- **What if my account is new?** → May need to wait for AWS account verification

---

**Next:** See `START_HERE.md` for deployment instructions
