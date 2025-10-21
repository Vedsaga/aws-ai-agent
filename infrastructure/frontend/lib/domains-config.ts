// Hardcoded domain configurations as fallback when API fails
// This ensures the frontend works even if the config API is unavailable

export interface DomainConfig {
  domain_id: string;
  name: string;
  description: string;
  icon?: string;
  color?: string;
}

export const DEFAULT_DOMAINS: DomainConfig[] = [
  {
    domain_id: 'civic_complaints',
    name: 'Civic Complaints',
    description: 'Report and track civic infrastructure issues like potholes, street lights, traffic problems',
    icon: '🏙️',
    color: 'blue',
  },
  {
    domain_id: 'emergency_services',
    name: 'Emergency Services',
    description: 'Emergency incidents, accidents, fires, medical emergencies',
    icon: '🚨',
    color: 'red',
  },
  {
    domain_id: 'environmental',
    name: 'Environmental',
    description: 'Environmental issues, pollution, waste management, air quality',
    icon: '🌳',
    color: 'green',
  },
];

export const DEFAULT_DOMAIN_ID = 'civic_complaints';

export function getDomainById(domainId: string): DomainConfig | undefined {
  return DEFAULT_DOMAINS.find(d => d.domain_id === domainId);
}

export function getDomainName(domainId: string): string {
  const domain = getDomainById(domainId);
  return domain?.name || domainId;
}

export async function loadDomains(): Promise<DomainConfig[]> {
  // Try to load from API first, fall back to hardcoded
  try {
    // API call would go here
    // For now, just return hardcoded
    return DEFAULT_DOMAINS;
  } catch (error) {
    console.warn('Failed to load domains from API, using defaults:', error);
    return DEFAULT_DOMAINS;
  }
}
