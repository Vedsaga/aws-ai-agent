#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CommandCenterBackendStack } from '../lib/command-center-backend-stack';
import { getEnvironmentConfig } from '../config/environment';

const app = new cdk.App();

const config = getEnvironmentConfig();

new CommandCenterBackendStack(app, config.stackName, {
  env: {
    account: config.account,
    region: config.region,
  },
  config,
  description: `Command Center Backend API - ${config.stage} environment`,
  tags: {
    Environment: config.stage,
    Project: 'CommandCenter',
    ManagedBy: 'CDK',
  },
});

app.synth();
