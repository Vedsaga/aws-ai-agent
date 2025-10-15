/**
 * Integration Test Suite for Command Center Backend API
 * 
 * Tests all API endpoints with various query parameters and payloads
 * Verifies response formats match data contracts
 * Tests error scenarios
 */

import axios from 'axios';

// Type for axios errors
interface AxiosError {
  response?: {
    status?: number;
    data?: any;
  };
  message: string;
}

// Configuration
const API_ENDPOINT = process.env.API_ENDPOINT || '';
const API_KEY = process.env.API_KEY || '';

if (!API_ENDPOINT) {
  console.error('Error: API_ENDPOINT environment variable is required');
  process.exit(1);
}

// Test utilities
interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
}

const results: TestResult[] = [];

async function runTest(name: string, testFn: () => Promise<void>): Promise<void> {
  const startTime = Date.now();
  try {
    await testFn();
    results.push({
      name,
      passed: true,
      duration: Date.now() - startTime
    });
    console.log(`✓ ${name}`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    results.push({
      name,
      passed: false,
      error: errorMessage,
      duration: Date.now() - startTime
    });
    console.error(`✗ ${name}`);
    console.error(`  Error: ${errorMessage}`);
  }
}

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function assertExists(value: any, fieldName: string): void {
  assert(value !== undefined && value !== null, `${fieldName} should exist`);
}

function assertType(value: any, expectedType: string, fieldName: string): void {
  const actualType = Array.isArray(value) ? 'array' : typeof value;
  assert(actualType === expectedType, `${fieldName} should be ${expectedType}, got ${actualType}`);
}

// Test Suite
async function testUpdatesEndpoint() {
  console.log('\n=== Testing GET /data/updates ===\n');

  // Test 1: Basic request with since parameter
  await runTest('GET /data/updates with since parameter', async () => {
    const response = await axios.get(`${API_ENDPOINT}/data/updates`, {
      params: { since: '2023-02-06T00:00:00Z' },
      headers: API_KEY ? { 'x-api-key': API_KEY } : {}
    });

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data, 'Response data');
    assertExists(data.latestTimestamp, 'latestTimestamp');
    assertType(data.latestTimestamp, 'string', 'latestTimestamp');
  });

  // Test 2: Request with domain filter
  await runTest('GET /data/updates with domain filter', async () => {
    const response = await axios.get(`${API_ENDPOINT}/data/updates`, {
      params: {
        since: '2023-02-06T00:00:00Z',
        domain: 'MEDICAL'
      },
      headers: API_KEY ? { 'x-api-key': API_KEY } : {}
    });

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data, 'Response data');

    // If mapUpdates exist, verify structure
    if (data.mapUpdates) {
      assertType(data.mapUpdates.mapLayers, 'array', 'mapLayers');
      assert(
        data.mapUpdates.mapAction === 'APPEND' ||
        data.mapUpdates.mapAction === 'REPLACE',
        'mapAction should be APPEND or REPLACE'
      );
    }
  });

  // Test 3: Request with all valid domains
  const domains = ['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION'];
  for (const domain of domains) {
    await runTest(`GET /data/updates with domain=${domain}`, async () => {
      const response = await axios.get(`${API_ENDPOINT}/data/updates`, {
        params: {
          since: '2023-02-06T00:00:00Z',
          domain
        },
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      });

      assert(response.status === 200, `Status should be 200 for domain ${domain}`);
    });
  }

  // Test 4: Error - missing since parameter
  await runTest('GET /data/updates without since parameter (error case)', async () => {
    try {
      await axios.get(`${API_ENDPOINT}/data/updates`, {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      });
      throw new Error('Should have thrown an error');
    } catch (error) {
      const axiosError = error as AxiosError;
      assert(
        axiosError.response?.status === 400 || axiosError.response?.status === 422,
        'Status should be 400 or 422 for missing parameter'
      );
    }
  });

  // Test 5: Error - invalid domain
  await runTest('GET /data/updates with invalid domain (error case)', async () => {
    try {
      await axios.get(`${API_ENDPOINT}/data/updates`, {
        params: {
          since: '2023-02-06T00:00:00Z',
          domain: 'INVALID_DOMAIN'
        },
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      });
      throw new Error('Should have thrown an error');
    } catch (error) {
      const axiosError = error as AxiosError;
      assert(
        axiosError.response?.status === 400 || axiosError.response?.status === 422,
        'Status should be 400 or 422 for invalid domain'
      );
    }
  });

  // Test 6: Verify mapLayers structure when present
  await runTest('GET /data/updates - verify mapLayers structure', async () => {
    const response = await axios.get(`${API_ENDPOINT}/data/updates`, {
      params: { since: '2023-02-06T00:00:00Z' },
      headers: API_KEY ? { 'x-api-key': API_KEY } : {}
    });

    const data: any = response.data;
    if (data.mapUpdates?.mapLayers) {
      const layers = data.mapUpdates.mapLayers;
      assertType(layers, 'array', 'mapLayers');

      if (layers.length > 0) {
        const layer = layers[0];
        assertExists(layer.layerId, 'layer.layerId');
        assertExists(layer.layerName, 'layer.layerName');
        assertExists(layer.geometryType, 'layer.geometryType');
        assertExists(layer.style, 'layer.style');
        assertExists(layer.data, 'layer.data');
        assertType(layer.data, 'object', 'layer.data');
        assert(layer.data.type === 'FeatureCollection', 'layer.data should be GeoJSON FeatureCollection');
      }
    }
  });
}

async function testQueryEndpoint() {
  console.log('\n=== Testing POST /agent/query ===\n');

  // Test 1: Basic natural language query
  await runTest('POST /agent/query with simple question', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/query`,
      {
        text: 'What are the critical medical incidents?'
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data, 'Response data');
    assertExists(data.chatResponse, 'chatResponse');
    assertType(data.chatResponse, 'string', 'chatResponse');
    assertExists(data.mapAction, 'mapAction');
    assert(
      data.mapAction === 'APPEND' || data.mapAction === 'REPLACE',
      'mapAction should be APPEND or REPLACE'
    );
  });

  // Test 2: Query with session ID
  await runTest('POST /agent/query with sessionId', async () => {
    const sessionId = `test-session-${Date.now()}`;
    const response = await axios.post(
      `${API_ENDPOINT}/agent/query`,
      {
        text: 'Show me fire incidents',
        sessionId
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data.chatResponse, 'chatResponse');
  });

  // Test 3: Query with current map state
  await runTest('POST /agent/query with currentMapState', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/query`,
      {
        text: 'What is happening in this area?',
        currentMapState: {
          center: [37.5, 37.0],
          zoom: 12
        }
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data.chatResponse, 'chatResponse');
  });

  // Test 4: Verify full response structure
  await runTest('POST /agent/query - verify full response structure', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/query`,
      {
        text: 'Show all structural damage'
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    const data: any = response.data;
    assertExists(data.simulationTime, 'simulationTime');
    assertExists(data.timestamp, 'timestamp');
    assertExists(data.chatResponse, 'chatResponse');
    assertExists(data.mapAction, 'mapAction');
    assertExists(data.mapLayers, 'mapLayers');
    assertType(data.mapLayers, 'array', 'mapLayers');

    // Optional fields
    if (data.viewState) {
      assertType(data.viewState, 'object', 'viewState');
    }
    if (data.uiContext) {
      assertType(data.uiContext, 'object', 'uiContext');
    }
  });

  // Test 5: Error - missing text parameter
  await runTest('POST /agent/query without text (error case)', async () => {
    try {
      await axios.post(
        `${API_ENDPOINT}/agent/query`,
        {},
        {
          headers: API_KEY ? { 'x-api-key': API_KEY } : {}
        }
      );
      throw new Error('Should have thrown an error');
    } catch (error) {
      const axiosError = error as AxiosError;
      assert(
        axiosError.response?.status === 400 || axiosError.response?.status === 422,
        'Status should be 400 or 422 for missing text'
      );
    }
  });

  // Test 6: Error - empty text
  await runTest('POST /agent/query with empty text (error case)', async () => {
    try {
      await axios.post(
        `${API_ENDPOINT}/agent/query`,
        { text: '' },
        {
          headers: API_KEY ? { 'x-api-key': API_KEY } : {}
        }
      );
      throw new Error('Should have thrown an error');
    } catch (error) {
      const axiosError = error as AxiosError;
      assert(
        axiosError.response?.status === 400 || axiosError.response?.status === 422,
        'Status should be 400 or 422 for empty text'
      );
    }
  });
}

async function testActionEndpoint() {
  console.log('\n=== Testing POST /agent/action ===\n');

  // Test 1: Basic action request
  await runTest('POST /agent/action with valid actionId', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/action`,
      {
        actionId: 'SHOW_CRITICAL_INCIDENTS'
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data, 'Response data');
    assertExists(data.chatResponse, 'chatResponse');
    assertExists(data.mapAction, 'mapAction');
  });

  // Test 2: Action with payload
  await runTest('POST /agent/action with payload', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/action`,
      {
        actionId: 'GENERATE_AREA_BRIEFING',
        payload: {
          area: 'Nurdağı',
          includeResources: true
        }
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data.chatResponse, 'chatResponse');
  });

  // Test 3: Verify response structure matches query endpoint
  await runTest('POST /agent/action - verify response structure', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/action`,
      {
        actionId: 'SHOW_MEDICAL_NEEDS'
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    // Should have same structure as query endpoint
    const data: any = response.data;
    assertExists(data.simulationTime, 'simulationTime');
    assertExists(data.timestamp, 'timestamp');
    assertExists(data.chatResponse, 'chatResponse');
    assertExists(data.mapAction, 'mapAction');
    assertExists(data.mapLayers, 'mapLayers');
    assertType(data.mapLayers, 'array', 'mapLayers');
  });

  // Test 4: Error - missing actionId
  await runTest('POST /agent/action without actionId (error case)', async () => {
    try {
      await axios.post(
        `${API_ENDPOINT}/agent/action`,
        {},
        {
          headers: API_KEY ? { 'x-api-key': API_KEY } : {}
        }
      );
      throw new Error('Should have thrown an error');
    } catch (error) {
      const axiosError = error as AxiosError;
      assert(
        axiosError.response?.status === 400 || axiosError.response?.status === 422,
        'Status should be 400 or 422 for missing actionId'
      );
    }
  });

  // Test 5: Invalid actionId (should still work but may return error message)
  await runTest('POST /agent/action with unknown actionId', async () => {
    const response = await axios.post(
      `${API_ENDPOINT}/agent/action`,
      {
        actionId: 'UNKNOWN_ACTION_12345'
      },
      {
        headers: API_KEY ? { 'x-api-key': API_KEY } : {}
      }
    );

    // Should return 200 but with error message in chatResponse
    assert(response.status === 200, 'Status should be 200');
    const data: any = response.data;
    assertExists(data.chatResponse, 'chatResponse');
  });
}

async function testCORS() {
  console.log('\n=== Testing CORS Configuration ===\n');

  await runTest('OPTIONS request returns CORS headers', async () => {
    const response = await axios.request({
      method: 'OPTIONS',
      url: `${API_ENDPOINT}/data/updates`,
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET'
      }
    });

    assert(
      response.status === 200 || response.status === 204,
      'OPTIONS should return 200 or 204'
    );
    assertExists(response.headers['access-control-allow-origin'], 'CORS allow-origin header');
  });
}

// Main test runner
async function runAllTests() {
  console.log('='.repeat(60));
  console.log('Command Center Backend - Integration Test Suite');
  console.log('='.repeat(60));
  console.log(`API Endpoint: ${API_ENDPOINT}`);
  console.log(`API Key: ${API_KEY ? '***' + API_KEY.slice(-4) : 'Not provided'}`);
  console.log('');

  const startTime = Date.now();

  try {
    await testUpdatesEndpoint();
    await testQueryEndpoint();
    await testActionEndpoint();
    await testCORS();
  } catch (error) {
    console.error('\nUnexpected error during test execution:', error);
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);

  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('Test Summary');
  console.log('='.repeat(60));

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const total = results.length;

  console.log(`Total: ${total}`);
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  console.log(`Duration: ${duration}s`);
  console.log('');

  if (failed > 0) {
    console.log('Failed tests:');
    results.filter(r => !r.passed).forEach(r => {
      console.log(`  ✗ ${r.name}`);
      console.log(`    ${r.error}`);
    });
    console.log('');
  }

  // Exit with appropriate code
  process.exit(failed > 0 ? 1 : 0);
}

// Run tests
runAllTests();
