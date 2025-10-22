# Error Toast Notification System - Testing Guide

This document provides a comprehensive guide for testing the error toast notification system implemented in the Multi-Agent Orchestration System frontend.

## Overview

The error toast notification system provides user-visible error messages for:
- API errors (network, server, authentication)
- Validation errors (form inputs)
- Agent execution failures (real-time)

## Test Scenarios

### 1. Network Failure Tests

#### Test 1.1: Submit Report with Network Disconnected
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Enter report text
4. Disconnect network (turn off WiFi or unplug ethernet)
5. Click "Submit Report"

**Expected Result:**
- Toast appears with title "Network Error"
- Description: "Please check your connection and try again"
- Variant: destructive (red)
- Duration: 5 seconds

#### Test 1.2: Submit Query with Network Disconnected
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Enter a question
4. Disconnect network
5. Click "Ask Question"

**Expected Result:**
- Toast appears with title "Network Error"
- Description: "Please check your connection and try again"
- Variant: destructive (red)

### 2. Validation Error Tests

#### Test 2.1: Submit Report with Empty Text
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Leave report text empty
4. Click "Submit Report"

**Expected Result:**
- Toast appears with title "Validation Error"
- Description: "Report text is required"
- Variant: destructive (red)
- Form does not submit

#### Test 2.2: Submit Report without Domain Selection
**Steps:**
1. Navigate to the dashboard
2. Do not select a domain (if possible)
3. Enter report text
4. Click "Submit Report"

**Expected Result:**
- Toast appears with title "Validation Error"
- Description: "Please select a domain"
- Variant: destructive (red)

#### Test 2.3: Submit Query with Empty Question
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Leave question field empty
4. Click "Ask Question"

**Expected Result:**
- Toast appears with title "Validation Error"
- Description: "Question is required"
- Variant: destructive (red)

#### Test 2.4: Upload Image Exceeding Size Limit
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Try to upload an image larger than 5MB

**Expected Result:**
- Toast appears with title "Validation Error"
- Description: "Image [filename] exceeds 5MB limit"
- Variant: destructive (red)
- Image is not added to the form

#### Test 2.5: Create Agent with Missing Required Fields
**Steps:**
1. Navigate to the agent creation form
2. Leave agent name empty
3. Click "Create Agent"

**Expected Result:**
- Toast appears with title "Validation Error"
- Description: "Agent name is required, System prompt is required, At least one tool must be selected, At least one output field is required"
- Variant: destructive (red)

#### Test 2.6: Create Agent with Duplicate Field Names
**Steps:**
1. Navigate to the agent creation form
2. Fill in required fields
3. Add multiple output fields with the same name
4. Click "Create Agent"

**Expected Result:**
- Toast appears with title "Validation Error"
- Description includes "Duplicate field names: [field_name]"
- Variant: destructive (red)

### 3. API Error Tests

#### Test 3.1: 401 Unauthorized Error
**Steps:**
1. Log in to the application
2. Wait for session to expire (or manually clear auth tokens)
3. Try to submit a report or query

**Expected Result:**
- Toast appears with title "Session expired"
- Description: "Please log in again"
- Variant: destructive (red)
- User is redirected to login page (if implemented)

#### Test 3.2: 403 Forbidden Error
**Steps:**
1. Attempt an action the user doesn't have permission for
2. (This may require backend configuration)

**Expected Result:**
- Toast appears with title "Access denied"
- Description: "You do not have permission to perform this action"
- Variant: destructive (red)

#### Test 3.3: 400 Bad Request Error
**Steps:**
1. Submit invalid data to the API
2. (This may require modifying request data)

**Expected Result:**
- Toast appears with title "Invalid request"
- Description: [Error message from server]
- Variant: destructive (red)

#### Test 3.4: 500 Server Error
**Steps:**
1. Trigger a server error (may require backend configuration)
2. Or wait for a natural server error

**Expected Result:**
- Toast appears with title "Server error"
- Description: "Something went wrong on our end. Please try again later"
- Variant: destructive (red)

### 4. Agent Execution Error Tests

#### Test 4.1: Agent Execution Failure
**Steps:**
1. Submit a report that causes an agent to fail
2. Monitor real-time status updates

**Expected Result:**
- Toast appears with title "[Agent Name] failed"
- Description: [Error message from agent]
- Variant: destructive (red)
- Duration: 10 seconds (longer for errors)

#### Test 4.2: WebSocket Connection Error
**Steps:**
1. Submit a report
2. Disconnect network during processing
3. Or close WebSocket connection

**Expected Result:**
- Toast appears with title "Connection error"
- Description: "Lost connection to status updates"
- Variant: destructive (red)

### 5. Success Toast Tests

#### Test 5.1: Successful Report Submission
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Enter valid report text
4. Click "Submit Report"

**Expected Result:**
- Toast appears with title "Report submitted"
- Description: "Your report is being processed"
- Variant: success (green)
- Duration: 3 seconds

#### Test 5.2: Successful Query Submission
**Steps:**
1. Navigate to the dashboard
2. Select a domain
3. Enter a valid question
4. Click "Ask Question"

**Expected Result:**
- Toast appears with title "Query submitted"
- Description: "Your question is being analyzed"
- Variant: success (green)

#### Test 5.3: Successful Report Processing
**Steps:**
1. Submit a report
2. Wait for processing to complete

**Expected Result:**
- Toast appears with title "Processing complete"
- Description: "Your report has been processed successfully"
- Variant: success (green)

#### Test 5.4: Successful Query Analysis
**Steps:**
1. Submit a query
2. Wait for analysis to complete

**Expected Result:**
- Toast appears with title "Analysis complete"
- Description: "Your query has been analyzed"
- Variant: success (green)

#### Test 5.5: Successful Agent Creation
**Steps:**
1. Navigate to agent creation form
2. Fill in all required fields correctly
3. Click "Create Agent"

**Expected Result:**
- Toast appears with title "Agent created successfully"
- Description: "Agent ID: [config_id]"
- Variant: success (green)

## Manual Testing Checklist

- [ ] Test 1.1: Network failure on report submission
- [ ] Test 1.2: Network failure on query submission
- [ ] Test 2.1: Empty report text validation
- [ ] Test 2.2: Missing domain selection validation
- [ ] Test 2.3: Empty question validation
- [ ] Test 2.4: Image size limit validation
- [ ] Test 2.5: Agent creation missing fields validation
- [ ] Test 2.6: Agent creation duplicate fields validation
- [ ] Test 3.1: 401 Unauthorized error
- [ ] Test 3.2: 403 Forbidden error
- [ ] Test 3.3: 400 Bad Request error
- [ ] Test 3.4: 500 Server error
- [ ] Test 4.1: Agent execution failure
- [ ] Test 4.2: WebSocket connection error
- [ ] Test 5.1: Successful report submission
- [ ] Test 5.2: Successful query submission
- [ ] Test 5.3: Successful report processing
- [ ] Test 5.4: Successful query analysis
- [ ] Test 5.5: Successful agent creation

## Automated Testing

The following automated tests are available:

### Unit Tests
```bash
cd infrastructure/frontend
npm test -- lib/__tests__/toast-utils.test.ts
npm test -- lib/__tests__/api-client.test.ts
```

### Integration Tests
Integration tests should verify:
1. Toast component renders correctly
2. Toast appears when API errors occur
3. Toast appears when validation fails
4. Toast dismisses after specified duration

## Visual Verification

When testing, verify the following visual aspects:

### Toast Appearance
- **Position**: Top-right corner of the screen
- **Width**: Maximum 420px
- **Animation**: Slides in from top/bottom
- **Shadow**: Visible drop shadow

### Destructive Variant (Error)
- **Background**: Red/destructive color
- **Text**: White or light color
- **Border**: Red border
- **Icon**: X or error icon (if implemented)

### Success Variant
- **Background**: Green background (via className)
- **Text**: Dark green text
- **Border**: Green border
- **Icon**: Checkmark icon (if implemented)

### Default Variant
- **Background**: Dark background (dark mode)
- **Text**: Light text
- **Border**: Subtle border

## Browser Compatibility

Test in the following browsers:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Mobile Testing

Test on mobile devices:
- [ ] iOS Safari
- [ ] Android Chrome
- [ ] Responsive design (various screen sizes)

## Accessibility Testing

Verify:
- [ ] Toast is announced by screen readers
- [ ] Toast can be dismissed with keyboard
- [ ] Color contrast meets WCAG standards
- [ ] Focus management is appropriate

## Performance Testing

Verify:
- [ ] Multiple toasts don't cause performance issues
- [ ] Toast animations are smooth
- [ ] Toast doesn't block user interaction
- [ ] Toast memory is properly cleaned up

## Notes

- Toast notifications should not block user interaction
- Multiple toasts should stack or queue appropriately
- Toast should auto-dismiss after specified duration
- User should be able to manually dismiss toast
- Toast should persist during page navigation (if applicable)

## Known Issues

Document any known issues here:
- None currently

## Future Enhancements

Potential improvements:
- Add toast action buttons (e.g., "Retry", "Dismiss")
- Add toast icons for different variants
- Add toast sound notifications (optional)
- Add toast persistence across page reloads
- Add toast history/log viewer
