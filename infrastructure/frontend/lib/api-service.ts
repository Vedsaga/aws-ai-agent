import {
  submitReport as apiSubmitReport,
  submitQuery as apiSubmitQuery,
  pollJobStatus,
  pollUntilComplete,
  listDomains as apiListDomains,
  getDomain as apiGetDomain,
  createDomain as apiCreateDomain,
  updateDomain as apiUpdateDomain,
  deleteDomain as apiDeleteDomain,
  listAgents as apiListAgents,
  getAgent as apiGetAgent,
  createAgent as apiCreateAgent,
  updateAgent as apiUpdateAgent,
  deleteAgent as apiDeleteAgent,
  fetchIncidents as apiFetchIncidents,
  fetchQueries as apiFetchQueries,
  listTools as apiListTools,
  registerTool as apiRegisterTool,
  listConfigs,
  createConfig,
  updateConfig,
  deleteConfig,
} from './api-client';
import type {
  IngestRequest,
  IngestResponse,
  QueryRequest,
  QueryResponse,
  StatusUpdate,
  DomainConfig,
  AgentConfig,
  ToolConfig,
  IncidentRecord,
  QueryResult,
  ConfigType,
} from './api-types';
import { DEFAULT_DOMAINS } from './domains-config';

export class ApiService {
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  // ==================== REPORT SUBMISSION ====================

  async submitReport(
    domainId: string,
    text: string,
    options?: {
      images?: string[];
      source?: string;
      priority?: 'low' | 'normal' | 'high' | 'urgent';
      reporter_contact?: string;
    }
  ): Promise<{ success: boolean; jobId?: string; error?: string }> {
    const data: IngestRequest = {
      domain_id: domainId,
      text,
      images: options?.images,
      source: options?.source || 'web',
      priority: options?.priority || 'normal',
      reporter_contact: options?.reporter_contact,
    };

    const response = await apiSubmitReport(data);

    if (response.data) {
      return {
        success: true,
        jobId: response.data.job_id,
      };
    }

    return {
      success: false,
      error: response.error || 'Failed to submit report',
    };
  }

  async submitReportWithPolling(
    domainId: string,
    text: string,
    onUpdate: (status: StatusUpdate) => void,
    options?: {
      images?: string[];
      source?: string;
      priority?: 'low' | 'normal' | 'high' | 'urgent';
      reporter_contact?: string;
      pollingIntervalMs?: number;
      maxAttempts?: number;
    }
  ): Promise<StatusUpdate | null> {
    const result = await this.submitReport(domainId, text, options);

    if (!result.success || !result.jobId) {
      return null;
    }

    return this.pollUntilComplete(
      result.jobId,
      onUpdate,
      options?.pollingIntervalMs,
      options?.maxAttempts
    );
  }

  // ==================== QUERY SUBMISSION ====================

  async submitQuery(
    domainId: string,
    question: string,
    options?: {
      filters?: any;
      include_visualizations?: boolean;
    }
  ): Promise<{ success: boolean; jobId?: string; error?: string }> {
    const data: QueryRequest = {
      domain_id: domainId,
      question,
      filters: options?.filters,
      include_visualizations: options?.include_visualizations,
    };

    const response = await apiSubmitQuery(data);

    if (response.data) {
      return {
        success: true,
        jobId: response.data.job_id,
      };
    }

    return {
      success: false,
      error: response.error || 'Failed to submit query',
    };
  }

  async submitQueryWithPolling(
    domainId: string,
    question: string,
    onUpdate: (status: StatusUpdate) => void,
    options?: {
      filters?: any;
      include_visualizations?: boolean;
      pollingIntervalMs?: number;
      maxAttempts?: number;
    }
  ): Promise<StatusUpdate | null> {
    const result = await this.submitQuery(domainId, question, options);

    if (!result.success || !result.jobId) {
      return null;
    }

    return this.pollUntilComplete(
      result.jobId,
      onUpdate,
      options?.pollingIntervalMs,
      options?.maxAttempts
    );
  }

  // ==================== STATUS POLLING ====================

  async pollUntilComplete(
    jobId: string,
    onUpdate: (status: StatusUpdate) => void,
    intervalMs: number = 2500,
    maxAttempts: number = 60
  ): Promise<StatusUpdate | null> {
    return pollUntilComplete(jobId, onUpdate, maxAttempts, intervalMs);
  }

  startPolling(
    jobId: string,
    onUpdate: (status: StatusUpdate) => void,
    intervalMs: number = 2500
  ): void {
    if (this.pollingIntervals.has(jobId)) {
      return;
    }

    const poll = async () => {
      const response = await pollJobStatus(jobId);
      if (response.data) {
        onUpdate(response.data);

        if (
          response.data.status === 'completed' ||
          response.data.status === 'failed'
        ) {
          this.stopPolling(jobId);
        }
      }
    };

    poll();
    const interval = setInterval(poll, intervalMs);
    this.pollingIntervals.set(jobId, interval);
  }

  stopPolling(jobId: string): void {
    const interval = this.pollingIntervals.get(jobId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(jobId);
    }
  }

  stopAllPolling(): void {
    this.pollingIntervals.forEach((interval) => clearInterval(interval));
    this.pollingIntervals.clear();
  }

  // ==================== DOMAIN MANAGEMENT ====================

  async listDomains(): Promise<DomainConfig[]> {
    try {
      const response = await apiListDomains();

      if (response.data && response.data.length > 0) {
        return response.data;
      }

      console.log('Using default domains as fallback');
      return DEFAULT_DOMAINS as DomainConfig[];
    } catch (error) {
      console.warn('Error fetching domains, using defaults:', error);
      return DEFAULT_DOMAINS as DomainConfig[];
    }
  }

  async getDomain(domainId: string): Promise<DomainConfig | null> {
    const response = await apiGetDomain(domainId);
    return response.data || null;
  }

  async createDomain(domain: DomainConfig): Promise<boolean> {
    const response = await apiCreateDomain(domain);
    return response.status === 200 || response.status === 201;
  }

  async updateDomain(domainId: string, domain: DomainConfig): Promise<boolean> {
    const response = await apiUpdateDomain(domainId, domain);
    return response.status === 200;
  }

  async deleteDomain(domainId: string): Promise<boolean> {
    const response = await apiDeleteDomain(domainId);
    return response.status === 200 || response.status === 204;
  }

  // ==================== AGENT MANAGEMENT ====================

  async listAgents(): Promise<AgentConfig[]> {
    const response = await apiListAgents();
    return response.data || [];
  }

  async getAgent(agentId: string): Promise<AgentConfig | null> {
    const response = await apiGetAgent(agentId);
    return response.data || null;
  }

  async createAgent(agent: AgentConfig): Promise<boolean> {
    const response = await apiCreateAgent(agent);
    return response.status === 200 || response.status === 201;
  }

  async updateAgent(agentId: string, agent: AgentConfig): Promise<boolean> {
    const response = await apiUpdateAgent(agentId, agent);
    return response.status === 200;
  }

  async deleteAgent(agentId: string): Promise<boolean> {
    const response = await apiDeleteAgent(agentId);
    return response.status === 200 || response.status === 204;
  }

  // ==================== DATA RETRIEVAL ====================

  async fetchIncidents(
    domainId?: string,
    filters?: any
  ): Promise<IncidentRecord[]> {
    const response = await apiFetchIncidents(domainId, filters);
    return response.data?.data || [];
  }

  async fetchQueries(domainId?: string, filters?: any): Promise<QueryResult[]> {
    const response = await apiFetchQueries(domainId, filters);
    return response.data?.data || [];
  }

  // ==================== TOOL REGISTRY ====================

  async listTools(): Promise<ToolConfig[]> {
    const response = await apiListTools();
    return response.data || [];
  }

  async registerTool(tool: ToolConfig): Promise<boolean> {
    const response = await apiRegisterTool(tool);
    return response.status === 200 || response.status === 201;
  }

  // ==================== GENERIC CONFIG OPERATIONS ====================

  async listConfigs(type: ConfigType): Promise<any[]> {
    const response = await listConfigs(type);
    return response.data?.configs || [];
  }

  async createCustomConfig(type: ConfigType, config: any): Promise<boolean> {
    const response = await createConfig({ type, config });
    return response.status === 200 || response.status === 201;
  }

  async updateCustomConfig(
    type: ConfigType,
    id: string,
    config: any
  ): Promise<boolean> {
    const response = await updateConfig(type, id, config);
    return response.status === 200;
  }

  async deleteCustomConfig(type: ConfigType, id: string): Promise<boolean> {
    const response = await deleteConfig(type, id);
    return response.status === 200 || response.status === 204;
  }

  // ==================== BATCH OPERATIONS ====================

  async submitMultipleReports(
    reports: Array<{
      domainId: string;
      text: string;
      images?: string[];
    }>
  ): Promise<{ jobIds: string[]; errors: string[] }> {
    const jobIds: string[] = [];
    const errors: string[] = [];

    for (const report of reports) {
      const result = await this.submitReport(
        report.domainId,
        report.text,
        report
      );

      if (result.success && result.jobId) {
        jobIds.push(result.jobId);
      } else {
        errors.push(result.error || 'Unknown error');
      }
    }

    return { jobIds, errors };
  }

  // ==================== UTILITY METHODS ====================

  async checkHealth(): Promise<boolean> {
    try {
      const domains = await this.listDomains();
      return domains.length > 0;
    } catch {
      return false;
    }
  }

  cleanup(): void {
    this.stopAllPolling();
  }
}

export const apiService = new ApiService();

export default apiService;
