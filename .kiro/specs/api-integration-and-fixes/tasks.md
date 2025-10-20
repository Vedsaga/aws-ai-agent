# Implementation Plan

## Overview

This implementation plan converts the API integration and bug fixes design into actionable coding tasks. Tasks are organized by feature area and build incrementally. Each task focuses on writing, modifying, or testing code.

## Task List

- [x] 1. Fix network error and enhance API client
  - Fix initialization issue causing network errors on page refresh
  - Add retry logic with exponential backoff
  - Enhance error handling and toast notifications
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 1.1 Fix API client initialization
  - Add ensureInitialized() function to wait for auth session
  - Prevent multiple simultaneous initialization attempts
  - Update apiRequest() to call ensureInitialized() before fetching
  - Test that page refresh no longer shows network errors
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 1.2 Implement retry logic with exponential backoff
  - Create apiRequestWithRetry() function
  - Implement exponential backoff (1s, 2s, 4s, max 10s)
  - Retry only on 5xx errors or network failures
  - Limit to 3 retry attempts
  - _Requirements: 10.4, 11.4_

- [x] 1.3 Add agent and domain API functions
  - Add createAgent(), listAgents(), getAgent(), updateAgent(), deleteAgent()
  - Add createDomain(), listDomains(), getDomain(), updateDomain(), deleteDomain()
  - Use proper TypeScript interfaces for request/response
  - Add error handling with toast notifications
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 2. Implement agent management UI
  - Create agent list view with filtering
  - Create agent form dialog for CRUD operations
  - Add agent card component with tags
  - Integrate with backend APIs
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2.1 Create AgentListView component
  - Fetch agents from API on mount
  - Display agents in grid layout (3 columns)
  - Add filter tabs: All, Built-in, Custom
  - Show agent count badges
  - Add "Create Agent" button
  - _Requirements: 2.1, 4.1, 4.2_

- [x] 2.2 Create AgentCard component
  - Display agent name, type, and description
  - Show tags: "Built-in", "Created by me", agent type
  - Add Edit and Delete buttons (only for custom agents)
  - Style with dark mode colors
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 2.3 Create AgentFormDialog component
  - Add agent type toggle (Data Ingest Agent / Data Query Agent)
  - Add form fields: name, system prompt, tools, output schema
  - Add parent agent selector (for query agents only)
  - Add key-value editor for output schema (max 5 keys)
  - Add example JSON field (for ingest agents)
  - Validate form before submission
  - _Requirements: 2.2, 2.3, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 2.4 Implement agent CRUD operations
  - Wire up create agent functionality
  - Wire up update agent functionality
  - Wire up delete agent functionality with confirmation
  - Show success/error toasts
  - Refresh agent list after operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 2.5 Add agent management page route
  - Create /agents page
  - Add AgentListView component
  - Add navigation from dashboard
  - Test agent CRUD flow end-to-end
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 3. Implement two-stage domain creation
  - Create domain creation wizard with two stages
  - Add agent selection UI for both stages
  - Add dependency graph visualization
  - Enforce stage validation rules
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 12.1, 12.2, 12.3, 12.4, 12.5, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

- [x] 3.1 Create DomainCreationWizard component
  - Add two-stage layout with stage indicator
  - Add domain name and description fields
  - Add stage navigation (Next/Back buttons)
  - Disable Next button until stage requirements met
  - _Requirements: 17.1, 17.2, 17.3_

- [x] 3.2 Implement Stage 1: Ingest Agent Selection
  - Display all ingestion agents (built-in + custom)
  - Add checkbox selection for agents
  - Show selected count badge
  - Require at least one agent selected
  - Disable Next button if no agents selected
  - _Requirements: 17.1, 17.2, 17.3_

- [x] 3.3 Implement Stage 2: Query Agent Selection
  - Display all query agents (built-in + custom)
  - Add checkbox selection for agents
  - Show selected count badge
  - Require at least one agent selected
  - Disable Create button if no agents selected
  - _Requirements: 17.1, 17.2, 17.3_

- [x] 3.4 Create DependencyGraphVisualization component
  - Analyze selected agents for dependency_parent relationships
  - Display parallel execution agents in horizontal layout
  - Display sequential execution agents with arrows
  - Update graph in real-time as agents are selected/deselected
  - Show separate sections for Ingestion Layer and Query Layer
  - _Requirements: 17.4, 17.5, 17.6, 17.7_

- [x] 3.5 Implement domain creation API call
  - Build DomainConfig from selected agents
  - Call createDomain() API with agent_ids
  - Handle success with toast and navigation
  - Handle errors with toast
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 3.6 Update manage page to show all domains
  - Fetch all domains (built-in + custom)
  - Add tags: "Built-in", "Created by me", "Public"
  - Add "Ask Question" and "Submit Report" actions
  - Navigate to appropriate panel when action clicked
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4. Implement real-time execution status visualization
  - Create execution status panel component
  - Subscribe to AppSync WebSocket for status updates
  - Display agent execution chain with status indicators
  - Show confidence scores for completed agents
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

- [x] 4.1 Create ExecutionStatusPanel component
  - Display list of agents in execution order
  - Show status icon for each agent (waiting, invoking, complete, error)
  - Display status message below agent name
  - Show confidence score badge when complete
  - Style with dark mode colors
  - _Requirements: 18.1, 18.2, 18.3, 18.9_

- [x] 4.2 Implement WebSocket subscription
  - Create subscribeToStatusUpdates() helper function
  - Subscribe to onStatusUpdate GraphQL subscription
  - Pass jobId as subscription variable
  - Update component state on each status update
  - Handle subscription errors gracefully
  - _Requirements: 18.8_

- [x] 4.3 Add status update handling
  - Update agent status when "invoking" message received
  - Update agent status when "calling_tool" message received
  - Update agent status when "complete" message received with confidence
  - Update agent status when "error" message received
  - Animate status transitions
  - _Requirements: 18.4, 18.5, 18.6, 18.7_

- [x] 4.4 Integrate status panel into ingestion flow
  - Add ExecutionStatusPanel to IngestionPanel
  - Pass jobId from submit response
  - Show panel when job starts
  - Hide panel when job completes
  - _Requirements: 18.1, 18.2_

- [x] 4.5 Integrate status panel into query flow
  - Add ExecutionStatusPanel to QueryPanel
  - Pass jobId from submit response
  - Show panel when job starts
  - Hide panel when job completes
  - _Requirements: 18.1, 18.2_

- [x] 5. Implement confidence-based clarification dialog
  - Create clarification dialog component
  - Detect low confidence fields after job completion
  - Generate targeted clarification questions
  - Re-submit with additional context
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9_

- [x] 5.1 Create ClarificationDialog component
  - Display low confidence fields with current values
  - Show confidence score badge for each field
  - Display targeted clarification question
  - Add textarea for user input
  - Add "Submit Clarification" and "Skip" buttons
  - _Requirements: 19.5, 19.8, 19.9_

- [x] 5.2 Implement confidence detection logic
  - Create extractLowConfidenceFields() function
  - Check each agent output for confidence < 0.9
  - Extract field name, current value, and confidence score
  - Return array of LowConfidenceField objects
  - _Requirements: 19.1, 19.2, 19.3_

- [x] 5.3 Implement clarification question generation
  - Create generateClarificationQuestion() function
  - Generate specific questions based on agent type
  - Geo Agent: Ask for more location details
  - Temporal Agent: Ask for specific date/time
  - Entity Agent: Ask for more category details
  - _Requirements: 19.4, 19.5_

- [x] 5.4 Integrate clarification into ingestion flow
  - Check confidence after job completion
  - Show ClarificationDialog if confidence < 0.9
  - Append clarification to original text
  - Re-submit report with enhanced context
  - Repeat until confidence >= 0.9 or user skips
  - Limit to 3 clarification rounds
  - _Requirements: 19.6, 19.7, 19.8_

- [x] 5.5 Integrate clarification into query flow
  - Check confidence after query completion
  - Show ClarificationDialog if confidence < 0.9
  - Append clarification to original question
  - Re-submit query with enhanced context
  - Repeat until confidence >= 0.9 or user skips
  - _Requirements: 19.6, 19.7, 19.8_

- [x] 6. Implement geometry type support
  - Enhance Geo Agent to detect geometry type
  - Update map rendering to support all geometry types
  - Add LineString rendering
  - Add Polygon rendering
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 6.1 Enhance Geo Agent backend
  - Add geometry_type field to output schema
  - Implement detect_geometry_type() function
  - Check for LineString patterns (from X to Y, along street)
  - Check for Polygon patterns (area, zone, neighborhood)
  - Default to Point for single locations
  - Update execute() to include geometry_type in output
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 6.2 Create geometry rendering utilities
  - Create renderGeometry() function in map-utils.ts
  - Add renderPoint() function
  - Add renderLineString() function
  - Add renderPolygon() function
  - Use category colors for all geometry types
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [x] 6.3 Implement LineString rendering
  - Add GeoJSON source for LineString
  - Add line layer with category color
  - Set line width to 4px
  - Add click handler to show popup
  - Add hover effect (cursor pointer)
  - _Requirements: 14.3, 14.5_

- [x] 6.4 Implement Polygon rendering
  - Add GeoJSON source for Polygon
  - Add fill layer with 30% opacity
  - Add border layer with category color
  - Add click handler to show popup
  - Add hover effect (cursor pointer)
  - _Requirements: 14.3, 14.6_

- [x] 6.5 Update MapView to use geometry rendering
  - Replace existing marker rendering with renderGeometry()
  - Pass incident data to renderGeometry()
  - Handle all three geometry types
  - Test with sample data for each type
  - _Requirements: 14.1, 14.2, 14.3, 14.7, 14.8_

- [x] 7. Add domain selection to ingestion and query panels
  - Add domain selector to IngestionPanel
  - Add domain selector to QueryPanel
  - Fetch domains from API
  - Validate domain selection before submission
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7.1 Update DomainSelector component
  - Fetch domains using listDomains() API
  - Display both built-in and custom domains
  - Show domain description in dropdown
  - Handle loading and error states
  - _Requirements: 5.2, 5.3, 6.2, 6.3_

- [x] 7.2 Add domain selector to IngestionPanel
  - Add DomainSelector above text input
  - Store selected domain in state
  - Disable submit button if no domain selected
  - Pass domain_id to submitReport() API
  - Show validation error if submitted without domain
  - _Requirements: 5.1, 5.4, 5.5_

- [x] 7.3 Add domain selector to QueryPanel
  - Add DomainSelector above question input
  - Store selected domain in state
  - Disable ask button if no domain selected
  - Pass domain_id to submitQuery() API
  - Show validation error if submitted without domain
  - _Requirements: 6.1, 6.4, 6.5_

- [x] 8. Implement backend enhancements
  - Add simplified domain creation endpoint
  - Enhance list endpoints with metadata
  - Add missing query agents to seed file
  - Deploy backend changes
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8.1 Add simplified domain creation method
  - Add create_from_agent_ids() method to DomainTemplateManager
  - Accept ingest_agent_ids and query_agent_ids arrays
  - Fetch agent configs from DynamoDB
  - Build playbook configs automatically
  - Build dependency graph from agent relationships
  - Call existing create() method with full config
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8.2 Update config handler to support simplified creation
  - Check if request body has agent_ids format
  - Call create_from_agent_ids() if simplified format
  - Call existing create() if full format
  - Return created domain template
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 8.3 Enhance list endpoints with metadata
  - Add is_builtin flag to agent list response
  - Add created_by_me flag to agent list response
  - Add is_builtin flag to domain list response
  - Add created_by_me flag to domain list response
  - Add agent_count to domain list response
  - Add incident_count to domain list response
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8.4 Add missing query agents to seed file
  - Add Which Agent (interrogative: which)
  - Add How Many Agent (interrogative: how_many)
  - Add How Much Agent (interrogative: how_much)
  - Add From Where Agent (interrogative: from_where)
  - Add What Kind Agent (interrogative: what_kind)
  - Verify total of 11 query agents
  - _Requirements: 4.1, 4.2_

- [x] 8.5 Deploy backend changes
  - Run CDK deploy for lambda updates
  - Verify API endpoints respond correctly
  - Test simplified domain creation
  - Test enhanced list endpoints
  - Verify all 11 query agents are available
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 9. Testing and bug fixes
  - Test all CRUD operations
  - Test two-stage domain creation
  - Test real-time status updates
  - Test confidence-based clarification
  - Test geometry rendering
  - Fix any bugs discovered
  - _Requirements: All_

- [x] 9.1 Test agent CRUD operations
  - Create custom ingestion agent
  - Create custom query agent with parent
  - List agents and verify filtering
  - Update agent configuration
  - Delete custom agent
  - Verify built-in agents cannot be deleted
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 9.2 Test domain creation flow
  - Open domain creation wizard
  - Select 2 ingestion agents in stage 1
  - Verify dependency graph shows parallel execution
  - Proceed to stage 2
  - Select 3 query agents
  - Verify dependency graph updates
  - Create domain
  - Verify domain appears in list
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

- [x] 9.3 Test real-time status updates
  - Submit report with domain selected
  - Verify ExecutionStatusPanel appears
  - Verify agents show "invoking" status
  - Verify agents show "complete" with confidence
  - Verify confidence badges display correctly
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

- [x] 9.4 Test confidence-based clarification
  - Submit report with ambiguous location
  - Verify low confidence detected (< 0.9)
  - Verify ClarificationDialog appears
  - Provide clarification details
  - Submit clarification
  - Verify report re-processed
  - Verify confidence improves
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9_

- [x] 9.5 Test geometry rendering
  - Submit report with single location (Point)
  - Verify marker appears on map
  - Submit report with "from X to Y" (LineString)
  - Verify line appears on map
  - Submit report with "area" or "zone" (Polygon)
  - Verify polygon appears on map
  - Test click interactions for all types
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 9.6 Test network error fixes
  - Refresh page multiple times
  - Verify no "NetworkError" toasts appear
  - Disconnect network
  - Attempt API call
  - Verify appropriate error toast
  - Reconnect network
  - Verify retry succeeds
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 9.7 Fix any discovered bugs
  - Document bugs found during testing
  - Prioritize critical bugs
  - Fix bugs one by one
  - Re-test after each fix
  - _Requirements: All_
