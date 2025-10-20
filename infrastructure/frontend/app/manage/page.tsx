'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { checkAuthStatus, logout, getStoredUser } from '@/lib/auth';
import { configureAmplify } from '@/lib/amplify-config';
import { listDomains } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import ViewModeSwitcher from '@/components/ViewModeSwitcher';
import DomainCreationWizard from '@/components/DomainCreationWizard';
import { MessageSquare, FileText } from 'lucide-react';

interface Domain {
  domain_id: string;
  template_name: string;
  description: string;
  agent_configs?: any[];
  playbook_configs?: any[];
  created_by: string;
  created_at: string | number;
  is_builtin?: boolean;
  agent_count?: number;
  incident_count?: number;
}

export default function ManagePage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const router = useRouter();
  const user = getStoredUser();

  useEffect(() => {
    configureAmplify();
    
    checkAuthStatus().then((isAuthenticated) => {
      if (!isAuthenticated) {
        router.push('/login');
      } else {
        fetchDomains();
      }
    });
  }, [router]);

  const fetchDomains = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listDomains();
      
      if (response.error) {
        // Only show error for non-auth errors
        if (response.status !== 401 && response.status !== 403) {
          setError(response.error);
        }
      } else if (response.data && response.data.domains) {
        setDomains(response.data.domains);
      }
    } catch (err) {
      console.error('Failed to fetch domains:', err);
      setError('Failed to load domains');
    } finally {
      setLoading(false);
    }
  };

  const handleDomainCreated = () => {
    fetchDomains(); // Refresh the list
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const getIngestionAgentCount = (domain: Domain) => {
    return domain.agent_configs?.filter((agent: any) => agent.agent_type === 'ingestion').length || 0;
  };

  const getQueryAgentCount = (domain: Domain) => {
    return domain.agent_configs?.filter((agent: any) => agent.agent_type === 'query').length || 0;
  };

  const handleAskQuestion = (domainId: string) => {
    // Navigate to dashboard with domain selected and query panel active
    router.push(`/dashboard?domain=${domainId}&panel=query`);
  };

  const handleSubmitReport = (domainId: string) => {
    // Navigate to dashboard with domain selected and ingestion panel active
    router.push(`/dashboard?domain=${domainId}&panel=ingest`);
  };

  const isCreatedByMe = (domain: Domain) => {
    return user && domain.created_by === user.userId;
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
          <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold text-foreground">Manage Domains</h2>
            <Button onClick={() => setShowCreateWizard(true)}>
              Create New Domain
            </Button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Domain Grid */}
          {domains.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground text-lg">No domains found</p>
              <Button onClick={() => setShowCreateWizard(true)} className="mt-4">
                Create Your First Domain
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {domains.map((domain) => (
                <Card 
                  key={domain.domain_id} 
                  className="hover:border-primary transition-colors"
                >
                  <CardHeader>
                    <div className="flex justify-between items-start gap-2">
                      <CardTitle className="text-xl">{domain.template_name}</CardTitle>
                      <div className="flex flex-wrap gap-1">
                        {domain.is_builtin && (
                          <Badge variant="secondary" className="text-xs">Built-in</Badge>
                        )}
                        {isCreatedByMe(domain) && (
                          <Badge variant="default" className="text-xs">Created by me</Badge>
                        )}
                        {!domain.is_builtin && !isCreatedByMe(domain) && (
                          <Badge variant="outline" className="text-xs">Public</Badge>
                        )}
                      </div>
                    </div>
                    <CardDescription>{domain.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Ingestion Agents:</span>
                        <span className="font-medium">{getIngestionAgentCount(domain)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Query Agents:</span>
                        <span className="font-medium">{getQueryAgentCount(domain)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Agents:</span>
                        <span className="font-medium">{domain.agent_count || domain.agent_configs?.length || 0}</span>
                      </div>
                      {domain.incident_count !== undefined && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Incidents:</span>
                          <span className="font-medium">{domain.incident_count}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleAskQuestion(domain.domain_id)}
                      className="flex-1"
                    >
                      <MessageSquare className="h-4 w-4 mr-1" />
                      Ask Question
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleSubmitReport(domain.domain_id)}
                      className="flex-1"
                    >
                      <FileText className="h-4 w-4 mr-1" />
                      Submit Report
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Domain Creation Wizard */}
      <DomainCreationWizard
        isOpen={showCreateWizard}
        onClose={() => setShowCreateWizard(false)}
        onComplete={handleDomainCreated}
      />
    </div>
  );
}
