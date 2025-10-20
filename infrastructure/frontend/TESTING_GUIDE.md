# Testing Guide for API Integration and Fixes

This document provides comprehensive testing instructions for all features implemented in the API integration and fixes spec.

## Prerequisites

1. Backend services deployed and running
2. Frontend development server running (`npm run dev` in `infrastructure/frontend`)
3. Valid user credentials for authentication
4. Browser with developer tools open

## Test Environment Setup

```bash
# Start frontend (if not already running)
cd infrastructure/frontend
npm run dev

# Frontend will be available at: http://localhost:3000
```

## 9.1 Agent CRUD Operations Testing

### Test Case 1.1: Create Custom Ingestion Agent

**Steps:**
1. Navigate to http://localhost:3000/agents
2. Click "Create Agent" button
3. Select "Data Ingest Agent" tab
4. Fill in the form:
   - Agent Name: "Test Ingest Agent"
   - Tools: Select "bedrock", "location_proxy"
   - System Prompt: "Extract location and priority from civic complaints"
   - Output Schema:
     - Field 1: name="location", type="string"
     - Field 2: name="priority", type="number"
     - Field 3: name="confidence", type="number"
5. Click "Create Agent"

**Expected Results:**
- ✅ Success toast appears: "Agent created successfully"
- ✅ Agent appears in the list with "Custom" tag
- ✅ Agent card shows correct name and type
- ✅ Agent count in "Custom" tab increases by 1

### Test Case 1.2: Create Custom Query Agent with Parent

**Steps:**
1. Click "Create Agent" button
2. Select "Data Query Agent" tab
3. Fill in the form:
   - Agent Name: "Test Query Agent"
   - Parent Agent: Select "When Agent" from dropdown
   - Tools: Select "bedrock", "retrieval_api"
   - System Prompt: "Analyze temporal patterns in incidents"
   - Output Schema:
     - Field 1: name="pattern", type="string"
     - Field 2: name="insight", type="string"
4. Click "Create Agent"

**Expected Results:**
- ✅ Success toast appears
- ✅ Agent appears with parent relationship indicator
- ✅ Agent is listed in "Custom" filter

### Test Case 1.3: List Agents and Verify Filtering

**Steps:**
1. Click "All" tab
2. Verify count matches total agents
3. Click "Built-in" tab
4. Verify only built-in agents shown (should be 17: 6 ingestion + 11 query)
5. Click "Custom" tab
6. Verify only custom agents shown (the 2 created above)

**Expected Results:**
- ✅ All tabs show correct counts
- ✅ Filtering works correctly
- ✅ Built-in agents have "Built-in" badge
- ✅ Custom agents have "Created by me" badge

### Test Case 1.4: Update Agent Configuration

**Steps:**
1. Find "Test Ingest Agent" in the list
2. Click "Edit" button
3. Modify:
   - System Prompt: "Extract location, priority, and category from civic complaints"
   - Add output field: name="category", type="string"
4. Click "Update Agent"

**Expected Results:**
- ✅ Success toast: "Agent updated successfully"
- ✅ Agent card reflects changes
- ✅ Agent list refreshes automatically

### Test Case 1.5: Delete Custom Agent

**Steps:**
1. Find "Test Query Agent" in the list
2. Click "Delete" button
3. Confirm deletion in dialog
4. Wait for deletion to complete

**Expected Results:**
- ✅ Confirmation dialog appears
- ✅ Success toast: "Agent deleted successfully"
- ✅ Agent removed from list
- ✅ Custom count decreases by 1

### Test Case 1.6: Verify Built-in Agents Cannot Be Deleted

**Steps:**
1. Switch to "Built-in" tab
2. Find any built-in agent (e.g., "Geo Agent")
3. Verify no "Delete" button is visible
4. Verify "Edit" button is also not visible

**Expected Results:**
- ✅ Built-in agents show no edit/delete buttons
- ✅ Only "View Details" or similar read-only actions available

---

## 9.2 Domain Creation Flow Testing

### Test Case 2.1: Open Domain Creation Wizard

**Steps:**
1. Navigate to http://localhost:3000/manage
2. Click "Create Domain" button
3. Verify wizard opens with Stage 1

**Expected Results:**
- ✅ Dialog opens with "Create Domain - Stage 1 of 2" title
- ✅ Domain name and description fields visible
- ✅ Ingestion agents list displayed
- ✅ "Next" button is disabled (no agents selected yet)

### Test Case 2.2: Select Ingestion Agents (Stage 1)

**Steps:**
1. Enter domain name: "Test Traffic Domain"
2. Enter description: "Testing domain creation with traffic agents"
3. Select 2 ingestion agents:
   - ✅ Geo Agent
   - ✅ Temporal Agent
4. Verify selected count badge shows "2 selected"
5. Verify dependency graph appears below showing parallel execution

**Expected Results:**
- ✅ Selected agents are highlighted
- ✅ Count badge updates correctly
- ✅ Dependency graph shows both agents in parallel
- ✅ "Next" button becomes enabled

### Test Case 2.3: Verify Dependency Graph Shows Parallel Execution

**Steps:**
1. Observe the dependency graph visualization
2. Verify both selected agents appear in "Ingestion Layer"
3. Verify they are shown horizontally (parallel execution)

**Expected Results:**
- ✅ Graph shows "Parallel: [Geo Agent] [Temporal Agent]"
- ✅ No arrows between them (indicating parallel execution)
- ✅ Graph updates in real-time as agents are selected/deselected

### Test Case 2.4: Proceed to Stage 2

**Steps:**
1. Click "Next: Select Query Agents" button
2. Verify stage indicator changes to "Stage 2 of 2"
3. Verify query agents list is displayed

**Expected Results:**
- ✅ Stage 2 UI appears
- ✅ Query agents list shows all 11 built-in query agents
- ✅ "Create" button is disabled (no agents selected yet)
- ✅ "Back" button is visible

### Test Case 2.5: Select Query Agents (Stage 2)

**Steps:**
1. Select 3 query agents:
   - ✅ When Agent
   - ✅ Where Agent
   - ✅ Why Agent
2. Verify selected count badge shows "3 selected"
3. Verify dependency graph updates to show query layer

**Expected Results:**
- ✅ Selected agents are highlighted
- ✅ Count badge updates correctly
- ✅ Dependency graph shows query layer below ingestion layer
- ✅ "Create" button becomes enabled

### Test Case 2.6: Verify Dependency Graph Updates

**Steps:**
1. Observe the complete dependency graph
2. Verify it shows both layers:
   - Ingestion Layer: Geo Agent, Temporal Agent (parallel)
   - Query Layer: When Agent, Where Agent, Why Agent (parallel)

**Expected Results:**
- ✅ Graph shows both layers clearly separated
- ✅ Query agents shown in parallel (no parent relationships)
- ✅ Visual distinction between layers

### Test Case 2.7: Create Domain

**Steps:**
1. Click "Create Domain" button
2. Wait for API call to complete

**Expected Results:**
- ✅ Success toast: "Domain created successfully"
- ✅ Dialog closes
- ✅ Domain appears in manage page list
- ✅ Domain has "Created by me" badge
- ✅ Domain shows correct agent count (5 agents)

### Test Case 2.8: Verify Domain Appears in List

**Steps:**
1. Verify "Test Traffic Domain" appears in domain list
2. Check domain card shows:
   - Domain name
   - Description
   - "Created by me" badge
   - Agent count: 5
   - "Ask Question" and "Submit Report" buttons

**Expected Results:**
- ✅ Domain card displays all information correctly
- ✅ Actions are available
- ✅ Domain is selectable

---

## 9.3 Real-Time Status Updates Testing

### Test Case 3.1: Submit Report with Domain Selected

**Steps:**
1. Navigate to http://localhost:3000/dashboard
2. Select "Test Traffic Domain" from domain selector
3. Enter report text: "Traffic accident at Main St and 5th Ave at 3pm today"
4. Click "Submit Report"

**Expected Results:**
- ✅ Submit button shows loading state
- ✅ ExecutionStatusPanel appears
- ✅ Job ID is displayed
- ✅ Agent list shows all 5 agents

### Test Case 3.2: Verify ExecutionStatusPanel Appears

**Steps:**
1. Observe the status panel that appears after submission
2. Verify it shows:
   - Job ID
   - List of agents in execution order
   - Initial status for each agent

**Expected Results:**
- ✅ Panel is visible and styled correctly
- ✅ All agents from domain are listed
- ✅ Initial status is "waiting" for all agents

### Test Case 3.3: Verify Agents Show "Invoking" Status

**Steps:**
1. Watch the status panel as execution progresses
2. Observe agents transitioning to "invoking" state
3. Verify status icon changes to spinning loader

**Expected Results:**
- ✅ Agents transition from "waiting" to "invoking"
- ✅ Spinning loader icon appears
- ✅ Status message updates: "Invoking agent..."
- ✅ Updates happen in real-time via WebSocket

### Test Case 3.4: Verify Agents Show "Complete" with Confidence

**Steps:**
1. Wait for agents to complete execution
2. Observe status transitions to "complete"
3. Verify confidence score badge appears

**Expected Results:**
- ✅ Status icon changes to green checkmark
- ✅ Status message: "Complete"
- ✅ Confidence badge appears (e.g., "95%")
- ✅ Badge color indicates confidence level:
  - Green for >= 90%
  - Yellow for 70-89%
  - Red for < 70%

### Test Case 3.5: Verify Confidence Badges Display Correctly

**Steps:**
1. Check each completed agent's confidence badge
2. Verify color coding matches confidence level
3. Verify percentage is displayed correctly

**Expected Results:**
- ✅ Geo Agent: Shows confidence (e.g., 95%)
- ✅ Temporal Agent: Shows confidence (e.g., 92%)
- ✅ Query agents: Show confidence scores
- ✅ Color coding is correct

---

## 9.4 Confidence-Based Clarification Testing

### Test Case 4.1: Submit Report with Ambiguous Location

**Steps:**
1. Select a domain with Geo Agent
2. Enter ambiguous report: "Pothole on Main Street"
3. Click "Submit Report"
4. Wait for processing to complete

**Expected Results:**
- ✅ Report is processed
- ✅ Geo Agent returns low confidence (< 0.9)
- ✅ System detects low confidence

### Test Case 4.2: Verify Low Confidence Detected

**Steps:**
1. Observe the execution status panel
2. Check Geo Agent's confidence score
3. Verify it's below 0.9 (e.g., 0.65)

**Expected Results:**
- ✅ Confidence badge shows red color
- ✅ Confidence score is < 90%
- ✅ System prepares clarification dialog

### Test Case 4.3: Verify ClarificationDialog Appears

**Steps:**
1. After job completion, clarification dialog should appear
2. Verify dialog content:
   - Title: "Additional Information Needed"
   - Low confidence fields listed
   - Targeted questions for each field

**Expected Results:**
- ✅ Dialog appears automatically
- ✅ Shows "Low Confidence Detected" message
- ✅ Lists affected fields (e.g., "Location")
- ✅ Shows current value and confidence score
- ✅ Displays clarification question

### Test Case 4.4: Provide Clarification Details

**Steps:**
1. Read the clarification question: "Which Main Street? Please provide city, cross streets, or nearby landmarks."
2. Enter clarification: "Main Street in downtown, near City Hall, between 1st and 2nd Avenue"
3. Verify textarea accepts input

**Expected Results:**
- ✅ Question is specific and helpful
- ✅ Textarea is functional
- ✅ Input is captured correctly

### Test Case 4.5: Submit Clarification

**Steps:**
1. Click "Submit Clarification" button
2. Observe re-processing

**Expected Results:**
- ✅ Dialog closes
- ✅ New job is submitted with enhanced context
- ✅ ExecutionStatusPanel appears again
- ✅ Original text + clarification is sent to agents

### Test Case 4.6: Verify Report Re-Processed

**Steps:**
1. Watch the execution status panel
2. Verify agents process the enhanced input
3. Wait for completion

**Expected Results:**
- ✅ All agents execute again
- ✅ Status updates appear in real-time
- ✅ Processing completes successfully

### Test Case 4.7: Verify Confidence Improves

**Steps:**
1. Check Geo Agent's new confidence score
2. Verify it's now >= 0.9 (e.g., 0.95)
3. Verify no further clarification is needed

**Expected Results:**
- ✅ Confidence score improves (e.g., 65% → 95%)
- ✅ Badge color changes to green
- ✅ No clarification dialog appears
- ✅ Results are displayed on map

---

## 9.5 Geometry Rendering Testing

### Test Case 5.1: Submit Report with Single Location (Point)

**Steps:**
1. Navigate to dashboard
2. Select domain with Geo Agent
3. Enter report: "Fire hydrant broken at 123 Main Street"
4. Submit and wait for completion
5. Navigate to map view

**Expected Results:**
- ✅ Geo Agent detects geometry_type: "Point"
- ✅ Map shows marker at location
- ✅ Marker uses category-specific color
- ✅ Marker has custom icon

### Test Case 5.2: Verify Marker Appears on Map

**Steps:**
1. Observe the map view
2. Verify marker is placed at correct coordinates
3. Click on marker

**Expected Results:**
- ✅ Marker is visible and correctly positioned
- ✅ Marker color matches incident category
- ✅ Click opens popup with incident details
- ✅ Popup shows all structured data

### Test Case 5.3: Submit Report with "from X to Y" (LineString)

**Steps:**
1. Enter report: "Road construction from Main Street to Oak Avenue along Highway 101"
2. Submit and wait for completion
3. Navigate to map view

**Expected Results:**
- ✅ Geo Agent detects geometry_type: "LineString"
- ✅ Geo Agent extracts multiple coordinates
- ✅ Map rendering function receives LineString data

### Test Case 5.4: Verify Line Appears on Map

**Steps:**
1. Observe the map view
2. Verify line is drawn connecting the locations
3. Hover over line
4. Click on line

**Expected Results:**
- ✅ Line is visible with category color
- ✅ Line width is 4px
- ✅ Line opacity is 80%
- ✅ Hover changes cursor to pointer
- ✅ Click opens popup with incident details

### Test Case 5.5: Submit Report with "area" or "zone" (Polygon)

**Steps:**
1. Enter report: "Power outage affecting the downtown area bounded by 1st St, 5th St, Main Ave, and Oak Ave"
2. Submit and wait for completion
3. Navigate to map view

**Expected Results:**
- ✅ Geo Agent detects geometry_type: "Polygon"
- ✅ Geo Agent extracts boundary coordinates
- ✅ Map rendering function receives Polygon data

### Test Case 5.6: Verify Polygon Appears on Map

**Steps:**
1. Observe the map view
2. Verify polygon area is filled
3. Verify polygon has border
4. Hover over polygon
5. Click on polygon

**Expected Results:**
- ✅ Polygon fill is visible with 30% opacity
- ✅ Polygon border is visible with category color
- ✅ Border width is 2px
- ✅ Hover changes cursor to pointer
- ✅ Click opens popup with incident details

### Test Case 5.7: Test Click Interactions for All Types

**Steps:**
1. Click on Point marker
2. Verify popup appears with incident details
3. Click on LineString
4. Verify popup appears at click location
5. Click on Polygon
6. Verify popup appears at click location

**Expected Results:**
- ✅ All geometry types respond to clicks
- ✅ Popups show correct incident information
- ✅ Popups are positioned correctly
- ✅ Popups can be closed

---

## 9.6 Network Error Fixes Testing

### Test Case 6.1: Refresh Page Multiple Times

**Steps:**
1. Navigate to http://localhost:3000/dashboard
2. Wait for page to load completely
3. Press F5 to refresh
4. Wait for page to load
5. Repeat 5 times

**Expected Results:**
- ✅ No "NetworkError" toasts appear
- ✅ No "Failed to load domains" errors
- ✅ Page loads successfully each time
- ✅ API client initializes properly

### Test Case 6.2: Verify No "NetworkError" Toasts Appear

**Steps:**
1. Open browser developer console
2. Monitor console for errors
3. Refresh page
4. Check for network-related errors

**Expected Results:**
- ✅ No "NetworkError when attempting to fetch resource" messages
- ✅ No initialization timeout errors
- ✅ Auth session loads correctly
- ✅ API requests succeed

### Test Case 6.3: Disconnect Network

**Steps:**
1. Open browser developer tools
2. Go to Network tab
3. Set throttling to "Offline"
4. Try to submit a report

**Expected Results:**
- ✅ Appropriate error toast appears
- ✅ Error message is user-friendly
- ✅ No crash or undefined errors
- ✅ UI remains functional

### Test Case 6.4: Attempt API Call While Offline

**Steps:**
1. While offline, click "Submit Report"
2. Observe error handling

**Expected Results:**
- ✅ Error toast: "Network error - Please check your connection"
- ✅ Submit button returns to normal state
- ✅ Form data is preserved
- ✅ User can retry after reconnecting

### Test Case 6.5: Verify Appropriate Error Toast

**Steps:**
1. Check the error toast content
2. Verify it's user-friendly and actionable

**Expected Results:**
- ✅ Toast shows network icon
- ✅ Message is clear: "Network error"
- ✅ Description suggests checking connection
- ✅ Toast auto-dismisses after 5 seconds

### Test Case 6.6: Reconnect Network

**Steps:**
1. Set network throttling back to "Online"
2. Click "Submit Report" again

**Expected Results:**
- ✅ Request succeeds
- ✅ No errors appear
- ✅ Normal flow continues

### Test Case 6.7: Verify Retry Succeeds

**Steps:**
1. Monitor network tab
2. Verify retry logic works for 5xx errors
3. Simulate server error (if possible)

**Expected Results:**
- ✅ Retry logic activates for 5xx errors
- ✅ Exponential backoff is applied (1s, 2s, 4s)
- ✅ Maximum 3 retries attempted
- ✅ Success after retry shows no error

---

## 9.7 Bug Fixes

### Bugs to Document and Fix

As you perform the above tests, document any bugs found in this format:

#### Bug Template

**Bug ID:** BUG-001
**Severity:** Critical / High / Medium / Low
**Component:** [Component name]
**Description:** [What went wrong]
**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:** [What should happen]
**Actual Behavior:** [What actually happened]
**Screenshots/Logs:** [If applicable]
**Fix Applied:** [Description of fix]
**Verification:** [How to verify the fix works]

---

## Automated Testing

### Running Existing Tests

```bash
# Run all tests
cd infrastructure/frontend
npm test

# Run specific test file
npm test -- lib/__tests__/api-client.test.ts

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Test Coverage Goals

- API Client: 80%+ coverage
- Components: 70%+ coverage
- Utilities: 90%+ coverage

---

## Performance Testing

### Load Testing Checklist

- [ ] Test with 10+ agents in domain
- [ ] Test with 100+ incidents on map
- [ ] Test rapid agent creation (10 in 1 minute)
- [ ] Test WebSocket connection stability (30+ minutes)
- [ ] Test clarification loop (3 rounds)

### Performance Metrics

- Page load time: < 2 seconds
- API response time: < 500ms
- WebSocket latency: < 100ms
- Map rendering: < 1 second for 100 incidents

---

## Security Testing

### Security Checklist

- [ ] Verify JWT token is included in all API requests
- [ ] Verify unauthorized users cannot access protected routes
- [ ] Verify users can only delete their own custom agents
- [ ] Verify built-in agents cannot be modified
- [ ] Verify input validation prevents XSS
- [ ] Verify SQL injection protection (if applicable)

---

## Browser Compatibility

Test in the following browsers:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

---

## Mobile Responsiveness

Test on the following screen sizes:

- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

---

## Accessibility Testing

- [ ] Keyboard navigation works
- [ ] Screen reader compatibility
- [ ] Color contrast meets WCAG AA standards
- [ ] Focus indicators are visible
- [ ] Form labels are properly associated

---

## Test Results Summary

After completing all tests, fill in this summary:

### Test Execution Summary

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Dev/Staging/Prod]

**Total Test Cases:** 40+
**Passed:** ___
**Failed:** ___
**Blocked:** ___
**Not Executed:** ___

**Pass Rate:** ___%

### Critical Issues Found

1. [Issue 1]
2. [Issue 2]
3. [Issue 3]

### Recommendations

1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

---

## Next Steps

After completing all tests:

1. Document all bugs found
2. Prioritize bugs by severity
3. Fix critical and high-priority bugs
4. Re-test fixed bugs
5. Update this document with results
6. Mark task 9 as complete in tasks.md
