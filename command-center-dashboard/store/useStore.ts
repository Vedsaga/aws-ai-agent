import { create } from 'zustand';

export interface MapLayer {
  layerId: string;
  layerName: string;
  geometryType: 'Point' | 'Polygon' | 'LineString';
  style: any;
  data: any;
}

export interface Alert {
  alertId: string;
  timestamp: string;
  severity: string;
  title: string;
  summary: string;
  location?: { lat: number; lon: number };
}

export interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  timestamp: string;
}

export interface SuggestedAction {
  label: string;
  actionId: string;
  payload?: any;
}

interface StoreState {
  simulationTime: string;
  timestamp: string;
  activeDomainFilter: string;
  mapAction: 'REPLACE' | 'APPEND';
  viewState: {
    bounds?: {
      southwest: { lat: number; lon: number };
      northeast: { lat: number; lon: number };
    };
  };
  mapLayers: MapLayer[];
  chatHistory: ChatMessage[];
  criticalAlerts: Alert[];
  suggestedActions: SuggestedAction[];
  isLoading: boolean;
  mapInstance: any;
  zoomToLocation: ((lat: number, lon: number, zoom?: number) => void) | null;
  
  setSimulationTime: (time: string) => void;
  setTimestamp: (timestamp: string) => void;
  setActiveDomainFilter: (filter: string) => void;
  setMapAction: (action: 'REPLACE' | 'APPEND') => void;
  setViewState: (viewState: any) => void;
  setMapLayers: (layers: MapLayer[]) => void;
  appendMapLayers: (layers: MapLayer[]) => void;
  addChatMessage: (message: ChatMessage) => void;
  addCriticalAlert: (alert: Alert) => void;
  setSuggestedActions: (actions: SuggestedAction[]) => void;
  setIsLoading: (loading: boolean) => void;
  updateFromResponse: (response: any) => void;
  setMapInstance: (mapInstance: any, zoomFn: (lat: number, lon: number, zoom?: number) => void) => void;
}

export const useStore = create<StoreState>((set) => ({
  simulationTime: 'Day 0, 00:00',
  timestamp: '2023-02-06T00:00:00Z',
  activeDomainFilter: 'CRITICAL',
  mapAction: 'REPLACE',
  viewState: {},
  mapLayers: [],
  chatHistory: [],
  criticalAlerts: [],
  suggestedActions: [],
  isLoading: false,
  mapInstance: null,
  zoomToLocation: null,

  setSimulationTime: (time) => set({ simulationTime: time }),
  setTimestamp: (timestamp) => {
    set({ timestamp });
    if (typeof window !== 'undefined') {
      localStorage.setItem('simulationTimestamp', timestamp);
    }
  },
  setActiveDomainFilter: (filter) => set({ activeDomainFilter: filter }),
  setMapAction: (action) => set({ mapAction: action }),
  setViewState: (viewState) => set({ viewState }),
  setMapLayers: (layers) => set({ mapLayers: layers }),
  appendMapLayers: (layers) => set((state) => ({ 
    mapLayers: [...state.mapLayers, ...layers] 
  })),
  addChatMessage: (message) => set((state) => ({ 
    chatHistory: [...state.chatHistory, message] 
  })),
  addCriticalAlert: (alert) => set((state) => {
    // Check if alert already exists
    const exists = state.criticalAlerts.some(a => a.alertId === alert.alertId);
    if (exists) return state;
    return { criticalAlerts: [...state.criticalAlerts, alert] };
  }),
  setSuggestedActions: (actions) => set({ suggestedActions: actions }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  updateFromResponse: (response) => set((state) => {
    const updates: any = {};
    
    if (response.simulationTime) updates.simulationTime = response.simulationTime;
    if (response.timestamp) {
      updates.timestamp = response.timestamp;
      if (typeof window !== 'undefined') {
        localStorage.setItem('simulationTimestamp', response.timestamp);
      }
    }
    if (response.mapAction) updates.mapAction = response.mapAction;
    if (response.viewState) updates.viewState = response.viewState;
    if (response.clientStateHint?.activeDomainFilter) {
      updates.activeDomainFilter = response.clientStateHint.activeDomainFilter;
    }
    
    if (response.mapLayers) {
      if (response.mapAction === 'REPLACE') {
        updates.mapLayers = response.mapLayers;
      } else {
        updates.mapLayers = [...state.mapLayers, ...response.mapLayers];
      }
    }
    
    if (response.uiContext?.suggestedActions) {
      updates.suggestedActions = response.uiContext.suggestedActions;
    }
    
    return updates;
  }),
  
  setMapInstance: (mapInstance, zoomFn) => set({ 
    mapInstance, 
    zoomToLocation: zoomFn 
  }),
}));
