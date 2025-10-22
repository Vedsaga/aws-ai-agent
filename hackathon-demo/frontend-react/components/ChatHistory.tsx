'use client';

import { useEffect, useRef, useMemo } from 'react';
import { useAppContext, ChatMessage } from '@/contexts/AppContext';

export default function ChatHistory() {
  const { selectedDomain, getChatHistory } = useAppContext();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messages = useMemo(
    () => (selectedDomain ? getChatHistory(selectedDomain) : []),
    [selectedDomain, getChatHistory]
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!selectedDomain) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Select a domain to view chat history
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No messages yet. Submit a report or ask a question to get started.
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-4 space-y-3">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex flex-col ${
            message.type === 'user' ? 'items-end' : 'items-start'
          }`}
        >
          <div
            className={`max-w-[85%] rounded-lg p-3 ${
              message.type === 'user'
                ? 'bg-primary text-primary-foreground'
                : message.type === 'system'
                ? 'bg-muted text-foreground'
                : 'bg-secondary text-secondary-foreground'
            }`}
          >
            {message.metadata?.agentName && (
              <div className="text-xs font-semibold mb-1 opacity-80">
                {message.metadata.agentName}
              </div>
            )}
            <div className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </div>
            <div className="text-xs opacity-70 mt-1">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}
