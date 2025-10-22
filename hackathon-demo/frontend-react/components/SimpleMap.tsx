'use client';

import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapReport {
  report_id: string;
  location: string;
  geo_coordinates: [number, number];
  entity: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status?: string;
}

interface SimpleMapProps {
  reports: MapReport[];
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return '#dc2626'; // red-600
    case 'high': return '#ea580c'; // orange-600
    case 'medium': return '#ca8a04'; // yellow-600
    case 'low': return '#16a34a'; // green-600
    default: return '#6b7280'; // gray-500
  }
};

const getStatusIcon = (severity: string) => {
  switch (severity) {
    case 'critical': return '🔴';
    case 'high': return '🟠';
    case 'medium': return '🟡';
    case 'low': return '🟢';
    default: return '⚪';
  }
};

export default function SimpleMap({ reports }: SimpleMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);

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
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-74.0060, 40.7128], // NYC default
      zoom: 12,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    return () => {
      map.current?.remove();
    };
  }, []);

  useEffect(() => {
    if (!map.current || reports.length === 0) return;

    // Clear existing markers
    markers.current.forEach((marker) => marker.remove());
    markers.current = [];

    // Add markers for each report
    reports.forEach((report) => {
      if (!report.geo_coordinates || report.geo_coordinates.length !== 2) return;

      const [lng, lat] = report.geo_coordinates;
      if (!lng || !lat || isNaN(lng) || isNaN(lat)) return;

      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'custom-marker';
      el.style.width = '32px';
      el.style.height = '32px';
      el.style.fontSize = '24px';
      el.style.cursor = 'pointer';
      el.textContent = getStatusIcon(report.severity);

      // Create popup
      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="padding: 8px; min-width: 200px;">
          <div style="font-weight: bold; margin-bottom: 4px; color: ${getSeverityColor(report.severity)}">
            ${report.severity.toUpperCase()}
          </div>
          <div style="margin-bottom: 4px;">
            <strong>Issue:</strong> ${report.entity}
          </div>
          <div style="margin-bottom: 4px;">
            <strong>Location:</strong> ${report.location}
          </div>
          ${report.status ? `
            <div style="margin-bottom: 4px;">
              <strong>Status:</strong> ${report.status}
            </div>
          ` : ''}
          <div style="font-size: 11px; color: #666; margin-top: 4px;">
            ID: ${report.report_id.substring(0, 8)}...
          </div>
        </div>
      `);

      // Add marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map.current!);

      markers.current.push(marker);
    });

    // Fit bounds to show all markers
    if (reports.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      reports.forEach((report) => {
        if (report.geo_coordinates && report.geo_coordinates.length === 2) {
          const [lng, lat] = report.geo_coordinates;
          if (lng && lat && !isNaN(lng) && !isNaN(lat)) {
            bounds.extend([lng, lat]);
          }
        }
      });

      if (!bounds.isEmpty()) {
        map.current.fitBounds(bounds, { 
          padding: 50, 
          maxZoom: 15,
          duration: 1000 
        });
      }
    }
  }, [reports]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg text-xs">
        <div className="font-semibold mb-2">Severity</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span>🔴</span>
            <span>Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🟠</span>
            <span>High</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🟡</span>
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <span>🟢</span>
            <span>Low</span>
          </div>
        </div>
      </div>

      {/* Report count */}
      <div className="absolute top-4 left-4 bg-white px-3 py-2 rounded-lg shadow-lg text-sm font-medium">
        {reports.length} {reports.length === 1 ? 'Report' : 'Reports'}
      </div>
    </div>
  );
}
