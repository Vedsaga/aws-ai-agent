import { Amplify } from 'aws-amplify';

export const configureAmplify = () => {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || '',
        userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || '',
        identityPoolId: process.env.NEXT_PUBLIC_IDENTITY_POOL_ID || '',
        loginWith: {
          email: true,
        },
        signUpVerificationMethod: 'code',
        userAttributes: {
          email: {
            required: true,
          },
        },
        allowGuestAccess: false,
        passwordFormat: {
          minLength: 8,
          requireLowercase: true,
          requireUppercase: true,
          requireNumbers: true,
          requireSpecialCharacters: true,
        },
      },
    },
    API: {
      REST: {
        'multi-agent-api': {
          endpoint: process.env.NEXT_PUBLIC_API_URL || '',
          region: process.env.NEXT_PUBLIC_COGNITO_REGION || 'us-east-1',
        },
      },
      GraphQL: {
        endpoint: process.env.NEXT_PUBLIC_APPSYNC_URL || '',
        region: process.env.NEXT_PUBLIC_APPSYNC_REGION || 'us-east-1',
        defaultAuthMode: 'userPool',
      },
    },
  });
};
