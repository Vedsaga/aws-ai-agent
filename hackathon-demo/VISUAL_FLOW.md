# DomainFlow Visual Flow

## Complete Demo Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SCENE 1: INGESTION                              │
└─────────────────────────────────────────────────────────────────────────┘

USER TYPES:
┌──────────────────────────────────────────────────────────────┐
│ "Street light broken near the post office"                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: 🔄 data-ingestion agent processing...                │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  BEDROCK      │
                    │  Claude 3.5   │
                    │  Sonnet       │
                    └───────────────┘
                            │
                            ↓
AGENT ANALYZES:
┌──────────────────────────────────────────────────────────────┐
│ ✓ Entity: "street light"                                     │
│ ✓ Severity: "high" (broken = urgent)                         │
│ ✗ Location: "near post office" (TOO VAGUE!)                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
AGENT RESPONDS:
┌──────────────────────────────────────────────────────────────┐
│ "Can you confirm the exact street address or intersection?"  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: ⚠️  Needs clarification                              │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
USER TYPES:
┌──────────────────────────────────────────────────────────────┐
│ "Yes, it's at 123 Main Street"                               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: 🔄 data-ingestion agent processing...                │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  BEDROCK      │
                    │  (with        │
                    │  history)     │
                    └───────────────┘
                            │
                            ↓
AGENT EXTRACTS:
┌──────────────────────────────────────────────────────────────┐
│ {                                                             │
│   "location": "123 Main Street",                             │
│   "geo_coordinates": [-74.0060, 40.7128],                    │
│   "entity": "broken streetlight",                            │
│   "severity": "high",                                         │
│   "confidence": 0.95                                          │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  DYNAMODB     │
                    │  Save Report  │
                    │  ID: abc-123  │
                    └───────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: ✅ Report saved! ID: abc-123                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │   MAP         │
                    │   📍 Marker   │
                    │   Added       │
                    └───────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                          SCENE 2: QUERY                                  │
└─────────────────────────────────────────────────────────────────────────┘

[SWITCH MODE TO: QUERY]

USER TYPES:
┌──────────────────────────────────────────────────────────────┐
│ "Show me all high-priority streetlight issues"               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: 🔄 data-query agent processing...                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  BEDROCK      │
                    │  Parse Query  │
                    └───────────────┘
                            │
                            ↓
AGENT PARSES:
┌──────────────────────────────────────────────────────────────┐
│ {                                                             │
│   "query_filters": {                                          │
│     "entity": "streetlight",                                  │
│     "severity": "high"                                        │
│   }                                                           │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  DYNAMODB     │
                    │  Scan + Filter│
                    └───────────────┘
                            │
                            ↓
RESULTS:
┌──────────────────────────────────────────────────────────────┐
│ Found 5 reports:                                              │
│ • 123 Main St - broken streetlight - high                    │
│ • 456 Oak Ave - flickering streetlight - high                │
│ • 789 Elm St - broken streetlight - high                     │
│ • 321 Pine Rd - dark streetlight - high                      │
│ • 654 Maple Dr - broken streetlight - high                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: ✅ Found 5 high-priority streetlight reports         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │   MAP         │
                    │   📍📍📍📍📍  │
                    │   5 Markers   │
                    │   (filtered)  │
                    └───────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                          SCENE 3: MANAGEMENT                             │
└─────────────────────────────────────────────────────────────────────────┘

[SWITCH MODE TO: MANAGEMENT]

USER TYPES:
┌──────────────────────────────────────────────────────────────┐
│ "Assign this report to Team B and make it due in 48 hours"   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: 🔄 data-management agent processing...               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  BEDROCK      │
                    │  Parse Command│
                    └───────────────┘
                            │
                            ↓
AGENT PARSES:
┌──────────────────────────────────────────────────────────────┐
│ {                                                             │
│   "report_id": "abc-123",                                     │
│   "updates": {                                                │
│     "assignee": "Team B",                                     │
│     "due_at": "2025-10-25T10:00:00Z",                        │
│     "status": "in_progress"                                   │
│   }                                                           │
│ }                                                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │  DYNAMODB     │
                    │  Update Report│
                    │  ID: abc-123  │
                    └───────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STATUS: ✅ Assigned to Team B, due October 25, 2025         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
                    ┌───────────────┐
                    │   MAP         │
                    │   📍 Marker   │
                    │   Updated     │
                    │   (click to   │
                    │   see details)│
                    └───────────────┘
```

## Agent Decision Tree

```
                        ┌─────────────┐
                        │ User Input  │
                        └─────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │  Which Mode?     │
                    └──────────────────┘
                    │        │        │
        ┌───────────┘        │        └───────────┐
        ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ INGESTION    │    │   QUERY      │    │ MANAGEMENT   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Extract:     │    │ Parse:       │    │ Parse:       │
│ • Location   │    │ • Filters    │    │ • Action     │
│ • Entity     │    │ • Intent     │    │ • Target     │
│ • Severity   │    │ • Scope      │    │ • Values     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Validate:    │    │ Query DB:    │    │ Update DB:   │
│ Confidence?  │    │ Apply filters│    │ Merge changes│
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
    ┌───┴───┐                ↓                    ↓
    ↓       ↓        ┌──────────────┐    ┌──────────────┐
┌──────┐ ┌──────┐   │ Format:      │    │ Confirm:     │
│ Low  │ │ High │   │ • Summary    │    │ • What       │
│ Conf │ │ Conf │   │ • GeoJSON    │    │   changed    │
└──────┘ └──────┘   │ • Count      │    │ • When       │
    │       │        └──────────────┘    └──────────────┘
    ↓       ↓                │                    │
┌──────┐ ┌──────┐           ↓                    ↓
│ Ask  │ │ Save │   ┌──────────────┐    ┌──────────────┐
│ User │ │ Data │   │ Return to    │    │ Return to    │
└──────┘ └──────┘   │ User         │    │ User         │
                     └──────────────┘    └──────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │  Chat    │  │  Modes   │  │  Map (Mapbox)            │  │
│  │  UI      │  │  Switch  │  │  • Markers               │  │
│  └──────────┘  └──────────┘  │  • Popups                │  │
│                               │  • Zoom/Pan              │  │
│                               └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ POST /orchestrate
                            │ {mode, message, session_id}
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                               │
│  • CORS enabled                                              │
│  • No auth (demo)                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    LAMBDA ORCHESTRATOR                       │
│                                                              │
│  def lambda_handler(event, context):                         │
│      mode = event['mode']                                    │
│      if mode == 'ingestion':                                 │
│          return handle_ingestion()                           │
│      elif mode == 'query':                                   │
│          return handle_query()                               │
│      elif mode == 'management':                              │
│          return handle_management()                          │
└─────────────────────────────────────────────────────────────┘
            │                   │                   │
            │                   │                   │
            ↓                   ↓                   ↓
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Bedrock     │    │  Bedrock     │    │  Bedrock     │
    │  Ingestion   │    │  Query       │    │  Management  │
    │  Prompt      │    │  Prompt      │    │  Prompt      │
    └──────────────┘    └──────────────┘    └──────────────┘
            │                   │                   │
            └───────────────────┴───────────────────┘
                            │
                            ↓
                    ┌──────────────┐
                    │  DYNAMODB    │
                    │  civic-      │
                    │  reports     │
                    └──────────────┘
                            │
                            ↓
                    ┌──────────────┐
                    │  EventBridge │
                    │  Status      │
                    │  Events      │
                    └──────────────┘
```

## Severity Color Coding

```
┌────────────────────────────────────────────────────────┐
│  SEVERITY LEVELS                                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│  🔴 CRITICAL  (Red #ef4444)                            │
│     • Immediate danger                                  │
│     • Requires urgent response                          │
│     • Example: Gas leak, downed power line             │
│                                                         │
│  🟠 HIGH      (Orange #f59e0b)                         │
│     • Significant issue                                 │
│     • Response within 24h                               │
│     • Example: Broken streetlight, large pothole       │
│                                                         │
│  🟡 MEDIUM    (Yellow #eab308)                         │
│     • Moderate issue                                    │
│     • Response within 1 week                            │
│     • Example: Graffiti, minor damage                  │
│                                                         │
│  🟢 LOW       (Green #22c55e)                          │
│     • Minor issue                                       │
│     • Response when convenient                          │
│     • Example: Cosmetic issues, suggestions            │
│                                                         │
└────────────────────────────────────────────────────────┘
```

## Timeline

```
0:00 ─────────────────────────────────────────────────── 5:00
│                                                           │
├─ 0:00-0:30: Opening                                      │
│  • Introduce concept                                     │
│  • Show interface                                        │
│                                                          │
├─ 0:30-2:30: Scene 1 (Ingestion)                         │
│  • Vague input                                           │
│  • Clarification                                         │
│  • Precise input                                         │
│  • Data saved                                            │
│  • Map updated                                           │
│                                                          │
├─ 2:30-4:00: Scene 2 (Query)                             │
│  • Switch mode                                           │
│  • Ask question                                          │
│  • See results                                           │
│  • Map filtered                                          │
│                                                          │
├─ 4:00-5:00: Scene 3 (Management) + Closing              │
│  • Switch mode                                           │
│  • Give command                                          │
│  • See update                                            │
│  • Wrap up                                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
