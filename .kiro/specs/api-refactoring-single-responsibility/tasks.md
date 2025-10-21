# Implementation Plan

This document outlines the implementation tasks for refactoring the Multi-Agent Orchestration System API to a unified agent architecture with single-responsibility endpoints.

## Task Overview

The implementation is organized into 8 major phases:
1. Database Schema Setup (RDS + DynamoDB)
2. Agent Management API
3. Domain Management API
4. Report Submission API Updates
5. Query & Management API Updates
6. Session Management API
7. Orchestrator Enhancements
8. Testing & Migration

---

## Phase 1: Database Schema Setup

- [x] 1. Create RDS PostgreSQL tables
  - Create agent_definitions table with agent_class, dependencies, output_schema
  - Create domain_configurations table with three playbooks (ingestion, query, management)
  - Create users, teams, tenants tables
  - Add indexes for tenant_id, agent_class, enabled fields
  - _Requirements: 1.1, 2.1, 8.1, 12.1_

- [-] 2. Create DynamoDB tables for flexible data
  - Create Reports table with GSIs for tenant-domain and domain-created
  - Create Sessions table with GSI for user-activity
  - Create Messages table with GSI for session-timestamp
  - Create QueryJobs table with GSI for session-created
  - _Requirements: 3.1, 4.1, 5.1, 8.2_

- [ ] 3. Create database initialization Lambda
  - Write db_init.py to create all RDS tables
  - Add SQL scripts for table creation with proper constraints
  - Test database initialization with psycopg2 layer
  - _Requirements: 8.1, 12.1_

---

## Phase 2: Agent Management API

- [ ] 4. Implement DAG validation algorithm
  - Write validate_dag() function using DFS cycle detection
  - Write build_dependency_graph() function for visualization
  - Add unit tests for circular dependency detection
  - Test with various graph structures (linear, parallel, diamond, circular)
  - _Requirements: 1.1, 9.1, 9.2_

- [ ] 5. Create Agent Handler Lambda
  - Implement create_agent() with DAG validation
  - Implement list_agents() with filtering by agent_class
  - Implement get_agent() with dependency graph generation
  - Implement update_agent() with circular dependency check
  - Implement delete_agent() with builtin protection
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 6. Add Agent API routes to API Gateway
  - Add POST /api/v1/agents route
  - Add GET /api/v1/agents route with query parameters
  - Add GET /api/v1/agents/{agent_id} route
  - Add PUT /api/v1/agents/{agent_id} route
  - Add DELETE /api/v1/agents/{agent_id} route
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 7. Write unit tests for Agent Handler
  - Test DAG validation with circular dependencies
  - Test agent creation with valid/invalid schemas
  - Test agent filtering by class
  - Test dependency graph generation
  - _Requirements: 10.1, 10.2_

---

## Phase 3: Domain Management API

- [ ] 8. Implement playbook validation
  - Write validate_playbook() function for DAG validation
  - Write validate_agent_class() to verify agents match playbook type
  - Add unit tests for playbook validation
  - _Requirements: 2.1, 9.1, 9.4_

- [ ] 9. Create Domain Handler Lambda
  - Implement create_domain() with playbook validation
  - Implement list_domains() with pagination
  - Implement get_domain() with full playbook details
  - Implement update_domain() with playbook validation
  - Implement delete_domain()
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 10. Add Domain API routes to API Gateway
  - Add POST /api/v1/domains route
  - Add GET /api/v1/domains route
  - Add GET /api/v1/domains/{domain_id} route
  - Add PUT /api/v1/domains/{domain_id} route
  - Add DELETE /api/v1/domains/{domain_id} route
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 11. Write unit tests for Domain Handler
  - Test playbook validation with invalid graphs
  - Test agent class verification
  - Test domain CRUD operations
  - _Requirements: 10.1, 10.2_

---

## Phase 4: Report Submission API Updates

- [ ] 12. Update Report Handler for new schema
  - Update create_report() to use Reports DynamoDB table
  - Add ingestion_data and management_data fields
  - Update get_report() to return full document structure
  - Update list_reports() with domain_id filtering
  - Implement update_report() for management_data merging
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 13. Update report submission flow
  - Modify ingest_handler_simple.py to use new Reports table
  - Update orchestrator invocation to pass ingestion_playbook
  - Add standard metadata (id, created_at, updated_at, created_by)
  - _Requirements: 3.1, 12.1, 12.2_

- [ ]* 14. Write integration tests for report flow
  - Test report submission end-to-end
  - Test ingestion_data population
  - Test management_data merging
  - _Requirements: 10.1, 10.3_

---

## Phase 5: Query & Management API Updates

- [ ] 15. Update Query Handler for mode selection
  - Add mode parameter ('query' or 'management') to request
  - Remove intent classification logic
  - Route to appropriate playbook based on mode
  - Update query_handler_simple.py to use QueryJobs table
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 16. Add execution_log to query response
  - Update QueryJobs table schema to include execution_log
  - Modify get_query() to return execution_log array
  - Add map_data and references_used fields
  - _Requirements: 4.3, 14.1, 14.2_

- [ ]* 17. Write integration tests for query flow
  - Test query submission with mode='query'
  - Test query submission with mode='management'
  - Test execution_log population
  - Test map_data and references_used
  - _Requirements: 10.1, 10.3_

---

## Phase 6: Session Management API

- [ ] 18. Create Session Handler Lambda
  - Implement create_session() for Sessions table
  - Implement list_sessions() with user-activity GSI
  - Implement get_session() with messages
  - Implement update_session() for metadata
  - Implement delete_session() with cascade to messages
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 19. Implement message grounding
  - Write create_assistant_message() with references metadata
  - Add references array linking to source Reports
  - Update session last_activity on message creation
  - _Requirements: 5.2, 5.3_

- [ ] 20. Add Session API routes to API Gateway
  - Add POST /api/v1/sessions route
  - Add GET /api/v1/sessions route
  - Add GET /api/v1/sessions/{session_id} route
  - Add PUT /api/v1/sessions/{session_id} route
  - Add DELETE /api/v1/sessions/{session_id} route
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 21. Write unit tests for Session Handler
  - Test session CRUD operations
  - Test message grounding with references
  - Test cascade delete
  - _Requirements: 10.1, 10.2_

---

## Phase 7: Orchestrator Enhancements

- [ ] 22. Implement agent output caching
  - Add cache dictionary to Orchestrator class
  - Check cache before executing agent
  - Store agent output in cache after execution
  - Clear cache after job completion
  - Log cache hits in execution_log
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 23. Implement execution logging
  - Add execution_log array to Orchestrator class
  - Log each agent execution with reasoning and output
  - Capture agent reasoning text from LLM response
  - Store intermediate outputs for debugging
  - Order log entries chronologically
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 24. Implement error propagation
  - Add error handling to execute_agent()
  - Mark failed agents as 'error' in execution_log
  - Automatically mark dependent agents as 'skipped'
  - Set job status to 'failed' on any agent failure
  - Stop execution on first failure (fail-fast)
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 25. Update orchestrator to use RDS for agents/domains
  - Replace DynamoDB queries with RDS Data API calls
  - Update load_playbook.py to query domain_configurations table
  - Update agent_invoker.py to query agent_definitions table
  - Add connection pooling for RDS
  - _Requirements: 8.1, 8.4_

- [ ]* 26. Write unit tests for orchestrator enhancements
  - Test agent output caching with shared dependencies
  - Test execution logging with reasoning capture
  - Test error propagation with fail-fast
  - Test topological sort with various graphs
  - _Requirements: 10.1, 10.2_

---

## Phase 8: Testing & Migration

- [ ] 27. Update TEST.py with new endpoints
  - Add test_agent_crud() for agent management
  - Add test_domain_crud() for domain management
  - Add test_report_submission() with new schema
  - Add test_query_submission() with mode parameter
  - Add test_session_management() for sessions
  - Add test_execution_log() to verify logging
  - _Requirements: 10.1, 10.3, 10.4_

- [ ]* 28. Add AppSync WebSocket tests
  - Write test_appsync_realtime() to establish WebSocket
  - Submit query and collect status updates
  - Verify status progression (agent_invoking → complete)
  - Test error status updates
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.5_

- [ ] 29. Remove old config API
  - Delete config_handler.py Lambda function
  - Remove /api/v1/config routes from API Gateway
  - Delete DynamoDB Configurations table (data not needed)
  - Update any references to old config API
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ] 30. Seed initial data
  - Create seed script for builtin agents (geo, temporal, entity, what, where, when, why, how)
  - Create seed script for sample domain (civic_complaints)
  - Add seed data to database initialization
  - Verify builtin agents are marked as is_inbuilt=true
  - _Requirements: 1.1, 2.1, 12.1_

- [ ] 31. Deploy and verify
  - Deploy all Lambda functions
  - Deploy API Gateway changes
  - Run full TEST.py suite
  - Verify 100% test pass rate
  - Monitor CloudWatch logs for errors
  - _Requirements: 10.1, 10.3, 10.4_
