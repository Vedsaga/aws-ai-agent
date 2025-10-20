'use client';

import { Agent } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit, Trash2 } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
  onEdit: (agent: Agent) => void;
  onDelete: (agent: Agent) => void;
}

export default function AgentCard({ agent, onEdit, onDelete }: AgentCardProps) {
  const getAgentTypeLabel = (type: string) => {
    switch (type) {
      case 'ingestion':
        return 'Data Ingest';
      case 'query':
        return 'Data Query';
      case 'custom':
        return 'Custom';
      default:
        return type;
    }
  };

  const getAgentTypeColor = (type: string) => {
    switch (type) {
      case 'ingestion':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'query':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      case 'custom':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{agent.agent_name}</CardTitle>
            <CardDescription className="mt-1">
              {agent.system_prompt?.substring(0, 100)}
              {agent.system_prompt?.length > 100 ? '...' : ''}
            </CardDescription>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mt-3">
          {agent.is_builtin && (
            <Badge variant="secondary" className="text-xs">
              Built-in
            </Badge>
          )}
          {!agent.is_builtin && (
            <Badge variant="outline" className="text-xs">
              Created by me
            </Badge>
          )}
          <Badge className={`text-xs ${getAgentTypeColor(agent.agent_type)}`}>
            {getAgentTypeLabel(agent.agent_type)}
          </Badge>
          {agent.interrogative && (
            <Badge variant="outline" className="text-xs">
              {agent.interrogative}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* Tools */}
        {agent.tools && agent.tools.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-muted-foreground mb-1">Tools:</p>
            <div className="flex flex-wrap gap-1">
              {agent.tools.map((tool, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {tool}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons - only show for custom agents */}
        {!agent.is_builtin && (
          <div className="flex gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onEdit(agent)}
            >
              <Edit className="h-3 w-3 mr-1" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex-1 text-destructive hover:text-destructive"
              onClick={() => onDelete(agent)}
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Delete
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
