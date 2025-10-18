import { fetchAuthSession } from 'aws-amplify/auth';

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
  options: RequestInit = {}
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

    return {
      data: response.ok ? data : undefined,
      error: response.ok ? undefined : data.message || 'Request failed',
      status: response.status,
    };
  } catch (error) {
    console.error('API request error:', error);
    return {
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 500,
    };
  }
}

// Ingestion API
export async function submitReport(
  domainId: string,
  text: string,
  images?: string[]
): Promise<ApiResponse<{ job_id: string; status: string }>> {
  return apiRequest('/ingest', {
    method: 'POST',
    body: JSON.stringify({
      domain_id: domainId,
      text,
      images: images || [],
    }),
  });
}

// Query API
export async function submitQuery(
  domainId: string,
  question: string
): Promise<ApiResponse<{ job_id: string; status: string }>> {
  return apiRequest('/query', {
    method: 'POST',
    body: JSON.stringify({
      domain_id: domainId,
      question,
    }),
  });
}

// Data API
export async function fetchIncidents(
  filters: Record<string, any>
): Promise<ApiResponse<{ data: any[]; pagination: any }>> {
  const queryParams = new URLSearchParams({
    type: 'retrieval',
    filters: JSON.stringify(filters),
  });
  return apiRequest(`/data?${queryParams.toString()}`);
}

// Configuration API
export async function createAgentConfig(
  config: any
): Promise<ApiResponse<{ config_id: string; status: string }>> {
  return apiRequest('/config', {
    method: 'POST',
    body: JSON.stringify({
      type: 'agent',
      config,
    }),
  });
}

export async function getAgentConfigs(): Promise<ApiResponse<{ configs: any[] }>> {
  return apiRequest('/config/agent');
}

export async function getToolRegistry(): Promise<ApiResponse<{ tools: any[] }>> {
  return apiRequest('/tools');
}

export async function getDomains(): Promise<ApiResponse<{ domains: any[] }>> {
  return apiRequest('/config/domain');
}
