/**
 * Map Utilities
 * Helper functions for map visualization and custom markers
 */

import { getCategoryColors, getSeverityColor } from './category-config';

export interface Incident {
  id: string;
  domain_id: string;
  raw_text: string;
  structured_data: Record<string, any>;
  location?: { latitude: number; longitude: number };
  created_at: string;
  images?: string[];
  geometry_type?: 'Point' | 'LineString' | 'Polygon';
  coordinates?: any;
}

/**
 * Create a custom marker element with category styling and severity indicator
 */
export function createCustomMarker(incident: Incident): HTMLElement {
  // Extract category from entity_agent or other agents
  const category = 
    incident.structured_data?.entity_agent?.category ||
    incident.structured_data?.category ||
    'default';
  
  // Extract severity from severity_classifier or other agents
  const severity = 
    incident.structured_data?.severity_classifier?.severity_level ||
    incident.structured_data?.severity ||
    'medium';
  
  const colors = getCategoryColors(category);
  const severityColor = getSeverityColor(severity);
  
  const el = document.createElement('div');
  el.className = 'custom-marker';
  el.style.cssText = 'cursor: pointer;';
  
  // Create marker HTML with category color and icon
  el.innerHTML = `
    <div style="
      width: 40px;
      height: 40px;
      background: ${colors.bg};
      border: 3px solid ${colors.border};
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      position: relative;
      transition: transform 0.2s ease;
    "
    onmouseover="this.style.transform='scale(1.1)'"
    onmouseout="this.style.transform='scale(1)'"
    >
      ${colors.icon}
      ${severity === 'critical' ? `
        <div style="
          position: absolute;
          top: -5px;
          right: -5px;
          width: 12px;
          height: 12px;
          background: ${severityColor};
          border: 2px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        "></div>
      ` : ''}
    </div>
  `;
  
  return el;
}

/**
 * Extract coordinates from incident data
 */
export function getIncidentCoordinates(incident: Incident): [number, number] | null {
  // Try coordinates field first
  if (incident.coordinates && Array.isArray(incident.coordinates)) {
    return incident.coordinates as [number, number];
  }
  
  // Try location object
  if (incident.location?.latitude && incident.location?.longitude) {
    return [incident.location.longitude, incident.location.latitude];
  }
  
  // Try structured_data.geo_agent
  if (incident.structured_data?.geo_agent?.coordinates) {
    const coords = incident.structured_data.geo_agent.coordinates;
    if (Array.isArray(coords) && coords.length >= 2) {
      return coords as [number, number];
    }
  }
  
  return null;
}

/**
 * Get geometry type from incident data
 */
export function getGeometryType(incident: Incident): 'Point' | 'LineString' | 'Polygon' {
  // Check explicit geometry_type field
  if (incident.geometry_type) {
    return incident.geometry_type;
  }
  
  // Check structured_data.geo_agent
  if (incident.structured_data?.geo_agent?.geometry_type) {
    return incident.structured_data.geo_agent.geometry_type;
  }
  
  // Default to Point
  return 'Point';
}

/**
 * Render geometry on map based on type
 */
export function renderGeometry(
  map: any,
  incident: Incident,
  onPopupCreate: (incident: Incident) => any
): void {
  const geometryType = getGeometryType(incident);
  const category = incident.structured_data?.entity_agent?.category || 'default';
  const colors = getCategoryColors(category);
  
  switch (geometryType) {
    case 'Point':
      renderPoint(map, incident, colors, onPopupCreate);
      break;
    case 'LineString':
      renderLineString(map, incident, colors, onPopupCreate);
      break;
    case 'Polygon':
      renderPolygon(map, incident, colors, onPopupCreate);
      break;
    default:
      // Fallback to Point
      renderPoint(map, incident, colors, onPopupCreate);
  }
}

/**
 * Render Point geometry as a marker
 */
export function renderPoint(
  map: any,
  incident: Incident,
  colors: any,
  onPopupCreate: (incident: Incident) => any
): any {
  const coords = getIncidentCoordinates(incident);
  if (!coords) return null;
  
  const markerElement = createCustomMarker(incident);
  const popup = onPopupCreate(incident);
  
  // Import mapboxgl dynamically to avoid SSR issues
  const mapboxgl = require('mapbox-gl');
  
  const marker = new mapboxgl.Marker(markerElement)
    .setLngLat(coords)
    .setPopup(popup)
    .addTo(map);
  
  return marker;
}

/**
 * Render LineString geometry as a line
 */
export function renderLineString(
  map: any,
  incident: Incident,
  colors: any,
  onPopupCreate: (incident: Incident) => any
): void {
  const coordinates = incident.structured_data?.geo_agent?.coordinates || incident.coordinates;
  if (!coordinates || !Array.isArray(coordinates)) return;
  
  const sourceId = `line-${incident.id}`;
  const layerId = `line-${incident.id}`;
  
  // Add source
  map.addSource(sourceId, {
    type: 'geojson',
    data: {
      type: 'Feature',
      properties: { incidentId: incident.id },
      geometry: {
        type: 'LineString',
        coordinates: coordinates
      }
    }
  });
  
  // Add layer with category color
  map.addLayer({
    id: layerId,
    type: 'line',
    source: sourceId,
    paint: {
      'line-color': colors.bg,
      'line-width': 4,
      'line-opacity': 0.8
    }
  });
  
  // Add click handler to show popup
  map.on('click', layerId, (e: any) => {
    onPopupCreate(incident)
      .setLngLat(e.lngLat)
      .addTo(map);
  });
  
  // Add hover effect (cursor pointer)
  map.on('mouseenter', layerId, () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  
  map.on('mouseleave', layerId, () => {
    map.getCanvas().style.cursor = '';
  });
}

/**
 * Render Polygon geometry as a filled area
 */
export function renderPolygon(
  map: any,
  incident: Incident,
  colors: any,
  onPopupCreate: (incident: Incident) => any
): void {
  const coordinates = incident.structured_data?.geo_agent?.coordinates || incident.coordinates;
  if (!coordinates || !Array.isArray(coordinates)) return;
  
  const sourceId = `polygon-${incident.id}`;
  const fillLayerId = `polygon-${incident.id}`;
  const borderLayerId = `polygon-border-${incident.id}`;
  
  // Add source
  map.addSource(sourceId, {
    type: 'geojson',
    data: {
      type: 'Feature',
      properties: { incidentId: incident.id },
      geometry: {
        type: 'Polygon',
        coordinates: coordinates
      }
    }
  });
  
  // Add fill layer with 30% opacity
  map.addLayer({
    id: fillLayerId,
    type: 'fill',
    source: sourceId,
    paint: {
      'fill-color': colors.bg,
      'fill-opacity': 0.3
    }
  });
  
  // Add border layer with category color
  map.addLayer({
    id: borderLayerId,
    type: 'line',
    source: sourceId,
    paint: {
      'line-color': colors.border,
      'line-width': 2,
      'line-opacity': 0.8
    }
  });
  
  // Add click handler to show popup
  map.on('click', fillLayerId, (e: any) => {
    onPopupCreate(incident)
      .setLngLat(e.lngLat)
      .addTo(map);
  });
  
  // Add hover effect (cursor pointer)
  map.on('mouseenter', fillLayerId, () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  
  map.on('mouseleave', fillLayerId, () => {
    map.getCanvas().style.cursor = '';
  });
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}
