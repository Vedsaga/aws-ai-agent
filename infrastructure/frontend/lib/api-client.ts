import { fetchAuthSession } from 'aws-amplify/auth';
import { showErrorToast, showNetworkErrorToast } from './toast-utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();
    
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  } catch (error) {
    console.error('Error getting auth headers:', error);
    return {
      'Content-Type': 'application/json',
    };
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {},
  showToast: boolean = true
): Promise<ApiResponse<T>> {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.message || data.error || 'Request failed';
      
      // Show appropriate error toast based on status code
      if (showToast) {
        if (response.status === 401) {
          showErrorToast('Session expired', 'Please log in again');
        } else if (response.status === 403) {
          showErrorToast('Access denied', 'You do not have permission to perform this action');
        } else if (response.status === 400) {
          showErrorToast('Invalid request', errorMessage);
        } else if (response.status >= 500) {
          showErrorToast('Server error', 'Something went wrong on our end. Please try again later');
        } else {
          showErrorToast('Request failed', errorMessage);
        }
      }

      return {
        data: undefined,
        error: errorMessage,
        status: response.status,
      };
    }

    return {
      data,
      error: undefined,
      status: response.status,
    };
  } catch (error) {
    console.error('API request error:', error);
    
    // Show network error toast
    if (showToast) {
      showNetworkErrorToast();
    }

    return {
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 500,
    };
  }
}

/**
 * Validate API response structure
 * @param data - Response data to validate
 * @param requiredFields - Array of required field names
 * @returns true if valid, false otherwise
 */
export function validateResponse(data: any, requiredFields: string[]): boolean {
  if (!data || typeof data !== 'object') {
    return false;
  }

  for (const field of requiredFields) {
    if (!(field in data)) {
      console.error(`Missing required field: ${field}`);
      return false;
    }
  }

  return true;
}

// Ingestion API
export async function submitReport(
  domainId: string,
  text: string,
  images?: string[]
): Promise<ApiResponse<{ job_id: string; status: string }>> {
  const response = await apiRequest<{ job_id: string; status: string }>(
    '/ingest',
    {
      method: 'POST',
      body: JSON.stringify({
        domain_id: domainId,
        text,
        images: images || [],
      }),
    },
    true // Show toast on error
  );

  // Validate response structure
  if (response.data && !validateResponse(response.data, ['job_id'])) {
    showErrorToast('Invalid response', 'Received unexpected data from server');
    return {
      error: 'Invalid response format',
      status: 500,
    };
  }

  return response;
}

// Query API
export async function submitQuery(
  domainId: string,
  question: string
): Promise<ApiResponse<{ job_id: string; status: string }>> {
  const response = await apiRequest<{ job_id: string; status: string }>(
    '/query',
    {
      method: 'POST',
      body: JSON.stringify({
        domain_id: domainId,
        question,
      }),
    },
    true // Show toast on error
  );

  // Validate response structure
  if (response.data && !validateResponse(response.data, ['job_id'])) {
    showErrorToast('Invalid response', 'Received unexpected data from server');
    return {
      error: 'Invalid response format',
      status: 500,
    };
  }

  return response;
}

// Data API
export async function fetchIncidents(
  filters: Record<string, any>
): Promise<ApiResponse<{ data: any[]; pagination: any }>> {
  const queryParams = new URLSearchParams({
    type: 'retrieval',
    filters: JSON.stringify(filters),
  });
  
  const response = await apiRequest<{ data: any[]; pagination: any }>(
    `/data?${queryParams.toString()}`,
    {},
    true // Show toast on error
  );

  // Validate response structure
  if (response.data && !validateResponse(response.data, ['data'])) {
    showErrorToast('Invalid response', 'Received unexpected data from server');
    return {
      error: 'Invalid response format',
      status: 500,
    };
  }

  return response;
}

// Configuration API
export async function createAgentConfig(
  config: any
): Promise<ApiResponse<{ config_id: string; status: string }>> {
  const response = await apiRequest<{ config_id: string; status: string }>(
    '/config',
    {
      method: 'POST',
      body: JSON.stringify({
        type: 'agent',
        config,
      }),
    },
    true // Show toast on error
  );

  return response;
}

export async function getAgentConfigs(): Promise<ApiResponse<{ configs: any[] }>> {
  const response = await apiRequest<{ configs: any[] }>(
    '/config/agent',
    {},
    false // Don't show toast for GET requests (handle in component)
  );

  return response;
}

export async function getToolRegistry(): Promise<ApiResponse<{ tools: any[] }>> {
  const response = await apiRequest<{ tools: any[] }>(
    '/tools',
    {},
    false // Don't show toast for GET requests
  );

  return response;
}

export async function getDomains(): Promise<ApiResponse<{ domains: any[] }>> {
  const response = await apiRequest<{ domains: any[] }>(
    '/config/domain',
    {},
    false // Don't show toast for GET requests
  );

  return response;
}
