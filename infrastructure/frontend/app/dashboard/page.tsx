'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { checkAuthStatus, logout, getStoredUser } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import IngestionPanel from '@/components/IngestionPanel';
import QueryPanel from '@/components/QueryPanel';
import ChatHistory from '@/components/ChatHistory';
import ViewModeSwitcher from '@/components/ViewModeSwitcher';

// Dynamic import for MapView to avoid SSR issues with Mapbox
const MapView = dynamic(() => import('@/components/MapView'), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center">Loading map...</div>,
});

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'ingest' | 'query'>('ingest');
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    configureAmplify();
    
    checkAuthStatus().then((isAuthenticated) => {
      if (!isAuthenticated) {
        router.push('/login');
      } else {
        setLoading(false);
      }
    });
  }, [router]);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const handleVisualizationUpdate = (viz: any) => {
    // Handle map visualization updates from query results
    console.log('Visualization update:', viz);
    // TODO: Update map with query results
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-lg text-foreground">Loading...</div>
      </div>
    );
  }

  const user = getStoredUser();

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm border-b border-border">
        <div className="px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Multi-Agent Orchestration System</h1>
            {user && (
              <p className="text-sm text-muted-foreground">
                {user.email} | Tenant: {user.tenantId || 'N/A'}
              </p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <ViewModeSwitcher className="w-64" />
            <button
              onClick={() => router.push('/config')}
              className="px-4 py-2 text-sm font-medium text-foreground bg-card border border-border rounded-md hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              Configure Agents
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-destructive-foreground bg-destructive rounded-md hover:bg-destructive/90 focus:outline-none focus:ring-2 focus:ring-ring"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map View (80% width) */}
        <div className="w-4/5 h-full">
          <MapView />
        </div>

        {/* Chat Interface (20% width) */}
        <div className="w-1/5 h-full flex flex-col bg-card border-l border-border">
          {/* Tabs */}
          <div className="flex border-b border-border">
            <button
              onClick={() => setActiveTab('ingest')}
              className={`flex-1 px-4 py-3 text-sm font-medium focus:outline-none ${
                activeTab === 'ingest'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Submit Report
            </button>
            <button
              onClick={() => setActiveTab('query')}
              className={`flex-1 px-4 py-3 text-sm font-medium focus:outline-none ${
                activeTab === 'query'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Ask Question
            </button>
          </div>

          {/* Panel Content - Split into input (60%) and chat history (40%) */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="h-3/5 overflow-hidden border-b border-border">
              {activeTab === 'ingest' ? (
                <IngestionPanel />
              ) : (
                <QueryPanel onVisualizationUpdate={handleVisualizationUpdate} />
              )}
            </div>
            <div className="h-2/5 overflow-hidden">
              <ChatHistory />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
