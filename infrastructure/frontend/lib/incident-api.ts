// Incident API Client - Submit reports and poll status

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_BASE_URL) {
  console.error('ERROR: NEXT_PUBLIC_API_URL environment variable not set');
  console.error('Please set it in your .env.local file');
}

export interface IncidentSubmission {
  domain_id: string;
  text: string;
  source?: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  reporter_contact?: string;
}

export interface IncidentResponse {
  job_id: string;
  status: string;
  message: string;
  timestamp: string;
  estimated_completion_seconds?: number;
}

export interface JobStatus {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  results?: any;
  structured_data?: any;
}

export class IncidentAPI {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  async submitIncident(data: IncidentSubmission): Promise<IncidentResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async pollJobStatus(jobId: string, maxAttempts = 60, intervalMs = 2000): Promise<JobStatus> {
    // Try status endpoint first
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/status/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${this.token}`,
          },
        });

        if (response.ok) {
          const status = await response.json();
          if (status.status === 'completed' || status.status === 'failed') {
            return status;
          }
        }
      } catch (error) {
        // Status endpoint might not exist, fallback to checking incidents
      }

      // Fallback: check incidents table directly
      try {
        const incidents = await this.getRecentIncidents(1, jobId);
        if (incidents && incidents.length > 0) {
          const incident = incidents[0];
          if (incident.status === 'completed' || incident.status === 'failed') {
            return {
              job_id: jobId,
              status: incident.status,
              results: incident.structured_data,
              structured_data: incident.structured_data,
            };
          }
        }
      } catch (error) {
        console.warn('Failed to check incident status:', error);
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    throw new Error('Job status check timeout');
  }

  async getRecentIncidents(limit = 10, jobId?: string): Promise<any[]> {
    // This would need a proper data API endpoint
    // For now, return empty array as we don't have direct access
    return [];
  }

  async queryIncidents(query: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        domain_id: 'civic_complaints',
        question: query,
      }),
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.status}`);
    }

    return response.json();
  }
}

export const incidentAPI = new IncidentAPI();

// React hook for easy usage
export function useIncidentAPI() {
  return {
    submitIncident: (data: IncidentSubmission) => incidentAPI.submitIncident(data),
    pollJobStatus: (jobId: string) => incidentAPI.pollJobStatus(jobId),
    queryIncidents: (query: string) => incidentAPI.queryIncidents(query),
  };
}
