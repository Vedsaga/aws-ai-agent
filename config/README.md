# Configuration Management

This directory contains configuration files for the Multi-Agent Orchestration System.

## Files

### `deployment.json`
Contains deployment-specific configuration:
- AWS region
- Deployment stage (dev, staging, prod)
- Project name and stack prefix
- Resource tags

**Usage:**
```python
import json
with open('config/deployment.json') as f:
    config = json.load(f)
    region = config['region']
    stage = config['stage']
```

### `models.json`
Contains Bedrock model configurations:
- Model IDs for different use cases
- Model parameters (max tokens, temperature)
- Model descriptions

**Usage:**
```python
import json
with open('config/models.json') as f:
    models = json.load(f)
    default_model = models['bedrock']['defaultModel']
```

### `lambda-defaults.json`
Contains default Lambda function configurations:
- Runtime version
- Timeout and memory settings
- Handler-specific overrides
- Environment variables

**Usage in CDK:**
```typescript
import * as fs from 'fs';
const lambdaConfig = JSON.parse(fs.readFileSync('config/lambda-defaults.json', 'utf8'));

new lambda.Function(this, 'MyFunction', {
  runtime: lambda.Runtime.PYTHON_3_11,
  timeout: cdk.Duration.seconds(lambdaConfig.timeout),
  memorySize: lambdaConfig.memorySize,
});
```

## Environment Variables

Sensitive configuration should be stored in environment variables, not in these JSON files.

See `.env.example` for required environment variables.

## Best Practices

1. **Never commit sensitive data** to these config files
2. **Use environment variables** for credentials and secrets
3. **Use AWS Secrets Manager** for production secrets
4. **Use AWS Systems Manager Parameter Store** for non-sensitive configuration
5. **Version control** these config files
6. **Document changes** when updating configurations

## Environment-Specific Configuration

For different environments, you can create:
- `deployment.dev.json`
- `deployment.staging.json`
- `deployment.prod.json`

Then load the appropriate file based on the `DEPLOYMENT_STAGE` environment variable:

```python
import os
import json

stage = os.environ.get('DEPLOYMENT_STAGE', 'dev')
config_file = f'config/deployment.{stage}.json'

with open(config_file) as f:
    config = json.load(f)
```

## Updating Configuration

When updating configuration:

1. Update the appropriate JSON file
2. Test changes in development environment
3. Update documentation if needed
4. Commit changes with descriptive message
5. Deploy to test environment first
6. Deploy to production after validation

## Security Notes

- Configuration files in this directory are **NOT encrypted**
- Do not store passwords, API keys, or tokens here
- Use AWS Secrets Manager for sensitive data
- Use environment variables for deployment-specific secrets
- Review configuration files regularly for security issues
