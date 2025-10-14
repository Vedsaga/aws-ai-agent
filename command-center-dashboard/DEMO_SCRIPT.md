# Demo Script for Hackathon Presentation

## Setup (Before Demo)

1. Start the development server:
```bash
cd command-center-dashboard
npm run dev
```

2. Open browser to `http://localhost:3000`
3. Clear localStorage to start fresh (optional):
```javascript
// In browser console
localStorage.clear();
location.reload();
```

## Demo Flow (5-7 minutes)

### 1. Introduction (30 seconds)

"Welcome to the Command Center Dashboard - a real-time disaster response simulation interface. This is designed for emergency coordinators managing a disaster response in Nurdağı, Turkey following a major earthquake."

### 2. Initial View (1 minute)

**Point out the layout:**
- "On the left, we have our operational map taking up 80% of the screen"
- "On the right, our interaction panel with alerts, chat, and timeline controls"
- "The map is currently showing critical incidents as of Hour 4 of the simulation"

**Highlight the map:**
- "You can see two critical incidents marked - a building collapse and a hospital at capacity"
- "The map automatically zoomed to fit all incidents in view"

### 3. Chat Interface (2 minutes)

**Show the initial agent message:**
- "The agent has already greeted us and explained what we're seeing"

**Type a query:**
```
Show me all food and water needs
```

**After response:**
- "The agent has identified 2 demand zones and a mobile kitchen"
- "Notice how the map automatically updated to show these new layers"
- "The demand zone is shown as a polygon, and the supply site as a point"
- "The map re-centered to show all relevant data"

**Click suggested action:**
- "The agent is also suggesting actions we can take"
- "Let's click 'Calculate route from kitchen to demand zone'"
- "This demonstrates how the interface can guide operators through complex workflows"

### 4. Real-Time Updates (1 minute)

**Wait for or explain polling:**
- "Every 5 seconds, the system polls for new data"
- "When new information comes in, it's automatically added to the map"
- "Critical alerts appear in the alerts panel at the top, regardless of what you're viewing"

**If an alert appears:**
- "Here's a critical alert about an imminent structural failure"
- "This ensures operators never miss urgent information"

### 5. Timeline Control (1 minute)

**Drag the timeline slider:**
- "The timeline slider lets us navigate through the 7-day simulation"
- "Let's jump ahead to Day 2"
- "Notice how the entire view refreshes with data from that time period"
- "The simulation time updates in the display"

### 6. Session Persistence (30 seconds)

**Refresh the page:**
- "If I refresh the page..."
- "The system remembers where we were in the timeline"
- "This ensures operators don't lose their place if they need to step away"

### 7. Architecture Highlights (1 minute)

**Quick technical overview:**
- "Built with Next.js and React for a modern, performant foundation"
- "Mapbox GL for high-quality vector map rendering"
- "Zustand for clean, centralized state management"
- "Unidirectional data flow ensures predictability"
- "Currently using mock data, but designed for easy backend integration"

### 8. Closing (30 seconds)

"This dashboard demonstrates how AI agents can provide intelligent, context-aware assistance in high-stakes disaster response scenarios. The interface adapts to the operator's needs, proactively surfaces critical information, and guides them through complex decision-making processes."

## Key Points to Emphasize

1. **Real-time responsiveness** - Data updates automatically
2. **Context awareness** - Agent understands what you're looking for
3. **Proactive assistance** - Suggested actions guide the workflow
4. **Critical information** - Alerts always visible regardless of context
5. **Session continuity** - State persists across page refreshes
6. **Clean architecture** - Easy to extend and integrate with real backends

## Backup Talking Points

If you have extra time or questions:

### Data Flow
- "The architecture uses a clean unidirectional data flow"
- "User actions trigger API calls, which update the central store"
- "All components subscribe to the store and re-render automatically"

### Scalability
- "The map can handle multiple layer types: points, polygons, and linestrings"
- "The REPLACE vs APPEND pattern allows for both full refreshes and incremental updates"
- "This keeps the interface responsive even with large datasets"

### Extensibility
- "The mock API service has the same interface as a real API would"
- "Swapping to a real backend is just a matter of replacing one file"
- "The component structure is modular and easy to extend"

### User Experience
- "The 80/20 split keeps the map as the primary focus"
- "Dark theme reduces eye strain during long operations"
- "Loading states provide feedback during data fetches"
- "Suggested actions reduce cognitive load on operators"

## Common Questions & Answers

**Q: Can it handle multiple users?**
A: The current implementation is single-user, but the architecture supports adding multi-user features through WebSocket connections and shared state management.

**Q: How does it scale with more data?**
A: Mapbox GL is highly optimized for large datasets. We can add clustering, filtering, and pagination as needed.

**Q: What about mobile devices?**
A: The current design is optimized for desktop command centers, but the responsive Tailwind CSS framework makes mobile adaptation straightforward.

**Q: How do you ensure data accuracy?**
A: The agent responses include timestamps and source information. In production, we'd add data validation, audit logs, and confidence scores.

**Q: Can it integrate with existing systems?**
A: Yes, the API service layer is designed to be a thin wrapper around any REST or GraphQL backend.
