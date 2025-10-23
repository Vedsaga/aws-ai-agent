'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('@/components/CivicMap'), { ssr: false });

type Mode = 'report' | 'query' | 'manage' | 'status';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AgentStatus {
  agent_id: string;
  status: 'running' | 'completed' | 'error' | 'invoking' | 'complete';
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
  assignee?: string;
  created_at?: string;
}

const MODE_CONFIG = {
  report: { label: 'Report', icon: '📝' },
  query: { label: 'Query', icon: '🔍' },
  manage: { label: 'Manage', icon: '⚙️' },
  status: { label: 'Status', icon: '📊' },
};

export default function HomePage() {
  const [mode, setMode] = useState<Mode>('report');
  const [showModeMenu, setShowModeMenu] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([]);
  const [mapReports, setMapReports] = useState<MapReport[]>([]);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

  // Load existing reports on mount and when mode changes
  useEffect(() => {
    loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

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
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }]);
    setLoading(true);
    setAgentStatuses([]);

    try {
      const response = await fetch(`${apiUrl}/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: mode === 'report' ? 'ingestion' : mode === 'query' ? 'query' : 'management',
          message: userMessage,
          session_id: 'civic-session'
        })
      });

      const data = await response.json();

      // Parse agent execution for status updates
      if (data.result?.agent_execution?.agent_results) {
        const statuses: AgentStatus[] = [];

        Object.entries(data.result.agent_execution.agent_results).forEach(([agentId, agentResult]: [string, any]) => {
          statuses.push({
            agent_id: agentId,
            status: agentResult.status || 'completed',
            message: `${agentId} completed`,
            data: agentResult,
            timestamp: new Date().toISOString()
          });
        });

        setAgentStatuses(statuses);
      }

      let assistantMessage = '';
      if (data.result?.needs_clarification) {
        assistantMessage = data.result.clarification_question || 'Please provide more details.';
      } else if (data.result?.results && Array.isArray(data.result.results)) {
        // Query results - prioritize showing actual data over summary
        const results = data.result.results;
        assistantMessage = `Found ${results.length} result${results.length !== 1 ? 's' : ''}:\n\n`;

        results.slice(0, 10).forEach((item: any, idx: number) => {
          const entity = item.entity || item.structured_data?.entity?.description || 'Issue';
          const location = item.location || item.structured_data?.location?.address || 'Unknown';
          const severity = item.severity || item.structured_data?.severity?.level || 'unknown';
          const status = item.status ? ` [${item.status}]` : '';

          assistantMessage += `${idx + 1}. ${entity}\n`;
          assistantMessage += `   ⚠️ ${severity.toUpperCase()}${status}\n`;
          assistantMessage += `   📍 ${location}\n`;
          if (item.assignee) assistantMessage += `   👤 ${item.assignee}\n`;
          assistantMessage += `\n`;
        });

        if (results.length > 10) {
          assistantMessage += `... and ${results.length - 10} more`;
        }

        // Add query results to map
        const queryReports = results.map((item: any) => {
          const report = {
            report_id: item.report_id || item.id,
            location: item.location || item.structured_data?.location?.address,
            geo_coordinates: item.geo_coordinates || item.structured_data?.location?.geo_coordinates,
            entity: item.entity || item.structured_data?.entity?.description || 'Issue',
            severity: item.severity || item.structured_data?.severity?.level || 'medium',
            status: item.status || 'pending',
            assignee: item.assignee,
            created_at: item.created_at
          };
          console.log('Query report mapped:', report);
          return report;
        }).filter((r: any) => {
          const valid = r.geo_coordinates && Array.isArray(r.geo_coordinates) && r.geo_coordinates.length === 2 && r.location;
          if (!valid) console.log('Filtered out report:', r);
          return valid;
        });

        console.log('Total query reports for map:', queryReports.length, queryReports);

        setMapReports(queryReports);
      } else if (data.result?.summary) {
        assistantMessage = data.result.summary;
      } else if (data.result?.confirmation) {
        assistantMessage = data.result.confirmation;
      } else if (data.result?.report_id) {
        const location = data.result.data?.location?.address || 'Unknown location';
        const severity = data.result.data?.severity?.level || 'unknown';
        const entity = data.result.data?.entity?.description || 'Issue';

        assistantMessage = `✅ Report created successfully!\n\n📍 ${entity}\n📌 Location: ${location}\n⚠️ Severity: ${severity.toUpperCase()}\n🆔 ID: ${data.result.report_id.substring(0, 8)}...`;

        // Add to map if it has location data
        if (data.result?.data?.location?.geo_coordinates) {
          const newReport: MapReport = {
            report_id: data.result.report_id,
            location: data.result.data.location.address,
            geo_coordinates: data.result.data.location.geo_coordinates,
            entity: data.result.data.entity?.description || 'Issue',
            severity: data.result.data.severity?.level || 'medium',
            status: 'pending',
            created_at: data.result.metadata?.created_at
          };
          setMapReports(prev => [...prev, newReport]);
        }
      } else if (data.result?.updates_applied) {
        // Management result
        assistantMessage = data.result.confirmation || 'Update completed successfully.';
      } else {
        assistantMessage = 'Request processed successfully.';
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: assistantMessage,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const getPlaceholder = () => {
    switch (mode) {
      case 'report':
        return 'Report an issue...';
      case 'query':
        return 'Ask a question...';
      case 'manage':
        return 'Give a command...';
    }
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-gray-900">
      {/* Left Panel - Map (80%) */}
      <div className="w-4/5 relative">
        {/* Domain Name - Top Left with 16px padding */}
        <div className="absolute top-4 left-4 z-10">
          <div className="bg-white/95 backdrop-blur-sm px-5 py-3 rounded-xl shadow-xl border-2 border-blue-200">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🏙️</span>
              <span className="font-bold text-xl text-gray-800">Civic Sense</span>
            </div>
          </div>
        </div>

        {/* Map */}
        <MapView reports={mapReports} />
      </div>

      {/* Right Panel - Chat (20%) */}
      <div className="w-1/5 bg-white flex flex-col shadow-2xl">
        {/* Chat Header */}
        <div className="p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700">
          <h2 className="text-white font-bold text-lg">Chat Panel</h2>
        </div>

        {/* Realtime Agent Status */}
        {agentStatuses.length > 0 && (
          <div className="p-3 bg-blue-50 border-b">
            <div className="text-xs font-bold text-blue-900 mb-2 flex items-center gap-2">
              <span className="animate-pulse">🔄</span>
              <span>Realtime Status</span>
            </div>
            <div className="space-y-1.5 max-h-28 overflow-y-auto">
              {agentStatuses.map((status, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs bg-white p-2 rounded">
                  <div className={`w-2 h-2 rounded-full ${status.status === 'completed' || status.status === 'complete' ? 'bg-green-500' :
                    status.status === 'error' ? 'bg-red-500' :
                      'bg-yellow-500 animate-pulse'
                    }`} />
                  <span className="font-semibold text-gray-800">{status.agent_id}</span>
                  {status.data?.confidence && (
                    <span className="text-gray-600 ml-auto font-mono">
                      {Math.round(status.data.confidence * 100)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 mt-12">
              <div className="text-5xl mb-3">💬</div>
              <p className="text-sm font-medium">Start chatting</p>
              <p className="text-xs mt-2 text-gray-500">
                {mode === 'report' && 'Report civic issues'}
                {mode === 'query' && 'Query data'}
                {mode === 'manage' && 'Manage reports'}
                {mode === 'status' && 'Check status'}
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`${msg.role === 'user'
                  ? 'ml-4 bg-blue-600 text-white'
                  : 'mr-4 bg-gray-100 text-gray-900'
                  } p-3 rounded-xl text-sm shadow-sm`}
              >
                <div className="font-bold text-xs mb-1 opacity-80">
                  {msg.role === 'user' ? 'You' : 'AI'}
                </div>
                <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
              </div>
            ))
          )}
        </div>

        {/* Input Area - Stadium Design */}
        <div className="p-4 border-t bg-gray-50">
          {/* Stadium Input with Mode Selector */}
          <div className="relative mb-3">
            <div className="flex items-center gap-2 bg-white border-2 border-gray-300 rounded-full px-4 py-3 shadow-sm hover:border-blue-400 transition-colors">
              {/* Mode Button with Icon */}
              <button
                onClick={() => setShowModeMenu(!showModeMenu)}
                className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-full text-xs font-bold hover:bg-blue-600 transition-colors"
              >
                <span className="text-base">{MODE_CONFIG[mode].icon}</span>
                <span>{MODE_CONFIG[mode].label}</span>
              </button>

              {/* Input Field */}
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={getPlaceholder()}
                className="flex-1 bg-transparent outline-none text-sm text-gray-800 placeholder-gray-400"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />

              {/* Send Button */}
              <button
                onClick={sendMessage}
                disabled={loading || !message.trim()}
                className="px-4 py-1.5 bg-blue-500 text-white rounded-full text-xs font-bold hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? '⏳' : '➤'}
              </button>
            </div>

            {/* Mode Dropdown */}
            {showModeMenu && (
              <div className="absolute bottom-full mb-2 left-0 bg-white rounded-2xl shadow-2xl border-2 border-gray-200 overflow-hidden">
                {(Object.keys(MODE_CONFIG) as Mode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => {
                      setMode(m);
                      setShowModeMenu(false);
                    }}
                    className={`w-full px-4 py-3 text-left text-sm flex items-center gap-3 hover:bg-blue-50 transition-colors ${mode === m ? 'bg-blue-100 text-blue-700 font-bold' : 'text-gray-700'
                      }`}
                  >
                    <span className="text-lg">{MODE_CONFIG[m].icon}</span>
                    <span>{MODE_CONFIG[m].label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
