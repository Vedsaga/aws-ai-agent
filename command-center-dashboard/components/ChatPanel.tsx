'use client';

import { useState } from 'react';
import { useStore } from '@/store/useStore';
import { mockApiService } from '@/services/mockApiService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

export default function ChatPanel() {
  const [input, setInput] = useState('');
  const { 
    chatHistory, 
    suggestedActions, 
    timestamp, 
    isLoading,
    addChatMessage, 
    updateFromResponse, 
    setIsLoading 
  } = useStore();

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: 'user' as const,
      content: input,
      timestamp: new Date().toISOString()
    };
    
    addChatMessage(userMessage);
    setInput('');
    setIsLoading(true);

    try {
      const response = await mockApiService.postQuery(input, timestamp);
      
      const agentMessage = {
        role: 'agent' as const,
        content: response.chatResponse,
        timestamp: response.timestamp
      };
      
      addChatMessage(agentMessage);
      updateFromResponse(response);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedAction = async (action: any) => {
    const userMessage = {
      role: 'user' as const,
      content: action.label,
      timestamp: new Date().toISOString()
    };
    
    addChatMessage(userMessage);
    setIsLoading(true);

    try {
      const response = await mockApiService.postQuery(action.label, timestamp);
      
      const agentMessage = {
        role: 'agent' as const,
        content: response.chatResponse,
        timestamp: response.timestamp
      };
      
      addChatMessage(agentMessage);
      updateFromResponse(response);
    } catch (error) {
      console.error('Error executing action:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatHistory.map((message, index) => (
          <Card key={index} className={`p-3 ${message.role === 'user' ? 'bg-slate-700/50' : 'bg-slate-800/50'}`}>
            <div className="text-xs text-slate-400 mb-1">
              {message.role === 'user' ? 'You' : 'Agent'}
            </div>
            <div className="text-sm">{message.content}</div>
          </Card>
        ))}
        {isLoading && (
          <Card className="p-3 bg-slate-800/50">
            <div className="text-sm text-slate-400">Agent is thinking...</div>
          </Card>
        )}
      </div>

      {suggestedActions.length > 0 && (
        <div className="p-4 border-t border-slate-700">
          <div className="text-xs text-slate-400 mb-2">Suggested Actions:</div>
          <div className="space-y-2">
            {suggestedActions.map((action, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                className="w-full text-left justify-start"
                onClick={() => handleSuggestedAction(action)}
                disabled={isLoading}
              >
                {action.label}
              </Button>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 border-t border-slate-700">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about the situation..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
