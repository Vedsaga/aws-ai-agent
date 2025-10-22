'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { listAgents, createDomain } from '@/lib/api-client';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import DependencyGraphVisualization from './DependencyGraphVisualization';
import AgentSelectionCard from './AgentSelectionCard';

interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, any>;
  dependency_parent?: string;
  interrogative?: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  updated_at: number;
}

interface Domain {
  template_id: string;
  template_name: string;
  domain_id: string;
  description: string;
  ingest_agent_ids: string[];
  query_agent_ids: string[];
}

interface DomainCreationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (domain: Domain) => void;
}

export default function DomainCreationWizard({ isOpen, onClose, onComplete }: DomainCreationWizardProps) {
  const [stage, setStage] = useState<1 | 2>(1);
  const [selectedIngestAgents, setSelectedIngestAgents] = useState<string[]>([]);
  const [selectedQueryAgents, setSelectedQueryAgents] = useState<string[]>([]);
  const [domainName, setDomainName] = useState('');
  const [domainDescription, setDomainDescription] = useState('');
  const [allAgents, setAllAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadAgents();
    }
  }, [isOpen]);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const response = await listAgents();
      if (response.data?.agents) {
        setAllAgents(response.data.agents);
      } else if (response.error) {
        showErrorToast('Failed to load agents', response.error);
      }
    } catch (error) {
      console.error('Error loading agents:', error);
      showErrorToast('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const ingestAgents = allAgents.filter(a => a.agent_type === 'ingestion');
  const queryAgents = allAgents.filter(a => a.agent_type === 'query');

  const canProceedToStage2 = selectedIngestAgents.length > 0 && domainName.trim() !== '';
  const canCreate = selectedIngestAgents.length > 0 && selectedQueryAgents.length > 0 && domainName.trim() !== '';

  const handleCreate = async () => {
    if (!canCreate) return;

    setCreating(true);
    try {
      const config = {
        template_name: domainName,
        domain_id: domainName.toLowerCase().replace(/\s+/g, '_'),
        description: domainDescription,
        ingest_agent_ids: selectedIngestAgents,
        query_agent_ids: selectedQueryAgents,
      };

      const response = await createDomain(config);
      if (response.data) {
        showSuccessToast('Domain created successfully');
        onComplete(response.data);
        handleClose();
      } else if (response.error) {
        showErrorToast('Failed to create domain', response.error);
      }
    } catch (error) {
      console.error('Error creating domain:', error);
      showErrorToast('Failed to create domain');
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    // Reset state
    setStage(1);
    setSelectedIngestAgents([]);
    setSelectedQueryAgents([]);
    setDomainName('');
    setDomainDescription('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Domain - Stage {stage} of 2</DialogTitle>
        </DialogHeader>

        {/* Domain Info */}
        <div className="space-y-4 mb-6">
          <div>
            <Label htmlFor="domain-name">Domain Name *</Label>
            <Input
              id="domain-name"
              value={domainName}
              onChange={(e) => setDomainName(e.target.value)}
              placeholder="e.g., Traffic Management"
              disabled={creating}
            />
          </div>
          <div>
            <Label htmlFor="domain-description">Description</Label>
            <Textarea
              id="domain-description"
              value={domainDescription}
              onChange={(e) => setDomainDescription(e.target.value)}
              placeholder="Describe the domain purpose"
              rows={3}
              disabled={creating}
            />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-muted-foreground">Loading agents...</div>
        ) : (
          <>
            {/* Stage 1: Select Ingest Agents */}
            {stage === 1 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Select Data Ingest Agents (Required)</h3>
                  <Badge variant={selectedIngestAgents.length > 0 ? 'default' : 'secondary'}>
                    {selectedIngestAgents.length} selected
                  </Badge>
                </div>

                {ingestAgents.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No ingestion agents available
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {ingestAgents.map((agent) => (
                      <AgentSelectionCard
                        key={agent.agent_id}
                        agent={agent}
                        selected={selectedIngestAgents.includes(agent.agent_id)}
                        onToggle={() => {
                          if (selectedIngestAgents.includes(agent.agent_id)) {
                            setSelectedIngestAgents(selectedIngestAgents.filter(id => id !== agent.agent_id));
                          } else {
                            setSelectedIngestAgents([...selectedIngestAgents, agent.agent_id]);
                          }
                        }}
                        disabled={creating}
                      />
                    ))}
                  </div>
                )}

                <Button
                  onClick={() => setStage(2)}
                  disabled={!canProceedToStage2 || creating}
                  className="w-full"
                >
                  Next: Select Query Agents
                </Button>
              </div>
            )}

            {/* Stage 2: Select Query Agents */}
            {stage === 2 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Select Data Query Agents (Required)</h3>
                  <Badge variant={selectedQueryAgents.length > 0 ? 'default' : 'secondary'}>
                    {selectedQueryAgents.length} selected
                  </Badge>
                </div>

                {queryAgents.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No query agents available
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {queryAgents.map((agent) => (
                      <AgentSelectionCard
                        key={agent.agent_id}
                        agent={agent}
                        selected={selectedQueryAgents.includes(agent.agent_id)}
                        onToggle={() => {
                          if (selectedQueryAgents.includes(agent.agent_id)) {
                            setSelectedQueryAgents(selectedQueryAgents.filter(id => id !== agent.agent_id));
                          } else {
                            setSelectedQueryAgents([...selectedQueryAgents, agent.agent_id]);
                          }
                        }}
                        disabled={creating}
                      />
                    ))}
                  </div>
                )}

                {/* Dependency Graph Visualization */}
                {(selectedIngestAgents.length > 0 || selectedQueryAgents.length > 0) && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold mb-2">Execution Flow</h4>
                    <DependencyGraphVisualization
                      ingestAgents={allAgents.filter(a => selectedIngestAgents.includes(a.agent_id))}
                      queryAgents={allAgents.filter(a => selectedQueryAgents.includes(a.agent_id))}
                    />
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setStage(1)}
                    className="flex-1"
                    disabled={creating}
                  >
                    Back
                  </Button>
                  <Button
                    onClick={handleCreate}
                    disabled={!canCreate || creating}
                    className="flex-1"
                  >
                    {creating ? 'Creating...' : 'Create Domain'}
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
