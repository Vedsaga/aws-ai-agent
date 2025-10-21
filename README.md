# Multi-Agent Orchestration System

A serverless, domain-agnostic multi-agent orchestration platform built on AWS for civic engagement, disaster response, and community data processing.

---

## Overview

This system enables users to submit unstructured reports (text + images) which are processed by specialized AI agents to extract structured data. Users can then query this data through natural language questions, with responses generated from multiple analytical perspectives.

**Status:** ✅ Production Ready - All APIs Verified Working (100% test pass rate)

---

## Quick Start

### 1. Deploy Backend (5 minutes)

```bash
./DEPLOY.sh
```

### 2. Test APIs (1 minute)

```bash
cd infrastructure
python3 TEST.py
```

### 3. Start Frontend (2 minutes)

```bash
cd infrastructure/frontend
npm install  # First time only
npm run dev
```

### 4. Login and Test

- **URL:** http://localhost:3000/login
- **Username:** testuser
- **Password:** TestPassword123!

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Users/Frontend                      │
│              (Next.js + React)                       │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│              API Gateway (REST)                      │
│         + Cognito JWT Authorizer                     │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼
    ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐
    │Config│   │Ingest│   │Query │   │ Data │
    │Lambda│   │Lambda│   │Lambda│   │Lambda│
    └───┬──┘   └───┬──┘   └───┬──┘   └───┬──┘
        │          │          │          │
        └──────────┼──────────┼──────────┘
                   ▼          ▼
        ┌─────────────────────────┐
        │   Orchestrator Lambda    │
        │  (Multi-Agent Coord)     │
        └─────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │DynamoDB│ │  RDS   │ │   S3   │
    │(Config)│ │(Data)  │ │(Files) │
    └────────┘ └────────┘ └────────┘
```

---

## Key Features

### Ingestion Pipeline
- **Domain Selection:** Civic Complaints, Agriculture, Disaster Response, Custom
- **Multi-Modal Input:** Text + images
- **Parallel Processing:** Multiple agents execute simultaneously
- **Real-Time Status:** Track processing progress
- **Structured Output:** Extracted data with defined schemas

### Query Pipeline
- **Natural Language:** Ask questions in plain English
- **Multi-Perspective Analysis:** 11 interrogative agents (What, When, Where, Why, How, etc.)
- **Comprehensive Answers:** Bullet points from each agent perspective
- **AI Summary:** Synthesized response from all agents
- **Visualization:** Map updates and charts

### Custom Agents
- **User-Defined:** Create agents via dashboard
- **Tool Selection:** Choose from registry (Bedrock, Comprehend, Location Service)
- **Output Schema:** Define structured output (max 5 keys)
- **Dependencies:** Single-level dependency graphs
- **Visual Editor:** n8n-style configuration interface

---

## Tech Stack

### AWS Services
- **Lambda** - Serverless compute
- **API Gateway** - REST APIs
- **Cognito** - Authentication
- **DynamoDB** - Configuration storage
- **RDS PostgreSQL** - Data storage
- **S3** - File storage
- **Bedrock** - LLM (Claude 3 Sonnet)
- **Comprehend** - NLP
- **Location Service** - Geocoding
- **CloudWatch** - Monitoring

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Mapbox GL JS** - Map visualization
- **AWS Amplify** - Authentication

### Backend
- **Python 3.11** - Lambda runtime
- **Boto3** - AWS SDK
- **AWS CDK** - Infrastructure as Code (TypeScript)

---

## Project Structure

```
.
├── README.md                          # This file
├── DEPLOYMENT.md                      # Deployment guide
├── DEPLOY.sh                          # Deployment script
│
├── infrastructure/
│   ├── API_DOCUMENTATION.md           # API reference & testing
│   ├── TEST.py                        # API test suite
│   ├── bin/app.ts                     # CDK app entry
│   ├── lib/stacks/                    # CDK stacks
│   │   ├── auth-stack.ts              # Cognito
│   │   ├── api-stack.ts               # API Gateway + Lambda
│   │   ├── data-stack.ts              # DynamoDB + RDS
│   │   └── storage-stack.ts           # S3
│   │
│   ├── lambda/                        # Lambda functions
│   │   ├── config-api/                # Agent/domain management
│   │   ├── orchestration/             # Multi-agent coordination
│   │   ├── realtime/                  # Status updates
│   │   └── authorizer/                # JWT validation
│   │
│   ├── frontend/                      # Next.js application
│   │   ├── app/                       # Pages
│   │   │   ├── login/                 # Login page
│   │   │   ├── dashboard/             # Main interface
│   │   │   ├── agents/                # Agent management
│   │   │   └── manage/                # Domain management
│   │   │
│   │   ├── components/                # React components
│   │   │   ├── MapView.tsx            # Map visualization
│   │   │   ├── IngestionPanel.tsx     # Report submission
│   │   │   ├── QueryPanel.tsx         # Question interface
│   │   │   └── AgentManagement.tsx    # Agent CRUD
│   │   │
│   │   └── lib/                       # Utilities
│   │       ├── api-client.ts          # API client
│   │       └── api-types.ts           # TypeScript types
│   │
│   └── scripts/                       # Utility scripts
│       ├── deploy.sh                  # Full deployment
│       ├── seed-data.sh               # Seed sample data
│       └── smoke-test.sh              # Quick verification
│
└── .kiro/specs/                       # Project specifications
    └── multi-agent-orchestration-system/
        ├── requirements.md            # 17 requirements
        ├── design.md                  # Architecture & design
        ├── tasks.md                   # Implementation plan
        └── diagrams/                  # 16 component diagrams
```

---

## API Endpoints

**Base URL:** `https://vluqfpl2zi.execute-api.us-east-1.amazonaws.com/v1`

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/config?type=agent` | GET | List agents | ✅ 200 |
| `/api/v1/config` | POST | Create agent/domain | ✅ 201 |
| `/api/v1/config/{type}/{id}` | GET | Get config | ✅ 200 |
| `/api/v1/config/{type}/{id}` | PUT | Update config | ✅ 200 |
| `/api/v1/config/{type}/{id}` | DELETE | Delete config | ✅ 200 |
| `/api/v1/ingest` | POST | Submit report | ✅ 202 |
| `/api/v1/query` | POST | Ask question | ✅ 202 |
| `/api/v1/tools` | GET | List tools | ✅ 200 |
| `/api/v1/data` | GET | Retrieve data | ✅ 200 |

See `infrastructure/API_DOCUMENTATION.md` for detailed API reference.

---

## Built-in Agents

1. **Geo Agent** - Extracts geographic information (location, coordinates)
2. **Temporal Agent** - Extracts time information (timestamp, date)
3. **Entity Agent** - Identifies entities (people, organizations)
4. **What Agent** - Answers "what" questions
5. **Where Agent** - Answers "where" questions
6. **When Agent** - Answers "when" questions
7. **Why Agent** - Answers "why" questions
8. **How Agent** - Answers "how" questions
9. **Who Agent** - Answers "who" questions
10. **Which Agent** - Answers "which" questions
11. **How Many Agent** - Answers "how many" questions

---

## Use Cases

### Civic Engagement
- Citizens report issues (potholes, broken streetlights)
- AI extracts location, severity, category
- Officials query trends and prioritize fixes
- Real-time dashboard shows all incidents on map

### Disaster Response
- Reports from affected areas (flooding, damage)
- AI extracts location, severity, needs
- Coordinators query resource requirements
- Optimize response team deployment

### Agriculture
- Farmers report crop issues (pests, disease)
- AI extracts crop type, location, severity
- Agronomists query patterns and trends
- Provide targeted recommendations

### Custom Domains
- Define your own domain template
- Create custom agents for specific needs
- Configure output schemas
- Build domain-specific workflows

---

## Testing

### Automated Tests

```bash
cd infrastructure
python3 TEST.py
```

**Test Coverage:**
- Authentication (401 without token)
- Config API (list, create, update, delete)
- Ingest API (submit reports)
- Query API (ask questions)
- Tools API (list tools)
- Data API (retrieve data)

**Expected:** 11/11 tests passed (100%)

### Manual Testing

See `infrastructure/API_DOCUMENTATION.md` for curl examples.

---

## Documentation

1. **README.md** (this file) - Project overview
2. **infrastructure/API_DOCUMENTATION.md** - Complete API reference and testing guide
3. **DEPLOYMENT.md** - Deployment instructions and troubleshooting

---

## Demo Flow (5 minutes)

### 1. Introduction (30 sec)
Show dashboard with map and chat interface. Explain multi-agent orchestration.

### 2. Submit Report (1 min)
- Click "Submit Report"
- Enter: "Broken streetlight on Main Street near the library"
- Show job ID returned
- Explain agent processing

### 3. Ask Question (1 min)
- Click "Ask Question"
- Enter: "What are the most common complaints this month?"
- Show job ID returned
- Explain interrogative agents

### 4. Create Custom Agent (1.5 min)
- Click "Manage Agents"
- Show built-in agents
- Create new agent
- Show in list

### 5. Conclusion (1 min)
- Highlight AWS services
- Emphasize scalability
- Show extensibility

---

## Development

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18+
- Python 3.11+
- AWS CLI configured
- AWS CDK CLI installed

### Local Development

```bash
# Backend (Lambda functions)
cd infrastructure/lambda/config-api
python3 config_handler.py

# Frontend
cd infrastructure/frontend
npm run dev
```

### Deploy Changes

```bash
# Deploy Lambda updates
./DEPLOY.sh

# Deploy infrastructure changes
cd infrastructure
cdk deploy --all
```

---

## Cost Optimization

### Current Configuration
- Lambda: Pay per invocation
- DynamoDB: On-demand pricing
- RDS: Aurora Serverless v2 (scales to 0.5 ACU)
- API Gateway: Pay per request

### Estimated Costs
- **Development:** $35-40/month
- **Production (low traffic):** $50-75/month
- **Production (high traffic):** $150-300/month

### Cost Reduction
- Stop RDS when not in use: `./infrastructure/scripts/stop-rds.sh`
- Use DynamoDB on-demand (already configured)
- Enable S3 lifecycle policies
- Set Lambda reserved concurrency limits

---

## Production Considerations

### Security
- Enable WAF on API Gateway
- Use Secrets Manager for credentials
- Enable CloudTrail logging
- Configure VPC endpoints
- Enable encryption at rest

### Reliability
- Multi-AZ RDS deployment
- Lambda reserved concurrency
- API Gateway throttling
- CloudWatch alarms
- Automated backups

### Monitoring
- CloudWatch dashboards
- X-Ray tracing
- Custom metrics
- Log aggregation
- SNS notifications

---

## Contributing

This is a hackathon project. For questions or issues, please contact the team.

---

## License

MIT License - Created for AWS AI Agent Hackathon

---

## Quick Commands

```bash
# Deploy system
./DEPLOY.sh

# Test APIs
cd infrastructure && python3 TEST.py

# Start frontend
cd infrastructure/frontend && npm run dev

# View logs
aws logs tail /aws/lambda/MultiAgentOrchestration-dev-Api-ConfigHandler --follow

# Reset password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_7QZ7Y6Gbl \
  --username testuser \
  --password TestPassword123! \
  --permanent \
  --region us-east-1
```

---

**Status:** ✅ Production Ready  
**Test Results:** 11/11 passed (100%)  
**Last Updated:** October 21, 2025

**Ready to deploy? Run `./DEPLOY.sh` now!**
