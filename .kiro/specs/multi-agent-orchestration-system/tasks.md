# Implementation Plan

This document outlines the implementation tasks for the Multi-Agent Orchestration System. Tasks are organized incrementally, with each task building on previous work. All tasks focus on code implementation, testing, and integration.

## Task Execution Notes

- Each task references specific requirements from requirements.md
- Tasks are numbered with decimal notation for sub-tasks
- Sub-tasks marked with `*` are optional (testing, documentation)
- Execute tasks in order for incremental progress
- All context documents (requirements, design, diagrams) are available during implementation

## Demo Strategy for Hackathon

**Goal**: Maximize judging criteria scores (Technical Execution 50%, Value 20%, Functionality 10%, Creativity 10%, Demo 10%)

**Approach**:
1. **Pre-built Custom Agent**: Hard-code "Severity Classifier" in seed data to show system working
2. **Live Agent Creation**: Build dashboard UI to create custom agents during demo
3. **Demo Flow**: Show existing system → Query data → Create "Priority Scorer" agent live → Test new agent
4. **Key Highlights**: AWS services, reproducibility (CDK), extensibility (custom agents), real-time updates, multi-domain support

**Why This Works**:
- Demonstrates technical execution (well-architected, reproducible)
- Shows functionality (agents working, scalable)
- Highlights creativity (interrogative agents, live customization)
- Proves value/impact (civic engagement, disaster response)
- Clear demo presentation (end-to-end agentic workflow)

---

## Phase 1: Infrastructure & Core Services

- [x] 1. Set up AWS CDK project structure and core infrastructure
  - Create CDK TypeScript project with proper folder structure
  - Define stack organization (auth, api, data, agents, orchestration)
  - Configure AWS account and region settings
  - Set up environment variables and parameter store structure
  - _Requirements: 17.1, 17.2_

- [x] 1.1 Implement authentication stack with Cognito
  - Create Cognito User Pool with password policies
  - Configure JWT token settings (1 hour access, 30 day refresh)
  - Add custom `tenant_id` claim to JWT
  - Create Lambda authorizer for API Gateway
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Implement API Gateway stack with 5 endpoints
  - Create REST API Gateway with custom domain
  - Define `/api/v1/ingest` POST endpoint
  - Define `/api/v1/query` POST endpoint
  - Define `/api/v1/data` GET endpoint
  - Define `/api/v1/config` POST/GET endpoints
  - Define `/api/v1/tools` POST/GET endpoints
  - Attach Lambda authorizer to all endpoints
  - Configure CORS and request validation
  - _Requirements: 1.5, 2.4_

- [x] 1.3 Implement data persistence stack
  - Create RDS PostgreSQL instance with Multi-AZ
  - Define `incidents` table schema with tenant partitioning
  - Define `image_evidence` table schema with tenant partitioning
  - Create indexes on tenant_id, domain_id, created_at
  - Create GIN index on structured_data JSONB column
  - Enable PostGIS extension for spatial queries
  - _Requirements: 5.4, 5.5_

- [x] 1.4 Create OpenSearch domain for vector search
  - Provision OpenSearch cluster (2 nodes, t3.medium)
  - Define `incident_embeddings` index mapping with knn_vector
  - Configure tenant_id filtering
  - Set up index lifecycle policies
  - _Requirements: 5.5_

- [x] 1.5 Create DynamoDB tables for configuration and sessions
  - Create `configurations` table (PK: tenant_id, SK: config_type#config_id)
  - Create GSI for config_type queries
  - Create `user_sessions` table (PK: user_id, SK: session_id)
  - Enable TTL on user_sessions
  - Create `tool_catalog` table (PK: tool_name)
  - Create `tool_permissions` table (PK: tenant_id#agent_id, SK: tool_name)
  - _Requirements: 1.4, 15.2_

- [x] 1.6 Create S3 buckets for image storage
  - Create evidence bucket with tenant_id prefix structure
  - Enable versioning and encryption at rest
  - Configure lifecycle policies for old images
  - Set up bucket policies for tenant isolation
  - _Requirements: 2.3_

---

## Phase 2: Agent Implementation

- [x] 2. Implement base agent Lambda function framework
  - Create Python base class for all agents
  - Implement standard input/output interface
  - Add tool invocation framework
  - Implement output schema validation (max 5 keys)
  - Add error handling and timeout management
  - _Requirements: 3.5, 8.4_

- [x] 2.1 Implement Geo Agent (ingestion)
  - Create Lambda function with Bedrock and Location Service integration
  - Implement system prompt for location extraction
  - Add Amazon Location Service geocoding
  - Add web search fallback for ambiguous locations
  - Validate output against 5-key schema
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.2 Implement Temporal Agent (ingestion)
  - Create Lambda function with Bedrock integration
  - Implement system prompt for time/date extraction
  - Parse relative time expressions (today, yesterday, last week)
  - Convert to ISO timestamps
  - Validate output against 5-key schema
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.3 Implement Entity Agent (ingestion)
  - Create Lambda function with Bedrock and Comprehend integration
  - Implement system prompt for entity extraction
  - Call AWS Comprehend for named entities
  - Extract sentiment and key phrases
  - Validate output against 5-key schema
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2.4 Implement 11 interrogative query agents
  - Create When Agent (temporal analysis)
  - Create Where Agent (spatial analysis)
  - Create Why Agent (causal analysis)
  - Create How Agent (method analysis)
  - Create What Agent (entity analysis)
  - Create Who Agent (person analysis)
  - Create Which Agent (selection analysis)
  - Create How Many Agent (count analysis)
  - Create How Much Agent (quantity analysis)
  - Create From Where Agent (origin analysis)
  - Create What Kind Agent (type analysis)
  - Each agent: Bedrock integration, Data API calls, 5-key output validation
  - _Requirements: 6.3, 6.4, 6.5, 8.1, 8.2_

- [x] 2.5 Implement custom agent creation framework
  - Create Lambda function for custom agent deployment
  - Support user-defined system prompts
  - Support user-selected tools from registry
  - Support user-defined output schemas (max 5 keys)
  - Support single-level dependency declaration
  - Hard-code "Severity Classifier" custom agent in seed data (depends on Entity Agent)
  - Verify Severity Classifier executes in ingestion pipeline
  - _Requirements: 10.2, 10.5_
  - _Demo: Pre-built custom agent working in pipeline_

---

## Phase 3: Tool Registry & Access Control

- [x] 3. Implement tool registry management
  - Create Lambda function for tool registration
  - Implement CRUD operations for tool catalog
  - Store tool metadata in DynamoDB
  - Support built-in and custom tools
  - _Requirements: 12.1, 12.2, 12.5_

- [x] 3.1 Implement tool access control layer
  - Create ACL checker Lambda function
  - Implement permission verification against DynamoDB
  - Add in-memory caching (5 min TTL)
  - Return tool metadata and credentials
  - _Requirements: 3.1, 3.2, 3.3, 12.3_

- [x] 3.2 Implement tool proxy functions
  - Create Bedrock proxy Lambda (IAM auth)
  - Create Comprehend proxy Lambda (IAM auth)
  - Create Location Service proxy Lambda (IAM auth)
  - Create Web Search proxy Lambda (API key from Secrets Manager)
  - Create Custom API proxy Lambda (user credentials from Secrets Manager)
  - _Requirements: 3.4_

- [x] 3.3 Implement data access tool proxies
  - Create Retrieval API tool proxy
  - Create Aggregation API tool proxy
  - Create Spatial API tool proxy
  - Create Analytics API tool proxy
  - Create Vector Search tool proxy
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

---

## Phase 4: Orchestration Engine

- [x] 4. Implement Step Functions state machine for orchestration
  - Define state machine JSON for unified orchestrator
  - Implement LoadPlaybook Lambda task
  - Implement LoadDependencyGraph Lambda task
  - Implement BuildExecutionPlan Lambda task (topological sort)
  - Configure Map state for parallel agent execution
  - Add error handling and retry logic
  - _Requirements: 2.2, 2.3, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4.1 Implement agent invoker Lambda
  - Create function to route to specific agent by ID
  - Load agent configuration from DynamoDB
  - Pass raw text and optional parent output
  - Handle agent timeouts and errors
  - Return standardized output format
  - _Requirements: 7.3, 7.4_

- [x] 4.2 Implement result aggregation Lambda
  - Collect outputs from all executed agents
  - Preserve execution order
  - Handle partial failures
  - Prepare data for validation
  - _Requirements: 7.5_

- [x] 4.3 Implement validation Lambda
  - Load output schemas from DynamoDB
  - Validate each agent output against schema
  - Check max 5 keys constraint
  - Cross-validate consistency across agents
  - Return validation results with errors
  - _Requirements: 5.1, 5.2_

- [x] 4.4 Implement synthesis Lambda
  - Merge validated outputs into single JSON document
  - Resolve conflicts between agent outputs
  - Format for database storage
  - _Requirements: 5.3_

- [x] 4.5 Implement save results Lambda
  - Insert structured data into RDS PostgreSQL
  - Create embeddings using Bedrock
  - Index embeddings in OpenSearch
  - Store image metadata references
  - Trigger EventBridge event for map update
  - _Requirements: 5.4, 5.5_

---

## Phase 5: Data Access APIs

- [x] 5. Implement Retrieval API Lambda
  - Parse query parameters (domain_id, date_from, date_to, location, category)
  - Build SQL query with tenant_id filter
  - Execute query against RDS PostgreSQL
  - Include image URLs from S3
  - Return paginated results
  - _Requirements: 13.2_

- [x] 5.1 Implement Aggregation API Lambda
  - Parse query parameters (domain_id, group_by, metric, field)
  - Build aggregation SQL query
  - Execute against RDS PostgreSQL
  - Return grouped statistics
  - _Requirements: 13.3_

- [x] 5.2 Implement Spatial Query API Lambda
  - Parse spatial query parameters (query_type, center, radius, bbox, polygon)
  - Build PostGIS spatial query
  - Execute against RDS PostgreSQL
  - Calculate distances for radius queries
  - Return spatial results with coordinates
  - _Requirements: 13.4_

- [x] 5.3 Implement Analytics API Lambda
  - Parse analytics parameters (analysis_type, field, time_bucket)
  - Build time series or pattern analysis query
  - Execute against RDS PostgreSQL and OpenSearch
  - Calculate trends and correlations
  - Return analytics results with summary
  - _Requirements: 13.5_

---

## Phase 6: Configuration Management

- [x] 6. Implement configuration API Lambda
  - Handle POST/GET/PUT/DELETE for all config types
  - Validate configuration schemas before saving
  - Store in DynamoDB with versioning
  - Backup previous versions to S3
  - _Requirements: 15.3, 15.4, 15.5_

- [x] 6.1 Implement agent configuration management
  - CRUD operations for agent configs
  - Validate system prompts, tools, output schemas
  - Enforce max 5 keys in output schema
  - Validate single-level dependency
  - _Requirements: 10.2, 15.1_

- [x] 6.2 Implement playbook configuration management
  - CRUD operations for playbook configs
  - Validate agent_ids exist
  - Support ingestion and query playbook types
  - Link to domain_id
  - _Requirements: 10.3, 10.4, 15.1_

- [x] 6.3 Implement dependency graph configuration management
  - CRUD operations for dependency graph configs
  - Validate no circular dependencies
  - Validate no multi-level dependencies (single parent only)
  - Validate all agents exist in playbook
  - Generate execution levels via topological sort
  - _Requirements: 11.3, 11.4, 15.1_

- [x] 6.4 Implement domain template system
  - Create pre-built templates for Civic Complaints, Agriculture, Disaster Response
  - Include agent configs, playbooks, dependency graphs, UI templates
  - Implement template instantiation for new tenants
  - _Requirements: 10.5, 15.2_

---

## Phase 7: Real-Time Status & WebSocket

- [x] 7. Implement AppSync GraphQL API for real-time status
  - Define GraphQL schema with Mutation and Subscription
  - Create AppSync API with WebSocket support
  - Configure DynamoDB for connection tracking
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 7.1 Implement status publisher Lambda
  - Accept status messages from orchestrator and agents
  - Look up user connection_id in DynamoDB
  - Publish to AppSync via GraphQL mutation
  - Handle connection failures gracefully
  - _Requirements: 4.2, 4.4_

- [x] 7.2 Integrate status publishing into orchestrator
  - Add status publish calls at each Step Functions checkpoint
  - Publish: loading_agents, invoking_agent, agent_complete, validating, synthesizing, complete, error
  - Include agent name and current action in messages
  - _Requirements: 4.2, 4.5_

- [x] 7.3 Integrate status publishing into agents
  - Publish status when calling tools
  - Include tool name and reason in message
  - Publish completion status with execution time
  - _Requirements: 4.2_

---

## Phase 8: Query Pipeline & Response Formation

- [x] 8. Implement query pipeline orchestration
  - Reuse Step Functions orchestrator with query playbook
  - Load query agents based on user selection
  - Execute query agents with dependency support
  - Pass raw question text to all agents
  - Append parent output to dependent agents
  - _Requirements: 6.1, 6.2, 6.5_

- [x] 8.1 Implement response formatter Lambda
  - Collect all query agent outputs
  - Generate one bullet point per agent (1-2 lines)
  - Format with interrogative prefix (What:, Where:, etc.)
  - Preserve execution order
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 8.2 Implement summary generator
  - Use Bedrock to synthesize all agent insights
  - Generate 2-3 sentence summary
  - Combine bullets and summary into final response
  - _Requirements: 9.3, 9.4_

- [x] 8.3 Implement visualization generator
  - Check for spatial data in query results
  - Generate map update instructions if present
  - Create heatmap data for concentrations
  - Return visualization config
  - _Requirements: 9.5_

---

## Phase 9: RAG Integration

- [x] 9. Implement RAG engine Lambda
  - Accept context request from query agents
  - Create question embedding using Bedrock
  - Perform vector search in OpenSearch
  - Retrieve full incident data from RDS
  - Generate contextual response using Bedrock
  - Return context to query agent
  - _Requirements: 6.5, 8.1, 8.2_

---

## Phase 10: Frontend Integration

- [x] 10. Implement Next.js web application structure
  - Set up Next.js project with TypeScript
  - Configure Mapbox GL JS for map visualization (80% of UI)
  - Create chat interface component (20% of UI)
  - Set up AppSync WebSocket client
  - _Requirements: 14.5_

- [x] 10.1 Implement authentication flow
  - Create login page with Cognito integration
  - Store JWT token in secure cookie
  - Implement token refresh logic
  - Add logout functionality
  - _Requirements: 1.1, 1.2_

- [x] 10.2 Implement ingestion interface
  - Create domain selection dropdown
  - Create text input for report submission
  - Add image upload component (max 5 images, 5MB each)
  - Display real-time status updates via AppSync
  - Show success message with incident ID
  - _Requirements: 2.1, 2.3, 2.4_

- [x] 10.3 Implement query interface
  - Create question input field
  - Display real-time status updates during query processing
  - Render bullet point response
  - Display summary
  - Update map with query results if spatial data present
  - _Requirements: 6.1, 9.1, 9.2, 9.3, 9.5_

- [x] 10.4 Implement map visualization
  - Display incidents as markers on map
  - Cluster markers for better performance
  - Show incident details on marker click
  - Display images in popup
  - Update map in real-time via EventBridge events
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 10.5 Implement configuration UI for custom agent creation
  - Create agent creation form (name, type, system prompt, tools, output schema)
  - Add tool selection dropdown from registry
  - Add output schema builder (max 5 keys with types)
  - Add dependency selection (single parent agent)
  - Implement real-time validation (schema, dependencies)
  - Create dependency graph visual editor (React Flow library)
  - Show existing agents as nodes, allow drag-and-drop connections
  - Validate single-level dependencies (no multi-level chains)
  - Display validation errors clearly
  - Save new agent configuration to DynamoDB via API
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 11.1, 11.2_
  - _Demo: Live creation of "Priority Scorer" agent during presentation_

---

## Phase 11: Deployment & Testing

- [x] 11. Create deployment scripts
  - Write CDK deployment script with all stacks
  - Create seed data script for sample domains and agents
  - Write smoke test script to verify deployment
  - Document deployment steps in README
  - _Requirements: 17.2, 17.3, 17.4_

- [x] 11.1 Deploy to AWS environment
  - Run `cdk bootstrap` for AWS environment setup
  - Deploy all CDK stacks in correct order
  - Verify all resources created successfully
  - Run seed data script
  - _Requirements: 17.2, 17.5_

- [ ] 11.2 Execute end-to-end integration test and demo preparation
  - Test ingestion pipeline: Submit civic complaint with image
  - Verify Severity Classifier custom agent executes (hard-coded)
  - Verify real-time status updates
  - Verify data stored in RDS and OpenSearch
  - Verify map marker appears
  - Test query pipeline: Ask question about complaints
  - Verify query agents execute
  - Verify bullet point response format
  - Verify summary generation
  - **Demo Preparation**: Practice creating "Priority Scorer" agent via dashboard
  - Verify new agent appears in dependency graph editor
  - Test adding Priority Scorer to playbook and submitting new complaint
  - Verify Priority Scorer executes with dependency on Temporal Agent
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_
  - _Demo: End-to-end workflow including live custom agent creation_

- [ ]* 11.3 Performance testing
  - Test with 100 concurrent users
  - Verify Lambda scaling
  - Verify database connection pooling
  - Verify API Gateway throttling
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ]* 11.4 Create monitoring dashboards
  - Create CloudWatch dashboard for key metrics
  - Set up alarms for error rates
  - Configure X-Ray tracing
  - Document monitoring setup
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

---

## Phase 12: Documentation & Demo Preparation

- [ ]* 12. Create deployment documentation
  - Write comprehensive README with prerequisites
  - Document all environment variables
  - Create architecture diagrams for presentation
  - Write troubleshooting guide
  - _Requirements: 17.3_

- [ ]* 12.1 Prepare demo script for judges
  - **Part 1**: Show existing system working (2 min)
    - Submit civic complaint "Pothole on Main Street" with image
    - Show real-time status updates (agents executing)
    - Show Severity Classifier custom agent in action
    - Show map marker appear with incident details
  - **Part 2**: Query existing data (2 min)
    - Ask "What are the trends in pothole complaints?"
    - Show query agents executing (What, Where, When, Why)
    - Show bullet point response with summary
    - Show map visualization update
  - **Part 3**: Create new custom agent live (3 min)
    - Open configuration dashboard
    - Create "Priority Scorer" agent
    - Set system prompt: "Score complaint priority 1-10 based on severity and time"
    - Select tools: Bedrock
    - Define output schema: priority_score, reasoning, urgency, recommended_action, timeline
    - Set dependency: Depends on Temporal Agent
    - Save and add to Civic Complaints playbook
  - **Part 4**: Test new agent (2 min)
    - Submit new complaint
    - Show Priority Scorer executing after Temporal Agent
    - Show priority score in structured data
    - Highlight extensibility and reproducibility
  - Prepare presentation slides highlighting:
    - Technical execution (50%): AWS services, architecture, reproducibility
    - Functionality (10%): Agents working, scalable, extensible
    - Creativity (10%): Interrogative agents, dependency graphs, live customization
    - Value/Impact (20%): Multi-domain, civic engagement, disaster response
    - Demo quality (10%): Clear workflow, real-time updates, live agent creation
  - _Requirements: 17.5_
  - _Demo: 9-minute presentation maximizing all judging criteria_

- [ ]* 12.2 Create API documentation
  - Document all API endpoints with examples
  - Create Postman collection for testing
  - Write integration guide for external systems
  - _Requirements: 1.5_

---

## Notes

- Tasks are designed to be executed sequentially for incremental progress
- Each task builds on previous tasks
- Optional tasks (marked with `*`) can be skipped for MVP
- All tasks reference specific requirements for traceability
- Focus on core functionality first, optimization later
- Real-time status updates integrated throughout for demo clarity
