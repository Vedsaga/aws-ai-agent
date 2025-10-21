import { useState, useEffect, useCallback, useRef } from 'react';
import { pollJobStatus } from '@/lib/api-client';
import type { StatusUpdate, JobStatus } from '@/lib/api-types';

interface UseJobPollingOptions {
  jobId: string | null;
  enabled?: boolean;
  intervalMs?: number;
  maxAttempts?: number;
  onUpdate?: (status: StatusUpdate) => void;
  onComplete?: (status: StatusUpdate) => void;
  onError?: (error: string) => void;
}

interface UseJobPollingResult {
  status: StatusUpdate | null;
  isPolling: boolean;
  error: string | null;
  progress: number;
  startPolling: () => void;
  stopPolling: () => void;
  resetPolling: () => void;
}

const TERMINAL_STATUSES: JobStatus[] = ['completed', 'failed', 'cancelled'];

export function useJobPolling({
  jobId,
  enabled = true,
  intervalMs = 2500,
  maxAttempts = 60,
  onUpdate,
  onComplete,
  onError,
}: UseJobPollingOptions): UseJobPollingResult {
  const [status, setStatus] = useState<StatusUpdate | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const attemptCountRef = useRef(0);
  const isActiveRef = useRef(true);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const pollStatus = useCallback(async () => {
    if (!jobId || !isActiveRef.current) {
      return;
    }

    try {
      attemptCountRef.current += 1;

      const response = await pollJobStatus(jobId);

      if (!isActiveRef.current) {
        return;
      }

      if (response.data) {
        const statusData = response.data;
        setStatus(statusData);
        setProgress(statusData.progress || 0);
        setError(null);

        if (onUpdate) {
          onUpdate(statusData);
        }

        if (TERMINAL_STATUSES.includes(statusData.status)) {
          stopPolling();

          if (onComplete) {
            onComplete(statusData);
          }

          if (statusData.status === 'failed' && statusData.error && onError) {
            onError(statusData.error);
          }
        }
      } else if (response.error) {
        console.warn(`Polling attempt ${attemptCountRef.current} failed:`, response.error);

        if (attemptCountRef.current >= maxAttempts) {
          const errorMsg = `Failed to get status after ${maxAttempts} attempts`;
          setError(errorMsg);
          stopPolling();

          if (onError) {
            onError(errorMsg);
          }
        }
      }
    } catch (err) {
      console.error('Error polling job status:', err);

      if (attemptCountRef.current >= maxAttempts) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        stopPolling();

        if (onError) {
          onError(errorMsg);
        }
      }
    }
  }, [jobId, maxAttempts, onUpdate, onComplete, onError, stopPolling]);

  const startPolling = useCallback(() => {
    if (!jobId || isPolling) {
      return;
    }

    attemptCountRef.current = 0;
    setError(null);
    setIsPolling(true);

    pollStatus();

    pollIntervalRef.current = setInterval(pollStatus, intervalMs);
  }, [jobId, isPolling, intervalMs, pollStatus]);

  const resetPolling = useCallback(() => {
    stopPolling();
    setStatus(null);
    setError(null);
    setProgress(0);
    attemptCountRef.current = 0;
  }, [stopPolling]);

  useEffect(() => {
    isActiveRef.current = true;

    if (enabled && jobId && !isPolling) {
      startPolling();
    }

    return () => {
      isActiveRef.current = false;
      stopPolling();
    };
  }, [enabled, jobId, startPolling, stopPolling]);

  return {
    status,
    isPolling,
    error,
    progress,
    startPolling,
    stopPolling,
    resetPolling,
  };
}

export function useMultiJobPolling(
  jobIds: string[],
  options: Omit<UseJobPollingOptions, 'jobId'> = {}
): Record<string, UseJobPollingResult> {
  const [results, setResults] = useState<Record<string, UseJobPollingResult>>({});

  useEffect(() => {
    const newResults: Record<string, UseJobPollingResult> = {};

    jobIds.forEach((jobId) => {
      const polling = useJobPolling({
        ...options,
        jobId,
      });
      newResults[jobId] = polling;
    });

    setResults(newResults);
  }, [jobIds, options]);

  return results;
}

export function useJobQueue() {
  const [queue, setQueue] = useState<string[]>([]);
  const [activeJobs, setActiveJobs] = useState<Set<string>>(new Set());
  const [completedJobs, setCompletedJobs] = useState<Set<string>>(new Set());
  const [failedJobs, setFailedJobs] = useState<Set<string>>(new Set());

  const addJob = useCallback((jobId: string) => {
    setQueue((prev) => [...prev, jobId]);
    setActiveJobs((prev) => new Set(prev).add(jobId));
  }, []);

  const markComplete = useCallback((jobId: string) => {
    setActiveJobs((prev) => {
      const next = new Set(prev);
      next.delete(jobId);
      return next;
    });
    setCompletedJobs((prev) => new Set(prev).add(jobId));
  }, []);

  const markFailed = useCallback((jobId: string) => {
    setActiveJobs((prev) => {
      const next = new Set(prev);
      next.delete(jobId);
      return next;
    });
    setFailedJobs((prev) => new Set(prev).add(jobId));
  }, []);

  const clearQueue = useCallback(() => {
    setQueue([]);
    setActiveJobs(new Set());
    setCompletedJobs(new Set());
    setFailedJobs(new Set());
  }, []);

  return {
    queue,
    activeJobs: Array.from(activeJobs),
    completedJobs: Array.from(completedJobs),
    failedJobs: Array.from(failedJobs),
    hasActiveJobs: activeJobs.size > 0,
    addJob,
    markComplete,
    markFailed,
    clearQueue,
  };
}
