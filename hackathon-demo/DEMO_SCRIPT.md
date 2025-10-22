# DomainFlow Demo Script

## Opening (30 seconds)

"Hello, and welcome. We're DomainFlow, and we're showing a new way to build data-driven applications. Our platform is built on three core agent classes: Data-Ingestion, Data-Query, and Data-Management.

Each class is wrapped by an orchestrator and verifier, which intelligently routes tasks to sub-agents. This architecture lets us replace rigid, custom-built apps and instead, use AI as the flexible interface for our data."

## Scene 1: Data Ingestion with Clarification (2 minutes)

**[Switch to browser, show frontend]**

"Let's see this in action with our 'Civic Complaints' domain. A user doesn't see a form; they just start talking."

**[Type in chat]:** "There's a broken streetlight near the post office"

**[Point to screen]**

"They're typing in a report about a streetlight, but the location is vague: 'near the post office'."

**[Agent status panel appears showing real-time execution]**

"Watch the agent execution panel. You can see:
- The Orchestrator planning which agents to run
- Geo Agent extracting location - confidence 60% - too low!
- Entity Agent identifying 'streetlight' - confidence 95%
- Severity Agent determining 'high' - confidence 90%
- The Verifier checking confidence scores"

**[Agent responds with clarification question]**

"A normal app would fail. But our Verifier sees the Geo Agent's confidence is too low. Instead of guessing, it asks for clarification."

**[Show status indicator]**

"As you see, the system is asking the user to confirm the location. This is the Verifier in action."

**[Type]:** "Yes, it's at 123 Main Street"

**[Agent confirms and saves]**

"The user replies 'Yes'... and now the data is grounded."

**[Map updates with marker]**

"Let's look at the admin panel. Instantly, the report is on the map. That conversation has been transformed into a perfectly structured, verified, JSON document."

## Scene 2: Data Query (1.5 minutes)

**[Switch mode to Query]**

"So, we've created data. Now, let's manage it. The admin doesn't need a separate dashboard. They just talk to the same system."

**[Type]:** "Show me all high-priority streetlight issues"

**[Point to status]**

"First, a 'read' query: 'Show me all high-priority streetlights.'"

**[Agent responds, map updates]**

"Our Data-Query orchestrator understands this 'read' intent. It runs the query, and the map updates to show the grounded results."

**[Point to map markers]**

"Here we can see all the high-priority streetlight reports, color-coded by severity."

## Scene 3: Data Management (1.5 minutes)

**[Switch mode to Management]**

"But here's the most powerful part. The admin is now typing a 'write' command:"

**[Type]:** "Assign this report to Team B and make it due in 48 hours"

**[Point to screen]**

"A traditional app would need a whole new 'Tasks API' for this. Our platform just sees this as a new intent and routes it to our Data-Management agent playbook."

**[Agent processes and confirms]**

"Watch the screen. As the agent confirms, the data on the map is updating in real-time."

**[Click on marker to show popup with assignment]**

"That pin now has the new assignment details. We've used natural language to update our database, with no custom API needed."

## Closing (30 seconds)

**[Face camera]**

"What you've just seen is an end-to-end workflow. We've shown how this architecture allows you to build data applications, not by writing new code, but by writing new prompts for new agents.

We built a 'Civic' domain today, but we could configure a 'Hospital' or 'Logistics' domain tomorrow. Thank you."

---

## Technical Talking Points (If Asked)

### Architecture
- Single DynamoDB table for reports
- Lambda orchestrator with Bedrock (Claude 3.5 Sonnet)
- EventBridge for real-time status
- No authentication (demo only)

### Agent Classes
1. **Data-Ingestion**: Extracts geo, entity, severity. Validates confidence. Asks for clarification when needed.
2. **Data-Query**: Parses natural language queries. Filters DynamoDB. Returns GeoJSON for map visualization.
3. **Data-Management**: Updates assignments, status, due dates. Tracks change history.

### Why This Matters
- Traditional apps: Build new API for every feature
- DomainFlow: Configure new agent with prompt
- Same infrastructure, infinite use cases
- AI as the flexible data interface

### Demo Limitations
- No auth (would use Cognito in production)
- Simple DynamoDB scan (would use GSI in production)
- Mock geocoding (would use AWS Location Service)
- No file uploads (would use S3 presigned URLs)

### Next Steps
- Multi-tenant isolation
- Agent chaining for complex workflows
- Verification agents for data quality
- Integration with external systems (Jira, ServiceNow)
