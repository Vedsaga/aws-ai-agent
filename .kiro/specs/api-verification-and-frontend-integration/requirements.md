# Requirements Document - API Verification and Frontend Integration

## Introduction

With 2 hours remaining before the hackathon deadline, we need to verify all AWS APIs are working correctly and ensure the frontend is properly integrated. This is critical for winning the hackathon.

## Glossary

- **API Gateway**: AWS API Gateway endpoint hosting REST APIs
- **Frontend**: Next.js React application in infrastructure/frontend
- **Config API**: API for managing agents and domain configurations
- **Ingest API**: API for submitting incident reports
- **Query API**: API for asking natural language questions
- **Data API**: API for retrieving stored incident data
- **Tools API**: API for managing tool registry
- **JWT Token**: JSON Web Token from AWS Cognito for authentication
- **AppSync**: AWS AppSync GraphQL API for real-time updates (not deployed)

## Requirements

### Requirement 1: API Verification

**User Story:** As a developer, I want to verify all deployed APIs are working correctly, so that I can confidently integrate them into the frontend.

#### Acceptance Criteria

1. WHEN the developer runs API verification tests, THE System SHALL return HTTP 200/201/202 status codes for all working endpoints
2. WHEN the developer tests the Config API, THE System SHALL successfully list agents, create agents, and manage configurations
3. WHEN the developer tests the Ingest API, THE System SHALL accept report submissions and return job IDs
4. WHEN the developer tests the Query API, THE System SHALL accept questions and return job IDs
5. WHEN the developer tests authentication, THE System SHALL properly validate JWT tokens and reject unauthorized requests

### Requirement 2: API Response Validation

**User Story:** As a developer, I want to understand the exact request/response format for each API, so that I can implement correct frontend integration.

#### Acceptance Criteria

1. WHEN the developer examines Config API responses, THE System SHALL return agent objects with agent_id, agent_name, agent_type, and is_builtin fields
2. WHEN the developer examines Ingest API responses, THE System SHALL return job_id and status fields with 202 Accepted status
3. WHEN the developer examines Query API responses, THE System SHALL return job_id and estimated_completion_seconds fields
4. WHEN the developer examines error responses, THE System SHALL return consistent error format with error message and timestamp
5. WHEN the developer tests Data API, THE System SHALL return data array and count fields

### Requirement 3: Frontend API Client Verification

**User Story:** As a developer, I want to verify the frontend API client is correctly configured, so that API calls work from the browser.

#### Acceptance Criteria

1. WHEN the frontend loads, THE Frontend SHALL successfully initialize Amplify with correct Cognito configuration
2. WHEN the frontend makes API requests, THE Frontend SHALL include valid JWT tokens in Authorization headers
3. WHEN API requests fail, THE Frontend SHALL display appropriate error messages to users
4. WHEN API requests succeed, THE Frontend SHALL parse responses correctly and update UI state
5. WHEN network errors occur, THE Frontend SHALL retry requests with exponential backoff

### Requirement 4: Critical API Endpoints Integration

**User Story:** As a user, I want to submit reports and ask questions through the frontend, so that I can interact with the multi-agent system.

#### Acceptance Criteria

1. WHEN the user submits a report, THE Frontend SHALL call POST /api/v1/ingest with domain_id and text fields
2. WHEN the user asks a question, THE Frontend SHALL call POST /api/v1/query with domain_id and question fields
3. WHEN the user views agents, THE Frontend SHALL call GET /api/v1/config?type=agent to list available agents
4. WHEN the user creates an agent, THE Frontend SHALL call POST /api/v1/config with type and config fields
5. WHEN API calls complete, THE Frontend SHALL display success notifications with job IDs

### Requirement 5: Environment Configuration Validation

**User Story:** As a developer, I want to ensure all environment variables are correctly configured, so that the frontend can connect to AWS services.

#### Acceptance Criteria

1. WHEN the frontend starts, THE System SHALL verify NEXT_PUBLIC_API_URL is set to the correct API Gateway endpoint
2. WHEN authentication is required, THE System SHALL verify NEXT_PUBLIC_COGNITO_USER_POOL_ID and NEXT_PUBLIC_COGNITO_CLIENT_ID are configured
3. WHEN environment variables are missing, THE System SHALL log clear error messages indicating which variables are missing
4. WHEN the developer checks configuration, THE System SHALL provide a way to test connectivity to all required services
5. WHEN configuration is correct, THE System SHALL successfully authenticate and make API calls

### Requirement 6: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when operations succeed or fail, so that I understand what's happening with my requests.

#### Acceptance Criteria

1. WHEN an API call succeeds, THE Frontend SHALL display a success toast notification with relevant details
2. WHEN an API call fails with 401, THE Frontend SHALL display "Session expired" message and prompt re-login
3. WHEN an API call fails with 400, THE Frontend SHALL display validation error details from the API response
4. WHEN an API call fails with 500, THE Frontend SHALL display "Server error" message and suggest retry
5. WHEN network connectivity fails, THE Frontend SHALL display "Network error" message and automatically retry

### Requirement 7: Demo Readiness Verification

**User Story:** As a presenter, I want to verify the complete end-to-end flow works, so that I can confidently demonstrate the system.

#### Acceptance Criteria

1. WHEN the presenter logs in, THE System SHALL successfully authenticate and load the dashboard
2. WHEN the presenter submits a test report, THE System SHALL accept it and return a job ID within 2 seconds
3. WHEN the presenter asks a test question, THE System SHALL accept it and return a job ID within 2 seconds
4. WHEN the presenter views agents, THE System SHALL display at least 5 built-in agents (geo, temporal, entity, what, where, when)
5. WHEN the presenter creates a custom agent, THE System SHALL successfully create it and display it in the agent list
