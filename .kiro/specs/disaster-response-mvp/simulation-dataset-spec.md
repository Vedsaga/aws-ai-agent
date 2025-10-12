# Sophisticated Simulation Dataset Specification

## 🎯 Objective
Create a comprehensive, realistic dataset that demonstrates the AI agent's ability to handle complex, real-world disaster response scenarios with edge cases, ambiguity, and dynamic variations.

## 📊 Dataset Volume & Distribution

### Total Reports: ~200-300 across 7 days

#### Day 0 (Earthquake Day - 24 hours)
**Total: 120-150 reports**

**Hour 0-6 (Immediate aftermath - 80% emergency):**
- 60-70 reports
- Building collapses with trapped people
- Fire outbreaks and gas leaks
- Immediate medical emergencies
- Infrastructure damage reports
- Power and water outages

**Hour 6-12 (Stabilization - 60% emergency, 40% resource):**
- 30-40 reports
- Continued rescue operations
- First resource shortage reports
- Temporary shelter needs
- Medical supply requests

**Hour 12-24 (Initial response - 50% emergency, 50% resource):**
- 30-40 reports
- Rescue team deployments
- Warehouse inventory updates
- Camp establishment
- Resource distribution begins

#### Day 1-2 (Active rescue phase)
**Total: 60-80 reports**
- 30% emergency, 70% operations
- Search and rescue operations
- Resource distribution logistics
- Warehouse-to-camp supply chains
- Team coordination updates
- Medical facility status

#### Day 3-4 (Transition phase)
**Total: 40-50 reports**
- 20% emergency, 80% recovery
- Secondary medical needs (chronic conditions)
- Blood type specific requests
- Sanitation and hygiene supplies
- Psychological support needs
- Infrastructure assessment

#### Day 5-7 (Recovery phase)
**Total: 20-30 reports**
- 10% emergency, 90% recovery
- Long-term medical supplies
- Reconstruction planning
- Resource inventory management
- Volunteer coordination
- Community support services

---

## 🎭 Persona Distribution

### Citizens (40% of reports)
- Local residents reporting needs
- Community leaders coordinating resources
- Volunteers offering help
- Affected families requesting assistance

### Warehouse Managers (20% of reports)
- Inventory updates
- Supply arrivals and departures
- Resource availability notifications
- Distribution schedules

### Rescue Teams (25% of reports)
- Field operation updates
- Resource requests from field
- Team movement notifications
- Rescue completion reports

### NGO Teams (15% of reports)
- Distribution activities
- Coordination with other organizations
- Resource pooling
- Specialized support (medical, psychological)

---

## 🌍 Language Distribution

- **Turkish:** 60% (primary language)
- **English:** 30% (international teams)
- **Arabic:** 10% (regional support teams)

---

## 🧩 Complex Scenario Categories

### 1. Ambiguous Location References (20% of reports)
**Examples:**
- "Near the old market in the city center"
- "The collapsed building on the main street"
- "Behind the mosque in the northern district"
- "Close to where the fire happened yesterday"
- "In the area with the most damage"

**AI Challenge:** Geo-intelligence agent must resolve using OSM data and context

### 2. Temporal References with Variations (30% of reports)
**Examples:**
- Absolute: "Machine will arrive at 8:15 AM"
- Relative: "Since the earthquake happened"
- Duration: "Will take about 2 hours"
- Contextual: "When the rescue team arrives"
- Vague: "Around dawn", "By evening", "Before nightfall"
- Past: "Building collapsed around 3:30 AM yesterday"

**AI Challenge:** Temporal reasoning agent must normalize and extract

### 3. Multi-Resource Scenarios (15% of reports)
**Examples:**
- "Need food AND medicine AND transportation for 50 people"
- "Have water but need containers to distribute it"
- "Medical supplies arrived but need personnel to administer"
- "Rescue team needs heavy machinery AND medical support"

**AI Challenge:** Resource allocation agent must handle dependencies

### 4. Conflicting or Updating Reports (10% of reports)
**Examples:**
- Initial: "100 people need food at location X"
- Update: "Only 60 people remain, 40 were evacuated"
- Conflict: Two reports about same location with different numbers
- Correction: "Previous report was incorrect, building is at different location"

**AI Challenge:** Validation agent must detect and flag conflicts

### 5. Implicit Needs (15% of reports)
**Examples:**
- "Elderly people trapped on 3rd floor" → Implies need for: rescue team, medical support, mobility assistance
- "Children crying in damaged school" → Implies: psychological support, food, shelter
- "Diabetic patient without medication for 2 days" → Implies: urgent insulin, medical monitoring

**AI Challenge:** Triage agent must infer implicit requirements

### 6. Supply Chain Tracking (10% of reports)
**Examples:**
- Warehouse: "Sent 100 food packages to Camp A at 10 AM"
- Rescue Team: "Picked up 100 food packages from Warehouse B"
- NGO: "Distributed 80 food packages, 20 remaining"
- Citizen: "Received food package from NGO team"

**AI Challenge:** Resource allocation agent must track flow

---

## 📝 Sample Report Templates

### Emergency Report (Day 0, Hour 2)
```
Persona: Citizen
Language: Turkish
Text: "Atatürk Caddesi'ndeki eski apartman çöktü, en az 15 kişi enkaz altında. Ağır iş makinelerine acil ihtiyaç var. Saat sabah 6 civarında oldu."
Translation: "Old apartment building on Atatürk Street collapsed, at least 15 people trapped under rubble. Urgent need for heavy machinery. Happened around 6 AM."
Location: GPS coordinates + "Atatürk Caddesi"
Temporal: "sabah 6 civarında" (around 6 AM)
Resources: Heavy machinery, rescue team
Urgency: Critical
```

### Resource Update (Day 1, Hour 14)
```
Persona: Warehouse Manager
Language: English
Text: "Warehouse B-12 received insulin shipment at 2 PM. 500 units available for diabetic patients. Can be picked up until 8 PM today. Contact: +90-555-123-4567"
Location: GPS coordinates + "Warehouse B-12"
Temporal: "at 2 PM", "until 8 PM today"
Resources: Medicine (insulin), 500 units
Urgency: Medium
Contact: Phone number
```

### Rescue Operation (Day 2, Hour 8)
```
Persona: Rescue Team
Language: English
Text: "Team Alpha completed search operation in cluster 0 area. Found 8 survivors, evacuated to Camp C. Moving to northern district, ETA 45 minutes. Need medical supplies for next operation."
Location: GPS coordinates + "cluster 0 area", "northern district"
Temporal: "completed", "ETA 45 minutes"
Resources: Medical supplies needed
Status: Operation completed, moving
```

### Complex Multi-Resource (Day 3, Hour 10)
```
Persona: NGO Volunteer
Language: Turkish
Text: "Kuzey bölgesinde 200 aileye su dağıttık ama kaplar bitti. Ayrıca diyabet hastaları için insülin ve tansiyon ilaçları gerekiyor. Yarın sabah 10'da tekrar geleceğiz."
Translation: "Distributed water to 200 families in northern area but ran out of containers. Also need insulin and blood pressure medication for diabetic patients. Will return tomorrow morning at 10."
Location: GPS coordinates + "northern area"
Temporal: "yarın sabah 10'da" (tomorrow morning at 10)
Resources: Containers, insulin, blood pressure medication
Beneficiaries: 200 families
```

### Ambiguous Location (Day 0, Hour 18)
```
Persona: Citizen
Language: Turkish
Text: "Eski pazarın arkasındaki sokakta gaz kaçağı var. Yangın çıkabilir. Lütfen acil müdahale edin."
Translation: "Gas leak in the street behind the old market. Fire may break out. Please intervene urgently."
Location: GPS coordinates + "behind the old market" (ambiguous)
Temporal: Immediate
Urgency: Critical
Challenge: Geo-intelligence must resolve "old market" location
```

### Temporal Complexity (Day 4, Hour 12)
```
Persona: Rescue Team
Language: English
Text: "We've been searching since dawn in the eastern sector. Found medical supplies that were reported missing 2 days ago. Will complete current operation by evening and return to base."
Location: GPS coordinates + "eastern sector"
Temporal: "since dawn", "2 days ago", "by evening"
Status: In progress
Challenge: Multiple temporal references to normalize
```

---

## 🎲 Dynamic Variations & Edge Cases

### Scenario 1: Resource Chain Tracking
```
T+0h: Warehouse A: "Sent 200 food packages to Camp B"
T+2h: Rescue Team: "Picked up 200 food packages from Warehouse A, heading to Camp B"
T+4h: Camp B: "Received 180 food packages, 20 lost in transit"
T+6h: NGO: "Distributed 150 food packages from Camp B to families"
T+8h: Citizen: "Received food package from NGO, thank you"
```
**AI Challenge:** Track complete supply chain, identify loss, verify distribution

### Scenario 2: Conflicting Reports
```
T+0h: Report A: "50 people trapped in building X"
T+1h: Report B: "30 people trapped in building X, 20 already rescued"
T+2h: Report C: "Building X is actually building Y, coordinates were wrong"
```
**AI Challenge:** Detect conflicts, flag for human review, update records

### Scenario 3: Implicit Needs Cascade
```
Report: "School collapsed with 100 children inside, rescue ongoing"
Implicit Needs:
- Heavy machinery (building collapse)
- Medical teams (injuries expected)
- Psychological support (children trauma)
- Family reunification (parents searching)
- Temporary shelter (displaced children)
- Food and water (immediate needs)
```
**AI Challenge:** Infer all implicit requirements from single report

### Scenario 4: Multi-Language Coordination
```
Turkish Citizen: "Yardım lazım, su yok" (Need help, no water)
English Rescue Team: "Responding to water shortage report, ETA 30 minutes"
Arabic NGO: "نحن نحمل الماء، أين الموقع؟" (We have water, where is the location?)
```
**AI Challenge:** Coordinate across languages, match supply with demand

### Scenario 5: Temporal Reasoning Complexity
```
Report: "The building collapsed around midnight, we've been waiting since then. Rescue team said they would arrive by 8 AM but it's already 10 AM. We need help urgently, people are getting weaker by the hour."
Temporal Elements:
- Event time: "around midnight" (vague)
- Duration: "since then" (relative to event)
- Expected: "by 8 AM" (absolute)
- Current: "already 10 AM" (absolute)
- Deterioration: "by the hour" (rate)
```
**AI Challenge:** Extract all temporal elements, calculate delays, assess urgency

---

## 🗺️ Geographic Distribution

### Cluster 0 (Pre-classified damage area)
- 10 destroyed buildings with OSM IDs
- High concentration of emergency reports (Day 0-1)
- Moderate severity
- 40 people affected

### Northern District
- Lower damage concentration
- Resource distribution hub
- Camp locations
- Warehouse facilities

### Eastern Sector
- Search and rescue operations
- Medical facility locations
- NGO coordination center

### Southern Area
- Temporary shelters
- Food distribution points
- Community gathering areas

### City Center
- Old market (landmark reference)
- Main street (ambiguous reference)
- Mosque (landmark reference)
- Administrative buildings

---

## 📈 Data Quality Variations

### High Quality (60%)
- Clear location with GPS
- Specific resource types and quantities
- Precise timestamps
- Contact information provided
- Single, focused need

### Medium Quality (30%)
- Ambiguous location descriptions
- Approximate quantities
- Relative time references
- Multiple needs in one report
- Some missing information

### Low Quality (10%)
- Very vague locations
- No quantities specified
- Unclear temporal references
- Conflicting information
- Requires significant inference

---

## 🎯 AI Agent Testing Scenarios

### Query 1: Simple Aggregation
"Show me all food shortage reports"
**Expected:** Density polygons, count, locations

### Query 2: Temporal Filtering
"What medicine requests came in the last 6 hours?"
**Expected:** Filtered list with timestamps, map markers

### Query 3: Spatial Analysis
"Show me rescue operations near damaged buildings"
**Expected:** Overlay of rescue dots on building damage polygons

### Query 4: Comparative Analysis
"Compare food availability in northern vs. southern areas"
**Expected:** Two polygon layers, statistical comparison

### Query 5: Complex Multi-Factor
"Where do we need blood type A+ urgently near cluster 0?"
**Expected:** Filtered by resource type, urgency, location, damage context

### Query 6: Supply Chain Tracking
"Track all reports related to Warehouse B-12"
**Expected:** Timeline of inventory changes, distributions, pickups

### Query 7: Ambiguous Resolution
"Show me reports from near the old market"
**Expected:** Geo-intelligence resolves location, shows relevant reports

### Query 8: Temporal Reasoning
"What happened between 6 AM and noon on Day 0?"
**Expected:** Timeline visualization, event sequence

### Query 9: Implicit Needs
"Show me reports that might need medical attention"
**Expected:** Reports with injuries, elderly, children, chronic conditions

### Query 10: Resource Matching
"Which warehouses have insulin and are accessible from cluster 0?"
**Expected:** Warehouse locations, inventory status, route visualization

---

## 💾 Data Format

### JSON Structure
```json
{
  "report_id": "R-20230206-0001",
  "timestamp": "2023-02-06T06:15:23Z",
  "simulation_day": 0,
  "simulation_hour": 6,
  "persona": {
    "type": "citizen",
    "language": "tr",
    "organization": null
  },
  "location": {
    "gps": [37.191032, 36.74483],
    "description": "Atatürk Caddesi'ndeki eski apartman",
    "ambiguity": "low"
  },
  "text_original": "Atatürk Caddesi'ndeki eski apartman çöktü...",
  "text_translated": "Old apartment building on Atatürk Street collapsed...",
  "extracted_data": {
    "incident_type": "building_collapse",
    "severity": "critical",
    "people_count": 15,
    "resources_needed": ["heavy_machinery", "rescue_team"],
    "temporal_references": [
      {"type": "event_time", "value": "06:00:00", "confidence": 0.7}
    ],
    "implicit_needs": ["medical_support", "ambulance"]
  },
  "processing_metadata": {
    "confidence": 0.92,
    "agents_used": ["translation", "entity_extraction", "geo_intelligence", "triage"],
    "requires_human_review": false
  }
}
```

---

## 🔄 Dataset Generation Process

1. **Define scenario templates** for each category
2. **Generate base reports** with variations
3. **Add temporal references** with different formats
4. **Inject ambiguity** in locations and quantities
5. **Create supply chain sequences** for tracking
6. **Add conflicting reports** for validation testing
7. **Distribute across timeline** following methodology
8. **Translate to multiple languages**
9. **Validate completeness** of edge cases
10. **Export to JSON** for system ingestion

---

## ✅ Dataset Validation Checklist

- [ ] All persona types represented
- [ ] All resource types covered
- [ ] Temporal reference variations included
- [ ] Ambiguous locations present
- [ ] Multi-resource scenarios included
- [ ] Supply chain sequences complete
- [ ] Conflicting reports added
- [ ] Implicit needs scenarios included
- [ ] Multi-language distribution correct
- [ ] Geographic distribution realistic
- [ ] Data quality variations present
- [ ] Edge cases covered
- [ ] Timeline methodology followed
- [ ] Volume targets met
- [ ] JSON format validated

---

This sophisticated dataset will demonstrate the AI agent's ability to handle real-world complexity and edge cases, showcasing the technical excellence required to win the hackathon.
