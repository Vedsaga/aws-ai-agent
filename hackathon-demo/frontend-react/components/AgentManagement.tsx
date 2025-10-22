'use client';

import { useState } from 'react';
import { Agent, deleteAgent } from '@/lib/api-client';
import { showErrorToast, showSuccessToast } from '@/lib/toast-utils';
import AgentListView from './AgentListView';
import AgentFormDialog from './AgentFormDialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export default function AgentManagement() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | undefined>(undefined);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deleting, setDeleting] = useState(false);

  const handleCreateAgent = () => {
    setSelectedAgent(undefined);
    setIsFormOpen(true);
  };

  const handleEditAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    setIsFormOpen(true);
  };

  const handleDeleteAgent = (agent: Agent) => {
    setAgentToDelete(agent);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!agentToDelete) return;

    setDeleting(true);
    try {
      const response = await deleteAgent(agentToDelete.agent_id);

      if (response.status === 200 || response.status === 204) {
        // Success toast is already shown by API client
        setIsDeleteDialogOpen(false);
        setAgentToDelete(null);
        // Refresh the agent list
        setRefreshKey((prev) => prev + 1);
      } else if (response.error) {
        // Error toast is already shown by API client
      }
    } catch (error) {
      console.error('Error deleting agent:', error);
      showErrorToast('Failed to delete agent', 'An unexpected error occurred');
    } finally {
      setDeleting(false);
    }
  };

  const handleSaveAgent = (agent: Agent) => {
    // Success toast is already shown by API client
    setIsFormOpen(false);
    setSelectedAgent(undefined);
    // Refresh the agent list
    setRefreshKey((prev) => prev + 1);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setSelectedAgent(undefined);
  };

  const handleCancelDelete = () => {
    setIsDeleteDialogOpen(false);
    setAgentToDelete(null);
  };

  return (
    <div>
      {/* Agent List View with key for refresh */}
      <AgentListView
        key={refreshKey}
        onCreateAgent={handleCreateAgent}
        onEditAgent={handleEditAgent}
        onDeleteAgent={handleDeleteAgent}
      />

      {/* Agent Form Dialog */}
      <AgentFormDialog
        agent={selectedAgent}
        isOpen={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleSaveAgent}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Agent</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{agentToDelete?.agent_name}&quot;? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancelDelete} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
