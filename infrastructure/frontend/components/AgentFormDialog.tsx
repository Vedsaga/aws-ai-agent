'use client';

import { useState, useEffect } from 'react';
import { Agent, AgentConfig, createAgent, updateAgent, listAgents, getToolRegistry } from '@/lib/api-client';
import { showValidationErrorToast } from '@/lib/toast-utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { X, Plus } from 'lucide-react';

interface AgentFormDialogProps {
  agent?: Agent;
  isOpen: boolean;
  onClose: () => void;
  onSave: (agent: Agent) => void;
}

interface Tool {
  name: string;
  description: string;
  category: string;
}

interface OutputSchemaField {
  name: string;
  type: string;
}

const FIELD_TYPES = ['string', 'number', 'boolean', 'object', 'array'];

export default function AgentFormDialog({
  agent,
  isOpen,
  onClose,
  onSave,
}: AgentFormDialogProps) {
  const [agentType, setAgentType] = useState<'ingestion' | 'query'>('ingestion');
  const [agentName, setAgentName] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [outputSchema, setOutputSchema] = useState<OutputSchemaField[]>([
    { name: '', type: 'string' },
  ]);
  const [parentAgent, setParentAgent] = useState('');
  const [availableParents, setAvailableParents] = useState<Agent[]>([]);
  const [exampleJson, setExampleJson] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState('');
  const [loading, setLoading] = useState(false);

  // Load tools and agents on mount
  useEffect(() => {
    if (isOpen) {
      loadTools();
      loadParentAgents();
    }
  }, [isOpen]);

  // Populate form when editing
  useEffect(() => {
    if (agent && isOpen) {
      setAgentName(agent.agent_name);
      setAgentType(agent.agent_type === 'query' ? 'query' : 'ingestion');
      setSystemPrompt(agent.system_prompt);
      setSelectedTools(agent.tools || []);
      setParentAgent(agent.dependency_parent || '');
      setApiEndpoint(agent.api_endpoint || '');
      
      // Convert output schema to fields
      const fields = Object.entries(agent.output_schema || {}).map(([name, type]) => ({
        name,
        type: typeof type === 'string' ? type : 'string',
      }));
      setOutputSchema(fields.length > 0 ? fields : [{ name: '', type: 'string' }]);
    } else if (isOpen) {
      // Reset form for new agent
      resetForm();
    }
  }, [agent, isOpen]);

  const resetForm = () => {
    setAgentType('ingestion');
    setAgentName('');
    setSystemPrompt('');
    setSelectedTools([]);
    setOutputSchema([{ name: '', type: 'string' }]);
    setParentAgent('');
    setExampleJson('');
    setApiEndpoint('');
  };

  const loadTools = async () => {
    const response = await getToolRegistry();
    if (response.data?.tools) {
      setAvailableTools(response.data.tools);
    }
  };

  const loadParentAgents = async () => {
    const response = await listAgents();
    if (response.data?.agents) {
      // Only show built-in query agents as parent options
      const queryAgents = response.data.agents.filter(
        (a) => a.agent_type === 'query' && a.is_builtin
      );
      setAvailableParents(queryAgents);
    }
  };

  const validateForm = (): boolean => {
    const errors: string[] = [];

    if (!agentName.trim()) {
      errors.push('Agent name is required');
    }

    if (!systemPrompt.trim()) {
      errors.push('System prompt is required');
    }

    if (selectedTools.length === 0) {
      errors.push('At least one tool must be selected');
    }

    const validFields = outputSchema.filter((field) => field.name.trim() !== '');
    if (validFields.length === 0) {
      errors.push('At least one output field is required');
    }

    if (validFields.length > 5) {
      errors.push('Maximum 5 output fields allowed');
    }

    const fieldNames = validFields.map((f) => f.name);
    const duplicates = fieldNames.filter((name, index) => fieldNames.indexOf(name) !== index);
    if (duplicates.length > 0) {
      errors.push(`Duplicate field names: ${duplicates.join(', ')}`);
    }

    if (errors.length > 0) {
      showValidationErrorToast(errors);
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    const validFields = outputSchema.filter((field) => field.name.trim() !== '');
    const schemaObject = validFields.reduce((acc, field) => {
      acc[field.name] = { type: field.type, required: true };
      return acc;
    }, {} as Record<string, any>);

    const config: AgentConfig = {
      agent_name: agentName,
      agent_type: agentType === 'query' ? 'query' : 'ingestion',
      system_prompt: systemPrompt,
      tools: selectedTools,
      output_schema: schemaObject,
      ...(parentAgent && { dependency_parent: parentAgent }),
      ...(apiEndpoint && { api_endpoint: apiEndpoint }),
    };

    try {
      let response;
      if (agent) {
        response = await updateAgent(agent.agent_id, config);
      } else {
        response = await createAgent(config);
      }

      if (response.data) {
        onSave(response.data);
        onClose();
        resetForm();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddField = () => {
    if (outputSchema.length < 5) {
      setOutputSchema([...outputSchema, { name: '', type: 'string' }]);
    }
  };

  const handleRemoveField = (index: number) => {
    if (outputSchema.length > 1) {
      setOutputSchema(outputSchema.filter((_, i) => i !== index));
    }
  };

  const handleFieldChange = (index: number, field: 'name' | 'type', value: string) => {
    const newSchema = [...outputSchema];
    newSchema[index][field] = value;
    setOutputSchema(newSchema);
  };

  const handleToolToggle = (toolName: string) => {
    setSelectedTools((prev) =>
      prev.includes(toolName) ? prev.filter((t) => t !== toolName) : [...prev, toolName]
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{agent ? 'Edit Agent' : 'Create Agent'}</DialogTitle>
          <DialogDescription>
            {agent ? 'Update agent configuration' : 'Create a new custom agent'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Agent Type Toggle */}
          <div>
            <label className="text-sm font-medium mb-2 block">Agent Type</label>
            <Tabs value={agentType} onValueChange={(v) => setAgentType(v as 'ingestion' | 'query')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="ingestion">Data Ingest Agent</TabsTrigger>
                <TabsTrigger value="query">Data Query Agent</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Agent Name */}
          <div>
            <label htmlFor="agent-name" className="text-sm font-medium mb-2 block">
              Agent Name *
            </label>
            <Input
              id="agent-name"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="e.g., Priority Scorer"
              disabled={loading}
            />
          </div>

          {/* Parent Agent Selection (for query agents only) */}
          {agentType === 'query' && (
            <div>
              <label htmlFor="parent-agent" className="text-sm font-medium mb-2 block">
                Parent Agent (Optional)
              </label>
              <Select value={parentAgent} onValueChange={setParentAgent} disabled={loading}>
                <SelectTrigger>
                  <SelectValue placeholder="Select parent agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None</SelectItem>
                  {availableParents.map((parent) => (
                    <SelectItem key={parent.agent_id} value={parent.agent_id}>
                      {parent.agent_name}
                      {parent.interrogative && ` (${parent.interrogative})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                Chain this agent with a built-in query agent
              </p>
            </div>
          )}

          {/* Tool Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Tools * (Select at least one)
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto p-3 border rounded-md">
              {availableTools.map((tool) => (
                <label key={tool.name} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedTools.includes(tool.name)}
                    onChange={() => handleToolToggle(tool.name)}
                    disabled={loading}
                    className="rounded text-primary focus:ring-primary"
                  />
                  <span className="text-sm">{tool.name}</span>
                </label>
              ))}
            </div>
          </div>

          {/* System Prompt */}
          <div>
            <label htmlFor="system-prompt" className="text-sm font-medium mb-2 block">
              System Prompt *
            </label>
            <textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={4}
              placeholder="Describe what this agent should do..."
              disabled={loading}
              className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          {/* Output Schema */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-medium">Output Schema * (Max 5 keys)</label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleAddField}
                disabled={loading || outputSchema.length >= 5}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Field
              </Button>
            </div>

            <div className="space-y-2">
              {outputSchema.map((field, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={field.name}
                    onChange={(e) => handleFieldChange(index, 'name', e.target.value)}
                    placeholder="Field name"
                    disabled={loading}
                    className="flex-1"
                  />
                  <Select
                    value={field.type}
                    onValueChange={(value) => handleFieldChange(index, 'type', value)}
                    disabled={loading}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FIELD_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {outputSchema.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveField(index)}
                      disabled={loading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Example JSON (for ingest agents) */}
          {agentType === 'ingestion' && (
            <div>
              <label htmlFor="example-json" className="text-sm font-medium mb-2 block">
                Example Output JSON (Optional)
              </label>
              <textarea
                id="example-json"
                value={exampleJson}
                onChange={(e) => setExampleJson(e.target.value)}
                rows={4}
                placeholder='{"location": "string", "confidence": 0.95}'
                disabled={loading}
                className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono"
              />
            </div>
          )}

          {/* API Endpoint (optional) */}
          <div>
            <label htmlFor="api-endpoint" className="text-sm font-medium mb-2 block">
              Custom API Endpoint (Optional)
            </label>
            <Input
              id="api-endpoint"
              value={apiEndpoint}
              onChange={(e) => setApiEndpoint(e.target.value)}
              placeholder="https://api.example.com/endpoint"
              disabled={loading}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Saving...' : agent ? 'Update Agent' : 'Create Agent'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
