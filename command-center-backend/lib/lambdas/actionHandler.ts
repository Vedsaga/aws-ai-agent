import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import {
  BedrockRuntimeClient,
  ConverseCommand,
  ConverseCommandInput,
  Tool,
  ToolResultBlock,
} from '@aws-sdk/client-bedrock-runtime';
import { ActionRequestSchema, ActionResponse, ErrorResponse } from '../types/api';
import { queryDatabase } from '../data-access/database-query';

// Initialize Bedrock Runtime client
const bedrockClient = new BedrockRuntimeClient({
  region: process.env.AWS_REGION || 'us-east-1',
});

// Environment variables
const BEDROCK_MODEL = process.env.BEDROCK_MODEL || 'amazon.nova-pro-v1:0';
const TABLE_NAME = process.env.TABLE_NAME;
const LOG_LEVEL = process.env.LOG_LEVEL || 'INFO';

// System prompt (same as query handler)
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
 * Known action IDs and their corresponding prompts
 * This mapping ensures only valid actions are processed
 */
const ACTION_MAPPINGS: Record<string, (payload?: any) => string> = {
  'GENERATE_AREA_BRIEFING': (payload) => {
    const area = payload?.area || 'the affected region';
    return `Generate a comprehensive briefing for ${area}. Include all critical incidents, resource status, and urgent needs.`;
  },
  'CALC_ROUTE': (payload) => {
    const from = payload?.from || 'the logistics hub';
    const to = payload?.to || 'the destination';
    return `Calculate the optimal route from ${from} to ${to}. Consider road conditions, damaged infrastructure, and current traffic.`;
  },
  'SHOW_CRITICAL_MEDICAL': () => {
    return 'Show all critical medical incidents on the map. Highlight the most urgent cases requiring immediate attention.';
  },
  'SHOW_RESOURCE_GAPS': () => {
    return 'Identify and display areas with critical resource shortages. Show food, water, medical supplies, and shelter gaps.';
  },
  'ANALYZE_DEMAND_ZONES': () => {
    return 'Analyze and visualize demand zones across the affected area. Create heat maps showing areas with highest need for assistance.';
  },
  'SHOW_FIRE_INCIDENTS': () => {
    return 'Display all active fire incidents on the map. Include severity levels and required firefighting resources.';
  },
  'SHOW_STRUCTURAL_DAMAGE': () => {
    return 'Show all structural damage reports including building collapses and infrastructure damage. Prioritize by severity.';
  },
  'SHOW_LOGISTICS_STATUS': () => {
    return 'Display the status of all logistics operations including supply routes, distribution points, and resource availability.';
  },
  'SHOW_COMMUNICATION_STATUS': () => {
    return 'Show the status of communication infrastructure including tower status and coverage gaps.';
  },
  'HELP': () => {
    return 'Provide an overview of available commands and how to use the Command Center system effectively.';
  },
};

/**
 * Lambda handler for POST /agent/action
 * 
 * Executes pre-defined actions by invoking Bedrock Agent with action-specific prompts
 * Returns structured response with chat message, map updates, and UI context
 * 
 * Request Body:
 * - actionId (required): Pre-defined action identifier
 * - payload (optional): Action-specific parameters
 */
export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  const requestId = event.requestContext.requestId;

  console.log('Action handler invoked', {
    requestId,
    hasBody: !!event.body,
  });

  try {
    // Validate environment variables
    if (!TABLE_NAME) {
      console.error('Missing required environment variables', {
        hasTableName: !!TABLE_NAME,
        requestId,
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
      console.error('Failed to parse request body', {
        error: parseError,
        requestId,
      });

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
    const validationResult = ActionRequestSchema.safeParse(requestBody);

    if (!validationResult.success) {
      console.error('Validation failed', {
        errors: validationResult.error.issues,
        requestBody,
        requestId,
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

    const { actionId, payload } = validationResult.data;

    // Validate actionId against known actions
    if (!ACTION_MAPPINGS[actionId]) {
      console.error('Invalid actionId', {
        actionId,
        availableActions: Object.keys(ACTION_MAPPINGS),
        requestId,
      });

      const errorResponse: ErrorResponse = {
        error: {
          code: 'INVALID_ACTION',
          message: `Unknown actionId: ${actionId}`,
          details: {
            actionId,
            availableActions: Object.keys(ACTION_MAPPINGS),
          },
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

    // Log action execution
    console.log('Executing action', {
      actionId,
      hasPayload: !!payload,
      payloadKeys: payload ? Object.keys(payload) : [],
      requestId,
    });

    // Construct prompt for the action
    const promptGenerator = ACTION_MAPPINGS[actionId];
    const prompt = promptGenerator(payload);

    console.log('Action prompt constructed', {
      actionId,
      promptLength: prompt.length,
      requestId,
    });

    console.log('Invoking Nova model for action', {
      model: BEDROCK_MODEL,
      actionId,
      requestId,
    });

    // Invoke Nova model with tool calling
    const startTime = Date.now();
    const agentResponse = await invokeModelWithTools(prompt);

    console.log('Model response received', {
      responseLength: agentResponse.length,
      duration: Date.now() - startTime,
      actionId,
      requestId,
    });

    // Transform agent output to API response format
    const actionResponse = transformAgentOutput(agentResponse, actionId);

    console.log('Response transformation completed', {
      hasMapLayers: actionResponse.mapLayers.length > 0,
      hasViewState: !!actionResponse.viewState,
      hasSuggestedActions: !!actionResponse.uiContext?.suggestedActions,
      actionId,
      requestId,
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: JSON.stringify(actionResponse),
    };

  } catch (error) {
    return handleError(error, event);
  }
}

/**
 * Invoke Nova model with tool calling capability
 * Implements agentic loop: model -> tool call -> model -> response
 * 
 * @param userMessage - User's query/action prompt
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
        maxTokens: 4096,
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

          console.log('Tool execution completed', {
            toolName: tool.name,
            resultSize: JSON.stringify(toolResult).length,
          });

          // Truncate large results to avoid SDK serialization issues
          const resultString = JSON.stringify(toolResult);
          const maxSize = 25000; // 25KB limit for tool results
          const truncatedResult = resultString.length > maxSize 
            ? resultString.substring(0, maxSize) + '... (truncated)'
            : resultString;

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

  return 'Query processing took too many steps. Please try a simpler action.';
}

/**
 * Transform agent output to API response format
 * 
 * The agent is instructed to return responses in a structured format that can be parsed.
 * This function extracts the chat response and any structured data (map layers, view state, etc.)
 * 
 * @param agentResponse - Raw response from Bedrock Agent
 * @param actionId - Action ID that was executed
 * @returns Structured ActionResponse
 */
function transformAgentOutput(agentResponse: string, actionId: string): ActionResponse {
  const timestamp = new Date().toISOString();

  // Calculate simulation time based on current timestamp
  const simulationTime = calculateSimulationTime(timestamp);

  // Try to parse structured response from agent
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
      actionId,
    });
  }

  // Ensure chatResponse is not empty
  if (!chatResponse || chatResponse.trim().length === 0) {
    chatResponse = `Action "${actionId}" was executed but no response was generated.`;
  }

  // Build the response structure
  const response: ActionResponse = {
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
 * @param timestamp - ISO 8601 timestamp
 * @returns Formatted simulation time string
 */
function calculateSimulationTime(timestamp: string): string {
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
  const requestId = event.requestContext.requestId;

  // Log detailed error information for debugging
  const errorDetails: any = {
    requestId,
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

  console.error('Error processing action request', errorDetails);

  let statusCode = 500;
  let errorCode = 'INTERNAL_ERROR';
  let errorMessage = 'An unexpected error occurred while processing the action';
  let shouldRetry = false;

  if (error instanceof Error) {
    const errorMsg = error.message.toLowerCase();
    const errorName = error.name.toLowerCase();

    // Configuration errors
    if (errorMsg.includes('agent_id') || errorMsg.includes('agent_alias_id')) {
      errorCode = 'CONFIGURATION_ERROR';
      errorMessage = 'Bedrock Agent configuration error';
      shouldRetry = false;
    }
    // Access/Authorization errors
    else if (errorMsg.includes('accessdenied') ||
      errorMsg.includes('unauthorizedexception') ||
      errorName.includes('accessdenied')) {
      statusCode = 403;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'Failed to invoke Bedrock Agent: Access denied';
      shouldRetry = false;
    }
    // Throttling errors
    else if (errorMsg.includes('throttling') ||
      errorMsg.includes('too many requests') ||
      errorName.includes('throttling')) {
      statusCode = 429;
      errorCode = 'RATE_LIMIT_EXCEEDED';
      errorMessage = 'Too many requests to Bedrock Agent. Please try again in a moment.';
      shouldRetry = true;
    }
    // Timeout errors
    else if (errorMsg.includes('timeout') ||
      errorMsg.includes('timed out') ||
      errorName.includes('timeout')) {
      statusCode = 504;
      errorCode = 'TIMEOUT_ERROR';
      errorMessage = 'Bedrock Agent request timed out. Please try a different action.';
      shouldRetry = true;
    }
    // Validation errors
    else if (errorMsg.includes('validation') ||
      errorName.includes('validation')) {
      statusCode = 400;
      errorCode = 'AGENT_ERROR';
      errorMessage = `Invalid request to Bedrock Agent: ${error.message}`;
      shouldRetry = false;
    }
    // Resource not found
    else if (errorName.includes('resourcenotfound') ||
      errorMsg.includes('not found')) {
      statusCode = 404;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'Bedrock Agent not found. Please check configuration.';
      shouldRetry = false;
    }
    // Service unavailable
    else if (errorMsg.includes('service unavailable') ||
      errorMsg.includes('503')) {
      statusCode = 503;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'Bedrock Agent service temporarily unavailable';
      shouldRetry = true;
    }
    // Model errors
    else if (errorMsg.includes('model') && errorMsg.includes('error')) {
      statusCode = 500;
      errorCode = 'AGENT_ERROR';
      errorMessage = 'Bedrock Agent model error. Please try again.';
      shouldRetry = true;
    }
  }

  const errorResponse: ErrorResponse = {
    error: {
      code: errorCode,
      message: errorMessage,
      details: {
        shouldRetry,
        requestId,
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
