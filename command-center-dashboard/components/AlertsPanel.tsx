'use client';

import { useStore } from '@/store/useStore';
import { Card } from '@/components/ui/card';

export default function AlertsPanel() {
  const { criticalAlerts, zoomToLocation } = useStore();

  const handleAlertClick = (alert: any) => {
    if (alert.location && zoomToLocation) {
      zoomToLocation(alert.location.lat, alert.location.lon, 16);
    }
  };

  if (criticalAlerts.length === 0) {
    return (
      <div className="p-4">
        <h3 className="text-sm font-semibold mb-2">Critical Alerts</h3>
        <p className="text-xs text-slate-400">No critical alerts at this time.</p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-sm font-semibold mb-2">Critical Alerts</h3>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {criticalAlerts.map((alert, index) => (
          <Card 
            key={`${alert.alertId}-${index}`} 
            className="p-3 bg-red-900/30 border-red-700 cursor-pointer hover:bg-red-900/40 transition-colors"
            onClick={() => handleAlertClick(alert)}
          >
            <div className="flex items-start justify-between mb-1">
              <span className="text-xs font-semibold text-red-400">{alert.severity}</span>
              <span className="text-xs text-slate-400">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="text-sm font-medium mb-1">{alert.title}</div>
            <div className="text-xs text-slate-300">{alert.summary}</div>
            {alert.location && (
              <div className="text-xs text-slate-500 mt-2">
                📍 Click to view on map
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
