/**
 * CLIENT-SIDE POLLING IMPLEMENTATION
 * 
 * Use this pattern in your frontend to get real-time updates
 */

// Configuration
const API_URL = 'https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1';
const POLL_INTERVAL = 2000; // 2 seconds
const MAX_POLL_TIME = 30000; // 30 seconds timeout

/**
 * Submit a report and poll for completion
 */
async function submitReportWithPolling(reportData, authToken) {
  // Step 1: Submit report
  const submitResponse = await fetch(`${API_URL}/api/v1/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify(reportData)
  });

  const submitResult = await submitResponse.json();
  const jobId = submitResult.job_id;

  console.log('Report submitted. Job ID:', jobId);
  showLoadingUI('Processing your report...');

  // Step 2: Poll for status
  const result = await pollForCompletion(jobId, authToken);

  return result;
}

/**
 * Poll status endpoint until job is complete
 */
async function pollForCompletion(jobId, authToken) {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      try {
        // Check if timeout exceeded
        if (Date.now() - startTime > MAX_POLL_TIME) {
          clearInterval(pollInterval);
          reject(new Error('Timeout: Job took too long to process'));
          return;
        }

        // Call status endpoint
        const response = await fetch(`${API_URL}/api/v1/status/${jobId}`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        const result = await response.json();

        console.log('Poll response:', result.status);

        // Check status
        if (result.status === 'processing' || result.action === 'WAIT') {
          // Still processing, continue polling
          updateLoadingUI(`${result.message || 'Processing...'} (${Math.floor((Date.now() - startTime) / 1000)}s)`);
          return;
        }

        // Job complete!
        clearInterval(pollInterval);
        hideLoadingUI();

        // Handle different outcomes
        if (result.status === 'needs_clarification') {
          // Agent needs more info
          showClarificationPrompt(result.data.ui.message, result.data.conversationContext);
          resolve(result);
        } else if (result.status === 'success') {
          // Success!
          showSuccessMessage(result.data.ui.message);
          
          // Update map if coordinates available
          if (result.data.map && result.data.map.data.length > 0) {
            updateMap(result.data.map);
          }
          
          resolve(result);
        } else {
          // Error
          reject(new Error(result.error || 'Unknown error'));
        }

      } catch (error) {
        clearInterval(pollInterval);
        hideLoadingUI();
        reject(error);
      }
    }, POLL_INTERVAL);
  });
}

/**
 * Submit a query and poll for results
 */
async function submitQueryWithPolling(question, domainId, authToken) {
  const submitResponse = await fetch(`${API_URL}/api/v1/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      domain_id: domainId,
      question: question
    })
  });

  const submitResult = await submitResponse.json();
  const jobId = submitResult.job_id;

  console.log('Query submitted. Job ID:', jobId);
  showLoadingUI('Analyzing your question...');

  const result = await pollForCompletion(jobId, authToken);
  return result;
}

/**
 * Handle clarification follow-up
 */
async function submitClarification(originalJobId, clarificationText, authToken) {
  // Re-submit with context
  const response = await fetch(`${API_URL}/api/v1/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      domain_id: 'civic_complaints',
      text: clarificationText,
      context: {
        previous_job_id: originalJobId,
        is_clarification: true
      }
    })
  });

  const result = await response.json();
  return pollForCompletion(result.job_id, authToken);
}

// ============================================
// UI Helper Functions (implement these)
// ============================================

function showLoadingUI(message) {
  console.log('Loading:', message);
  // Show spinner/loading indicator in your UI
  // Example: document.getElementById('loading').textContent = message;
}

function updateLoadingUI(message) {
  console.log('Loading update:', message);
  // Update loading message
}

function hideLoadingUI() {
  console.log('Loading complete');
  // Hide loading indicator
}

function showSuccessMessage(message) {
  console.log('Success:', message);
  // Show success toast/notification
}

function showClarificationPrompt(question, context) {
  console.log('Clarification needed:', question);
  // Show input field with the clarification question
  // Save context for follow-up submission
}

function updateMap(mapData) {
  console.log('Updating map:', mapData);
  // Update your map component with new data
  // Example for Leaflet:
  // mapData.data.forEach(point => {
  //   L.marker([point.geometry.lat, point.geometry.lon])
  //     .addTo(map)
  //     .bindPopup(JSON.stringify(point.fullReport));
  // });
}

// ============================================
// EXAMPLE USAGE
// ============================================

// Example 1: Submit a report
async function exampleSubmitReport() {
  try {
    const result = await submitReportWithPolling({
      domain_id: 'civic_complaints',
      text: 'Broken streetlight on Main Street near the park. Not working for 3 days.',
      priority: 'high'
    }, 'YOUR_JWT_TOKEN');

    console.log('Final result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
}

// Example 2: Submit a query
async function exampleSubmitQuery() {
  try {
    const result = await submitQueryWithPolling(
      'Where are all the streetlight issues?',
      'civic_complaints',
      'YOUR_JWT_TOKEN'
    );

    console.log('Query result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
}

// Example 3: Handle clarification
async function exampleHandleClarification(originalJobId) {
  try {
    const result = await submitClarification(
      originalJobId,
      'It happened yesterday morning around 8 AM',
      'YOUR_JWT_TOKEN'
    );

    console.log('Clarification result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
}

// Export for use in your app
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    submitReportWithPolling,
    submitQueryWithPolling,
    submitClarification,
    pollForCompletion
  };
}
