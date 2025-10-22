#!/usr/bin/env node

/**
 * API Connectivity Test Script
 * Tests all API endpoints to verify they're accessible
 */

// Load API URL from environment variable
const API_BASE_URL = process.env.API_BASE_URL;

if (!API_BASE_URL) {
  console.error('❌ ERROR: API_BASE_URL environment variable not set');
  console.error('Please set it in your .env file or export it');
  process.exit(1);
}

async function testEndpoint(name, endpoint, options = {}) {
  console.log(`\nTesting: ${name}`);
  console.log(`URL: ${API_BASE_URL}${endpoint}`);
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    console.log(`Status: ${response.status} ${response.statusText}`);
    
    const data = await response.json();
    console.log(`Response:`, JSON.stringify(data, null, 2).substring(0, 500));
    
    return { success: response.ok, status: response.status, data };
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log('='.repeat(60));
  console.log('API Connectivity Test');
  console.log('='.repeat(60));
  
  // Test 1: Get domains
  await testEndpoint(
    'Get Domains',
    '/config?type=domain_template'
  );
  
  // Test 2: Get agents
  await testEndpoint(
    'Get Agents',
    '/config?type=agent'
  );
  
  // Test 3: Get incidents
  await testEndpoint(
    'Get Incidents',
    '/data?type=retrieval&filters={}'
  );
  
  console.log('\n' + '='.repeat(60));
  console.log('Tests Complete');
  console.log('='.repeat(60));
}

runTests();
