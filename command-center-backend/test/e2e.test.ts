/**
 * End-to-End Test Suite for Command Center Backend
 * 
 * This test suite validates the entire system integration including:
 * - API Gateway endpoints
 * - Lambda handlers
 * - DynamoDB queries
 * - Bedrock Agent integration (if deployed)
 * 
 * Prerequisites:
 * - Stack must be deployed
 * - Database must be populated with simulation data
 * - API key must be available
 * - Bedrock Agent must be configured
 */

import axios from 'axios';
import { 
  UpdatesResponse, 
  QueryResponse, 
  ActionResponse,
  ErrorResponse 
} from '../lib/types/api';

// Configuration from environment variables
const API_ENDPOINT = process.env.API_ENDPOINT || '';
const API_KEY = process.env.API_KEY || '';
const SKIP_AGENT_TESTS = process.env.SKIP_AGENT_TESTS === 'true';

// Test configuration
const TEST_TIMEOUT = 70000; // 70 seconds for agent tests
const SIMULATION_START = '2023-02-06T00:00:00Z';

// Axios client with API key
const apiClient = axios.create({
  baseURL: API_ENDPOINT,
  headers: {
    'x-api-key': API_KEY,
    'Content-Type': 'application/json',
  },
  timeout: 65000, // 65 seconds
  validateStatus: () => true, // Don't throw on any status
});

// Test results tracking
interface TestResult {
  name: string;
  passed: boolean;
  duration: number;
  error?: string;
  details?: any;
}

const testResults: TestResult[] = [];

function recordTest(name: string, passed: boolean, duration: number, error?: string, details?: any) {
  testResults.push({ name, passed, duration, error, details });
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status} - ${name} (${duration}ms)`);
  if (error) {
    console.log(`  Error: ${error}`);
  }
  if (details) {
    console.log(`  Details:`, JSON.stringify(details, null, 2));
  }
}

// Validation helpers
function validateUpdatesResponse(data: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!data.latestTimestamp) {
    errors.push('Missing latestTimestamp');
  }
  
  if (data.mapUpdates) {
    if (!data.mapUpdates.mapAction || !['APPEND', 'REPLACE'].includes(data.mapUpdates.mapAction)) {
      errors.push('Invalid or missing mapAction');
    }
    if (!Array.isArray(data.mapUpdates.mapLayers)) {
      errors.push('mapLayers must be an array');
    } else {
      data.mapUpdates.mapLayers.forEach((layer: any, idx: number) => {
        if (!layer.layerId) errors.push(`Layer ${idx}: missing layerId`);
        if (!layer.layerName) errors.push(`Layer ${idx}: missing layerName`);
        if (!layer.geometryType) errors.push(`Layer ${idx}: missing geometryType`);
        if (!layer.data || layer.data.type !== 'FeatureCollection') {
          errors.push(`Layer ${idx}: invalid GeoJSON FeatureCollection`);
        }
      });
    }
  }
  
  if (data.criticalAlerts && !Array.isArray(data.criticalAlerts)) {
    errors.push('criticalAlerts must be an array');
  }
  
  return { valid: errors.length === 0, errors };
}

function validateQueryResponse(data: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!data.simulationTime) errors.push('Missing simulationTime');
  if (!data.timestamp) errors.push('Missing timestamp');
  if (!data.chatResponse) errors.push('Missing chatResponse');
  if (!data.mapAction || !['APPEND', 'REPLACE'].includes(data.mapAction)) {
    errors.push('Invalid or missing mapAction');
  }
  if (!Array.isArray(data.mapLayers)) {
    errors.push('mapLayers must be an array');
  }
  
  return { valid: errors.length === 0, errors };
}

// Test Suite
async function runTests() {
  console.log('='.repeat(80));
  console.log('COMMAND CENTER BACKEND - END-TO-END TEST SUITE');
  console.log('='.repeat(80));
  console.log(`API Endpoint: ${API_ENDPOINT}`);
  console.log(`API Key: ${API_KEY ? '***' + API_KEY.slice(-4) : 'NOT SET'}`);
  console.log(`Skip Agent Tests: ${SKIP_AGENT_TESTS}`);
  console.log('='.repeat(80));
  console.log('');

  // Pre-flight checks
  if (!API_ENDPOINT) {
    console.error('❌ ERROR: API_ENDPOINT environment variable not set');
    console.error('Usage: API_ENDPOINT=https://xxx.execute-api.region.amazonaws.com/prod API_KEY=xxx npm run test:e2e');
    process.exit(1);
  }

  if (!API_KEY) {
    console.error('❌ ERROR: API_KEY environment variable not set');
    process.exit(1);
  }

  console.log('Starting tests...\n');

  // Test 1: GET /data/updates - Basic query
  await testUpdatesBasic();

  // Test 2: GET /data/updates - With domain filter
  await testUpdatesWithDomain();

  // Test 3: GET /data/updates - Invalid parameters
  await testUpdatesInvalidParams();

  // Test 4: GET /data/updates - Future timestamp (should return empty)
  await testUpdatesFutureTimestamp();

  // Test 5: GET /data/updates - Verify data structure
  await testUpdatesDataStructure();

  if (!SKIP_AGENT_TESTS) {
    // Test 6: POST /agent/query - Simple query
    await testQuerySimple();

    // Test 7: POST /agent/query - Complex query
    await testQueryComplex();

    // Test 8: POST /agent/query - Invalid request
    await testQueryInvalid();

    // Test 9: POST /agent/action - Pre-defined action
    await testActionExecution();

    // Test 10: POST /agent/action - Invalid action
    await testActionInvalid();

    // Test 11: POST /agent/query - With map context
    await testQueryWithMapContext();

    // Test 12: POST /agent/action - Multiple actions
    await testMultipleActions();
  } else {
    console.log('⏭️  Skipping Bedrock Agent tests (SKIP_AGENT_TESTS=true)\n');
  }

  // Print summary
  printSummary();
}

async function testUpdatesBasic() {
  const testName = 'GET /data/updates - Basic query';
  const start = Date.now();
  
  try {
    const response = await apiClient.get('/data/updates', {
      params: {
        since: SIMULATION_START,
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as UpdatesResponse;
    const validation = validateUpdatesResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '), data);
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      latestTimestamp: data.latestTimestamp,
      layerCount: data.mapUpdates?.mapLayers?.length || 0,
      alertCount: data.criticalAlerts?.length || 0,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testUpdatesWithDomain() {
  const testName = 'GET /data/updates - With domain filter (MEDICAL)';
  const start = Date.now();
  
  try {
    const response = await apiClient.get('/data/updates', {
      params: {
        since: SIMULATION_START,
        domain: 'MEDICAL',
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as UpdatesResponse;
    const validation = validateUpdatesResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '));
      return;
    }
    
    // Verify all layers are MEDICAL domain
    const layers = data.mapUpdates?.mapLayers || [];
    const nonMedicalLayers = layers.filter((l: any) => !l.layerId.includes('medical'));
    
    if (nonMedicalLayers.length > 0) {
      recordTest(testName, false, duration, 'Found non-MEDICAL layers in filtered response');
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      layerCount: layers.length,
      alertCount: data.criticalAlerts?.length || 0,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testUpdatesInvalidParams() {
  const testName = 'GET /data/updates - Invalid parameters';
  const start = Date.now();
  
  try {
    const response = await apiClient.get('/data/updates', {
      params: {
        since: 'invalid-timestamp',
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 400) {
      recordTest(testName, false, duration, `Expected 400, got ${response.status}`);
      return;
    }
    
    const errorData = response.data as ErrorResponse;
    if (!errorData.error || !errorData.error.code) {
      recordTest(testName, false, duration, 'Invalid error response structure');
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      errorCode: errorData.error.code,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testUpdatesFutureTimestamp() {
  const testName = 'GET /data/updates - Future timestamp (should return empty)';
  const start = Date.now();
  
  try {
    const futureDate = new Date('2025-01-01T00:00:00Z').toISOString();
    const response = await apiClient.get('/data/updates', {
      params: {
        since: futureDate,
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`);
      return;
    }
    
    const data = response.data as UpdatesResponse;
    const layerCount = data.mapUpdates?.mapLayers?.length || 0;
    const alertCount = data.criticalAlerts?.length || 0;
    
    if (layerCount > 0 || alertCount > 0) {
      recordTest(testName, false, duration, 'Expected empty response for future timestamp');
      return;
    }
    
    recordTest(testName, true, duration);
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testUpdatesDataStructure() {
  const testName = 'GET /data/updates - Verify GeoJSON structure';
  const start = Date.now();
  
  try {
    const response = await apiClient.get('/data/updates', {
      params: {
        since: SIMULATION_START,
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`);
      return;
    }
    
    const data = response.data as UpdatesResponse;
    const layers = data.mapUpdates?.mapLayers || [];
    
    if (layers.length === 0) {
      recordTest(testName, false, duration, 'No layers returned - database may be empty');
      return;
    }
    
    // Verify first layer has valid GeoJSON
    const firstLayer = layers[0];
    if (!firstLayer.data.features || !Array.isArray(firstLayer.data.features)) {
      recordTest(testName, false, duration, 'Invalid GeoJSON features array');
      return;
    }
    
    if (firstLayer.data.features.length === 0) {
      recordTest(testName, false, duration, 'No features in layer');
      return;
    }
    
    const firstFeature = firstLayer.data.features[0];
    if (!firstFeature.geometry || !firstFeature.properties) {
      recordTest(testName, false, duration, 'Invalid GeoJSON feature structure');
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      layerCount: layers.length,
      firstLayerFeatureCount: firstLayer.data.features.length,
      firstFeatureType: firstFeature.geometry.type,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testQuerySimple() {
  const testName = 'POST /agent/query - Simple query';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/query', {
      text: 'What are the critical incidents?',
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as QueryResponse;
    const validation = validateQueryResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '));
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      chatResponseLength: data.chatResponse.length,
      mapLayerCount: data.mapLayers.length,
      hasViewState: !!data.viewState,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testQueryComplex() {
  const testName = 'POST /agent/query - Complex query with filters';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/query', {
      text: 'Show me all critical medical incidents in the last 24 hours',
      sessionId: 'test-session-complex',
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as QueryResponse;
    const validation = validateQueryResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '));
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      chatResponseLength: data.chatResponse.length,
      mapLayerCount: data.mapLayers.length,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testQueryInvalid() {
  const testName = 'POST /agent/query - Invalid request (missing text)';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/query', {
      sessionId: 'test-session',
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 400) {
      recordTest(testName, false, duration, `Expected 400, got ${response.status}`);
      return;
    }
    
    const errorData = response.data as ErrorResponse;
    if (!errorData.error || !errorData.error.code) {
      recordTest(testName, false, duration, 'Invalid error response structure');
      return;
    }
    
    recordTest(testName, true, duration);
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testActionExecution() {
  const testName = 'POST /agent/action - Execute SHOW_CRITICAL_MEDICAL';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/action', {
      actionId: 'SHOW_CRITICAL_MEDICAL',
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as QueryResponse;
    const validation = validateQueryResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '));
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      chatResponseLength: data.chatResponse.length,
      mapLayerCount: data.mapLayers.length,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testActionInvalid() {
  const testName = 'POST /agent/action - Invalid action ID';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/action', {
      actionId: 'INVALID_ACTION_ID',
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 400) {
      recordTest(testName, false, duration, `Expected 400, got ${response.status}`);
      return;
    }
    
    const errorData = response.data as ErrorResponse;
    if (!errorData.error || errorData.error.code !== 'INVALID_ACTION') {
      recordTest(testName, false, duration, 'Expected INVALID_ACTION error code');
      return;
    }
    
    recordTest(testName, true, duration);
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testQueryWithMapContext() {
  const testName = 'POST /agent/query - With map context';
  const start = Date.now();
  
  try {
    const response = await apiClient.post('/agent/query', {
      text: 'What incidents are in this area?',
      currentMapState: {
        center: [37.15, 37.12],
        zoom: 12,
      },
    });
    
    const duration = Date.now() - start;
    
    if (response.status !== 200) {
      recordTest(testName, false, duration, `Expected 200, got ${response.status}`, response.data);
      return;
    }
    
    const data = response.data as QueryResponse;
    const validation = validateQueryResponse(data);
    if (!validation.valid) {
      recordTest(testName, false, duration, validation.errors.join(', '));
      return;
    }
    
    recordTest(testName, true, duration);
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

async function testMultipleActions() {
  const testName = 'POST /agent/action - Multiple sequential actions';
  const start = Date.now();
  
  try {
    const actions = ['SHOW_FIRE_INCIDENTS', 'SHOW_STRUCTURAL_DAMAGE', 'HELP'];
    let allPassed = true;
    
    for (const actionId of actions) {
      const response = await apiClient.post('/agent/action', { actionId });
      
      if (response.status !== 200) {
        allPassed = false;
        break;
      }
      
      const validation = validateQueryResponse(response.data);
      if (!validation.valid) {
        allPassed = false;
        break;
      }
    }
    
    const duration = Date.now() - start;
    
    if (!allPassed) {
      recordTest(testName, false, duration, 'One or more actions failed');
      return;
    }
    
    recordTest(testName, true, duration, undefined, {
      actionsExecuted: actions.length,
    });
  } catch (error) {
    const duration = Date.now() - start;
    recordTest(testName, false, duration, (error as Error).message);
  }
}

function printSummary() {
  console.log('\n' + '='.repeat(80));
  console.log('TEST SUMMARY');
  console.log('='.repeat(80));
  
  const passed = testResults.filter(t => t.passed).length;
  const failed = testResults.filter(t => !t.passed).length;
  const total = testResults.length;
  const passRate = ((passed / total) * 100).toFixed(1);
  
  console.log(`Total Tests: ${total}`);
  console.log(`Passed: ${passed} ✅`);
  console.log(`Failed: ${failed} ❌`);
  console.log(`Pass Rate: ${passRate}%`);
  console.log('');
  
  if (failed > 0) {
    console.log('FAILED TESTS:');
    testResults.filter(t => !t.passed).forEach(t => {
      console.log(`  ❌ ${t.name}`);
      if (t.error) {
        console.log(`     Error: ${t.error}`);
      }
    });
    console.log('');
  }
  
  const avgDuration = testResults.reduce((sum, t) => sum + t.duration, 0) / total;
  console.log(`Average Test Duration: ${avgDuration.toFixed(0)}ms`);
  console.log(`Total Test Duration: ${testResults.reduce((sum, t) => sum + t.duration, 0)}ms`);
  
  console.log('='.repeat(80));
  
  // Exit with error code if any tests failed
  if (failed > 0) {
    process.exit(1);
  }
}

// Run tests
runTests().catch(error => {
  console.error('Fatal error running tests:', error);
  process.exit(1);
});
