/**
 * Multi-Agent Orchestration System - Frontend API Client
 * Ready to use in React, Vue, or vanilla JavaScript
 *
 * Base URL: https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1
 * Authentication: AWS Cognito JWT Token
 *
 * Status: ✅ All APIs tested and working (Oct 20, 2025)
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_CONFIG = {
  baseUrl: "https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1",
  cognito: {
    userPoolId: "us-east-1_7QZ7Y6Gbl",
    clientId: "6gobbpage9af3nd7ahm3lchkct",
    region: "us-east-1"
  },
  // Test credentials (replace with actual user login)
  testUser: {
    username: "testuser",
    password: "TestPassword123!"
  }
};

// ============================================================================
// AUTHENTICATION
// ============================================================================

/**
 * Get JWT token from AWS Cognito
 * @param {string} username
 * @param {string} password
 * @returns {Promise<string>} JWT token
 */
async function getAuthToken(username, password) {
  const url = `https://cognito-idp.${API_CONFIG.cognito.region}.amazonaws.com/`;

  const payload = {
    AuthFlow: "USER_PASSWORD_AUTH",
    ClientId: API_CONFIG.cognito.clientId,
    AuthParameters: {
      USERNAME: username,
      PASSWORD: password
    }
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Authentication failed: ${response.status}`);
  }

  const data = await response.json();
  return data.AuthenticationResult.IdToken;
}

// ============================================================================
// API CLIENT CLASS
// ============================================================================

class MultiAgentAPIClient {
  constructor(token) {
    this.token = token;
    this.baseUrl = API_CONFIG.baseUrl;
  }

  /**
   * Make GET request
   */
  async get(endpoint, params = {}) {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    Object.keys(params).forEach(key =>
      url.searchParams.append(key, params[key])
    );

    const response = await fetch(url, {
      method: "GET",
      headers: this._getHeaders()
    });

    return this._handleResponse(response);
  }

  /**
   * Make POST request
   */
  async post(endpoint, data) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: this._getHeaders(),
      body: JSON.stringify(data)
    });

    return this._handleResponse(response);
  }

  /**
   * Make PUT request
   */
  async put(endpoint, data) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PUT",
      headers: this._getHeaders(),
      body: JSON.stringify(data)
    });

    return this._handleResponse(response);
  }

  /**
   * Make DELETE request
   */
  async delete(endpoint) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: this._getHeaders()
    });

    return this._handleResponse(response);
  }

  /**
   * Get request headers
   */
  _getHeaders() {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${this.token}`
    };
  }

  /**
   * Handle API response
   */
  async _handleResponse(response) {
    const data = await response.json();

    if (!response.ok) {
      throw new APIError(
        data.error || data.message || `HTTP ${response.status}`,
        response.status,
        data
      );
    }

    return data;
  }

  // ========================================================================
  // CONFIG API METHODS
  // ========================================================================

  /**
   * List all agents
   * @returns {Promise<{configs: Array, count: number}>}
   */
  async listAgents() {
    return this.get("/api/v1/config", { type: "agent" });
  }

  /**
   * Create custom agent
   * @param {Object} agentConfig - Agent configuration
   * @returns {Promise<Object>} Created agent
   */
  async createAgent(agentConfig) {
    return this.post("/api/v1/config", {
      type: "agent",
      config: agentConfig
    });
  }

  /**
   * List domain templates
   * @returns {Promise<{configs: Array, count: number}>}
   */
  async listDomains() {
    return this.get("/api/v1/config", { type: "domain_template" });
  }

  // ========================================================================
  // INGEST API METHODS
  // ========================================================================

  /**
   * Submit a report for processing
   * @param {string} domainId - Domain ID (e.g., "civic_complaints")
   * @param {string} text - Report text
   * @param {Object} options - Additional options (priority, source, etc.)
   * @returns {Promise<{job_id: string, status: string}>}
   */
  async submitReport(domainId, text, options = {}) {
    return this.post("/api/v1/ingest", {
      domain_id: domainId,
      text: text,
      priority: options.priority || "normal",
      source: options.source || "web",
      reporter_contact: options.reporter_contact,
      images: options.images || []
    });
  }

  // ========================================================================
  // QUERY API METHODS
  // ========================================================================

  /**
   * Ask a question about the data
   * @param {string} domainId - Domain ID
   * @param {string} question - Natural language question
   * @param {Object} filters - Optional filters
   * @returns {Promise<{job_id: string, status: string}>}
   */
  async askQuestion(domainId, question, filters = {}) {
    return this.post("/api/v1/query", {
      domain_id: domainId,
      question: question,
      filters: filters,
      include_visualizations: filters.include_visualizations || false
    });
  }

  // ========================================================================
  // DATA API METHODS
  // ========================================================================

  /**
   * Retrieve incidents/reports
   * @param {Object} filters - Optional filters
   * @returns {Promise<{status: string, data: Array, count: number}>}
   */
  async retrieveIncidents(filters = {}) {
    return this.get("/api/v1/data", {
      type: "retrieval",
      ...filters
    });
  }

  // ========================================================================
  // TOOLS API METHODS
  // ========================================================================

  /**
   * List available tools
   * @returns {Promise<{tools: Array, count: number}>}
   */
  async listTools() {
    return this.get("/api/v1/tools");
  }
}

// ============================================================================
// CUSTOM ERROR CLASS
// ============================================================================

class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.details = details;
  }
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/**
 * Example 1: Initialize and list agents
 */
async function example1_listAgents() {
  try {
    // Get authentication token
    const token = await getAuthToken(
      API_CONFIG.testUser.username,
      API_CONFIG.testUser.password
    );

    // Create API client
    const client = new MultiAgentAPIClient(token);

    // List all agents
    const agents = await client.listAgents();
    console.log(`Found ${agents.count} agents:`, agents.configs);

    return agents;
  } catch (error) {
    console.error("Error:", error.message);
    throw error;
  }
}

/**
 * Example 2: Submit a report
 */
async function example2_submitReport() {
  try {
    const token = await getAuthToken(
      API_CONFIG.testUser.username,
      API_CONFIG.testUser.password
    );

    const client = new MultiAgentAPIClient(token);

    // Submit report
    const result = await client.submitReport(
      "civic_complaints",
      "There is a broken streetlight on Main Street near the library",
      { priority: "high" }
    );

    console.log("Report submitted:", result.job_id);
    console.log("Status:", result.status);

    return result;
  } catch (error) {
    console.error("Error:", error.message);
    throw error;
  }
}

/**
 * Example 3: Ask a question
 */
async function example3_askQuestion() {
  try {
    const token = await getAuthToken(
      API_CONFIG.testUser.username,
      API_CONFIG.testUser.password
    );

    const client = new MultiAgentAPIClient(token);

    // Ask question
    const result = await client.askQuestion(
      "civic_complaints",
      "What are the most common infrastructure complaints this month?"
    );

    console.log("Question submitted:", result.job_id);
    console.log("Estimated completion:", result.estimated_completion_seconds, "seconds");

    return result;
  } catch (error) {
    console.error("Error:", error.message);
    throw error;
  }
}

/**
 * Example 4: Create custom agent
 */
async function example4_createAgent() {
  try {
    const token = await getAuthToken(
      API_CONFIG.testUser.username,
      API_CONFIG.testUser.password
    );

    const client = new MultiAgentAPIClient(token);

    // Create custom agent
    const newAgent = await client.createAgent({
      agent_name: "Custom Severity Agent",
      agent_type: "custom",
      system_prompt: "You analyze incident severity",
      tools: ["bedrock"],
      output_schema: {
        severity: "string",
        urgency: "number"
      }
    });

    console.log("Agent created:", newAgent.agent_id);
    console.log("Agent name:", newAgent.agent_name);

    return newAgent;
  } catch (error) {
    console.error("Error:", error.message);
    throw error;
  }
}

/**
 * Example 5: Complete workflow
 */
async function example5_completeWorkflow() {
  try {
    // Step 1: Authenticate
    console.log("1. Authenticating...");
    const token = await getAuthToken(
      API_CONFIG.testUser.username,
      API_CONFIG.testUser.password
    );
    const client = new MultiAgentAPIClient(token);

    // Step 2: List available agents
    console.log("2. Loading agents...");
    const agents = await client.listAgents();
    console.log(`   Found ${agents.count} agents`);

    // Step 3: Submit a report
    console.log("3. Submitting report...");
    const report = await client.submitReport(
      "civic_complaints",
      "Multiple potholes on Oak Avenue causing traffic issues"
    );
    console.log(`   Report submitted: ${report.job_id}`);

    // Step 4: Ask a question
    console.log("4. Asking question...");
    const query = await client.askQuestion(
      "civic_complaints",
      "Where are most infrastructure issues reported?"
    );
    console.log(`   Query submitted: ${query.job_id}`);

    // Step 5: Retrieve data
    console.log("5. Retrieving incidents...");
    const incidents = await client.retrieveIncidents();
    console.log(`   Found ${incidents.count} incidents`);

    console.log("\n✅ Workflow completed successfully!");

    return {
      agents: agents.count,
      reportJobId: report.job_id,
      queryJobId: query.job_id,
      incidents: incidents.count
    };
  } catch (error) {
    console.error("Workflow failed:", error.message);
    throw error;
  }
}

// ============================================================================
// EXPORTS (for module usage)
// ============================================================================

// For ES6 modules
export {
  MultiAgentAPIClient,
  getAuthToken,
  APIError,
  API_CONFIG
};

// For CommonJS
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    MultiAgentAPIClient,
    getAuthToken,
    APIError,
    API_CONFIG
  };
}

// For browser global
if (typeof window !== "undefined") {
  window.MultiAgentAPIClient = MultiAgentAPIClient;
  window.getAuthToken = getAuthToken;
  window.APIError = APIError;
  window.API_CONFIG = API_CONFIG;
}

// ============================================================================
// QUICK TEST (uncomment to run in browser console or Node.js)
// ============================================================================

/*
(async () => {
  console.log("🚀 Testing Multi-Agent API Client...\n");
  await example5_completeWorkflow();
})();
*/
