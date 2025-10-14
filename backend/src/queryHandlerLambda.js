// src/queryHandlerLambda.js

/**
 * This Lambda function handles the POST /agent/query endpoint.
 * It acts as the primary interface for natural language queries from the client.
 * Its main responsibility is to invoke the Amazon Bedrock Agent with the user's text
 * and return the agent's final, synthesized response.
 */

// Mock AWS SDK v3 client for Bedrock Agent Runtime.
// In a real project, you would install this with `npm install @aws-sdk/client-bedrock-agent-runtime`.
const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");

/**
 * Mocks the response from the Bedrock Agent.
 * The real response would be a stream of chunks, which we would need to assemble.
 * This mock represents the final, assembled response.
 */
const MOCK_AGENT_RESPONSE = {
    chatResponse: "Yes, I found one critical medical incident related to a building collapse in Beyoğlu.",
    // In a real scenario, the agent might also return the raw source data it used.
    sourceData: [
        {
            Day: "DAY_0",
            Timestamp: "2023-02-06T04:00:00Z",
            eventId: "e4a2b2c1-0b5a-4b3c-8a1e-8b0a9b3a2a1b",
            domain: "MEDICAL",
            severity: "CRITICAL",
            summary: "Building collapse reported with multiple injuries."
        }
    ]
};

/**
 * AWS Lambda handler function.
 *
 * @param {Object} event The event object from API Gateway. The user's query is in the body.
 * @returns {Object} The API Gateway response object containing the agent's full response.
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

    const userQuery = body.text;
    const sessionId = body.sessionId || `session_${Date.now()}`; // A session ID is required by the agent.

    if (!userQuery) {
        return {
            statusCode: 400,
            headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: "Missing 'text' field in request body." }),
        };
    }

    // In a real script, you would configure your AWS region and credentials.
    // const bedrockClient = new BedrockAgentRuntimeClient({ region: "us-east-1" });
    const params = {
        agentId: "YOUR_AGENT_ID",         // Replace with your actual Agent ID
        agentAliasId: "YOUR_AGENT_ALIAS_ID", // Replace with your actual Agent Alias ID
        sessionId: sessionId,
        inputText: userQuery,
    };

    try {
        // --- This is a MOCKED AWS SDK call ---
        // In a real script, this would invoke the agent.
        // const command = new InvokeAgentCommand(params);
        // const responseStream = await bedrockClient.send(command);
        // let finalResponse = "";
        // for await (const chunk of responseStream.completion) {
        //     finalResponse += Buffer.from(chunk.bytes).toString('utf-8');
        // }

        console.log("--- MOCK SUCCESS ---");
        console.log("Demonstrating invocation of Bedrock Agent with params:", JSON.stringify(params, null, 2));
        const finalResponse = MOCK_AGENT_RESPONSE;

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" // Enable CORS
            },
            body: JSON.stringify(finalResponse),
        };

    } catch (err) {
        console.error("Error invoking Bedrock Agent", err);
        return {
            statusCode: 500,
            headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
            body: JSON.stringify({ message: "Internal Server Error" }),
        };
    }
};
