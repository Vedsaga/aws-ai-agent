'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/SimpleMap'), { ssr: false });

type Mode = 'report' | 'query' | 'manage';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface AgentStatus {
  agent_id: string;
  status: 'running' | 'completed' | 'error' | 'invoking' | 'complete' | 'clarification';
  message: string;
  data?: any;
  timestamp: string;
}

interface MapReport {
  report_id: string;
  location: string;
  geo_coordinates: [number, number];
  entity: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status?: string;
}

export default function HomePage() {
  const [mode, setMode] = useState<Mode>('report');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const [mapReports, setMapReports] = useState<MapReport[]>([]);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

  // Load existing reports on mount
  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      const response = await fetch(`${apiUrl}/reports`);
      const data = await response.json();
      if (data.reports) {
        setMapReports(data.reports);
      }
    } catch (error) {
      console.error('Error loading reports:', error);
    }
  };

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = message;
    setMessage('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setAgentStatuses([]);

    try {
      const response = await fetch(`${apiUrl}/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: mode === 'report' ? 'ingestion' : mode === 'query' ? 'query' : 'management',
          message: userMessage,
          session_id: 'demo-session'
        })
      });

      const data = await response.json();
      
      // Parse agent response for status updates
      if (data.result?.agent_response) {
        try {
          const agentData = JSON.parse(data.result.agent_response);
          const statuses: AgentStatus[] = [];
          
          Object.entries(agentData).forEach(([agentId, agentResult]: [string, any]) => {
            statuses.push({
              agent_id: agentId,
              status: 'completed',
              message: `${agentId} completed`,
              data: agentResult,
              timestamp: new Date().toISOString()
            });
          });
          
          setAgentStatuses(statuses);
        } catch (e) {
          console.error('Failed to parse agent response:', e);
        }
      }
      
      let assistantMessage = '';
      if (data.result?.needs_clarification) {
        assistantMessage = data.result.question;
      } else if (data.result?.summary) {
        assistantMessage = data.result.summary;
      } else if (data.result?.confirmation) {
        assistantMessage = data.result.confirmation;
      } else if (data.result?.report_id) {
        assistantMessage = `Report created successfully! ID: ${data.result.report_id}`;
        
        // Add to map if it has location data
        if (data.result?.data) {
          setMapReports(prev => [...prev, {
            report_id: data.result.report_id,
            ...data.result.data
          }]);
        }
      } else {
        assistantMessage = 'Request processed successfully.';
      }

      setMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }]);
      
      // Reload reports to update map
      loadReports();
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, there was an error processing your request.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const getModeLabel = (m: Mode) => {
    switch (m) {
      case 'report': return 'Report Issue';
      case 'query': return 'Query Data';
      case 'manage': return 'Manage Tasks';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Panel - Chat */}
      <div className="w-1/2 p-4 border-r">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Civic Reports AI</h1>
          <p className="text-gray-600">Report issues, query data, or manage tasks</p>
        </div>

        <Tabs value={mode} onValueChange={(v) => setMode(v as Mode)} className="mb-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="report">Report Issue</TabsTrigger>
            <TabsTrigger value="query">Query Data</TabsTrigger>
            <TabsTrigger value="manage">Manage Tasks</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Agent Status Panel */}
        {agentStatuses.length > 0 && (
          <Card className="p-3 mb-4 bg-blue-50">
            <div className="text-sm font-semibold mb-2">Agent Activity</div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {agentStatuses.map((status, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  <div className={`w-2 h-2 rounded-full ${
                    status.status === 'completed' || status.status === 'complete' ? 'bg-green-500' :
                    status.status === 'error' ? 'bg-red-500' :
                    status.status === 'running' || status.status === 'invoking' ? 'bg-yellow-500 animate-pulse' :
                    'bg-blue-500'
                  }`} />
                  <span className="font-medium">{status.agent_id}:</span>
                  <span className="text-gray-600">{status.message}</span>
                  {status.data?.confidence && (
                    <span className="text-gray-500">({Math.round(status.data.confidence * 100)}%)</span>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        <Card className="p-4 mb-4 h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-lg mb-2">No messages yet</p>
              <p className="text-sm">
                {mode === 'report' && 'Report a civic issue like potholes, broken streetlights, etc.'}
                {mode === 'query' && 'Ask questions about reported issues in your area'}
                {mode === 'manage' && 'Assign tasks or update report status'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-100 ml-12'
                      : 'bg-gray-100 mr-12'
                  }`}
                >
                  <div className="font-semibold text-sm mb-1">
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </div>
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <div className="flex gap-2">
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={
              mode === 'report'
                ? 'Describe the issue... (e.g., "Broken streetlight at 123 Main St")'
                : mode === 'query'
                ? 'Ask a question... (e.g., "Show me all potholes on Main Street")'
                : 'Give a command... (e.g., "Assign report ABC to Team B")'
            }
            className="flex-1"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
          />
          <Button
            onClick={sendMessage}
            disabled={loading || !message.trim()}
            className="self-end"
          >
            {loading ? 'Sending...' : 'Send'}
          </Button>
        </div>
      </div>

      {/* Right Panel - Map */}
      <div className="w-1/2 p-4">
        <div className="h-full rounded-lg overflow-hidden border">
          <MapView reports={mapReports} />
        </div>
      </div>
    </div>
  );
}
