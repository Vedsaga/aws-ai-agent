// src/updatesHandlerLambda.js

/**
 * This Lambda function handles the GET /data/updates endpoint.
 * It is designed to be a direct-access, high-performance endpoint that does not use the Bedrock Agent.
 * It retrieves events from the DynamoDB 'MasterEventTimeline' table based on a 'since' timestamp
 * and an optional 'domain' filter.
 */

// Mock AWS SDK v3 client for DynamoDB.
// In a real project, you would install this with `npm install @aws-sdk/client-dynamodb`.
const { DynamoDBClient, QueryCommand } = require("@aws-sdk/client-dynamodb");
const { unmarshall } = require("@aws-sdk/util-dynamodb");

/**
 * Mocks the response from a DynamoDB query.
 * In a real function, this would be the actual data returned from the database.
 */
const MOCK_DB_RESPONSE = [
    {
        Day: "DAY_1",
        Timestamp: "2023-02-07T10:00:00Z",
        eventId: "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
        domain: "SHELTER",
        severity: "MEDIUM",
        summary: "Temporary shelter capacity reaching its limit in Fatih district.",
        geojson: {
            type: "Point",
            coordinates: [28.9497, 41.0136]
        }
    },
];


/**
 * AWS Lambda handler function.
 *
 * @param {Object} event The event object from API Gateway. It should contain queryStringParameters.
 * @returns {Object} The API Gateway response object.
 */
exports.handler = async (event) => {
    console.log("Received event:", JSON.stringify(event, null, 2));

    // Extract query string parameters from the API Gateway event.
    const since = event.queryStringParameters?.since;
    const domain = event.queryStringParameters?.domain;

    // The 'since' parameter is mandatory.
    if (!since) {
        return {
            statusCode: 400,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" // Enable CORS
            },
            body: JSON.stringify({ message: "Missing required query parameter: since" }),
        };
    }

    // In a real script, you would configure your AWS region and credentials.
    // const dbClient = new DynamoDBClient({ region: "us-east-1" });

    // Construct the DynamoDB Query parameters.
    // This is a simplified example. A real implementation would need to handle partitioning
    // (e.g., querying across multiple 'Day' partitions if the time range crosses a day boundary).
    const params = {
        TableName: "MasterEventTimeline",
        KeyConditionExpression: "#day = :dayVal AND #ts > :sinceVal",
        ExpressionAttributeNames: {
            "#day": "Day",
            "#ts": "Timestamp"
        },
        ExpressionAttributeValues: {
            ":dayVal": { S: "DAY_1" }, // Simplified for mock
            ":sinceVal": { S: since }
        }
    };

    // If a 'domain' is specified, we query the Global Secondary Index (GSI).
    if (domain) {
        params.IndexName = "domain-timestamp-index";
        params.KeyConditionExpression = "#domain = :domainVal AND #ts > :sinceVal";
        params.ExpressionAttributeNames = {
            "#domain": "domain",
            "#ts": "Timestamp"
        };
        params.ExpressionAttributeValues = {
            ":domainVal": { S: domain },
            ":sinceVal": { S: since }
        };
    }

    try {
        // --- This is a MOCKED AWS SDK call ---
        // In a real script, the following line would be active to query AWS.
        // const data = await dbClient.send(new QueryCommand(params));
        // const items = data.Items.map(item => unmarshall(item));

        console.log("--- MOCK SUCCESS ---");
        console.log("This is a demonstration. The script has formatted the query and would have sent it to DynamoDB.");
        console.log("DynamoDB Query Params:", JSON.stringify(params, null, 2));
        const items = MOCK_DB_RESPONSE; // Use mock data

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" // Enable CORS
            },
            body: JSON.stringify({
                updates: items,
                lastEvaluatedTimestamp: items.length > 0 ? items[items.length - 1].Timestamp : since,
            }),
        };

    } catch (err) {
        console.error("Error querying DynamoDB", err);
        return {
            statusCode: 500,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            body: JSON.stringify({ message: "Internal Server Error" }),
        };
    }
};
