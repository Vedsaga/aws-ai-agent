'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface ChatMessage {
  id: string;
  type: 'user' | 'system' | 'agent';
  content: string;
  timestamp: string;
  metadata?: {
    jobId?: string;
    agentName?: string;
    status?: string;
  };
}

interface AppState {
  selectedDomain: string | null;
  chatHistory: Record<string, ChatMessage[]>;
}

interface AppContextType extends AppState {
  setSelectedDomain: (domainId: string | null) => void;
  addChatMessage: (domainId: string, message: ChatMessage) => void;
  clearChatHistory: (domainId: string) => void;
  getChatHistory: (domainId: string) => ChatMessage[];
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const STORAGE_KEY = 'maos_chat_history';
const DOMAIN_STORAGE_KEY = 'maos_selected_domain';

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedDomain, setSelectedDomainState] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<Record<string, ChatMessage[]>>({});
  const [isInitialized, setIsInitialized] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem(STORAGE_KEY);
      if (savedHistory) {
        const parsed = JSON.parse(savedHistory);
        setChatHistory(parsed);
      }

      const savedDomain = localStorage.getItem(DOMAIN_STORAGE_KEY);
      if (savedDomain) {
        setSelectedDomainState(savedDomain);
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error);
    } finally {
      setIsInitialized(true);
    }
  }, []);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (isInitialized) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory));
      } catch (error) {
        console.error('Error saving chat history to localStorage:', error);
      }
    }
  }, [chatHistory, isInitialized]);

  // Save selected domain to localStorage whenever it changes
  useEffect(() => {
    if (isInitialized && selectedDomain) {
      try {
        localStorage.setItem(DOMAIN_STORAGE_KEY, selectedDomain);
      } catch (error) {
        console.error('Error saving selected domain to localStorage:', error);
      }
    }
  }, [selectedDomain, isInitialized]);

  const setSelectedDomain = (domainId: string | null) => {
    setSelectedDomainState(domainId);
  };

  const addChatMessage = (domainId: string, message: ChatMessage) => {
    setChatHistory((prev) => ({
      ...prev,
      [domainId]: [...(prev[domainId] || []), message],
    }));
  };

  const clearChatHistory = (domainId: string) => {
    setChatHistory((prev) => ({
      ...prev,
      [domainId]: [],
    }));
  };

  const getChatHistory = (domainId: string): ChatMessage[] => {
    return chatHistory[domainId] || [];
  };

  const value: AppContextType = {
    selectedDomain,
    chatHistory,
    setSelectedDomain,
    addChatMessage,
    clearChatHistory,
    getChatHistory,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}
