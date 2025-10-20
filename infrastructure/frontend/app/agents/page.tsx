'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { checkAuthStatus, logout, getStoredUser } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import AgentManagement from '@/components/AgentManagement';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function AgentsPage() {
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-lg text-foreground">Loading...</div>
      </div>
    );
  }

  const user = getStoredUser();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm border-b border-border">
        <div className="px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/dashboard')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Agent Management</h1>
              {user && (
                <p className="text-sm text-muted-foreground">
                  {user.email} | Tenant: {user.tenantId || 'N/A'}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={() => router.push('/manage')}
            >
              Manage Domains
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/config')}
            >
              Configure Agents
            </Button>
            <Button variant="destructive" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-6 py-8">
        <AgentManagement />
      </main>
    </div>
  );
}
