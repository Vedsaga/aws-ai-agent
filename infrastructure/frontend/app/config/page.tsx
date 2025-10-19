'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { checkAuthStatus, logout } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import AgentCreationForm from '@/components/AgentCreationForm';

// Dynamic import to avoid SSR issues with ReactFlow
const DependencyGraphEditor = dynamic(() => import('@/components/DependencyGraphEditor'), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center">Loading graph...</div>,
});

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState<'create' | 'graph'>('create');
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

  const handleAgentCreated = () => {
    // Refresh graph when new agent is created
    setActiveTab('graph');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-lg text-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm border-b border-border">
        <div className="px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">Agent Configuration</h1>
          <div className="flex gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 text-sm font-medium text-foreground bg-card border border-border rounded-md hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              Back to Dashboard
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

      {/* Tabs */}
      <div className="bg-card border-b border-border">
        <div className="px-6">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('create')}
              className={`py-4 text-sm font-medium border-b-2 focus:outline-none ${
                activeTab === 'create'
                  ? 'text-primary border-primary'
                  : 'text-muted-foreground border-transparent hover:text-foreground hover:border-border'
              }`}
            >
              Create Agent
            </button>
            <button
              onClick={() => setActiveTab('graph')}
              className={`py-4 text-sm font-medium border-b-2 focus:outline-none ${
                activeTab === 'graph'
                  ? 'text-primary border-primary'
                  : 'text-muted-foreground border-transparent hover:text-foreground hover:border-border'
              }`}
            >
              Dependency Graph
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {activeTab === 'create' ? (
          <AgentCreationForm onSuccess={handleAgentCreated} />
        ) : (
          <div className="h-full bg-card rounded-lg shadow-md border border-border">
            <DependencyGraphEditor />
          </div>
        )}
      </div>
    </div>
  );
}
