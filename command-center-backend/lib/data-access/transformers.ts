import { EventItem } from '../types/database';
import { MapLayer, Alert, GeoJSONFeatureCollection, GeoJSONFeature } from '../types/api';

/**
 * Icon mapping based on event domain and properties
 */
const ICON_MAP: Record<string, string> = {
  MEDICAL: 'MEDICAL_FACILITY',
  FIRE: 'FIRE_INCIDENT',
  STRUCTURAL: 'BUILDING_COLLAPSE',
  LOGISTICS: 'SUPPLY_POINT',
  COMMUNICATION: 'COMMUNICATION_TOWER',
};

/**
 * Color mapping based on severity
 */
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#DC2626',  // Red
  HIGH: '#F59E0B',      // Orange
  MEDIUM: '#3B82F6',    // Blue
  LOW: '#10B981',       // Green
};

/**
 * Transform EventItem to GeoJSON Feature
 * 
 * @param event - EventItem from DynamoDB
 * @returns GeoJSON Feature
 */
export function eventToGeoJSONFeature(event: EventItem): GeoJSONFeature {
  try {
    const geometry = JSON.parse(event.geojson);

    return {
      type: 'Feature',
      geometry,
      properties: {
        eventId: event.eventId,
        timestamp: event.Timestamp,
        domain: event.domain,
        severity: event.severity,
        summary: event.summary,
        details: event.details,
        resourcesNeeded: event.resourcesNeeded,
        contactInfo: event.contactInfo,
      },
    };
  } catch (error) {
    console.error('Error parsing GeoJSON for event', {
      eventId: event.eventId,
      error: error instanceof Error ? error.message : String(error),
    });
    
    // Return a default Point feature at 0,0 if parsing fails
    return {
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [0, 0],
      },
      properties: {
        eventId: event.eventId,
        timestamp: event.Timestamp,
        domain: event.domain,
        severity: event.severity,
        summary: event.summary,
        error: 'Failed to parse geometry',
      },
    };
  }
}

/**
 * Determine layer type based on event properties
 * Groups events into incidents, resources, or alerts
 */
function getLayerType(event: EventItem): 'incidents' | 'resources' | 'alerts' {
  // Critical and high severity events are alerts
  if (event.severity === 'CRITICAL' || event.severity === 'HIGH') {
    return 'alerts';
  }
  
  // Logistics domain events are typically resources
  if (event.domain === 'LOGISTICS') {
    return 'resources';
  }
  
  // Everything else is an incident
  return 'incidents';
}

/**
 * Get appropriate style for an event based on its properties
 */
function getEventStyle(event: EventItem, geometryType: string): {
  icon?: string;
  color: string;
  size?: number;
  fillColor?: string;
  fillOpacity?: number;
} {
  const baseColor = SEVERITY_COLORS[event.severity] || '#6B7280';
  
  if (geometryType === 'Point') {
    return {
      icon: ICON_MAP[event.domain] || 'DEFAULT_MARKER',
      color: baseColor,
      size: event.severity === 'CRITICAL' ? 12 : event.severity === 'HIGH' ? 10 : 8,
    };
  } else if (geometryType === 'Polygon') {
    return {
      color: baseColor,
      fillColor: baseColor,
      fillOpacity: 0.3,
    };
  } else {
    // LineString
    return {
      color: baseColor,
      size: 3,
    };
  }
}

/**
 * Transform array of EventItems to MapLayers grouped by domain and layer type
 * 
 * @param events - Array of EventItem records
 * @returns Array of MapLayer structures
 */
export function eventsToMapLayers(events: EventItem[]): MapLayer[] {
  if (events.length === 0) {
    return [];
  }

  // Group events by domain and layer type
  const groupedEvents = events.reduce((acc, event) => {
    const layerType = getLayerType(event);
    const key = `${event.domain}-${layerType}`;
    
    if (!acc[key]) {
      acc[key] = {
        domain: event.domain,
        layerType,
        events: [],
      };
    }
    acc[key].events.push(event);
    return acc;
  }, {} as Record<string, { domain: string; layerType: string; events: EventItem[] }>);

  // Create a MapLayer for each group
  const mapLayers: MapLayer[] = [];

  for (const [key, group] of Object.entries(groupedEvents)) {
    const features = group.events.map(eventToGeoJSONFeature);

    // Determine geometry type from first event
    const firstGeometry = JSON.parse(group.events[0].geojson);
    const geometryType = firstGeometry.type as 'Point' | 'Polygon' | 'LineString';

    // Get style for the first event (representative of the group)
    const style = getEventStyle(group.events[0], geometryType);

    mapLayers.push({
      layerId: `${group.domain.toLowerCase()}-${group.layerType}-layer`,
      layerName: `${group.domain} ${group.layerType.charAt(0).toUpperCase() + group.layerType.slice(1)}`,
      geometryType,
      style,
      data: {
        type: 'FeatureCollection',
        features,
      },
    });
  }

  return mapLayers;
}

/**
 * Extract critical alerts from events
 * Only includes CRITICAL and HIGH severity events
 * 
 * @param events - Array of EventItem records
 * @returns Array of Alert structures
 */
export function extractCriticalAlerts(events: EventItem[]): Alert[] {
  return events
    .filter(event => event.severity === 'CRITICAL' || event.severity === 'HIGH')
    .map(event => {
      try {
        const geometry = JSON.parse(event.geojson);
        
        // Extract coordinates based on geometry type
        let lat: number, lon: number;
        if (geometry.type === 'Point') {
          [lon, lat] = geometry.coordinates;
        } else if (geometry.type === 'Polygon') {
          // Use first coordinate of first ring
          [lon, lat] = geometry.coordinates[0][0];
        } else if (geometry.type === 'LineString') {
          // Use first coordinate
          [lon, lat] = geometry.coordinates[0];
        } else {
          // Default fallback
          lat = 0;
          lon = 0;
        }

        return {
          alertId: event.eventId,
          timestamp: event.Timestamp,
          severity: event.severity as 'CRITICAL' | 'HIGH',
          title: `${event.domain} - ${event.severity}`,
          summary: event.summary,
          location: { lat, lon },
        };
      } catch (error) {
        console.error('Error extracting alert coordinates', {
          eventId: event.eventId,
          error: error instanceof Error ? error.message : String(error),
        });
        
        // Return alert with default location if parsing fails
        return {
          alertId: event.eventId,
          timestamp: event.Timestamp,
          severity: event.severity as 'CRITICAL' | 'HIGH',
          title: `${event.domain} - ${event.severity}`,
          summary: event.summary,
          location: { lat: 0, lon: 0 },
        };
      }
    });
}

/**
 * Get the latest timestamp from an array of events
 * 
 * @param events - Array of EventItem records
 * @returns Latest timestamp as ISO 8601 string
 */
export function getLatestTimestamp(events: EventItem[]): string {
  if (events.length === 0) {
    return new Date().toISOString();
  }

  const timestamps = events.map(e => e.Timestamp);
  timestamps.sort();
  return timestamps[timestamps.length - 1];
}

/**
 * Transform events to UpdatesResponse format
 * 
 * @param events - Array of EventItem records
 * @returns Object with mapLayers and criticalAlerts
 */
export function transformToUpdatesResponse(events: EventItem[]): {
  latestTimestamp: string;
  mapLayers: MapLayer[];
  criticalAlerts: Alert[];
} {
  return {
    latestTimestamp: getLatestTimestamp(events),
    mapLayers: eventsToMapLayers(events),
    criticalAlerts: extractCriticalAlerts(events),
  };
}
