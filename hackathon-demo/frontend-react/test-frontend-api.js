/**
 * Frontend API Test Script
 * Tests API calls using the same method as the frontend application
 * Run with: node test-frontend-api.js
 */

const https = require('https');

// Load configuration from environment variables
const API_URL = process.env.API_BASE_URL;
const USER_POOL_ID = process.env.COGNITO_USER_POOL_ID;
const CLIENT_ID = process.env.COGNITO_CLIENT_ID;
const USERNAME = process.env.TEST_USERNAME || 'testuser';
const PASSWORD = process.env.TEST_PASSWORD;
const REGION = process.env.AWS_REGION || 'us-east-1';

// Validate required environment variables
if (!API_URL || !USER_POOL_ID || !CLIENT_ID || !PASSWORD) {
  console.error('❌ ERROR: Missing required environment variables');
  console.error('Required: API_BASE_URL, COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, TEST_PASSWORD');
  console.error('Please set these in your .env file or export them');
  process.exit(1);
}

// AWS SDK for authentication
const AWS = require('aws-sdk');
AWS.config.update({ region: REGION });

const cognito = new AWS.CognitoIdentityServiceProvider();

console.log('=========================================');
console.log('Frontend API Test Suite');
console.log('=========================================\n');
console.log(`API URL: ${API_URL}`);
console.log(`Username: ${USERNAME}\n`);

async function authenticate() {
  console.log('Step 1: Authenticating...');
  console.log('-------------------------');
  
  try {
    const params = {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: CLIENT_ID,
      AuthParameters: {
        USERNAME: USERNAME,
        PASSWORD: PASSWORD,
      },
    };
    
    const result = await cognito.initiateAuth(params).promise();
    const idToken = result.AuthenticationResult.IdToken;
    
    console.log('✅ PASS - Authentication successful');
    console.log(`   ID Token: ${idToken.substring(0, 50)}...\n`);
    
    return idToken;
  } catch (error) {
    console.log('❌ FAIL - Authentication failed');
    console.log(`   Error: ${error.message}\n`);
    throw error;
  }
}

function makeRequest(path, method, token, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_URL + path);
    
    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };
    
    if (body) {
      const bodyStr = JSON.stringify(body);
      options.headers['Content-Length'] = Buffer.byteLength(bodyStr);
    }
    
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ status: res.statusCode, data: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, data: data });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (body) {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

async function testListAgents(token) {
  console.log('Step 2: List Agents');
  console.log('-------------------------');
  
  try {
    const response = await makeRequest('/config?type=agent', 'GET', token);
    
    if (response.status === 200) {
      const agentCount = response.data.configs ? response.data.configs.length : 0;
      console.log('✅ PASS - Listed agents successfully');
      console.log(`   Agent count: ${agentCount}`);
      if (response.data.configs && response.data.configs[0]) {
        console.log(`   First agent: ${response.data.configs[0].agent_name || 'N/A'}`);
      }
      return response.data;
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
      return null;
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
    return null;
  } finally {
    console.log('');
  }
}

async function testListDomains(token) {
  console.log('Step 3: List Domains');
  console.log('-------------------------');
  
  try {
    const response = await makeRequest('/config?type=domain_template', 'GET', token);
    
    if (response.status === 200) {
      const domainCount = response.data.configs ? response.data.configs.length : 0;
      console.log('✅ PASS - Listed domains successfully');
      console.log(`   Domain count: ${domainCount}`);
      if (response.data.configs && response.data.configs[0]) {
        console.log(`   First domain: ${response.data.configs[0].template_name || 'N/A'}`);
      }
      return response.data;
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
      return null;
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
    return null;
  } finally {
    console.log('');
  }
}

async function testCreateAgent(token) {
  console.log('Step 4: Create Custom Agent');
  console.log('-------------------------');
  
  const agentConfig = {
    type: 'agent',
    config: {
      agent_name: 'Test Priority Agent',
      agent_type: 'ingestion',
      system_prompt: 'Extract priority level from civic complaints.',
      tools: ['bedrock'],
      output_schema: {
        priority: { type: 'string', required: true },
        urgency_score: { type: 'number', required: true },
        confidence: { type: 'number', required: true },
      },
    },
  };
  
  try {
    const response = await makeRequest('/config', 'POST', token, agentConfig);
    
    if (response.status === 200 || response.status === 201) {
      const agentId = response.data.config_id || response.data.agent_id || response.data.id;
      console.log('✅ PASS - Created agent successfully');
      console.log(`   Agent ID: ${agentId}`);
      return agentId;
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
      return null;
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
    return null;
  } finally {
    console.log('');
  }
}

async function testDeleteAgent(token, agentId) {
  console.log('Step 5: Delete Test Agent');
  console.log('-------------------------');
  
  try {
    const response = await makeRequest(`/config/agent/${agentId}`, 'DELETE', token);
    
    if (response.status === 200 || response.status === 204) {
      console.log('✅ PASS - Deleted agent successfully');
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
  } finally {
    console.log('');
  }
}

async function testSubmitReport(token, domainId) {
  console.log('Step 6: Submit Report (Ingestion)');
  console.log('-------------------------');
  
  const payload = {
    domain_id: domainId,
    text: 'Traffic accident at Main Street and 5th Avenue at 3pm today.',
    images: [],
  };
  
  try {
    const response = await makeRequest('/ingest', 'POST', token, payload);
    
    if (response.status === 200 || response.status === 202) {
      const jobId = response.data.job_id;
      console.log('✅ PASS - Submitted report successfully');
      console.log(`   Job ID: ${jobId}`);
      console.log(`   Status: ${response.data.status}`);
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
  } finally {
    console.log('');
  }
}

async function testSubmitQuery(token, domainId) {
  console.log('Step 7: Submit Query');
  console.log('-------------------------');
  
  const payload = {
    domain_id: domainId,
    question: 'What traffic incidents happened today?',
  };
  
  try {
    const response = await makeRequest('/query', 'POST', token, payload);
    
    if (response.status === 200 || response.status === 202) {
      const jobId = response.data.job_id;
      console.log('✅ PASS - Submitted query successfully');
      console.log(`   Job ID: ${jobId}`);
      console.log(`   Status: ${response.data.status}`);
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
  } finally {
    console.log('');
  }
}

async function testFetchData(token) {
  console.log('Step 8: Fetch Incidents Data');
  console.log('-------------------------');
  
  try {
    const response = await makeRequest('/data?type=retrieval&limit=5', 'GET', token);
    
    if (response.status === 200) {
      const incidentCount = response.data.data ? response.data.data.length : 0;
      console.log('✅ PASS - Fetched data successfully');
      console.log(`   Incident count: ${incidentCount}`);
    } else {
      console.log(`❌ FAIL - HTTP ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}`);
    }
  } catch (error) {
    console.log(`❌ FAIL - ${error.message}`);
  } finally {
    console.log('');
  }
}

async function runTests() {
  try {
    // Authenticate
    const token = await authenticate();
    
    // Test listing agents
    const agentsData = await testListAgents(token);
    
    // Test listing domains
    const domainsData = await testListDomains(token);
    
    // Test creating an agent
    const createdAgentId = await testCreateAgent(token);
    
    // Test submitting a report (if we have a domain)
    if (domainsData && domainsData.configs && domainsData.configs[0]) {
      const domainId = domainsData.configs[0].domain_id || domainsData.configs[0].id;
      await testSubmitReport(token, domainId);
      await testSubmitQuery(token, domainId);
    }
    
    // Test fetching data
    await testFetchData(token);
    
    // Clean up - delete test agent
    if (createdAgentId) {
      await testDeleteAgent(token, createdAgentId);
    }
    
    console.log('=========================================');
    console.log('Test Suite Complete');
    console.log('=========================================\n');
    
  } catch (error) {
    console.error('Test suite failed:', error);
    process.exit(1);
  }
}

// Run the tests
runTests();
