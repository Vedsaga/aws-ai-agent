# API Checklist - All Exist! ✅

## Your Questions → API Endpoints

### ✅ Fetching all custom agents created
**API:** `GET /api/v1/config?type=agent`
- Returns all agents (built-in + custom) for your tenant
- File: `infrastructure/lambda/config-api/config_handler.py` (line 100+)

### ✅ Fetching the agent dependency graph
**API:** `GET /api/v1/config?type=dependency_graph`
- Returns all dependency graphs for your tenant
- File: `infrastructure/lambda/config-api/config_handler.py` (line 100+)

### ✅ Fetching the built-in agents
**API:** `GET /api/v1/config?type=agent`
- Same endpoint, filter by `is_builtin: true` on frontend
- Built-in agents: GeoAgent, TemporalAgent, EntityAgent, Query Agents (When, Where, Why, etc.)

### ✅ Creating custom agent
**API:** `POST /api/v1/config`
```json
{
  "type": "agent",
  "config": {
    "agent_name": "Priority Scorer",
    "agent_type": "custom",
    "system_prompt": "Score priority 1-10",
    "tools": ["bedrock"],
    "output_schema": {
      "priority": "number",
      "reasoning": "string"
    },
    "dependency_parent": "entity_agent_id"
  }
}
```
- File: `infrastructure/lambda/config-api/config_handler.py` (line 60+)

### ✅ Updating custom agent
**API:** `PUT /api/v1/config/agent/{agent_id}`
```json
{
  "config": {
    "agent_name": "Updated Name",
    ...
  }
}
```
- File: `infrastructure/lambda/config-api/config_handler.py` (line 130+)

### ✅ Fetching custom domains (make available for public use)
**API:** `GET /api/v1/config?type=domain_template`
- Returns all domain templates for your tenant
- Built-in domains: Civic Complaints, Disaster Response, Agriculture
- File: `infrastructure/lambda/config-api/config_handler.py` (line 100+)

### ✅ Creating custom domain
**API:** `POST /api/v1/config`
```json
{
  "type": "domain_template",
  "config": {
    "template_name": "My Custom Domain",
    "domain_id": "my_custom_domain",
    "agent_configs": [...],
    "playbook_configs": [...]
  }
}
```
- File: `infrastructure/lambda/config-api/config_handler.py` (line 60+)

## Dashboard Features

### ✅ Chat with domain (80% map, 20% chat)
**Already implemented!**
- File: `infrastructure/frontend/app/dashboard/page.tsx`
- Layout: `w-4/5` (80%) for map, `w-1/5` (20%) for chat
- Two tabs: "Submit Report" (ingestion) and "Ask Question" (query)

### ✅ Data table view for domain creators
**API:** `GET /api/v1/data?type=retrieval&filters={...}`
- Returns all incidents with structured data
- File: `infrastructure/lambda/data-api-proxies/retrieval_proxy.py`
- Supports filters: date_range, location, category, custom fields

**What's missing:** Frontend component to display the table
- Need to create `DataTableView.tsx` component
- Add a new tab or page for table view

### ✅ Ask questions and interact with data
**API:** `POST /api/v1/query`
```json
{
  "domain_id": "civic_complaints",
  "question": "What are the trends in pothole complaints?"
}
```
- Returns: job_id for tracking
- Real-time updates via AppSync WebSocket
- File: `infrastructure/lambda/orchestration/` (query pipeline)

**Already implemented!**
- File: `infrastructure/frontend/components/QueryPanel.tsx`
- Submits questions to query API
- Displays real-time status updates

## What's Actually Missing (Frontend Only)

1. **Dark mode** - Need to add Shadcn UI with dark theme
2. **Error toasts** - Need to add toast notifications for errors
3. **Domain selector** - Need dropdown to select domain before submit
4. **Data table component** - Need to create table view for incidents
5. **Better status display** - Improve real-time status UI

## Summary

**Backend: 100% Complete ✅**
- All APIs exist and are deployed
- Agent creation, dependency graphs, domains all working
- Data retrieval, query pipeline all functional

**Frontend: ~60% Complete**
- Dashboard layout exists (80% map, 20% chat)
- Agent creation form exists
- Dependency graph editor exists
- Map view exists
- Query panel exists

**Frontend Gaps: ~40%**
- Dark mode styling
- Error handling UI
- Domain selector
- Data table view
- Polish and UX improvements

**Time estimate: 8-12 hours of focused frontend work**
