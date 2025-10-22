# Manual Testing Guide for API Integration and Fixes

This guide provides step-by-step instructions for manually testing all features implemented in the API integration and fixes spec.

## Prerequisites

1. Frontend is running: `npm run dev` in `infrastructure/frontend`
2. Backend APIs are deployed and accessible
3. User is logged in with valid credentials

## Test 9.1: Agent CRUD Operations

### Test 9.1.1: Create Custom Ingestion Agent

**Steps:**
1. Navigate to `/agents` page
2. Click "Create Agent" button
3. Select "Data Ingest Agent" tab
4. Fill in the form:
   - Agent Name: "Test Ingest Agent"
   - Tools: Select "bedrock" and "comprehend"
   - System Prompt: "Extract priority level from civic complaints"
   - Output Schema:
     - Field 1: name="priority", type="string"
     - Field 2: name="confidence", type="number"
5. Click "Create Agent"

**Expected Results:**
- ✅ Success toast appears: "Agent created successfully"
- ✅ Agent appears in the list with "Created by me" tag
- ✅ Agent shows "Data Ingest" type badge
- ✅ Agent card displays correct name and tools

### Test 9.1.2: Create Custom Query Agent with Parent

**Steps:**
1. Click "Create Agent" button again
2. Select "Data Query Agent" tab
3. Fill in the form:
   - Agent Name: "Test Query Agent"
   - Parent Agent: Select "When Agent" from dropdown
   - Tools: Select "bedrock" and "retrieval_api"
   - System Prompt: "Analyze temporal patterns in incidents"
   - Output Schema:
     - Field 1: name="pattern", type="string"
     - Field 2: name="insight", type="string"
4. Click "Create Agent"

**Expected Results:**
- ✅ Success toast appears: "Agent created successfully"
- ✅ Agent appears in the list with "Created by me" tag
- ✅ Agent shows "Data Query" type badge
- ✅ Parent agent relationship is saved (verify in edit mode)

### Test 9.1.3: List Agents and Verify Filtering

**Steps:**
1. Click "All" tab - should show all agents (built-in + custom)
2. Click "Built-in" tab - should show only built-in agents
3. Click "Custom" tab - should show only custom agents
4. Verify counts in tab labels match displayed agents

**Expected Results:**
- ✅ "All" tab shows 19+ agents (17 built-in + 2 custom)
- ✅ "Built-in" tab shows 17 agents (6 ingest + 11 query)
- ✅ "Custom" tab shows 2 agents (the ones we just created)
- ✅ Tab counts are accurate
- ✅ Built-in agents show "Built-in" badge
- ✅ Custom agents show "Created by me" badge

### Test 9.1.4: Update Agent Configuration

**Steps:**
1. Find "Test Ingest Agent" in the list
2. Click "Edit" button
3. Modify the form:
   - System Prompt: "Extract priority level and urgency from civic complaints"
   - Add output field: name="urgency", type="string"
4. Click "Update Agent"

**Expected Results:**
- ✅ Success toast appears: "Agent updated successfully"
- ✅ Agent card shows updated system prompt (truncated)
- ✅ Re-open edit dialog to verify all changes were saved

### Test 9.1.5: Delete Custom Agent

**Steps:**
1. Find "Test Query Agent" in the list
2. Click "Delete" button
3. Confirm deletion in dialog

**Expected Results:**
- ✅ Confirmation dialog appears with agent name
- ✅ Success toast appears: "Agent deleted successfully"
- ✅ Agent is removed from the list
- ✅ Custom count decreases by 1

### Test 9.1.6: Verify Built-in Agents Cannot Be Deleted

**Steps:**
1. Find any built-in agent (e.g., "Geo Agent")
2. Verify no "Edit" or "Delete" buttons are shown

**Expected Results:**
- ✅ Built-in agents do not show Edit/Delete buttons
- ✅ Only custom agents show action buttons

---

## Test 9.2: Domain Creation Flow

### Test 9.2.1: Open Domain Creation Wizard

**Steps:**
1. Navigate to `/manage` page
2. Click "Create Domain" button (or similar)
3. Verify wizard opens with Stage 1

**Expected Results:**
- ✅ Dialog opens with "Create Domain - Stage 1 of 2" title
- ✅ Domain name and description fields are visible
- ✅ Ingestion agents are displayed
- ✅ "Next" button is disabled (no agents selected yet)

### Test 9.2.2: Select 2 Ingestion Agents in Stage 1

**Steps:**
1. Enter domain name: "Test Traffic Domain"
2. Enter description: "Testing domain creation flow"
3. Select "Geo Agent" checkbox
4. Select "Temporal Agent" checkbox
5. Verify selected count badge shows "2 selected"

**Expected Results:**
- ✅ Selected count badge updates to "2 selected"
- ✅ "Next" button becomes enabled
- ✅ Selected agents are visually highlighted

### Test 9.2.3: Verify Dependency Graph Shows Parallel Execution

**Steps:**
1. Scroll down to view dependency graph
2. Verify graph shows parallel execution for selected agents

**Expected Results:**
- ✅ Dependency graph section is visible
- ✅ Shows "Ingestion Layer" with "Parallel: Geo Agent, Temporal Agent"
- ✅ No sequential execution shown (no arrows)

### Test 9.2.4: Proceed to Stage 2

**Steps:**
1. Click "Next: Select Query Agents" button
2. Verify stage indicator updates to "Stage 2 of 2"

**Expected Results:**
- ✅ Stage indicator shows "Stage 2 of 2"
- ✅ Query agents are displayed
- ✅ "Create" button is disabled (no query agents selected yet)
- ✅ "Back" button is visible

### Test 9.2.5: Select 3 Query Agents

**Steps:**
1. Select "When Agent" checkbox
2. Select "Where Agent" checkbox
3. Select "Why Agent" checkbox
4. Verify selected count badge shows "3 selected"

**Expected Results:**
- ✅ Selected count badge updates to "3 selected"
- ✅ "Create" button becomes enabled
- ✅ Selected agents are visually highlighted

### Test 9.2.6: Verify Dependency Graph Updates

**Steps:**
1. Scroll down to view updated dependency graph
2. Verify graph shows both ingestion and query layers

**Expected Results:**
- ✅ Ingestion Layer shows: "Parallel: Geo Agent, Temporal Agent"
- ✅ Query Layer shows: "Parallel: When Agent, Where Agent, Why Agent"
- ✅ Graph updates in real-time as agents are selected/deselected

### Test 9.2.7: Create Domain

**Steps:**
1. Click "Create Domain" button
2. Wait for API response

**Expected Results:**
- ✅ Success toast appears: "Domain created successfully"
- ✅ Dialog closes
- ✅ Redirected to domain list or dashboard

### Test 9.2.8: Verify Domain Appears in List

**Steps:**
1. Navigate to `/manage` page
2. Find "Test Traffic Domain" in the list

**Expected Results:**
- ✅ Domain appears in the list
- ✅ Shows "Created by me" tag
- ✅ Shows agent count: 5 agents
- ✅ Shows description

---

## Test 9.3: Real-Time Status Updates

### Test 9.3.1: Submit Report with Domain Selected

**Steps:**
1. Navigate to dashboard
2. Select "Test Traffic Domain" from domain selector
3. Enter report text: "Traffic accident at Main St and 5th Ave at 2pm today"
4. Click "Submit Report"

**Expected Results:**
- ✅ Report submission succeeds
- ✅ Job ID is returned
- ✅ ExecutionStatusPanel appears

### Test 9.3.2: Verify ExecutionStatusPanel Appears

**Steps:**
1. Observe the execution status panel

**Expected Results:**
- ✅ Panel shows "Execution Status" title
- ✅ Lists all agents in execution order
- ✅ Shows initial "Waiting..." status for all agents

### Test 9.3.3: Verify Agents Show "Invoking" Status

**Steps:**
1. Watch status updates in real-time
2. Observe agents transitioning to "invoking" state

**Expected Results:**
- ✅ Agents show spinning loader icon when invoking
- ✅ Status message updates to "Invoking..."
- ✅ Status updates happen in real-time (WebSocket)

### Test 9.3.4: Verify Agents Show "Complete" with Confidence

**Steps:**
1. Wait for agents to complete execution
2. Observe completion status

**Expected Results:**
- ✅ Agents show green checkmark icon when complete
- ✅ Status message updates to "Complete"
- ✅ Confidence badge appears (e.g., "95%")
- ✅ Confidence badge is green if >= 90%, red if < 90%

### Test 9.3.5: Verify Confidence Badges Display Correctly

**Steps:**
1. Check confidence scores for all completed agents
2. Verify color coding

**Expected Results:**
- ✅ High confidence (>= 90%) shows green badge
- ✅ Low confidence (< 90%) shows red badge
- ✅ Percentage is displayed correctly (e.g., "95%")

---

## Test 9.4: Confidence-Based Clarification

### Test 9.4.1: Submit Report with Ambiguous Location

**Steps:**
1. Navigate to dashboard
2. Select a domain with Geo Agent
3. Enter ambiguous report: "Pothole on Main Street"
4. Click "Submit Report"
5. Wait for processing to complete

**Expected Results:**
- ✅ Report is processed
- ✅ Geo Agent returns low confidence (< 0.9)

### Test 9.4.2: Verify Low Confidence Detected

**Steps:**
1. Observe execution status panel
2. Check Geo Agent confidence score

**Expected Results:**
- ✅ Geo Agent shows confidence < 90% (e.g., "65%")
- ✅ Confidence badge is red

### Test 9.4.3: Verify ClarificationDialog Appears

**Steps:**
1. After all agents complete, clarification dialog should appear

**Expected Results:**
- ✅ Dialog appears with title "Additional Information Needed"
- ✅ Shows low confidence field: "Location"
- ✅ Shows current value: "Main Street"
- ✅ Shows confidence score: "65%"
- ✅ Shows clarification question: "Which Main Street are you referring to?"

### Test 9.4.4: Provide Clarification Details

**Steps:**
1. In the clarification dialog, enter additional details:
   - "Main Street in downtown, near City Hall, between 1st and 2nd Avenue"
2. Click "Submit Clarification"

**Expected Results:**
- ✅ Dialog closes
- ✅ Report is re-submitted with enhanced context
- ✅ ExecutionStatusPanel appears again

### Test 9.4.5: Submit Clarification

**Steps:**
1. Wait for re-processing to complete
2. Observe new confidence scores

**Expected Results:**
- ✅ Report is re-processed with additional context
- ✅ Agents execute again

### Test 9.4.6: Verify Report Re-Processed

**Steps:**
1. Check execution status panel
2. Verify all agents complete

**Expected Results:**
- ✅ All agents show "Complete" status
- ✅ New confidence scores are calculated

### Test 9.4.7: Verify Confidence Improves

**Steps:**
1. Check Geo Agent confidence score
2. Compare with previous score

**Expected Results:**
- ✅ Geo Agent confidence increases (e.g., from 65% to 95%)
- ✅ Confidence badge turns green
- ✅ No further clarification dialog appears
- ✅ Success toast shows: "Report submitted successfully"

---

## Test 9.5: Geometry Rendering

### Test 9.5.1: Submit Report with Single Location (Point)

**Steps:**
1. Navigate to dashboard
2. Select a domain with Geo Agent
3. Enter report: "Broken streetlight at 123 Main St"
4. Click "Submit Report"
5. Wait for processing
6. Navigate to map view

**Expected Results:**
- ✅ Incident appears on map as a marker (Point)
- ✅ Marker has category-specific color
- ✅ Marker has appropriate icon

### Test 9.5.2: Verify Marker Appears on Map

**Steps:**
1. Locate the incident on the map
2. Verify marker rendering

**Expected Results:**
- ✅ Marker is visible at correct coordinates
- ✅ Marker color matches incident category
- ✅ Marker is clickable

### Test 9.5.3: Submit Report with "from X to Y" (LineString)

**Steps:**
1. Submit new report: "Road construction from Main St to Oak Ave along 5th Street"
2. Wait for processing
3. Navigate to map view

**Expected Results:**
- ✅ Geo Agent detects LineString geometry type
- ✅ Incident appears on map as a line

### Test 9.5.4: Verify Line Appears on Map

**Steps:**
1. Locate the incident on the map
2. Verify line rendering

**Expected Results:**
- ✅ Line is visible connecting the two locations
- ✅ Line color matches incident category
- ✅ Line width is 4px
- ✅ Line is clickable

### Test 9.5.5: Submit Report with "area" or "zone" (Polygon)

**Steps:**
1. Submit new report: "Flooding in the downtown area bounded by Main, Oak, 1st, and 5th"
2. Wait for processing
3. Navigate to map view

**Expected Results:**
- ✅ Geo Agent detects Polygon geometry type
- ✅ Incident appears on map as a filled area

### Test 9.5.6: Verify Polygon Appears on Map

**Steps:**
1. Locate the incident on the map
2. Verify polygon rendering

**Expected Results:**
- ✅ Polygon is visible covering the area
- ✅ Fill color matches incident category with 30% opacity
- ✅ Border is visible with category color
- ✅ Polygon is clickable

### Test 9.5.7: Test Click Interactions for All Types

**Steps:**
1. Click on Point marker
2. Click on LineString
3. Click on Polygon

**Expected Results:**
- ✅ Popup appears for Point with incident details
- ✅ Popup appears for LineString with incident details
- ✅ Popup appears for Polygon with incident details
- ✅ Popups show: title, description, category, timestamp
- ✅ Hover effect shows pointer cursor for all geometry types

---

## Test 9.6: Network Error Fixes

### Test 9.6.1: Refresh Page Multiple Times

**Steps:**
1. Navigate to dashboard
2. Press F5 to refresh
3. Wait for page to load
4. Repeat 5 times

**Expected Results:**
- ✅ No "NetworkError" toasts appear
- ✅ No "Failed to load domains" errors
- ✅ Page loads successfully each time
- ✅ API client initializes properly

### Test 9.6.2: Verify No "NetworkError" Toasts Appear

**Steps:**
1. Monitor toast notifications during page loads
2. Check browser console for errors

**Expected Results:**
- ✅ No network error toasts on page refresh
- ✅ No console errors related to fetch failures
- ✅ API initialization completes silently

### Test 9.6.3: Disconnect Network

**Steps:**
1. Open browser DevTools
2. Go to Network tab
3. Set throttling to "Offline"
4. Try to submit a report

**Expected Results:**
- ✅ Request fails (expected)
- ✅ Appropriate error toast appears

### Test 9.6.4: Attempt API Call

**Steps:**
1. While offline, click "Submit Report"
2. Observe error handling

**Expected Results:**
- ✅ Error toast appears: "Network error"
- ✅ Toast message is user-friendly
- ✅ No crash or unhandled errors

### Test 9.6.5: Verify Appropriate Error Toast

**Steps:**
1. Read the error toast message
2. Verify it's helpful to the user

**Expected Results:**
- ✅ Toast shows: "Network error - Please check your connection"
- ✅ Toast is dismissible
- ✅ Toast has error styling (red)

### Test 9.6.6: Reconnect Network

**Steps:**
1. Set throttling back to "Online"
2. Try to submit a report again

**Expected Results:**
- ✅ Network is restored
- ✅ API calls work again

### Test 9.6.7: Verify Retry Succeeds

**Steps:**
1. Submit a report
2. Verify it succeeds

**Expected Results:**
- ✅ Report submission succeeds
- ✅ Success toast appears
- ✅ No retry attempts needed (network is stable)

---

## Test 9.7: Fix Any Discovered Bugs

### Bug Tracking Template

For each bug discovered during testing:

**Bug ID:** [Sequential number]
**Test Section:** [Which test revealed the bug]
**Severity:** [Critical / High / Medium / Low]
**Description:** [What went wrong]
**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:** [What should happen]
**Actual Behavior:** [What actually happened]
**Screenshots/Logs:** [If applicable]
**Fix Applied:** [Description of fix]
**Verification:** [How to verify the fix]

---

## Summary Checklist

After completing all tests, verify:

- [ ] All agent CRUD operations work correctly
- [ ] Agent filtering works (All, Built-in, Custom)
- [ ] Built-in agents cannot be edited or deleted
- [ ] Domain creation wizard works with 2 stages
- [ ] Dependency graph visualizes execution flow
- [ ] Real-time status updates work via WebSocket
- [ ] Confidence scores display correctly
- [ ] Clarification dialog appears for low confidence
- [ ] Clarification improves confidence scores
- [ ] Point geometry renders as markers
- [ ] LineString geometry renders as lines
- [ ] Polygon geometry renders as filled areas
- [ ] All geometry types are clickable with popups
- [ ] No network errors on page refresh
- [ ] Offline mode shows appropriate errors
- [ ] Retry logic works for transient failures
- [ ] All discovered bugs are documented and fixed

---

## Notes

- Test with different user accounts to verify multi-tenancy
- Test with different browsers (Chrome, Firefox, Safari)
- Test on different screen sizes (desktop, tablet, mobile)
- Monitor browser console for any warnings or errors
- Check network tab for failed requests
- Verify all API responses have correct structure
- Test edge cases (empty inputs, special characters, etc.)
