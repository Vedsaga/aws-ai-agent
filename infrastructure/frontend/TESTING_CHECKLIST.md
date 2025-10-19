# MVP Enhancements Testing Checklist

## Overview
This document provides a comprehensive testing checklist for all MVP enhancements.
Test the application at: http://localhost:3000

## Pre-Testing Setup
- [ ] Frontend server running (`npm run dev`)
- [ ] Backend APIs accessible
- [ ] User logged in
- [ ] Browser console open for debugging

## Task 9.1: Civic Complaint Submission Flow

### Test Steps:
1. **Navigate to Dashboard**
   - [ ] Open http://localhost:3000/dashboard
   - [ ] Verify dark mode is applied
   - [ ] Verify map loads with dark-v11 style

2. **Select Domain**
   - [ ] Click domain selector dropdown
   - [ ] Verify "Civic Complaints" domain is available
   - [ ] Select "Civic Complaints"
   - [ ] Verify selection persists

3. **Submit Report**
   - [ ] Click "Submit Report" tab
   - [ ] Enter text: "Large pothole on Main Street near 5th Avenue"
   - [ ] (Optional) Upload an image
   - [ ] Click Submit button
   - [ ] Verify no validation errors

4. **Verify Real-Time Status**
   - [ ] Status panel shows "Processing..."
   - [ ] Agent names appear as they execute
   - [ ] Status updates show: loading → invoking → complete
   - [ ] No error messages appear

5. **Verify Map Marker**
   - [ ] New marker appears on map within 5 seconds
   - [ ] Marker has correct category icon (🕳️ for pothole)
   - [ ] Marker has correct category color (red)

6. **Verify Popup Details**
   - [ ] Click on the new marker
   - [ ] Popup opens with detailed information
   - [ ] Category header shows with correct color
   - [ ] Original report text is displayed
   - [ ] Extracted structured data is shown
   - [ ] Images are displayed (if uploaded)
   - [ ] "View Full Details" button is present

### Expected Results:
- ✅ Report submitted successfully
- ✅ Real-time status updates displayed
- ✅ Marker appears on map with correct styling
- ✅ Popup shows complete incident details

### Common Issues:
- ❌ Network error: Check API_URL in .env.local
- ❌ No marker appears: Check console for coordinate extraction errors
- ❌ Status not updating: Check AppSync WebSocket connection

---

## Task 9.2: Query Flow

### Test Steps:
1. **Switch to Query Tab**
   - [ ] Click "Ask Question" tab
   - [ ] Verify query input field is visible

2. **Submit Ambiguous Query**
   - [ ] Enter: "What are the trends in pothole complaints?"
   - [ ] Click Submit
   - [ ] Verify clarification panel appears (if implemented)

3. **Answer Clarification Questions**
   - [ ] Select time range: "This month"
   - [ ] Select location: "All"
   - [ ] Click "Submit Query"

4. **Verify Query Processing**
   - [ ] Status panel shows query agents executing
   - [ ] Agent names appear: trend_analyzer, pattern_detector, etc.
   - [ ] All agents complete successfully

5. **Verify Results Display**
   - [ ] Bullet points appear in chat (one per agent)
   - [ ] Summary text is displayed
   - [ ] Results are formatted clearly

6. **Verify Map Updates**
   - [ ] Map markers update to show query results
   - [ ] Relevant incidents are highlighted
   - [ ] Map zooms to show relevant area

### Expected Results:
- ✅ Query submitted successfully
- ✅ Clarification questions appear for ambiguous queries
- ✅ Query results displayed as bullet points + summary
- ✅ Map updates to show relevant incidents

### Common Issues:
- ❌ Clarification not showing: Check query-utils.ts logic
- ❌ No results: Check query API response format
- ❌ Map not updating: Check visualization update handler

---

## Task 9.3: Domain Switching

### Test Steps:
1. **Initial State**
   - [ ] On dashboard with "Civic Complaints" selected
   - [ ] Submit a report or query to create chat history
   - [ ] Verify chat messages appear

2. **Switch to Different Domain**
   - [ ] Open domain selector
   - [ ] Select "Disaster Response"
   - [ ] Verify domain changes

3. **Verify Chat Clears**
   - [ ] Chat history panel is empty
   - [ ] No previous messages visible
   - [ ] Status panel is clear

4. **Submit in New Domain**
   - [ ] Submit a new report in Disaster Response
   - [ ] Verify it processes correctly
   - [ ] New chat messages appear

5. **Switch Back**
   - [ ] Select "Civic Complaints" again
   - [ ] Verify previous chat history is restored
   - [ ] All previous messages are visible

### Expected Results:
- ✅ Chat history clears when switching domains
- ✅ Chat history restores when switching back
- ✅ Each domain maintains separate chat history
- ✅ localStorage persists chat across page refreshes

### Common Issues:
- ❌ Chat not clearing: Check AppContext domain change handler
- ❌ Chat not restoring: Check localStorage persistence
- ❌ Wrong domain data: Check domain_id in API calls

---

## Task 9.4: Manage Mode

### Test Steps:
1. **Switch to Manage Mode**
   - [ ] Click "Manage Domain" tab in ViewModeSwitcher
   - [ ] Verify navigation to /manage
   - [ ] Page loads successfully

2. **Verify Domain Grid**
   - [ ] Domain cards are displayed in grid (3 columns)
   - [ ] Each card shows: name, description, agent counts
   - [ ] "Created by me" badges show for user's domains
   - [ ] Built-in domains don't have "Created by me" badge

3. **Test Domain Card Actions**
   - [ ] Click "View Data" on a domain
   - [ ] Verify navigation to /manage/[domainId]
   - [ ] Data table loads with incidents

4. **Verify Data Table**
   - [ ] Table displays incidents
   - [ ] Columns show: ID, Time, Location, Category, + agent outputs
   - [ ] Data is formatted correctly
   - [ ] Pagination controls are visible

5. **Test Filtering**
   - [ ] Use date range filter
   - [ ] Use location search
   - [ ] Use category filter
   - [ ] Verify table updates

6. **Test Sorting**
   - [ ] Click column headers
   - [ ] Verify sort direction toggles
   - [ ] Data reorders correctly

7. **Test Row Click**
   - [ ] Click a table row
   - [ ] IncidentDetailModal opens
   - [ ] Full incident details displayed
   - [ ] Images shown (if available)
   - [ ] Mini map shows location

### Expected Results:
- ✅ Manage mode accessible via ViewModeSwitcher
- ✅ Domain grid displays all domains
- ✅ "Created by me" badges show correctly
- ✅ Data table works with filtering and sorting
- ✅ Detail modal shows complete incident information

### Common Issues:
- ❌ Grid not loading: Check /config?type=domain_template API
- ❌ Badges wrong: Check user.id comparison
- ❌ Table empty: Check /data?type=retrieval API
- ❌ Filters not working: Check API query parameters

---

## Task 9.5: Error Handling

### Test Steps:
1. **Network Error Test**
   - [ ] Disconnect network/wifi
   - [ ] Try to submit a report
   - [ ] Verify error toast appears
   - [ ] Toast shows: "Network error" message
   - [ ] Toast has destructive (red) styling

2. **Validation Error Test**
   - [ ] Leave domain selector empty
   - [ ] Try to submit report
   - [ ] Verify validation error toast
   - [ ] Toast shows: "Please select a domain"

3. **Empty Field Test**
   - [ ] Select domain
   - [ ] Leave text field empty
   - [ ] Try to submit
   - [ ] Verify validation error toast
   - [ ] Toast shows: "Report text is required"

4. **Success Test**
   - [ ] Reconnect network
   - [ ] Fill all required fields
   - [ ] Submit report
   - [ ] Verify success toast (if implemented)
   - [ ] Toast shows: "Report submitted successfully"

5. **API Error Test**
   - [ ] Submit invalid data (if possible)
   - [ ] Verify appropriate error toast
   - [ ] Error message is user-friendly

### Expected Results:
- ✅ Network errors show clear toast messages
- ✅ Validation errors prevent submission
- ✅ Success messages confirm actions
- ✅ All toasts auto-dismiss after 3-5 seconds
- ✅ Toasts are styled correctly (dark mode)

### Common Issues:
- ❌ Toast not showing: Check Toaster component in layout
- ❌ Wrong message: Check toast-utils.ts
- ❌ Toast not dismissing: Check duration parameter

---

## Task 9.6: Visual Design

### Test Steps:
1. **Dark Mode Verification**
   - [ ] All pages use dark background
   - [ ] Text has high contrast (readable)
   - [ ] Map uses dark-v11 style
   - [ ] Cards and panels have dark styling
   - [ ] Buttons have appropriate dark theme colors

2. **Category Colors**
   - [ ] Pothole markers are red (🕳️)
   - [ ] Street light markers are amber (💡)
   - [ ] Sidewalk markers are purple (🚶)
   - [ ] Trash markers are green (🗑️)
   - [ ] Flooding markers are blue (🌊)
   - [ ] Fire markers are dark red (🔥)

3. **Severity Indicators**
   - [ ] Critical incidents have red dot on marker
   - [ ] Red dot positioned at top-right of marker
   - [ ] Non-critical incidents have no dot

4. **Geometry Rendering**
   - [ ] Point geometry shows as marker
   - [ ] LineString shows as colored line
   - [ ] Polygon shows as filled area with border
   - [ ] All geometries use category colors

5. **Hover Effects**
   - [ ] Cursor changes to pointer over LineString
   - [ ] Cursor changes to pointer over Polygon
   - [ ] Cursor changes to pointer over markers
   - [ ] Hover state is visually clear

### Expected Results:
- ✅ Consistent dark mode across all pages
- ✅ Category colors match specification
- ✅ Severity indicators display correctly
- ✅ All geometry types render properly
- ✅ Hover effects work smoothly

### Common Issues:
- ❌ Light mode showing: Check html className="dark"
- ❌ Wrong colors: Check category-config.ts
- ❌ Geometry not rendering: Check map-utils.ts
- ❌ No hover effect: Check MapView event handlers

---

## Task 9.7: Performance Optimization

### Test Steps:
1. **Map Performance**
   - [ ] Load page with 100+ markers
   - [ ] Verify map renders smoothly
   - [ ] Pan and zoom are responsive
   - [ ] No lag when interacting

2. **Popup Performance**
   - [ ] Click multiple markers rapidly
   - [ ] Popups open quickly (<500ms)
   - [ ] No memory leaks (check DevTools)

3. **Table Performance**
   - [ ] Load data table with 100+ rows
   - [ ] Scrolling is smooth
   - [ ] Sorting is fast (<1s)
   - [ ] Filtering is responsive

4. **Bundle Size**
   - [ ] Run: npm run build
   - [ ] Check bundle size in output
   - [ ] Verify code splitting is working
   - [ ] Large components are lazy loaded

### Expected Results:
- ✅ Map handles 100+ markers smoothly
- ✅ Popups open instantly
- ✅ Table scrolling is smooth
- ✅ Bundle size is reasonable (<1MB)

### Performance Targets:
- Map render: <2s for 100 markers
- Popup open: <500ms
- Table sort: <1s for 1000 rows
- Initial page load: <3s

### Common Issues:
- ❌ Slow map: Reduce marker complexity
- ❌ Slow popups: Implement memoization
- ❌ Slow table: Implement virtualization
- ❌ Large bundle: Lazy load components

---

## Task 9.8: Demo Script Preparation

### Demo Flow (5 minutes):

**1. Introduction (30 seconds)**
- Show login page
- Explain multi-tenant architecture
- Log in as demo user

**2. Civic Complaint Submission (90 seconds)**
- Navigate to dashboard
- Show dark mode UI
- Select "Civic Complaints" domain
- Submit report: "Large pothole on Main Street"
- Show real-time status updates
- Point out marker appearing on map
- Click marker to show detailed popup

**3. Query and Analysis (90 seconds)**
- Switch to "Ask Question" tab
- Ask: "What are the trends in pothole complaints?"
- Show clarification questions
- Submit refined query
- Show query results (bullet points + summary)
- Show map updating with query results

**4. Domain Management (60 seconds)**
- Switch to "Manage Domain" mode
- Show domain grid
- Point out "Created by me" badges
- Click "View Data" on a domain
- Show data table with filtering
- Click row to show detail modal

**5. Error Handling Demo (30 seconds)**
- Try to submit without domain selected
- Show validation error toast
- Fill form correctly
- Show success

**6. Wrap-up (30 seconds)**
- Highlight key features:
  - Dark mode UI
  - Real-time processing
  - Multi-domain support
  - Data visualization
  - Error handling

### Demo Data Preparation:
- [ ] Create 3-5 sample incidents in each domain
- [ ] Ensure variety of categories
- [ ] Include images in some incidents
- [ ] Create incidents with different geometries
- [ ] Test all features with demo data

### Backup Plan:
- [ ] Screenshots of key features
- [ ] Video recording of working demo
- [ ] Prepared sample data in case of API issues
- [ ] Offline mode explanation ready

---

## Final Checklist

### All Features Working:
- [ ] Dark mode applied consistently
- [ ] Domain selector functional
- [ ] Report submission works end-to-end
- [ ] Query flow works with clarification
- [ ] Real-time status updates display
- [ ] Map visualization works (all geometry types)
- [ ] Data table with filtering/sorting
- [ ] Error handling with toasts
- [ ] View mode switching
- [ ] Chat history persistence

### Documentation:
- [ ] README updated
- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Known issues documented

### Demo Ready:
- [ ] Demo script prepared
- [ ] Sample data loaded
- [ ] Backup plan ready
- [ ] Team practiced demo

---

## Bug Tracking

### Known Issues:
1. **Network Error on Page Refresh**
   - Issue: "NetworkError when attempting to fetch resource" on every page refresh
   - Status: Needs investigation
   - Priority: High

2. **No API Calls Being Made**
   - Issue: Resources not showing, no API calls in network tab
   - Status: Needs investigation
   - Priority: Critical

### To Investigate:
- [ ] Check API_URL configuration
- [ ] Verify authentication token
- [ ] Check CORS settings
- [ ] Verify API endpoints are accessible
- [ ] Check browser console for errors

---

## Testing Sign-off

**Tester Name:** _______________
**Date:** _______________
**Environment:** _______________

**Overall Status:**
- [ ] All tests passed
- [ ] Some tests failed (see notes)
- [ ] Blocked (see notes)

**Notes:**
_______________________________________________
_______________________________________________
_______________________________________________
