import { ToolInputSchema, ToolOutput, RawEvent, ErrorResponse } from '../types/api';
import { queryEventsWithFilters } from '../data-access/query-functions';
import { EventItem } from '../types/database';

/**
 * Calculate distance between two coordinates using Haversine formula
 * 
 * @param lat1 - Latitude of first point
 * @param lon1 - Longitude of first point
 * @param lat2 - Latitude of second point
 * @param lon2 - Longitude of second point
 * @returns Distance in kilometers
 */
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in kilometers
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return distance;
}

/**
 * Extract coordinates from GeoJSON string
 * Handles Point, Polygon, and LineString geometries
 * 
 * @param geojsonStr - Stringified GeoJSON
 * @returns Coordinates [lon, lat] or null if invalid
 */
function extractCoordinates(geojsonStr: string): [number, number] | null {
  try {
    const geojson = JSON.parse(geojsonStr);
    
    if (!geojson || !geojson.type || !geojson.coordinates) {
      return null;
    }
    
    // Handle different geometry types
    switch (geojson.type) {
      case 'Point':
        // Point: [lon, lat]
        return geojson.coordinates as [number, number];
      
      case 'Polygon':
        // Polygon: [[[lon, lat], ...]]
        // Use first coordinate of outer ring
        if (Array.isArray(geojson.coordinates[0]) && geojson.coordinates[0].length > 0) {
          return geojson.coordinates[0][0] as [number, number];
        }
        return null;
      
      case 'LineString':
        // LineString: [[lon, lat], ...]
        // Use first coordinate
        if (Array.isArray(geojson.coordinates) && geojson.coordinates.length > 0) {
          return geojson.coordinates[0] as [number, number];
        }
        return null;
      
      default:
        return null;
    }
  } catch (error) {
    console.error('Failed to parse GeoJSON', { geojsonStr, error });
    return null;
  }
}

/**
 * Filter events by location proximity
 * 
 * @param events - Array of EventItem records
 * @param targetLat - Target latitude
 * @param targetLon - Target longitude
 * @param radiusKm - Radius in kilometers
 * @returns Filtered array of events within radius
 */
function filterByLocation(
  events: EventItem[],
  targetLat: number,
  targetLon: number,
  radiusKm: number
): EventItem[] {
  return events.filter(event => {
    const coords = extractCoordinates(event.geojson);
    
    if (!coords) {
      return false;
    }
    
    const [lon, lat] = coords;
    const distance = calculateDistance(targetLat, targetLon, lat, lon);
    
    return distance <= radiusKm;
  });
}

/**
 * Transform EventItem to RawEvent for tool output
 * 
 * @param event - EventItem from DynamoDB
 * @returns RawEvent for agent consumption
 */
function transformToRawEvent(event: EventItem): RawEvent {
  return {
    eventId: event.eventId,
    timestamp: event.Timestamp,
    domain: event.domain,
    severity: event.severity,
    geojson: event.geojson,
    summary: event.summary,
    details: event.details,
    resourcesNeeded: event.resourcesNeeded,
    contactInfo: event.contactInfo,
  };
}

/**
 * Lambda handler for databaseQueryTool (Bedrock Agent Action Group)
 * 
 * This Lambda is invoked by the Bedrock Agent when it needs to query the database.
 * It accepts structured parameters and returns raw event data.
 * 
 * @param event - Bedrock Agent event containing tool input
 * @returns Tool output with events and count
 */
export async function handler(event: any): Promise<any> {
  console.log('Database query tool invoked', {
    event: JSON.stringify(event, null, 2),
  });

  try {
    // Extract parameters from Bedrock Agent event
    // Bedrock sends the input in event.parameters or event.requestBody.content.application/json
    let toolInput: any;
    
    if (event.parameters) {
      // Parameters come as an array of {name, value} objects
      toolInput = event.parameters.reduce((acc: any, param: any) => {
        acc[param.name] = param.value;
        return acc;
      }, {});
    } else if (event.requestBody?.content?.['application/json']) {
      toolInput = JSON.parse(event.requestBody.content['application/json']);
    } else if (event.inputText) {
      // Fallback: try to parse inputText as JSON
      toolInput = JSON.parse(event.inputText);
    } else {
      throw new Error('Unable to extract tool input from event');
    }

    console.log('Extracted tool input', { toolInput });

    // Validate tool input using Zod schema
    const validationResult = ToolInputSchema.safeParse(toolInput);
    
    if (!validationResult.success) {
      console.error('Tool input validation failed', {
        errors: validationResult.error.issues,
        toolInput,
      });
      
      return {
        error: {
          code: 'INVALID_PARAMETERS',
          message: 'Invalid tool parameters',
          details: validationResult.error.issues,
        },
      };
    }

    const { domain, severity, startTime, endTime, location, limit } = validationResult.data;

    console.log('Tool input validated', {
      domain,
      severity,
      startTime,
      endTime,
      location,
      limit,
    });

    // Query DynamoDB with filters
    const queryStartTime = Date.now();
    let events = await queryEventsWithFilters({
      domain,
      severity,
      startTime,
      endTime,
      limit: limit || 100, // Default limit to prevent large responses
    });
    const queryDuration = Date.now() - queryStartTime;

    console.log('DynamoDB query completed', {
      eventCount: events.length,
      queryDuration,
    });

    // Apply location-based filtering if specified
    if (location) {
      const filterStartTime = Date.now();
      const radiusKm = location.radiusKm || 10; // Default 10km radius
      events = filterByLocation(events, location.lat, location.lon, radiusKm);
      const filterDuration = Date.now() - filterStartTime;
      
      console.log('Location filtering completed', {
        filteredCount: events.length,
        filterDuration,
        location,
        radiusKm,
      });
    }

    // Apply limit if specified and not already applied in query
    if (limit && events.length > limit) {
      events = events.slice(0, limit);
    }

    // Transform to raw events for agent
    const rawEvents = events.map(transformToRawEvent);

    // Build tool output
    const toolOutput: ToolOutput = {
      events: rawEvents,
      count: rawEvents.length,
    };

    console.log('Tool execution completed successfully', {
      eventCount: toolOutput.count,
    });

    return toolOutput;

  } catch (error) {
    console.error('Error in database query tool', {
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      event: JSON.stringify(event, null, 2),
    });

    // Return structured error for agent
    return {
      error: {
        code: 'TOOL_EXECUTION_ERROR',
        message: error instanceof Error ? error.message : 'An unexpected error occurred',
        details: {
          errorType: error instanceof Error ? error.constructor.name : typeof error,
        },
      },
    };
  }
}
