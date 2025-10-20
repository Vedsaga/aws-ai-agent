# Requirements Document

## Introduction

This document defines requirements for integrating backend APIs with frontend components and fixing critical bugs in the Multi-Agent Orchestration System. The focus is on enabling CRUD operations for custom agents and domains, fixing network error issues, and improving the user experience for domain selection and agent configuration.

## Glossary

- **System**: The Multi-Agent Orchestration System frontend application
- **User**: A person interacting with the System
- **Domain**: A use case configuration with ingestion and query agents
- **Custom Agent**: A user-created agent with custom configuration
- **Built-in Agent**: A pre-configured agent provided by the System (11 query agents, 6 ingestion agents)
- **Data Ingest Agent**: An agent that extracts structured data from unstructured input
- **Data Query Agent**: An agent that analyzes data from an interrogative perspective (11 interrogatives: when, where, why, how, what, who, which, how_many, how_much, from_where, what_kind)
- **API Component**: A frontend component that communicates with backend APIs
- **CRUD**: Create, Read, Update, Delete operations
- **Confidence Score**: A numerical value (0.0 to 1.0) indicating agent's confidence in its output
- **Geometry Type**: The spatial representation type (Point, LineString, Polygon) for map rendering
- **Orchestrator**: The backend component that validates agent outputs and checks confidence scores
- **Validator Agent**: A backend component that cross-validates consistency across agent outputs

## Requirements

### Requirement 1: API Integration for Modules and Panels

**User Story:** As a User, I want all frontend components to communicate with backend APIs, so that I can perform operations on real data.

#### Acceptance Criteria

1. THE System SHALL integrate API calls into all data-displaying components
2. THE System SHALL use the Configuration API for agent and domain management
3. THE System SHALL use the Data API for incident retrieval and display
4. THE System SHALL handle API responses and update UI accordingly
5. THE System SHALL display loading states while API requests are in progress

### Requirement 2: Custom Agent CRUD Operations

**User Story:** As a User, I want to create, view, update, and delete custom agents, so that I can configure the System for my specific needs.

#### Acceptance Criteria

1. THE System SHALL provide a form to create new custom agents
2. THE System SHALL allow Users to specify agent type (Data Ingest Agent or Data Query Agent)
3. THE System SHALL allow Users to configure agent properties including system prompt, tools, and API endpoints
4. THE System SHALL display a list of all custom agents created by the User
5. THE System SHALL allow Users to edit existing custom agents
6. THE System SHALL allow Users to delete custom agents they created

### Requirement 3: Domain Management with Agent Selection

**User Story:** As a User, I want to create domains by selecting from built-in and custom agents, so that I can configure workflows for my use cases.

#### Acceptance Criteria

1. THE System SHALL provide a domain creation interface
2. THE System SHALL display all available agents (built-in + custom) for selection
3. THE System SHALL allow Users to select multiple Data Ingest Agents for a domain
4. THE System SHALL allow Users to select multiple Data Query Agents for a domain
5. THE System SHALL save domain configuration via the Configuration API

### Requirement 4: Built-in and Custom Agent Display

**User Story:** As a User, I want to see all available agents including built-in and my custom agents, so that I can choose the right agents for my domain.

#### Acceptance Criteria

1. THE System SHALL display all 14 built-in agents (3 ingestion, 11 query)
2. THE System SHALL display all custom agents created by the User
3. THE System SHALL indicate agent type with visual tags (built-in, custom, created by me)
4. THE System SHALL show agent details including name, type, and capabilities
5. THE System SHALL filter agents by type (Data Ingest Agent, Data Query Agent)

### Requirement 5: Domain Selection for Report Submission

**User Story:** As a User, I want to select a domain before submitting a report, so that the System processes my input with the correct agents.

#### Acceptance Criteria

1. THE System SHALL display a domain selector in the report submission panel
2. THE System SHALL fetch available domains from the Configuration API
3. THE System SHALL include built-in domains and custom domains in the selector
4. WHEN a User selects a domain, THE System SHALL enable the submit button
5. THE System SHALL prevent report submission without domain selection

### Requirement 6: Domain Selection for Asking Questions

**User Story:** As a User, I want to select a domain before asking questions, so that the System queries the correct data and agents.

#### Acceptance Criteria

1. THE System SHALL display a domain selector in the query panel
2. THE System SHALL fetch available domains from the Configuration API
3. THE System SHALL include built-in domains and custom domains in the selector
4. WHEN a User selects a domain, THE System SHALL enable the ask button
5. THE System SHALL prevent question submission without domain selection

### Requirement 7: Manage Domain Page Improvements

**User Story:** As a User, I want to see all domains including built-in ones on the manage page, so that I can view and interact with any domain.

#### Acceptance Criteria

1. THE System SHALL display all domains on the manage page (built-in + custom)
2. THE System SHALL show visual tags indicating domain origin (built-in, created by me, created by others)
3. THE System SHALL provide "Ask Question" action on each domain card
4. THE System SHALL provide "Submit Report" action on each domain card
5. THE System SHALL navigate to appropriate panel when action is clicked

### Requirement 8: Agent Configuration Form Enhancements

**User Story:** As a Domain Creator, I want a comprehensive agent configuration form, so that I can create custom agents with all necessary settings.

#### Acceptance Criteria

1. THE System SHALL provide a toggle to select agent type (Data Ingest Agent or Data Query Agent)
2. THE System SHALL allow selection of one parent agent for execution chaining
3. THE System SHALL provide fields for tool selection from available tools
4. THE System SHALL provide fields for custom API endpoint configuration
5. THE System SHALL provide a text area for system prompt input
6. THE System SHALL provide key-value pair inputs for agent configuration
7. THE System SHALL provide an example JSON field for Data Ingest Agents to define output schema
8. THE System SHALL apply dark mode styling to the form

### Requirement 9: Query Agent Parent Chaining

**User Story:** As a Domain Creator, I want to chain custom Data Query Agents with built-in interrogative agents, so that I can create complex analysis workflows.

#### Acceptance Criteria

1. WHEN creating a Data Query Agent, THE System SHALL display all 11 built-in query agents as parent options
2. THE System SHALL allow selection of exactly one parent agent
3. THE System SHALL prevent selection of multiple parent agents
4. THE System SHALL save parent agent relationship in agent configuration
5. THE System SHALL display parent agent relationship in agent details

### Requirement 10: Network Error Fix

**User Story:** As a User, I want the System to load without showing network errors on every page refresh, so that I have a smooth experience.

#### Acceptance Criteria

1. THE System SHALL NOT display "Failed to load domains" error on page load
2. THE System SHALL NOT display "NetworkError when attempting to fetch resource" on page refresh
3. THE System SHALL properly initialize API client with authentication
4. THE System SHALL retry failed requests with exponential backoff
5. THE System SHALL only show network errors for actual network failures

### Requirement 11: Domain Resource Loading

**User Story:** As a User, I want to see domains and resources load correctly, so that I can interact with the System.

#### Acceptance Criteria

1. THE System SHALL make API calls to fetch domains on component mount
2. THE System SHALL display loading indicators while fetching data
3. THE System SHALL handle API errors gracefully with user-friendly messages
4. THE System SHALL display fetched domains in the UI
5. THE System SHALL cache domain data to reduce unnecessary API calls

### Requirement 12: Domain Creation Flow Removal

**User Story:** As a User, I want a streamlined domain creation process, so that I can quickly configure domains without unnecessary steps.

#### Acceptance Criteria

1. THE System SHALL NOT navigate to agent creation form when creating a domain
2. THE System SHALL display agent selection interface directly in domain creation
3. THE System SHALL allow selection of agents from a list (built-in + custom)
4. THE System SHALL create domain with selected agents in a single step
5. THE System SHALL validate that at least one agent is selected before creation


### Requirement 13: Confidence Score Validation

**User Story:** As a System Administrator, I want the orchestrator to validate agent outputs based on confidence scores, so that low-confidence results are flagged or rejected.

#### Acceptance Criteria

1. THE System SHALL extract confidence scores from agent outputs during validation
2. THE System SHALL flag outputs with confidence scores below 0.5 as low-confidence
3. THE System SHALL display confidence scores in the UI for each agent output
4. THE System SHALL allow Users to filter results by confidence threshold
5. THE System SHALL highlight low-confidence results with visual indicators

### Requirement 14: Geometry Type Support for Map Rendering

**User Story:** As a User, I want to see different geometry types (Point, LineString, Polygon) rendered on the map, so that I can visualize spatial data appropriately.

#### Acceptance Criteria

1. THE System SHALL support Point geometry for single-location incidents
2. THE System SHALL support LineString geometry for linear features (roads, routes)
3. THE System SHALL support Polygon geometry for area features (zones, regions)
4. THE System SHALL render Points as markers with category-specific colors and icons
5. THE System SHALL render LineStrings as colored lines on the map
6. THE System SHALL render Polygons as filled areas with borders on the map
7. THE System SHALL detect geometry type from agent output or text analysis
8. THE System SHALL default to Point geometry when type is ambiguous

### Requirement 15: Enhanced Geo Agent Capabilities

**User Story:** As a Domain Creator, I want the Geo Agent to support multiple geometry types, so that it can extract appropriate spatial representations.

#### Acceptance Criteria

1. THE System SHALL enhance Geo Agent to detect geometry type from text
2. WHEN text mentions "from X to Y" or "along X street", THE System SHALL use LineString geometry
3. WHEN text mentions "area", "zone", "neighborhood", or "block", THE System SHALL use Polygon geometry
4. THE System SHALL default to Point geometry for single locations
5. THE System SHALL include geometry_type field in Geo Agent output schema

### Requirement 16: Query Agent Tool Access

**User Story:** As a Query Agent, I want access to data retrieval tools and other agents, so that I can provide comprehensive analysis.

#### Acceptance Criteria

1. THE System SHALL allow Query Agents to invoke Data Retrieval API
2. THE System SHALL allow Query Agents to invoke Spatial Query API
3. THE System SHALL allow Query Agents to invoke Analytics API
4. THE System SHALL allow Query Agents to call Geo Agent for location analysis
5. THE System SHALL allow Query Agents to chain with other agents dynamically
6. THE System SHALL provide Query Agents with access to domain data context

### Requirement 17: Two-Stage Domain Creation with Dependency Visualization

**User Story:** As a Domain Creator, I want a guided two-stage domain creation process with dependency visualization, so that I can understand agent execution flow.

#### Acceptance Criteria

1. THE System SHALL enforce selection of at least one Data Ingest Agent in stage 1
2. THE System SHALL enforce selection of at least one Data Query Agent in stage 2
3. THE System SHALL prevent domain creation without both agent types selected
4. THE System SHALL display a dependency graph below agent selection showing execution flow
5. WHEN agents have dependency_parent defined, THE System SHALL show sequential execution in the graph
6. WHEN multiple agents have no dependencies, THE System SHALL show parallel execution in the graph
7. THE System SHALL update the dependency graph in real-time as agents are selected/deselected

### Requirement 18: Real-Time Execution Status Visualization

**User Story:** As a User, I want to see real-time status of agent execution during ingestion and query, so that I understand what the System is doing.

#### Acceptance Criteria

1. THE System SHALL display a real-time status panel during data ingestion
2. THE System SHALL display a real-time status panel during query execution
3. THE System SHALL show agent execution chain with current status for each agent
4. WHEN an agent starts execution, THE System SHALL update its status to "invoking"
5. WHEN an agent calls a tool, THE System SHALL update its status to "calling_tool: {tool_name}"
6. WHEN an agent completes, THE System SHALL update its status to "complete" with confidence score
7. WHEN an agent fails, THE System SHALL update its status to "error" with error message
8. THE System SHALL use WebSocket (AppSync) for real-time status updates
9. THE System SHALL visualize the dependency graph with color-coded status indicators


### Requirement 19: Confidence-Based Clarification Dialog

**User Story:** As a User, I want the System to ask follow-up questions when confidence is low, so that I can provide additional information for accurate processing.

#### Acceptance Criteria

1. WHEN ingestion agents produce outputs with confidence below 0.9, THE System SHALL initiate a clarification dialog
2. WHEN query agents produce outputs with confidence below 0.9, THE System SHALL initiate a clarification dialog
3. THE System SHALL identify which specific fields have low confidence
4. THE System SHALL generate targeted follow-up questions for low-confidence fields
5. THE System SHALL display the clarification dialog to the User with specific questions
6. WHEN the User provides clarification, THE System SHALL re-process with the additional context
7. THE System SHALL continue clarification rounds until confidence reaches 0.9 or higher
8. THE System SHALL allow Users to skip clarification and proceed with low-confidence results
9. THE System SHALL display confidence scores for each field in the clarification dialog
