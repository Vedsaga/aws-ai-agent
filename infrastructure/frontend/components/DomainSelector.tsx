'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { listDomains, Domain } from '@/lib/api-client';
import { showErrorToast } from '@/lib/toast-utils';

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
  const [error, setError] = useState<string | null>(null);

  const loadDomains = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await listDomains();

      if (response.data?.domains) {
        // Display both built-in and custom domains
        setDomains(response.data.domains);
        
        // Auto-select first domain if none selected
        if (!selectedDomain && response.data.domains.length > 0) {
          onDomainChange(response.data.domains[0].domain_id);
        }
      } else if (response.error) {
        // Handle error states
        setError(response.error);
        setDomains([]);
        
        // Only show error toast if it's not an auth error (401/403)
        if (response.status !== 401 && response.status !== 403) {
          showErrorToast('Failed to load domains', response.error);
        }
      }
    } catch (error) {
      console.error('Error loading domains:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError(errorMessage);
      setDomains([]);
    } finally {
      setLoading(false);
    }
  }, [selectedDomain, onDomainChange]);

  useEffect(() => {
    loadDomains();
  }, [loadDomains]);

  // Loading state
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

  // Error state
  if (error && domains.length === 0) {
    return (
      <div className={`w-full ${className}`}>
        <Select disabled>
          <SelectTrigger className="w-full border-red-500">
            <SelectValue placeholder="Failed to load domains" />
          </SelectTrigger>
        </Select>
      </div>
    );
  }

  // Empty state
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
                {/* Show domain description in dropdown */}
                {domain.description && (
                  <div className="text-xs text-muted-foreground line-clamp-2">
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
