import { queryEventsWithFilters } from './query-functions';
import { EventItem } from '../types/database';

/**
 * Query database for events - used by AI agent tool
 * 
 * @param params - Query parameters
 * @returns Query results with events
 */
export async function queryDatabase(params: {
  tableName: string;
  domain?: string;
  severity?: string;
  startTime?: string;
  endTime?: string;
  limit?: number;
}): Promise<{
  events: EventItem[];
  count: number;
  filters: any;
}> {
  console.log('Database query tool invoked', {
    domain: params.domain,
    severity: params.severity,
    hasTimeRange: !!(params.startTime || params.endTime),
    limit: params.limit,
  });

  // Set table name for the query functions
  process.env.TABLE_NAME = params.tableName;

  // Query events with filters
  const events = await queryEventsWithFilters({
    domain: params.domain,
    severity: params.severity,
    startTime: params.startTime,
    endTime: params.endTime,
    limit: params.limit || 100,
  });

  console.log('Database query completed', {
    eventCount: events.length,
  });

  return {
    events,
    count: events.length,
    filters: {
      domain: params.domain,
      severity: params.severity,
      startTime: params.startTime,
      endTime: params.endTime,
      limit: params.limit,
    },
  };
}
