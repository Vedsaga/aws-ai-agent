// src/databaseQueryToolLambda.js

/**
 * This Lambda function is the "tool" for the Amazon Bedrock Agent.
 * The agent calls this function when its reasoning determines it needs to query the database.
 * It receives structured parameters from the agent, performs the actual query against DynamoDB,
 * and returns the raw data back to the agent for synthesis into a natural language response.
 */

// Mock AWS SDK v3 client for DynamoDB.
const { DynamoDBClient, QueryCommand } = require("@aws-sdk/client-dynamodb");
const { unmarshall } = require("@aws-sdk/util-dynamodb");

/**
 * Mocks the response from a DynamoDB query based on a domain filter.
 */
const MOCK_DB_RESPONSE_MEDICAL = [
    {
        Day: "DAY_0",
        Timestamp: "2023-02-06T04:00:00Z",
        eventId: "e4a2b2c1-0b5a-4b3c-8a1e-8b0a9b3a2a1b",
        domain: "MEDICAL",
        severity: "CRITICAL",
        summary: "Building collapse reported with multiple injuries.",
        geojson: { type: "Point", coordinates: [28.9784, 41.0344] }
    }
];

/**
 * AWS Lambda handler function.
 *
 * @param {Object} event The event object from the Bedrock Agent. The agent's parameters are expected here.
 * @returns {Object} The raw data retrieved from the database.
 */
exports.handler = async (event) => {
    console.log("Received event from Bedrock Agent:", JSON.stringify(event, null, 2));

    // The Bedrock agent's action group parameters are typically passed in the event.
    // The exact structure can vary, so we'll check a common pattern.
    const queryParams = event.queryParams || {};
    const { domain, severity } = queryParams;

    if (!domain && !severity) {
         return {
            statusCode: 400,
            body: JSON.stringify({ message: "Missing required query parameter: domain or severity" }),
        };
    }

    // In a real script, you would configure your AWS region and credentials.
    // const dbClient = new DynamoDBClient({ region: "us-east-1" });

    // Construct the DynamoDB Query parameters.
    // This example assumes querying the 'domain-timestamp-index' GSI.
    // A more complex tool could build more dynamic queries based on more parameters.
    const params = {
        TableName: "MasterEventTimeline",
        IndexName: "domain-timestamp-index",
        KeyConditionExpression: "#domain = :domainVal",
        ExpressionAttributeNames: { "#domain": "domain" },
        ExpressionAttributeValues: { ":domainVal": { S: domain } }
    };

    // Example of adding a filter for severity
    if (severity) {
        params.FilterExpression = "severity = :sevVal";
        params.ExpressionAttributeValues[":sevVal"] = { S: severity };
    }


    try {
        // --- This is a MOCKED AWS SDK call ---
        // In a real script, this would query DynamoDB.
        // const data = await dbClient.send(new QueryCommand(params));
        // const items = data.Items.map(item => unmarshall(item));

        console.log("--- MOCK SUCCESS ---");
        console.log("Agent tool is demonstrating a DB query with params:", JSON.stringify(params, null, 2));
        const items = MOCK_DB_RESPONSE_MEDICAL; // Use mock data

        // The agent expects the raw data back to reason over it.
        // The response format for the agent should be defined in the Action Group OpenAPI schema.
        // We'll return a simple object containing the results.
        return {
            response: {
                results: items
            }
        };

    } catch (err) {
        console.error("Error querying DynamoDB", err);
         return {
            statusCode: 500,
            body: JSON.stringify({ message: "Internal Server Error" }),
        };
    }
};
