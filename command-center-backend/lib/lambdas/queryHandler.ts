import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import {
  BedrockRuntimeClient,
  ConverseCommand,
  ConverseCommandInput,
  Tool,
  ToolResultBlock,
} from '@aws-sdk/client-bedrock-runtime';
import { QueryRequestSchema, QueryResponse, ErrorResponse } from '../types/api';
import { queryDatabase } from '../data-access/database-query';

// Initialize Bedrock Runtime client for direct model invocation
const bedrockClient = new BedrockRuntimeClient({
  region: process.env.AWS_REGION || 'us-east-1',
});

// Environment variables
const BEDROCK_MODEL = process.env.BEDROCK_MODEL || 'amazon.nova-pro-v1:0';
const TABLE_NAME = process.env.TABLE_NAME;
const LOG_LEVEL = process.env.LOG_LEVEL || 'INFO';

// System prompt for the AI agent
const SYSTEM_PROMPT = `You are an AI assistant for a disaster response Command Center. Your role is to help operators understand the current situation by answering questions about incidents, resources, and response activities during the 2023 Turkey earthquake response simulation.

You have access to a database of events from a 7-day earthquake response simulation. Use the queryDatabase tool to retrieve relevant data when needed.

When answering questions:
1. Be concise and factual
2. Include specific numbers and locations when available
3. Highlight critical or urgent situations
4. Autonomously control the map visualization - decide optimal zoom levels, generate density polygons, and center the map to best answer the query
5. If the data doesn't exist or you're unsure, say so clearly

Your response should be in JSON format with:
- chatResponse: Your natural language answer
- mapAction: "REPLACE" (clear existing layers) or "APPEND" (add to existing)
- mapLayers: Array of GeoJSON layers with styling (Points, Polygons, LineStrings)
- viewState: Map bounds or center/zoom to focus on relevant area (optional)
- uiContext: Suggested follow-up actions for the operator (optional)

When creating map layers:
- Use appropriate icons for Point layers (BUILDING_COLLAPSE, FOOD_SUPPLY, DONATION_POINT, MEDICAL_FACILITY, FIRE_INCIDENT, STRUCTURAL_DAMAGE, LOGISTICS_HUB, COMMUNICATION_TOWER)
- Use color coding for severity (CRITICAL=#DC2626, HIGH=#F59E0B, MEDIUM=#3B82F6, LOW=#10B981)
- For demand zones or analysis areas, use Polygon layers with semi-transparent fills
- Always include meaningful properties in GeoJSON features for tooltips`;

// Define the database query tool
const DATABASE_QUERY_TOOL: Tool = {
  toolSpec: {
    name: 'queryDatabase',
    description: 'Query the simulation database for events based on domain, severity, time range, and location filters',
    inputSchema: {
      json: {
        type: 'object',
        properties: {
          domain: {
            type: 'string',
            enum: ['MEDICAL', 'FIRE', 'LOGISTICS', 'COMMUNICATION', 'STRUCTURAL'],
            description: 'Filter by event domain/category',
          },
          severity: {
            type: 'string',
            enum: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            description: 'Filter by severity level',
          },
          startTime: {
            type: 'string',
            description: 'Start of time range (ISO 8601 format)',
          },
          endTime: {
            type: 'string',
            description: 'End of time range (ISO 8601 format)',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of results to return (default: 100)',
          },
        },
        required: [],
      },
    },
  },
};

/**
 * Lambda handler for POST /agent/query
 * 
 * Handles natural language queries by invoking Bedrock Agent
 * Returns structured response with chat message, map updates, and UI context
 * 
 * Request Body:
 * - text (required): Natural language query
 * - sessionId (optional): For conversation continuity
 * - currentMapState (optional): Current map context
 */
export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  console.log('Query handler invoked', {
    requestId: event.requestContext.requestId,
    hasBody: !!event.body,
  });

  try {
    // Validate environment variables
    if (!TABLE_NAME) {
      console.error('Missing required environment variables', {
        hasTableName: !!TABLE_NAME,
      });

      const errorResponse: ErrorResponse = {
        error: {
          code: 'CONFIGURATION_ERROR',
          message: 'Database configuration is missing',
        },
      };

      return {
        statusCode: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
        body: JSON.stringify(errorResponse),
      };
    }

    // Parse and validate request body
    if (!event.body) {
      const errorResponse: ErrorResponse = {
        error: {
          code: 'INVALID_REQUEST',
          message: 'Request body is required',
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

    let requestBody: any;
    try {
      requestBody = JSON.parse(event.body);
    } catch (parseError) {
      console.error('Failed to parse request body', { error: parseError });

      const errorResponse: ErrorResponse = {
        error: {
          code: 'INVALID_REQUEST',
          message: 'Request body must be valid JSON',
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

    // Validate using Zod schema
    const validationResult = QueryRequestSchema.safeParse(requestBody);

    if (!validationResult.success) {
      console.error('Validation failed', {
        errors: validationResult.error.issues,
        requestBody,
      });

      const errorResponse: ErrorResponse = {
        error: {
          code: 'INVALID_REQUEST',
          message: 'Invalid request body',
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

    const { text, sessionId, currentMapState } = validationResult.data;

    console.log('Request validated', {
      textLength: text.length,
      hasSessionId: !!sessionId,
      hasMapState: !!currentMapState,
    });

    // Build user message with context
    let userMessage = text;
    if (currentMapState) {
      userMessage += `\n\nCurrent map context: center at [${currentMapState.center[0]}, ${currentMapState.center[1]}], zoom level ${currentMapState.zoom}`;
    }

    console.log('Invoking Nova model with Converse API', {
      model: BEDROCK_MODEL,
      messageLength: userMessage.length,
    });

    // Invoke Nova model with tool calling using Converse API
    const startTime = Date.now();
    const agentResponse = await invokeModelWithTools(userMessage);

    console.log('Model response received', {
      responseLength: agentResponse.length,
      duration: Date.now() - startTime,
    });

    // Transform agent output to API response format
    const queryResponse = transformAgentOutput(agentResponse, text);

    console.log('Response transformation completed', {
      hasMapLayers: queryResponse.mapLayers.length > 0,
      hasViewState: !!queryResponse.viewState,
      hasSuggestedActions: !!queryResponse.uiContext?.suggestedActions,
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(queryResponse),
    };

  } catch (error) {
    return handleError(error, event);
  }
}

/**
 * Invoke Nova model with tool calling capability
 * Implements agentic loop: model -> tool call -> model -> response
 * 
 * @param userMessage - User's query
 * @returns Final model response as string
 */
async function invokeModelWithTools(userMessage: string): Promise<string> {
  const messages: any[] = [
    {
      role: 'user',
      content: [{ text: userMessage }],
    },
  ];

  const MAX_ITERATIONS = 5; // Prevent infinite loops
  let iteration = 0;

  while (iteration < MAX_ITERATIONS) {
    iteration++;

    console.log(`Agentic loop iteration ${iteration}`, {
      messageCount: messages.length,
    });

    // Prepare Converse API input
    const input: ConverseCommandInput = {
      modelId: BEDROCK_MODEL,
      messages,
      system: [{ text: SYSTEM_PROMPT }],
      toolConfig: {
        tools: [DATABASE_QUERY_TOOL],
      },
      inferenceConfig: {
        maxTokens: 2048, // Reduced to prevent timeouts and force concise responses
        temperature: 0.7,
        topP: 0.9,
      },
    };

    // Invoke the model
    const command = new ConverseCommand(input);
    const response = await bedrockClient.send(command);

    console.log('Model response received', {
      stopReason: response.stopReason,
      usage: response.usage,
    });

    // Check stop reason
    if (response.stopReason === 'end_turn') {
      // Model finished without tool calls
      const textContent = response.output?.message?.content?.find((c: any) => c.text);
      return textContent?.text || 'No response generated';
    }

    if (response.stopReason === 'tool_use') {
      // Model wants to use a tool
      console.log('Model requested tool use');

      // Add assistant message to conversation
      messages.push({
        role: 'assistant',
        content: response.output?.message?.content || [],
      });

      // Execute tool calls
      const toolResultContent: any[] = [];
      const toolUses = response.output?.message?.content?.filter((c: any) => c.toolUse) || [];

      for (const toolUse of toolUses) {
        const tool = toolUse.toolUse;
        if (!tool) continue; // Skip if tool is undefined

        console.log('Executing tool', {
          toolName: tool.name,
          toolUseId: tool.toolUseId,
          input: tool.input,
        });

        try {
          let toolResult: any;

          if (tool.name === 'queryDatabase') {
            // Execute database query
            // Cast tool.input to the expected type
            const input = tool.input as Record<string, any>;
            toolResult = await queryDatabase({
              tableName: TABLE_NAME!,
              domain: input.domain,
              severity: input.severity,
              startTime: input.startTime,
              endTime: input.endTime,
              limit: input.limit || 100,
            });
          } else {
            toolResult = { error: `Unknown tool: ${tool.name}` };
          }

          const resultString = JSON.stringify(toolResult);
          const maxSize = 5000; // 5KB limit for tool results to prevent timeouts
          const wasTruncated = resultString.length > maxSize;
          const truncatedResult = wasTruncated
            ? resultString.substring(0, maxSize) + '... (truncated due to size, showing first 5KB of ' + resultString.length + ' bytes)'
            : resultString;

          console.log('Tool execution completed', {
            toolName: tool.name,
            originalSize: resultString.length,
            truncatedSize: truncatedResult.length,
            wasTruncated,
          });

          toolResultContent.push({
            toolResult: {
              toolUseId: tool.toolUseId,
              content: [{ text: truncatedResult }],
            },
          });
        } catch (toolError) {
          console.error('Tool execution failed', {
            toolName: tool.name,
            error: toolError instanceof Error ? toolError.message : String(toolError),
          });

          toolResultContent.push({
            toolResult: {
              toolUseId: tool.toolUseId,
              content: [
                {
                  text: `Error executing tool: ${toolError instanceof Error ? toolError.message : String(toolError)}`,
                },
              ],
              status: 'error',
            },
          });
        }
      }

      // Add tool results to conversation
      messages.push({
        role: 'user',
        content: toolResultContent,
      });

      // Continue the loop to get model's response with tool results
      continue;
    }

    // Handle other stop reasons
    console.warn('Unexpected stop reason', {
      stopReason: response.stopReason,
    });

    const textContent = response.output?.message?.content?.find((c: any) => c.text);
    return textContent?.text || 'Unable to generate response';
  }

  // Max iterations reached
  console.warn('Max agentic loop iterations reached', {
    maxIterations: MAX_ITERATIONS,
  });

  return 'Query processing took too many steps. Please try a simpler question.';
}

/**
 * Transform agent output to API response format
 * 
 * The agent is instructed to return responses in a structured format that can be parsed.
 * This function extracts the chat response and any structured data (map layers, view state, etc.)
 * 
 * @param agentResponse - Raw response from Bedrock Agent
 * @param originalQuery - Original user query
 * @returns Structured QueryResponse
 */
function transformAgentOutput(agentResponse: string, originalQuery: string): QueryResponse {
  const timestamp = new Date().toISOString();

  // Calculate simulation time based on current timestamp
  // For now, use a simple placeholder. In production, this would be calculated
  // based on the simulation timeline state
  const simulationTime = calculateSimulationTime(timestamp);

  // Try to parse structured response from agent
  // The agent may return JSON-formatted data or plain text
  let parsedResponse: any = null;
  let chatResponse = agentResponse;
  let mapAction: 'REPLACE' | 'APPEND' = 'REPLACE';
  let mapLayers: any[] = [];
  let viewState: any = undefined;
  let uiContext: any = undefined;
  let clientStateHint: any = undefined;
  let tabularData: any = undefined;

  try {
    // Try to extract JSON from the response
    // The agent might wrap JSON in markdown code blocks or return it directly
    const jsonMatch = agentResponse.match(/```json\s*([\s\S]*?)\s*```/) ||
      agentResponse.match(/\{[\s\S]*\}/);

    if (jsonMatch) {
      const jsonStr = jsonMatch[1] || jsonMatch[0];
      parsedResponse = JSON.parse(jsonStr);

      // Extract structured fields if present
      if (parsedResponse.chatResponse) {
        chatResponse = parsedResponse.chatResponse;
      }
      if (parsedResponse.mapAction) {
        mapAction = parsedResponse.mapAction;
      }
      if (parsedResponse.mapLayers) {
        mapLayers = parsedResponse.mapLayers;
      }
      if (parsedResponse.viewState) {
        viewState = parsedResponse.viewState;
      }
      if (parsedResponse.uiContext) {
        uiContext = parsedResponse.uiContext;
      }
      if (parsedResponse.clientStateHint) {
        clientStateHint = parsedResponse.clientStateHint;
      }
      if (parsedResponse.tabularData) {
        tabularData = parsedResponse.tabularData;
      }

      // If chatResponse was in JSON, remove the JSON block from the text
      if (jsonMatch[1]) {
        chatResponse = agentResponse.replace(/```json\s*[\s\S]*?\s*```/, '').trim();
        if (!chatResponse && parsedResponse.chatResponse) {
          chatResponse = parsedResponse.chatResponse;
        }
      }
    }
  } catch (parseError) {
    // If parsing fails, use the raw response as chat response
    console.log('Could not parse structured response from agent, using raw text', {
      error: parseError instanceof Error ? parseError.message : String(parseError),
    });
  }

  // Ensure chatResponse is not empty
  if (!chatResponse || chatResponse.trim().length === 0) {
    chatResponse = 'I received your query but was unable to generate a response.';
  }

  // Build the response structure
  const response: QueryResponse = {
    simulationTime,
    timestamp,
    chatResponse,
    mapAction,
    mapLayers,
  };

  // Add optional fields if present
  if (viewState) {
    response.viewState = viewState;
  }
  if (tabularData) {
    response.tabularData = tabularData;
  }
  if (uiContext) {
    response.uiContext = uiContext;
  }
  if (clientStateHint) {
    response.clientStateHint = clientStateHint;
  }

  return response;
}

/**
 * Calculate simulation time from timestamp
 * 
 * This is a simplified implementation. In production, this would:
 * 1. Query the current simulation state from DynamoDB
 * 2. Calculate the day and time based on the simulation timeline
 * 3. Return a formatted string like "Day 3, 14:30"
 * 
 * @param timestamp - ISO 8601 timestamp
 * @returns Formatted simulation time string
 */
function calculateSimulationTime(timestamp: string): string {
  // For now, return a placeholder
  // This could be enhanced to track actual simulation time
  const date = new Date(timestamp);
  const hours = date.getUTCHours();
  const minutes = date.getUTCMinutes();

  // Simple mapping: use current hour to determine simulation day
  const day = Math.floor(hours / 4) % 7; // Cycle through 7 days
  const simHour = hours % 24;
  const simMinute = minutes;

  return `Day ${day}, ${simHour.toString().padStart(2, '0')}:${simMinute.toString().padStart(2, '0')}`;
}

/**
 * Handle errors and return appropriate error response
 * 
 * @param error - Error object
 * @param event - Original API Gateway event
 * @returns API Gateway error response
 */
function handleError(error: unknown, event: APIGatewayProxyEvent): APIGatewayProxyResult {
  // Log detailed error information for debugging
  const errorDetails: any = {
    requestId: event.requestContext.requestId,
    timestamp: new Date().toISOString(),
  };

  if (error instanceof Error) {
    errorDetails.errorName = error.name;
    errorDetails.errorMessage = error.message;
    errorDetails.errorStack = error.stack;

    // Log AWS SDK specific error properties
    if ('$metadata' in error) {
      errorDetails.awsMetadata = (error as any).$metadata;
    }
    if ('$fault' in error) {
      errorDetails.awsFault = (error as any).$fault;
    }
  } else {
    errorDetails.error = String(error);
  }

  console.error('Error processing query request', errorDetails);

  let statusCode = 500;
  let errorCode = 'INTERNAL_ERROR';
  let errorMessage = 'An unexpected error occurred while processing the query';
  let shouldRetry = false;

  if (error instanceof Error) {
    const errorMsg = error.message.toLowerCase();
    const errorName = error.name.toLowerCase();

    // Configuration errors
    if (errorMsg.includes('table_name') || errorMsg.includes('model')) {
      errorCode = 'CONFIGURATION_ERROR';
      errorMessage = 'Service configuration error';
      shouldRetry = false;
    }
    // Access/Authorization errors
    else if (errorMsg.includes('accessdenied') ||
      errorMsg.includes('unauthorizedexception') ||
      errorName.includes('accessdenied')) {
      statusCode = 403;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'Failed to invoke AI model: Access denied';
      shouldRetry = false;
    }
    // Throttling errors
    else if (errorMsg.includes('throttling') ||
      errorMsg.includes('too many requests') ||
      errorName.includes('throttling')) {
      statusCode = 429;
      errorCode = 'RATE_LIMIT_EXCEEDED';
      errorMessage = 'Too many requests to AI service. Please try again in a moment.';
      shouldRetry = true;
    }
    // Timeout errors
    else if (errorMsg.includes('timeout') ||
      errorMsg.includes('timed out') ||
      errorName.includes('timeout')) {
      statusCode = 504;
      errorCode = 'TIMEOUT_ERROR';
      errorMessage = 'AI model request timed out. Please try a simpler query.';
      shouldRetry = true;
    }
    // Validation errors
    else if (errorMsg.includes('validation') ||
      errorName.includes('validation')) {
      statusCode = 400;
      errorCode = 'AGENT_ERROR';
      errorMessage = `Invalid request to AI model: ${error.message}`;
      shouldRetry = false;
    }
    // Resource not found
    else if (errorName.includes('resourcenotfound') ||
      errorMsg.includes('not found')) {
      statusCode = 404;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'AI model not found. Please check configuration.';
      shouldRetry = false;
    }
    // Service unavailable
    else if (errorMsg.includes('service unavailable') ||
      errorMsg.includes('503')) {
      statusCode = 503;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'AI service temporarily unavailable';
      shouldRetry = true;
    }
    // Model errors
    else if (errorMsg.includes('model') && errorMsg.includes('error')) {
      statusCode = 500;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'AI model error. Please try again.';
      shouldRetry = true;
    }
  }

  const errorResponse: ErrorResponse = {
    error: {
      code: errorCode,
      message: errorMessage,
      details: {
        shouldRetry,
        requestId: event.requestContext.requestId,
      },
    },
  };

  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'X-Should-Retry': shouldRetry ? 'true' : 'false',
    },
    body: JSON.stringify(errorResponse),
  };
}
