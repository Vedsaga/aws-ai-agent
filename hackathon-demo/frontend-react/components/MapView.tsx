'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { fetchIncidents } from '@/lib/api-client';
import {
  createCustomMarker,
  getIncidentCoordinates,
  getGeometryType,
  renderGeometry,
  type Incident
} from '@/lib/map-utils';
import { getCategoryColors } from '@/lib/category-config';
import { createDetailedPopup } from '@/lib/popup-utils';

export default function MapView() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    if (!mapContainer.current) return;

    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!mapboxToken) {
      console.error('Mapbox token not configured');
      return;
    }

    mapboxgl.accessToken = mapboxToken;

    // Initialize map
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-98.5795, 39.8283], // Center of US
      zoom: 4,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    // Load incidents automatically on mount
    // loadIncidents(); // Disabled auto-load to prevent network errors

    return () => {
      map.current?.remove();
    };
  }, []);

  // Auto-zoom to fit all incidents
  const autoZoomToIncidents = (incidentList: Incident[]) => {
    if (!map.current || incidentList.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();
    let hasValidCoords = false;

    incidentList.forEach((incident) => {
      const coords = getIncidentCoordinates(incident);
      if (coords && coords.length > 0) {
        coords.forEach(([lng, lat]) => {
          if (lng && lat && !isNaN(lng) && !isNaN(lat)) {
            bounds.extend([lng, lat]);
            hasValidCoords = true;
          }
        });
      }
    });

    if (hasValidCoords) {
      map.current.fitBounds(bounds, {
        padding: 50,
        maxZoom: 15,
        duration: 1000,
      });
    }
  };

  // Load incidents from API
  const loadIncidents = async () => {
    try {
      const response = await fetchIncidents({});
      if (response.data?.data) {
        const incidentData = response.data.data;
        setIncidents(incidentData);

        // Auto-zoom to show all incidents
        setTimeout(() => {
          autoZoomToIncidents(incidentData);
        }, 100);
      }
    } catch (error) {
      console.error('Failed to load incidents:', error);
    }
  };

  const handleRefresh = async () => {
    try {
      const response = await fetchIncidents({});
      if (response.data?.data) {
        setIncidents(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
    }
  };

  useEffect(() => {
    if (!map.current || incidents.length === 0) return;

    // Clear existing markers and layers
    markers.current.forEach((marker) => marker.remove());
    markers.current = [];

    // Remove existing layers and sources
    incidents.forEach((incident) => {
      const lineLayerId = `line-${incident.id}`;
      const polygonLayerId = `polygon-${incident.id}`;
      const polygonBorderId = `polygon-border-${incident.id}`;

      if (map.current?.getLayer(lineLayerId)) {
        map.current.removeLayer(lineLayerId);
      }
      if (map.current?.getLayer(polygonLayerId)) {
        map.current.removeLayer(polygonLayerId);
      }
      if (map.current?.getLayer(polygonBorderId)) {
        map.current.removeLayer(polygonBorderId);
      }
      if (map.current?.getSource(lineLayerId)) {
        map.current.removeSource(lineLayerId);
      }
      if (map.current?.getSource(polygonLayerId)) {
        map.current.removeSource(polygonLayerId);
      }
    });

    // Add markers/geometries for each incident
    incidents.forEach((incident) => {
      const geometryType = getGeometryType(incident);
      const popup = createDetailedPopup(incident);

      if (geometryType === 'Point') {
        // Use custom marker for point geometry
        const coords = getIncidentCoordinates(incident);
        if (!coords) return;

        const markerElement = createCustomMarker(incident);
        const marker = new mapboxgl.Marker(markerElement)
          .setLngLat(coords)
          .setPopup(popup)
          .addTo(map.current!);

        markers.current.push(marker);
      } else if (geometryType === 'LineString') {
        // Render LineString
        renderLineString(incident);
      } else if (geometryType === 'Polygon') {
        // Render Polygon
        renderPolygon(incident);
      }
    });

    // Fit bounds to show all markers
    if (incidents.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      incidents.forEach((incident) => {
        const coords = getIncidentCoordinates(incident);
        if (coords) {
          bounds.extend(coords);
        }
      });

      if (!bounds.isEmpty()) {
        map.current.fitBounds(bounds, { padding: 50, maxZoom: 15 });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incidents]);

  const renderLineString = (incident: Incident) => {
    if (!map.current) return;

    const coordinates = incident.structured_data?.geo_agent?.coordinates || incident.coordinates;
    if (!coordinates || !Array.isArray(coordinates)) return;

    const category = incident.structured_data?.entity_agent?.category || 'default';
    const colors = getCategoryColors(category);
    const sourceId = `line-${incident.id}`;
    const layerId = `line-${incident.id}`;

    // Add source
    map.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: coordinates
        }
      }
    });

    // Add layer
    map.current.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      paint: {
        'line-color': colors.bg,
        'line-width': 4,
        'line-opacity': 0.8
      }
    });

    // Add click handler
    map.current.on('click', layerId, (e) => {
      createDetailedPopup(incident)
        .setLngLat(e.lngLat)
        .addTo(map.current!);
    });

    // Add hover effects
    map.current.on('mouseenter', layerId, () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = 'pointer';
      }
    });

    map.current.on('mouseleave', layerId, () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = '';
      }
    });
  };

  const renderPolygon = (incident: Incident) => {
    if (!map.current) return;

    const coordinates = incident.structured_data?.geo_agent?.coordinates || incident.coordinates;
    if (!coordinates || !Array.isArray(coordinates)) return;

    const category = incident.structured_data?.entity_agent?.category || 'default';
    const colors = getCategoryColors(category);
    const sourceId = `polygon-${incident.id}`;
    const fillLayerId = `polygon-${incident.id}`;
    const borderLayerId = `polygon-border-${incident.id}`;

    // Add source
    map.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'Polygon',
          coordinates: coordinates
        }
      }
    });

    // Add fill layer
    map.current.addLayer({
      id: fillLayerId,
      type: 'fill',
      source: sourceId,
      paint: {
        'fill-color': colors.bg,
        'fill-opacity': 0.3
      }
    });

    // Add border layer
    map.current.addLayer({
      id: borderLayerId,
      type: 'line',
      source: sourceId,
      paint: {
        'line-color': colors.border,
        'line-width': 2,
        'line-opacity': 0.8
      }
    });

    // Add click handler
    map.current.on('click', fillLayerId, (e) => {
      createDetailedPopup(incident)
        .setLngLat(e.lngLat)
        .addTo(map.current!);
    });

    // Add hover effects
    map.current.on('mouseenter', fillLayerId, () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = 'pointer';
      }
    });

    map.current.on('mouseleave', fillLayerId, () => {
      if (map.current) {
        map.current.getCanvas().style.cursor = '';
      }
    });
  };


  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Refresh button */}
      <button
        onClick={handleRefresh}
        className="absolute top-4 left-4 bg-card text-card-foreground px-4 py-2 rounded-md shadow-md hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm font-medium border border-border"
      >
        Refresh Map
      </button>

      {/* Incident count */}
      <div className="absolute bottom-4 left-4 bg-card text-card-foreground px-4 py-2 rounded-md shadow-md text-sm border border-border">
        <span className="font-medium">{incidents.length}</span> incidents
      </div>
    </div>
  );
}
