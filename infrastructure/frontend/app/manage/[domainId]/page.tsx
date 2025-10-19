'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { checkAuthStatus, logout, getStoredUser } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import { Button } from '@/components/ui/button';
import ViewModeSwitcher from '@/components/ViewModeSwitcher';
import DataTableView from '@/components/DataTableView';

export default function DomainDataPage() {
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const params = useParams();
  const domainId = params.domainId as string;
  const user = getStoredUser();

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-lg text-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
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
      <main className="flex-1 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Page Header */}
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              onClick={() => router.push('/manage')}
            >
              ← Back to Domains
            </Button>
            <h2 className="text-3xl font-bold text-foreground">Domain Data</h2>
          </div>

          {/* Data Table View */}
          <DataTableView domainId={domainId} />
        </div>
      </main>
    </div>
  );
}
