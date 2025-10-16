#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CommandCenterBackendStack } from '../lib/command-center-backend-stack';
import { getEnvironmentConfig } from '../config/environment';

const app = new cdk.App();

// Get environment configuration
const config = getEnvironmentConfig();

// Create the stack
new CommandCenterBackendStack(app, config.stackName, {
  config,
  env: {
    account: config.account || process.env.CDK_DEFAULT_ACCOUNT,
    region: config.region,
  },
  description: `Command Center Backend - ${config.stage} environment`,
});

app.synth();
