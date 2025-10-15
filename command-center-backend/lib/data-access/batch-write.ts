import { BatchWriteCommand, BatchWriteCommandInput } from '@aws-sdk/lib-dynamodb';
import { getDynamoDBClient, getTableName } from './dynamodb-client';
import { EventItem } from '../types/database';

/**
 * Batch write events to DynamoDB
 * DynamoDB allows max 25 items per batch, so we chunk the items
 * 
 * @param events - Array of EventItem records to write
 * @returns Number of items successfully written
 */
export async function batchWriteEvents(events: EventItem[]): Promise<number> {
  const client = getDynamoDBClient();
  const tableName = getTableName();

  // Chunk events into batches of 25 (DynamoDB limit)
  const chunks = chunkArray(events, 25);
  let totalWritten = 0;

  for (const chunk of chunks) {
    const params: BatchWriteCommandInput = {
      RequestItems: {
        [tableName]: chunk.map(event => ({
          PutRequest: {
            Item: event,
          },
        })),
      },
    };

    const command = new BatchWriteCommand(params);
    const response = await client.send(command);

    // Handle unprocessed items
    if (response.UnprocessedItems && Object.keys(response.UnprocessedItems).length > 0) {
      console.warn(`Unprocessed items in batch write:`, response.UnprocessedItems);
      // In production, you might want to retry unprocessed items
    }

    totalWritten += chunk.length;
  }

  return totalWritten;
}

/**
 * Chunk an array into smaller arrays of specified size
 * 
 * @param array - Array to chunk
 * @param size - Size of each chunk
 * @returns Array of chunks
 */
function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

/**
 * Validate event item before writing
 * 
 * @param event - EventItem to validate
 * @returns true if valid, throws error if invalid
 */
export function validateEventItem(event: EventItem): boolean {
  if (!event.Day || !event.Timestamp || !event.eventId) {
    throw new Error('EventItem must have Day, Timestamp, and eventId');
  }

  if (!event.domain || !event.severity || !event.geojson || !event.summary) {
    throw new Error('EventItem must have domain, severity, geojson, and summary');
  }

  // Validate domain
  const validDomains = ['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION'];
  if (!validDomains.includes(event.domain)) {
    throw new Error(`Invalid domain: ${event.domain}`);
  }

  // Validate severity
  const validSeverities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  if (!validSeverities.includes(event.severity)) {
    throw new Error(`Invalid severity: ${event.severity}`);
  }

  // Validate geojson is valid JSON
  try {
    JSON.parse(event.geojson);
  } catch (error) {
    throw new Error('Invalid GeoJSON format');
  }

  return true;
}
