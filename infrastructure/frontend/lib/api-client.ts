import { fetchAuthSession } from "aws-amplify/auth";
import { Amplify } from "aws-amplify";
import {
  showErrorToast,
  showNetworkErrorToast,
  showSuccessToast,
} from "./toast-utils";
import { initGuard } from "./init-guard";
import type {
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
  QueryResult,
  StatusUpdate,
  ConfigRequest,
  ConfigResponse,
  ConfigItem,
  ConfigType,
  DataRequest,
  DataResponse,
  IncidentRecord,
  DomainConfig,
  AgentConfig,
  ToolConfig,
} from "./api-types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

async function ensureInitialized(): Promise<void> {
  try {
    await initGuard.ensureReady({ timeout: 5000, skipIfInvalid: true });
  } catch (error) {
    console.error("Initialization error:", error);
  }
}

async function getAuthHeaders(): Promise<HeadersInit> {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();

    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  } catch (error) {
    console.error("Error getting auth headers:", error);
    return {
      "Content-Type": "application/json",
    };
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {},
  showToast: boolean = true,
): Promise<ApiResponse<T>> {
  try {
    await ensureInitialized();

    if (!initGuard.canMakeApiCalls()) {
      console.warn("API not ready - skipping request to:", endpoint);
      return {
        error: "API not configured",
        status: 503,
      };
    }

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
      const errorMessage = data.message || data.error || "Request failed";

      if (showToast) {
        if (response.status === 401) {
          showErrorToast("Session expired", "Please log in again");
        } else if (response.status === 403) {
          showErrorToast(
            "Access denied",
            "You do not have permission to perform this action",
          );
        } else if (response.status === 400) {
          showErrorToast("Invalid request", errorMessage);
        } else if (response.status >= 500) {
          showErrorToast(
            "Server error",
            "Something went wrong. Please try again later",
          );
        } else {
          showErrorToast("Request failed", errorMessage);
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
    console.error("API request error:", error);

    if (
      showToast &&
      error instanceof Error &&
      !error.message.includes("timeout")
    ) {
      showNetworkErrorToast();
    }

    return {
      error: error instanceof Error ? error.message : "Unknown error",
      status: 500,
    };
  }
}

export async function apiRequestWithRetry<T = any>(
  endpoint: string,
  options: RequestInit = {},
  showToast: boolean = true,
  maxRetries: number = 3,
): Promise<ApiResponse<T>> {
  let lastError: any;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await apiRequest<T>(endpoint, options, false);

    if (response.data !== undefined && response.status < 500) {
      return response;
    }

    const shouldRetry =
      (response.status >= 500 || response.status === 0) && attempt < maxRetries;

    if (!shouldRetry) {
      if (showToast) {
        if (response.status >= 500) {
          showErrorToast(
            "Server error",
            "Something went wrong. Please try again later",
          );
        } else if (response.status === 0) {
          showNetworkErrorToast();
        }
      }
      return response;
    }

    const baseDelay = 1000;
    const delay = Math.min(baseDelay * Math.pow(2, attempt), 10000);

    console.log(
      `Request failed (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms...`,
    );
    lastError = response.error;

    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  return {
    error: lastError || "Request failed after retries",
    status: 500,
  };
}

// ==================== INGEST API ====================

export async function submitReport(
  data: IngestRequest,
): Promise<ApiResponse<IngestResponse>> {
  return apiRequest<IngestResponse>("/api/v1/ingest", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ==================== QUERY API ====================

export async function submitQuery(
  data: QueryRequest,
): Promise<ApiResponse<QueryResponse>> {
  return apiRequest<QueryResponse>("/api/v1/query", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ==================== STATUS POLLING ====================

export async function pollJobStatus(
  jobId: string,
): Promise<ApiResponse<StatusUpdate>> {
  return apiRequest<StatusUpdate>(
    `/api/v1/status/${jobId}`,
    {
      method: "GET",
    },
    false,
  );
}

export async function pollUntilComplete(
  jobId: string,
  onUpdate?: (status: StatusUpdate) => void,
  maxAttempts: number = 30,
  intervalMs: number = 2000,
): Promise<StatusUpdate | null> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await pollJobStatus(jobId);

    if (response.data) {
      if (onUpdate) {
        onUpdate(response.data);
      }

      if (
        response.data.status === "completed" ||
        response.data.status === "failed"
      ) {
        return response.data;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  return null;
}

// ==================== CONFIG API ====================

export async function listConfigs(
  type: ConfigType,
): Promise<ApiResponse<ConfigResponse>> {
  return apiRequest<ConfigResponse>(`/api/v1/config?type=${type}`, {
    method: "GET",
  });
}

export async function getConfig(
  type: ConfigType,
  id: string,
): Promise<ApiResponse<ConfigItem>> {
  return apiRequest<ConfigItem>(`/api/v1/config/${type}/${id}`, {
    method: "GET",
  });
}

export async function createConfig(
  data: ConfigRequest,
): Promise<ApiResponse<ConfigItem>> {
  const response = await apiRequest<ConfigItem>("/api/v1/config", {
    method: "POST",
    body: JSON.stringify(data),
  });

  if (response.data) {
    showSuccessToast(
      "Configuration created",
      `${data.type} has been created successfully`,
    );
  }

  return response;
}

export async function updateConfig(
  type: ConfigType,
  id: string,
  config: any,
): Promise<ApiResponse<ConfigItem>> {
  const response = await apiRequest<ConfigItem>(
    `/api/v1/config/${type}/${id}`,
    {
      method: "PUT",
      body: JSON.stringify({ config }),
    },
  );

  if (response.data) {
    showSuccessToast(
      "Configuration updated",
      `${type} has been updated successfully`,
    );
  }

  return response;
}

export async function deleteConfig(
  type: ConfigType,
  id: string,
): Promise<ApiResponse<void>> {
  const response = await apiRequest<void>(`/api/v1/config/${type}/${id}`, {
    method: "DELETE",
  });

  if (response.status === 200) {
    showSuccessToast(
      "Configuration deleted",
      `${type} has been deleted successfully`,
    );
  }

  return response;
}

// ==================== DOMAIN-SPECIFIC CONFIG ====================

export async function listDomains(): Promise<ApiResponse<DomainConfig[]>> {
  const response = await listConfigs("domain");
  if (response.data) {
    return {
      data: response.data.configs.map((c) => c.config as DomainConfig),
      status: response.status,
    };
  }
  return { error: response.error, status: response.status };
}

export async function getDomain(
  domainId: string,
): Promise<ApiResponse<DomainConfig>> {
  const response = await getConfig("domain", domainId);
  if (response.data) {
    return {
      data: response.data.config as DomainConfig,
      status: response.status,
    };
  }
  return { error: response.error, status: response.status };
}

export async function createDomain(
  domain: DomainConfig,
): Promise<ApiResponse<ConfigItem>> {
  return createConfig({
    type: "domain",
    config: domain,
  });
}

export async function updateDomain(
  domainId: string,
  domain: DomainConfig,
): Promise<ApiResponse<ConfigItem>> {
  return updateConfig("domain", domainId, domain);
}

export async function deleteDomain(
  domainId: string,
): Promise<ApiResponse<void>> {
  return deleteConfig("domain", domainId);
}

// ==================== AGENT-SPECIFIC CONFIG ====================

export async function listAgents(): Promise<ApiResponse<AgentConfig[]>> {
  const response = await listConfigs("agent");
  if (response.data) {
    return {
      data: response.data.configs.map((c) => c.config as AgentConfig),
      status: response.status,
    };
  }
  return { error: response.error, status: response.status };
}

export async function getAgent(
  agentId: string,
): Promise<ApiResponse<AgentConfig>> {
  const response = await getConfig("agent", agentId);
  if (response.data) {
    return {
      data: response.data.config as AgentConfig,
      status: response.status,
    };
  }
  return { error: response.error, status: response.status };
}

export async function createAgent(
  agent: AgentConfig,
): Promise<ApiResponse<ConfigItem>> {
  return createConfig({
    type: "agent",
    config: agent,
  });
}

export async function updateAgent(
  agentId: string,
  agent: AgentConfig,
): Promise<ApiResponse<ConfigItem>> {
  return updateConfig("agent", agentId, agent);
}

export async function deleteAgent(agentId: string): Promise<ApiResponse<void>> {
  return deleteConfig("agent", agentId);
}

// ==================== DATA API ====================

export async function fetchData<T = any>(
  params: DataRequest = {},
): Promise<ApiResponse<DataResponse<T>>> {
  const queryParams = new URLSearchParams();

  if (params.type) queryParams.append("type", params.type);
  if (params.filters)
    queryParams.append("filters", JSON.stringify(params.filters));

  const queryString = queryParams.toString();
  const endpoint = `/api/v1/data${queryString ? `?${queryString}` : ""}`;

  return apiRequest<DataResponse<T>>(endpoint, {
    method: "GET",
  });
}

export async function fetchIncidents(
  domainId?: string,
  filters?: any,
): Promise<ApiResponse<DataResponse<IncidentRecord>>> {
  return fetchData<IncidentRecord>({
    type: "incidents",
    filters: {
      ...(domainId && { domain_id: domainId }),
      ...filters,
    },
  });
}

export async function fetchQueries(
  domainId?: string,
  filters?: any,
): Promise<ApiResponse<DataResponse<QueryResult>>> {
  return fetchData<QueryResult>({
    type: "queries",
    filters: {
      ...(domainId && { domain_id: domainId }),
      ...filters,
    },
  });
}

// ==================== TOOLS API ====================

export async function listTools(): Promise<ApiResponse<ToolConfig[]>> {
  const response = await apiRequest<{ tools: ToolConfig[] }>("/api/v1/tools", {
    method: "GET",
  });

  if (response.data) {
    return {
      data: response.data.tools,
      status: response.status,
    };
  }

  return { error: response.error, status: response.status };
}

export async function registerTool(
  tool: ToolConfig,
): Promise<ApiResponse<ToolConfig>> {
  const response = await apiRequest<ToolConfig>("/api/v1/tools", {
    method: "POST",
    body: JSON.stringify(tool),
  });

  if (response.data) {
    showSuccessToast(
      "Tool registered",
      `${tool.name} has been registered successfully`,
    );
  }

  return response;
}

// ==================== UTILITY FUNCTIONS ====================

export function validateResponse(data: any, requiredFields: string[]): boolean {
  if (!data || typeof data !== "object") {
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

export function formatError(error: any): string {
  if (typeof error === "string") return error;
  if (error?.message) return error.message;
  if (error?.error) return error.error;
  return "An unknown error occurred";
}

export function isNetworkError(error: any): boolean {
  if (!error) return false;
  const errorStr = formatError(error).toLowerCase();
  return (
    errorStr.includes("network") ||
    errorStr.includes("fetch") ||
    errorStr.includes("connection") ||
    errorStr.includes("timeout")
  );
}

// Export API base URL for external use
export { API_BASE_URL };
