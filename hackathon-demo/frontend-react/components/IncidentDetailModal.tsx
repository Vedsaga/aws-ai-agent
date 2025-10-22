'use client';

import { useEffect, useRef, memo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CATEGORY_COLORS } from '@/lib/category-config';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface Incident {
  id: string;
  domain_id: string;
  raw_text: string;
  structured_data: Record<string, any>;
  location?: { latitude: number; longitude: number };
  created_at: string;
  images?: string[];
}

interface IncidentDetailModalProps {
  incident: Incident | null;
  isOpen: boolean;
  onClose: () => void;
}

const IncidentDetailModal = memo(function IncidentDetailModal({
  incident,
  isOpen,
  onClose,
}: IncidentDetailModalProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!isOpen || !incident || !incident.location || !mapContainerRef.current) {
      return;
    }

    // Initialize map
    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!mapboxToken) {
      console.error('Mapbox token not found');
      return;
    }

    mapboxgl.accessToken = mapboxToken;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [incident.location.longitude, incident.location.latitude],
      zoom: 14,
    });

    // Add marker
    new mapboxgl.Marker({ color: '#EF4444' })
      .setLngLat([incident.location.longitude, incident.location.latitude])
      .addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [isOpen, incident]);

  if (!incident) {
    return null;
  }

  const category =
    incident.structured_data.entity_agent?.category ||
    incident.structured_data.civic_entity_agent?.category ||
    'default';
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
              style={{
                background: colors.bg,
                border: `3px solid ${colors.border}`,
              }}
            >
              {colors.icon}
            </div>
            <div>
              <DialogTitle className="text-xl">Incident Details</DialogTitle>
              <p className="text-sm text-muted-foreground">
                ID: {incident.id} • {formatDate(incident.created_at)}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Category Badge */}
          <div>
            <Badge
              style={{
                background: colors.bg,
                color: 'white',
              }}
            >
              {category}
            </Badge>
          </div>

          {/* Original Report */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Original Report</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{incident.raw_text}</p>
            </CardContent>
          </Card>

          {/* Structured Data */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Extracted Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(incident.structured_data).map(
                  ([agentName, agentData]) => (
                    <div
                      key={agentName}
                      className="p-3 bg-muted/50 rounded-lg space-y-2"
                    >
                      <h4 className="text-sm font-semibold">
                        {agentName
                          .replace(/_/g, ' ')
                          .replace(/\b\w/g, (l) => l.toUpperCase())}
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        {typeof agentData === 'object' &&
                          agentData !== null &&
                          Object.entries(agentData).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="text-muted-foreground font-medium">
                                {key.replace(/_/g, ' ')}:
                              </span>{' '}
                              <span>
                                {typeof value === 'object'
                                  ? JSON.stringify(value)
                                  : String(value)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            </CardContent>
          </Card>

          {/* Images */}
          {incident.images && incident.images.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Evidence Images</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2">
                  {incident.images.map((imageUrl, i) => (
                    <div
                      key={i}
                      className="relative aspect-square cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => window.open(imageUrl, '_blank')}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={imageUrl}
                        alt={`Evidence ${i + 1}`}
                        className="w-full h-full object-cover rounded-lg"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Location Map */}
          {incident.location && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Location</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Coordinates: {incident.location.latitude.toFixed(6)},{' '}
                    {incident.location.longitude.toFixed(6)}
                  </p>
                  <div
                    ref={mapContainerRef}
                    className="w-full h-64 rounded-lg border"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
});

export default IncidentDetailModal;
