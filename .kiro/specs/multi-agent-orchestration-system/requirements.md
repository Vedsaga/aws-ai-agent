# Requirements Document

## Introduction

This document defines the requirements for a Multi-Agent Orchestration System designed for civic engagement, disaster response, and domain-agnostic data processing. The system enables users to submit unstructured reports (text + images) within a selected domain, which are processed by specialized AI agents to extract structured data. Users can then query this data through natural language questions, with responses generated from multiple analytical perspectives (interrogative agents). The architecture is built on AWS services, emphasizing multi-tenancy, real-time status updates, API-first design for easy client integration, and reproducible deployment through Infrastructure as Code. The system prioritizes technical execution, scalability, and clear demonstration of end-to-end agentic workflows.

## Glossary

- **System**: The Multi-Agent Orchestration System
- **User**: A tenant (citizen, admin, analyst, NGO) interacting with the System
- **Agent**: An AI-powered Lambda function that processes data or queries with a specific focus
- **Ingestion Agent**: An Agent that extracts structured data from raw user input
- **Query Agent**: An Agent that analyzes stored data from a specific interrogative perspective
- **Interrogative**: A question word (When, Where, Why, How, What, Who, Which, etc.) defining an analytical perspective
- **Playbook**: A domain-specific configuration defining which Agents to use for data processing
- **Dependency Graph**: A configuration defining execution order where an Agent waits for a parent Agent's output
- **Domain**: A use case context (e.g., Civic Complaints, Disaster Response) with associated Playbooks
- **Tool**: An external service or API (Amazon Location, AWS Comprehend, Web Search) that Agents can invoke
- **Tool Registry**: A centralized catalog of available Tools with access control
- **Orchestrator**: The workflow engine that executes Agents according to Dependency Graphs
- **Image Evidence**: An image file attached to a report for visual reference, stored but not processed by Agents
- **Tenant**: An isolated organizational unit with dedicated data partitions
- **JWT Token**: JSON Web Token containing User authentication and role information
- **AppSync**: AWS service providing WebSocket connections for real-time status updates
- **Bedrock**: AWS service providing LLM capabilities for Agents and chat
- **Point**: A single analytical output from a Query Agent (1-2 line insight)

## Requirements

### Requirement 1: User Authentication and Multi-Tenancy

**User Story:** As a User, I want to securely log in and have my data isolated from other tenants, so that my information remains private and secure.

#### Acceptance Criteria

1. WHEN a User submits login credentials, THE System SHALL authenticate via AWS Cognito and return a JWT Token containing tenant_id
2. WHEN a User makes an API request, THE System SHALL validate the JWT Token at API Gateway before processing
3. THE System SHALL partition all database tables by tenant_id to ensure data isolation
4. THE System SHALL maintain session state in DynamoDB with session_id and chat_id per User
5. THE System SHALL provide RESTful APIs at /api/v1/* endpoints for client-side integration

### Requirement 2: Domain Selection and Data Ingestion

**User Story:** As a Citizen, I want to select a domain and submit text reports with optional image evidence, so that the System can extract and store structured information.

#### Acceptance Criteria

1. WHEN a User submits a report, THE System SHALL require the User to select a Domain from available options before processing
2. WHEN a User submits a report via the chat interface, THE System SHALL accept text input and optionally one or more image files
3. THE System SHALL store image files as evidence linked to the report without processing them through Agents
4. THE System SHALL route the text input to the /api/v1/ingest endpoint with JWT Token validation and selected Domain identifier
5. THE System SHALL load the Domain's configured Playbook from the Configuration Store to determine which Ingestion Agents to execute

### Requirement 3: Agent Execution and Tool Access

**User Story:** As a System Administrator, I want Agents to access only authorized Tools, so that security and cost controls are enforced.

#### Acceptance Criteria

1. WHEN an Agent requests a Tool, THE System SHALL verify permissions via the Tool Access Control Layer before granting access
2. THE System SHALL maintain a Tool Registry containing Amazon Location Service, Web Search API, AWS Comprehend, Custom Domain APIs, Data Query APIs, and Vector Search
3. THE System SHALL enforce per-Agent Tool permissions defined in the Configuration Store
4. THE System SHALL execute Agents as AWS Lambda functions with appropriate IAM roles
5. THE System SHALL limit each Agent's output to a maximum of 5 JSON keys

### Requirement 4: Real-Time Status Broadcasting

**User Story:** As a User, I want to see real-time updates on Agent execution progress, so that I understand what the System is doing with my request.

#### Acceptance Criteria

1. WHEN the Orchestrator starts Agent execution, THE System SHALL publish status messages to AWS AppSync via WebSocket
2. THE System SHALL broadcast status updates at key checkpoints: loading Agents, invoking each Agent, calling Tools, validating outputs, and synthesizing results
3. THE System SHALL deliver status messages to the User's chat interface within 500 milliseconds of event occurrence
4. THE System SHALL include Agent name and current action in each status message
5. THE System SHALL maintain one WebSocket connection per authenticated User session

### Requirement 5: Data Validation and Synthesis

**User Story:** As a System Administrator, I want Agent outputs to be validated and synthesized into coherent structured data, so that data quality is maintained.

#### Acceptance Criteria

1. WHEN all Ingestion Agents complete execution, THE System SHALL validate each Agent's output against its defined schema
2. THE System SHALL cross-check outputs for consistency across Agents
3. THE System SHALL synthesize validated outputs into a single JSON document
4. THE System SHALL store the synthesized JSON in PostgreSQL partitioned by tenant_id
5. THE System SHALL create vector embeddings and store them in the Vector Database partitioned by tenant_id

### Requirement 6: Query Pipeline with Interrogative Agents

**User Story:** As an Admin, I want to ask natural language questions about collected data and receive multi-perspective analysis, so that I can gain comprehensive insights.

#### Acceptance Criteria

1. WHEN a User submits a question via the chat interface, THE System SHALL route the request to the /api/v1/query endpoint with JWT Token validation
2. THE System SHALL load the User's configured Query Playbook to determine which Query Agents to execute
3. THE System SHALL provide built-in Query Agents for interrogatives: When, Where, Why, How, What, Who, Which, How many, How much, From where, and What kind
4. THE System SHALL execute Query Agents in parallel by default, respecting single-level Dependency Graph constraints
5. THE System SHALL pass raw question text to all Query Agents, and SHALL append parent Agent output to dependent Agents

### Requirement 7: Agent Execution with Dependency Management

**User Story:** As a System, I want to execute Ingestion Agents in the correct order based on dependencies, so that dependent Agents receive necessary parent outputs.

#### Acceptance Criteria

1. THE System SHALL execute Ingestion Agents in parallel by default when no dependencies are declared
2. WHEN an Ingestion Agent has a declared dependency, THE System SHALL wait for the parent Agent's output before invoking the dependent Agent
3. THE System SHALL pass raw user text to all Ingestion Agents
4. WHEN an Agent depends on a parent Agent, THE System SHALL append the parent Agent's output to the raw text input
5. THE System SHALL enforce single-level dependency hierarchy preventing multi-level dependency chains

### Requirement 8: Query Agent Auto-Generation and Schema Awareness

**User Story:** As a User creating a Domain, I want Query Agents to automatically understand my Ingestion Agent schemas, so that queries are contextually relevant.

#### Acceptance Criteria

1. WHEN a User selects an interrogative for a Domain, THE System SHALL auto-generate a Query Agent with a system prompt matching the interrogative perspective
2. THE System SHALL link the Query Agent to all Ingestion Agent schemas from the associated Domain
3. THE System SHALL auto-assign appropriate Tools to the Query Agent based on the interrogative type
4. THE System SHALL allow Users to customize auto-generated Query Agents including system prompts, Tool access, and dependencies
5. THE System SHALL store Query Agent configurations in the Configuration Store partitioned by tenant_id

### Requirement 9: Response Formation with Bullet Points and Summary

**User Story:** As a User, I want query responses formatted as concise bullet points with a summary, so that I can quickly understand insights from multiple analytical perspectives.

#### Acceptance Criteria

1. WHEN all Query Agents complete execution, THE System SHALL generate one bullet point per Query Agent containing 1-2 lines of insight
2. THE System SHALL aggregate all bullet points in the order of Agent execution
3. THE System SHALL generate a summary synthesizing insights from all Query Agents
4. THE System SHALL format the response as: bullet points followed by summary
5. THE System SHALL optionally generate visualizations via the Visualization Generator and update the map view

### Requirement 10: Custom Agent and Domain Creation

**User Story:** As a Power User, I want to create custom Agents and Domains with specific Tool access and execution dependencies, so that I can tailor the System to my unique use case.

#### Acceptance Criteria

1. THE System SHALL provide a configuration interface at /api/v1/config for creating custom Agents
2. WHEN a User creates a custom Agent, THE System SHALL allow specification of: Agent name, system prompt, Tool permissions, output schema (max 5 keys), and single-level dependency on one parent Agent
3. THE System SHALL provide a configuration interface for creating custom Domains (Playbooks)
4. WHEN a User creates a Domain, THE System SHALL allow selection of Ingestion Agents and Query Agents from built-in and custom Agents
5. THE System SHALL store all custom configurations in the Configuration Store partitioned by tenant_id with no cross-tenant sharing

### Requirement 11: Dependency Graph Visualization and Management

**User Story:** As a User, I want to visualize and manage Agent execution dependencies in a graphical interface, so that I can understand and control workflow complexity.

#### Acceptance Criteria

1. THE System SHALL provide a visual Dependency Graph editor similar to n8n workflow builder
2. THE System SHALL display Agents as nodes and dependencies as directed edges
3. WHEN a User attempts to create a multi-level dependency chain, THE System SHALL prevent the action and display an error message
4. THE System SHALL allow Users to define single-level dependencies where an Agent depends on exactly one parent Agent
5. THE System SHALL store Dependency Graph configurations separately from Playbook configurations in the Configuration Store

### Requirement 12: Tool Registry Management

**User Story:** As a System Administrator, I want to register and manage Tools in a centralized registry, so that Agents can discover and use available integrations.

#### Acceptance Criteria

1. THE System SHALL provide an interface at /api/v1/tools for registering new Tools
2. WHEN a Tool is registered, THE System SHALL store Tool metadata including name, endpoint, authentication method, and description in the Tool Catalog
3. THE System SHALL allow Administrators to define per-Agent Tool permissions in the Tool Access Control Layer
4. THE System SHALL support the following built-in Tools: Amazon Location Service, Web Search API, AWS Comprehend, Custom Domain APIs, Data Query APIs, and Vector Search
5. THE System SHALL validate Tool availability before Agent execution and SHALL fail gracefully if a required Tool is unavailable

### Requirement 13: Data Persistence and Retrieval APIs

**User Story:** As a Developer, I want structured APIs for data access, so that Agents, client applications, and external systems can query data without direct database access.

#### Acceptance Criteria

1. THE System SHALL provide four Data Service APIs: Retrieval API, Aggregation API, Spatial Query API, and Analytics API
2. THE Retrieval API SHALL support filtering incidents by date range, location, category, and User-defined fields, and SHALL return associated image evidence URLs
3. THE Aggregation API SHALL provide statistics and summaries including counts, averages, and distributions
4. THE Spatial Query API SHALL support geospatial queries including radius search, bounding box, and polygon intersection
5. THE Analytics API SHALL provide trend detection and pattern recognition across temporal and spatial dimensions

### Requirement 14: Real-Time Map Visualization Updates

**User Story:** As a User, I want the map view to automatically update when new data is ingested, so that I see the latest information without manual refresh.

#### Acceptance Criteria

1. WHEN the System stores new structured data in PostgreSQL, THE System SHALL trigger an EventBridge event
2. THE EventBridge event SHALL route to the map update handler
3. THE System SHALL push map updates to connected Users via AppSync WebSocket
4. THE System SHALL update map markers within 2 seconds of data ingestion completion
5. THE System SHALL display 80% of the UI as map visualization and 20% as chat interface

### Requirement 15: Configuration Store Schema and Management

**User Story:** As a System Administrator, I want all configurations stored in a structured schema, so that the System is reproducible and auditable.

#### Acceptance Criteria

1. THE System SHALL store eight configuration types in the Configuration Store: Agent Configurations, Playbook Configurations, Dependency Graph Configurations, Tool Permissions, Output Schemas, Example Outputs, Domain Templates, and UI Templates
2. THE System SHALL partition the Configuration Store by tenant_id
3. THE System SHALL provide CRUD operations for all configuration types via /api/v1/config endpoint
4. THE System SHALL validate configuration changes against schema definitions before persisting
5. THE System SHALL maintain configuration version history for audit and rollback purposes

### Requirement 16: Scalability and Serverless Architecture

**User Story:** As a System Operator, I want the System to automatically scale with demand, so that performance remains consistent during usage spikes.

#### Acceptance Criteria

1. THE System SHALL implement all Agents as AWS Lambda functions with automatic concurrency scaling
2. THE System SHALL use API Gateway with throttling limits to protect backend services
3. THE System SHALL partition PostgreSQL tables by tenant_id to enable horizontal scaling
4. THE System SHALL use DynamoDB for session storage to leverage automatic scaling
5. THE System SHALL implement asynchronous Agent execution to prevent API Gateway timeout issues

### Requirement 17: Infrastructure as Code and Reproducible Deployment

**User Story:** As a Developer, I want to deploy the entire System using Infrastructure as Code, so that the architecture is reproducible and well-documented for judges and users.

#### Acceptance Criteria

1. THE System SHALL provide AWS CDK or CloudFormation templates defining all infrastructure components
2. THE deployment process SHALL complete in under 30 minutes from a single command execution
3. THE System SHALL include a deployment guide with prerequisites, step-by-step instructions, and verification steps
4. THE System SHALL configure all AWS service integrations including Cognito, API Gateway, Lambda, AppSync, Bedrock, Comprehend, Location Service, RDS PostgreSQL, and DynamoDB
5. THE System SHALL provide sample Domain configurations and test data for demonstration purposes
