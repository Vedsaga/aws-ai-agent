import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

/**
 * Singleton DynamoDB client with connection reuse
 * This is important for Lambda performance - reusing connections across invocations
 */
let documentClient: DynamoDBDocumentClient | null = null;

/**
 * Get or create DynamoDB Document Client
 * Uses singleton pattern to reuse connections across Lambda invocations
 */
export function getDynamoDBClient(): DynamoDBDocumentClient {
  if (!documentClient) {
    const client = new DynamoDBClient({
      region: process.env.AWS_REGION || 'us-east-1',
    });

    documentClient = DynamoDBDocumentClient.from(client, {
      marshallOptions: {
        removeUndefinedValues: true,
        convertClassInstanceToMap: true,
      },
      unmarshallOptions: {
        wrapNumbers: false,
      },
    });
  }

  return documentClient;
}

/**
 * Get table name from environment variable
 */
export function getTableName(): string {
  const tableName = process.env.TABLE_NAME;
  if (!tableName) {
    throw new Error('TABLE_NAME environment variable is not set');
  }
  return tableName;
}
