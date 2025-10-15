import { QueryCommand, QueryCommandInput } from '@aws-sdk/lib-dynamodb';
import { getDynamoDBClient, getTableName } from './dynamodb-client';
import { EventItem } from '../types/database';

/**
 * Query events by time range for a specific day
 * 
 * @param day - Day partition key (e.g., "DAY_0", "DAY_1")
 * @param sinceTimestamp - ISO 8601 timestamp to filter events after
 * @returns Array of EventItem records
 */
export async function queryEventsByTimeRange(
  day: string,
  sinceTimestamp: string
): Promise<EventItem[]> {
  try {
    const client = getDynamoDBClient();
    const tableName = getTableName();

    const params: QueryCommandInput = {
      TableName: tableName,
      KeyConditionExpression: '#day = :day AND #timestamp > :since',
      ExpressionAttributeNames: {
        '#day': 'Day',
        '#timestamp': 'Timestamp',
      },
      ExpressionAttributeValues: {
        ':day': day,
        ':since': sinceTimestamp,
      },
    };

    console.log('Querying events by time range', { day, sinceTimestamp });

    const command = new QueryCommand(params);
    const response = await client.send(command);

    console.log('Query completed', {
      day,
      itemCount: response.Items?.length || 0,
      consumedCapacity: response.ConsumedCapacity,
    });

    return (response.Items || []) as EventItem[];
  } catch (error) {
    console.error('Error querying events by time range', {
      day,
      sinceTimestamp,
      error: error instanceof Error ? error.message : String(error),
    });
    throw new Error(`Failed to query events for ${day}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Query events by domain and time range using GSI
 * 
 * @param domain - Domain filter (MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION)
 * @param sinceTimestamp - ISO 8601 timestamp to filter events after
 * @returns Array of EventItem records
 */
export async function queryEventsByDomain(
  domain: string,
  sinceTimestamp: string
): Promise<EventItem[]> {
  try {
    const client = getDynamoDBClient();
    const tableName = getTableName();

    const params: QueryCommandInput = {
      TableName: tableName,
      IndexName: 'domain-timestamp-index',
      KeyConditionExpression: '#domain = :domain AND #timestamp > :since',
      ExpressionAttributeNames: {
        '#domain': 'domain',
        '#timestamp': 'Timestamp',
      },
      ExpressionAttributeValues: {
        ':domain': domain,
        ':since': sinceTimestamp,
      },
    };

    console.log('Querying events by domain', { domain, sinceTimestamp });

    const command = new QueryCommand(params);
    const response = await client.send(command);

    console.log('Query completed', {
      domain,
      itemCount: response.Items?.length || 0,
      consumedCapacity: response.ConsumedCapacity,
    });

    return (response.Items || []) as EventItem[];
  } catch (error) {
    console.error('Error querying events by domain', {
      domain,
      sinceTimestamp,
      error: error instanceof Error ? error.message : String(error),
    });
    throw new Error(`Failed to query events for domain ${domain}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Query events with multiple filters
 * 
 * @param options - Query options
 * @returns Array of EventItem records
 */
export async function queryEventsWithFilters(options: {
  domain?: string;
  severity?: string;
  startTime?: string;
  endTime?: string;
  limit?: number;
}): Promise<EventItem[]> {
  const client = getDynamoDBClient();
  const tableName = getTableName();

  // If domain is specified, use GSI
  if (options.domain) {
    let keyConditionExpression = '#domain = :domain';
    const expressionAttributeNames: Record<string, string> = {
      '#domain': 'domain',
    };
    const expressionAttributeValues: Record<string, any> = {
      ':domain': options.domain,
    };

    // Add time range conditions
    if (options.startTime && options.endTime) {
      keyConditionExpression += ' AND #timestamp BETWEEN :start AND :end';
      expressionAttributeNames['#timestamp'] = 'Timestamp';
      expressionAttributeValues[':start'] = options.startTime;
      expressionAttributeValues[':end'] = options.endTime;
    } else if (options.startTime) {
      keyConditionExpression += ' AND #timestamp >= :start';
      expressionAttributeNames['#timestamp'] = 'Timestamp';
      expressionAttributeValues[':start'] = options.startTime;
    } else if (options.endTime) {
      keyConditionExpression += ' AND #timestamp <= :end';
      expressionAttributeNames['#timestamp'] = 'Timestamp';
      expressionAttributeValues[':end'] = options.endTime;
    }

    // Add severity filter if specified
    let filterExpression: string | undefined;
    if (options.severity) {
      filterExpression = '#severity = :severity';
      expressionAttributeNames['#severity'] = 'severity';
      expressionAttributeValues[':severity'] = options.severity;
    }

    const params: QueryCommandInput = {
      TableName: tableName,
      IndexName: 'domain-timestamp-index',
      KeyConditionExpression: keyConditionExpression,
      FilterExpression: filterExpression,
      ExpressionAttributeNames: expressionAttributeNames,
      ExpressionAttributeValues: expressionAttributeValues,
      Limit: options.limit,
    };

    const command = new QueryCommand(params);
    const response = await client.send(command);

    return (response.Items || []) as EventItem[];
  }

  // If no domain specified, query across all days with time range and severity filters
  const allEvents: EventItem[] = [];
  
  // Determine which days to query based on time range
  let startDay = 0;
  let endDay = 6;
  
  if (options.startTime) {
    const startDayNum = parseInt(getDayFromTimestamp(options.startTime).split('_')[1]);
    if (startDayNum >= 0 && startDayNum <= 6) {
      startDay = startDayNum;
    }
  }
  
  if (options.endTime) {
    const endDayNum = parseInt(getDayFromTimestamp(options.endTime).split('_')[1]);
    if (endDayNum >= 0 && endDayNum <= 6) {
      endDay = endDayNum;
    }
  }
  
  // Query each day
  for (let i = startDay; i <= endDay; i++) {
    const dayKey = `DAY_${i}`;
    
    try {
      let keyConditionExpression = '#day = :day';
      const expressionAttributeNames: Record<string, string> = {
        '#day': 'Day',
      };
      const expressionAttributeValues: Record<string, any> = {
        ':day': dayKey,
      };
      
      // Add time range conditions
      if (options.startTime && options.endTime) {
        keyConditionExpression += ' AND #timestamp BETWEEN :start AND :end';
        expressionAttributeNames['#timestamp'] = 'Timestamp';
        expressionAttributeValues[':start'] = options.startTime;
        expressionAttributeValues[':end'] = options.endTime;
      } else if (options.startTime) {
        keyConditionExpression += ' AND #timestamp >= :start';
        expressionAttributeNames['#timestamp'] = 'Timestamp';
        expressionAttributeValues[':start'] = options.startTime;
      } else if (options.endTime) {
        keyConditionExpression += ' AND #timestamp <= :end';
        expressionAttributeNames['#timestamp'] = 'Timestamp';
        expressionAttributeValues[':end'] = options.endTime;
      }
      
      // Add severity filter if specified
      let filterExpression: string | undefined;
      if (options.severity) {
        filterExpression = '#severity = :severity';
        expressionAttributeNames['#severity'] = 'severity';
        expressionAttributeValues[':severity'] = options.severity;
      }
      
      const params: QueryCommandInput = {
        TableName: tableName,
        KeyConditionExpression: keyConditionExpression,
        FilterExpression: filterExpression,
        ExpressionAttributeNames: expressionAttributeNames,
        ExpressionAttributeValues: expressionAttributeValues,
      };
      
      const command = new QueryCommand(params);
      const response = await client.send(command);
      
      if (response.Items) {
        allEvents.push(...(response.Items as EventItem[]));
      }
      
      // Check if we've reached the limit
      if (options.limit && allEvents.length >= options.limit) {
        break;
      }
    } catch (error) {
      console.error(`Failed to query ${dayKey}`, {
        error: error instanceof Error ? error.message : String(error),
      });
      // Continue with other days
    }
  }
  
  // Sort by timestamp
  allEvents.sort((a, b) => a.Timestamp.localeCompare(b.Timestamp));
  
  // Apply limit if specified
  if (options.limit && allEvents.length > options.limit) {
    return allEvents.slice(0, options.limit);
  }
  
  return allEvents;
}

/**
 * Get the day partition key from a timestamp
 * Assumes simulation starts on Day 0 (2023-02-06)
 * 
 * @param timestamp - ISO 8601 timestamp
 * @returns Day partition key (e.g., "DAY_0")
 */
export function getDayFromTimestamp(timestamp: string): string {
  const simulationStart = new Date('2023-02-06T00:00:00Z');
  const eventDate = new Date(timestamp);
  
  const daysDiff = Math.floor(
    (eventDate.getTime() - simulationStart.getTime()) / (1000 * 60 * 60 * 24)
  );
  
  return `DAY_${daysDiff}`;
}

/**
 * Query events across multiple days
 * 
 * @param sinceTimestamp - ISO 8601 timestamp to filter events after
 * @param domain - Optional domain filter
 * @returns Array of EventItem records
 */
export async function queryEventsSince(
  sinceTimestamp: string,
  domain?: string
): Promise<EventItem[]> {
  try {
    console.log('Querying events since timestamp', { sinceTimestamp, domain });

    // If domain is specified, use the GSI query
    if (domain) {
      return queryEventsByDomain(domain, sinceTimestamp);
    }

    // Otherwise, determine which days to query
    const startDay = getDayFromTimestamp(sinceTimestamp);
    const startDayNum = parseInt(startDay.split('_')[1]);
    
    // Validate day number is within range
    if (startDayNum < 0 || startDayNum > 6) {
      console.warn('Timestamp outside simulation range', { sinceTimestamp, startDayNum });
      return [];
    }
    
    // Query from the start day to DAY_6
    const allEvents: EventItem[] = [];
    for (let i = startDayNum; i <= 6; i++) {
      const dayKey = `DAY_${i}`;
      try {
        const events = await queryEventsByTimeRange(dayKey, sinceTimestamp);
        allEvents.push(...events);
      } catch (error) {
        // Log error but continue with other days
        console.error(`Failed to query ${dayKey}, continuing with other days`, {
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    // Sort by timestamp
    allEvents.sort((a, b) => a.Timestamp.localeCompare(b.Timestamp));

    console.log('Query events since completed', {
      totalEvents: allEvents.length,
      daysQueried: 6 - startDayNum + 1,
    });

    return allEvents;
  } catch (error) {
    console.error('Error in queryEventsSince', {
      sinceTimestamp,
      domain,
      error: error instanceof Error ? error.message : String(error),
    });
    throw new Error(`Failed to query events: ${error instanceof Error ? error.message : String(error)}`);
  }
}
