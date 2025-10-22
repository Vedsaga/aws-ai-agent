'use client';

import { useState, useEffect } from 'react';
import { submitQuery } from '@/lib/api-client';
import { subscribeToJobStatus, StatusUpdate } from '@/lib/appsync-client';
import { getStoredUser } from '@/lib/auth';
import { showValidationErrorToast, showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import { useAppContext } from '@/contexts/AppContext';
import DomainSelector from './DomainSelector';
import { QueryClarificationPanel } from './QueryClarificationPanel';
import { needsClarification, getClarificationQuestions } from '@/lib/query-utils';
import ExecutionStatusPanel, { AgentStatus } from './ExecutionStatusPanel';
import ClarificationDialog, { LowConfidenceField } from './ClarificationDialog';
import { extractLowConfidenceFields, formatEnhancedText } from '@/lib/confidence-utils';

interface QueryResponse {
  bulletPoints: string[];
  summary: string;
  visualization?: any;
}

export default function QueryPanel({ onVisualizationUpdate }: { onVisualizationUpdate?: (viz: any) => void }) {
  const { selectedDomain, setSelectedDomain, addChatMessage } = useAppContext();
  const [question, setQuestion] = useState('');
  const [originalQuestion, setOriginalQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [showClarification, setShowClarification] = useState(false);
  const [clarificationQuestions, setClarificationQuestions] = useState<any[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
  const [agentNames, setAgentNames] = useState<string[]>([]);
  const [showStatusPanel, setShowStatusPanel] = useState(false);
  const [showConfidenceClarification, setShowConfidenceClarification] = useState(false);
  const [lowConfidenceFields, setLowConfidenceFields] = useState<LowConfidenceField[]>([]);
  const [clarificationRound, setClarificationRound] = useState(0);
  const [agentOutputs, setAgentOutputs] = useState<any[]>([]);

  useEffect(() => {
    if (!jobId || !selectedDomain) return;

    const user = getStoredUser();
    if (!user) return;

    // Show status panel when job starts
    setShowStatusPanel(true);

    const subscription = subscribeToJobStatus(
      user.userId,
      jobId,
      (update: StatusUpdate) => {
        const message = `${update.agentName}: ${update.message}`;
        setStatusMessages((prev) => [...prev, message]);
        
        // Update agent status
        const newStatus: AgentStatus = {
          agentName: update.agentName,
          status: update.status as AgentStatus['status'],
          message: update.message,
          confidence: update.confidence,
          timestamp: update.timestamp,
        };
        
        setAgentStatuses((prev) => ({
          ...prev,
          [update.agentName]: newStatus,
        }));
        
        // Add agent to list if not already present
        setAgentNames((prev) => {
          if (!prev.includes(update.agentName)) {
            return [...prev, update.agentName];
          }
          return prev;
        });
        
        // Collect agent outputs for confidence checking
        if (update.status === 'complete' && update.confidence !== undefined) {
          setAgentOutputs((prev) => [
            ...prev,
            {
              agent_name: update.agentName,
              output: {
                confidence: update.confidence,
              },
            },
          ]);
        }
        
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
            confidence: update.confidence,
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
            }
          } catch (e) {
            // Message is not JSON, just a status update
          }
          
          // Check if all agents are complete
          const updatedStatuses = {
            ...agentStatuses,
            [update.agentName]: newStatus,
          };
          
          const allComplete = Object.values(updatedStatuses).every(
            (status) => status.status === 'complete' || status.status === 'error'
          );
          
          if (allComplete) {
            setLoading(false);
            setShowStatusPanel(false);
            
            // Check for low confidence fields
            const currentOutputs = [...agentOutputs];
            if (update.confidence !== undefined) {
              currentOutputs.push({
                agent_name: update.agentName,
                output: {
                  confidence: update.confidence,
                },
              });
            }
            
            const lowConfFields = extractLowConfidenceFields(currentOutputs, 0.9);
            
            // Only show clarification if we haven't exceeded max rounds
            if (lowConfFields.length > 0 && clarificationRound < 3) {
              setLowConfidenceFields(lowConfFields);
              setShowConfidenceClarification(true);
            } else {
              showSuccessToast('Analysis complete', 'Your query has been analyzed');
            }
          }
        } else if (update.status === 'error') {
          setLoading(false);
          showErrorToast(`${update.agentName} failed`, update.message);
        }
      },
      (error) => {
        console.error('Status subscription error:', error);
        showErrorToast('Connection error', 'Lost connection to status updates');
        setShowStatusPanel(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [jobId, selectedDomain, addChatMessage, onVisualizationUpdate, agentStatuses]);

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

    // Store original question on first submission
    if (!originalQuestion) {
      setOriginalQuestion(queryText);
    }

    setLoading(true);
    setStatusMessages([]);
    setResponse(null);
    setJobId(null);
    setShowClarification(false);
    setAgentStatuses({});
    setAgentNames([]);
    setAgentOutputs([]);

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

  const handleConfidenceClarificationSubmit = (clarifications: Record<string, string>) => {
    // Append clarification to original question
    const enhancedQuestion = formatEnhancedText(originalQuestion, clarifications);
    
    // Increment clarification round
    setClarificationRound((prev) => prev + 1);
    
    // Update question and re-submit
    setQuestion(enhancedQuestion);
    setShowConfidenceClarification(false);
    
    // Re-submit with enhanced context
    submitQueryToAPI(enhancedQuestion);
  };

  const handleConfidenceClarificationSkip = () => {
    setShowConfidenceClarification(false);
    showSuccessToast('Analysis complete', 'Your query has been analyzed (with low confidence)');
  };

  const handleClarificationSubmit = (refinedQuery: string) => {
    submitQueryToAPI(refinedQuery);
  };

  const handleClarificationSkip = () => {
    submitQueryToAPI(question);
  };

  const handleReset = () => {
    setQuestion('');
    setOriginalQuestion('');
    setStatusMessages([]);
    setJobId(null);
    setResponse(null);
    setLoading(false);
    setShowClarification(false);
    setClarificationQuestions([]);
    setAgentStatuses({});
    setAgentNames([]);
    setShowStatusPanel(false);
    setShowConfidenceClarification(false);
    setLowConfidenceFields([]);
    setClarificationRound(0);
    setAgentOutputs([]);
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

        {/* Confidence-based Clarification Dialog */}
        {showConfidenceClarification && jobId && (
          <ClarificationDialog
            isOpen={showConfidenceClarification}
            jobId={jobId}
            lowConfidenceFields={lowConfidenceFields}
            onSubmit={handleConfidenceClarificationSubmit}
            onSkip={handleConfidenceClarificationSkip}
          />
        )}

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

        {/* Execution Status Panel */}
        {showStatusPanel && jobId && agentNames.length > 0 && (
          <div className="mb-4">
            <ExecutionStatusPanel
              jobId={jobId}
              agentStatuses={agentStatuses}
              agentNames={agentNames}
            />
          </div>
        )}

        {/* Status Messages (fallback for simple text display) */}
        {!showStatusPanel && statusMessages.length > 0 && (
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
