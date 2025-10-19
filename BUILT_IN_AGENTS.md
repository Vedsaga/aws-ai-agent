# Built-in Agents Summary

## Data Ingestion Agents (3)

### 1. GeoAgent
- **Purpose:** Extract location information from text
- **Tools:** Amazon Location Service, Web Search, Bedrock
- **Output (5 keys):**
  - `location_name`: Name of the location
  - `coordinates`: [latitude, longitude]
  - `address`: Full address
  - `confidence`: Confidence score (0.0-1.0)
  - `location_type`: Type (city, street, landmark, etc.)
- **File:** `infrastructure/lambda/agents/geo_agent.py`

### 2. TemporalAgent
- **Purpose:** Extract time/date information from text
- **Tools:** Bedrock
- **Output (5 keys):**
  - `timestamp`: ISO 8601 timestamp
  - `time_expression`: Original time expression
  - `time_type`: Type (absolute, relative, range)
  - `confidence`: Confidence score (0.0-1.0)
  - `timezone`: Timezone identifier
- **File:** `infrastructure/lambda/agents/temporal_agent.py`

### 3. EntityAgent
- **Purpose:** Extract entities, sentiment, and key phrases
- **Tools:** AWS Comprehend, Bedrock
- **Output (5 keys):**
  - `entities`: List of named entities
  - `sentiment`: Sentiment (POSITIVE, NEGATIVE, NEUTRAL, MIXED)
  - `key_phrases`: Important phrases
  - `category`: Content category
  - `confidence`: Confidence score (0.0-1.0)
- **File:** `infrastructure/lambda/agents/entity_agent.py`

## Data Query Agents (11)

All query agents analyze data from different interrogative perspectives:

### 1. WhenAgent
- **Perspective:** Temporal analysis
- **Focus:** When did events occur? Timing patterns?

### 2. WhereAgent
- **Perspective:** Spatial analysis
- **Focus:** Where are events located? Geographic patterns?

### 3. WhyAgent
- **Perspective:** Causal analysis
- **Focus:** Why did events happen? Root causes?

### 4. HowAgent
- **Perspective:** Method analysis
- **Focus:** How did events happen? What methods?

### 5. WhatAgent
- **Perspective:** Entity analysis
- **Focus:** What entities are involved? What happened?

### 6. WhoAgent
- **Perspective:** Person analysis
- **Focus:** Who is involved? Who reported?

### 7. WhichAgent
- **Perspective:** Selection analysis
- **Focus:** Which items? Which categories?

### 8. HowManyAgent
- **Perspective:** Count analysis
- **Focus:** How many incidents? Quantities?

### 9. HowMuchAgent
- **Perspective:** Magnitude analysis
- **Focus:** How much impact? Severity levels?

### 10. FromWhereAgent
- **Perspective:** Origin analysis
- **Focus:** From where did it originate? Sources?

### 11. WhatKindAgent
- **Perspective:** Type analysis
- **Focus:** What kind of events? Classifications?

**Common Output (5 keys for all query agents):**
- `insight`: 1-2 line answer from perspective
- `data_points`: Supporting data (max 5 items)
- `confidence`: Confidence score (0.0-1.0)
- `source`: Data source identifier
- `summary`: Brief summary of analysis

**File:** `infrastructure/lambda/agents/query_agents.py`

## Custom Agents (Example)

### SeverityClassifier (Pre-configured)
- **Purpose:** Classify incident severity
- **Tools:** Bedrock
- **Output (5 keys):**
  - `severity_score`: Score 1-10
  - `severity_level`: low/medium/high/critical
  - `risk_factors`: List of risks
  - `urgency`: immediate/urgent/moderate/low
  - `reasoning`: Explanation
- **Dependency:** Depends on EntityAgent (single-level)
- **File:** `infrastructure/lambda/agents/custom_agent.py`

## Total Built-in Agents: 14

- **Ingestion:** 3 agents
- **Query:** 11 agents
- **Custom (example):** 1 agent (SeverityClassifier)

## Key Constraints

1. **Max 5 keys per agent output** - Enforced by validation layer
2. **Single-level dependencies** - Each agent can depend on max 1 parent
3. **Tool access control** - Agents can only use authorized tools
4. **Tenant isolation** - All agents scoped to tenant_id

## Built-in Domains (3)

### 1. Civic Complaints
- **Ingestion Agents:** GeoAgent, TemporalAgent, EntityAgent, SeverityClassifier
- **Query Agents:** All 11 interrogative agents
- **Use Case:** Potholes, street lights, infrastructure issues

### 2. Disaster Response
- **Ingestion Agents:** GeoAgent, TemporalAgent, EntityAgent
- **Query Agents:** All 11 interrogative agents
- **Use Case:** Emergency reporting, disaster coordination

### 3. Agriculture
- **Ingestion Agents:** GeoAgent, TemporalAgent, EntityAgent
- **Query Agents:** All 11 interrogative agents
- **Use Case:** Crop monitoring, farm issues

## Creating Custom Agents

Users can create unlimited custom agents via:
- **API:** `POST /api/v1/config` with `type: "agent"`
- **UI:** Agent Creation Form at `/config`

**Requirements:**
- Agent name
- System prompt
- Tool selection (from registry)
- Output schema (max 5 keys)
- Optional: Single parent dependency
