'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { fetchIncidents } from '@/lib/api-client';

interface Incident {
  id: string;
  location: {
    latitude: number;
    longitude: number;
  };
  structured_data: any;
  raw_text: string;
  created_at: string;
  images?: string[];
}

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
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-98.5795, 39.8283], // Center of US
      zoom: 4,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add fullscreen control
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    // Load initial incidents
    loadIncidents();

    return () => {
      map.current?.remove();
    };
  }, []);

  useEffect(() => {
    if (!map.current || incidents.length === 0) return;

    // Clear existing markers
    markers.current.forEach((marker) => marker.remove());
    markers.current = [];

    // Add markers for each incident
    incidents.forEach((incident) => {
      if (!incident.location?.latitude || !incident.location?.longitude) return;

      const el = document.createElement('div');
      el.className = 'custom-marker';
      el.style.width = '30px';
      el.style.height = '30px';
      el.style.borderRadius = '50%';
      el.style.backgroundColor = '#4F46E5';
      el.style.border = '2px solid white';
      el.style.cursor = 'pointer';
      el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';

      const popup = createPopup(incident);

      const marker = new mapboxgl.Marker(el)
        .setLngLat([incident.location.longitude, incident.location.latitude])
        .setPopup(popup)
        .addTo(map.current!);

      markers.current.push(marker);
    });

    // Fit bounds to show all markers
    if (incidents.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      incidents.forEach((incident) => {
        if (incident.location?.latitude && incident.location?.longitude) {
          bounds.extend([incident.location.longitude, incident.location.latitude]);
        }
      });
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 15 });
    }
  }, [incidents]);

  const createPopup = (incident: Incident): mapboxgl.Popup => {
    const popupContent = document.createElement('div');
    popupContent.className = 'p-2 max-w-xs';

    // Title
    const title = document.createElement('h3');
    title.className = 'font-bold text-sm mb-2';
    title.textContent = incident.structured_data?.category || 'Incident';
    popupContent.appendChild(title);

    // Description
    const description = document.createElement('p');
    description.className = 'text-xs text-gray-700 mb-2';
    description.textContent = incident.raw_text.substring(0, 100) + (incident.raw_text.length > 100 ? '...' : '');
    popupContent.appendChild(description);

    // Structured data
    if (incident.structured_data) {
      const dataDiv = document.createElement('div');
      dataDiv.className = 'text-xs text-gray-600 mb-2';
      
      Object.entries(incident.structured_data).slice(0, 3).forEach(([key, value]) => {
        const item = document.createElement('div');
        item.textContent = `${key}: ${value}`;
        dataDiv.appendChild(item);
      });
      
      popupContent.appendChild(dataDiv);
    }

    // Images
    if (incident.images && incident.images.length > 0) {
      const imagesDiv = document.createElement('div');
      imagesDiv.className = 'flex gap-1 mb-2';
      
      incident.images.slice(0, 3).forEach((imageUrl) => {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'w-16 h-16 object-cover rounded cursor-pointer';
        img.onclick = () => window.open(imageUrl, '_blank');
        imagesDiv.appendChild(img);
      });
      
      popupContent.appendChild(imagesDiv);
    }

    // Timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'text-xs text-gray-500';
    timestamp.textContent = new Date(incident.created_at).toLocaleString();
    popupContent.appendChild(timestamp);

    return new mapboxgl.Popup({ offset: 25 }).setDOMContent(popupContent);
  };

  const loadIncidents = async () => {
    const response = await fetchIncidents({});
    if (response.data?.data) {
      setIncidents(response.data.data);
    }
  };

  const handleRefresh = () => {
    loadIncidents();
  };

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Refresh button */}
      <button
        onClick={handleRefresh}
        className="absolute top-4 left-4 bg-white px-4 py-2 rounded-md shadow-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-medium"
      >
        Refresh Map
      </button>

      {/* Incident count */}
      <div className="absolute bottom-4 left-4 bg-white px-4 py-2 rounded-md shadow-md text-sm">
        <span className="font-medium">{incidents.length}</span> incidents
      </div>
    </div>
  );
}
