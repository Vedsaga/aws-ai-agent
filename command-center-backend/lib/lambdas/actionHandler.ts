import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import {
  BedrockAgentRuntimeClient,
  InvokeAgentCommand,
  InvokeAgentCommandInput,
} from '@aws-sdk/client-bedrock-agent-runtime';
import { ActionRequestSchema, ActionResponse, ErrorResponse } from '../types/api';

// Initialize Bedrock Agent Runtime client
const bedrockClient = new BedrockAgentRuntimeClient({
  region: process.env.AWS_REGION || 'us-east-1',
});

// Environment variables
const AGENT_ID = process.env.AGENT_ID;
const AGENT_ALIAS_ID = process.env.AGENT_ALIAS_ID;
const LOG_LEVEL = process.env.LOG_LEVEL || 'INFO';

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
    if (!AGENT_ID || !AGENT_ALIAS_ID) {
      console.error('Missing required environment variables', {
        hasAgentId: !!AGENT_ID,
        hasAgentAliasId: !!AGENT_ALIAS_ID,
        requestId,
      });

      const errorResponse: ErrorResponse = {
        error: {
          code: 'CONFIGURATION_ERROR',
          message: 'Bedrock Agent is not properly configured',
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

    // Prepare input for Bedrock Agent
    const sessionId = `action-${actionId}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const agentInput: InvokeAgentCommandInput = {
      agentId: AGENT_ID,
      agentAliasId: AGENT_ALIAS_ID,
      sessionId,
      inputText: prompt,
    };

    console.log('Invoking Bedrock Agent for action', {
      agentId: AGENT_ID,
      agentAliasId: AGENT_ALIAS_ID,
      sessionId,
      actionId,
      requestId,
    });

    // Invoke Bedrock Agent with timeout handling
    const startTime = Date.now();
    const AGENT_TIMEOUT_MS = 55000; // 55 seconds (Lambda timeout is 60s)

    let response: any;
    let agentResponse: string;

    try {
      const command = new InvokeAgentCommand(agentInput);

      // Create a timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Agent invocation timeout')), AGENT_TIMEOUT_MS);
      });

      // Race between agent invocation and timeout
      response = await Promise.race([
        bedrockClient.send(command),
        timeoutPromise,
      ]);

      const invocationDuration = Date.now() - startTime;

      console.log('Bedrock Agent invoked successfully', {
        invocationDuration,
        hasCompletion: !!response.completion,
        actionId,
        requestId,
      });

      // Process agent response stream
      agentResponse = await processAgentResponse(response, startTime, AGENT_TIMEOUT_MS);

      console.log('Agent response processed', {
        responseLength: agentResponse.length,
        processingDuration: Date.now() - startTime,
        actionId,
        requestId,
      });

    } catch (agentError) {
      // Handle agent-specific errors
      const duration = Date.now() - startTime;

      console.error('Error invoking Bedrock Agent', {
        error: agentError instanceof Error ? agentError.message : String(agentError),
        duration,
        actionId,
        agentId: AGENT_ID,
        agentAliasId: AGENT_ALIAS_ID,
        requestId,
      });

      // Check if it's a timeout
      if (agentError instanceof Error && agentError.message.includes('timeout')) {
        // Return partial response with timeout explanation
        const partialResponse: ActionResponse = {
          simulationTime: calculateSimulationTime(new Date().toISOString()),
          timestamp: new Date().toISOString(),
          chatResponse: `The action "${actionId}" is taking longer than expected. Please try again or try a different action.`,
          mapAction: 'REPLACE',
          mapLayers: [],
          uiContext: {
            suggestedActions: [
              {
                label: 'Try again',
                actionId,
                payload,
              },
              {
                label: 'Get help',
                actionId: 'HELP',
              },
            ],
          },
        };

        return {
          statusCode: 200,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
          },
          body: JSON.stringify(partialResponse),
        };
      }

      // Re-throw other errors to be handled by the main error handler
      throw agentError;
    }

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
 * Process the streaming response from Bedrock Agent
 * 
 * @param response - Response from InvokeAgentCommand
 * @param startTime - Start time of the request
 * @param timeoutMs - Timeout in milliseconds
 * @returns Complete agent response text
 */
async function processAgentResponse(
  response: any,
  startTime: number,
  timeoutMs: number
): Promise<string> {
  let completeResponse = '';
  let chunkCount = 0;

  try {
    // The response.completion is an async iterable stream
    if (response.completion) {
      for await (const event of response.completion) {
        // Check if we've exceeded the timeout
        const elapsed = Date.now() - startTime;
        if (elapsed > timeoutMs) {
          console.warn('Stream processing timeout', {
            elapsed,
            timeoutMs,
            chunkCount,
            partialResponseLength: completeResponse.length,
          });

          // Return partial response if we have any
          if (completeResponse) {
            return completeResponse;
          }

          throw new Error('Stream processing timeout');
        }

        if (event.chunk && event.chunk.bytes) {
          // Decode the bytes to string
          const chunk = new TextDecoder().decode(event.chunk.bytes);
          completeResponse += chunk;
          chunkCount++;

          if (LOG_LEVEL === 'DEBUG') {
            console.log('Received chunk', {
              chunkLength: chunk.length,
              chunkCount,
              totalLength: completeResponse.length,
            });
          }
        }
      }
    }

    console.log('Stream processing completed', {
      chunkCount,
      totalLength: completeResponse.length,
      duration: Date.now() - startTime,
    });

    return completeResponse;
  } catch (error) {
    console.error('Error processing agent response stream', {
      error: error instanceof Error ? error.message : String(error),
      partialResponseLength: completeResponse.length,
      chunkCount,
    });

    // Return partial response if available
    if (completeResponse && completeResponse.length > 0) {
      console.log('Returning partial response due to error', {
        partialLength: completeResponse.length,
      });
      return completeResponse;
    }

    throw error;
  }
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
      errorMessage = 'Invalid request to Bedrock Agent';
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
