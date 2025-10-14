// src/actionHandlerLambda.js

/**
 * This Lambda function handles the POST /agent/action endpoint.
 * This endpoint is for predefined user actions (e.g., clicking a button in the UI
 * that triggers a specific, non-natural-language request).
 *
 * For the current requirements, this function can be a simple placeholder.
 * A more advanced implementation might use the 'actionId' to trigger
 * specific queries or workflows via the Bedrock Agent.
 */

// Mock AWS SDK v3 client for Bedrock Agent Runtime.
const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");

/**
 * AWS Lambda handler function.
 *
 * @param {Object} event The event object from API Gateway. The action details are in the body.
 * @returns {Object} The API Gateway response object.
 */
exports.handler = async (event) => {
    console.log("Received event:", JSON.stringify(event, null, 2));

    let body;
    try {
        body = JSON.parse(event.body);
    } catch (e) {
        return {
            statusCode: 400,
            headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: "Invalid JSON in request body." })
        };
    }

    const actionId = body.actionId;
    const sessionId = body.sessionId || `session_${Date.now()}`;

    if (!actionId) {
        return {
            statusCode: 400,
            headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: "Missing 'actionId' field in request body." }),
        };
    }

    console.log(`--- MOCK SUCCESS ---`);
    console.log(`This is a demonstration for action '${actionId}'.`);
    console.log("In a real application, this ID would be passed to the Bedrock agent to trigger a specific tool or chain of thought.");

    // The response would typically come from the agent, but we'll mock a simple acknowledgement.
    const mockResponse = {
        chatResponse: `The action '${actionId}' has been acknowledged and is being processed.`,
        status: "SUCCESS"
    };

    return {
        statusCode: 200,
        headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*" // Enable CORS
        },
        body: JSON.stringify(mockResponse),
    };
};
