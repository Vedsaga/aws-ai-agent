// getToken.js
const AWS = require('aws-sdk');

const USER_POOL_ID = 'us-east-1_7QZ7Y6Gbl';
const CLIENT_ID = '6gobbpage9af3nd7ahm3lchkct';
const REGION = 'us-east-1';
const username = 'testuser';
const password = 'TestPassword123!';

const cognito = new AWS.CognitoIdentityServiceProvider({ region: REGION });

const params = {
    AuthFlow: 'USER_PASSWORD_AUTH',
    ClientId: CLIENT_ID,
    AuthParameters: {
        USERNAME: username,
        PASSWORD: password,
    },
};

cognito.initiateAuth(params, (err, data) => {
    if (err) {
        console.error("Authentication failed:", err);
        process.exit(1);
    } else {
        console.log(data.AuthenticationResult.IdToken);
    }
});
