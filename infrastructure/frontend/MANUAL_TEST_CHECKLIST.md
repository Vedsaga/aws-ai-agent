# Manual Test Checklist - API Integration and Fixes

## Test Session Information
- **Date:** _______________
- **Tester:** _______________
- **Environment:** http://localhost:3000
- **Browser:** _______________

## Pre-Test Setup
- [ ] Backend services are running
- [ ] Frontend dev server is running (`npm run dev`)
- [ ] User is logged in with valid credentials
- [ ] Browser developer tools are open (F12)
- [ ] Network tab is monitoring requests

---

## 9.1 Agent CRUD Operations

### Test 1.1: Create Custom Ingestion Agent
- [ ] Navigate to `/agents`
- [ ] Click "Create Agent" button
- [ ] Dialog opens successfully
- [ ] Select "Data Ingest Agent" tab
- [ ] Fill in form:
  - Agent Name: "Test Ingest Agent"
  - Tools: bedrock, location_proxy
  - System Prompt: "Extract location and priority from civic complaints"
  - Output Schema:
    - location: string
    - priority: number
    - confidence: number
- [ ] Click "Create Agent"
- [ ] Success toast appears
- [ ] Agent appears in list with "Custom" badge
- [ ] Agent count increases

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 1.2: Create Custom Query Agent with Parent
- [ ] Click "Create Agent" button
- [ ] Select "Data Query Agent" tab
- [ ] Fill in form:
  - Agent Name: "Test Query Agent"
  - Parent Agent: "When Agent"
  - Tools: bedrock, retrieval_api
  - System Prompt: "Analyze temporal patterns"
  - Output Schema:
    - pattern: string
    - insight: string
- [ ] Click "Create Agent"
- [ ] Success toast appears
- [ ] Agent appears with parent indicator

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 1.3: List and Filter Agents
- [ ] Click "All" tab - shows all agents
- [ ] Click "Built-in" tab - shows only built-in (17 agents)
- [ ] Click "Custom" tab - shows only custom (2 agents)
- [ ] Counts are correct in each tab
- [ ] Built-in agents have "Built-in" badge
- [ ] Custom agents have "Created by me" badge

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 1.4: Update Agent Configuration
- [ ] Find "Test Ingest Agent"
- [ ] Click "Edit" button
- [ ] Modify system prompt
- [ ] Add new output field: category: string
- [ ] Click "Update Agent"
- [ ] Success toast appears
- [ ] Changes reflected in agent card

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 1.5: Delete Custom Agent
- [ ] Find "Test Query Agent"
- [ ] Click "Delete" button
- [ ] Confirmation dialog appears
- [ ] Click "Delete" in dialog
- [ ] Success toast appears
- [ ] Agent removed from list
- [ ] Custom count decreases

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 1.6: Built-in Agent Protection
- [ ] Switch to "Built-in" tab
- [ ] Select any built-in agent
- [ ] Verify NO "Edit" button visible
- [ ] Verify NO "Delete" button visible
- [ ] Only read-only actions available

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.2 Domain Creation Flow

### Test 2.1: Open Domain Creation Wizard
- [ ] Navigate to `/manage`
- [ ] Click "Create Domain" button
- [ ] Dialog opens with "Stage 1 of 2"
- [ ] Domain name field visible
- [ ] Description field visible
- [ ] Ingestion agents list visible
- [ ] "Next" button is disabled

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.2: Stage 1 - Select Ingestion Agents
- [ ] Enter domain name: "Test Traffic Domain"
- [ ] Enter description: "Testing domain creation"
- [ ] Select "Geo Agent" checkbox
- [ ] Select "Temporal Agent" checkbox
- [ ] Count badge shows "2 selected"
- [ ] Dependency graph appears
- [ ] "Next" button becomes enabled

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.3: Verify Parallel Execution Graph
- [ ] Dependency graph shows "Ingestion Layer"
- [ ] Both agents shown horizontally (parallel)
- [ ] Label says "Parallel: [Geo Agent] [Temporal Agent]"
- [ ] No arrows between agents
- [ ] Graph updates when selecting/deselecting

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.4: Proceed to Stage 2
- [ ] Click "Next: Select Query Agents"
- [ ] Stage indicator changes to "Stage 2 of 2"
- [ ] Query agents list appears
- [ ] All 11 query agents visible
- [ ] "Create" button is disabled
- [ ] "Back" button is visible

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.5: Stage 2 - Select Query Agents
- [ ] Select "When Agent" checkbox
- [ ] Select "Where Agent" checkbox
- [ ] Select "Why Agent" checkbox
- [ ] Count badge shows "3 selected"
- [ ] Dependency graph updates
- [ ] "Create" button becomes enabled

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.6: Verify Complete Dependency Graph
- [ ] Graph shows "Ingestion Layer" section
- [ ] Ingestion: Geo Agent, Temporal Agent (parallel)
- [ ] Graph shows "Query Layer" section
- [ ] Query: When, Where, Why (parallel)
- [ ] Clear visual separation between layers

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.7: Create Domain
- [ ] Click "Create Domain" button
- [ ] Success toast appears
- [ ] Dialog closes
- [ ] Domain appears in list
- [ ] Domain has "Created by me" badge
- [ ] Agent count shows 5

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 2.8: Verify Domain in List
- [ ] "Test Traffic Domain" visible
- [ ] Description is correct
- [ ] "Created by me" badge present
- [ ] Agent count: 5
- [ ] "Ask Question" button visible
- [ ] "Submit Report" button visible

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.3 Real-Time Status Updates

### Test 3.1: Submit Report
- [ ] Navigate to `/dashboard`
- [ ] Select "Test Traffic Domain" from dropdown
- [ ] Enter: "Traffic accident at Main St and 5th Ave at 3pm today"
- [ ] Click "Submit Report"
- [ ] Submit button shows loading
- [ ] ExecutionStatusPanel appears
- [ ] Job ID is displayed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 3.2: Verify Status Panel
- [ ] Panel shows job ID
- [ ] All 5 agents listed
- [ ] Initial status: "waiting" for all
- [ ] Status icons are gray circles
- [ ] Panel is styled correctly

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 3.3: Verify "Invoking" Status
- [ ] Agents transition to "invoking"
- [ ] Status icon changes to spinning loader (blue)
- [ ] Status message: "Invoking agent..."
- [ ] Updates happen in real-time
- [ ] No page refresh needed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 3.4: Verify "Complete" Status
- [ ] Agents transition to "complete"
- [ ] Status icon changes to green checkmark
- [ ] Status message: "Complete"
- [ ] Confidence badge appears
- [ ] Badge shows percentage (e.g., "95%")

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 3.5: Verify Confidence Badges
- [ ] Geo Agent shows confidence score
- [ ] Temporal Agent shows confidence score
- [ ] Query agents show confidence scores
- [ ] Badge color coding:
  - Green for >= 90%
  - Yellow for 70-89%
  - Red for < 70%
- [ ] Percentages are accurate

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.4 Confidence-Based Clarification

### Test 4.1: Submit Ambiguous Report
- [ ] Select domain with Geo Agent
- [ ] Enter: "Pothole on Main Street"
- [ ] Click "Submit Report"
- [ ] Wait for processing
- [ ] Execution completes

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.2: Verify Low Confidence
- [ ] Geo Agent confidence < 90%
- [ ] Badge shows red color
- [ ] Confidence score visible (e.g., 65%)
- [ ] System detects low confidence

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.3: Verify Clarification Dialog
- [ ] Dialog appears automatically
- [ ] Title: "Additional Information Needed"
- [ ] Low confidence fields listed
- [ ] Current value shown
- [ ] Confidence score shown
- [ ] Clarification question displayed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.4: Provide Clarification
- [ ] Question is specific and helpful
- [ ] Example: "Which Main Street? Please provide city, cross streets, or nearby landmarks."
- [ ] Textarea is functional
- [ ] Enter: "Main Street in downtown, near City Hall, between 1st and 2nd Avenue"
- [ ] Input is captured

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.5: Submit Clarification
- [ ] Click "Submit Clarification"
- [ ] Dialog closes
- [ ] New job starts
- [ ] ExecutionStatusPanel appears again
- [ ] Enhanced text is sent to agents

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.6: Verify Re-Processing
- [ ] All agents execute again
- [ ] Status updates in real-time
- [ ] Processing completes
- [ ] Results are updated

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 4.7: Verify Confidence Improves
- [ ] Geo Agent confidence now >= 90%
- [ ] Badge color changes to green
- [ ] New confidence score (e.g., 95%)
- [ ] No further clarification needed
- [ ] Results displayed on map

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.5 Geometry Rendering

### Test 5.1: Point Geometry
- [ ] Submit: "Fire hydrant broken at 123 Main Street"
- [ ] Wait for completion
- [ ] Navigate to map view
- [ ] Geo Agent detects geometry_type: "Point"
- [ ] Marker appears on map
- [ ] Marker has category color
- [ ] Marker has custom icon

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.2: Verify Point Marker
- [ ] Marker is visible
- [ ] Marker is correctly positioned
- [ ] Click marker
- [ ] Popup appears with incident details
- [ ] Popup shows all structured data
- [ ] Popup can be closed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.3: LineString Geometry
- [ ] Submit: "Road construction from Main Street to Oak Avenue along Highway 101"
- [ ] Wait for completion
- [ ] Navigate to map view
- [ ] Geo Agent detects geometry_type: "LineString"
- [ ] Multiple coordinates extracted

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.4: Verify LineString Rendering
- [ ] Line is visible on map
- [ ] Line connects locations
- [ ] Line has category color
- [ ] Line width is 4px
- [ ] Line opacity is 80%
- [ ] Hover changes cursor to pointer
- [ ] Click opens popup
- [ ] Popup shows incident details

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.5: Polygon Geometry
- [ ] Submit: "Power outage affecting the downtown area bounded by 1st St, 5th St, Main Ave, and Oak Ave"
- [ ] Wait for completion
- [ ] Navigate to map view
- [ ] Geo Agent detects geometry_type: "Polygon"
- [ ] Boundary coordinates extracted

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.6: Verify Polygon Rendering
- [ ] Polygon fill is visible
- [ ] Fill opacity is 30%
- [ ] Polygon border is visible
- [ ] Border has category color
- [ ] Border width is 2px
- [ ] Hover changes cursor to pointer
- [ ] Click opens popup
- [ ] Popup shows incident details

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 5.7: Test All Geometry Interactions
- [ ] Click Point marker - popup appears
- [ ] Click LineString - popup appears at click location
- [ ] Click Polygon - popup appears at click location
- [ ] All popups show correct information
- [ ] All popups are positioned correctly
- [ ] All popups can be closed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.6 Network Error Fixes

### Test 6.1: Multiple Page Refreshes
- [ ] Navigate to `/dashboard`
- [ ] Wait for complete load
- [ ] Press F5 to refresh
- [ ] Wait for load
- [ ] Repeat 5 times
- [ ] NO "NetworkError" toasts appear
- [ ] NO "Failed to load domains" errors
- [ ] Page loads successfully each time

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.2: Verify No Network Errors
- [ ] Open browser console
- [ ] Monitor for errors
- [ ] Refresh page
- [ ] NO "NetworkError when attempting to fetch resource"
- [ ] NO initialization timeout errors
- [ ] Auth session loads correctly
- [ ] API requests succeed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.3: Simulate Network Disconnect
- [ ] Open DevTools Network tab
- [ ] Set throttling to "Offline"
- [ ] Try to submit a report
- [ ] Appropriate error toast appears
- [ ] Error message is user-friendly
- [ ] NO crash or undefined errors
- [ ] UI remains functional

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.4: API Call While Offline
- [ ] While offline, click "Submit Report"
- [ ] Error toast appears
- [ ] Message: "Network error - Please check your connection"
- [ ] Submit button returns to normal
- [ ] Form data is preserved
- [ ] Can retry after reconnecting

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.5: Verify Error Toast
- [ ] Toast shows network icon
- [ ] Message is clear
- [ ] Description is helpful
- [ ] Toast auto-dismisses after 5 seconds
- [ ] Toast can be manually dismissed

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.6: Reconnect Network
- [ ] Set throttling back to "Online"
- [ ] Click "Submit Report" again
- [ ] Request succeeds
- [ ] NO errors appear
- [ ] Normal flow continues

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

### Test 6.7: Verify Retry Logic
- [ ] Monitor Network tab
- [ ] Simulate 5xx error (if possible)
- [ ] Retry logic activates
- [ ] Exponential backoff applied (1s, 2s, 4s)
- [ ] Maximum 3 retries attempted
- [ ] Success after retry shows no error

**Result:** ✅ PASS / ❌ FAIL
**Notes:** _______________

---

## 9.7 Bug Documentation

### Bugs Found During Testing

#### Bug #1
- **Severity:** Critical / High / Medium / Low
- **Component:** _______________
- **Description:** _______________
- **Steps to Reproduce:**
  1. _______________
  2. _______________
  3. _______________
- **Expected:** _______________
- **Actual:** _______________
- **Screenshot/Log:** _______________

#### Bug #2
- **Severity:** Critical / High / Medium / Low
- **Component:** _______________
- **Description:** _______________
- **Steps to Reproduce:**
  1. _______________
  2. _______________
  3. _______________
- **Expected:** _______________
- **Actual:** _______________
- **Screenshot/Log:** _______________

#### Bug #3
- **Severity:** Critical / High / Medium / Low
- **Component:** _______________
- **Description:** _______________
- **Steps to Reproduce:**
  1. _______________
  2. _______________
  3. _______________
- **Expected:** _______________
- **Actual:** _______________
- **Screenshot/Log:** _______________

---

## Test Summary

### Overall Results
- **Total Tests:** 40
- **Passed:** _____ / 40
- **Failed:** _____ / 40
- **Pass Rate:** _____%

### Critical Issues
1. _______________
2. _______________
3. _______________

### High Priority Issues
1. _______________
2. _______________
3. _______________

### Medium Priority Issues
1. _______________
2. _______________
3. _______________

### Low Priority Issues
1. _______________
2. _______________
3. _______________

### Recommendations
1. _______________
2. _______________
3. _______________

### Sign-off
- **Tester:** _______________
- **Date:** _______________
- **Status:** ✅ APPROVED / ❌ NEEDS WORK
