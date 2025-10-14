import mapboxgl from 'mapbox-gl';
import { MapLayer } from '@/store/useStore';

/**
 * Calculates a bounding box from map layers and fits the map view to it.
 * @param mapLayers - The array of layers from your API response.
 * @param map - The Mapbox map instance.
 */
export function fitMapToBounds(mapLayers: MapLayer[], map: mapboxgl.Map) {
  if (!map || !mapLayers || mapLayers.length === 0) {
    return; // Exit if map or data isn't available
  }

  // Use Mapbox's LngLatBounds utility to build the bounding box
  const bounds = new mapboxgl.LngLatBounds();

  mapLayers.forEach(layer => {
    if (!layer.data?.features) return;
    
    layer.data.features.forEach((feature: any) => {
      // This recursive function handles all geometry types (Points, Polygons, etc.)
      const extendBounds = (coords: any) => {
        if (Array.isArray(coords[0])) {
          coords.forEach(extendBounds);
        } else {
          bounds.extend(coords as [number, number]);
        }
      };
      
      if (feature.geometry?.coordinates) {
        extendBounds(feature.geometry.coordinates);
      }
    });
  });

  // Ensure the bounds are valid before trying to fit
  if (bounds.isEmpty()) {
    return;
  }

  // Animate the map to fit the new bounding box
  map.fitBounds(bounds, {
    padding: 60,      // Adds 60px padding to avoid icons at the very edge
    maxZoom: 15,      // Prevents zooming in too far on a single point
    duration: 1000    // Smooth animation over 1 second
  });
}

/**
 * Get color based on severity or type
 */
export function getMarkerColor(properties: any, defaultColor: string = '#FF4136'): string {
  if (properties.severity === 'CRITICAL') return '#DC2626'; // Red-600
  if (properties.severity === 'HIGH') return '#EA580C'; // Orange-600
  if (properties.severity === 'MEDIUM') return '#CA8A04'; // Yellow-600
  if (properties.type === 'Food Supply' || properties.type === 'Water Supply') return '#16A34A'; // Green-600
  if (properties.type === 'Medical') return '#2563EB'; // Blue-600
  return defaultColor;
}
