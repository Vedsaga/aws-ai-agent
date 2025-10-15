export interface EnvironmentConfig {
  account?: string;
  region: string;
  stage: 'dev' | 'staging' | 'prod';
  stackName: string;
  costAlertThreshold: number;
  costAlertEmail: string;
}

export const getEnvironmentConfig = (): EnvironmentConfig => {
  const stage = (process.env.STAGE || 'dev') as 'dev' | 'staging' | 'prod';
  
  const configs: Record<string, EnvironmentConfig> = {
    dev: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'dev',
      stackName: 'CommandCenterBackend-Dev',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
    },
    staging: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'staging',
      stackName: 'CommandCenterBackend-Staging',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
    },
    prod: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
      stage: 'prod',
      stackName: 'CommandCenterBackend-Prod',
      costAlertThreshold: 50,
      costAlertEmail: process.env.COST_ALERT_EMAIL || 'admin@example.com',
    },
  };

  return configs[stage];
};
