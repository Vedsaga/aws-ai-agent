import { fetchAuthSession } from 'aws-amplify/auth';
import { Amplify } from 'aws-amplify';
import { showErrorToast, showNetworkErrorToast, showSuccessToast } from './toast-utils';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

// Track initialization state
let isInitializing = false;
let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

/**
 * Ensure Amplify is configured and auth session is ready
 * Prevents multiple simultaneous initialization attempts
 */
async function ensureInitialized(): Promise<void> {
  // If already initialized, return immediately
  if (isInitialized) {
    return;
  }

  // If initialization is in progress, wait for it
  if (isInitializing && initializationPromise) {
    return initializationPromise;
  }

  // Start initialization
  isInitializing = true;
  initializationPromise = (async () => {
    try {
      // Configure Amplify if not already configured
      if (!Amplify.getConfig().Auth) {
        Amplify.configure({
          Auth: {
            Cognito: {
              userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || '',
              userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || '',
              identityPoolId: process.env.NEXT_PUBLIC_IDENTITY_POOL_ID || '',
              loginWith: {
                email: true,
              },
              signUpVerificationMethod: 'code',
              userAttributes: {
                email: {
                  required: true,
                },
              },
              allowGuestAccess: false,
              passwordFormat: {
                minLength: 8,
                requireLowercase: true,
                requireUppercase: true,
                requireNumbers: true,
                requireSpecialCharacters: true,
              },
            },
          },
          API: {
            REST: {
              'multi-agent-api': {
                endpoint: process.env.NEXT_PUBLIC_API_URL || '',
                region: process.env.NEXT_PUBLIC_COGNITO_REGION || 'us-east-1',
              },
            },
            GraphQL: {
              endpoint: process.env.NEXT_PUBLIC_APPSYNC_URL || '',
              region: process.env.NEXT_PUBLIC_APPSYNC_REGION || 'us-east-1',
              defaultAuthMode: 'userPool',
            },
          },
        });
      }

      // Wait for auth session to be ready (with timeout)
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Auth initialization timeout')), 5000)
      );
      
      const sessionPromise = fetchAuthSession().catch(() => {
        // Session fetch can fail if user is not logged in, which is okay
        return null;
      });

      await Promise.race([sessionPromise, timeoutPromise]);

      isInitialized = true;
    } catch (error) {
      console.error('Initialization error:', error);
      // Don't throw - allow requests to proceed even if initialization has issues
      isInitialized = true;
    } finally {
      isInitializing = false;
    }
  })();

  return initializationPromise;
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
    // Ensure Amplify is initialized before making requests
    await ensureInitialized();

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
    
    // Show network error toast only for actual network errors
    // Don't show for initialization timeouts on page load
    if (showToast && error instanceof Error && !error.message.includes('timeout')) {
      showNetworkErrorToast();
    }

    return {
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 500,
    };
  }
}

/**
 * API request with retry logic and exponential backoff
 * Retries only on 5xx errors or network failures
 * @param endpoint - API endpoint
 * @param options - Fetch options
 * @param showToast - Whether to show error toasts
 * @param maxRetries - Maximum number of retry attempts (default: 3)
 * @returns API response
 */
export async function apiRequestWithRetry<T = any>(
  endpoint: string,
  options: RequestInit = {},
  showToast: boolean = true,
  maxRetries: number = 3
): Promise<ApiResponse<T>> {
  let lastError: any;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await apiRequest<T>(endpoint, options, false); // Don't show toast on retries
    
    // Success - return immediately
    if (response.data !== undefined && response.status < 500) {
      return response;
    }
    
    // Check if we should retry
    const shouldRetry = 
      (response.status >= 500 || response.status === 0) && // 5xx errors or network failures
      attempt < maxRetries;
    
    if (!shouldRetry) {
      // Last attempt failed - show toast if requested
      if (showToast) {
        if (response.status >= 500) {
          showErrorToast('Server error', 'Something went wrong on our end. Please try again later');
        } else if (response.status === 0) {
          showNetworkErrorToast();
        }
      }
      return response;
    }
    
    // Calculate backoff delay: 1s, 2s, 4s (capped at 10s)
    const baseDelay = 1000;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), 10000);
    
    console.log(`Request failed (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms...`);
    lastError = response.error;
    
    // Wait before retrying
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  
  // All retries exhausted
  return {
    error: lastError || 'Request failed after retries',
    status: 500,
  };
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

// ============================================================================
// TypeScript Interfaces
// ============================================================================

export interface AgentConfig {
  agent_name: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  system_prompt: string;
  tools: string[];
  output_schema: Record<string, any>;
  dependency_parent?: string;
  interrogative?: string;
  api_endpoint?: string;
}

export interface Agent extends AgentConfig {
  agent_id: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  updated_at: number;
}

export interface DomainConfig {
  template_name: string;
  domain_id: string;
  description: string;
  ingest_agent_ids: string[];
  query_agent_ids: string[];
}

export interface Domain extends DomainConfig {
  template_id: string;
  is_builtin: boolean;
  created_by: string;
  created_at: number;
  agent_count?: number;
  incident_count?: number;
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

// ============================================================================
// Agent CRUD Operations
// ============================================================================

/**
 * Create a new agent
 */
export async function createAgent(config: AgentConfig): Promise<ApiResponse<Agent>> {
  const response = await apiRequestWithRetry<Agent>(
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

  if (response.data) {
    showSuccessToast('Success', 'Agent created successfully');
  }

  return response;
}

/**
 * List all agents (built-in + custom)
 */
export async function listAgents(): Promise<ApiResponse<{ agents: Agent[] }>> {
  const response = await apiRequest<{ agents: Agent[] }>(
    '/config?type=agent',
    {},
    false // Don't show toast for GET requests
  );

  return response;
}

/**
 * Get a specific agent by ID
 */
export async function getAgent(agentId: string): Promise<ApiResponse<Agent>> {
  const response = await apiRequest<Agent>(
    `/config/agent/${agentId}`,
    {},
    false // Don't show toast for GET requests
  );

  return response;
}

/**
 * Update an existing agent
 */
export async function updateAgent(agentId: string, config: AgentConfig): Promise<ApiResponse<Agent>> {
  const response = await apiRequestWithRetry<Agent>(
    `/config/agent/${agentId}`,
    {
      method: 'PUT',
      body: JSON.stringify(config),
    },
    true // Show toast on error
  );

  if (response.data) {
    showSuccessToast('Success', 'Agent updated successfully');
  }

  return response;
}

/**
 * Delete an agent
 */
export async function deleteAgent(agentId: string): Promise<ApiResponse<void>> {
  const response = await apiRequestWithRetry<void>(
    `/config/agent/${agentId}`,
    {
      method: 'DELETE',
    },
    true // Show toast on error
  );

  if (response.status === 200 || response.status === 204) {
    showSuccessToast('Success', 'Agent deleted successfully');
  }

  return response;
}

// ============================================================================
// Domain CRUD Operations
// ============================================================================

/**
 * Create a new domain
 */
export async function createDomain(config: DomainConfig): Promise<ApiResponse<Domain>> {
  const response = await apiRequestWithRetry<Domain>(
    '/config',
    {
      method: 'POST',
      body: JSON.stringify({
        type: 'domain_template',
        config,
      }),
    },
    true // Show toast on error
  );

  if (response.data) {
    showSuccessToast('Success', 'Domain created successfully');
  }

  return response;
}

/**
 * List all domains (built-in + custom)
 */
export async function listDomains(): Promise<ApiResponse<{ domains: Domain[] }>> {
  const response = await apiRequest<{ domains: Domain[] }>(
    '/config?type=domain_template',
    {},
    false // Don't show toast for GET requests
  );

  return response;
}

/**
 * Get a specific domain by ID
 */
export async function getDomain(domainId: string): Promise<ApiResponse<Domain>> {
  const response = await apiRequest<Domain>(
    `/config/domain_template/${domainId}`,
    {},
    false // Don't show toast for GET requests
  );

  return response;
}

/**
 * Update an existing domain
 */
export async function updateDomain(domainId: string, config: DomainConfig): Promise<ApiResponse<Domain>> {
  const response = await apiRequestWithRetry<Domain>(
    `/config/domain_template/${domainId}`,
    {
      method: 'PUT',
      body: JSON.stringify(config),
    },
    true // Show toast on error
  );

  if (response.data) {
    showSuccessToast('Success', 'Domain updated successfully');
  }

  return response;
}

/**
 * Delete a domain
 */
export async function deleteDomain(domainId: string): Promise<ApiResponse<void>> {
  const response = await apiRequestWithRetry<void>(
    `/config/domain_template/${domainId}`,
    {
      method: 'DELETE',
    },
    true // Show toast on error
  );

  if (response.status === 200 || response.status === 204) {
    showSuccessToast('Success', 'Domain deleted successfully');
  }

  return response;
}
