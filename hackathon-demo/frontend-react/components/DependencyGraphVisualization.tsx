'use client';

import { Badge } from '@/components/ui/badge';
import { ArrowRight } from 'lucide-react';

interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  dependency_parent?: string;
  is_builtin: boolean;
}

interface DependencyGraphVisualizationProps {
  ingestAgents: Agent[];
  queryAgents: Agent[];
}

export default function DependencyGraphVisualization({
  ingestAgents,
  queryAgents,
}: DependencyGraphVisualizationProps) {
  // Separate agents by execution pattern
  const parallelIngestAgents = ingestAgents.filter(a => !a.dependency_parent);
  const sequentialIngestAgents = ingestAgents.filter(a => a.dependency_parent);

  const parallelQueryAgents = queryAgents.filter(a => !a.dependency_parent);
  const sequentialQueryAgents = queryAgents.filter(a => a.dependency_parent);

  // Sort sequential agents by dependency chain
  const sortSequentialAgents = (agents: Agent[]): Agent[] => {
    const sorted: Agent[] = [];
    const remaining = [...agents];
    const processed = new Set<string>();

    // Add agents without dependencies first
    const noDeps = remaining.filter(a => !a.dependency_parent);
    sorted.push(...noDeps);
    noDeps.forEach(a => processed.add(a.agent_id));

    // Add agents with dependencies in order
    let iterations = 0;
    while (remaining.length > sorted.length && iterations < 10) {
      for (const agent of remaining) {
        if (!processed.has(agent.agent_id) && agent.dependency_parent && processed.has(agent.dependency_parent)) {
          sorted.push(agent);
          processed.add(agent.agent_id);
        }
      }
      iterations++;
    }

    return sorted;
  };

  const sortedSequentialIngest = sortSequentialAgents(sequentialIngestAgents);
  const sortedSequentialQuery = sortSequentialAgents(sequentialQueryAgents);

  if (ingestAgents.length === 0 && queryAgents.length === 0) {
    return (
      <div className="border rounded-lg p-4 bg-card text-center text-muted-foreground text-sm">
        No agents selected
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-card space-y-4">
      {/* Ingestion Layer */}
      {ingestAgents.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase">
            Ingestion Layer
          </div>

          {/* Parallel Execution */}
          {parallelIngestAgents.length > 0 && (
            <div className="mb-2">
              <div className="text-xs text-muted-foreground mb-1">Parallel Execution:</div>
              <div className="flex flex-wrap gap-2">
                {parallelIngestAgents.map((agent) => (
                  <Badge key={agent.agent_id} variant="secondary" className="text-xs">
                    {agent.agent_name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Sequential Execution */}
          {sortedSequentialIngest.length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Sequential Execution:</div>
              <div className="flex items-center gap-1 flex-wrap">
                {sortedSequentialIngest.map((agent, idx) => (
                  <div key={agent.agent_id} className="flex items-center gap-1">
                    <Badge variant="outline" className="text-xs">
                      {agent.agent_name}
                    </Badge>
                    {idx < sortedSequentialIngest.length - 1 && (
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Query Layer */}
      {queryAgents.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase">
            Query Layer
          </div>

          {/* Parallel Execution */}
          {parallelQueryAgents.length > 0 && (
            <div className="mb-2">
              <div className="text-xs text-muted-foreground mb-1">Parallel Execution:</div>
              <div className="flex flex-wrap gap-2">
                {parallelQueryAgents.map((agent) => (
                  <Badge key={agent.agent_id} variant="secondary" className="text-xs">
                    {agent.agent_name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Sequential Execution */}
          {sortedSequentialQuery.length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Sequential Execution:</div>
              <div className="flex items-center gap-1 flex-wrap">
                {sortedSequentialQuery.map((agent, idx) => (
                  <div key={agent.agent_id} className="flex items-center gap-1">
                    <Badge variant="outline" className="text-xs">
                      {agent.agent_name}
                    </Badge>
                    {idx < sortedSequentialQuery.length - 1 && (
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
