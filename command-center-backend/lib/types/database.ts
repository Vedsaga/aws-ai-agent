/**
 * DynamoDB EventItem interface matching the table schema
 */
export interface EventItem {
  Day: string;                    // PK: DAY_0 to DAY_6
  Timestamp: string;              // SK: ISO 8601 timestamp
  eventId: string;                // UUID
  domain: string;                 // MEDICAL | FIRE | STRUCTURAL | LOGISTICS | COMMUNICATION
  severity: string;               // CRITICAL | HIGH | MEDIUM | LOW
  geojson: string;                // Stringified GeoJSON
  summary: string;                // Brief description
  details?: string;               // Optional: full details
  resourcesNeeded?: string[];     // Optional: list of resources
  contactInfo?: string;           // Optional: contact information
}

/**
 * Domain types for event categorization
 */
export type Domain = 'MEDICAL' | 'FIRE' | 'STRUCTURAL' | 'LOGISTICS' | 'COMMUNICATION';

/**
 * Severity levels for events
 */
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

/**
 * Geometry types for map layers
 */
export type GeometryType = 'Point' | 'Polygon' | 'LineString';

/**
 * Map action types
 */
export type MapAction = 'REPLACE' | 'APPEND';
