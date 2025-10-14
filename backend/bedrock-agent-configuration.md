# Bedrock Agent Configuration Guide

This document outlines the steps and configuration details required to set up the Amazon Bedrock Agent for the Command Center Backend, as described in Phase 4 of the `TaskList.md`.

### 1. Create a New Agent in Amazon Bedrock

1.  Navigate to the Amazon Bedrock console.
2.  Go to **Agents** and click **Create Agent**.
3.  Provide a name (e.g., `CommandCenterAgent`) and a description.
4.  Select an appropriate IAM role that grants the agent permissions to invoke Lambda functions.
5.  Choose a foundation model. **Claude 3 Sonnet** is a good choice for its reasoning capabilities.

### 2. Write the Agent Instruction Prompt

This is the core "persona" of your agent. Enter the following into the **Instructions** box.

```text
You are the Command Center AI Assistant. Your primary goal is to answer questions about emergency events using the data available to you. You are precise, calm, and focus on providing factual information.

When a user asks a question, you must first determine what specific information is needed. Then, use the `databaseQueryTool` to retrieve that information. The tool can search for events by 'domain' (e.g., MEDICAL, LOGISTICS) and 'severity' (e.g., CRITICAL, HIGH).

After retrieving the data, synthesize it into a clear, natural language response for the user. Always present the key details from the data you found. If you cannot find any relevant information, clearly state that no data was found for the user's query. Do not make up information.
```

### 3. Create the Action Group (The Tool)

The Action Group connects your agent to its `databaseQueryToolLambda` tool.

1.  In the agent configuration, click **Add** under **Action groups**.
2.  **Action group name:** `databaseQueryTool`
3.  **Lambda function:** Select the `databaseQueryToolLambda` function you deployed.
4.  **API Schema:** This is the critical part. It tells the agent what the tool can do. Select **Define with OpenAPI schema** and provide the following JSON:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Database Query Tool",
    "version": "1.0.0",
    "description": "A tool to query the master event timeline for emergency incidents."
  },
  "paths": {
    "/query": {
      "post": {
        "summary": "Query for emergency events.",
        "description": "Searches the database for events based on filters like domain and severity.",
        "operationId": "queryDatabase",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "queryParams": {
                    "type": "object",
                    "properties": {
                      "domain": {
                        "type": "string",
                        "description": "The category of the event to search for (e.g., 'MEDICAL', 'SHELTER')."
                      },
                      "severity": {
                        "type": "string",
                        "description": "The severity level of the event to search for (e.g., 'CRITICAL', 'HIGH')."
                      }
                    },
                    "required": ["domain"]
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful query",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 4. Test the Agent

Once the agent and its Action Group are created:

1.  Go to the **Test** playground in the Bedrock console for your agent.
2.  Ask it questions that will force it to use its tool. For example:
    *   `"Are there any critical medical incidents?"`
    *   `"Find all logistics events."`
    *   `"Show me high severity shelter updates."`
3.  Observe the **Trace**. You should see the agent reasoning that it needs to call the `databaseQueryTool`, see it invoke the `databaseQueryToolLambda` with the correct parameters (e.g., `{"domain": "MEDICAL", "severity": "CRITICAL"}`), and then see the raw JSON data that comes back from the Lambda.
4.  Finally, the agent should synthesize this data into a user-friendly chat response.

This completes the manual configuration of the Bedrock Agent.
