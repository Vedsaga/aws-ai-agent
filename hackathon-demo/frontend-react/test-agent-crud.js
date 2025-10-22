/**
 * Automated test script for Agent CRUD operations
 * Run with: node test-agent-crud.js
 * 
 * Prerequisites:
 * - Backend APIs must be deployed and accessible
 * - Valid JWT token must be provided
 * - Environment variables must be set
 */

const https = require('https');
const http = require('http');

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api-url.com';
const JWT_TOKEN = process.env.TEST_JWT_TOKEN || '';

if (!JWT_TOKEN) {
  console.error('❌ Error: TEST_JWT_TOKEN environment variable is required');
  console.log('Usage: TEST_JWT_TOKEN="your-token" node test-agent-crud.js');
  process.exit(1);
}

// Test results tracking
const results = {
  passed: 0,
  failed: 0,
  tests: []
};

// Helper function to make API requests
function apiRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, API_BASE_URL);
    const isHttps = url.protocol === 'https:';
    const lib = isHttps ? https : http;

    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${JWT_TOKEN}`
      }
    };

    if (body) {
      const bodyStr = JSON.stringify(body);
      options.headers['Content-Length'] = Buffer.byteLength(bodyStr);
    }

    const req = lib.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const parsed = data ? JSON.parse(data) : {};
          resolve({
            status: res.statusCode,
            data: parsed,
            headers: res.headers
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            data: data,
            headers: res.headers
          });
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

// Test helper functions
function assert(condition, message) {
  if (condition) {
    console.log(`  ✅ ${message}`);
    results.passed++;
  } else {
    console.log(`  ❌ ${message}`);
    results.failed++;
  }
  results.tests.push({ passed: condition, message });
}

function assertEqual(actual, expected, message) {
  const condition = actual === expected;
  assert(condition, `${message} (expected: ${expected}, got: ${actual})`);
}

function assertExists(value, message) {
  assert(value !== undefined && value !== null, message);
}

// Test suite
async function runTests() {
  console.log('🧪 Starting Agent CRUD Tests\n');
  console.log(`API Base URL: ${API_BASE_URL}\n`);

  let createdAgentId = null;

  // Test 1: List all agents
  console.log('Test 1: List all agents');
  try {
    const response = await apiRequest('GET', '/config?type=agent');
    assertEqual(response.status, 200, 'Status code should be 200');
    assertExists(response.data.agents, 'Response should contain agents array');
    
    if (response.data.agents) {
      const builtinCount = response.data.agents.filter(a => a.is_builtin).length;
      const customCount = response.data.agents.filter(a => !a.is_builtin).length;
      console.log(`  ℹ️  Found ${response.data.agents.length} total agents (${builtinCount} built-in, ${customCount} custom)`);
      assert(builtinCount >= 17, 'Should have at least 17 built-in agents');
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    results.failed++;
  }
  console.log('');

  // Test 2: Create custom ingestion agent
  console.log('Test 2: Create custom ingestion agent');
  try {
    const agentConfig = {
      agent_name: 'Test Ingest Agent ' + Date.now(),
      agent_type: 'ingestion',
      system_prompt: 'Extract priority level from civic complaints',
      tools: ['bedrock', 'comprehend'],
      output_schema: {
        priority: { type: 'string', required: true },
        confidence: { type: 'number', required: true }
      }
    };

    const response = await apiRequest('POST', '/config', {
      type: 'agent',
      config: agentConfig
    });

    assertEqual(response.status, 200, 'Status code should be 200');
    assertExists(response.data.agent_id, 'Response should contain agent_id');
    
    if (response.data.agent_id) {
      createdAgentId = response.data.agent_id;
      console.log(`  ℹ️  Created agent with ID: ${createdAgentId}`);
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    results.failed++;
  }
  console.log('');

  // Test 3: Get specific agent
  if (createdAgentId) {
    console.log('Test 3: Get specific agent');
    try {
      const response = await apiRequest('GET', `/config/agent/${createdAgentId}`);
      assertEqual(response.status, 200, 'Status code should be 200');
      assertExists(response.data.agent_name, 'Response should contain agent_name');
      assertEqual(response.data.agent_type, 'ingestion', 'Agent type should be ingestion');
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      results.failed++;
    }
    console.log('');
  }

  // Test 4: Update agent
  if (createdAgentId) {
    console.log('Test 4: Update agent');
    try {
      const updatedConfig = {
        agent_name: 'Updated Test Agent',
        agent_type: 'ingestion',
        system_prompt: 'Extract priority level and urgency from civic complaints',
        tools: ['bedrock', 'comprehend'],
        output_schema: {
          priority: { type: 'string', required: true },
          urgency: { type: 'string', required: true },
          confidence: { type: 'number', required: true }
        }
      };

      const response = await apiRequest('PUT', `/config/agent/${createdAgentId}`, updatedConfig);
      assertEqual(response.status, 200, 'Status code should be 200');
      
      // Verify update
      const getResponse = await apiRequest('GET', `/config/agent/${createdAgentId}`);
      assertEqual(getResponse.data.agent_name, 'Updated Test Agent', 'Agent name should be updated');
      assertExists(getResponse.data.output_schema.urgency, 'New field should exist in schema');
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
      results.failed++;
    }
    console.log('');
  }

  // Test 5: Create query agent with parent
  console.log('Test 5: Create query agent with parent');
  let queryAgentId = null;
  try {
    const queryConfig = {
      agent_name: 'Test Query Agent ' + Date.now(),
      agent_type: 'query',
      system_prompt: 'Analyze temporal patterns in incidents',
      tools: ['bedrock', 'retrieval_api'],
      output_schema: {
        pattern: { type: 'string', required: true },
        insight: { type: 'string', required: true }
      },
      dependency_parent: 'when_agent'
    };

    const response = await apiRequest('POST', '/config', {
      type: 'agent',
      config: queryConfig
    });

    assertEqual(response.status, 200, 'Status code should be 200');
    assertExists(response.data.agent_id, 'Response should contain agent_id');
    
    if (response.data.agent_id) {
      queryAgentId = response.data.agent_id;
      console.log(`  ℹ️  Created query agent with ID: ${queryAgentId}`);
      
      // Verify parent relationship
      const getResponse = await apiRequest('GET', `/config/agent/${queryAgentId}`);
      assertEqual(getResponse.data.dependency_parent, 'when_agent', 'Parent agent should be set');
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    results.failed++;
  }
  console.log('');

  // Test 6: Delete agents
  console.log('Test 6: Delete custom agents');
  try {
    if (createdAgentId) {
      const response1 = await apiRequest('DELETE', `/config/agent/${createdAgentId}`);
      assert(response1.status === 200 || response1.status === 204, 'Delete should succeed for custom agent');
      console.log(`  ℹ️  Deleted agent: ${createdAgentId}`);
    }

    if (queryAgentId) {
      const response2 = await apiRequest('DELETE', `/config/agent/${queryAgentId}`);
      assert(response2.status === 200 || response2.status === 204, 'Delete should succeed for query agent');
      console.log(`  ℹ️  Deleted agent: ${queryAgentId}`);
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    results.failed++;
  }
  console.log('');

  // Test 7: Verify built-in agents cannot be deleted
  console.log('Test 7: Verify built-in agents cannot be deleted');
  try {
    const listResponse = await apiRequest('GET', '/config?type=agent');
    const builtinAgent = listResponse.data.agents.find(a => a.is_builtin);
    
    if (builtinAgent) {
      const deleteResponse = await apiRequest('DELETE', `/config/agent/${builtinAgent.agent_id}`);
      assert(deleteResponse.status === 403 || deleteResponse.status === 400, 
        'Delete should fail for built-in agent');
      console.log(`  ℹ️  Correctly prevented deletion of built-in agent: ${builtinAgent.agent_name}`);
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    results.failed++;
  }
  console.log('');

  // Print summary
  console.log('═'.repeat(60));
  console.log('Test Summary');
  console.log('═'.repeat(60));
  console.log(`Total Tests: ${results.passed + results.failed}`);
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`Success Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);
  console.log('═'.repeat(60));

  if (results.failed > 0) {
    console.log('\n❌ Some tests failed. Please review the output above.');
    process.exit(1);
  } else {
    console.log('\n✅ All tests passed!');
    process.exit(0);
  }
}

// Run the tests
runTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
