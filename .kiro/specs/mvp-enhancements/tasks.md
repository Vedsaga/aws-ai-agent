# Implementation Plan

## Overview

This implementation plan converts the MVP enhancements design into actionable coding tasks. All tasks focus on frontend development since the backend is fully deployed. Each task builds incrementally and can be tested independently.

## Task List

- [x] 1. Set up Shadcn UI and dark mode theme
  - Install Shadcn UI with dark mode preset
  - Configure Tailwind CSS for dark mode
  - Update root layout to apply dark theme globally
  - Test theme application across existing pages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Install and configure Shadcn UI
  - Run `npx shadcn-ui@latest init` in frontend directory
  - Select dark mode as default theme
  - Configure component installation path
  - _Requirements: 1.1_

- [x] 1.2 Install required Shadcn components
  - Install: button, input, select, table, dialog, toast, tabs, card, badge
  - Verify components are accessible in project
  - _Requirements: 1.1_

- [x] 1.3 Configure Tailwind for dark mode
  - Update `tailwind.config.ts` with dark mode class strategy
  - Add dark mode color palette to CSS variables
  - Test dark mode colors in browser
  - _Requirements: 1.2, 1.3_

- [x] 1.4 Update root layout for dark theme
  - Add `className="dark"` to html element in `app/layout.tsx`
  - Add dark background and text colors to body
  - Add Toaster component to layout
  - _Requirements: 1.3, 1.4_

- [x] 1.5 Update Mapbox to dark style
  - Change map style to `mapbox://styles/mapbox/dark-v11` in MapView component
  - Test map rendering with dark theme
  - _Requirements: 1.2_

- [x] 2. Implement error toast notification system
  - Create toast utility functions
  - Add error handling to API client
  - Add validation error display to forms
  - Test error scenarios
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2.1 Create toast utility functions
  - Create `lib/toast-utils.ts` with showToast function
  - Support variants: default, destructive, success
  - Export typed interface for toast options
  - _Requirements: 2.1_

- [x] 2.2 Add error handling to API client
  - Update `lib/api-client.ts` to show toasts on errors
  - Handle network errors, 401, 403, 400, 500 responses
  - Add response validation helpers
  - _Requirements: 2.1, 2.2_

- [x] 2.3 Add validation to forms
  - Update AgentCreationForm with inline validation
  - Update IngestionPanel with validation
  - Update QueryPanel with validation
  - Show toast on validation failures
  - _Requirements: 2.2_

- [x] 2.4 Test error scenarios
  - Test network failure (disconnect wifi)
  - Test validation errors (empty fields)
  - Test API errors (invalid data)
  - Verify toast displays correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Create domain selector with chat history
  - Create DomainSelector component
  - Implement chat history persistence
  - Add domain selector to dashboard
  - Test domain switching and chat restoration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Create DomainSelector component
  - Create `components/DomainSelector.tsx`
  - Fetch domains from `/config?type=domain_template` API
  - Display domain name and description in dropdown
  - Handle domain selection change
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3.2 Implement chat history state management
  - Create AppContext with chatHistory state
  - Add addChatMessage and clearChatHistory actions
  - Persist chat history to localStorage
  - Load chat history on mount
  - _Requirements: 7.5_

- [x] 3.3 Add domain selector to dashboard
  - Add DomainSelector to IngestionPanel
  - Add DomainSelector to QueryPanel
  - Pass selectedDomain to API calls
  - _Requirements: 3.1, 3.4_

- [x] 3.4 Implement chat restoration on domain switch
  - Load chat messages for selected domain
  - Display messages in chat panel
  - Clear messages when switching domains
  - _Requirements: 7.5_

- [x] 3.5 Test domain switching
  - Switch between Civic Complaints, Disaster Response, Agriculture
  - Verify chat history persists per domain
  - Verify API calls use correct domain_id
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Create view mode switcher and manage screen
  - Create ViewModeSwitcher component
  - Create Manage page with domain grid
  - Implement routing between modes
  - Test mode switching
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 4.1 Create ViewModeSwitcher component
  - Create `components/ViewModeSwitcher.tsx`
  - Use Tabs component with "Use Domain" and "Manage Domain" options
  - Handle mode change and navigation
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 4.2 Add view mode switcher to dashboard
  - Add ViewModeSwitcher to dashboard header
  - Navigate to `/manage` when "Manage Domain" selected
  - Navigate to `/dashboard` when "Use Domain" selected
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 4.3 Create Manage page
  - Create `app/manage/page.tsx`
  - Fetch domains from API
  - Display domains in grid layout (3 columns)
  - Show domain name, description, agent counts
  - _Requirements: 8.3, 8.4_

- [x] 4.4 Add "Created by me" badges
  - Compare domain.created_by with current user.id
  - Display Badge component with "Created by me" text
  - Style badge with secondary variant
  - _Requirements: 8.4_

- [x] 4.5 Add action buttons to domain cards
  - Add "View Data" button navigating to `/manage/{domain_id}`
  - Add "Edit" button navigating to `/config/domain/{domain_id}`
  - Style buttons with outline variant
  - _Requirements: 8.3_

- [x] 5. Implement visual design system
  - Define category colors and icons
  - Create custom map markers
  - Add severity indicators
  - Implement geometry rendering
  - Test visual consistency
  - _Requirements: 1.5, 4.4, 4.5_

- [x] 5.1 Define category colors and icons
  - Create `lib/category-config.ts` with CATEGORY_COLORS constant
  - Define colors for: pothole, street_light, sidewalk, trash, flooding, fire, default
  - Define icons (emojis) for each category
  - Export SEVERITY_COLORS constant
  - _Requirements: 1.5_

- [x] 5.2 Create custom marker function
  - Create `lib/map-utils.ts` with createCustomMarker function
  - Generate HTML element with category color and icon
  - Add severity indicator (red dot) for critical incidents
  - Return styled div element
  - _Requirements: 1.5, 4.4_

- [x] 5.3 Update MapView to use custom markers
  - Import createCustomMarker function
  - Replace default markers with custom markers
  - Pass incident data to marker creation
  - Test marker rendering
  - _Requirements: 1.5, 4.4_

- [x] 5.4 Implement LineString rendering
  - Add map.addSource for LineString geometry
  - Add map.addLayer with line type
  - Style line with category color and 3px width
  - Add click handler to show popup
  - _Requirements: 4.5_

- [x] 5.5 Implement Polygon rendering
  - Add map.addSource for Polygon geometry
  - Add map.addLayer with fill type (30% opacity)
  - Add map.addLayer with line type for border
  - Add click handler to show popup
  - _Requirements: 4.5_

- [x] 5.6 Add hover effects
  - Add mouseenter handler to change cursor to pointer
  - Add mouseleave handler to reset cursor
  - Apply to LineString and Polygon layers
  - _Requirements: 4.5_

- [x] 6. Create enhanced map popups
  - Create detailed popup component
  - Add category header with color
  - Display all agent outputs
  - Add image gallery
  - Test popup interactions
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6.1 Create detailed popup function
  - Create `lib/popup-utils.ts` with createDetailedPopup function
  - Generate popup HTML with category header
  - Style header with category color
  - Return mapboxgl.Popup instance
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 6.2 Add original report section
  - Display incident.raw_text in popup
  - Style with gray text color
  - Add "Report" heading
  - _Requirements: 4.3_

- [x] 6.3 Add structured data section
  - Loop through incident.structured_data
  - Display each agent's output in separate card
  - Show agent name as heading
  - Display key-value pairs
  - _Requirements: 4.3_

- [x] 6.4 Add image gallery
  - Check if incident.images exists and has items
  - Display images in 3-column grid
  - Make images clickable to open in new tab
  - Style with rounded corners
  - _Requirements: 4.3_

- [x] 6.5 Add action buttons
  - Add "View Full Details" button
  - Link to `/manage/{domain_id}?incident={incident_id}`
  - Style with primary color
  - _Requirements: 4.3_

- [x] 6.6 Update MapView to use detailed popups
  - Import createDetailedPopup function
  - Set popup on marker creation
  - Add popup to LineString click handler
  - Add popup to Polygon click handler
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Implement query clarification system
  - Create clarification detection logic
  - Create clarification UI component
  - Implement query refinement
  - Test with ambiguous queries
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.1 Create clarification detection
  - Create `lib/query-utils.ts` with needsClarification function
  - Define ambiguous query patterns (regex)
  - Return boolean indicating if clarification needed
  - _Requirements: 7.1, 7.2_

- [x] 7.2 Create clarification questions generator
  - Create getClarificationQuestions function
  - Check for missing category, location, time_range
  - Return array of ClarificationQuestion objects
  - _Requirements: 7.2_

- [x] 7.3 Create QueryClarificationPanel component
  - Create `components/QueryClarificationPanel.tsx`
  - Display original query
  - Show clarification questions with Select inputs
  - Add "Submit Query" and "Skip" buttons
  - _Requirements: 7.2, 7.3_

- [x] 7.4 Implement query refinement
  - Create buildRefinedQuery function
  - Append category, location, time_range to query
  - Return refined query string
  - _Requirements: 7.3_

- [x] 7.5 Integrate clarification into QueryPanel
  - Check if query needs clarification on submit
  - Show QueryClarificationPanel if needed
  - Submit refined query to API
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Create data table view
  - Create DataTableView component
  - Implement filtering and sorting
  - Create IncidentDetailModal
  - Integrate with Retrieval API
  - Test with real data
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8.1 Create DataTableView component
  - Create `components/DataTableView.tsx`
  - Fetch incidents from `/data?type=retrieval` API
  - Display incidents in Shadcn Table component
  - Show columns: ID, Time, Location, Category, + agent outputs
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 8.2 Implement filtering
  - Add DateRangePicker for date filtering
  - Add Input for location search
  - Add Select for category filtering
  - Update API call with filter parameters
  - _Requirements: 6.4_

- [x] 8.3 Implement sorting
  - Add click handlers to table headers
  - Toggle sort direction on click
  - Update API call with sort parameters
  - Show sort indicator (arrow icon)
  - _Requirements: 6.4_

- [x] 8.4 Implement pagination
  - Add Pagination component below table
  - Handle page change events
  - Update API call with page parameter
  - Display current page and total pages
  - _Requirements: 6.2_

- [x] 8.5 Create IncidentDetailModal
  - Create `components/IncidentDetailModal.tsx`
  - Display full incident details in Dialog
  - Show raw text, structured data, images
  - Add mini map showing incident location
  - _Requirements: 6.5_

- [x] 8.6 Add row click handler
  - Handle table row click event
  - Open IncidentDetailModal with incident data
  - Close modal on backdrop click or close button
  - _Requirements: 6.5_

- [x] 8.7 Create domain-specific data table page
  - Create `app/manage/[domainId]/page.tsx`
  - Add DataTableView component
  - Filter incidents by domain_id
  - Add back button to manage page
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Polish and testing
  - Fix UI bugs
  - Test end-to-end flows
  - Validate API integrations
  - Optimize performance
  - Prepare demo script
  - _Requirements: All_

- [x] 9.1 Test civic complaint submission flow
  - Select Civic Complaints domain
  - Submit report with text and image
  - Verify real-time status updates
  - Verify map marker appears
  - Click marker and verify popup shows details
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 9.2 Test query flow
  - Ask "What are the trends in pothole complaints?"
  - Verify clarification questions appear
  - Submit refined query
  - Verify bullet points and summary display
  - Verify map updates with query results
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 9.3 Test domain switching
  - Switch from Civic Complaints to Disaster Response
  - Verify chat history clears
  - Submit report in Disaster Response
  - Switch back to Civic Complaints
  - Verify previous chat history restored
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9.4 Test manage mode
  - Click "Manage Domain" tab
  - Verify navigation to `/manage`
  - Verify domain grid displays
  - Verify "Created by me" badges show correctly
  - Click "View Data" on a domain
  - Verify data table displays incidents
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9.5 Test error handling
  - Disconnect network and submit report
  - Verify error toast displays
  - Submit form with empty fields
  - Verify validation error toast
  - Reconnect network and retry
  - Verify success toast
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 9.6 Test visual design
  - Verify dark mode applied consistently
  - Verify category colors and icons display
  - Verify severity indicators show for critical incidents
  - Verify LineString and Polygon render correctly
  - Verify hover effects work
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 9.7 Optimize performance
  - Check map rendering performance with 100+ markers
  - Optimize popup creation (memoization)
  - Optimize table rendering (virtualization if needed)
  - Check bundle size and lazy load components
  - _Requirements: All_

- [x] 9.8 Prepare demo script
  - Write step-by-step demo flow
  - Prepare sample data for demo
  - Test demo flow end-to-end
  - Create backup plan for network issues
  - _Requirements: All_


