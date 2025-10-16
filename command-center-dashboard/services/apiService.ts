/**
 * Real API Service for Command Center Backend
 * 
 * This service replaces the mock API service with real backend integration.
 * Configure the API endpoint and key in your .env.local file.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

interface ApiError {
  code: string;
  message: string;
  details?: any;
}

class ApiServiceError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiServiceError';
  }
}

/**
 * Make an authenticated request to the backend API
 */
async function fetchApi(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle error response
      const error = data.error as ApiError;
      throw new ApiServiceError(
        error.message || 'API request failed',
        error.code || 'UNKNOWN_ERROR',
        error.details
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiServiceError) {
      throw error;
    }
    
    // Network or parsing error
    console.error('API request failed:', error);
    throw new ApiServiceError(
      'Failed to connect to backend API',
      'NETWORK_ERROR',
      { originalError: error }
    );
  }
}

export const apiService = {
  /**
   * Get initial data load
   * Uses the query endpoint with a default query to load initial state
   */
  async getInitialLoad() {
    try {
      const response = await fetchApi('/agent/query', {
        method: 'POST',
        body: JSON.stringify({
          text: 'Show me the current situation overview with all active incidents',
        }),
      });
      
      return response;
    } catch (error) {
      console.error('Failed to get initial load:', error);
      throw error;
    }
  },

  /**
   * Post a natural language query to the AI agent
   */
  async postQuery(query: string, sessionId?: string, currentMapState?: any) {
    try {
      const response = await fetchApi('/agent/query', {
        method: 'POST',
        body: JSON.stringify({
          text: query,
          sessionId,
          currentMapState,
        }),
      });
      
      return response;
    } catch (error) {
      console.error('Failed to post query:', error);
      throw error;
    }
  },

  /**
   * Execute a pre-defined action
   */
  async executeAction(actionId: string, payload?: any) {
    try {
      const response = await fetchApi('/agent/action', {
        method: 'POST',
        body: JSON.stringify({
          actionId,
          payload,
        }),
      });
      
      return response;
    } catch (error) {
      console.error('Failed to execute action:', error);
      throw error;
    }
  },

  /**
   * Get incremental updates since a timestamp
   */
  async getUpdates(since: string, domain?: string) {
    try {
      const params = new URLSearchParams({ since });
      if (domain) {
        params.append('domain', domain);
      }
      
      const response = await fetchApi(`/data/updates?${params.toString()}`, {
        method: 'GET',
      });
      
      return response;
    } catch (error) {
      console.error('Failed to get updates:', error);
      throw error;
    }
  },

  /**
   * Check if API is configured and reachable
   */
  async healthCheck(): Promise<boolean> {
    if (!API_BASE_URL || !API_KEY) {
      console.warn('API not configured. Set NEXT_PUBLIC_API_BASE_URL and NEXT_PUBLIC_API_KEY');
      return false;
    }

    try {
      // Try a simple query to check connectivity
      await this.getUpdates(new Date().toISOString());
      return true;
    } catch (error) {
      console.error('API health check failed:', error);
      return false;
    }
  },
};

export { ApiServiceError };
export type { ApiError };
