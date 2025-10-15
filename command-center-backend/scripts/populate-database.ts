#!/usr/bin/env node
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, BatchWriteCommand } from '@aws-sdk/lib-dynamodb';
import { generateSimulationData } from './generate-simulation-data';
import { EventItem } from '../lib/types/database';

/**
 * Populate DynamoDB with simulation data
 * This script batch-writes events to DynamoDB with progress logging and error handling
 */

// Configuration
const BATCH_SIZE = 25; // DynamoDB BatchWriteItem limit
const RETRY_DELAY_MS = 1000;
const MAX_RETRIES = 3;

/**
 * Validate event data before insertion
 */
function validateEvent(event: EventItem): boolean {
  if (!event.Day || !event.Timestamp || !event.eventId) {
    console.error(`Invalid event: missing required fields`, event);
    return false;
  }
  
  if (!event.Day.match(/^DAY_[0-6]$/)) {
    console.error(`Invalid Day format: ${event.Day}`);
    return false;
  }
  
  const validDomains = ['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION'];
  if (!validDomains.includes(event.domain)) {
    console.error(`Invalid domain: ${event.domain}`);
    return false;
  }
  
  const validSeverities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  if (!validSeverities.includes(event.severity)) {
    console.error(`Invalid severity: ${event.severity}`);
    return false;
  }
  
  try {
    JSON.parse(event.geojson);
  } catch (e) {
    console.error(`Invalid GeoJSON: ${event.geojson}`);
    return false;
  }
  
  return true;
}

/**
 * Split array into chunks
 */
function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Batch write events to DynamoDB with retry logic
 */
async function batchWriteWithRetry(
  docClient: DynamoDBDocumentClient,
  tableName: string,
  items: EventItem[],
  retryCount: number = 0
): Promise<void> {
  const putRequests = items.map(item => ({
    PutRequest: { Item: item }
  }));
  
  try {
    const command = new BatchWriteCommand({
      RequestItems: {
        [tableName]: putRequests
      }
    });
    
    const response = await docClient.send(command);
    
    // Handle unprocessed items
    if (response.UnprocessedItems && response.UnprocessedItems[tableName]) {
      const unprocessedCount = response.UnprocessedItems[tableName].length;
      console.warn(`  ${unprocessedCount} unprocessed items, retrying...`);
      
      if (retryCount < MAX_RETRIES) {
        await sleep(RETRY_DELAY_MS * (retryCount + 1)); // Exponential backoff
        const unprocessedItems = response.UnprocessedItems[tableName].map(
          req => req.PutRequest!.Item as EventItem
        );
        await batchWriteWithRetry(docClient, tableName, unprocessedItems, retryCount + 1);
      } else {
        throw new Error(`Failed to write ${unprocessedCount} items after ${MAX_RETRIES} retries`);
      }
    }
  } catch (error) {
    if (retryCount < MAX_RETRIES) {
      console.warn(`  Batch write failed, retrying (attempt ${retryCount + 1}/${MAX_RETRIES})...`);
      await sleep(RETRY_DELAY_MS * (retryCount + 1));
      await batchWriteWithRetry(docClient, tableName, items, retryCount + 1);
    } else {
      throw error;
    }
  }
}

/**
 * Main population function
 */
async function populateDatabase() {
  // Get table name from environment or use default
  const tableName = process.env.TABLE_NAME || 'MasterEventTimeline';
  const region = process.env.AWS_REGION || 'us-east-1';
  
  console.log('='.repeat(60));
  console.log('Command Center Backend - Database Population');
  console.log('='.repeat(60));
  console.log(`Table: ${tableName}`);
  console.log(`Region: ${region}`);
  console.log('');
  
  // Initialize DynamoDB client
  const client = new DynamoDBClient({ region });
  const docClient = DynamoDBDocumentClient.from(client, {
    marshallOptions: {
      removeUndefinedValues: true,
      convertClassInstanceToMap: true
    }
  });
  
  try {
    // Generate simulation data
    console.log('Step 1: Generating simulation data...');
    const events = generateSimulationData();
    console.log(`✓ Generated ${events.length} events\n`);
    
    // Validate all events
    console.log('Step 2: Validating events...');
    const validEvents = events.filter(validateEvent);
    const invalidCount = events.length - validEvents.length;
    
    if (invalidCount > 0) {
      console.warn(`⚠ ${invalidCount} invalid events skipped`);
    }
    console.log(`✓ ${validEvents.length} valid events\n`);
    
    if (validEvents.length === 0) {
      throw new Error('No valid events to insert');
    }
    
    // Partition events by day for progress tracking
    const eventsByDay: { [key: string]: EventItem[] } = {};
    validEvents.forEach(event => {
      if (!eventsByDay[event.Day]) {
        eventsByDay[event.Day] = [];
      }
      eventsByDay[event.Day].push(event);
    });
    
    console.log('Step 3: Writing events to DynamoDB...');
    console.log(`Batch size: ${BATCH_SIZE} items per batch\n`);
    
    let totalWritten = 0;
    const startTime = Date.now();
    
    // Process each day
    for (let day = 0; day <= 6; day++) {
      const dayKey = `DAY_${day}`;
      const dayEvents = eventsByDay[dayKey] || [];
      
      if (dayEvents.length === 0) {
        console.log(`${dayKey}: No events`);
        continue;
      }
      
      console.log(`${dayKey}: Writing ${dayEvents.length} events...`);
      
      // Split into batches
      const batches = chunkArray(dayEvents, BATCH_SIZE);
      
      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        process.stdout.write(`  Batch ${i + 1}/${batches.length} (${batch.length} items)... `);
        
        try {
          await batchWriteWithRetry(docClient, tableName, batch);
          totalWritten += batch.length;
          console.log('✓');
        } catch (error) {
          console.log('✗');
          throw error;
        }
        
        // Small delay between batches to avoid throttling
        if (i < batches.length - 1) {
          await sleep(100);
        }
      }
      
      console.log(`  ✓ ${dayEvents.length} events written\n`);
    }
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    
    console.log('='.repeat(60));
    console.log('Population Complete!');
    console.log('='.repeat(60));
    console.log(`Total events written: ${totalWritten}`);
    console.log(`Duration: ${duration}s`);
    console.log(`Average: ${(totalWritten / parseFloat(duration)).toFixed(1)} events/sec`);
    console.log('');
    
    // Summary by domain
    console.log('Events by domain:');
    const domains = ['MEDICAL', 'FIRE', 'STRUCTURAL', 'LOGISTICS', 'COMMUNICATION'];
    domains.forEach(domain => {
      const count = validEvents.filter(e => e.domain === domain).length;
      console.log(`  ${domain.padEnd(15)}: ${count}`);
    });
    
    console.log('');
    console.log('Events by day:');
    for (let day = 0; day <= 6; day++) {
      const dayKey = `DAY_${day}`;
      const count = eventsByDay[dayKey]?.length || 0;
      console.log(`  ${dayKey}: ${count}`);
    }
    
  } catch (error) {
    console.error('\n❌ Error during population:');
    console.error(error);
    process.exit(1);
  } finally {
    client.destroy();
  }
}

// Run if executed directly
if (require.main === module) {
  populateDatabase()
    .then(() => {
      console.log('\n✓ Database population successful');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n✗ Database population failed:', error);
      process.exit(1);
    });
}

export { populateDatabase };
