# Diagram 10: Query Pipeline End-to-End Flow

## Purpose
Complete flow from user question to multi-perspective response with bullet points and summary.

## Diagram

```mermaid
flowchart TB
    User["User asks question<br/>What are pothole trends"]
    
    APIGW["API Gateway<br/>POST /api/v1/query"]
    
    QueryHandler["Query Handler Lambda<br/>Start Step Functions"]
    
    StepFunctions["Step Functions<br/>Load query playbook<br/>Build execution plan"]
    
    ParallelQuery["Execute Query Agents<br/>What Where When Why<br/>Each analyzes from perspective"]
    
    DataAPIs["Query Agents call<br/>Data Access APIs<br/>Retrieval Aggregation Analytics"]
    
    Aggregate["Aggregate Results<br/>Collect all agent outputs"]
    
    ResponseFormat["Response Formatter<br/>Generate bullets<br/>One per agent"]
    
    GenerateSummary["Generate Summary<br/>Synthesize insights"]
    
    VizUpdate["Visualization Generator<br/>Update map if needed"]
    
    AppSync["AppSync broadcasts<br/>Real-time status"]
    
    User -->|Step 1| APIGW
    APIGW -->|Step 2| QueryHandler
    QueryHandler -->|Step 3| StepFunctions
    StepFunctions -->|Step 4| ParallelQuery
    ParallelQuery -->|Step 5| DataAPIs
    DataAPIs -->|Step 6| Aggregate
    Aggregate -->|Step 7| ResponseFormat
    ResponseFormat -->|Step 8| GenerateSummary
    GenerateSummary -->|Step 9| VizUpdate
    VizUpdate -->|Step 10| User
    
    StepFunctions -.->|Status updates| AppSync
    ParallelQuery -.->|Status updates| AppSync
    ResponseFormat -.->|Status updates| AppSync
    AppSync -.->|WebSocket| User

    classDef userBox fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef processBox fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef statusBox fill:#e0f7fa,stroke:#00838f,stroke-width:2px
    
    class User userBox
    class APIGW,QueryHandler,StepFunctions,ParallelQuery,DataAPIs,Aggregate,ResponseFormat,GenerateSummary,VizUpdate processBox
    class AppSync statusBox
```

## Flow Steps

1. User asks "What are the trends in pothole complaints?"
2. API Gateway validates JWT and routes to query handler
3. Handler starts Step Functions with query playbook
4. Step Functions loads query agents (What, Where, When, Why)
5. Query agents execute in parallel, each calling Data APIs
6. What Agent: Analyzes complaint types and categories
7. Where Agent: Analyzes geographic distribution
8. When Agent: Analyzes temporal patterns
9. Why Agent: Analyzes root causes
10. Results aggregated from all agents
11. Response Formatter generates bullet points (one per agent)
12. Summary generated synthesizing all insights
13. Visualization updated if spatial data present

## Example Response

```
Question: "What are the trends in pothole complaints?"

Response:
• What: 45 pothole complaints received, primarily road surface damage
• Where: Concentrated in downtown area and District 5
• When: 80% reported in last 2 weeks, peak on weekdays 8-10am
• Why: Recent heavy rainfall caused road deterioration

Summary: Pothole complaints have surged in downtown due to recent rainfall, with 45 reports concentrated in high-traffic areas during morning commute hours.
```

## Query Agent Execution

Each query agent:
- Receives raw question text
- Loads ingestion agent schemas for context
- Calls appropriate Data APIs
- Analyzes from interrogative perspective
- Returns max 5 keys with 1-2 line insight
