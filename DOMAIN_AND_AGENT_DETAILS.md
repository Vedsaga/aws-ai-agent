# Complete Domain and Agent Details

## Built-in Domains (3)

### 1. Civic Complaints Domain

**Domain ID:** `civic_complaints`
**Description:** Citizen-reported infrastructure and service issues (potholes, street lights, broken sidewalks, etc.)

#### Ingestion Agents (4)

**1.1 Geo Agent**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock, Amazon Location Service, Web Search
- **Output Schema (4 keys):**
  ```json
  {
    "location": "string",        // e.g., "Main Street near City Hall"
    "coordinates": "array",      // e.g., [40.7128, -74.0060]
    "address": "string",         // e.g., "123 Main St, New York, NY"
    "confidence": "number"       // e.g., 0.95
  }
  ```

**1.2 Temporal Agent**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock
- **Output Schema (3 keys):**
  ```json
  {
    "timestamp": "string",       // e.g., "2024-10-19T14:30:00Z"
    "time_reference": "string",  // e.g., "today morning"
    "urgency": "string"          // e.g., "immediate", "urgent", "moderate"
  }
  ```

**1.3 Entity Agent**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock, AWS Comprehend
- **Output Schema (4 keys):**
  ```json
  {
    "entities": "array",         // e.g., ["City Hall", "Department of Transportation"]
    "sentiment": "string",       // e.g., "NEGATIVE", "POSITIVE", "NEUTRAL"
    "key_phrases": "array",      // e.g., ["large pothole", "dangerous condition"]
    "category": "string"         // e.g., "infrastructure", "safety", "environment"
  }
  ```

**1.4 Severity Classifier**
- **Type:** Custom (example)
- **Tools:** Bedrock
- **Dependency:** Depends on Entity Agent (single-level)
- **Output Schema (4 keys):**
  ```json
  {
    "severity": "number",              // e.g., 8 (scale 1-10)
    "reasoning": "string",             // e.g., "Safety hazard affecting pedestrians"
    "urgency_level": "string",         // e.g., "high", "medium", "low"
    "recommended_action": "string"     // e.g., "Immediate repair required"
  }
  ```

#### Query Agents (4 selected)

**1.5 When Agent**
- **Type:** Query (built-in)
- **Interrogative:** When
- **Tools:** Bedrock, Retrieval API, Analytics API
- **Output Schema (3 keys):**
  ```json
  {
    "time_pattern": "string",    // e.g., "Most complaints occur on weekdays"
    "frequency": "string",       // e.g., "15 complaints per week"
    "trend": "string"            // e.g., "Increasing trend in last month"
  }
  ```

**1.6 Where Agent**
- **Type:** Query (built-in)
- **Interrogative:** Where
- **Tools:** Bedrock, Spatial API, Retrieval API
- **Output Schema (3 keys):**
  ```json
  {
    "locations": "array",        // e.g., ["Downtown", "North Side", "East End"]
    "hotspots": "array",         // e.g., [{"location": "Main St", "count": 25}]
    "distribution": "string"     // e.g., "Concentrated in downtown area"
  }
  ```

**1.7 What Agent**
- **Type:** Query (built-in)
- **Interrogative:** What
- **Tools:** Bedrock, Retrieval API, Aggregation API
- **Output Schema (3 keys):**
  ```json
  {
    "incident_types": "array",   // e.g., ["potholes", "street lights", "sidewalks"]
    "common_issues": "array",    // e.g., ["infrastructure damage", "safety hazards"]
    "summary": "string"          // e.g., "Potholes are the most common complaint"
  }
  ```

**1.8 Why Agent**
- **Type:** Query (built-in)
- **Interrogative:** Why
- **Tools:** Bedrock, Analytics API, Retrieval API
- **Output Schema (3 keys):**
  ```json
  {
    "causes": "array",           // e.g., ["weather damage", "aging infrastructure"]
    "factors": "array",          // e.g., ["heavy traffic", "poor maintenance"]
    "analysis": "string"         // e.g., "Winter weather is primary cause"
  }
  ```

---

### 2. Disaster Response Domain

**Domain ID:** `disaster_response`
**Description:** Emergency and disaster incident reporting (floods, fires, earthquakes, etc.)

#### Ingestion Agents (2)

**2.1 Geo Agent (Disaster)**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock, Amazon Location Service
- **Output Schema (3 keys):**
  ```json
  {
    "location": "string",        // e.g., "Riverside District"
    "coordinates": "array",      // e.g., [34.0522, -118.2437]
    "affected_area": "string"    // e.g., "5 square kilometers"
  }
  ```

**2.2 Severity Agent (Disaster)**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock
- **Output Schema (4 keys):**
  ```json
  {
    "severity": "string",        // e.g., "critical", "high", "moderate"
    "urgency_level": "number",   // e.g., 9 (scale 1-10)
    "casualties": "string",      // e.g., "multiple injuries reported"
    "damage_type": "string"      // e.g., "structural damage", "flooding"
  }
  ```

#### Query Agents
- Uses all 11 built-in query agents (When, Where, Why, How, What, Who, Which, How Many, How Much, From Where, What Kind)
- Same output schema as Civic Complaints query agents

---

### 3. Agriculture Domain

**Domain ID:** `agriculture`
**Description:** Agricultural issues and crop monitoring (pest infestations, crop diseases, weather damage)

#### Ingestion Agents (2)

**3.1 Crop Agent**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock
- **Output Schema (4 keys):**
  ```json
  {
    "crop_type": "string",       // e.g., "wheat", "corn", "soybeans"
    "condition": "string",       // e.g., "healthy", "stressed", "diseased"
    "issues": "array",           // e.g., ["aphid infestation", "drought stress"]
    "growth_stage": "string"     // e.g., "flowering", "vegetative", "harvest"
  }
  ```

**3.2 Geo Agent (Agriculture)**
- **Type:** Ingestion (built-in)
- **Tools:** Bedrock, Amazon Location Service
- **Output Schema (3 keys):**
  ```json
  {
    "location": "string",        // e.g., "Johnson Farm, Field 3"
    "coordinates": "array",      // e.g., [41.8781, -87.6298]
    "field_size": "string"       // e.g., "50 acres"
  }
  ```

#### Query Agents
- Uses all 11 built-in query agents
- Same output schema as other domains

---

## All Built-in Query Agents (11)

All query agents share a common output schema (5 keys):

```json
{
  "insight": "string",           // 1-2 line answer from perspective
  "data_points": "array",        // Supporting data (max 5 items)
  "confidence": "number",        // Confidence score (0.0-1.0)
  "source": "string",            // Data source identifier
  "summary": "string"            // Brief summary of analysis
}
```

### Query Agent List

1. **When Agent** - Temporal analysis (when events occurred, time patterns)
2. **Where Agent** - Spatial analysis (where events located, geographic patterns)
3. **Why Agent** - Causal analysis (why events happened, root causes)
4. **How Agent** - Method analysis (how events happened, processes)
5. **What Agent** - Entity analysis (what entities involved, what happened)
6. **Who Agent** - Person analysis (who involved, who reported)
7. **Which Agent** - Selection analysis (which items, which categories)
8. **How Many Agent** - Count analysis (how many incidents, quantities)
9. **How Much Agent** - Magnitude analysis (how much impact, severity)
10. **From Where Agent** - Origin analysis (from where originated, sources)
11. **What Kind Agent** - Type analysis (what kind of events, classifications)

---

## Summary Table

| Domain | Ingestion Agents | Query Agents | Total Agents |
|--------|-----------------|--------------|--------------|
| Civic Complaints | 4 (Geo, Temporal, Entity, Severity) | 4 (When, Where, What, Why) | 8 |
| Disaster Response | 2 (Geo, Severity) | 11 (all interrogatives) | 13 |
| Agriculture | 2 (Crop, Geo) | 11 (all interrogatives) | 13 |

**Total Built-in Agents:** 14 unique agents
- 3 Ingestion agents (Geo, Temporal, Entity)
- 11 Query agents (all interrogatives)
- 1 Custom example (Severity Classifier)

**Note:** Geo Agent is reused across domains with different configurations

---

## Key Constraints

1. **Max 5 keys per agent output** - Enforced by validation layer
2. **Single-level dependencies** - Each agent can depend on max 1 parent
3. **Tool access control** - Agents can only use authorized tools
4. **Tenant isolation** - All data scoped to tenant_id

---

## Example: Civic Complaint Flow

**User Input:**
> "There's a large pothole on Main Street near City Hall. It's been there since yesterday and is causing traffic issues."

**Ingestion Pipeline Output:**

```json
{
  "geo_agent": {
    "location": "Main Street near City Hall",
    "coordinates": [40.7128, -74.0060],
    "address": "Main St & Park Ave, New York, NY",
    "confidence": 0.92
  },
  "temporal_agent": {
    "timestamp": "2024-10-18T00:00:00Z",
    "time_reference": "yesterday",
    "urgency": "moderate"
  },
  "entity_agent": {
    "entities": ["Main Street", "City Hall"],
    "sentiment": "NEGATIVE",
    "key_phrases": ["large pothole", "traffic issues"],
    "category": "infrastructure"
  },
  "severity_classifier": {
    "severity": 7,
    "reasoning": "Infrastructure damage affecting traffic flow",
    "urgency_level": "high",
    "recommended_action": "Schedule repair within 48 hours"
  }
}
```

**Query Example:**
> "What are the trends in pothole complaints?"

**Query Pipeline Output:**

```json
{
  "when_agent": {
    "insight": "Pothole complaints increase by 40% after winter months",
    "data_points": ["Jan: 45", "Feb: 52", "Mar: 63"],
    "confidence": 0.88,
    "source": "analytics_api",
    "summary": "Seasonal pattern with winter peak"
  },
  "where_agent": {
    "insight": "Downtown area has 3x more pothole complaints than suburbs",
    "data_points": ["Downtown: 120", "North Side: 45", "South Side: 38"],
    "confidence": 0.91,
    "source": "spatial_api",
    "summary": "Concentrated in high-traffic downtown area"
  },
  "what_agent": {
    "insight": "Potholes account for 35% of all infrastructure complaints",
    "data_points": ["Potholes: 203", "Street lights: 145", "Sidewalks: 89"],
    "confidence": 0.95,
    "source": "aggregation_api",
    "summary": "Most common infrastructure issue"
  },
  "why_agent": {
    "insight": "Freeze-thaw cycles and heavy traffic are primary causes",
    "data_points": ["Weather: 65%", "Traffic: 25%", "Age: 10%"],
    "confidence": 0.82,
    "source": "analytics_api",
    "summary": "Weather-related infrastructure degradation"
  }
}
```

**Final Response to User:**
- **When:** Pothole complaints increase by 40% after winter months
- **Where:** Downtown area has 3x more pothole complaints than suburbs
- **What:** Potholes account for 35% of all infrastructure complaints
- **Why:** Freeze-thaw cycles and heavy traffic are primary causes

**Summary:** Pothole complaints show a clear seasonal pattern with winter peaks, concentrated in high-traffic downtown areas. Weather-related infrastructure degradation is the primary cause, accounting for 65% of incidents.
