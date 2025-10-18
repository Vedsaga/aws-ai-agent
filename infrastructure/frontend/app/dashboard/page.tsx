'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { checkAuthStatus, logout, getStoredUser } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import IngestionPanel from '@/components/IngestionPanel';
import QueryPanel from '@/components/QueryPanel';

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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  const user = getStoredUser();

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Multi-Agent Orchestration System</h1>
            {user && (
              <p className="text-sm text-gray-600">
                {user.email} | Tenant: {user.tenantId || 'N/A'}
              </p>
            )}
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => router.push('/config')}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Configure Agents
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
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
        <div className="w-1/5 h-full flex flex-col bg-white border-l border-gray-200">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('ingest')}
              className={`flex-1 px-4 py-3 text-sm font-medium focus:outline-none ${
                activeTab === 'ingest'
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Submit Report
            </button>
            <button
              onClick={() => setActiveTab('query')}
              className={`flex-1 px-4 py-3 text-sm font-medium focus:outline-none ${
                activeTab === 'query'
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Ask Question
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'ingest' ? (
              <IngestionPanel />
            ) : (
              <QueryPanel onVisualizationUpdate={handleVisualizationUpdate} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
