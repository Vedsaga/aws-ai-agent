'use client';

import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useStore } from '@/store/useStore';
import { IconLibrary } from '@/lib/icon-map';
import { fitMapToBounds, getMarkerColor } from '@/lib/map-utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

export default function MapComponent() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<mapboxgl.Marker[]>([]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { mapLayers, viewState, mapAction, setMapInstance } = useStore();

  // Function to zoom to a location
  const zoomToLocation = (lat: number, lon: number, zoom: number = 15) => {
    if (map.current) {
      map.current.flyTo({
        center: [lon, lat],
        zoom: zoom,
        duration: 1500,
        essential: true
      });
    }
  };

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    if (!mapboxgl.accessToken) {
      setMapError('Mapbox token not configured. Please add NEXT_PUBLIC_MAPBOX_TOKEN to .env.local');
      return;
    }

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [37.17, 37.07],
        zoom: 12
      });

      map.current.on('load', () => {
        console.log('Map loaded successfully');
        setMapError(null);
        if (map.current) {
          setMapInstance(map.current, zoomToLocation);
        }
      });

      map.current.on('error', (e) => {
        console.error('Map error:', e);
        setMapError('Map failed to load. Check your Mapbox token.');
      });
    } catch (error) {
      console.error('Error initializing map:', error);
      setMapError('Failed to initialize map');
    }

    return () => {
      markers.current.forEach(marker => marker.remove());
      markers.current = [];
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Render markers when layers change
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    // Clear old markers if REPLACE action
    if (mapAction === 'REPLACE') {
      markers.current.forEach(marker => marker.remove());
      markers.current = [];
    }

    // Render new markers
    mapLayers.forEach((layer) => {
      if (layer.geometryType === 'Point' && layer.data?.features) {
        layer.data.features.forEach((feature: any) => {
          const { icon, color, size = 1 } = layer.style;
          const { coordinates } = feature.geometry;
          const properties = feature.properties || {};

          // Get the icon component
          const IconComponent = IconLibrary[icon as keyof typeof IconLibrary] || IconLibrary.UNKNOWN;
          
          // Determine color based on severity or use provided color
          const markerColor = getMarkerColor(properties, color);

          // Create marker container
          const markerContainer = document.createElement('div');
          markerContainer.className = 'custom-marker';
          markerContainer.style.cursor = 'pointer';

          // Render React icon into container
          const root = createRoot(markerContainer);
          root.render(
            <div
              style={{
                backgroundColor: markerColor,
                borderRadius: '50%',
                padding: `${8 * size}px`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px solid white',
                boxShadow: '0 2px 10px rgba(0,0,0,0.4)',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              <IconComponent color="white" size={20 * size} strokeWidth={2.5} />
            </div>
          );

          // Create Mapbox marker
          const marker = new mapboxgl.Marker(markerContainer)
            .setLngLat(coordinates)
            .addTo(map.current!);

          // Add popup on hover
          const popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false,
            offset: 15,
            className: 'custom-popup'
          });

          markerContainer.addEventListener('mouseenter', () => {
            const tooltipContent = `
              <div style="
                padding: 12px;
                background: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
              ">
                <strong style="
                  color: ${markerColor};
                  font-size: 14px;
                  display: block;
                  margin-bottom: 6px;
                ">${properties.type || properties.name || 'Incident'}</strong>
                <p style="
                  margin: 0;
                  font-size: 12px;
                  color: #cbd5e1;
                  line-height: 1.4;
                ">${properties.summary || properties.capacity || 'Click for details'}</p>
              </div>
            `;
            
            popup.setLngLat(coordinates).setHTML(tooltipContent).addTo(map.current!);
          });

          markerContainer.addEventListener('mouseleave', () => {
            popup.remove();
          });

          // Add click handler
          markerContainer.addEventListener('click', () => {
            setSelectedFeature({
              ...properties,
              layerName: layer.layerName,
              coordinates: coordinates
            });
            setIsDialogOpen(true);
            popup.remove();
          });

          markers.current.push(marker);
        });
      } else if (layer.geometryType === 'Polygon') {
        // Handle polygons (existing code)
        const sourceId = `source-${layer.layerId}`;
        
        if (!map.current?.getSource(sourceId)) {
          map.current?.addSource(sourceId, {
            type: 'geojson',
            data: layer.data
          });
        }

        if (!map.current?.getLayer(`layer-${layer.layerId}`)) {
          map.current?.addLayer({
            id: `layer-${layer.layerId}`,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': layer.style.fillColor || '#FF851B',
              'fill-opacity': layer.style.fillOpacity || 0.5
            }
          });

          map.current?.addLayer({
            id: `layer-${layer.layerId}-outline`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': layer.style.fillColor || '#FF851B',
              'line-width': 2
            }
          });
        }
      }
    });

    // Fit map to show all markers
    if (mapLayers.length > 0 && map.current) {
      fitMapToBounds(mapLayers, map.current);
    }
  }, [mapLayers, mapAction]);

  // Handle viewState bounds (legacy support)
  useEffect(() => {
    if (!map.current || !viewState.bounds) return;

    const { southwest, northeast } = viewState.bounds;
    map.current.fitBounds(
      [
        [southwest.lon, southwest.lat],
        [northeast.lon, northeast.lat]
      ],
      { padding: 50, duration: 1000 }
    );
  }, [viewState]);

  if (mapError) {
    return (
      <div className="w-full h-full bg-slate-900 flex items-center justify-center p-8">
        <div className="max-w-2xl text-center">
          <div className="text-red-500 text-xl font-bold mb-4">⚠️ Map Configuration Required</div>
          <div className="text-slate-300 mb-6">{mapError}</div>
          <div className="bg-slate-800 p-6 rounded-lg text-left">
            <div className="text-sm text-slate-400 mb-4">To fix this:</div>
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-300">
              <li>Go to <a href="https://account.mapbox.com/access-tokens/" target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">Mapbox Access Tokens</a></li>
              <li>Create a new <strong>PUBLIC</strong> token (starts with <code className="bg-slate-700 px-1">pk.</code>)</li>
              <li>Check these scopes: <code className="bg-slate-700 px-1">styles:read</code>, <code className="bg-slate-700 px-1">fonts:read</code>, <code className="bg-slate-700 px-1">datasets:read</code></li>
              <li>Copy the token</li>
              <li>Edit <code className="bg-slate-700 px-1">.env.local</code> and set:<br/>
                <code className="bg-slate-700 px-2 py-1 block mt-2">NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_token_here</code>
              </li>
              <li>Restart the dev server: <code className="bg-slate-700 px-1">npm run dev</code></li>
            </ol>
          </div>
          <div className="mt-6 text-xs text-slate-500">
            Note: Never use secret tokens (sk.*) in browser code!
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div ref={mapContainer} className="w-full h-full" />
      
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-100">
              {selectedFeature?.type || selectedFeature?.name || 'Incident Details'}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedFeature?.layerName}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {selectedFeature?.incidentId && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Incident ID</div>
                <div className="text-slate-100">{selectedFeature.incidentId}</div>
              </div>
            )}
            
            {selectedFeature?.summary && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Summary</div>
                <div className="text-slate-100">{selectedFeature.summary}</div>
              </div>
            )}
            
            {selectedFeature?.severity && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Severity</div>
                <div className={`inline-block px-2 py-1 rounded text-sm font-semibold ${
                  selectedFeature.severity === 'CRITICAL' ? 'bg-red-900 text-red-200' :
                  selectedFeature.severity === 'HIGH' ? 'bg-orange-900 text-orange-200' :
                  'bg-yellow-900 text-yellow-200'
                }`}>
                  {selectedFeature.severity}
                </div>
              </div>
            )}
            
            {selectedFeature?.reportedAt && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Reported At</div>
                <div className="text-slate-100">
                  {new Date(selectedFeature.reportedAt).toLocaleString()}
                </div>
              </div>
            )}
            
            {selectedFeature?.coordinates && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Location</div>
                <div className="text-slate-100 font-mono text-sm">
                  {selectedFeature.coordinates[1].toFixed(4)}, {selectedFeature.coordinates[0].toFixed(4)}
                </div>
              </div>
            )}

            {selectedFeature?.siteId && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Site ID</div>
                <div className="text-slate-100">{selectedFeature.siteId}</div>
              </div>
            )}
            
            {selectedFeature?.name && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Name</div>
                <div className="text-slate-100">{selectedFeature.name}</div>
              </div>
            )}
            
            {selectedFeature?.capacity && (
              <div>
                <div className="text-sm font-semibold text-slate-400">Capacity</div>
                <div className="text-slate-100">{selectedFeature.capacity}</div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
