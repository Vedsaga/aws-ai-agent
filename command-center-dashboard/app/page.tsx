'use client';

import { useEffect } from 'react';
import dynamic from 'next/dynamic';
import InteractionPanel from '@/components/InteractionPanel';
import { useStore } from '@/store/useStore';
import { mockApiService } from '@/services/mockApiService';

const MapComponent = dynamic(() => import('@/components/MapComponent'), {
  ssr: false,
  loading: () => <div className="w-full h-full bg-gray-900 flex items-center justify-center">Loading map...</div>
});

export default function Home() {
  const { 
    timestamp, 
    activeDomainFilter, 
    updateFromResponse, 
    addChatMessage, 
    addCriticalAlert,
    setTimestamp 
  } = useStore();

  useEffect(() => {
    const savedTimestamp = localStorage.getItem('simulationTimestamp');
    if (savedTimestamp) {
      setTimestamp(savedTimestamp);
    }

    const loadInitialData = async () => {
      try {
        const response = await mockApiService.getInitialLoad();
        
        const agentMessage = {
          role: 'agent' as const,
          content: response.chatResponse,
          timestamp: response.timestamp
        };
        
        addChatMessage(agentMessage);
        updateFromResponse(response);
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    };

    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await mockApiService.getUpdates(timestamp, activeDomainFilter);
        
        if (response.mapUpdates?.mapLayers) {
          updateFromResponse({
            mapAction: response.mapUpdates.mapAction,
            mapLayers: response.mapUpdates.mapLayers
          });
        }
        
        if (response.criticalAlerts && response.criticalAlerts.length > 0) {
          response.criticalAlerts.forEach((alert) => {
            addCriticalAlert(alert);
          });
        }
      } catch (error) {
        console.error('Error polling updates:', error);
      }
    }, 5000);

    return () => clearInterval(pollInterval);
  }, [timestamp, activeDomainFilter, updateFromResponse, addCriticalAlert]);

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-slate-950 text-white">
      <div className="w-[80%] h-full">
        <MapComponent />
      </div>
      <div className="w-[20%] h-full">
        <InteractionPanel />
      </div>
    </div>
  );
}
