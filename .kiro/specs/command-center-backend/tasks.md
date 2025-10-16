# Implementation Plan

- [x] 1. Set up AWS infrastructure foundation with CDK
  - Create AWS CDK project structure with TypeScript
  - Configure CDK app with stack for Command Center Backend
  - Define IAM roles with least privilege for Lambda, DynamoDB, Bedrock, and API Gateway
  - Set up environment configuration for dev/staging/prod
  - _Requirements: 7.1, 7.2_

- [x] 2. Create DynamoDB table and data models
  - [x] 2.1 Define DynamoDB table schema in CDK
    - Create MasterEventTimeline table with Day (PK) and Timestamp (SK)
    - Add Global Secondary Index: domain-timestamp-index
    - Configure encryption at rest and point-in-time recovery
    - _Requirements: 5.1, 5.3, 5.4, 5.5_

  - [x] 2.2 Create TypeScript interfaces for data models
    - Define EventItem interface matching DynamoDB schema
    - Create request/response interfaces for all API endpoints
    - Define MapLayer, Alert, and GeoJSON feature interfaces
    - Add validation schemas using Zod or similar
    - _Requirements: 1.5, 2.5, 3.5, 4.4_

  - [x] 2.3 Implement data access layer utilities
    - Create DynamoDB client wrapper with connection reuse
    - Implement query functions for time-range and domain filtering
    - Add batch write utilities for data population
    - Create helper functions for transforming DB records to API responses
    - _Requirements: 2.4, 5.2_

- [x] 3. Build data population script
  - [x] 3.1 Create simulation data generation script
    - Write script to generate 7-day simulation timeline with diverse events
    - Include events across all domains (MEDICAL, FIRE, STRUCTURAL, LOGISTICS, COMMUNICATION)
    - Generate events with varying severity levels and GeoJSON geometries
    - Add realistic timestamps distributed across 7 days
    - _Requirements: 5.1_

  - [x] 3.2 Implement database population logic
    - Create script to batch-write events to DynamoDB
    - Partition events by day (DAY_0 through DAY_6)
    - Validate data before insertion
    - Add progress logging and error handling
    - _Requirements: 5.1, 5.2_

- [x] 4. Implement updatesHandlerLambda
  - [x] 4.1 Create Lambda function for GET /data/updates
    - Set up Lambda handler with TypeScript
    - Implement query parameter parsing and validation
    - Add logic to query DynamoDB with since timestamp filter
    - Implement optional domain filtering using GSI
    - _Requirements: 1.4, 2.1, 2.2, 2.3_

  - [x] 4.2 Transform database results to API response format
    - Convert EventItem records to MapLayer structures
    - Group events by layer type (incidents, resources, alerts)
    - Apply appropriate styling based on event properties
    - Generate GeoJSON FeatureCollections
    - Extract critical alerts from high-severity events
    - _Requirements: 1.5, 2.5_

  - [x] 4.3 Add error handling and logging
    - Implement try-catch blocks for DynamoDB operations
    - Add structured logging to CloudWatch
    - Handle edge cases (no results, invalid parameters)
    - Return appropriate HTTP status codes
    - _Requirements: 2.4, 7.6_

- [x] 5. Create databaseQueryToolLambda for Bedrock Agent
  - [x] 5.1 Implement tool Lambda function
    - Create Lambda handler that accepts structured parameters from Bedrock
    - Parse tool input (domain, severity, startTime, endTime, location filters)
    - Build DynamoDB query based on provided filters
    - Execute query and return raw results to agent
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 5.2 Add location-based filtering logic
    - Implement geospatial filtering for location queries
    - Calculate distance between coordinates for radius queries
    - Filter results based on proximity to specified location
    - _Requirements: 6.2, 6.3_

  - [x] 5.3 Implement error handling for tool Lambda
    - Handle invalid parameters gracefully
    - Return structured error messages to agent
    - Log tool invocations for debugging
    - _Requirements: 6.4, 6.5_

- [x] 6. Configure Amazon Bedrock Agent
  - [x] 6.1 Create Bedrock Agent in AWS Console or CDK
    - Set up agent with Claude 3 Sonnet model
    - Configure agent name and description
    - Set agent timeout and resource limits
    - _Requirements: 3.1, 3.2_

  - [x] 6.2 Write and configure agent instruction prompt
    - Create detailed instruction prompt defining agent persona
    - Include guidelines for map visualization control
    - Specify response structure requirements
    - Add examples of good responses
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 6.3 Create Action Group for database queries
    - Define Action Group named "databaseQueryTool"
    - Create OpenAPI schema for tool parameters
    - Associate Action Group with databaseQueryToolLambda
    - Configure tool description for agent understanding
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 6.4 Test agent in Bedrock console
    - Test basic queries in Bedrock playground
    - Verify tool invocation works correctly
    - Test various query types (domain filters, time ranges, locations)
    - Refine instruction prompt based on test results
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Implement queryHandlerLambda
  - [x] 7.1 Create Lambda function for POST /agent/query
    - Set up Lambda handler with TypeScript
    - Implement request body parsing and validation
    - Add AWS SDK code to invoke Bedrock Agent
    - Pass user text and optional context to agent
    - _Requirements: 1.4, 3.1, 3.2_

  - [x] 7.2 Transform agent output to API response format
    - Parse agent's response
    - Construct full response structure with all required fields
    - Add simulationTime and timestamp
    - Set mapAction (REPLACE or APPEND)
    - Format mapLayers with proper styling
    - Add viewState for map control
    - Include uiContext with suggested actions
    - _Requirements: 3.4, 3.5_

  - [x] 7.3 Handle agent errors and timeouts
    - Implement timeout handling for long-running agent queries
    - Handle agent invocation failures gracefully
    - Return partial responses when possible
    - Log agent interactions for debugging
    - _Requirements: 3.6, 7.6_

- [x] 8. Implement actionHandlerLambda
  - [x] 8.1 Create Lambda function for POST /agent/action
    - Set up Lambda handler with TypeScript
    - Implement actionId to query intent mapping
    - Parse action payload parameters
    - _Requirements: 1.4, 4.1, 4.2_

  - [x] 8.2 Construct prompts for pre-defined actions
    - Map common actionIds to specific prompts
    - Include payload context in prompts
    - Invoke Bedrock Agent with constructed prompt
    - _Requirements: 4.2, 4.3_

  - [x] 8.3 Transform agent output to API response
    - Use same transformation logic as queryHandlerLambda
    - Ensure response format matches data contract
    - Handle action-specific response formatting
    - _Requirements: 4.4_

  - [x] 8.4 Add validation for actionIds
    - Validate actionId against known actions
    - Return clear error for invalid actionIds
    - Log action executions
    - _Requirements: 4.5_

- [x] 9. Set up API Gateway
  - [x] 9.1 Create REST API in CDK
    - Define API Gateway REST API resource
    - Configure API name and description
    - Set up API stages (dev, prod)
    - _Requirements: 1.1, 1.2_

  - [x] 9.2 Configure API routes and integrations
    - Create GET /data/updates route → updatesHandlerLambda
    - Create POST /agent/query route → queryHandlerLambda
    - Create POST /agent/action route → actionHandlerLambda
    - Configure Lambda proxy integrations
    - _Requirements: 1.4_

  - [x] 9.3 Set up CORS configuration
    - Set up CORS with appropriate origins for dashboard
    - Configure request/response models
    - Add basic request validation
    - _Requirements: 1.3_

- [x] 10. Add monitoring and logging
  - [x] 10.1 Configure CloudWatch logging
    - Enable CloudWatch Logs for all Lambda functions
    - Set log retention policies
    - Add structured logging to Lambda code
    - Configure API Gateway access logs
    - _Requirements: 7.6_

  - [x] 10.2 Create CloudWatch dashboard with cost controls
    - Add metrics for API Gateway (requests, latency, errors)
    - Add metrics for Lambda (invocations, duration, errors)
    - Add metrics for DynamoDB (read/write capacity, throttles)
    - Create billing alarm to shut down resources if costs exceed $50
    - Set up SNS topic for cost alert notifications
    - Configure automatic resource termination on budget breach
    - _Requirements: 7.3, 7.4, 7.5_

- [x] 11. Write deployment and testing scripts
  - [x] 11.1 Create CDK deployment script
    - Write script to deploy full stack with single command
    - Add environment variable configuration
    - Include post-deployment validation
    - _Requirements: 7.1_

  - [x] 11.2 Create data population script
    - Write script to populate DynamoDB after deployment
    - Add validation to check data was inserted correctly
    - Include rollback capability
    - _Requirements: 5.1_

  - [x] 11.3 Write integration test suite
    - Create tests for each API endpoint
    - Test with various query parameters and payloads
    - Verify response formats match data contracts
    - Test error scenarios
    - _Requirements: 1.5, 2.5, 3.5, 4.4_

  - [x] 11.4 Create end-to-end test script
    - Test complete flow from API Gateway to DynamoDB
    - Test agent query flow with tool invocation
    - Measure and validate response times
    - Test with concurrent requests
    - _Requirements: 7.3, 7.4_

- [x] 12. Documentation and final integration
  - [x] 12.1 Write API documentation
    - Document all endpoints with request/response examples
    - Include authentication instructions
    - Add error code reference
    - Create Postman collection or OpenAPI spec
    - _Requirements: 1.1, 1.5_

  - [x] 12.2 Create deployment guide
    - Write step-by-step deployment instructions
    - Document required AWS permissions
    - Include troubleshooting section
    - Add configuration reference
    - _Requirements: 7.1_

  - [x] 12.3 Integrate with Command Center Dashboard
    - Provide API endpoint URL and API key to frontend team
    - Test integration with actual dashboard
    - Verify all data contracts work correctly
    - Conduct end-to-end testing with dashboard
    - _Requirements: 1.1, 1.5, 2.5, 3.5, 4.4_
