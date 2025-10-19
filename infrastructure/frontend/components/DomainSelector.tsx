'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiRequest } from '@/lib/api-client';
import { showErrorToast } from '@/lib/toast-utils';

interface Domain {
  domain_id: string;
  template_name: string;
  description: string;
  agent_configs?: any[];
  playbook_configs?: any[];
  created_by?: string;
  created_at?: string;
}

interface DomainSelectorProps {
  selectedDomain: string | null;
  onDomainChange: (domainId: string) => void;
  className?: string;
}

export default function DomainSelector({
  selectedDomain,
  onDomainChange,
  className = '',
}: DomainSelectorProps) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDomains = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiRequest<{ configs: Domain[]; count: number }>(
        '/config?type=domain_template',
        {},
        false // Don't show toast for GET requests
      );

      if (response.data?.configs) {
        setDomains(response.data.configs);
        
        // Auto-select first domain if none selected
        if (!selectedDomain && response.data.configs.length > 0) {
          onDomainChange(response.data.configs[0].domain_id);
        }
      } else if (response.error) {
        // Only show error toast if it's not an auth error (401/403)
        if (response.status !== 401 && response.status !== 403) {
          showErrorToast('Failed to load domains', response.error);
        }
        setDomains([]);
      }
    } catch (error) {
      console.error('Error loading domains:', error);
      // Don't show toast for network errors during initial load
      setDomains([]);
    } finally {
      setLoading(false);
    }
  }, [selectedDomain, onDomainChange]);

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  if (loading) {
    return (
      <div className={`w-full ${className}`}>
        <Select disabled>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Loading domains..." />
          </SelectTrigger>
        </Select>
      </div>
    );
  }

  if (domains.length === 0) {
    return (
      <div className={`w-full ${className}`}>
        <Select disabled>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="No domains available" />
          </SelectTrigger>
        </Select>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      <Select value={selectedDomain || undefined} onValueChange={onDomainChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select a domain" />
        </SelectTrigger>
        <SelectContent>
          {domains.map((domain) => (
            <SelectItem key={domain.domain_id} value={domain.domain_id}>
              <div className="flex flex-col">
                <div className="font-medium">{domain.template_name}</div>
                {domain.description && (
                  <div className="text-xs text-muted-foreground">
                    {domain.description}
                  </div>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
