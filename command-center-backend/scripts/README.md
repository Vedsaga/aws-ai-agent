# Data Population Scripts

This directory contains scripts for generating and populating simulation data for the Command Center Backend.

## Scripts

### 1. generate-simulation-data.ts

Generates realistic 7-day earthquake response simulation data with:
- **420 total events** across 7 days (DAY_0 through DAY_6)
- **5 domains**: MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION
- **4 severity levels**: CRITICAL, HIGH, MEDIUM, LOW
- **GeoJSON geometries**: Points and Polygons for map visualization
- **Realistic timestamps**: Distributed throughout each day
- **Turkish earthquake context**: Events centered around affected cities (Kahramanmaraş, Gaziantep, Hatay, etc.)

**Event Distribution:**
- Day 0 (Earthquake day): 75 events (15 per domain)
- Day 1: 60 events (12 per domain)
- Day 2: 50 events (10 per domain)
- Day 3: 40 events (8 per domain)
- Day 4: 30 events (6 per domain)
- Day 5: 25 events (5 per domain)
- Day 6: 20 events (4 per domain)

**Usage:**
```bash
# Generate and display sample data
npm run generate-data

# Or use directly
ts-node scripts/generate-simulation-data.ts
```

### 2. populate-database.ts

Populates DynamoDB with the generated simulation data using batch write operations.

**Features:**
- **Batch writing**: Uses DynamoDB BatchWriteItem (25 items per batch)
- **Data validation**: Validates all events before insertion
- **Retry logic**: Automatic retry with exponential backoff for failed writes
- **Progress logging**: Real-time progress updates during population
- **Error handling**: Comprehensive error handling and reporting
- **Partitioning**: Events partitioned by day (DAY_0 through DAY_6)

**Prerequisites:**
- AWS credentials configured (via environment variables or AWS CLI)
- DynamoDB table created (via CDK deployment)
- Appropriate IAM permissions for DynamoDB write operations

**Environment Variables:**
- `TABLE_NAME`: DynamoDB table name (default: "MasterEventTimeline")
- `AWS_REGION`: AWS region (default: "us-east-1")

**Usage:**
```bash
# Populate database
npm run populate-db

# Or use directly with custom table name
TABLE_NAME=MyCustomTable AWS_REGION=us-west-2 ts-node scripts/populate-database.ts
```

**Output Example:**
```
============================================================
Command Center Backend - Database Population
============================================================
Table: MasterEventTimeline
Region: us-east-1

Step 1: Generating simulation data...
Generated 420 events across 7 days
Events per domain:
  MEDICAL: 84
  FIRE: 84
  STRUCTURAL: 84
  LOGISTICS: 84
  COMMUNICATION: 84
✓ Generated 420 events

Step 2: Validating events...
✓ 420 valid events

Step 3: Writing events to DynamoDB...
Batch size: 25 items per batch

DAY_0: Writing 75 events...
  Batch 1/3 (25 items)... ✓
  Batch 2/3 (25 items)... ✓
  Batch 3/3 (25 items)... ✓
  ✓ 75 events written

[... continues for all days ...]

============================================================
Population Complete!
============================================================
Total events written: 420
Duration: 12.34s
Average: 34.0 events/sec

Events by domain:
  MEDICAL        : 84
  FIRE           : 84
  STRUCTURAL     : 84
  LOGISTICS      : 84
  COMMUNICATION  : 84

Events by day:
  DAY_0: 75
  DAY_1: 60
  DAY_2: 50
  DAY_3: 40
  DAY_4: 30
  DAY_5: 25
  DAY_6: 20
```

## Data Model

Each event follows the `EventItem` interface:

```typescript
interface EventItem {
  Day: string;                    // PK: DAY_0 to DAY_6
  Timestamp: string;              // SK: ISO 8601 timestamp
  eventId: string;                // UUID
  domain: string;                 // MEDICAL | FIRE | STRUCTURAL | LOGISTICS | COMMUNICATION
  severity: string;               // CRITICAL | HIGH | MEDIUM | LOW
  geojson: string;                // Stringified GeoJSON (Point or Polygon)
  summary: string;                // Brief description
  details?: string;               // Optional: full details
  resourcesNeeded?: string[];     // Optional: list of resources
  contactInfo?: string;           // Optional: contact information
}
```

## Workflow

1. **Deploy Infrastructure**: Deploy the CDK stack to create the DynamoDB table
   ```bash
   npm run deploy
   ```

2. **Populate Database**: Run the population script to insert simulation data
   ```bash
   npm run populate-db
   ```

3. **Verify**: Check DynamoDB console or query the table to verify data

## Error Handling

The population script includes comprehensive error handling:

- **Validation errors**: Invalid events are skipped and logged
- **Write failures**: Automatic retry with exponential backoff (up to 3 retries)
- **Unprocessed items**: Automatically retried with backoff
- **Network errors**: Graceful failure with detailed error messages

## Performance

- **Batch size**: 25 items per batch (DynamoDB limit)
- **Throttling protection**: Small delays between batches
- **Retry strategy**: Exponential backoff (1s, 2s, 3s)
- **Expected duration**: ~10-15 seconds for 420 events

## Troubleshooting

**Issue**: "Table not found" error
- **Solution**: Ensure the CDK stack is deployed and the table exists

**Issue**: "Access denied" error
- **Solution**: Check AWS credentials and IAM permissions

**Issue**: "Throttling" errors
- **Solution**: The script automatically retries with backoff. If persistent, check DynamoDB capacity settings.

**Issue**: No output when running scripts
- **Solution**: Ensure scripts are compiled first with `npm run build`
