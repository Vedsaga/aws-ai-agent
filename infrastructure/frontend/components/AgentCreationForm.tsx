'use client';

import { useState, useEffect } from 'react';
import { createAgentConfig, getAgentConfigs, getToolRegistry } from '@/lib/api-client';

interface Tool {
  name: string;
  description: string;
  category: string;
}

interface Agent {
  id: string;
  name: string;
  type: string;
}

interface OutputSchemaField {
  name: string;
  type: string;
}

const FIELD_TYPES = ['string', 'number', 'boolean', 'object', 'array'];

export default function AgentCreationForm({ onSuccess }: { onSuccess?: () => void }) {
  const [agentName, setAgentName] = useState('');
  const [agentType, setAgentType] = useState<'ingestion' | 'query' | 'custom'>('custom');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [outputSchema, setOutputSchema] = useState<OutputSchemaField[]>([
    { name: '', type: 'string' },
  ]);
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [parentAgent, setParentAgent] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadTools();
    loadAgents();
  }, []);

  const loadTools = async () => {
    const response = await getToolRegistry();
    if (response.data?.tools) {
      setAvailableTools(response.data.tools);
    }
  };

  const loadAgents = async () => {
    const response = await getAgentConfigs();
    if (response.data?.configs) {
      setAvailableAgents(response.data.configs);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: string[] = [];

    if (!agentName.trim()) {
      newErrors.push('Agent name is required');
    }

    if (!systemPrompt.trim()) {
      newErrors.push('System prompt is required');
    }

    if (selectedTools.length === 0) {
      newErrors.push('At least one tool must be selected');
    }

    // Validate output schema
    const validFields = outputSchema.filter((field) => field.name.trim() !== '');
    if (validFields.length === 0) {
      newErrors.push('At least one output field is required');
    }

    if (validFields.length > 5) {
      newErrors.push('Maximum 5 output fields allowed');
    }

    // Check for duplicate field names
    const fieldNames = validFields.map((f) => f.name);
    const duplicates = fieldNames.filter((name, index) => fieldNames.indexOf(name) !== index);
    if (duplicates.length > 0) {
      newErrors.push(`Duplicate field names: ${duplicates.join(', ')}`);
    }

    // Validate single-level dependency
    if (parentAgent) {
      const parent = availableAgents.find((a) => a.id === parentAgent);
      if (parent) {
        // Check if parent has a dependency (would create multi-level)
        const parentConfig = availableAgents.find((a) => a.id === parentAgent);
        if (parentConfig && (parentConfig as any).dependency_parent) {
          newErrors.push('Cannot create multi-level dependencies. Parent agent already has a dependency.');
        }
      }
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleAddField = () => {
    if (outputSchema.length < 5) {
      setOutputSchema([...outputSchema, { name: '', type: 'string' }]);
    }
  };

  const handleRemoveField = (index: number) => {
    setOutputSchema(outputSchema.filter((_, i) => i !== index));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSuccess(false);

    const validFields = outputSchema.filter((field) => field.name.trim() !== '');
    const schemaObject = validFields.reduce((acc, field) => {
      acc[field.name] = field.type;
      return acc;
    }, {} as Record<string, string>);

    const config = {
      agent_name: agentName,
      agent_type: agentType,
      system_prompt: systemPrompt,
      tools: selectedTools,
      output_schema: schemaObject,
      ...(parentAgent && { dependency_parent: parentAgent }),
    };

    const response = await createAgentConfig(config);
    
    if (response.data?.config_id) {
      setSuccess(true);
      setErrors([]);
      
      // Reset form
      setTimeout(() => {
        setAgentName('');
        setSystemPrompt('');
        setSelectedTools([]);
        setOutputSchema([{ name: '', type: 'string' }]);
        setParentAgent('');
        setSuccess(false);
        
        if (onSuccess) {
          onSuccess();
        }
      }, 2000);
    } else {
      setErrors([response.error || 'Failed to create agent']);
    }
    
    setLoading(false);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Create Custom Agent</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Errors */}
        {errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <h3 className="text-sm font-semibold text-red-800 mb-2">Validation Errors:</h3>
            <ul className="list-disc list-inside space-y-1">
              {errors.map((error, index) => (
                <li key={index} className="text-sm text-red-700">
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Success */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <p className="text-sm text-green-800">✓ Agent created successfully!</p>
          </div>
        )}

        {/* Agent Name */}
        <div>
          <label htmlFor="agent-name" className="block text-sm font-medium text-gray-700 mb-1">
            Agent Name *
          </label>
          <input
            id="agent-name"
            type="text"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            disabled={loading}
            placeholder="e.g., Priority Scorer"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Agent Type */}
        <div>
          <label htmlFor="agent-type" className="block text-sm font-medium text-gray-700 mb-1">
            Agent Type *
          </label>
          <select
            id="agent-type"
            value={agentType}
            onChange={(e) => setAgentType(e.target.value as any)}
            disabled={loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="custom">Custom</option>
            <option value="ingestion">Ingestion</option>
            <option value="query">Query</option>
          </select>
        </div>

        {/* System Prompt */}
        <div>
          <label htmlFor="system-prompt" className="block text-sm font-medium text-gray-700 mb-1">
            System Prompt *
          </label>
          <textarea
            id="system-prompt"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            disabled={loading}
            rows={4}
            placeholder="Describe what this agent should do..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Tool Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tools * (Select at least one)
          </label>
          <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto custom-scrollbar p-2 border border-gray-200 rounded-md">
            {availableTools.map((tool) => (
              <label key={tool.name} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedTools.includes(tool.name)}
                  onChange={() => handleToolToggle(tool.name)}
                  disabled={loading}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">{tool.name}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Output Schema */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Output Schema * (Max 5 fields)
            </label>
            <button
              type="button"
              onClick={handleAddField}
              disabled={loading || outputSchema.length >= 5}
              className="text-sm text-indigo-600 hover:text-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              + Add Field
            </button>
          </div>
          
          <div className="space-y-2">
            {outputSchema.map((field, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={field.name}
                  onChange={(e) => handleFieldChange(index, 'name', e.target.value)}
                  disabled={loading}
                  placeholder="Field name"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <select
                  value={field.type}
                  onChange={(e) => handleFieldChange(index, 'type', e.target.value)}
                  disabled={loading}
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {FIELD_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                {outputSchema.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveField(index)}
                    disabled={loading}
                    className="px-3 py-2 text-red-600 hover:text-red-700 disabled:opacity-50"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Dependency Selection */}
        <div>
          <label htmlFor="parent-agent" className="block text-sm font-medium text-gray-700 mb-1">
            Parent Agent (Optional - Single Level Only)
          </label>
          <select
            id="parent-agent"
            value={parentAgent}
            onChange={(e) => setParentAgent(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">None</option>
            {availableAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name} ({agent.type})
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            This agent will receive the parent agent&apos;s output as additional context
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Agent'}
          </button>
        </div>
      </form>
    </div>
  );
}
