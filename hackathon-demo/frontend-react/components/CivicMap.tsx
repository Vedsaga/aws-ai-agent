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
  assignee?: string;
  created_at?: string;
}

interface CivicMapProps {
  reports: MapReport[];
}

const getSeverityConfig = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { color: '#dc2626', emoji: '🔴', label: 'Critical' };
    case 'high':
      return { color: '#ea580c', emoji: '🟠', label: 'High' };
    case 'medium':
      return { color: '#ca8a04', emoji: '🟡', label: 'Medium' };
    case 'low':
      return { color: '#16a34a', emoji: '🟢', label: 'Low' };
    default:
      return { color: '#6b7280', emoji: '⚪', label: 'Unknown' };
  }
};

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'in_progress':
      return '#3b82f6'; // blue
    case 'resolved':
      return '#10b981'; // green
    case 'closed':
      return '#6b7280'; // gray
    default:
      return '#f59e0b'; // amber (pending)
  }
};

const calculateBounds = (reports: MapReport[]) => {
  if (reports.length === 0) return null;

  let minLng = Infinity;
  let maxLng = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;

  reports.forEach((report) => {
    if (report.geo_coordinates && report.geo_coordinates.length === 2) {
      const [lng, lat] = report.geo_coordinates;
      if (lng && lat && !isNaN(lng) && !isNaN(lat)) {
        minLng = Math.min(minLng, lng);
        maxLng = Math.max(maxLng, lng);
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
      }
    }
  });

  if (minLng === Infinity) return null;

  return {
    sw: [minLng, minLat] as [number, number],
    ne: [maxLng, maxLat] as [number, number],
  };
};

export default function CivicMap({ reports }: CivicMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);

  useEffect(() => {
    if (!mapContainer.current) return;

    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!mapboxToken || mapboxToken === 'YOUR_MAPBOX_TOKEN_HERE') {
      console.warn('Mapbox token not configured');
      return;
    }

    mapboxgl.accessToken = mapboxToken;

    // Initialize map
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-74.0060, 40.7128], // NYC default
      zoom: 12,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

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

      const severityConfig = getSeverityConfig(report.severity);
      const statusColor = getStatusColor(report.status);

      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'custom-marker';
      el.style.width = '40px';
      el.style.height = '40px';
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.justifyContent = 'center';
      el.style.fontSize = '28px';
      el.style.cursor = 'pointer';
      el.style.filter = 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))';
      el.style.transition = 'transform 0.2s';
      el.textContent = severityConfig.emoji;

      // Add status ring
      if (report.status) {
        el.style.border = `3px solid ${statusColor}`;
        el.style.borderRadius = '50%';
        el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
      }

      // Hover effect
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.2)';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
      });

      // Create popup
      const popupContent = `
        <div style="padding: 12px; min-width: 250px; font-family: system-ui;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 24px;">${severityConfig.emoji}</span>
            <div>
              <div style="font-weight: bold; color: ${severityConfig.color}; font-size: 14px;">
                ${severityConfig.label.toUpperCase()}
              </div>
              ${report.status ? `
                <div style="font-size: 11px; color: #666; margin-top: 2px;">
                  Status: <span style="color: ${statusColor}; font-weight: 600;">${report.status.replace('_', ' ')}</span>
                </div>
              ` : ''}
            </div>
          </div>
          
          <div style="margin-bottom: 8px; padding: 8px; background: #f3f4f6; border-radius: 6px;">
            <div style="font-weight: 600; margin-bottom: 4px; font-size: 13px;">
              ${report.entity}
            </div>
            <div style="font-size: 12px; color: #666;">
              📍 ${report.location}
            </div>
          </div>

          ${report.assignee ? `
            <div style="margin-bottom: 8px; font-size: 12px;">
              <strong>Assigned to:</strong> ${report.assignee}
            </div>
          ` : ''}

          ${report.created_at ? `
            <div style="font-size: 11px; color: #999; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
              Created: ${new Date(report.created_at).toLocaleString()}
            </div>
          ` : ''}

          <div style="font-size: 10px; color: #999; margin-top: 4px;">
            ID: ${report.report_id.substring(0, 8)}...
          </div>
        </div>
      `;

      const popup = new mapboxgl.Popup({ 
        offset: 25,
        maxWidth: '300px'
      }).setHTML(popupContent);

      // Add marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map.current!);

      markers.current.push(marker);
    });

    // Fit bounds to show all markers
    const bounds = calculateBounds(reports);
    if (bounds && map.current) {
      map.current.fitBounds([bounds.sw, bounds.ne], {
        padding: { top: 80, bottom: 50, left: 50, right: 50 },
        maxZoom: 15,
        duration: 1000,
      });
    }
  }, [reports]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Legend */}
      <div className="absolute bottom-6 right-6 bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-xl text-xs border border-gray-200">
        <div className="font-bold mb-3 text-gray-800">Severity Levels</div>
        <div className="space-y-2">
          {['critical', 'high', 'medium', 'low'].map((severity) => {
            const config = getSeverityConfig(severity);
            return (
              <div key={severity} className="flex items-center gap-2">
                <span className="text-lg">{config.emoji}</span>
                <span className="text-gray-700">{config.label}</span>
              </div>
            );
          })}
        </div>

        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="font-bold mb-2 text-gray-800">Status Rings</div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#f59e0b' }}></div>
              <span className="text-gray-600">Pending</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#3b82f6' }}></div>
              <span className="text-gray-600">In Progress</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: '#10b981' }}></div>
              <span className="text-gray-600">Resolved</span>
            </div>
          </div>
        </div>
      </div>

      {/* Report Count */}
      <div className="absolute top-20 left-4 bg-white/95 backdrop-blur-sm px-4 py-2 rounded-lg shadow-lg text-sm font-medium border border-gray-200">
        <span className="text-gray-600">Reports:</span>{' '}
        <span className="text-gray-900 font-bold">{reports.length}</span>
      </div>
    </div>
  );
}
