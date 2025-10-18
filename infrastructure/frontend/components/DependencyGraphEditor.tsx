'use client';

import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { getAgentConfigs } from '@/lib/api-client';

interface Agent {
  id: string;
  name: string;
  type: string;
  dependency_parent?: string;
}

export default function DependencyGraphEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    const response = await getAgentConfigs();
    if (response.data?.configs) {
      setAgents(response.data.configs);
      buildGraph(response.data.configs);
    }
  };

  const buildGraph = (agentList: Agent[]) => {
    // Create nodes for each agent
    const newNodes: Node[] = agentList.map((agent, index) => ({
      id: agent.id,
      type: 'default',
      data: {
        label: (
          <div className="text-center">
            <div className="font-semibold">{agent.name}</div>
            <div className="text-xs text-gray-500">{agent.type}</div>
          </div>
        ),
      },
      position: {
        x: (index % 4) * 250,
        y: Math.floor(index / 4) * 150,
      },
      style: {
        background: agent.type === 'ingestion' ? '#E0E7FF' : agent.type === 'query' ? '#DBEAFE' : '#FEF3C7',
        border: '2px solid #4F46E5',
        borderRadius: '8px',
        padding: '10px',
        width: 200,
      },
    }));

    // Create edges based on dependencies
    const newEdges: Edge[] = agentList
      .filter((agent) => agent.dependency_parent)
      .map((agent) => ({
        id: `${agent.dependency_parent}-${agent.id}`,
        source: agent.dependency_parent!,
        target: agent.id,
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#4F46E5',
        },
        style: {
          stroke: '#4F46E5',
          strokeWidth: 2,
        },
      }));

    setNodes(newNodes);
    setEdges(newEdges);
  };

  const onConnect = useCallback(
    (connection: Connection) => {
      setError('');

      // Validate single-level dependency
      const targetAgent = agents.find((a) => a.id === connection.target);
      const sourceAgent = agents.find((a) => a.id === connection.source);

      if (!targetAgent || !sourceAgent) {
        setError('Invalid connection');
        return;
      }

      // Check if source already has a parent (would create multi-level)
      if (sourceAgent.dependency_parent) {
        setError(`Cannot create multi-level dependency. ${sourceAgent.name} already depends on another agent.`);
        return;
      }

      // Check if target already has a parent
      const existingParent = edges.find((e) => e.target === connection.target);
      if (existingParent) {
        setError(`${targetAgent.name} already has a parent dependency. Remove it first.`);
        return;
      }

      // Check for circular dependency
      if (connection.source === connection.target) {
        setError('Cannot create circular dependency (agent depending on itself)');
        return;
      }

      // Check if this would create a cycle
      const wouldCreateCycle = (source: string, target: string): boolean => {
        const visited = new Set<string>();
        const queue = [target];

        while (queue.length > 0) {
          const current = queue.shift()!;
          if (current === source) return true;
          if (visited.has(current)) continue;
          visited.add(current);

          const children = edges.filter((e) => e.source === current).map((e) => e.target);
          queue.push(...children);
        }

        return false;
      };

      if (wouldCreateCycle(connection.source!, connection.target!)) {
        setError('Cannot create circular dependency chain');
        return;
      }

      setEdges((eds) => addEdge(connection, eds));
    },
    [agents, edges, setEdges]
  );

  const handleDeleteEdge = (edgeId: string) => {
    setEdges((eds) => eds.filter((e) => e.id !== edgeId));
    setError('');
  };

  const handleRefresh = () => {
    loadAgents();
    setError('');
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold">Dependency Graph Editor</h2>
            <p className="text-sm text-gray-600">Drag to connect agents (single-level only)</p>
          </div>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Refresh
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Legend */}
        <div className="mt-3 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-indigo-200 border-2 border-indigo-600 rounded"></div>
            <span>Ingestion</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-200 border-2 border-indigo-600 rounded"></div>
            <span>Query</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-200 border-2 border-indigo-600 rounded"></div>
            <span>Custom</span>
          </div>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          attributionPosition="bottom-left"
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>

      {/* Edge List */}
      {edges.length > 0 && (
        <div className="p-4 border-t border-gray-200 max-h-32 overflow-y-auto custom-scrollbar">
          <h3 className="text-sm font-semibold mb-2">Dependencies:</h3>
          <div className="space-y-1">
            {edges.map((edge) => {
              const source = agents.find((a) => a.id === edge.source);
              const target = agents.find((a) => a.id === edge.target);
              return (
                <div key={edge.id} className="flex justify-between items-center text-sm">
                  <span>
                    {source?.name} → {target?.name}
                  </span>
                  <button
                    onClick={() => handleDeleteEdge(edge.id)}
                    className="text-red-600 hover:text-red-700 text-xs"
                  >
                    Remove
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
