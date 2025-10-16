# Bedrock Model Selection Guide

## Available Models

You can now easily switch between different Claude models during deployment.

### Supported Models

| Model | ID | Best For | Cost | Speed |
|-------|-----|----------|------|-------|
| **Claude 3 Sonnet** (default) | `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced performance | $$ | Medium |
| **Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20240620-v1:0` | Best overall | $$$ | Fast |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Fast responses | $ | Fastest |
| **Claude 3 Opus** | `anthropic.claude-3-opus-20240229-v1:0` | Most capable | $$$$ | Slower |

---

## How to Select a Model

### During Deployment

Use the `--model` flag:

```bash
# Deploy with Claude 3 Sonnet (default)
bash scripts/full-deploy.sh

# Deploy with Claude 3.5 Sonnet (recommended)
bash scripts/full-deploy.sh --model anthropic.claude-3-5-sonnet-20240620-v1:0

# Deploy with Claude 3 Haiku (fastest, cheapest)
bash scripts/full-deploy.sh --model anthropic.claude-3-haiku-20240307-v1:0

# Deploy with Claude 3 Opus (most capable)
bash scripts/full-deploy.sh --model anthropic.claude-3-opus-20240229-v1:0
```

### Via Environment Variable

```bash
# Set model via environment variable
export BEDROCK_MODEL="anthropic.claude-3-5-sonnet-20240620-v1:0"
bash scripts/full-deploy.sh

# Or inline
BEDROCK_MODEL="anthropic.claude-3-haiku-20240307-v1:0" bash scripts/full-deploy.sh
```

---

## Model Comparison

### Claude 3 Sonnet (Default)
**ID:** `anthropic.claude-3-sonnet-20240229-v1:0`

✅ **Pros:**
- Good balance of speed and capability
- Reliable for most use cases
- Moderate cost

❌ **Cons:**
- Not the fastest
- Not the most capable

**Use when:** You want balanced performance and cost

---

### Claude 3.5 Sonnet (Recommended)
**ID:** `anthropic.claude-3-5-sonnet-20240620-v1:0`

✅ **Pros:**
- Best overall performance
- Improved reasoning
- Better at complex queries
- Faster than Claude 3 Sonnet

❌ **Cons:**
- Slightly higher cost than Claude 3 Sonnet

**Use when:** You want the best performance (recommended for production)

---

### Claude 3 Haiku (Fastest)
**ID:** `anthropic.claude-3-haiku-20240307-v1:0`

✅ **Pros:**
- Fastest responses
- Lowest cost
- Good for simple queries

❌ **Cons:**
- Less capable for complex reasoning
- May miss nuances

**Use when:** Speed and cost are priorities, queries are straightforward

---

### Claude 3 Opus (Most Capable)
**ID:** `anthropic.claude-3-opus-20240229-v1:0`

✅ **Pros:**
- Most capable model
- Best at complex reasoning
- Highest quality responses

❌ **Cons:**
- Highest cost
- Slower responses

**Use when:** You need maximum capability, cost is not a concern

---

## Switching Models

### Change Model After Deployment

To switch to a different model:

```bash
# Redeploy with new model
bash scripts/full-deploy.sh --model anthropic.claude-3-5-sonnet-20240620-v1:0 --skip-populate
```

**Time:** ~3-5 minutes (only updates Bedrock Agent)

### What Gets Updated

When you change models:
- ✅ Bedrock Agent configuration
- ✅ IAM permissions
- ❌ Database (unchanged)
- ❌ Lambda functions (unchanged)
- ❌ API Gateway (unchanged)

---

## Model Access Requirements

### Before Using a Model

Ensure you have access to the model in AWS Bedrock:

1. Go to: https://console.aws.amazon.com/bedrock/
2. Click: **Model access** (left sidebar)
3. Click: **Manage model access**
4. Check the models you want to use:
   - ☑ Claude 3 Sonnet
   - ☑ Claude 3.5 Sonnet
   - ☑ Claude 3 Haiku
   - ☑ Claude 3 Opus
5. Click: **Request model access**
6. Wait for approval (usually instant)

### Verify Access

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1 | grep -i claude

# Check specific model
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20240620-v1:0']"
```

---

## Cost Comparison

Approximate costs per 1,000 requests (assuming 1K input + 1K output tokens):

| Model | Input Cost | Output Cost | Total per 1K requests |
|-------|-----------|-------------|----------------------|
| Claude 3 Haiku | $0.25 | $1.25 | **~$1.50** |
| Claude 3 Sonnet | $3.00 | $15.00 | **~$18.00** |
| Claude 3.5 Sonnet | $3.00 | $15.00 | **~$18.00** |
| Claude 3 Opus | $15.00 | $75.00 | **~$90.00** |

**Note:** Actual costs vary based on token usage. These are estimates.

---

## Recommendations

### Development
```bash
# Use Haiku for fast iteration
bash scripts/full-deploy.sh --model anthropic.claude-3-haiku-20240307-v1:0
```

### Staging
```bash
# Use Sonnet for testing
bash scripts/full-deploy.sh --stage staging --model anthropic.claude-3-sonnet-20240229-v1:0
```

### Production
```bash
# Use Claude 3.5 Sonnet for best performance
bash scripts/full-deploy.sh --stage prod --model anthropic.claude-3-5-sonnet-20240620-v1:0
```

---

## Troubleshooting

### "Access Denied" Error

**Error:** `Access denied to model anthropic.claude-3-5-sonnet`

**Solution:**
1. Request model access in Bedrock Console (see above)
2. Wait for approval
3. Redeploy

### Model Not Found

**Error:** `Model not found: anthropic.claude-3-5-sonnet-20240620-v1:0`

**Solution:**
- Check model ID spelling
- Verify model is available in your region
- Some models may not be available in all regions

### Wrong Model in Use

**Check current model:**
```bash
aws bedrock-agent get-agent --agent-id YOUR_AGENT_ID \
  --query 'agent.foundationModel'
```

**Update model:**
```bash
bash scripts/full-deploy.sh --model NEW_MODEL_ID --skip-populate
```

---

## Examples

### Quick Development Deployment
```bash
# Fast and cheap for testing
bash scripts/full-deploy.sh --model anthropic.claude-3-haiku-20240307-v1:0
```

### Production Deployment
```bash
# Best performance
bash scripts/full-deploy.sh \
  --stage prod \
  --model anthropic.claude-3-5-sonnet-20240620-v1:0
```

### Switch Model Only
```bash
# Change model without repopulating database
bash scripts/full-deploy.sh \
  --model anthropic.claude-3-5-sonnet-20240620-v1:0 \
  --skip-populate
```

### Test Different Models
```bash
# Deploy with Haiku
bash scripts/full-deploy.sh --model anthropic.claude-3-haiku-20240307-v1:0

# Test performance
npm run test:integration

# Switch to Sonnet
bash scripts/full-deploy.sh --model anthropic.claude-3-sonnet-20240229-v1:0 --skip-populate

# Test again
npm run test:integration

# Compare results
```

---

## Summary

**Default Model:** Claude 3 Sonnet  
**Recommended Model:** Claude 3.5 Sonnet  
**Fastest Model:** Claude 3 Haiku  
**Most Capable:** Claude 3 Opus  

**Change Model:**
```bash
bash scripts/full-deploy.sh --model MODEL_ID
```

**See all options:**
```bash
bash scripts/full-deploy.sh --help
```
