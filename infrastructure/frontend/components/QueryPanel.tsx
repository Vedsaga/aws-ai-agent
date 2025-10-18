'use client';

import { useState, useEffect } from 'react';
import { submitQuery, getDomains } from '@/lib/api-client';
import { subscribeToStatusUpdates, StatusUpdate } from '@/lib/appsync-client';
import { getStoredUser } from '@/lib/auth';

interface Domain {
  id: string;
  name: string;
  description: string;
}

interface QueryResponse {
  bulletPoints: string[];
  summary: string;
  visualization?: any;
}

export default function QueryPanel({ onVisualizationUpdate }: { onVisualizationUpdate?: (viz: any) => void }) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  useEffect(() => {
    loadDomains();
  }, []);

  useEffect(() => {
    if (!jobId) return;

    const user = getStoredUser();
    if (!user) return;

    const subscription = subscribeToStatusUpdates(
      user.userId,
      (update: StatusUpdate) => {
        if (update.jobId === jobId) {
          const message = `${update.agentName}: ${update.message}`;
          setStatusMessages((prev) => [...prev, message]);
          
          if (update.status === 'complete') {
            // Parse response from message if available
            try {
              const data = JSON.parse(update.message);
              if (data.bulletPoints && data.summary) {
                setResponse(data);
                if (data.visualization && onVisualizationUpdate) {
                  onVisualizationUpdate(data.visualization);
                }
              }
            } catch (e) {
              // Message is not JSON, just a status update
            }
            setLoading(false);
          } else if (update.status === 'error') {
            setLoading(false);
          }
        }
      },
      (error) => {
        console.error('Status subscription error:', error);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId, onVisualizationUpdate]);

  const loadDomains = async () => {
    const apiResponse = await getDomains();
    if (apiResponse.data?.domains) {
      setDomains(apiResponse.data.domains);
      if (apiResponse.data.domains.length > 0) {
        setSelectedDomain(apiResponse.data.domains[0].id);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedDomain || !question.trim()) {
      alert('Please select a domain and enter a question');
      return;
    }

    setLoading(true);
    setStatusMessages([]);
    setResponse(null);
    setJobId(null);

    const apiResponse = await submitQuery(selectedDomain, question);
    
    if (apiResponse.data?.job_id) {
      setJobId(apiResponse.data.job_id);
      setStatusMessages(['Query submitted. Analyzing...']);
    } else {
      alert(apiResponse.error || 'Failed to submit query');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setStatusMessages([]);
    setJobId(null);
    setResponse(null);
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col bg-white p-4 overflow-hidden">
      <h2 className="text-xl font-bold mb-4">Ask a Question</h2>
      
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
        {/* Domain Selection */}
        <div className="mb-4">
          <label htmlFor="query-domain" className="block text-sm font-medium text-gray-700 mb-1">
            Domain
          </label>
          <select
            id="query-domain"
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {domains.map((domain) => (
              <option key={domain.id} value={domain.id}>
                {domain.name}
              </option>
            ))}
          </select>
        </div>

        {/* Question Input */}
        <div className="mb-4">
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-1">
            Your Question
          </label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            placeholder="What are the trends in complaints?"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Status Messages */}
        {statusMessages.length > 0 && (
          <div className="mb-4 p-3 bg-gray-50 rounded-md max-h-24 overflow-y-auto custom-scrollbar">
            {statusMessages.map((msg, index) => (
              <div key={index} className="text-sm text-gray-700 mb-1">
                {msg}
              </div>
            ))}
          </div>
        )}

        {/* Response Display */}
        {response && (
          <div className="mb-4 flex-1 overflow-y-auto custom-scrollbar">
            {/* Bullet Points */}
            {response.bulletPoints && response.bulletPoints.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Analysis:</h3>
                <ul className="space-y-2">
                  {response.bulletPoints.map((point, index) => (
                    <li key={index} className="text-sm text-gray-800 flex">
                      <span className="mr-2">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Summary */}
            {response.summary && (
              <div className="p-3 bg-indigo-50 rounded-md">
                <h3 className="text-sm font-semibold text-indigo-900 mb-2">Summary:</h3>
                <p className="text-sm text-indigo-800">{response.summary}</p>
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || !selectedDomain || !question.trim()}
            className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Ask Question'}
          </button>
          
          {(response || statusMessages.length > 0) && (
            <button
              type="button"
              onClick={handleReset}
              disabled={loading}
              className="py-2 px-4 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              New Query
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
