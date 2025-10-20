/**
 * AppSync Client Example for Real-time Status Updates
 *
 * This example shows how to subscribe to job status updates using AWS AppSync.
 * The client receives real-time notifications as agents execute and the job progresses.
 */

const https = require('https');
const crypto = require('crypto');
const WebSocket = require('ws');

// Configuration
const APPSYNC_API_URL = process.env.APPSYNC_API_URL || 'https://your-api-id.appsync-api.us-east-1.amazonaws.com/graphql';
const APPSYNC_API_KEY = process.env.APPSYNC_API_KEY || 'your-api-key-here';
const USER_ID = process.env.USER_ID || 'demo-user';

// GraphQL subscription query
const SUBSCRIPTION_QUERY = `
  subscription OnStatusUpdate($userId: ID!) {
    onStatusUpdate(userId: $userId) {
      jobId
      userId
      agentName
      status
      message
      timestamp
      metadata
    }
  }
`;

/**
 * Subscribe to status updates for a specific user
 */
class AppSyncStatusSubscriber {
  constructor(apiUrl, apiKey, userId) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
    this.userId = userId;
    this.ws = null;
    this.subscriptionId = null;
    this.statusCallbacks = [];
  }

  /**
   * Register a callback for status updates
   */
  onStatus(callback) {
    this.statusCallbacks.push(callback);
  }

  /**
   * Start the subscription
   */
  async subscribe() {
    console.log(`Subscribing to status updates for user: ${this.userId}`);

    // Build subscription payload
    const subscriptionPayload = {
      query: SUBSCRIPTION_QUERY,
      variables: {
        userId: this.userId
      }
    };

    // Encode subscription payload
    const encodedPayload = Buffer.from(JSON.stringify(subscriptionPayload)).toString('base64');

    // Build WebSocket URL
    const wsUrl = this.apiUrl
      .replace('https://', 'wss://')
      .replace('/graphql', '/realtime');

    const header = Buffer.from(JSON.stringify({
      host: new URL(this.apiUrl).host,
      'x-api-key': this.apiKey
    })).toString('base64');

    const url = `${wsUrl}?header=${header}&payload=${encodedPayload}`;

    // Connect WebSocket
    this.ws = new WebSocket(url, ['graphql-ws']);

    this.ws.on('open', () => {
      console.log('WebSocket connected');

      // Send connection init
      this.ws.send(JSON.stringify({
        type: 'connection_init'
      }));
    });

    this.ws.on('message', (data) => {
      const message = JSON.parse(data);
      this.handleMessage(message);
    });

    this.ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    this.ws.on('close', () => {
      console.log('WebSocket closed');
      this.subscriptionId = null;
    });
  }

  /**
   * Handle WebSocket messages
   */
  handleMessage(message) {
    console.log('Received message:', JSON.stringify(message, null, 2));

    switch (message.type) {
      case 'connection_ack':
        console.log('Connection acknowledged');
        this.startSubscription();
        break;

      case 'start_ack':
        console.log('Subscription started');
        this.subscriptionId = message.id;
        break;

      case 'data':
        const statusUpdate = message.payload.data.onStatusUpdate;
        this.handleStatusUpdate(statusUpdate);
        break;

      case 'error':
        console.error('Subscription error:', message.payload);
        break;

      case 'complete':
        console.log('Subscription completed');
        break;

      case 'ka':
        // Keep-alive
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  /**
   * Start the GraphQL subscription
   */
  startSubscription() {
    const startMessage = {
      id: crypto.randomUUID(),
      type: 'start',
      payload: {
        data: JSON.stringify({
          query: SUBSCRIPTION_QUERY,
          variables: {
            userId: this.userId
          }
        }),
        extensions: {
          authorization: {
            'x-api-key': this.apiKey
          }
        }
      }
    };

    this.ws.send(JSON.stringify(startMessage));
  }

  /**
   * Handle status update
   */
  handleStatusUpdate(update) {
    console.log('\n--- Status Update ---');
    console.log(`Job ID: ${update.jobId}`);
    console.log(`Status: ${update.status}`);
    console.log(`Message: ${update.message}`);

    if (update.agentName) {
      console.log(`Agent: ${update.agentName}`);
    }

    if (update.metadata) {
      console.log(`Metadata: ${JSON.stringify(JSON.parse(update.metadata), null, 2)}`);
    }

    console.log(`Timestamp: ${update.timestamp}`);
    console.log('-------------------\n');

    // Call registered callbacks
    this.statusCallbacks.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in status callback:', error);
      }
    });
  }

  /**
   * Stop the subscription
   */
  unsubscribe() {
    if (this.ws && this.subscriptionId) {
      this.ws.send(JSON.stringify({
        type: 'stop',
        id: this.subscriptionId
      }));
    }

    if (this.ws) {
      this.ws.close();
    }
  }
}

/**
 * HTTP client for making GraphQL queries
 */
async function makeGraphQLRequest(query, variables = {}) {
  const payload = JSON.stringify({
    query,
    variables
  });

  const url = new URL(APPSYNC_API_URL);

  const options = {
    hostname: url.hostname,
    path: url.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': APPSYNC_API_KEY,
      'Content-Length': Buffer.byteLength(payload)
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.errors) {
            reject(new Error(JSON.stringify(response.errors)));
          } else {
            resolve(response.data);
          }
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(payload);
    req.end();
  });
}

/**
 * Example: Submit a report and monitor status in real-time
 */
async function submitReportAndMonitor() {
  const API_BASE_URL = process.env.API_BASE_URL || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev';

  // Create subscriber
  const subscriber = new AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID);

  // Track job completion
  let jobCompleted = false;
  let jobResult = null;

  // Register status callback
  subscriber.onStatus((update) => {
    if (update.status === 'complete' || update.status === 'error') {
      jobCompleted = true;
      jobResult = update;
    }
  });

  // Start subscription
  await subscriber.subscribe();

  // Wait for connection
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Submit report
  console.log('Submitting report...');
  const reportPayload = {
    domain_id: 'civic_complaints',
    text: 'There is a large pothole at the intersection of Main Street and 5th Avenue causing traffic issues',
    source: 'web',
    priority: 'normal'
  };

  const ingestUrl = `${API_BASE_URL}/api/v1/ingest`;
  const ingestResponse = await fetch(ingestUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': 'default-tenant'
    },
    body: JSON.stringify(reportPayload)
  });

  const ingestResult = await ingestResponse.json();
  console.log('Report submitted:', ingestResult);
  console.log('Job ID:', ingestResult.job_id);

  // Wait for job completion
  console.log('\nMonitoring job progress...\n');
  while (!jobCompleted) {
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log('\nJob completed!');
  console.log('Final result:', jobResult);

  // Clean up
  subscriber.unsubscribe();
}

/**
 * Example: Monitor multiple jobs simultaneously
 */
async function monitorMultipleJobs(jobIds) {
  const subscriber = new AppSyncStatusSubscriber(APPSYNC_API_URL, APPSYNC_API_KEY, USER_ID);

  const jobStatus = {};
  jobIds.forEach(id => {
    jobStatus[id] = {
      started: false,
      completed: false,
      updates: []
    };
  });

  subscriber.onStatus((update) => {
    const jobId = update.jobId;

    if (jobStatus[jobId]) {
      jobStatus[jobId].started = true;
      jobStatus[jobId].updates.push(update);

      if (update.status === 'complete' || update.status === 'error') {
        jobStatus[jobId].completed = true;
      }

      // Check if all jobs completed
      const allCompleted = Object.values(jobStatus).every(job => job.completed);
      if (allCompleted) {
        console.log('\nAll jobs completed!');
        console.log('Summary:', JSON.stringify(jobStatus, null, 2));
        subscriber.unsubscribe();
      }
    }
  });

  await subscriber.subscribe();
  console.log(`Monitoring ${jobIds.length} jobs...`);
}

/**
 * Browser-compatible fetch-based example
 */
const BrowserAppSyncClient = {
  apiUrl: APPSYNC_API_URL,
  apiKey: APPSYNC_API_KEY,

  async subscribe(userId, onStatusUpdate) {
    const subscriptionPayload = {
      query: SUBSCRIPTION_QUERY,
      variables: { userId }
    };

    const encodedPayload = btoa(JSON.stringify(subscriptionPayload));
    const header = btoa(JSON.stringify({
      host: new URL(this.apiUrl).host,
      'x-api-key': this.apiKey
    }));

    const wsUrl = this.apiUrl
      .replace('https://', 'wss://')
      .replace('/graphql', '/realtime');

    const url = `${wsUrl}?header=${header}&payload=${encodedPayload}`;

    const ws = new WebSocket(url, ['graphql-ws']);

    ws.onopen = () => {
      console.log('Connected to AppSync');
      ws.send(JSON.stringify({ type: 'connection_init' }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'connection_ack') {
        ws.send(JSON.stringify({
          id: crypto.randomUUID(),
          type: 'start',
          payload: {
            data: JSON.stringify(subscriptionPayload),
            extensions: {
              authorization: { 'x-api-key': this.apiKey }
            }
          }
        }));
      } else if (message.type === 'data') {
        onStatusUpdate(message.payload.data.onStatusUpdate);
      }
    };

    return ws;
  }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    AppSyncStatusSubscriber,
    makeGraphQLRequest,
    submitReportAndMonitor,
    monitorMultipleJobs,
    BrowserAppSyncClient
  };
}

// Example usage
if (require.main === module) {
  console.log('AppSync Real-time Status Monitor');
  console.log('================================\n');

  // Check if WebSocket is available
  if (typeof WebSocket === 'undefined') {
    console.error('WebSocket not available. Install ws package: npm install ws');
    process.exit(1);
  }

  // Run example
  submitReportAndMonitor()
    .catch(error => {
      console.error('Error:', error);
      process.exit(1);
    });
}
