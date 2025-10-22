import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export class AuthStack extends cdk.Stack {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;
  public readonly authorizerFunction: lambda.Function;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Cognito User Pool with password policies
    this.userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: `${id}-UserPool`,
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
        username: true,
      },
      autoVerify: {
        email: true,
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      mfa: cognito.Mfa.OPTIONAL,
      mfaSecondFactor: {
        sms: true,
        otp: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
      customAttributes: {
        tenant_id: new cognito.StringAttribute({ mutable: true }),
      },
    });

    // User Pool Client with JWT token settings
    this.userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool: this.userPool,
      userPoolClientName: `${id}-Client`,
      generateSecret: false,
      authFlows: {
        userPassword: true,
        userSrp: true,
        custom: true,
      },
      accessTokenValidity: cdk.Duration.hours(1), // 1 hour access token
      idTokenValidity: cdk.Duration.hours(1),
      refreshTokenValidity: cdk.Duration.days(30), // 30 day refresh token
      preventUserExistenceErrors: true,
      enableTokenRevocation: true,
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
          implicitCodeGrant: false,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
      },
    });

    // Lambda Authorizer Function - using regular Function with bundled dependencies
    // Note: We can't use PythonFunction here because it requires docker and poetry
    // Instead, we'll create a layer with the dependencies
    const authorizerLayer = new lambda.LayerVersion(this, 'AuthorizerLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/authorizer'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output/python && cp *.py /asset-output/python/'
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      description: 'PyJWT and dependencies for authorizer',
    });

    this.authorizerFunction = new lambda.Function(this, 'AuthorizerFunction', {
      functionName: `${id}-Authorizer`,
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'authorizer.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/authorizer')),
      layers: [authorizerLayer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        USER_POOL_ID: this.userPool.userPoolId,
        USER_POOL_CLIENT_ID: this.userPoolClient.userPoolClientId,
        REGION: this.region,
      },
      description: 'Lambda authorizer for API Gateway JWT validation',
    });

    // Grant permissions to the authorizer to access Cognito
    this.authorizerFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'cognito-idp:GetUser',
          'cognito-idp:AdminGetUser',
        ],
        resources: [this.userPool.userPoolArn],
      })
    );

    // Outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: this.userPool.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: `${id}-UserPoolId`,
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: this.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
      exportName: `${id}-UserPoolClientId`,
    });

    new cdk.CfnOutput(this, 'AuthorizerFunctionArn', {
      value: this.authorizerFunction.functionArn,
      description: 'Lambda Authorizer Function ARN',
      exportName: `${id}-AuthorizerFunctionArn`,
    });

    // Store configuration in SSM Parameter Store
    new cdk.aws_ssm.StringParameter(this, 'UserPoolIdParameter', {
      parameterName: '/app/cognito/user-pool-id',
      stringValue: this.userPool.userPoolId,
      description: 'Cognito User Pool ID',
    });

    new cdk.aws_ssm.StringParameter(this, 'UserPoolClientIdParameter', {
      parameterName: '/app/cognito/user-pool-client-id',
      stringValue: this.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
    });
  }
}
