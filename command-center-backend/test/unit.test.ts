/**
 * Unit Tests for Command Center Backend
 * 
 * Tests individual functions and modules without external dependencies
 */

import {
  eventToGeoJSONFeature,
  eventsToMapLayers,
  extractCriticalAlerts,
  getLatestTimestamp,
  transformToUpdatesResponse,
} from '../lib/data-access/transformers';
import { getDayFromTimestamp } from '../lib/data-access/query-functions';
import { validateEventItem } from '../lib/data-access/batch-write';
import { EventItem } from '../lib/types/database';

// Test data
const mockEvent: EventItem = {
  Day: 'DAY_0',
  Timestamp: '2023-02-06T04:00:00Z',
  eventId: 'test-event-001',
  domain: 'MEDICAL',
  severity: 'CRITICAL',
  geojson: JSON.stringify({
    type: 'Point',
    coordinates: [37.15, 37.12],
  }),
  summary: 'Test medical incident',
  details: 'Detailed description',
  resourcesNeeded: ['ambulance', 'medical-supplies'],
  contactInfo: 'test@example.com',
};

const mockEvents: EventItem[] = [
  mockEvent,
  {
    ...mockEvent,
    eventId: 'test-event-002',
    Timestamp: '2023-02-06T05:00:00Z',
    severity: 'HIGH',
    domain: 'FIRE',
  },
  {
    ...mockEvent,
    eventId: 'test-event-003',
    Timestamp: '2023-02-06T06:00:00Z',
    severity: 'MEDIUM',
    domain: 'STRUCTURAL',
  },
];

// Test results
interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
}

const results: TestResult[] = [];

function test(name: string, fn: () => void | Promise<void>) {
  try {
    const result = fn();
    if (result instanceof Promise) {
      result.then(() => {
        results.push({ name, passed: true });
        console.log(`✅ ${name}`);
      }).catch(error => {
        results.push({ name, passed: false, error: error.message });
        console.log(`❌ ${name}: ${error.message}`);
      });
    } else {
      results.push({ name, passed: true });
      console.log(`✅ ${name}`);
    }
  } catch (error) {
    results.push({ name, passed: false, error: (error as Error).message });
    console.log(`❌ ${name}: ${(error as Error).message}`);
  }
}

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertEquals(actual: any, expected: any, message?: string) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(message || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

// Run tests
console.log('='.repeat(80));
console.log('UNIT TESTS');
console.log('='.repeat(80));
console.log('');

// Transformer tests
test('eventToGeoJSONFeature - converts EventItem to GeoJSON Feature', () => {
  const feature = eventToGeoJSONFeature(mockEvent);

  assert(feature.type === 'Feature', 'Feature type should be "Feature"');
  assert(feature.geometry.type === 'Point', 'Geometry type should be "Point"');
  assert(Array.isArray(feature.geometry.coordinates), 'Coordinates should be an array');
  assert(feature.properties.eventId === mockEvent.eventId, 'Properties should include eventId');
  assert(feature.properties.domain === mockEvent.domain, 'Properties should include domain');
});

test('eventToGeoJSONFeature - handles invalid GeoJSON gracefully', () => {
  const invalidEvent: EventItem = {
    ...mockEvent,
    geojson: 'invalid-json',
  };

  const feature = eventToGeoJSONFeature(invalidEvent);

  assert(feature.type === 'Feature', 'Should still return a Feature');
  assert(feature.geometry.type === 'Point', 'Should default to Point');
  assert(feature.properties.error === 'Failed to parse geometry', 'Should include error in properties');
});

test('eventsToMapLayers - groups events by domain and layer type', () => {
  const layers = eventsToMapLayers(mockEvents);

  assert(Array.isArray(layers), 'Should return an array');
  assert(layers.length > 0, 'Should return at least one layer');

  layers.forEach(layer => {
    assert(!!layer.layerId, 'Each layer should have a layerId');
    assert(!!layer.layerName, 'Each layer should have a layerName');
    assert(!!layer.geometryType, 'Each layer should have a geometryType');
    assert(layer.data.type === 'FeatureCollection', 'Each layer should have a FeatureCollection');
    assert(Array.isArray(layer.data.features), 'Each layer should have features array');
  });
});

test('eventsToMapLayers - returns empty array for no events', () => {
  const layers = eventsToMapLayers([]);

  assertEquals(layers, [], 'Should return empty array for no events');
});

test('extractCriticalAlerts - filters CRITICAL and HIGH severity events', () => {
  const alerts = extractCriticalAlerts(mockEvents);

  assert(Array.isArray(alerts), 'Should return an array');
  assert(alerts.length === 2, 'Should return 2 alerts (CRITICAL and HIGH)');

  alerts.forEach(alert => {
    assert(!!alert.alertId, 'Each alert should have an alertId');
    assert(alert.severity === 'CRITICAL' || alert.severity === 'HIGH', 'Alert severity should be CRITICAL or HIGH');
    assert(!!alert.location, 'Each alert should have a location');
    assert(typeof alert.location.lat === 'number', 'Location should have lat');
    assert(typeof alert.location.lon === 'number', 'Location should have lon');
  });
});

test('extractCriticalAlerts - returns empty array for no critical events', () => {
  const lowSeverityEvents: EventItem[] = [{
    ...mockEvent,
    severity: 'LOW',
  }];

  const alerts = extractCriticalAlerts(lowSeverityEvents);

  assertEquals(alerts, [], 'Should return empty array for no critical events');
});

test('getLatestTimestamp - returns latest timestamp from events', () => {
  const latest = getLatestTimestamp(mockEvents);

  assertEquals(latest, '2023-02-06T06:00:00Z', 'Should return the latest timestamp');
});

test('getLatestTimestamp - returns current time for empty array', () => {
  const latest = getLatestTimestamp([]);

  assert(!!latest, 'Should return a timestamp');
  assert(new Date(latest).getTime() > 0, 'Should be a valid timestamp');
});

test('transformToUpdatesResponse - creates complete UpdatesResponse', () => {
  const response = transformToUpdatesResponse(mockEvents);

  assert(!!response.latestTimestamp, 'Should have latestTimestamp');
  assert(Array.isArray(response.mapLayers), 'Should have mapLayers array');
  assert(Array.isArray(response.criticalAlerts), 'Should have criticalAlerts array');
  assert(response.criticalAlerts.length === 2, 'Should have 2 critical alerts');
});

// Query function tests
test('getDayFromTimestamp - calculates correct day partition', () => {
  const day0 = getDayFromTimestamp('2023-02-06T00:00:00Z');
  assertEquals(day0, 'DAY_0', 'Simulation start should be DAY_0');

  const day1 = getDayFromTimestamp('2023-02-07T00:00:00Z');
  assertEquals(day1, 'DAY_1', 'Next day should be DAY_1');

  const day6 = getDayFromTimestamp('2023-02-12T00:00:00Z');
  assertEquals(day6, 'DAY_6', 'Day 6 should be DAY_6');
});

test('getDayFromTimestamp - handles timestamps within same day', () => {
  const morning = getDayFromTimestamp('2023-02-06T08:00:00Z');
  const evening = getDayFromTimestamp('2023-02-06T20:00:00Z');

  assertEquals(morning, evening, 'Same day timestamps should return same partition');
  assertEquals(morning, 'DAY_0', 'Should be DAY_0');
});

// Validation tests
test('validateEventItem - accepts valid event', () => {
  const isValid = validateEventItem(mockEvent);

  assert(isValid === true, 'Valid event should pass validation');
});

test('validateEventItem - rejects event without required fields', () => {
  const invalidEvent: any = {
    Day: 'DAY_0',
    // Missing Timestamp
    eventId: 'test',
  };

  try {
    validateEventItem(invalidEvent);
    throw new Error('Should have thrown validation error');
  } catch (error) {
    assert((error as Error).message.includes('must have'), 'Should throw validation error');
  }
});

test('validateEventItem - rejects invalid domain', () => {
  const invalidEvent: EventItem = {
    ...mockEvent,
    domain: 'INVALID_DOMAIN',
  };

  try {
    validateEventItem(invalidEvent);
    throw new Error('Should have thrown validation error');
  } catch (error) {
    assert((error as Error).message.includes('Invalid domain'), 'Should throw domain validation error');
  }
});

test('validateEventItem - rejects invalid severity', () => {
  const invalidEvent: EventItem = {
    ...mockEvent,
    severity: 'INVALID_SEVERITY',
  };

  try {
    validateEventItem(invalidEvent);
    throw new Error('Should have thrown validation error');
  } catch (error) {
    assert((error as Error).message.includes('Invalid severity'), 'Should throw severity validation error');
  }
});

test('validateEventItem - rejects invalid GeoJSON', () => {
  const invalidEvent: EventItem = {
    ...mockEvent,
    geojson: 'not-valid-json',
  };

  try {
    validateEventItem(invalidEvent);
    throw new Error('Should have thrown validation error');
  } catch (error) {
    assert((error as Error).message.includes('Invalid GeoJSON'), 'Should throw GeoJSON validation error');
  }
});

// Print summary
setTimeout(() => {
  console.log('');
  console.log('='.repeat(80));
  console.log('SUMMARY');
  console.log('='.repeat(80));

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const total = results.length;

  console.log(`Total: ${total}`);
  console.log(`Passed: ${passed} ✅`);
  console.log(`Failed: ${failed} ❌`);
  console.log(`Pass Rate: ${((passed / total) * 100).toFixed(1)}%`);

  if (failed > 0) {
    console.log('');
    console.log('FAILED TESTS:');
    results.filter(r => !r.passed).forEach(r => {
      console.log(`  ❌ ${r.name}`);
      if (r.error) {
        console.log(`     ${r.error}`);
      }
    });
  }

  console.log('='.repeat(80));

  process.exit(failed > 0 ? 1 : 0);
}, 100);
