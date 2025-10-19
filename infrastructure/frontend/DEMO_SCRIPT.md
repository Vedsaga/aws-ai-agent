# MVP Demo Script - Multi-Agent Orchestration System

## Demo Overview
**Duration:** 5 minutes
**Audience:** Hackathon judges
**Goal:** Showcase the multi-agent orchestration system with dark mode UI, real-time processing, and data visualization

## Pre-Demo Checklist
- [ ] Frontend server running (`npm run dev` in infrastructure/frontend)
- [ ] Backend APIs accessible and healthy
- [ ] Browser open to http://localhost:3000
- [ ] DevTools closed (or minimized)
- [ ] Test user credentials ready
- [ ] Sample data prepared (3-5 incidents per domain)
- [ ] Network connection stable
- [ ] Screen recording started (backup)

## Demo Flow

### 1. Introduction (30 seconds)

**Script:**
> "Welcome! Today I'm presenting our Multi-Agent Orchestration System - a platform that uses specialized AI agents to process unstructured data in real-time. The system features a dark mode UI, multi-domain support, and live data visualization."

**Actions:**
- Show login page
- Briefly explain multi-tenant architecture
- Log in with demo credentials

**Key Points:**
- Multi-tenant SaaS platform
- AWS-powered backend (API Gateway, Lambda, RDS, OpenSearch)
- React/Next.js frontend with Shadcn UI

---

### 2. Civic Complaint Submission (90 seconds)

**Script:**
> "Let's start with a civic complaint use case. Citizens can report issues like potholes, broken street lights, or trash problems. Watch how our specialized agents extract structured data in real-time."

**Actions:**
1. Navigate to dashboard
2. Point out dark mode UI and map
3. Select "Civic Complaints" from domain selector
4. Click "Submit Report" tab
5. Enter text: "Large pothole on Main Street near 5th Avenue causing traffic issues"
6. (Optional) Upload a sample image
7. Click Submit

**What to Highlight:**
- ✨ Dark mode theme (consistent across UI and map)
- ✨ Domain selector with built-in domains
- ✨ Real-time status updates showing agent execution
- ✨ Agent names appearing: Entity Agent, Geo Agent, Temporal Agent
- ✨ Status progression: loading → invoking → complete

**Wait for Processing:**
- Point out status panel showing agent progress
- Mention: "Three ingestion agents are processing this report"
- Explain: Entity Agent extracts category, Geo Agent finds location, Temporal Agent determines urgency

**After Processing:**
8. Point to new marker on map
9. Highlight custom marker with category icon (🕳️) and color (red)
10. Click marker to show detailed popup

**What to Highlight in Popup:**
- ✨ Category header with color coding
- ✨ Original report text
- ✨ Structured data extracted by each agent
- ✨ Image evidence (if uploaded)
- ✨ "View Full Details" button

---

### 3. Query and Analysis (90 seconds)

**Script:**
> "Now let's analyze the data. Domain creators can ask questions about trends and patterns. Our query agents provide insights from different analytical perspectives."

**Actions:**
1. Click "Ask Question" tab
2. Enter query: "What are the trends in pothole complaints this month?"
3. (If clarification appears) Answer questions:
   - Time range: "This month"
   - Location: "All"
4. Click Submit

**What to Highlight:**
- ✨ Query clarification system (if triggered)
- ✨ Real-time status showing query agents executing
- ✨ Multiple query agents: Trend Analyzer, Pattern Detector, Severity Classifier

**After Processing:**
5. Point out bullet points (one per query agent)
6. Highlight summary at bottom
7. Show map updating with query results

**What to Highlight:**
- ✨ Structured insights from multiple agents
- ✨ AI-generated summary
- ✨ Map visualization of query results
- ✨ Interactive data exploration

---

### 4. Domain Management (60 seconds)

**Script:**
> "The system supports multiple domains. Let's switch to management mode to see all available domains and their data."

**Actions:**
1. Click "Manage Domain" tab in ViewModeSwitcher
2. Show domain grid with cards
3. Point out "Created by me" badges
4. Click "View Data" on Civic Complaints domain

**What to Highlight:**
- ✨ Domain grid with 3 built-in domains
- ✨ "Created by me" badges for user-created domains
- ✨ Agent counts per domain
- ✨ Clean, organized layout

**In Data Table:**
5. Show table with incidents
6. Demonstrate filtering (select category)
7. Demonstrate sorting (click column header)
8. Click a row to open detail modal

**What to Highlight:**
- ✨ Tabulated view of all incidents
- ✨ Filtering by category, date, location
- ✨ Sorting by any column
- ✨ Detailed modal with mini map

---

### 5. Error Handling Demo (30 seconds)

**Script:**
> "The system includes robust error handling with user-friendly notifications."

**Actions:**
1. Go back to dashboard
2. Try to submit without selecting domain
3. Show validation error toast
4. Fill form correctly
5. Submit successfully

**What to Highlight:**
- ✨ Validation error toast (red, clear message)
- ✨ Form validation before submission
- ✨ Success confirmation
- ✨ No network error spam on page load (bug fixed!)

---

### 6. Domain Switching (30 seconds)

**Script:**
> "Each domain maintains its own chat history. Watch what happens when we switch domains."

**Actions:**
1. Note current chat messages
2. Switch to "Disaster Response" domain
3. Show chat history clears
4. Switch back to "Civic Complaints"
5. Show chat history restored

**What to Highlight:**
- ✨ Per-domain chat history
- ✨ LocalStorage persistence
- ✨ Seamless domain switching
- ✨ Context preservation

---

### 7. Wrap-up (30 seconds)

**Script:**
> "To summarize, our Multi-Agent Orchestration System provides:
> - Real-time processing with specialized AI agents
> - Dark mode UI with excellent UX
> - Multi-domain support for different use cases
> - Interactive data visualization
> - Robust error handling
> 
> All powered by AWS serverless architecture with API Gateway, Lambda, RDS, and OpenSearch. Thank you!"

**Actions:**
- Show dashboard one more time
- Highlight key features on screen
- Open to questions

---

## Key Features to Emphasize

### Technical Excellence:
1. ✅ **Real-time Processing** - WebSocket status updates via AppSync
2. ✅ **Multi-Agent Architecture** - Specialized agents for different tasks
3. ✅ **Serverless AWS Stack** - Scalable, cost-effective infrastructure
4. ✅ **Dark Mode UI** - Modern, accessible design with Shadcn UI
5. ✅ **Data Visualization** - Interactive Mapbox maps with custom markers

### User Experience:
1. ✅ **Intuitive Interface** - Clean, organized layout
2. ✅ **Error Handling** - Clear, actionable error messages
3. ✅ **Real-time Feedback** - Users see exactly what's happening
4. ✅ **Multi-domain Support** - One platform, many use cases
5. ✅ **Data Management** - Powerful filtering, sorting, and search

### Innovation:
1. ✅ **Query Clarification** - AI asks follow-up questions for ambiguous queries
2. ✅ **Custom Markers** - Category-based icons and colors
3. ✅ **Geometry Support** - Points, lines, and polygons on map
4. ✅ **Chat History** - Per-domain conversation persistence
5. ✅ **Role Switching** - Use mode vs Manage mode

---

## Backup Plan (If Technical Issues)

### If Backend is Down:
1. Show screenshots of working system
2. Walk through code architecture
3. Explain agent design and orchestration
4. Show database schema and API design

### If Frontend Crashes:
1. Restart development server
2. While waiting, explain architecture
3. Show code examples
4. Discuss design decisions

### If Network is Slow:
1. Use pre-recorded video
2. Narrate over video
3. Show code and architecture diagrams
4. Answer questions about implementation

---

## Sample Data for Demo

### Civic Complaints:
1. "Large pothole on Main Street near 5th Avenue"
2. "Broken street light at Park Avenue and 3rd Street"
3. "Overflowing trash bins in Central Park"
4. "Damaged sidewalk on Elm Street causing safety hazard"
5. "Graffiti on public building at City Hall"

### Disaster Response:
1. "Flooding on River Road affecting 10 homes"
2. "Fire reported at 123 Oak Street, multiple units responding"
3. "Power outage in downtown area affecting 500 residents"

### Agriculture:
1. "Pest infestation detected in wheat field sector A"
2. "Irrigation system failure in corn field B"
3. "Soil moisture levels critical in vineyard C"

---

## Questions & Answers Preparation

### Q: How does the multi-agent system work?
**A:** "Each agent is a specialized Lambda function with a specific role. Ingestion agents extract structured data (entity, location, time), while query agents analyze data from different perspectives (trends, patterns, severity). The orchestrator coordinates agent execution using Step Functions."

### Q: How do you handle agent failures?
**A:** "We have comprehensive error handling at multiple levels. If an agent fails, the system continues with other agents and shows the error in the status panel. We also have retry logic and fallback mechanisms."

### Q: Can users create custom agents?
**A:** "Yes! The system includes an agent creation interface where users can define custom agents with their own prompts, tools, and output schemas. This makes the platform extensible for any use case."

### Q: What's the scalability of the system?
**A:** "It's fully serverless on AWS, so it scales automatically. API Gateway handles request routing, Lambda functions scale to zero when not in use, and RDS Aurora can scale read replicas. We can handle thousands of concurrent requests."

### Q: How do you ensure data privacy?
**A:** "We use multi-tenant architecture with tenant isolation at the database level. Each user's data is segregated, and we use Cognito for authentication with JWT tokens. All API calls are authenticated and authorized."

---

## Post-Demo Actions

### If Demo Goes Well:
- [ ] Thank judges
- [ ] Provide GitHub repo link
- [ ] Offer to answer technical questions
- [ ] Share architecture diagrams
- [ ] Provide contact information

### If Demo Has Issues:
- [ ] Acknowledge the issue calmly
- [ ] Explain what should have happened
- [ ] Show backup materials (screenshots, video)
- [ ] Emphasize the working features
- [ ] Offer to demo again later

---

## Demo Success Criteria

### Must Show:
- ✅ Report submission with real-time status
- ✅ Map visualization with custom markers
- ✅ Query processing with results
- ✅ Domain switching
- ✅ Data table view

### Nice to Show:
- ✅ Error handling
- ✅ Query clarification
- ✅ Detailed popups
- ✅ Filtering and sorting
- ✅ Chat history persistence

### Bonus Points:
- ✅ Geometry rendering (LineString, Polygon)
- ✅ Severity indicators
- ✅ Image evidence
- ✅ Mini map in detail modal
- ✅ Performance (fast, responsive)

---

## Final Checklist

**Before Demo:**
- [ ] Test entire flow end-to-end
- [ ] Verify all features work
- [ ] Prepare sample data
- [ ] Check network connection
- [ ] Close unnecessary tabs/apps
- [ ] Start screen recording
- [ ] Have backup plan ready

**During Demo:**
- [ ] Speak clearly and confidently
- [ ] Highlight key features
- [ ] Show real-time processing
- [ ] Demonstrate error handling
- [ ] Engage with judges

**After Demo:**
- [ ] Answer questions thoroughly
- [ ] Provide additional materials
- [ ] Thank judges for their time
- [ ] Follow up if needed

---

## Good Luck! 🚀

Remember:
- Stay calm and confident
- Focus on the value proposition
- Highlight technical excellence
- Show, don't just tell
- Have fun!
