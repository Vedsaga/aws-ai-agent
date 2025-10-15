import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { UpdatesRequestSchema, UpdatesResponse, ErrorResponse } from '../types/api';
import { queryEventsSince } from '../data-access/query-functions';
import { transformToUpdatesResponse } from '../data-access/transformers';

/**
 * Lambda handler for GET /data/updates
 * 
 * Retrieves event updates based on time and optional domain filters
 * Returns lean JSON structure with map layers and critical alerts
 * 
 * Query Parameters:
 * - since (required): ISO 8601 timestamp
 * - domain (optional): MEDICAL | FIRE | STRUCTURAL | LOGISTICS | COMMUNICATION
 */
export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  console.log('Updates handler invoked', {
    queryStringParameters: event.queryStringParameters,
    requestId: event.requestContext.requestId,
  });

  try {
    // Parse and validate query parameters
    const queryParams = event.queryStringParameters || {};
    
    // Validate using Zod schema
    const validationResult = UpdatesRequestSchema.safeParse(queryParams);
    
    if (!validationResult.success) {
      console.error('Validation failed', {
        errors: validationResult.error.issues,
        queryParams,
      });
      
      const errorResponse: ErrorResponse = {
        error: {
          code: 'INVALID_REQUEST',
          message: 'Invalid query parameters',
          details: validationResult.error.issues,
        },
      };
      
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify(errorResponse),
      };
    }

    const { since, domain } = validationResult.data;

    console.log('Query parameters validated', { since, domain });

    // Query DynamoDB with since timestamp and optional domain filter
    const startTime = Date.now();
    const events = await queryEventsSince(since, domain);
    const queryDuration = Date.now() - startTime;

    console.log('DynamoDB query completed', {
      eventCount: events.length,
      queryDuration,
      domain: domain || 'all',
    });

    // Transform database results to API response format
    const transformStartTime = Date.now();
    const { latestTimestamp, mapLayers, criticalAlerts } = transformToUpdatesResponse(events);
    const transformDuration = Date.now() - transformStartTime;

    console.log('Response transformation completed', {
      transformDuration,
      layerCount: mapLayers.length,
      alertCount: criticalAlerts.length,
    });

    // Build response
    const response: UpdatesResponse = {
      latestTimestamp,
    };

    // Only include mapUpdates if there are events
    if (mapLayers.length > 0) {
      response.mapUpdates = {
        mapAction: 'APPEND',
        mapLayers,
      };
    }

    // Only include criticalAlerts if there are any
    if (criticalAlerts.length > 0) {
      response.criticalAlerts = criticalAlerts;
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(response),
    };

  } catch (error) {
    console.error('Error processing updates request', {
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      queryParams: event.queryStringParameters,
    });

    // Determine error type and appropriate response
    let statusCode = 500;
    let errorCode = 'INTERNAL_ERROR';
    let errorMessage = 'An unexpected error occurred while processing the request';

    if (error instanceof Error) {
      // Check for specific error types
      if (error.message.includes('TABLE_NAME')) {
        errorCode = 'CONFIGURATION_ERROR';
        errorMessage = 'Database configuration error';
      } else if (error.message.includes('Failed to query')) {
        errorCode = 'DATABASE_ERROR';
        errorMessage = 'Failed to retrieve data from database';
      } else if (error.message.includes('timeout')) {
        statusCode = 504;
        errorCode = 'TIMEOUT_ERROR';
        errorMessage = 'Request timed out';
      }
    }

    const errorResponse: ErrorResponse = {
      error: {
        code: errorCode,
        message: errorMessage,
      },
    };

    return {
      statusCode,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(errorResponse),
    };
  }
}
