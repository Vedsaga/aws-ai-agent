import { z } from 'zod';

/**
 * GeoJSON Feature interface
 */
export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  properties: Record<string, any>;
}

/**
 * GeoJSON FeatureCollection interface
 */
export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

/**
 * Map layer style configuration
 */
export interface MapLayerStyle {
  icon?: string;                  // For Point layers
  color?: string;                 // Hex color
  size?: number;                  // For Point layers
  fillColor?: string;             // For Polygon layers
  fillOpacity?: number;           // For Polygon layers
}

/**
 * Map layer structure
 */
export interface MapLayer {
  layerId: string;
  layerName: string;
  geometryType: 'Point' | 'Polygon' | 'LineString';
  style: MapLayerStyle;
  data: GeoJSONFeatureCollection;
}

/**
 * Alert structure
 */
export interface Alert {
  alertId: string;
  timestamp: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  summary: string;
  location: {
    lat: number;
    lon: number;
  };
}

/**
 * View state for map control
 */
export interface ViewState {
  bounds?: {
    southwest: { lat: number; lon: number };
    northeast: { lat: number; lon: number };
  };
  center?: { lat: number; lon: number };
  zoom?: number;
}

/**
 * Suggested action structure
 */
export interface SuggestedAction {
  label: string;
  actionId: string;
  payload?: object;
}

/**
 * UI context structure
 */
export interface UIContext {
  suggestedActions?: SuggestedAction[];
}

/**
 * Client state hint structure
 */
export interface ClientStateHint {
  activeDomainFilter?: string;
}

// ============================================================================
// GET /data/updates - Request and Response
// ============================================================================

/**
 * Updates request query parameters
 */
export interface UpdatesRequest {
  since: string;      // ISO 8601 timestamp
  domain?: string;    // Optional: domain filter
}

/**
 * Updates response structure
 */
export interface UpdatesResponse {
  latestTimestamp: string;
  mapUpdates?: {
    mapAction: 'APPEND' | 'REPLACE';
    mapLayers: MapLayer[];
  };
  criticalAlerts?: Alert[];
}

// Zod validation schema for UpdatesRequest
export const UpdatesRequestSchema = z.object({
  since: z.string().datetime(),
  domain: z.enum(['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION']).optional(),
});

// ============================================================================
// POST /agent/query - Request and Response
// ============================================================================

/**
 * Query request structure
 */
export interface QueryRequest {
  text: string;
  sessionId?: string;
  currentMapState?: {
    center: [number, number];
    zoom: number;
  };
}

/**
 * Query response structure
 */
export interface QueryResponse {
  simulationTime: string;
  timestamp: string;
  chatResponse: string;
  mapAction: 'REPLACE' | 'APPEND';
  viewState?: ViewState;
  mapLayers: MapLayer[];
  tabularData?: any;
  uiContext?: UIContext;
  clientStateHint?: ClientStateHint;
}

// Zod validation schema for QueryRequest
export const QueryRequestSchema = z.object({
  text: z.string().min(1),
  sessionId: z.string().optional(),
  currentMapState: z.object({
    center: z.tuple([z.number(), z.number()]),
    zoom: z.number(),
  }).optional(),
});

// ============================================================================
// POST /agent/action - Request and Response
// ============================================================================

/**
 * Action request structure
 */
export interface ActionRequest {
  actionId: string;
  payload?: object;
}

/**
 * Action response structure (same as QueryResponse)
 */
export type ActionResponse = QueryResponse;

// Zod validation schema for ActionRequest
export const ActionRequestSchema = z.object({
  actionId: z.string().min(1),
  payload: z.record(z.string(), z.any()).optional(),
});

// ============================================================================
// Bedrock Agent Tool - Request and Response
// ============================================================================

/**
 * Database query tool input (from Bedrock Agent)
 */
export interface ToolInput {
  domain?: string;
  severity?: string;
  startTime?: string;
  endTime?: string;
  location?: {
    lat: number;
    lon: number;
    radiusKm?: number;
  };
  limit?: number;
}

/**
 * Raw event structure for tool output
 */
export interface RawEvent {
  eventId: string;
  timestamp: string;
  domain: string;
  severity: string;
  geojson: string;
  summary: string;
  details?: string;
  resourcesNeeded?: string[];
  contactInfo?: string;
}

/**
 * Database query tool output (to Bedrock Agent)
 */
export interface ToolOutput {
  events: RawEvent[];
  count: number;
}

// Zod validation schema for ToolInput
export const ToolInputSchema = z.object({
  domain: z.enum(['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION']).optional(),
  severity: z.enum(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']).optional(),
  startTime: z.string().datetime().optional(),
  endTime: z.string().datetime().optional(),
  location: z.object({
    lat: z.number(),
    lon: z.number(),
    radiusKm: z.number().optional(),
  }).optional(),
  limit: z.number().int().positive().optional(),
});

// ============================================================================
// Error Response
// ============================================================================

/**
 * Error response structure
 */
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: object;
  };
}
