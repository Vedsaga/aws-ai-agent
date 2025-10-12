# Quick Reference Guide

## 🎯 Core Winning Feature
**AI Agent Autonomous Map Control** - When operators ask questions, the AI independently:
- Decides optimal zoom level
- Generates density polygons
- Centers map on relevant areas
- Provides reasoning explanations

## 📊 System Overview

### What We're Building
- **Mobile App:** Simple 2-screen text input (NO audio/STT)
- **Multi-Agent Pipeline:** 7 specialist agents processing text reports
- **Dashboard:** 80-20 layout with AI-controlled map + text chat
- **Simulation:** 14-minute browser timeline = 7-day earthquake response

### What We're NOT Building
- ❌ Audio/STT processing (using pre-generated text)
- ❌ Task assignment system (using notifications instead)
- ❌ Collaboration features (individual sessions)
- ❌ Data export/reporting
- ❌ Custom ML models (using pre-trained AWS services)

## 🏗️ Architecture Stack

### AWS Services
- **Bedrock AgentCore** - Central orchestrator
- **Bedrock Nova** - Advanced reasoning
- **Amazon Q** - Knowledge assistant
- **Amazon Translate** - Multi-language
- **Amazon Comprehend** - NLP analysis
- **Amazon Location Service** - Geo-intelligence + OSM
- **DynamoDB** - Temporal data storage
- **EventBridge** - Event orchestration
- **SQS** - Resilient queuing
- **Lambda** - Serverless processing
- **API Gateway** - REST + WebSocket
- **S3** - GeoJSON + simulation data
- **Amplify** - Frontend hosting
- **CDK** - Infrastructure as code

### Frontend Stack
- **React** - UI framework
- **shadcn/ui** - Component library
- **Leaflet** - Map visualization
- **WebSocket** - Real-time updates

## 📝 Key Data Structures

### Text Report (NO audio)
```typescript
{
  id: string;
  transcript: string; // Pre-generated text
  originalLanguage: string;
  location: [lat, lon];
  temporalData: {
    simulationDay: 0-7;
    simulationHour: 0-23;
  };
  persona: 'citizen' | 'warehouse_manager' | 'rescue_team' | 'ngo';
  extractedData: {
    resourceType: string;
    quantity: number;
    urgency: string;
    temporalReferences: string[];
  };
}
```

### Notification
```typescript
{
  id: string;
  type: 'global' | 'proximity_based';
  message: string;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  distance?: number; // meters from user
  contactInfo?: string;
}
```

### Map Control Result
```typescript
{
  query: string;
  mapActions: {
    zoomChange: { newZoom: number; reason: string };
    centerChange: { newCenter: [lat, lon]; reason: string };
    polygonUpdates: { add: [], remove: [], modify: [] };
  };
  snapshotRecommendation: {
    shouldSave: boolean;
    suggestedName: string;
  };
  textResponse: string; // AI explanation
}
```

## 🎭 7 Specialist Agents

1. **Translation & Linguistics** - Amazon Translate + Comprehend
2. **Entity Extraction** - Amazon Comprehend + Bedrock
3. **Geo-Intelligence** - Location Service + OSM (resolve "near old market")
4. **Triage & Severity** - Bedrock Nova + damage context
5. **Resource Allocation** - DynamoDB + Bedrock optimization
6. **Temporal Reasoning** - Adaptive extraction ("by 8:15 AM", "since morning")
7. **Contact Manager** - Regex extraction + validation

## 📊 Simulation Dataset

### Volume: 200-300 reports across 7 days

**Day 0 (0-6h):** 80% emergency (collapses, fires, trapped people)
**Day 0 (6-24h):** 60% emergency, 40% resource requests
**Day 1-2:** 30% emergency, 70% rescue operations
**Day 3-7:** 10% emergency, 90% secondary needs

### Complexity Categories
- Ambiguous locations ("near the old market")
- Temporal variations ("around dawn", "by 8:15 AM")
- Multi-resource scenarios ("need food AND medicine AND transport")
- Supply chain tracking (warehouse → rescue team → distribution)
- Conflicting reports (validation testing)
- Implicit needs (elderly trapped → medical + mobility support)

### Languages
- Turkish: 60%
- English: 30%
- Arabic: 10%

## 🎬 3-Minute Demo Script

**0:00-0:30** - Problem introduction (Turkey earthquake coordination)
**0:30-1:00** - Mobile app + multi-agent processing
**1:00-2:00** - AI autonomous map control (CORE FEATURE):
  - Query 1: "Show me food shortage areas in last 12 hours"
  - Query 2: "Compare medicine requests near damaged buildings vs. safe zones"
  - Query 3: "Focus on cluster 0 and show rescue team movements"
**2:00-2:30** - Time slider progression (14 min = 7 days)
**2:30-3:00** - Technical architecture highlight

## 💰 Cost Estimate

**Total: ~$13 (within $100 budget)**
- Bedrock AgentCore: $5
- Bedrock Nova: $3
- Amazon Q: $0.40
- Other services: $4.60

## 🏆 Judging Criteria

**Technical Execution (50%):**
- ✅ Bedrock AgentCore + Nova + Q
- ✅ 7 specialist agents
- ✅ Autonomous capabilities
- ✅ Well-architected
- ✅ Reproducible (single CDK script)

**Potential Value (20%):**
- ✅ Real-world problem
- ✅ Measurable impact

**Creativity (10%):**
- ✅ Novel AI-controlled visualization
- ✅ Autonomous polygon generation

**Functionality (10%):**
- ✅ Working as expected
- ✅ Scalable

**Demo (10%):**
- ✅ End-to-end workflow
- ✅ Clear presentation

## 📋 Implementation Checklist

### Phase 1: Infrastructure (Task 1)
- [ ] AWS CDK setup
- [ ] Bedrock AgentCore configuration
- [ ] DynamoDB tables
- [ ] S3 buckets

### Phase 2: Data & Agents (Tasks 2-3)
- [ ] Data models
- [ ] 7 specialist agents
- [ ] Validation system
- [ ] Simulation dataset

### Phase 3: Applications (Tasks 4-5)
- [ ] Mobile app (text input + notifications)
- [ ] Dashboard (80-20 layout)
- [ ] AI map control (CORE FEATURE)
- [ ] Chat interface

### Phase 4: Simulation & Demo (Tasks 6-8)
- [ ] Temporal controls
- [ ] Session management
- [ ] Pre-classified data loading
- [ ] 3-minute demo script

## 🚀 Quick Start Commands

```bash
# Deploy infrastructure
npm run deploy

# Start dashboard locally
cd dashboard && npm run dev

# Start mobile app locally
cd mobile-app && npm run dev

# Generate simulation data
npm run generate-simulation-data

# Run demo
npm run demo
```

## 📞 Demo Queries

1. "Show me food shortage areas in the last 12 hours"
2. "Compare medicine requests near damaged buildings vs. safe zones"
3. "Focus on cluster 0 and show rescue team movements"
4. "Which warehouses have insulin and are accessible from cluster 0?"
5. "Show me all reports mentioning 'blood type A+'"

## 🎯 Success Metrics

- [ ] AI agent autonomously controls map
- [ ] System handles 200+ complex reports
- [ ] Demo completes in under 3 minutes
- [ ] All AWS services integrated
- [ ] Costs stay under $100
- [ ] System deployable with single script

## 📚 Key Documents

- **requirements.md** - What we're building
- **design.md** - How we're building it
- **tasks.md** - Implementation steps
- **hackathon-strategy.md** - Winning strategy
- **simulation-dataset-spec.md** - Dataset details
- **IMPROVEMENTS-SUMMARY.md** - All changes made
- **ADDITIONAL-CONSIDERATIONS.md** - Advanced features

---

**Remember:** Focus on the CORE WINNING FEATURE - AI agent autonomous map control. Everything else supports this.
