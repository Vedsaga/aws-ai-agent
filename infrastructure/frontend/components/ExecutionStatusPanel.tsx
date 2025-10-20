'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, Circle, Wrench } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface AgentStatus {
  agentName: string;
  status: 'waiting' | 'invoking' | 'calling_tool' | 'complete' | 'error';
  message: string;
  confidence?: number;
  timestamp: string;
}

interface ExecutionStatusPanelProps {
  jobId: string;
  agentStatuses: Record<string, AgentStatus>;
  agentNames: string[];
}

export default function ExecutionStatusPanel({
  jobId,
  agentStatuses,
  agentNames,
}: ExecutionStatusPanelProps) {
  const [animatingAgents, setAnimatingAgents] = useState<Set<string>>(new Set());

  // Trigger animation when status changes
  useEffect(() => {
    const newAnimatingAgents = new Set<string>();
    
    Object.keys(agentStatuses).forEach((agentName) => {
      const status = agentStatuses[agentName];
      // Animate on status transitions
      if (status && status.status !== 'waiting') {
        newAnimatingAgents.add(agentName);
      }
    });

    setAnimatingAgents(newAnimatingAgents);

    // Clear animation after 500ms
    const timer = setTimeout(() => {
      setAnimatingAgents(new Set());
    }, 500);

    return () => clearTimeout(timer);
  }, [agentStatuses]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'invoking':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'calling_tool':
        return <Wrench className="w-5 h-5 text-yellow-500 animate-pulse" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'text-green-500';
      case 'error':
        return 'text-red-500';
      case 'invoking':
        return 'text-blue-500';
      case 'calling_tool':
        return 'text-yellow-500';
      default:
        return 'text-gray-400';
    }
  };

  const getBackgroundClass = (status: string, isAnimating: boolean) => {
    const baseClass = 'p-2 rounded-md transition-all duration-300';
    
    if (isAnimating) {
      switch (status) {
        case 'complete':
          return `${baseClass} bg-green-500/10 scale-[1.02]`;
        case 'error':
          return `${baseClass} bg-red-500/10 scale-[1.02]`;
        case 'invoking':
          return `${baseClass} bg-blue-500/10 scale-[1.02]`;
        case 'calling_tool':
          return `${baseClass} bg-yellow-500/10 scale-[1.02]`;
        default:
          return `${baseClass} hover:bg-muted/50`;
      }
    }
    
    return `${baseClass} hover:bg-muted/50`;
  };

  return (
    <Card className="p-4 bg-card border-border">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-foreground">Execution Status</h3>
        <span className="text-xs text-muted-foreground">Job: {jobId.slice(0, 8)}...</span>
      </div>

      <div className="space-y-3">
        {agentNames.map((agentName) => {
          const status = agentStatuses[agentName];
          const isAnimating = animatingAgents.has(agentName);

          return (
            <div
              key={agentName}
              className={`flex items-start gap-3 ${getBackgroundClass(
                status?.status || 'waiting',
                isAnimating
              )}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getStatusIcon(status?.status || 'waiting')}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium text-sm text-foreground truncate">
                    {agentName}
                  </div>
                  {status?.confidence !== undefined && (
                    <Badge
                      variant={status.confidence >= 0.9 ? 'default' : 'destructive'}
                      className="flex-shrink-0 animate-in fade-in duration-300"
                    >
                      {(status.confidence * 100).toFixed(0)}%
                    </Badge>
                  )}
                </div>
                <div className={`text-xs mt-0.5 ${getStatusColor(status?.status || 'waiting')}`}>
                  {status?.message || 'Waiting...'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
