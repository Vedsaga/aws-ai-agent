# Domain Selector and Chat History Implementation

## Overview
Successfully implemented task 3 "Create domain selector with chat history" from the MVP enhancements spec. This feature allows users to select domains and maintains per-domain chat history with automatic restoration when switching between domains.

## Components Implemented

### 1. DomainSelector Component (`components/DomainSelector.tsx`)
- Fetches domains from `/config?type=domain_template` API
- Displays domain name and description in a dropdown using Shadcn Select component
- Auto-selects first domain if none is selected
- Handles loading and error states gracefully
- Integrated with dark mode theme

### 2. AppContext (`contexts/AppContext.tsx`)
- Global state management for:
  - `selectedDomain`: Currently selected domain ID
  - `chatHistory`: Per-domain chat message history
- Actions:
  - `setSelectedDomain`: Update selected domain
  - `addChatMessage`: Add message to domain's chat history
  - `clearChatHistory`: Clear messages for a domain
  - `getChatHistory`: Retrieve messages for a domain
- Persists to localStorage:
  - Chat history saved to `maos_chat_history`
  - Selected domain saved to `maos_selected_domain`
- Auto-loads from localStorage on mount

### 3. ChatHistory Component (`components/ChatHistory.tsx`)
- Displays chat messages for the selected domain
- Different styling for user vs agent messages:
  - User messages: Right-aligned, primary color
  - Agent messages: Left-aligned, secondary color
  - System messages: Muted color
- Shows agent name and timestamp for each message
- Auto-scrolls to bottom when new messages arrive
- Empty state when no domain selected or no messages

### 4. Updated Components

#### IngestionPanel
- Replaced native select with DomainSelector component
- Integrated with AppContext for domain selection
- Adds user reports to chat history
- Adds agent status updates to chat history
- Updated styling to use dark mode theme colors

#### QueryPanel
- Replaced native select with DomainSelector component
- Integrated with AppContext for domain selection
- Adds user questions to chat history
- Adds agent responses to chat history
- Updated styling to use dark mode theme colors

#### Dashboard Page
- Split chat interface into two sections:
  - Top 60%: Input panel (Submit Report or Ask Question)
  - Bottom 40%: Chat history display
- Maintains tab switching between ingestion and query modes

#### Root Layout
- Wrapped app with AppProvider to enable global state

## Features

### Domain Selection
- Users can select from available domains in both ingestion and query panels
- Domain selection is synchronized across both panels via AppContext
- Selected domain persists across page refreshes via localStorage

### Chat History
- Each domain maintains its own separate chat history
- Messages include:
  - User submissions (reports and questions)
  - Agent status updates
  - Agent responses
- Chat history persists in localStorage
- Automatic restoration when switching back to a domain
- Auto-scroll to latest message

### Chat Message Types
```typescript
interface ChatMessage {
  id: string;
  type: 'user' | 'system' | 'agent';
  content: string;
  timestamp: string;
  metadata?: {
    jobId?: string;
    agentName?: string;
    status?: string;
  };
}
```

## Testing Results

### Build Status
✅ TypeScript compilation successful
✅ No linting errors
✅ No type errors
✅ Production build successful

### Code Quality
- All components follow React best practices
- Proper use of hooks (useState, useEffect, useCallback, useMemo)
- TypeScript type safety enforced
- ESLint warnings resolved

## User Experience Flow

1. **Initial Load**
   - App loads selected domain from localStorage (if available)
   - Chat history for that domain is restored
   - Domain selector shows current selection

2. **Submitting a Report**
   - User selects domain (if not already selected)
   - User enters report text and uploads images
   - User message added to chat history
   - Report submitted to backend
   - Agent status updates appear in chat history in real-time

3. **Asking a Question**
   - User selects domain (same as ingestion panel)
   - User enters question
   - User message added to chat history
   - Query submitted to backend
   - Agent responses appear in chat history in real-time

4. **Switching Domains**
   - User selects different domain from dropdown
   - Chat history for previous domain is saved
   - Chat history for new domain is loaded and displayed
   - All subsequent interactions use the new domain

5. **Page Refresh**
   - Selected domain is restored from localStorage
   - Chat history for that domain is restored
   - User can continue where they left off

## API Integration

### Domain Fetching
```typescript
GET /config?type=domain_template
Response: {
  configs: Array<{
    domain_id: string;
    template_name: string;
    description: string;
    agent_configs: any[];
    playbook_configs: any[];
    created_by: string;
    created_at: string;
  }>;
  count: number;
}
```

### Report Submission
```typescript
POST /ingest
Body: {
  domain_id: string;
  text: string;
  images: string[];
}
Response: {
  job_id: string;
  status: string;
}
```

### Query Submission
```typescript
POST /query
Body: {
  domain_id: string;
  question: string;
}
Response: {
  job_id: string;
  status: string;
}
```

## Storage Schema

### localStorage Keys
- `maos_chat_history`: JSON object mapping domain IDs to message arrays
- `maos_selected_domain`: Currently selected domain ID

### Example Storage
```json
{
  "maos_selected_domain": "civic-complaints-001",
  "maos_chat_history": {
    "civic-complaints-001": [
      {
        "id": "1234567890-0.123",
        "type": "user",
        "content": "There's a pothole on Main St",
        "timestamp": "2025-10-19T12:34:56.789Z"
      },
      {
        "id": "1234567891-0.456",
        "type": "agent",
        "content": "EntityAgent: Extracted category: pothole",
        "timestamp": "2025-10-19T12:34:57.123Z",
        "metadata": {
          "jobId": "job-123",
          "agentName": "EntityAgent",
          "status": "complete"
        }
      }
    ],
    "disaster-response-001": [
      // Messages for disaster response domain
    ]
  }
}
```

## Next Steps

The domain selector and chat history system is now fully functional. Users can:
- ✅ Select domains from a dropdown
- ✅ Submit reports and queries to the selected domain
- ✅ View chat history for each domain
- ✅ Switch between domains with automatic chat restoration
- ✅ Persist selections and history across page refreshes

This implementation satisfies all requirements for task 3 and provides a solid foundation for the remaining MVP enhancements.
