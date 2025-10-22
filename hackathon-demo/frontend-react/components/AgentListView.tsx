'use client';

import { useEffect, useState } from 'react';
import { Agent, listAgents } from '@/lib/api-client';
import { showErrorToast } from '@/lib/toast-utils';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Plus, Loader2 } from 'lucide-react';
import AgentCard from './AgentCard';

interface AgentListViewProps {
  onCreateAgent: () => void;
  onEditAgent: (agent: Agent) => void;
  onDeleteAgent: (agent: Agent) => void;
}

type FilterType = 'all' | 'builtin' | 'custom';

export default function AgentListView({
  onCreateAgent,
  onEditAgent,
  onDeleteAgent,
}: AgentListViewProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await listAgents();

      if (response.data?.agents) {
        setAgents(response.data.agents);
      } else if (response.error) {
        if (response.status !== 401 && response.status !== 403) {
          showErrorToast('Failed to load agents', response.error);
        }
        setAgents([]);
      }
    } catch (error) {
      console.error('Error loading agents:', error);
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const filteredAgents = agents.filter((agent) => {
    if (filter === 'builtin') return agent.is_builtin;
    if (filter === 'custom') return !agent.is_builtin;
    return true;
  });

  const builtinCount = agents.filter((a) => a.is_builtin).length;
  const customCount = agents.filter((a) => !a.is_builtin).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filters and create button */}
      <div className="flex items-center justify-between">
        <Tabs value={filter} onValueChange={(value) => setFilter(value as FilterType)}>
          <TabsList>
            <TabsTrigger value="all">
              All ({agents.length})
            </TabsTrigger>
            <TabsTrigger value="builtin">
              Built-in ({builtinCount})
            </TabsTrigger>
            <TabsTrigger value="custom">
              Custom ({customCount})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <Button onClick={onCreateAgent}>
          <Plus className="h-4 w-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Agent grid */}
      {filteredAgents.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            {filter === 'custom'
              ? 'No custom agents yet. Create your first agent to get started.'
              : 'No agents found.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              onEdit={onEditAgent}
              onDelete={onDeleteAgent}
            />
          ))}
        </div>
      )}
    </div>
  );
}
