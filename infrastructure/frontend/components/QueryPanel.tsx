'use client';

import { useState, useEffect } from 'react';
import { submitQuery } from '@/lib/api-client';
import { subscribeToStatusUpdates, StatusUpdate } from '@/lib/appsync-client';
import { getStoredUser } from '@/lib/auth';
import { showValidationErrorToast, showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import { useAppContext } from '@/contexts/AppContext';
import DomainSelector from './DomainSelector';
import { QueryClarificationPanel } from './QueryClarificationPanel';
import { needsClarification, getClarificationQuestions } from '@/lib/query-utils';

interface QueryResponse {
  bulletPoints: string[];
  summary: string;
  visualization?: any;
}

export default function QueryPanel({ onVisualizationUpdate }: { onVisualizationUpdate?: (viz: any) => void }) {
  const { selectedDomain, setSelectedDomain, addChatMessage } = useAppContext();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [showClarification, setShowClarification] = useState(false);
  const [clarificationQuestions, setClarificationQuestions] = useState<any[]>([]);

  useEffect(() => {
    if (!jobId || !selectedDomain) return;

    const user = getStoredUser();
    if (!user) return;

    const subscription = subscribeToStatusUpdates(
      user.userId,
      (update: StatusUpdate) => {
        if (update.jobId === jobId) {
          const message = `${update.agentName}: ${update.message}`;
          setStatusMessages((prev) => [...prev, message]);
          
          // Add to chat history
          addChatMessage(selectedDomain, {
            id: `${Date.now()}-${Math.random()}`,
            type: 'agent',
            content: message,
            timestamp: new Date().toISOString(),
            metadata: {
              jobId: update.jobId,
              agentName: update.agentName,
              status: update.status,
            },
          });
          
          if (update.status === 'complete') {
            // Parse response from message if available
            try {
              const data = JSON.parse(update.message);
              if (data.bulletPoints && data.summary) {
                setResponse(data);
                if (data.visualization && onVisualizationUpdate) {
                  onVisualizationUpdate(data.visualization);
                }
                showSuccessToast('Analysis complete', 'Your query has been analyzed');
              }
            } catch (e) {
              // Message is not JSON, just a status update
            }
            setLoading(false);
          } else if (update.status === 'error') {
            setLoading(false);
            showErrorToast(`${update.agentName} failed`, update.message);
          }
        }
      },
      (error) => {
        console.error('Status subscription error:', error);
        showErrorToast('Connection error', 'Lost connection to status updates');
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId, selectedDomain, addChatMessage, onVisualizationUpdate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const errors: string[] = [];
    if (!selectedDomain) {
      errors.push('Please select a domain');
    }
    if (!question.trim()) {
      errors.push('Question is required');
    }
    
    if (errors.length > 0) {
      showValidationErrorToast(errors);
      return;
    }

    // Check if query needs clarification
    if (needsClarification(question)) {
      const questions = getClarificationQuestions(question);
      if (questions.length > 0) {
        setClarificationQuestions(questions);
        setShowClarification(true);
        return;
      }
    }

    // Submit query directly if no clarification needed
    submitQueryToAPI(question);
  };

  const submitQueryToAPI = async (queryText: string) => {
    // TypeScript guard - we know selectedDomain is not null here
    if (!selectedDomain) return;

    setLoading(true);
    setStatusMessages([]);
    setResponse(null);
    setJobId(null);
    setShowClarification(false);

    // Add user question to chat history
    addChatMessage(selectedDomain, {
      id: `${Date.now()}-${Math.random()}`,
      type: 'user',
      content: queryText,
      timestamp: new Date().toISOString(),
    });

    const apiResponse = await submitQuery(selectedDomain, queryText);
    
    if (apiResponse.data?.job_id) {
      setJobId(apiResponse.data.job_id);
      setStatusMessages(['Query submitted. Analyzing...']);
      showSuccessToast('Query submitted', 'Your question is being analyzed');
    } else {
      // Error toast is already shown by API client
      setLoading(false);
    }
  };

  const handleClarificationSubmit = (refinedQuery: string) => {
    submitQueryToAPI(refinedQuery);
  };

  const handleClarificationSkip = () => {
    submitQueryToAPI(question);
  };

  const handleReset = () => {
    setQuestion('');
    setStatusMessages([]);
    setJobId(null);
    setResponse(null);
    setLoading(false);
    setShowClarification(false);
    setClarificationQuestions([]);
  };

  return (
    <div className="h-full flex flex-col bg-card p-4 overflow-hidden">
      <h2 className="text-xl font-bold mb-4 text-foreground">Ask a Question</h2>
      
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
        {/* Domain Selection */}
        <div className="mb-4">
          <label htmlFor="query-domain" className="block text-sm font-medium text-foreground mb-1">
            Domain
          </label>
          <DomainSelector
            selectedDomain={selectedDomain}
            onDomainChange={setSelectedDomain}
          />
        </div>

        {/* Question Input */}
        <div className="mb-4">
          <label htmlFor="question" className="block text-sm font-medium text-foreground mb-1">
            Your Question
          </label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            placeholder="What are the trends in complaints?"
            className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring bg-background text-foreground"
          />
        </div>

        {/* Clarification Panel */}
        {showClarification && !loading && (
          <div className="mb-4">
            <QueryClarificationPanel
              query={question}
              questions={clarificationQuestions}
              onSubmit={handleClarificationSubmit}
              onSkip={handleClarificationSkip}
            />
          </div>
        )}

        {/* Status Messages */}
        {statusMessages.length > 0 && (
          <div className="mb-4 p-3 bg-muted rounded-md max-h-24 overflow-y-auto custom-scrollbar">
            {statusMessages.map((msg, index) => (
              <div key={index} className="text-sm text-foreground mb-1">
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
                <h3 className="text-sm font-semibold text-foreground mb-2">Analysis:</h3>
                <ul className="space-y-2">
                  {response.bulletPoints.map((point, index) => (
                    <li key={index} className="text-sm text-foreground flex">
                      <span className="mr-2">•</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Summary */}
            {response.summary && (
              <div className="p-3 bg-primary/10 rounded-md">
                <h3 className="text-sm font-semibold text-primary mb-2">Summary:</h3>
                <p className="text-sm text-foreground">{response.summary}</p>
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        {!showClarification && (
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={loading || !selectedDomain || !question.trim()}
              className="flex-1 py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Analyzing...' : 'Ask Question'}
            </button>
            
            {(response || statusMessages.length > 0) && (
              <button
                type="button"
                onClick={handleReset}
                disabled={loading}
                className="py-2 px-4 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 focus:outline-none focus:ring-2 focus:ring-ring"
              >
                New Query
              </button>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
