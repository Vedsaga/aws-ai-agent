'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';

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

interface AgentSelectionCardProps {
  agent: Agent;
  selected: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export default function AgentSelectionCard({ agent, selected, onToggle, disabled = false }: AgentSelectionCardProps) {
  // Extract description from system prompt (first 100 chars)
  const description = agent.system_prompt?.substring(0, 100) + (agent.system_prompt?.length > 100 ? '...' : '');

  return (
    <Card
      className={`cursor-pointer transition-all ${
        selected ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={() => !disabled && onToggle()}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Checkbox
                checked={selected}
                onCheckedChange={onToggle}
                disabled={disabled}
                onClick={(e) => e.stopPropagation()}
              />
              {agent.agent_name}
            </CardTitle>
          </div>
          <div className="flex flex-wrap gap-1">
            {agent.is_builtin && (
              <Badge variant="secondary" className="text-xs">
                Built-in
              </Badge>
            )}
            {!agent.is_builtin && (
              <Badge variant="outline" className="text-xs">
                Custom
              </Badge>
            )}
          </div>
        </div>
        {description && (
          <CardDescription className="text-xs mt-2">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1">
          {agent.interrogative && (
            <Badge variant="default" className="text-xs">
              {agent.interrogative}
            </Badge>
          )}
          {agent.tools && agent.tools.length > 0 && (
            <Badge variant="outline" className="text-xs">
              {agent.tools.length} tool{agent.tools.length !== 1 ? 's' : ''}
            </Badge>
          )}
          {agent.dependency_parent && (
            <Badge variant="outline" className="text-xs">
              Chained
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
