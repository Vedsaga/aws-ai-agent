'use client';

import { createContext, useContext, ReactNode, useState } from 'react';

interface AppContextType {
  selectedDomain?: string;
  setSelectedDomain?: (domain: string) => void;
}

const AppContext = createContext<AppContextType>({});

export function AppProvider({ children }: { children: ReactNode }) {
  const [selectedDomain, setSelectedDomain] = useState<string>('civic-sense');
  
  return (
    <AppContext.Provider value={{ selectedDomain, setSelectedDomain }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}

// Alias for backward compatibility
export const useAppContext = useApp;
