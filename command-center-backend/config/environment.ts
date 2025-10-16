export interface EnvironmentConfig {
  account?: string;
  region: string;
  stage: 'dev' | 'staging' | 'prod';
  stackName: string;
  costAlertThreshold: number;
  costAlertEmail: string;
  bedrockModel: string;
}

export const getEnvironmentConfig = (): EnvironmentConfig => {
  const stage = (process.env.STAGE || 'dev') as 'dev' | 'staging' | 'prod';

  // Default Bedrock model - can be overridden via BEDROCK_MODEL env var
  const defaultModel = 'anthropic.claude-3-sonnet-20240229-v1:0';
  const bedrockModel = process.env.BEDROCK_MODEL || defaultModel;

  const configs: Record<string, EnvironmentConfig> = {
    dev: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'dev',
      stackName: 'CommandCenterBackend-Dev',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
      bedrockModel,
    },
    staging: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'staging',
      stackName: 'CommandCenterBackend-Staging',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
      bedrockModel,
    },
    prod: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'prod',
      stackName: 'CommandCenterBackend-Prod',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
      bedrockModel,
    },
  };

  return configs[stage];
};
