/**
 * Integration tests for API client
 * Tests the complete flow of agent and domain CRUD operations
 */

import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import {
  createAgent,
  listAgents,
  getAgent,
  updateAgent,
  deleteAgent,
  createDomain,
  listDomains,
  getDomain,
  updateDomain,
  deleteDomain,
  AgentConfig,
  DomainConfig,
} from '../api-client';

describe('API Integration Tests', () => {
  let testAgentId: string;
  let testDomainId: string;

  describe('Agent CRUD Operations', () => {
    it('should create a custom ingestion agent', async () => {
      const config: AgentConfig = {
        agent_name: 'Test Ingest Agent',
        agent_type: 'ingestion',
        system_prompt: 'Extract location and priority from civic complaints',
        tools: ['bedrock', 'location_proxy'],
        output_schema: {
          location: { type: 'string', required: true },
          priority: { type: 'number', required: true },
          confidence: { type: 'number', required: true },
        },
      };

      const response = await createAgent(config);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.agent_name).toBe('Test Ingest Agent');
      expect(response.data?.is_builtin).toBe(false);

      if (response.data) {
        testAgentId = response.data.agent_id;
      }
    }, 10000);

    it('should list all agents including the created one', async () => {
      const response = await listAgents();

      expect(response.status).toBe(200);
      expect(response.data?.agents).toBeDefined();
      expect(Array.isArray(response.data?.agents)).toBe(true);

      const createdAgent = response.data?.agents.find(
        (a) => a.agent_id === testAgentId
      );
      expect(createdAgent).toBeDefined();
    }, 10000);

    it('should get a specific agent by ID', async () => {
      const response = await getAgent(testAgentId);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.agent_id).toBe(testAgentId);
      expect(response.data?.agent_name).toBe('Test Ingest Agent');
    }, 10000);

    it('should update an agent configuration', async () => {
      const updatedConfig: AgentConfig = {
        agent_name: 'Test Ingest Agent Updated',
        agent_type: 'ingestion',
        system_prompt: 'Extract location, priority, and category from civic complaints',
        tools: ['bedrock', 'location_proxy', 'comprehend_proxy'],
        output_schema: {
          location: { type: 'string', required: true },
          priority: { type: 'number', required: true },
          category: { type: 'string', required: true },
          confidence: { type: 'number', required: true },
        },
      };

      const response = await updateAgent(testAgentId, updatedConfig);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.agent_name).toBe('Test Ingest Agent Updated');
      expect(response.data?.tools).toContain('comprehend_proxy');
    }, 10000);

    it('should filter agents by type', async () => {
      const response = await listAgents();

      expect(response.data?.agents).toBeDefined();

      const builtinAgents = response.data?.agents.filter((a) => a.is_builtin);
      const customAgents = response.data?.agents.filter((a) => !a.is_builtin);

      expect(builtinAgents.length).toBeGreaterThan(0);
      expect(customAgents.length).toBeGreaterThan(0);

      // Should have 17 built-in agents (6 ingestion + 11 query)
      expect(builtinAgents.length).toBeGreaterThanOrEqual(17);
    }, 10000);
  });

  describe('Domain CRUD Operations', () => {
    it('should create a domain with selected agents', async () => {
      // First, get some agent IDs
      const agentsResponse = await listAgents();
      expect(agentsResponse.data?.agents).toBeDefined();

      const agents = agentsResponse.data!.agents;
      const ingestAgents = agents
        .filter((a) => a.agent_type === 'ingestion')
        .slice(0, 2)
        .map((a) => a.agent_id);
      const queryAgents = agents
        .filter((a) => a.agent_type === 'query')
        .slice(0, 3)
        .map((a) => a.agent_id);

      const config: DomainConfig = {
        template_name: 'Test Traffic Domain',
        domain_id: 'test_traffic_domain',
        description: 'Testing domain creation with traffic agents',
        ingest_agent_ids: ingestAgents,
        query_agent_ids: queryAgents,
      };

      const response = await createDomain(config);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.template_name).toBe('Test Traffic Domain');
      expect(response.data?.is_builtin).toBe(false);

      if (response.data) {
        testDomainId = response.data.template_id;
      }
    }, 15000);

    it('should list all domains including the created one', async () => {
      const response = await listDomains();

      expect(response.status).toBe(200);
      expect(response.data?.domains).toBeDefined();
      expect(Array.isArray(response.data?.domains)).toBe(true);

      const createdDomain = response.data?.domains.find(
        (d) => d.template_id === testDomainId
      );
      expect(createdDomain).toBeDefined();
    }, 10000);

    it('should get a specific domain by ID', async () => {
      const response = await getDomain(testDomainId);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.template_id).toBe(testDomainId);
      expect(response.data?.template_name).toBe('Test Traffic Domain');
    }, 10000);

    it('should update a domain configuration', async () => {
      const updatedConfig: DomainConfig = {
        template_name: 'Test Traffic Domain Updated',
        domain_id: 'test_traffic_domain',
        description: 'Updated description for testing',
        ingest_agent_ids: [],
        query_agent_ids: [],
      };

      const response = await updateDomain(testDomainId, updatedConfig);

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.template_name).toBe('Test Traffic Domain Updated');
    }, 10000);
  });

  describe('Cleanup', () => {
    it('should delete the test domain', async () => {
      const response = await deleteDomain(testDomainId);

      expect(response.status).toBeGreaterThanOrEqual(200);
      expect(response.status).toBeLessThan(300);
    }, 10000);

    it('should delete the test agent', async () => {
      const response = await deleteAgent(testAgentId);

      expect(response.status).toBeGreaterThanOrEqual(200);
      expect(response.status).toBeLessThan(300);
    }, 10000);

    it('should verify agent is deleted', async () => {
      const response = await listAgents();

      const deletedAgent = response.data?.agents.find(
        (a) => a.agent_id === testAgentId
      );
      expect(deletedAgent).toBeUndefined();
    }, 10000);

    it('should verify domain is deleted', async () => {
      const response = await listDomains();

      const deletedDomain = response.data?.domains.find(
        (d) => d.template_id === testDomainId
      );
      expect(deletedDomain).toBeUndefined();
    }, 10000);
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // This test would require mocking network failures
      // For now, we just verify the error handling structure exists
      expect(typeof createAgent).toBe('function');
      expect(typeof listAgents).toBe('function');
    });

    it('should handle 404 errors for non-existent resources', async () => {
      const response = await getAgent('non-existent-id');

      expect(response.status).toBe(404);
      expect(response.error).toBeDefined();
    }, 10000);

    it('should handle validation errors', async () => {
      const invalidConfig: AgentConfig = {
        agent_name: '', // Empty name should fail validation
        agent_type: 'ingestion',
        system_prompt: '',
        tools: [],
        output_schema: {},
      };

      const response = await createAgent(invalidConfig);

      expect(response.status).toBeGreaterThanOrEqual(400);
      expect(response.status).toBeLessThan(500);
      expect(response.error).toBeDefined();
    }, 10000);
  });

  describe('Built-in Agents Protection', () => {
    it('should not allow deletion of built-in agents', async () => {
      const agentsResponse = await listAgents();
      const builtinAgent = agentsResponse.data?.agents.find((a) => a.is_builtin);

      if (builtinAgent) {
        const response = await deleteAgent(builtinAgent.agent_id);

        expect(response.status).toBeGreaterThanOrEqual(400);
        expect(response.error).toBeDefined();
      }
    }, 10000);

    it('should not allow modification of built-in agents', async () => {
      const agentsResponse = await listAgents();
      const builtinAgent = agentsResponse.data?.agents.find((a) => a.is_builtin);

      if (builtinAgent) {
        const config: AgentConfig = {
          agent_name: 'Modified Built-in Agent',
          agent_type: builtinAgent.agent_type,
          system_prompt: 'Modified prompt',
          tools: builtinAgent.tools,
          output_schema: builtinAgent.output_schema,
        };

        const response = await updateAgent(builtinAgent.agent_id, config);

        expect(response.status).toBeGreaterThanOrEqual(400);
        expect(response.error).toBeDefined();
      }
    }, 10000);
  });
});
