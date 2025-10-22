'use client';

import { useState, useEffect, useRef } from 'react';
import { incidentAPI } from '@/lib/incident-api';

interface Message {
  id: string;
  type: 'user' | 'system' | 'result';
  content: string;
  timestamp: Date;
  jobId?: string;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
  data?: any;
}

interface IncidentChatProps {
  token: string;
  domainId?: string;
}

export default function IncidentChat({ token, domainId = 'civic_complaints' }: IncidentChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      type: 'system',
      content: 'Hello! Report an incident or ask me about existing reports.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Set token on mount
  useEffect(() => {
    if (token) {
      incidentAPI.setToken(token);
    }
  }, [token]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [
      ...prev,
      {
        ...message,
        id: Date.now().toString(),
        timestamp: new Date(),
      },
    ]);
  };

  const updateMessage = (id: string, updates: Partial<Message>) => {
    setMessages(prev =>
      prev.map(msg => (msg.id === id ? { ...msg, ...updates } : msg))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage = input.trim();
    setInput('');
    setIsProcessing(true);

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
    });

    try {
      // Determine if it's a query or incident report
      const isQuery = userMessage.toLowerCase().match(/^(show|find|list|what|where|when|how many)/);

      if (isQuery) {
        // Handle as query
        await handleQuery(userMessage);
      } else {
        // Handle as incident submission
        await handleIncidentSubmission(userMessage);
      }
    } catch (error: any) {
      addMessage({
        type: 'system',
        content: `Error: ${error.message}`,
        status: 'failed',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleIncidentSubmission = async (text: string) => {
    // Add processing message
    const processingMsgId = Date.now().toString();
    addMessage({
      type: 'system',
      content: '📝 Submitting your report...',
      status: 'pending',
    });

    try {
      // Submit incident
      const response = await incidentAPI.submitIncident({
        domain_id: domainId,
        text: text,
        source: 'web_chat',
        priority: 'normal',
      });

      // Update with job ID
      updateMessage(processingMsgId, {
        content: `✓ Report submitted (Job: ${response.job_id.slice(0, 12)}...)`,
        jobId: response.job_id,
        status: 'processing',
      });

      // Add processing status message
      const statusMsgId = (Date.now() + 1).toString();
      addMessage({
        type: 'system',
        content: '⏳ Processing your report with AI agents...',
        jobId: response.job_id,
        status: 'processing',
      });

      // Poll for completion
      setTimeout(async () => {
        try {
          const status = await incidentAPI.pollJobStatus(response.job_id);

          if (status.status === 'completed') {
            updateMessage(statusMsgId, {
              content: '✅ Report processed successfully!',
              status: 'completed',
            });

            // Show results
            addMessage({
              type: 'result',
              content: formatResults(status.structured_data),
              data: status.structured_data,
              status: 'completed',
            });
          } else if (status.status === 'failed') {
            updateMessage(statusMsgId, {
              content: '❌ Processing failed',
              status: 'failed',
            });
          }
        } catch (error) {
          // Timeout or error - show completion message anyway
          updateMessage(statusMsgId, {
            content: '✓ Report submitted. Check dashboard for results.',
            status: 'completed',
          });
        }
      }, 2000);
    } catch (error: any) {
      throw error;
    }
  };

  const handleQuery = async (query: string) => {
    addMessage({
      type: 'system',
      content: '🔍 Searching incidents...',
      status: 'processing',
    });

    try {
      const response = await incidentAPI.queryIncidents(query);

      if (response.job_id) {
        addMessage({
          type: 'system',
          content: '⏳ Processing your query...',
          jobId: response.job_id,
          status: 'processing',
        });

        // Poll for query results
        setTimeout(async () => {
          try {
            const status = await incidentAPI.pollJobStatus(response.job_id);
            if (status.status === 'completed' && status.results) {
              addMessage({
                type: 'result',
                content: formatQueryResults(status.results),
                data: status.results,
                status: 'completed',
              });
            } else {
              addMessage({
                type: 'system',
                content: 'Query completed. Check dashboard for detailed results.',
                status: 'completed',
              });
            }
          } catch (error) {
            addMessage({
              type: 'system',
              content: 'Query submitted. Results will appear in dashboard.',
              status: 'completed',
            });
          }
        }, 2000);
      }
    } catch (error: any) {
      throw error;
    }
  };

  const formatResults = (data: any): string => {
    if (!data) return 'Report processed successfully.';

    const parts: string[] = [];

    if (data.location) {
      parts.push(`📍 Location: ${data.location.address || 'Detected'}`);
    }

    if (data.timestamp) {
      parts.push(`⏰ Time: ${data.timestamp}`);
    }

    if (data.category) {
      parts.push(`🏷️ Category: ${data.category}`);
    }

    if (data.summary) {
      parts.push(`\n${data.summary}`);
    }

    return parts.length > 0 ? parts.join('\n') : 'Report processed successfully.';
  };

  const formatQueryResults = (data: any): string => {
    if (!data) return 'No results found.';

    if (Array.isArray(data)) {
      return `Found ${data.length} incident(s):\n\n${data
        .slice(0, 5)
        .map((item, i) => `${i + 1}. ${item.summary || item.text || 'Incident'}`)
        .join('\n')}`;
    }

    if (data.summary) return data.summary;
    if (data.message) return data.message;

    return JSON.stringify(data, null, 2);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b bg-blue-600 text-white rounded-t-lg">
        <h2 className="text-lg font-semibold">Incident Chat</h2>
        <p className="text-sm text-blue-100">Report incidents or ask questions</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.type === 'result'
                  ? 'bg-green-50 border border-green-200 text-gray-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
              {message.status === 'processing' && (
                <div className="mt-2 flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-transparent"></div>
                  <span className="text-xs text-gray-500">Processing...</span>
                </div>
              )}
              <div className="text-xs opacity-70 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Report an incident or ask a question..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? '...' : 'Send'}
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          Examples: "Pothole at Main St" or "Show all traffic incidents"
        </div>
      </form>
    </div>
  );
}
